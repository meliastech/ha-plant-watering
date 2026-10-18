"""Plant Watering: soil-moisture watering alerts with a plant database."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, device_registry as dr, entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .const import CONF_AREA, CONF_SOIL_SENSOR, DOMAIN, PHOTO_DIR, PLATFORMS, STATIC_URL, STORAGE_VERSION
from .plant import Plant, PlantConfigEntry
from .plant_db import IMAGE_DIR, async_get_db

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the generic plant pictures for dashboards."""
    await hass.http.async_register_static_paths([StaticPathConfig(STATIC_URL, str(IMAGE_DIR), True)])
    return True


async def async_setup_entry(hass: HomeAssistant, entry: PlantConfigEntry) -> bool:
    """Set up one plant."""
    plant = Plant(hass, entry, await async_get_db(hass))
    await plant.async_load()
    entry.runtime_data = plant

    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Plant Watering",
        model=plant.type_name,
    )
    if device.area_id is None:
        area_id = entry.data.get(CONF_AREA) or _sensor_area(hass, plant.soil_sensor)
        if area_id:
            dr.async_get(hass).async_update_device(device.id, area_id=area_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    plant.async_start()
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PlantConfigEntry) -> bool:
    """Unload a plant."""
    await entry.runtime_data.async_save()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: PlantConfigEntry) -> None:
    """Delete the plant's saved settings and photo."""
    await Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_remove()

    def remove_photos() -> None:
        for photo in Path(hass.config.path(PHOTO_DIR)).glob(f"{entry.entry_id}.*"):
            photo.unlink(missing_ok=True)

    await hass.async_add_executor_job(remove_photos)


async def _async_options_updated(hass: HomeAssistant, entry: PlantConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _sensor_area(hass: HomeAssistant, entity_id: str) -> str | None:
    """Area of the soil sensor, directly or through its device."""
    entity = er.async_get(hass).async_get(entity_id)
    if entity is None:
        return None
    if entity.area_id:
        return entity.area_id
    if entity.device_id and (device := dr.async_get(hass).async_get(entity.device_id)):
        return device.area_id
    return None
