"""Switch platform for Indevolt integration."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Final

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import IndevoltCoordinator, IndevoltConfigEntry
from .entity import IndevoltEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class IndevoltSwitchEntityDescription(SwitchEntityDescription):
    """Custom entity description class for Indevolt switch entities."""

    read_key: str
    write_key: str
    on_value: int = 1001
    off_value: int = 1000
    generation: list[int] = field(default_factory=lambda: [1, 2])


SWITCHES: Final = (
    IndevoltSwitchEntityDescription(
        key="grid_charging",
        translation_key="grid_charging",
        generation=[2],
        read_key="2618",
        write_key="1143",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IndevoltConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform for Indevolt."""
    coordinator = entry.runtime_data
    device_gen = coordinator.device_info_data.get("generation", 1)

    # Initialize switch values (first fetch)
    initial_keys = [
        description.read_key
        for description in SWITCHES
        if device_gen in description.generation
    ]
    coordinator.set_initial_sensor_keys(initial_keys)
    await coordinator.async_config_entry_first_refresh()

    # Add switch entities based on device generation
    async_add_entities(
        [
            IndevoltSwitchEntity(coordinator=coordinator, description=description)
            for description in SWITCHES
            if device_gen in description.generation
        ]
    )


class IndevoltSwitchEntity(IndevoltEntity, SwitchEntity):
    """Represents a switch entity for Indevolt devices."""

    entity_description: IndevoltSwitchEntityDescription

    def __init__(
        self,
        coordinator: IndevoltCoordinator,
        description: IndevoltSwitchEntityDescription,
    ) -> None:
        """Initialize the Indevolt switch entity."""
        super().__init__(coordinator, context=description.read_key)

        self.entity_description = description
        self._attr_unique_id = f"{self.serial_number}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        if not self.coordinator.data:
            return None

        raw_value = self.coordinator.data.get(self.entity_description.read_key)
        if raw_value is None:
            return None

        # If on_value is specified, check for exact match
        if self.entity_description.on_value is not None:
            return raw_value == self.entity_description.on_value

        # Otherwise, ON means anything except off_value
        return raw_value != self.entity_description.off_value

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        try:
            await self.coordinator.async_push_data(self.entity_description.write_key, 1)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to turn on %s: %s",
                self.entity_description.key,
                err,
            )
            raise

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        try:
            await self.coordinator.async_push_data(self.entity_description.write_key, 0)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to turn off %s: %s",
                self.entity_description.key,
                err,
            )
            raise
