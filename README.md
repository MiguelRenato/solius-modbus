# Solius Modbus for Home Assistant

Version: 1.0.0

Custom Home Assistant integration for Solius heat pumps. Add and configure it from the Home Assistant UI.

## Installation

Requires Home Assistant 2025.11 or later.

1. Copy custom_components/aerona_chofu into your Home Assistant configuration directory. The manifest should be at /config/custom_components/aerona_chofu/manifest.json.
2. Restart Home Assistant.
3. Open Settings → Devices & services → Add integration and search for Solius Modbus.
4. Choose the connection type that matches your Modbus adapter.

The package includes a cropped heat pump icon and Solius logo. Home Assistant 2026.3 or later loads these from the integration brand folder. Earlier Home Assistant versions can still use the integration but do not display locally bundled brand images.

| Connection | Configuration |
| --- | --- |
| Modbus TCP | Adapter IP/hostname and TCP port, commonly 502. The gateway converts TCP requests to RTU. |
| Modbus RTU over TCP | Adapter IP/hostname and TCP port in transparent mode, forwarding RTU frames with CRC. |
| Modbus RTU (USB/RS-485) | Serial device path available to Home Assistant. On Linux, prefer a stable /dev/serial/by-id/... path when available. |

The reference project lists Modbus unit ID 1, 19200 baud, 8 data bits, no parity, and 2 stop bits (19200 8N2). Configure network gateways with these serial settings. Use the actual values configured on the heat pump if they have been changed. The default polling interval is 15 seconds.

If Home Assistant already has a modbus connection for this same pump, disable that connection before using this integration on the same bus. With Home Assistant Container, pass the USB serial device through to the container.

## Dashboard layout

The device page lists entities in Home Assistant's standard layout. To group DHW mode and Operating mode in a bordered card like the reference image, import dashboard/aerona3_chofu_solius.yaml as a Lovelace dashboard.

In Home Assistant, open Settings → Dashboards → Add dashboard, create a dashboard, then open its menu and choose Edit dashboard → Raw configuration editor. Add the YAML file's view under the dashboard's views list.

The YAML uses the default entity IDs generated for a new installation. If your entities already existed, Home Assistant may have kept their earlier IDs. In that case, open the entity page and replace the YAML IDs with the IDs shown in your installation.

## Entities

- Flow, return, outdoor, discharge, suction, defrost sensor, plate heat exchanger, DHW tank, and buffer tank temperatures.
- Water temperature difference in °C, calculated as flow temperature minus return temperature.
- Read-only Operating mode and DHW mode sensors. Operating mode is a sensor, not a control.
- Compressor frequency and a compressor-running indication derived from frequency above 0 Hz.
- Electrical power as reported by the heat pump in 100 W increments, plus fan and circulation pump speeds.

DHW tank temperature uses input register 16 with a 0.1 °C scale. Buffer tank temperature uses input register 18 with a 0.1 °C scale. Some optional registers may not be supported on every model. Unsupported optional readings remain unavailable while other sensors continue to update.

The register addresses and scales follow the community Modbus map at https://github.com/aerona-chofu-ashp/modbus/tree/25d44f3a34099ae8ac8ebe6fe0401732df3383e7.
