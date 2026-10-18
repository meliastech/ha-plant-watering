"""Needs-water binary sensor."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import PlantEntity
from .plant import PlantConfigEntry

NEEDS_WATER = BinarySensorEntityDescription(
    key="needs_water",
    translation_key="needs_water",
    device_class=BinarySensorDeviceClass.PROBLEM,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: PlantConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up the needs-water sensor."""
    async_add_entities([NeedsWaterSensor(entry.runtime_data, NEEDS_WATER)])


class NeedsWaterSensor(PlantEntity, BinarySensorEntity):
    """On from when moisture drops to the minimum until the plant is watered."""

    @property
    def is_on(self) -> bool:
        """Whether the plant needs water."""
        return self.plant.needs_water

    @property
    def available(self) -> bool:
        """Unavailable while the soil sensor isn't reporting."""
        return self.plant.moisture is not None
