"""Peblar EV charger component."""

import logging

from awesomeversion import AwesomeVersion
import pypeblar

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_TOKEN,
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    __version__ as HA_VERSION,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_SCAN_INTERVAL_WHILE_CHARGING, DOMAIN, MIN_HA_VERSION, PLATFORMS
from .coordinator import PeblarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Peblar component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Peblar integration from a config entry."""
    current = AwesomeVersion(HA_VERSION)
    req_min = AwesomeVersion(MIN_HA_VERSION)
    if current < req_min:
        _LOGGER.error(
            "Integration requires Home Assistant version %s or later", req_min
        )
        return False

    _LOGGER.debug("Setting up Peblar component")

    coordinator = PeblarDataUpdateCoordinator(
        hass,
        entry,
        entry.data[CONF_SCAN_INTERVAL],
        entry.data[CONF_SCAN_INTERVAL_WHILE_CHARGING],
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
