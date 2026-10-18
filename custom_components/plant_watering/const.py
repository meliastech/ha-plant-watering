"""Constants for Plant Watering."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "plant_watering"

PLATFORMS: Final = [
    Platform.BINARY_SENSOR,
    Platform.IMAGE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
]

CONF_SOIL_SENSOR: Final = "soil_sensor"
CONF_PLANT_TYPE: Final = "plant_type"
CONF_AREA: Final = "area"
CONF_NOTIFY_TARGETS: Final = "notify_targets"
CONF_DAILY_REMINDER: Final = "daily_reminder"
CONF_REMINDER_TIME: Final = "reminder_time"
CONF_PHOTO: Final = "photo"
CONF_REMOVE_PHOTO: Final = "remove_photo"

DEFAULT_REMINDER_TIME: Final = "09:00:00"
# Moisture has to climb this far above the minimum before the alert re-arms,
# so a sensor hovering around the threshold doesn't send a stream of alerts.
REARM_MARGIN: Final = 3.0

CUSTOM_TYPE: Final = "custom"

STATUS_OK: Final = "ok"
STATUS_NEEDS_WATER: Final = "needs_water"
STATUS_SENSOR_OFFLINE: Final = "sensor_offline"

EVENT_NEEDS_WATER: Final = f"{DOMAIN}_needs_water"

STATIC_URL: Final = f"/{DOMAIN}_static"
PHOTO_DIR: Final = f"{DOMAIN}/photos"
STORAGE_VERSION: Final = 1
