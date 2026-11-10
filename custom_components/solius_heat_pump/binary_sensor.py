"""Aerona compressor running indication."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AeronaConfigEntry
from .entity import AeronaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AeronaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the compressor status entity."""
    async_add_entities([AeronaCompressor(entry, "compressor_running")])


class AeronaCompressor(AeronaEntity, BinarySensorEntity):
    """Indicate whether the reported compressor frequency is positive."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def is_on(self) -> bool:
        """Return whether the compressor is operating."""
        return self.coordinator.data[1] > 0
