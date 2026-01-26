"""Number platform for Indevolt integration."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Final

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import IndevoltCoordinator, IndevoltConfigEntry
from .entity import IndevoltEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class IndevoltNumberEntityDescription(NumberEntityDescription):
    """Custom entity description class for Indevolt number entities."""

    read_key: str
    write_key: str
    generation: list[int] = field(default_factory=lambda: [1, 2])


NUMBERS: Final = (
    IndevoltNumberEntityDescription(
        key="discharge_limit",
        generation=[2],
        translation_key="discharge_limit",
        read_key="6105",
        write_key="1142",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
    ),
    IndevoltNumberEntityDescription(
        key="max_ac_output_power",
        generation=[2],
        translation_key="max_ac_output_power",
        read_key="11011",
        write_key="1147",
        native_min_value=0,
        native_max_value=2400,
        native_step=100,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    IndevoltNumberEntityDescription(
        key="inverter_input_limit",
        generation=[2],
        translation_key="inverter_input_limit",
        read_key="11009",
        write_key="1138",
        native_min_value=100,
        native_max_value=2400,
        native_step=100,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    IndevoltNumberEntityDescription(
        key="feedin_power_limit",
        generation=[2],
        translation_key="feedin_power_limit",
        read_key="11010",
        write_key="1146",
        native_min_value=100,
        native_max_value=2400,
        native_step=100,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IndevoltConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform for Indevolt."""
    coordinator = entry.runtime_data
    device_gen = coordinator.device_info_data.get("generation", 1)

    # Initialize number values (first fetch)
    initial_keys = [
        description.read_key
        for description in NUMBERS
        if device_gen in description.generation
    ]
    coordinator.set_initial_sensor_keys(initial_keys)
    await coordinator.async_config_entry_first_refresh()

    # Add number entities based on device generation
    async_add_entities(
        [
            IndevoltNumberEntity(coordinator=coordinator, description=description)
            for description in NUMBERS
            if device_gen in description.generation
        ]
    )


class IndevoltNumberEntity(IndevoltEntity, NumberEntity):
    """Represents a number entity for Indevolt devices."""

    entity_description: IndevoltNumberEntityDescription
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: IndevoltCoordinator,
        description: IndevoltNumberEntityDescription,
    ) -> None:
        """Initialize the Indevolt number entity."""
        super().__init__(coordinator, context=description.read_key)

        self.entity_description = description
        self._attr_unique_id = f"{self.serial_number}_{description.key}"

    @property
    def native_value(self) -> int | None:
        """Return the current value."""
        if not self.coordinator.data:
            return None
        
        raw_value = self.coordinator.data.get(self.entity_description.read_key)
        if raw_value is None:
            return None
        
        return int(raw_value)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        try:
            await self.coordinator.async_push_data(
                self.entity_description.write_key, int(value)
            )
            await self.coordinator.async_request_refresh()

        except Exception as err:
            _LOGGER.error(
                "Failed to set %s to %s: %s",
                self.entity_description.key,
                value,
                err,
            )
            raise
