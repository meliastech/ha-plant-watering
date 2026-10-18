"""Plant picture: the user's own photo, or the plant type's generic picture."""

from __future__ import annotations

import mimetypes

from homeassistant.components.image import ImageEntity, ImageEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import PlantEntity
from .plant import Plant, PlantConfigEntry
from .plant_db import IMAGE_DIR

PHOTO = ImageEntityDescription(key="photo", translation_key="photo")


async def async_setup_entry(
    hass: HomeAssistant, entry: PlantConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up the plant picture."""
    async_add_entities([PlantPhoto(hass, entry.runtime_data)])


class PlantPhoto(PlantEntity, ImageEntity):
    """The plant's picture."""

    def __init__(self, hass: HomeAssistant, plant: Plant) -> None:
        """Initialise the picture."""
        PlantEntity.__init__(self, plant, PHOTO)
        ImageEntity.__init__(self, hass)
        self._version = plant.photo_version
        self._attr_image_last_updated = dt_util.utcnow()

    def _handle_plant_update(self) -> None:
        if self.plant.photo_version != self._version:
            self._version = self.plant.photo_version
            self._attr_image_last_updated = dt_util.utcnow()
        super()._handle_plant_update()

    async def async_image(self) -> bytes | None:
        """The user's photo if there is one, else the generic picture."""
        plant = self.plant
        if plant.photo:
            path = plant.photo_path
            self._attr_content_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        else:
            image = plant.plant_type.image if plant.plant_type else "leafy"
            path = IMAGE_DIR / f"{image}.svg"
            self._attr_content_type = "image/svg+xml"
        try:
            return await self.hass.async_add_executor_job(path.read_bytes)
        except FileNotFoundError:
            return None
