"""Switch platform for Indevolt integration."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import IndevoltCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities from a config entry."""
    coordinator: IndevoltCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        [
            GridChargingSwitch(coordinator, config_entry),
        ]
    )


class IndevoltSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Base class for Indevolt switch entities."""

    def __init__(self, coordinator: IndevoltCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self.coordinator = coordinator

        name_suffix = (self._attr_name or "").replace(" ", "_").lower()
        self._attr_unique_id = f"{config_entry.entry_id}_{name_suffix}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        if self.coordinator.data:
            value = self._get_switch_state()
            return bool(value) if value is not None else None
        return None

    def _get_write_cjson_point(self) -> str:
        """Get the cJson Point for writing to this entity."""
        raise NotImplementedError

    def _get_switch_state(self) -> bool:
        """Get the current switch state for this entity."""
        raise NotImplementedError

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        try:
            await self.coordinator.async_push_data(self._get_write_cjson_point(), 1)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on %s: %s", self.name, err)
            raise

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        try:
            await self.coordinator.async_push_data(self._get_write_cjson_point(), 0)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off %s: %s", self.name, err)
            raise


class GridChargingSwitch(IndevoltSwitchEntity):
    """Switch for Grid Charging."""

    _attr_name = "Grid Charging"
    _attr_icon = "mdi:transmission-tower"

    def _get_write_cjson_point(self) -> str:
        """Get the cJson Point for writing Grid Charging state."""
        return "1143"

    def _get_switch_state(self) -> bool:
        """Get the current switch state for this entity."""
        val = self.coordinator.data.get("2618")
        return val != 1000


"""Switch for enabling / disabling Bypass."""
"""Placeholder: The read point for this sensor is still unclear"""
"""class Bypasswitch(IndevoltSwitchEntity):

    _attr_name = "Bypass"
    _attr_icon = "mdi:transmission-tower"

    def _get_write_cjson_point(self) -> str:
        return "7266"

    def _get_switch_state(self) -> bool:
        val = self.coordinator.data.get("2618")
        return val != 1000 """


"""Switch for enabling / disabling LED light."""
"""Placeholder: The read point for this sensor is still unclear"""
"""class Bypasswitch(IndevoltSwitchEntity):

    _attr_name = "Light Indicator"
    _attr_icon = "mdi:light"

    def _get_write_cjson_point(self) -> str:
        return "7265"

    def _get_switch_state(self) -> bool:
        val = self.coordinator.data.get("2618")
        return val != 1000 """
