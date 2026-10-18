"""Config and options flows."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.plant_watering.const import DOMAIN

from .conftest import SOIL


async def test_add_plant(hass: HomeAssistant) -> None:
    """Adding a plant creates an entry; the same sensor can't be used twice."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM

    user_input = {"name": "Office Plant", "soil_sensor": SOIL, "plant_type": "peace_lily"}
    with patch("custom_components.plant_watering.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Office Plant"
    assert result["data"]["plant_type"] == "peace_lily"

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_alert_options(hass: HomeAssistant, setup_plant: MockConfigEntry) -> None:
    """Alert settings are saved as options."""
    result = await hass.config_entries.options.async_init(setup_plant.entry_id)
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "alerts"})
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "soil_sensor": SOIL,
            "notify_targets": ["notify.mobile_app_pauls_iphone"],
            "daily_reminder": False,
            "reminder_time": "08:30:00",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert setup_plant.options["notify_targets"] == ["notify.mobile_app_pauls_iphone"]
    assert setup_plant.options["daily_reminder"] is False


async def test_upload_photo(hass: HomeAssistant, hass_client, setup_plant: MockConfigEntry, tmp_path: Path) -> None:
    """An uploaded photo replaces the generic picture, and can be removed again."""
    upload = tmp_path / "my-plant.png"
    upload.write_bytes(b"\x89PNG\r\n\x1a\nfake")

    @contextmanager
    def fake_upload(hass, file_id):
        yield upload

    result = await hass.config_entries.options.async_init(setup_plant.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "photo"})
    with patch("custom_components.plant_watering.config_flow.process_uploaded_file", fake_upload):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"photo": "4f4ea6d2-3d0a-4a39-9a0a-0b4c4a6e8a51"}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    client = await hass_client()
    resp = await client.get(hass.states.get("image.office_plant_photo").attributes["entity_picture"])
    assert resp.content_type == "image/png"
    assert await resp.read() == upload.read_bytes()

    result = await hass.config_entries.options.async_init(setup_plant.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "photo"})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"remove_photo": True})
    await hass.async_block_till_done()
    resp = await client.get(hass.states.get("image.office_plant_photo").attributes["entity_picture"])
    assert resp.content_type == "image/svg+xml"
    assert not list(Path(hass.config.path("plant_watering/photos")).glob("*"))
