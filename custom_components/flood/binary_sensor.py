"""Support for the Flood binary_sensors."""
import logging

from .const import CONTROLLER, COORDINATOR, DOMAIN
from .entity import FloodEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Flood platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    cont = data[CONTROLLER]
    cdnt = data[COORDINATOR]

    entities = [
        FloodConnectedEntity(cont, cdnt, "Backend connection", "connected", "status"),
    ]

    async_add_entities(entities, True)


class FloodConnectedEntity(FloodEntity):
    """Representation of a Flood sensor."""

    @property
    def device_class(self):
        """Return the icon to use in the frontend."""
        return "connectivity"

    @property
    def state(self):
        """Return the state."""
        if self.coordinator.data.get(self._category):
            return self.coordinator.data[self._category].get(self._key)
