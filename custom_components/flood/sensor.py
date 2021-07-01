"""Support for the Flood sensors."""
import logging

from homeassistant.const import DATA_RATE_KILOBYTES_PER_SECOND

from .const import CONTROLLER, COORDINATOR, DOMAIN
from .entity import FloodEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Flood platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    cont = data[CONTROLLER]
    cdnt = data[COORDINATOR]

    entities = [
        FloodSpeedSensorEntity(
            cont,
            cdnt,
            "Current Download",
            "history",
            "downloadSpeed",
            "mdi:download",
        ),
        FloodSpeedSensorEntity(
            cont,
            cdnt,
            "Current Upload",
            "history",
            "uploadSpeed",
            "mdi:upload",
        ),
        FloodSensorEntity(
            cont,
            cdnt,
            "Last notification",
            "last_notification",
            "title",
            "mdi:comment-outline",
            attributes=["type", "torrent"],
        ),
        FloodSensorEntity(
            cont,
            cdnt,
            "Torrents",
            "torrents",
            "count",
            "mdi:file",
            attributes=["seeding", "downloading", "completed", "active", "inactive"],
        ),
    ]

    async_add_entities(entities, True)


class FloodSpeedSensorEntity(FloodEntity):
    """Representation of a Flood sensor."""

    @property
    def unit_of_measurement(self) -> str:
        """Return the icon to use in the frontend."""
        return DATA_RATE_KILOBYTES_PER_SECOND

    @property
    def state(self) -> int:
        """Return the state."""
        byte_value = float(self.coordinator.data.get(self._category, {}).get(self._key))
        return int(byte_value / 1024)

    @property
    def state_attributes(self):
        """Return the state attributes."""
        if self._attributes and self.coordinator.data.get(self._category, {}):
            attributes = {}
            for attribute in self._attributes:
                attributes.update(
                    {
                        attribute: self.coordinator.data.get(self._category, {}).get(
                            attribute
                        )
                    }
                )
            return attributes


class FloodSensorEntity(FloodEntity):
    """Representation of a Flood sensor."""

    @property
    def state(self):
        """Return the state."""
        if self.coordinator.data.get(self._category):
            return self.coordinator.data[self._category].get(self._key)

    @property
    def state_attributes(self):
        """Return the state attributes."""
        if self._attributes and self.coordinator.data.get(self._category, {}):
            attributes = {}
            for attribute in self._attributes:
                attributes.update(
                    {
                        attribute: self.coordinator.data.get(self._category, {}).get(
                            attribute
                        )
                    }
                )
            return attributes
