"""Solius Modbus integration."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_POLL_INTERVAL, DOMAIN
from .modbus_client import AeronaModbusClient, AeronaModbusError

_LOGGER = logging.getLogger(__name__)
PLATFORMS = (Platform.SENSOR, Platform.BINARY_SENSOR)


class AeronaCoordinator(DataUpdateCoordinator[dict[int, int]]):
    """Poll the heat pump once for all entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Set up the polling interval and client."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=entry.data[CONF_POLL_INTERVAL]),
            always_update=False,
        )
        self.client = AeronaModbusClient(entry.data)

    async def _async_update_data(self) -> dict[int, int]:
        """Fetch a fresh snapshot."""
        try:
            return await self.client.async_read()
        except AeronaModbusError as err:
            raise UpdateFailed(str(err)) from err


type AeronaConfigEntry = ConfigEntry[AeronaCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: AeronaConfigEntry) -> bool:
    """Set up a heat pump configured in the UI."""
    coordinator = AeronaCoordinator(hass, entry)
    entry.async_on_unload(coordinator.client.close)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AeronaConfigEntry) -> bool:
    """Unload all heat pump entities."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
