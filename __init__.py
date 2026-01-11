"""Home Assistant integration for indevolt device."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_DEVICE_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .const import DOMAIN
from .coordinator import IndevoltCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA_CHARGE = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required("power"): cv.positive_int,
        vol.Required("target_soc"): cv.positive_int,
    }
)

SERVICE_SCHEMA_DISCHARGE = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required("power"): cv.positive_int,
    }
)

STOP_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
    }
)

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]


async def _get_coordinator_from_device(hass: HomeAssistant, device_id: str) -> IndevoltCoordinator:
    """Get coordinator from device ID."""
    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get(device_id)

    if not device_entry:
        raise ServiceValidationError(
            f"Device {device_id} not found",
            translation_domain=DOMAIN,
            translation_key="device_not_found",
        )

    entry_id = next(
        (entry_id for entry_id in device_entry.config_entries if entry_id in hass.data.get(DOMAIN, {})),
        None,
    )

    if not entry_id:
        raise ServiceValidationError(
            f"No config entry found for device {device_id}",
            translation_domain=DOMAIN,
            translation_key="no_config_entry",
        )

    entry = hass.config_entries.async_get_entry(entry_id)
    if not entry or entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            f"Config entry for device {device_id} is not loaded",
            translation_domain=DOMAIN,
            translation_key="integration_not_loaded",
        )

    return hass.data[DOMAIN][entry_id]


async def _ensure_realtime_control_mode(coordinator: IndevoltCoordinator) -> bool:
    """Ensure device is in Real-time Control mode (mode 4) before executing service commands."""
    current_mode = coordinator.data.get("7101")

    if current_mode is None:
        mode_int = -1

    else:
        try:
            mode_int = int(current_mode) if isinstance(current_mode, str) else current_mode

        except (ValueError, TypeError):
            _LOGGER.warning("Invalid energy mode value: %s", current_mode)
            mode_int = -1

    _LOGGER.info("Current energy mode: %s", mode_int)

    if mode_int != 4:
        try:
            _LOGGER.info("Switching to Real-Time Control mode (mode 4)")
            await coordinator.async_push_data("47005", 4)
            await coordinator.async_request_refresh()

        except Exception:
            _LOGGER.exception("Failed to switch to Real-time Control mode")
            return False

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up indevolt from a config entry.

    This is the main setup function called when a config entry is added.
    It initializes the coordinator and sets up platforms.
    """
    hass.data.setdefault(DOMAIN, {})

    try:
        # Setup coordinator and perform initial data refresh
        coordinator = IndevoltCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()

        # Store coordinator (for platform access) and setup platforms
        hass.data[DOMAIN][entry.entry_id] = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Register services only once (when first entry is added)
        if len(hass.data[DOMAIN]) == 1:
            await _async_register_services(hass)

    except Exception as err:
        _LOGGER.exception("Unexpected error occurredduring initial setup")

        # Clean up partially created resources
        if entry.entry_id in hass.data.get(DOMAIN, {}):
            del hass.data[DOMAIN][entry.entry_id]

        raise ConfigEntryNotReady from err

    else:
        return True


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration services."""

    async def charge(call: ServiceCall) -> None:
        """Handle the service call to start charging."""
        device_id = call.data[CONF_DEVICE_ID]
        target_soc = call.data["target_soc"]
        power = call.data["power"]

        coordinator = await _get_coordinator_from_device(hass, device_id)

        # Ensure device is in Real-time Control mode
        if await _ensure_realtime_control_mode(coordinator):
            _LOGGER.info("Charging %s with power: %s, target SOC: %s", device_id, power, target_soc)
            await coordinator.async_push_data("47015", [1, power, target_soc])
            await coordinator.async_request_refresh()

    async def discharge(call: ServiceCall) -> None:
        """Handle the service call to start discharging."""
        device_id = call.data[CONF_DEVICE_ID]
        power = call.data["power"]

        coordinator = await _get_coordinator_from_device(hass, device_id)

        # Validate power based on device generation
        generation = get_device_gen(coordinator.config_entry.data.get("device_model"))
        max_power = 2400 if generation == 2 else 800
        if power > max_power:
            raise ServiceValidationError(
                f"Power {power}W exceeds maximum {max_power}W for generation {generation} devices"
            )

        # Ensure device is in Real-time Control mode
        if await _ensure_realtime_control_mode(coordinator):
            emergency_soc = coordinator.data.get("6105", 10)

            _LOGGER.info("Discharging %s with power: %s, emergency SOC: %s", device_id, power, emergency_soc)
            await coordinator.async_push_data("47015", [2, power, emergency_soc])
            await coordinator.async_request_refresh()

    async def stop(call: ServiceCall) -> None:
        """Handle the service call to stop the battery."""
        device_id = call.data[CONF_DEVICE_ID]

        coordinator = await _get_coordinator_from_device(hass, device_id)

        # Ensure device is in Real-time Control mode
        if await _ensure_realtime_control_mode(coordinator):
            _LOGGER.info("Stopping battery %s", device_id)
            await coordinator.async_push_data("47015", [0, 0, 0])
            await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, "charge", charge, schema=SERVICE_SCHEMA_CHARGE)
    hass.services.async_register(DOMAIN, "discharge", discharge, schema=SERVICE_SCHEMA_DISCHARGE)
    hass.services.async_register(DOMAIN, "stop", stop, schema=SERVICE_SCHEMA_CHARGE)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and clean up resources.

    This is called when the integration is removed or reloaded.
    """
    if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
        return True

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok
