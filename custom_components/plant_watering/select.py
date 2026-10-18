"""Plant type select."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CUSTOM_TYPE
from .entity import PlantEntity
from .plant import PlantConfigEntry

PLANT_TYPE = SelectEntityDescription(
    key="plant_type",
    translation_key="plant_type",
    icon="mdi:sprout",
    entity_category=EntityCategory.CONFIG,
)
CUSTOM_NAME = "Custom"


async def async_setup_entry(
    hass: HomeAssistant, entry: PlantConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up the plant type select."""
    async_add_entities([PlantTypeSelect(entry.runtime_data, PLANT_TYPE)])


class PlantTypeSelect(PlantEntity, SelectEntity):
    """Choosing a plant type applies its watering presets."""

    @property
    def options(self) -> list[str]:
        """Plant type names from the database, plus Custom."""
        return [plant.name for plant in self.plant.db.types] + [CUSTOM_NAME]

    @property
    def current_option(self) -> str:
        """The plant's type."""
        return self.plant.type_name

    async def async_select_option(self, option: str) -> None:
        """Change the type and apply its presets."""
        type_id = next((p.id for p in self.plant.db.types if p.name == option), CUSTOM_TYPE)
        self.plant.async_set_plant_type(type_id)
