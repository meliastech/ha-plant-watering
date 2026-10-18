"""The runtime model of one plant."""

from __future__ import annotations

from collections.abc import Callable
import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import area_registry as ar, device_registry as dr
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DAILY_REMINDER,
    CONF_NOTIFY_TARGETS,
    CONF_PLANT_TYPE,
    CONF_REMINDER_TIME,
    CONF_SOIL_SENSOR,
    DEFAULT_REMINDER_TIME,
    DOMAIN,
    EVENT_NEEDS_WATER,
    PHOTO_DIR,
    REARM_MARGIN,
    STATUS_NEEDS_WATER,
    STATUS_OK,
    STATUS_SENSOR_OFFLINE,
    STORAGE_VERSION,
)
from .plant_db import PlantDatabase, PlantType

_LOGGER = logging.getLogger(__name__)

FALLBACK_MIN_MOISTURE = 30.0
FALLBACK_WATER_ML = 300


type PlantConfigEntry = ConfigEntry[Plant]


class Plant:
    """One plant: its type, watering settings, photo and needs-water state."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, db: PlantDatabase) -> None:
        """Initialise the plant."""
        self.hass = hass
        self.entry = entry
        self.db = db
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self._listeners: list[CALLBACK_TYPE] = []
        self.plant_type_id: str = entry.data[CONF_PLANT_TYPE]
        self.min_moisture = FALLBACK_MIN_MOISTURE
        self.water_ml = FALLBACK_WATER_ML
        self.needs_water = False
        self.photo: str | None = None
        self.photo_version = 0

    async def async_load(self) -> None:
        """Load saved settings, falling back to the plant type's presets."""
        saved = await self._store.async_load() or {}
        self.plant_type_id = saved.get("plant_type", self.plant_type_id)
        preset = self.plant_type
        self.min_moisture = float(saved.get("min_moisture", preset.min_moisture if preset else FALLBACK_MIN_MOISTURE))
        self.water_ml = int(saved.get("water_ml", preset.water_ml if preset else FALLBACK_WATER_ML))
        self.needs_water = bool(saved.get("needs_water", False))
        self.photo = saved.get("photo")

    @callback
    def async_start(self) -> None:
        """Start following the soil sensor and the daily reminder."""
        self.entry.async_on_unload(
            async_track_state_change_event(self.hass, [self.soil_sensor], self._async_soil_changed)
        )
        if self.entry.options.get(CONF_DAILY_REMINDER, True):
            time = dt_util.parse_time(self.entry.options.get(CONF_REMINDER_TIME, DEFAULT_REMINDER_TIME))
            if time is not None:
                self.entry.async_on_unload(
                    async_track_time_change(
                        self.hass, self._async_reminder, hour=time.hour, minute=time.minute, second=time.second
                    )
                )
        self._evaluate()

    async def async_save(self) -> None:
        """Save settings now rather than after the usual short delay."""
        await self._store.async_save(self._data_to_save())

    # Settings

    @property
    def name(self) -> str:
        """Plant name."""
        return self.entry.title

    @property
    def soil_sensor(self) -> str:
        """Entity id of the soil moisture sensor."""
        return self.entry.options.get(CONF_SOIL_SENSOR, self.entry.data[CONF_SOIL_SENSOR])

    @property
    def notify_targets(self) -> list[str]:
        """Notify services to alert, without the notify. prefix."""
        return [t.removeprefix("notify.") for t in self.entry.options.get(CONF_NOTIFY_TARGETS, [])]

    @property
    def plant_type(self) -> PlantType | None:
        """The plant type from the database, or None for a custom type."""
        return self.db.get(self.plant_type_id)

    @property
    def type_name(self) -> str:
        """Readable plant type."""
        return self.plant_type.name if self.plant_type else "Custom"

    @property
    def photo_path(self) -> Path:
        """Where the user's own photo is stored."""
        return Path(self.hass.config.path(PHOTO_DIR, self.photo or ""))

    @property
    def area_name(self) -> str | None:
        """Name of the area the plant's device is in."""
        device = dr.async_get(self.hass).async_get_device(identifiers={(DOMAIN, self.entry.entry_id)})
        if device is None or device.area_id is None:
            return None
        area = ar.async_get(self.hass).async_get_area(device.area_id)
        return area.name if area else None

    @callback
    def async_set_plant_type(self, type_id: str) -> None:
        """Change the plant type, resetting watering settings to its presets."""
        self.plant_type_id = type_id
        if preset := self.plant_type:
            self.min_moisture = preset.min_moisture
            self.water_ml = preset.water_ml
        registry = dr.async_get(self.hass)
        if device := registry.async_get_device(identifiers={(DOMAIN, self.entry.entry_id)}):
            registry.async_update_device(device.id, model=self.type_name)
        self.photo_version += 1
        self._evaluate()

    @callback
    def async_set_min_moisture(self, value: float) -> None:
        """Override the minimum moisture."""
        self.min_moisture = value
        self._evaluate()

    @callback
    def async_set_water_ml(self, value: int) -> None:
        """Override the watering amount."""
        self.water_ml = value
        self._changed()

    @callback
    def async_set_photo(self, filename: str | None) -> None:
        """Use a photo stored in the photo folder, or None for the generic picture."""
        self.photo = filename
        self.photo_version += 1
        self._changed()

    # State

    @property
    def moisture(self) -> float | None:
        """Current soil moisture, or None when the sensor isn't reporting."""
        state = self.hass.states.get(self.soil_sensor)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    @property
    def status(self) -> str:
        """ok, needs_water or sensor_offline."""
        if self.moisture is None:
            return STATUS_SENSOR_OFFLINE
        return STATUS_NEEDS_WATER if self.needs_water else STATUS_OK

    @callback
    def async_add_listener(self, update: CALLBACK_TYPE) -> Callable[[], None]:
        """Call update whenever the plant changes."""
        self._listeners.append(update)
        return lambda: self._listeners.remove(update)

    @callback
    def _changed(self) -> None:
        self._store.async_delay_save(self._data_to_save, 1)
        for update in list(self._listeners):
            update()

    def _data_to_save(self) -> dict[str, Any]:
        return {
            "plant_type": self.plant_type_id,
            "min_moisture": self.min_moisture,
            "water_ml": self.water_ml,
            "needs_water": self.needs_water,
            "photo": self.photo,
        }

    @callback
    def _async_soil_changed(self, event: Event[EventStateChangedData]) -> None:
        self._evaluate()

    @callback
    def _evaluate(self) -> None:
        """Flag the plant once per dry spell; re-arm when it has been watered."""
        moisture = self.moisture
        if moisture is not None:
            if not self.needs_water and moisture <= self.min_moisture:
                self.needs_water = True
                self._alert(moisture, reminder=False)
            elif self.needs_water and moisture > self.min_moisture + REARM_MARGIN:
                self.needs_water = False
        self._changed()

    @callback
    def _async_reminder(self, now: Any) -> None:
        moisture = self.moisture
        if self.needs_water and moisture is not None:
            self._alert(moisture, reminder=True)

    @callback
    def _alert(self, moisture: float, reminder: bool) -> None:
        area = self.area_name
        where = f" in {area}" if area else ""
        message = (
            f"Water {self.name} ({self.type_name}){where}: moisture {moisture:g}% "
            f"(min {self.min_moisture:g}%). Give it about {self.water_ml} mL."
        )
        self.hass.bus.async_fire(
            EVENT_NEEDS_WATER,
            {
                "entry_id": self.entry.entry_id,
                "name": self.name,
                "plant_type": self.type_name,
                "area": area,
                "moisture": moisture,
                "min_moisture": self.min_moisture,
                "water_ml": self.water_ml,
                "reminder": reminder,
                "message": message,
            },
        )
        title = f"Reminder: water {self.name}" if reminder else f"Water {self.name}"
        for target in self.notify_targets:
            if not self.hass.services.has_service("notify", target):
                _LOGGER.warning("Notify service notify.%s for %s doesn't exist", target, self.name)
                continue
            self.hass.async_create_task(
                self.hass.services.async_call("notify", target, {"title": title, "message": message})
            )
