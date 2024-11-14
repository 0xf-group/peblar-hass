"""Diagnostics support for Peblar."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import PeblarDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: PeblarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    info: dict[str, Any] = await coordinator.async_get_diagnostics()
    return info
