"""Plant status and moisture sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import STATIC_URL, STATUS_NEEDS_WATER, STATUS_OK, STATUS_SENSOR_OFFLINE
from .entity import PlantEntity
from .plant import PlantConfigEntry

STATUS = SensorEntityDescription(
    key="status",
    translation_key="status",
    device_class=SensorDeviceClass.ENUM,
    options=[STATUS_OK, STATUS_NEEDS_WATER, STATUS_SENSOR_OFFLINE],
)
MOISTURE = SensorEntityDescription(
    key="moisture",
    device_class=SensorDeviceClass.MOISTURE,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=PERCENTAGE,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: PlantConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up the plant's sensors."""
    plant = entry.runtime_data
    async_add_entities([PlantStatusSensor(plant, STATUS), PlantMoistureSensor(plant, MOISTURE)])


class PlantStatusSensor(PlantEntity, SensorEntity):
    """Overall plant status, with the plant's details as attributes."""

    @property
    def native_value(self) -> str:
        """ok, needs_water or sensor_offline."""
        return self.plant.status

    @property
    def icon(self) -> str:
        """Icon that reflects the status."""
        return {
            STATUS_OK: "mdi:sprout",
            STATUS_NEEDS_WATER: "mdi:watering-can",
        }.get(self.plant.status, "mdi:sprout-outline")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Plant details for dashboards and automations."""
        plant = self.plant
        preset = plant.plant_type
        return {
            "plant_type": plant.type_name,
            "scientific_name": preset.scientific_name if preset else None,
            "moisture": plant.moisture,
            "min_moisture": plant.min_moisture,
            "max_moisture": preset.max_moisture if preset else None,
            "water_amount": plant.water_ml,
            "light": preset.light if preset else None,
            "care": preset.care if preset else None,
            "soil_sensor": plant.soil_sensor,
            "generic_picture": f"{STATIC_URL}/{preset.image if preset else 'leafy'}.svg",
        }


class PlantMoistureSensor(PlantEntity, SensorEntity):
    """The soil sensor's reading, kept on the plant's device."""

    async def async_added_to_hass(self) -> None:
        """Also follow the soil sensor."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_state_change_event(self.hass, [self.plant.soil_sensor], self._async_soil_changed)
        )

    @callback
    def _async_soil_changed(self, event: Event[EventStateChangedData]) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        """Soil moisture."""
        return self.plant.moisture

    @property
    def available(self) -> bool:
        """Unavailable while the soil sensor isn't reporting."""
        return self.plant.moisture is not None
