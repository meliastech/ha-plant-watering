# Plant Watering for Home Assistant

Watering alerts for your plants, driven by soil moisture sensors and a built-in plant database.

Pick a plant type when you add a plant and it fills in when to water (minimum soil moisture) and how much to give (watering amount). You can override either on any plant. Each plant gets a generic picture of its type, which you can replace with a photo of your own plant.

## What you get for each plant

Each plant is a device, placed in a room, with these entities:

| Entity | What it does |
| --- | --- |
| `select.<plant>_plant_type` | The plant type. Changing it applies that type's minimum moisture and watering amount. |
| `number.<plant>_minimum_moisture` | Water the plant when the soil gets this dry. Preset from the type, overridable. |
| `number.<plant>_watering_amount` | How much water to give, in mL. Preset from the type, overridable. |
| `sensor.<plant>_moisture` | The soil sensor's reading, kept on the plant's device. |
| `binary_sensor.<plant>_needs_water` | On from when moisture drops to the minimum until the plant has been watered. |
| `sensor.<plant>_status` | `ok`, `needs_water` or `sensor_offline`, with the plant's details (type, scientific name, light, care notes, generic picture URL) as attributes. |
| `image.<plant>_photo` | Your photo of the plant, or the type's generic picture. |

## Alerts

When a plant's moisture drops to its minimum the integration:

- turns on its **Needs water** sensor,
- fires a `plant_watering_needs_water` event (with the plant, room, moisture, minimum, watering amount and a ready-made message), and
- sends a notification to any notify services you chose, for example `notify.mobile_app_your_phone`.

It alerts once per dry spell. The alert re-arms when moisture climbs 3% above the minimum, so a sensor hovering around the threshold doesn't send a stream of notifications. An optional daily reminder (9:00 by default) repeats the alert while the plant still needs water. An offline or unavailable sensor is reported as offline and never counts as dry.

## Installation

### HACS

1. In HACS, open the menu and choose **Custom repositories**.
2. Add `https://github.com/meliastech/ha-plant-watering` with the type **Integration**.
3. Install **Plant Watering** and restart Home Assistant.

### Manual

Copy `custom_components/plant_watering` into your Home Assistant `config/custom_components` folder and restart.

## Adding a plant

**Settings > Devices & services > Add integration > Plant Watering.** Give the plant a name, choose its soil moisture sensor and plant type, and optionally a room (it defaults to the sensor's room).

Open the plant's **Configure** menu to:

- **Sensor and alerts:** change the soil sensor, choose who gets notified, and set the daily reminder.
- **Photo:** upload a photo of your plant, or go back to the generic picture.

## The plant database

The database lives in [`custom_components/plant_watering/data/plants.json`](custom_components/plant_watering/data/plants.json). Each type has:

| Field | Meaning |
| --- | --- |
| `min_moisture` | Soil moisture % at which to water. |
| `max_moisture` | The wettest the soil should stay (shown as an attribute; for future use). |
| `water_ml` | A typical drink for a plant in a 15-20 cm pot. |
| `light`, `care` | Short care notes. |
| `image` | Which generic picture to use. |

The moisture values are starting points for common capacitive soil sensors, which don't all read the same, so adjust each plant to what you see from its sensor. Pull requests that add plant types are welcome.

The generic pictures are SVGs drawn by [`scripts/generate_images.py`](scripts/generate_images.py) and are served at `/plant_watering_static/<image>.svg` for use in dashboards.

## Example dashboard card

```yaml
type: vertical-stack
cards:
  - type: picture-entity
    entity: image.office_plant_photo
    name: Office Plant
    show_state: false
  - type: tile
    entity: sensor.office_plant_status
  - type: gauge
    entity: sensor.office_plant_moisture
    min: 0
    max: 100
    needle: true
  - type: entities
    entities:
      - select.office_plant_plant_type
      - number.office_plant_minimum_moisture
      - number.office_plant_watering_amount
```

## Development

```bash
pip install -r requirements_test.txt
pytest
```

## Licence

MIT
