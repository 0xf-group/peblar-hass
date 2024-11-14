import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PeblarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Peblar sensors from a config entry."""
    coordinator: PeblarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors: list[SensorEntity] = coordinator.sensors
    async_add_entities(sensors, update_before_add=True)
    _LOGGER.debug("Added sensors for Peblar integration")
