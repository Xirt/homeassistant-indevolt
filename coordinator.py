"""Home Assistant integration for indevolt device."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .indevolt_api import IndevoltAPI, TimeOutException
from .utils import get_device_gen

_LOGGER = logging.getLogger(__name__)


class IndevoltCoordinator(DataUpdateCoordinator):
    """Coordinator for fetching and pushing data to indevolt devices.

    This coordinator manages periodic data updates from indevolt devices and
    handles writing data back to the device.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the indevolt coordinator.

        Args:
            hass: Home Assistant instance.
            config: Configuration dictionary with host, port, and scan_interval.
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)),
        )
        self.config_entry = entry
        self.session = async_get_clientsession(hass)

        # Initialize Indevolt API.
        self.api = IndevoltAPI(
            host=entry.data["host"],
            port=entry.data["port"],
            session=async_get_clientsession(self.hass),
        )

    @property
    def config(self) -> dict:
        """Helper to access combined config data and options."""
        return {**self.config_entry.data, **self.config_entry.options}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for entities."""
        sn = self.config_entry.data.get("sn", "unknown")
        model = self.config_entry.data.get("device_model", "unknown")

        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            manufacturer="INDEVOLT",
            name=f"INDEVOLT {model}",
            serial_number=sn,
            model=model,
            sw_version=self.config_entry.data.get("fw_version", "unknown"),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch raw JSON data from the device."""
        try:
            if get_device_gen(self.config["device_model"]) == 1:
                keys = [0, 7101, 1664, 1665, 2108, 1502, 1505, 2101, 2107, 1501, 6000, 6001, 6002, 6105, 6004, 6005, 6006, 6007, 7120, 21028]  # fmt: skip
            else:
                keys = [0, 7101, 142, 6105, 2618, 11009, 2101, 2108, 11010, 2108, 667, 2107, 2104, 2105, 11034, 1502, 6004, 6005, 6006, 6007, 7120, 11016, 2600, 2612, 6001, 6000, 6002, 1502, 1501, 1532, 1600, 1632, 1664, 1633, 1601, 1665, 1634, 1602, 1666, 1635, 1603, 1667, 11011, 9012, 9030, 9049, 9068, 9163, 9216]  # fmt: skip

            data: dict[str, Any] = {}
            for key in keys:
                result = await self.api.fetch_data([key])
                data.update(result)

        except TimeOutException as err:
            _LOGGER.warning("Device update timed out: %s", err)
            raise UpdateFailed(f"Update timed out: {err}") from err

        except Exception as err:
            _LOGGER.exception("Failed to update device data")
            raise UpdateFailed(f"Update failed: {err}") from err

        else:
            return data

    async def async_push_data(self, cjson_point: str, value: Any) -> dict[str, Any]:
        """Push/write data to device.

        Args:
            cjson_point: cJson Point identifier (e.g., "47015")
            value: Value to write (will be converted to list if needed)

        Example:
            await coordinator.async_push_data("47015", [2,700,5])
            await coordinator.async_push_data("47005", 100)
        """
        try:
            result = await self.api.set_data(cjson_point, value)

        except Exception:
            _LOGGER.exception("Failed to push data to device for sensor %s", cjson_point)
            raise

        else:
            _LOGGER.info("Data pushed to device %s: %s", cjson_point, value)
            _LOGGER.info("Result of push: %s", str(result))
            return result
