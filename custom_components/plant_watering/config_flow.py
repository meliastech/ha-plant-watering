"""Config and options flows for Plant Watering."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

import voluptuous as vol

from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    CONF_AREA,
    CONF_DAILY_REMINDER,
    CONF_NOTIFY_TARGETS,
    CONF_PHOTO,
    CONF_PLANT_TYPE,
    CONF_REMINDER_TIME,
    CONF_REMOVE_PHOTO,
    CONF_SOIL_SENSOR,
    CUSTOM_TYPE,
    DEFAULT_REMINDER_TIME,
    DOMAIN,
    PHOTO_DIR,
)
from .plant import PlantConfigEntry
from .plant_db import async_get_db

PHOTO_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

SOIL_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.MOISTURE)
)


async def _plant_type_selector(hass: HomeAssistant) -> selector.SelectSelector:
    db = await async_get_db(hass)
    options = [selector.SelectOptionDict(value=p.id, label=p.name) for p in db.types]
    options.append(selector.SelectOptionDict(value=CUSTOM_TYPE, label="Custom"))
    return selector.SelectSelector(
        selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN, sort=False)
    )


class PlantWateringConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a plant."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Name the plant, pick its soil sensor and type."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_SOIL_SENSOR])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_SOIL_SENSOR: user_input[CONF_SOIL_SENSOR],
                    CONF_PLANT_TYPE: user_input[CONF_PLANT_TYPE],
                    CONF_AREA: user_input.get(CONF_AREA),
                },
                options={CONF_DAILY_REMINDER: True, CONF_REMINDER_TIME: DEFAULT_REMINDER_TIME, CONF_NOTIFY_TARGETS: []},
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): selector.TextSelector(),
                vol.Required(CONF_SOIL_SENSOR): SOIL_SENSOR_SELECTOR,
                vol.Required(CONF_PLANT_TYPE, default="generic"): await _plant_type_selector(self.hass),
                vol.Optional(CONF_AREA): selector.AreaSelector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: PlantConfigEntry) -> PlantWateringOptionsFlow:
        """Plant settings."""
        return PlantWateringOptionsFlow()


class PlantWateringOptionsFlow(OptionsFlow):
    """Change a plant's sensor, alerts or photo."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Pick what to change."""
        return self.async_show_menu(step_id="init", menu_options=["alerts", "photo"])

    async def async_step_alerts(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Soil sensor, who to notify and the daily reminder."""
        options = self.config_entry.options
        if user_input is not None:
            return self.async_create_entry(data={**options, **user_input})

        notify_services = sorted(
            f"notify.{service}"
            for service in self.hass.services.async_services_for_domain("notify")
            if service not in ("send_message", "persistent_notification")
        )
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SOIL_SENSOR,
                    default=options.get(CONF_SOIL_SENSOR, self.config_entry.data[CONF_SOIL_SENSOR]),
                ): SOIL_SENSOR_SELECTOR,
                vol.Optional(CONF_NOTIFY_TARGETS, default=options.get(CONF_NOTIFY_TARGETS, [])): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=notify_services, multiple=True, custom_value=True)
                ),
                vol.Required(CONF_DAILY_REMINDER, default=options.get(CONF_DAILY_REMINDER, True)): selector.BooleanSelector(),
                vol.Required(
                    CONF_REMINDER_TIME, default=options.get(CONF_REMINDER_TIME, DEFAULT_REMINDER_TIME)
                ): selector.TimeSelector(),
            }
        )
        return self.async_show_form(step_id="alerts", data_schema=schema)

    async def async_step_photo(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Upload a photo of the plant, or go back to the generic picture."""
        plant = self.config_entry.runtime_data
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get(CONF_REMOVE_PHOTO):
                await self.hass.async_add_executor_job(_delete_photos, self.hass, self.config_entry.entry_id)
                plant.async_set_photo(None)
                return self.async_create_entry(data=dict(self.config_entry.options))
            if file_id := user_input.get(CONF_PHOTO):
                filename = await self.hass.async_add_executor_job(
                    _save_photo, self.hass, file_id, self.config_entry.entry_id
                )
                if filename is None:
                    errors[CONF_PHOTO] = "invalid_photo"
                else:
                    plant.async_set_photo(filename)
                    return self.async_create_entry(data=dict(self.config_entry.options))
            else:
                return self.async_create_entry(data=dict(self.config_entry.options))

        schema = vol.Schema(
            {
                vol.Optional(CONF_PHOTO): selector.FileSelector(selector.FileSelectorConfig(accept="image/*")),
                vol.Optional(CONF_REMOVE_PHOTO, default=False): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="photo", data_schema=schema, errors=errors)


def _save_photo(hass: HomeAssistant, file_id: str, entry_id: str) -> str | None:
    """Move an uploaded photo into the photo folder; None if it isn't an image."""
    with process_uploaded_file(hass, file_id) as upload:
        suffix = upload.suffix.lower()
        if suffix not in PHOTO_TYPES:
            return None
        photo_dir = Path(hass.config.path(PHOTO_DIR))
        photo_dir.mkdir(parents=True, exist_ok=True)
        _delete_photos(hass, entry_id)
        filename = f"{entry_id}{suffix}"
        shutil.copyfile(upload, photo_dir / filename)
    return filename


def _delete_photos(hass: HomeAssistant, entry_id: str) -> None:
    for photo in Path(hass.config.path(PHOTO_DIR)).glob(f"{entry_id}.*"):
        photo.unlink(missing_ok=True)
