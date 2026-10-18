"""Minimum moisture and watering amount."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import PlantEntity
from .plant import Plant, PlantConfigEntry


@dataclass(frozen=True, kw_only=True)
class PlantNumberDescription(NumberEntityDescription):
    """A plant setting stored on the Plant."""

    value_fn: Callable[[Plant], float]
    set_fn: Callable[[Plant, float], None]


NUMBERS = (
    PlantNumberDescription(
        key="min_moisture",
        translation_key="min_moisture",
        icon="mdi:water-percent-alert",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda plant: plant.min_moisture,
        set_fn=lambda plant, value: plant.async_set_min_moisture(value),
    ),
    PlantNumberDescription(
        key="water_amount",
        translation_key="water_amount",
        icon="mdi:watering-can",
        native_min_value=0,
        native_max_value=5000,
        native_step=10,
        native_unit_of_measurement=UnitOfVolume.MILLILITERS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda plant: plant.water_ml,
        set_fn=lambda plant, value: plant.async_set_water_ml(int(value)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: PlantConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up the plant's number settings."""
    async_add_entities(PlantNumber(entry.runtime_data, description) for description in NUMBERS)


class PlantNumber(PlantEntity, NumberEntity):
    """A watering setting, preset from the plant type and overridable."""

    entity_description: PlantNumberDescription

    @property
    def native_value(self) -> float:
        """Current value."""
        return self.entity_description.value_fn(self.plant)

    async def async_set_native_value(self, value: float) -> None:
        """Override the preset."""
        self.entity_description.set_fn(self.plant, value)
