"""Fixtures for Plant Watering tests."""

from __future__ import annotations

import pytest

from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.plant_watering.const import (
    CONF_DAILY_REMINDER,
    CONF_NOTIFY_TARGETS,
    CONF_PLANT_TYPE,
    CONF_REMINDER_TIME,
    CONF_SOIL_SENSOR,
    DOMAIN,
)

SOIL = "sensor.office_plant_soil_moisture"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom integrations in every test."""
    return


@pytest.fixture
def entry() -> MockConfigEntry:
    """A Monstera on the office soil sensor."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Office Plant",
        unique_id=SOIL,
        data={CONF_SOIL_SENSOR: SOIL, CONF_PLANT_TYPE: "monstera", CONF_NAME: "Office Plant"},
        options={
            CONF_NOTIFY_TARGETS: ["notify.mobile_app_test_phone"],
            CONF_DAILY_REMINDER: True,
            CONF_REMINDER_TIME: "09:00:00",
        },
    )


@pytest.fixture
async def setup_plant(hass: HomeAssistant, entry: MockConfigEntry) -> MockConfigEntry:
    """Set up the plant with the soil sensor at 60%."""
    await async_setup_component(hass, "http", {})
    hass.states.async_set(SOIL, "60", {"unit_of_measurement": "%", "device_class": "moisture"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
