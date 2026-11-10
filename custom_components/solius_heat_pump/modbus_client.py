"""Read and write Solius Modbus registers."""

from collections.abc import Mapping
from typing import Any

from homeassistant.const import CONF_HOST, CONF_PORT
from pymodbus import FramerType
from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    CONF_BAUDRATE,
    CONF_SERIAL_PORT,
    CONF_TRANSPORT,
    CONF_UNIT_ID,
    TRANSPORT_RTU_TCP,
    TRANSPORT_SERIAL,
)

CORE_BLOCK = (0, 10)
OPTIONAL_BLOCKS = ((10, 4), (16, 3), (32, 2))


class AeronaModbusError(Exception):
    """Communication with the heat pump failed."""


class AeronaModbusClient:
    """Own one Modbus session for the heat pump."""

    def __init__(self, config: Mapping[str, Any]) -> None:
        """Create the transport without opening it."""
        transport = config[CONF_TRANSPORT]
        self._unit_id = config[CONF_UNIT_ID]
        if transport == TRANSPORT_SERIAL:
            self._client = AsyncModbusSerialClient(
                config[CONF_SERIAL_PORT],
                baudrate=config[CONF_BAUDRATE],
                bytesize=8,
                parity=config["parity"],
                stopbits=config["stopbits"],
                timeout=3,
                retries=0,
                reconnect_delay=0,
            )
        else:
            self._client = AsyncModbusTcpClient(
                config[CONF_HOST],
                port=config[CONF_PORT],
                framer=FramerType.RTU
                if transport == TRANSPORT_RTU_TCP
                else FramerType.SOCKET,
                timeout=3,
                retries=0,
                reconnect_delay=0,
            )

    def close(self) -> None:
        """Close the transport."""
        self._client.close()

    async def _read(self, address: int, count: int) -> list[int] | None:
        """Return signed values, or None for an illegal register address."""
        response = await self._client.read_input_registers(
            address, count=count, device_id=self._unit_id
        )
        if response.isError():
            if getattr(response, "exception_code", None) == 2:
                return None
            raise AeronaModbusError(f"Input register {address}: {response}")
        if len(response.registers) != count:
            raise AeronaModbusError(f"Incomplete input register response at {address}")
        return [word - 65536 if word >= 32768 else word for word in response.registers]

    async def async_read(self) -> dict[int, int]:
        """Read telemetry, tolerating optional registers missing on some models."""
        try:
            if not self._client.connected and not await self._client.connect():
                raise AeronaModbusError("Could not connect to the Modbus endpoint")

            values = await self._read(*CORE_BLOCK)
            if values is None:
                raise AeronaModbusError("Required input registers 0–9 are unsupported")
            data = dict(enumerate(values))

            for address, count in OPTIONAL_BLOCKS:
                values = await self._read(address, count)
                if values is not None:
                    data.update(enumerate(values, start=address))
                elif count > 1:
                    for register in range(address, address + count):
                        values = await self._read(register, 1)
                        if values is not None:
                            data[register] = values[0]
            return data
        except (OSError, TimeoutError, ModbusException, AeronaModbusError) as err:
            self.close()
            raise AeronaModbusError(str(err)) from err
