"""Common device information for Aerona entities."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AeronaConfigEntry, AeronaCoordinator
from .const import DOMAIN


class AeronaEntity(CoordinatorEntity[AeronaCoordinator]):
    """An entity belonging to the configured heat pump."""

    _attr_has_entity_name = True

    def __init__(self, entry: AeronaConfigEntry, key: str) -> None:
        """Use the config entry's stable identity."""
        super().__init__(entry.runtime_data)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="MigasLAB",
            model="Solius",
            name="Solius",
        )
