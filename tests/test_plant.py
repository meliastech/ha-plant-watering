"""Plant behaviour: presets, overrides and alerts."""

from __future__ import annotations

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_capture_events, async_mock_service

from custom_components.plant_watering.const import EVENT_NEEDS_WATER

from .conftest import SOIL

STATUS = "sensor.office_plant_status"
NEEDS_WATER = "binary_sensor.office_plant_needs_water"
MIN = "number.office_plant_minimum_moisture"
WATER = "number.office_plant_watering_amount"
TYPE = "select.office_plant_plant_type"
MOISTURE = "sensor.office_plant_moisture"
PHOTO = "image.office_plant_photo"


async def test_presets_from_plant_type(hass: HomeAssistant, setup_plant: MockConfigEntry) -> None:
    """The plant starts with its type's presets."""
    assert hass.states.get(TYPE).state == "Monstera"
    assert float(hass.states.get(MIN).state) == 30
    assert float(hass.states.get(WATER).state) == 500
    assert hass.states.get(STATUS).state == "ok"
    assert hass.states.get(MOISTURE).state == "60.0"
    status = hass.states.get(STATUS).attributes
    assert status["scientific_name"] == "Monstera deliciosa"
    assert status["generic_picture"] == "/plant_watering_static/monstera.svg"


async def test_changing_type_applies_presets_and_overrides_stick(
    hass: HomeAssistant, setup_plant: MockConfigEntry
) -> None:
    """Setting the type sets the watering amount; overrides then stay until the type changes."""
    await hass.services.async_call("number", "set_value", {"entity_id": WATER, "value": 750}, blocking=True)
    assert float(hass.states.get(WATER).state) == 750

    await hass.services.async_call("select", "select_option", {"entity_id": TYPE, "option": "Boston Fern"}, blocking=True)
    assert float(hass.states.get(MIN).state) == 50
    assert float(hass.states.get(WATER).state) == 400

    await hass.services.async_call("select", "select_option", {"entity_id": TYPE, "option": "Custom"}, blocking=True)
    assert hass.states.get(TYPE).state == "Custom"
    assert float(hass.states.get(WATER).state) == 400

    # Settings survive a reload
    await hass.services.async_call("number", "set_value", {"entity_id": MIN, "value": 42}, blocking=True)
    await hass.config_entries.async_reload(setup_plant.entry_id)
    await hass.async_block_till_done()
    assert float(hass.states.get(MIN).state) == 42
    assert hass.states.get(TYPE).state == "Custom"


async def test_alert_once_per_dry_spell(hass: HomeAssistant, setup_plant: MockConfigEntry) -> None:
    """Notify when moisture hits the minimum, once, and re-arm after watering."""
    calls = async_mock_service(hass, "notify", "mobile_app_test_phone")
    events = async_capture_events(hass, EVENT_NEEDS_WATER)

    hass.states.async_set(SOIL, "30")
    await hass.async_block_till_done()
    assert hass.states.get(NEEDS_WATER).state == STATE_ON
    assert hass.states.get(STATUS).state == "needs_water"
    assert len(calls) == 1
    assert calls[0].data["title"] == "Water Office Plant"
    assert "Give it about 500 mL" in calls[0].data["message"]
    assert events[0].data["moisture"] == 30

    hass.states.async_set(SOIL, "25")
    hass.states.async_set(SOIL, "32")  # within the re-arm margin
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert hass.states.get(NEEDS_WATER).state == STATE_ON

    hass.states.async_set(SOIL, "70")
    await hass.async_block_till_done()
    assert hass.states.get(NEEDS_WATER).state == STATE_OFF

    hass.states.async_set(SOIL, "20")
    await hass.async_block_till_done()
    assert len(calls) == 2


async def test_raising_minimum_triggers_alert(hass: HomeAssistant, setup_plant: MockConfigEntry) -> None:
    """Changing the minimum is re-evaluated straight away."""
    calls = async_mock_service(hass, "notify", "mobile_app_test_phone")
    await hass.services.async_call("number", "set_value", {"entity_id": MIN, "value": 65}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get(NEEDS_WATER).state == STATE_ON
    assert len(calls) == 1


async def test_offline_sensor_is_not_dry(hass: HomeAssistant, setup_plant: MockConfigEntry) -> None:
    """An unavailable soil sensor is reported as offline, never as needing water."""
    calls = async_mock_service(hass, "notify", "mobile_app_test_phone")
    hass.states.async_set(SOIL, STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get(STATUS).state == "sensor_offline"
    assert hass.states.get(NEEDS_WATER).state == STATE_UNAVAILABLE
    assert hass.states.get(MOISTURE).state == STATE_UNAVAILABLE
    assert not calls


async def test_generic_picture(hass: HomeAssistant, hass_client, setup_plant: MockConfigEntry) -> None:
    """The photo shows the plant type's generic picture until a photo is uploaded."""
    client = await hass_client()
    url = hass.states.get(PHOTO).attributes["entity_picture"]
    resp = await client.get(url)
    assert resp.status == 200
    assert resp.content_type == "image/svg+xml"
    assert b"<svg" in await resp.read()

    resp = await client.get("/plant_watering_static/fern.svg")
    assert resp.status == 200
