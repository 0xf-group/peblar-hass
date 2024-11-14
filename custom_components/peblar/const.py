"""Peblar EV Charger constants"""

from homeassistant.const import Platform

DOMAIN = "peblar"

MANUFACTURER = "Peblar"

PLATFORMS = [Platform.SENSOR]

MIN_HA_VERSION = "2024.10.0"

SUPPORTED_PEBLAR_API_VERSION = "1.0"

DEFAULT_FRIENDLY_NAME = "Peblar EV Charger"
DEFAULT_SCAN_INTERVAL = 15
DEFAULT_SCAN_INTERVAL_WHILE_CHARGING = 1

CONF_SCAN_INTERVAL_WHILE_CHARGING = "scan_interval_while_charging"

DATA_COORDINATOR = "coordinator"
DATA_PEBLAR_CLIENT = "client"
DATA_PEBLAR_URL = "url"
