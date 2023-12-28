"""Support for the Flood select."""

from homeassistant.components.select import SelectEntity
from homeassistant.const import UnitOfDataRate

from .const import CONTROLLER, COORDINATOR, DOMAIN
from .entity import FloodEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Flood platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    cont = data[CONTROLLER]
    cdnt = data[COORDINATOR]

    entities = [
        FloodSpeedLimitEntity(
            cont,
            cdnt,
            "Download Limit",
            "client_settings",
            "throttleGlobalDownSpeed",
            "mdi:download-lock",
        ),
        FloodSpeedLimitEntity(
            cont,
            cdnt,
            "Upload Limit",
            "client_settings",
            "throttleGlobalUpSpeed",
            "mdi:upload-lock",
        ),
    ]

    async_add_entities(entities, True)


class FloodSpeedLimitEntity(FloodEntity, SelectEntity):
    """Representation of a Flood speed limit entity."""

    @property
    def unit_of_measurement(self) -> str:
        """Return the icon to use in the frontend."""
        return UnitOfDataRate.KILOBYTES_PER_SECOND

    @property
    def current_option(self):
        """Return the state."""
        byte_value = float(self.coordinator.data.get(self._category, {}).get(self._key))
        return str(round(byte_value / 1024))

    @property
    def options(self):
        """Return list of speed limit set in Flood settings."""
        byte_value = float(self.coordinator.data.get(self._category, {}).get(self._key))
        current = round(byte_value / 1024)

        options = []
        if self.coordinator.data.get("settings"):
            limits = self.coordinator.data["settings"].get("speedLimits", {})
            if self._key == "throttleGlobalDownSpeed":
                options = [round(number / 1024) for number in limits.get("download")]
            elif self._key == "throttleGlobalUpSpeed":
                options = [round(number / 1024) for number in limits.get("upload")]

        if current not in options:
            options.append(current)

        options.sort()

        return [str(i) for i in options]

    async def async_select_option(self, option: str) -> None:
        """Update the current value."""
        speed = int(option)
        if self._key == "throttleGlobalDownSpeed":
            await self._controller.set_download_limit(speed)
        elif self._key == "throttleGlobalUpSpeed":
            await self._controller.set_upload_limit(speed)
        await self.coordinator.async_request_refresh()
