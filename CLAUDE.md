# Plant Watering (ha-plant-watering)

At the end of a working session, update ## Status with what changed and what's next.

Home Assistant custom integration (domain `plant_watering`), installed through HACS as a custom
repository. Each plant is a device driven by a soil moisture sensor and a built-in plant-type database,
with alerts (event, notify services, optional daily reminder) when it needs water.

## Stack

- Python, Home Assistant >= 2025.1.0 (`hacs.json`). Manifest: `config_flow: true`, `integration_type: device`,
  `iot_class: calculated`, dependencies `file_upload`, `http`, no pip requirements, version 0.1.0.
- Tests: `pytest-homeassistant-custom-component` with pytest-asyncio (`asyncio_mode = "auto"`), Python 3.13 in CI.

## Commands

```bash
pip install -r requirements_test.txt
pytest                                # tests/ (config flow, plant logic)
python scripts/generate_images.py     # redraw the generic plant SVGs (run from repo root)
```

## Layout

- `custom_components/plant_watering/`
  - `__init__.py` setup, static path `/plant_watering_static/<image>.svg`; `plant.py` core state and alert
    logic (alert once per dry spell, re-arm at minimum + 3%, offline sensor never counts as dry).
  - Platforms: `sensor.py` (moisture, status), `binary_sensor.py` (needs water), `number.py` (minimum
    moisture, watering amount), `select.py` (plant type), `image.py` (photo or generic picture).
  - `config_flow.py` (add plant + options: sensor/alerts, photo upload), `entity.py`, `const.py`.
  - `plant_db.py` + `data/plants.json` (types: `min_moisture`, `max_moisture`, `water_ml`, `light`, `care`, `image`).
  - `images/*.svg` generic pictures; `strings.json` and `translations/en.json` (keep them identical).
- `tests/` - `conftest.py`, `test_config_flow.py`, `test_plant.py`.
- `.github/workflows/validate.yml` - on every push/PR: hassfest, HACS action (`ignore: brands`), pytest.

## Conventions

- Bump `version` in `manifest.json` for releases (HACS reads it).
- Moisture thresholds are starting points for capacitive sensors; document any change to `plants.json` defaults.
- Fired event name `plant_watering_needs_water` is public API for users' automations; don't rename it.
- Single initial commit so far; no branch/PR habits visible yet.

## Memory

Use the `memory` MCP server: recall project `ha-plant-watering` before working, and remember decisions,
gotchas and todos there. Never save secrets.

## Status

- Live: v0.1.0 on `main`, installable as a HACS custom repository.
- Known problem: the `Validate` workflow on `main` fails (run 39093097204, 18 Oct 2026). hassfest and pytest
  pass; only the HACS job fails, 2/8 checks: "The repository has no description" and "The repository has
  no valid topics". Fix is in GitHub repo settings, not code: add a description and topics (e.g.
  `home-assistant`, `hacs`, `hacs-integration`). Every PR will show the same failure until then.
- Note: the workflow uses `hacs/action@main` and `home-assistant/actions/hassfest@master` (unpinned).
- Open PRs: none besides this one.
- Last updated: 12 Nov 2026
