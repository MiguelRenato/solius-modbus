"""Set up the Modbus transport in the Home Assistant UI."""

import json
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import (
    CONF_BAUDRATE,
    CONF_POLL_INTERVAL,
    CONF_SERIAL_PORT,
    CONF_TRANSPORT,
    CONF_UNIT_ID,
    DOMAIN,
    TRANSPORT_RTU_TCP,
    TRANSPORT_SERIAL,
    TRANSPORT_TCP,
)
from .modbus_client import AeronaModbusClient, AeronaModbusError


class AeronaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure one Solius heat pump."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select how the heat pump is connected."""
        if user_input is not None:
            self._transport = user_input[CONF_TRANSPORT]
            return await self.async_step_connection()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TRANSPORT, default=TRANSPORT_TCP): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                TRANSPORT_TCP,
                                TRANSPORT_RTU_TCP,
                                TRANSPORT_SERIAL,
                            ],
                            translation_key="transport",
                        )
                    )
                }
            ),
        )

    async def async_step_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Check a real Modbus response before creating an entry."""
        errors = {}
        serial = self._transport == TRANSPORT_SERIAL
        if user_input is not None:
            data = {**user_input, CONF_TRANSPORT: self._transport}
            if serial:
                data[CONF_SERIAL_PORT] = data[CONF_SERIAL_PORT].strip()
                endpoint = [data[CONF_SERIAL_PORT]]
                label = data[CONF_SERIAL_PORT]
            else:
                data[CONF_HOST] = data[CONF_HOST].strip().lower()
                endpoint = [data[CONF_HOST], data[CONF_PORT]]
                label = f"{data[CONF_HOST]}:{data[CONF_PORT]}"
            if not endpoint[0]:
                errors["base"] = "invalid_endpoint"
            else:
                unit_id = data[CONF_UNIT_ID]
                # TCP and RTU-over-TCP are alternative framings for the same endpoint.
                unique_id = json.dumps([*endpoint, unit_id])
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                try:
                    client = AeronaModbusClient(data)
                    try:
                        await client.async_read()
                    finally:
                        client.close()
                except (AeronaModbusError, OSError, ValueError):
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                    title=f"Solius Modbus ({label}, ID {unit_id})",
                    data=data,
                    )

        if serial:
            fields = {
                vol.Required(CONF_SERIAL_PORT, default="/dev/ttyUSB0"): cv.string,
                vol.Required(CONF_BAUDRATE, default=19200): vol.All(
                    vol.Coerce(int), vol.Range(min=1200, max=115200)
                ),
                vol.Required("parity", default="N"): vol.In(["N", "E", "O"]),
                vol.Required("stopbits", default=2): vol.All(
                    vol.Coerce(int), vol.In([1, 2])
                ),
            }
        else:
            fields = {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT, default=502): cv.port,
            }

        fields.update(
            {
                vol.Required(CONF_UNIT_ID, default=1): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=247)
                ),
                vol.Required(CONF_POLL_INTERVAL, default=15): vol.All(
                    vol.Coerce(int), vol.Range(min=5, max=300)
                ),
            }
        )
        return self.async_show_form(
            step_id="connection",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(fields), user_input
            ),
            errors=errors,
            last_step=True,
        )
