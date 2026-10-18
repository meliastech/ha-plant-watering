"""The bundled plant database."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import DOMAIN

DATA_FILE = Path(__file__).parent / "data" / "plants.json"
IMAGE_DIR = Path(__file__).parent / "images"
DB_KEY = f"{DOMAIN}_db"


@dataclass(frozen=True, slots=True)
class PlantType:
    """A plant type and its watering presets."""

    id: str
    name: str
    scientific_name: str
    image: str
    min_moisture: float
    max_moisture: float
    water_ml: int
    light: str
    care: str

    @property
    def image_path(self) -> Path:
        """Path of the generic picture for this plant type."""
        return IMAGE_DIR / f"{self.image}.svg"


class PlantDatabase:
    """Plant types keyed by id."""

    def __init__(self, types: list[PlantType]) -> None:
        """Initialise the database."""
        self._types = {plant.id: plant for plant in types}

    def get(self, type_id: str | None) -> PlantType | None:
        """Return a plant type, or None for unknown or custom types."""
        return self._types.get(type_id) if type_id else None

    @property
    def types(self) -> list[PlantType]:
        """All plant types sorted by name, with the generic type first."""
        return sorted(self._types.values(), key=lambda p: (p.id != "generic", p.name.lower()))

    @classmethod
    def from_file(cls, path: Path = DATA_FILE) -> PlantDatabase:
        """Load the database from its JSON file."""
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls([PlantType(**plant) for plant in raw["plants"]])


async def async_get_db(hass: HomeAssistant) -> PlantDatabase:
    """Return the plant database, loading it once."""
    if (db := hass.data.get(DB_KEY)) is None:
        db = hass.data[DB_KEY] = await hass.async_add_executor_job(PlantDatabase.from_file)
    return db
