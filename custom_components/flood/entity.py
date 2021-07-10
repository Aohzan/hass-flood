"""Support for the generic Flood entity."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class FloodEntity(CoordinatorEntity):
    """Representation of a Flood generic entity."""

    def __init__(
        self,
        controller,
        coordinator,
        name: str,
        category: str = None,
        key: str = None,
        icon: str = None,
        attributes: dict = None,
        max_speed_limit: int = 0,
    ):
        """Initialize the entity."""
        super().__init__(coordinator)
        self._controller = controller
        self._name = f"Flood {name}"
        self._category = category
        self._key = key
        self._icon = icon
        self._attributes = attributes
        self._max_speed_limit = max_speed_limit

    @property
    def device_info(self):
        """Return device information identifier."""
        return {
            "identifiers": {(DOMAIN, self._controller.host)},
            "via_device": (DOMAIN, self._controller.host),
        }

    @property
    def unique_id(self):
        """Return an unique id."""
        return "_".join(
            [
                DOMAIN,
                self._controller.host,
                self._name,
            ]
        )

    @property
    def name(self):
        """Return the name."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self._icon
