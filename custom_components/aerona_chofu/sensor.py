"""Aerona heat pump measurements and operating modes."""

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfFrequency, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AeronaConfigEntry
from .entity import AeronaEntity


@dataclass(frozen=True, kw_only=True)
class AeronaSensorDescription(SensorEntityDescription):
    """Associate a Modbus register and scale with an entity."""

    address: int | None = None
    scale: float = 1


def temperature(
    key: str, address: int, scale: float = 1, *, enabled: bool = True
) -> AeronaSensorDescription:
    """Describe a temperature register."""
    return AeronaSensorDescription(
        key=key,
        address=address,
        scale=scale,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=enabled,
    )


SENSORS = (
    temperature("return_water", 0),
    AeronaSensorDescription(
        key="compressor_frequency",
        address=1,
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    temperature("discharge", 2),
    AeronaSensorDescription(
        key="electrical_power",
        address=3,
        scale=100,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AeronaSensorDescription(
        key="fan_speed",
        address=4,
        scale=10,
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    temperature("defrost", 5),
    temperature("outdoor_air", 6),
    AeronaSensorDescription(
        key="water_pump_speed",
        address=7,
        scale=100,
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    temperature("suction", 8),
    temperature("flow_water", 9),
    AeronaSensorDescription(
        key="selected_mode",
        address=10,
        device_class=SensorDeviceClass.ENUM,
        options=["off", "heating", "cooling"],
    ),
    temperature("zone_1_target", 11, 0.1, enabled=False),
    temperature("zone_2_target", 12, 0.1, enabled=False),
    AeronaSensorDescription(
        key="dhw_mode",
        address=13,
        device_class=SensorDeviceClass.ENUM,
        options=["off", "comfort", "economy", "forced"],
    ),
    temperature("dhw_tank", 16, 0.1),
    temperature("buffer_tank", 18, 0.1),
    temperature("plate_exchanger", 32),
    temperature("indoor_zone_1", 33, 0.1, enabled=False),
    AeronaSensorDescription(
        key="water_delta",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AeronaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for the heat pump."""
    async_add_entities(AeronaSensor(entry, description) for description in SENSORS)


class AeronaSensor(AeronaEntity, SensorEntity):
    """One measurement or selected operating mode."""

    entity_description: AeronaSensorDescription

    def __init__(
        self, entry: AeronaConfigEntry, description: AeronaSensorDescription
    ) -> None:
        """Apply the sensor description."""
        super().__init__(entry, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Hide values for registers the device does not provide."""
        return super().available and self.native_value is not None

    @property
    def native_value(self) -> float | str | None:
        """Decode the latest measurement."""
        description = self.entity_description
        data = self.coordinator.data
        if description.address is None:
            return data[9] - data[0]
        value = data.get(description.address)
        if value is None:
            return None
        if description.options is not None:
            if 0 <= value < len(description.options):
                return description.options[value]
            return None
        return round(value * description.scale, 1)
