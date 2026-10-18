"""Base entity for a plant."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription

from .const import DOMAIN
from .plant import Plant


class PlantEntity(Entity):
    """An entity that belongs to one plant's device."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, plant: Plant, description: EntityDescription) -> None:
        """Initialise the entity."""
        self.plant = plant
        self.entity_description = description
        self._attr_unique_id = f"{plant.entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, plant.entry.entry_id)})

    async def async_added_to_hass(self) -> None:
        """Follow changes to the plant."""
        self.async_on_remove(self.plant.async_add_listener(self._handle_plant_update))

    def _handle_plant_update(self) -> None:
        self.async_write_ha_state()
