"""Sensor platform for Indevolt integration."""

from dataclasses import dataclass, field
import logging
from typing import Final

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .utils import get_device_gen

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class IndevoltSensorEntityDescription(SensorEntityDescription):
    """Custom entity description class for Indevolt sensors."""

    coefficient: float = 1.0
    state_mapping: dict[int, str] = field(default_factory=dict)


SENSORS_GEN1: Final = (
    IndevoltSensorEntityDescription(
        key="1664",
        name="DC Input Power1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1665",
        name="DC Input Power2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="2108",
        name="Total AC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1502",
        name="Daily Production",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="1505",
        name="Cumulative Production",
        coefficient=0.001,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="2101",
        name="Total AC Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="2107",
        name="Total AC Input Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="1501",
        name="Total DC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="6000",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="6002",
        name="Battery SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="6004",
        name="Battery Daily Charging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="6005",
        name="Battery Daily Discharging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="6006",
        name="Battery Total Charging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="6007",
        name="Battery Total Discharging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="21028",
        name="Meter Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="7101",
        name="Working mode",
        state_mapping={
            0: "Outdoor Portable",
            1: "Self-consumed Prioritized",
            5: "Charge/Discharge Schedule",
        },
        device_class=SensorDeviceClass.ENUM,
    ),
    IndevoltSensorEntityDescription(
        key="6001",
        name="Battery Charge/Discharge State",
        state_mapping={1000: "Static", 1001: "Charging", 1002: "Discharging"},
        device_class=SensorDeviceClass.ENUM,
    ),
    IndevoltSensorEntityDescription(
        key="7120",
        name="Meter Connection Status",
        state_mapping={1000: "ON", 1001: "OFF"},
        device_class=SensorDeviceClass.ENUM,
    ),
    IndevoltSensorEntityDescription(
        key="serial_number",
        name="Serial Number",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="serial_number",
    ),
)

SENSORS_GEN2: Final = (
    IndevoltSensorEntityDescription(
        key="0",
        name="Serial Number",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="serial_number",
    ),
    # System Operating Information
    IndevoltSensorEntityDescription(
        key="142",
        name="Rated capacity",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="2101",
        name="Total AC Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="2108",
        name="Total AC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Bypass Power
    IndevoltSensorEntityDescription(
        key="667",
        name="Bypass Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Electrical Energy Information
    IndevoltSensorEntityDescription(
        key="2107",
        name="Total AC Output Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="2104",
        name="Total AC Input Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="2105",
        name="Off-grid Output Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="11034",
        name="Bypass Input Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="6004",
        name="Battery Daily Charging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="6005",
        name="Battery Daily Discharging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="6006",
        name="Battery Total Charging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="6007",
        name="Battery Total Discharging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # Electricity Meter Status
    IndevoltSensorEntityDescription(
        key="7120",
        name="Meter Connection Status",
        state_mapping={1000: "ON", 1001: "OFF"},
        device_class=SensorDeviceClass.ENUM,
    ),
    IndevoltSensorEntityDescription(
        key="11016",
        name="Meter Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Grid information
    IndevoltSensorEntityDescription(
        key="2600",
        name="Grid Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="2612",
        name="Grid Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Battery Pack Operating Parameters
    IndevoltSensorEntityDescription(
        key="6000",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="6001",
        name="Battery Charge/Discharge State",
        state_mapping={1000: "Static", 1001: "Charging", 1002: "Discharging"},
        device_class=SensorDeviceClass.ENUM,
    ),
    # PV Operating Parameters
    IndevoltSensorEntityDescription(
        key="1501",
        name="Total DC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1502",
        name="Daily PV Production",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IndevoltSensorEntityDescription(
        key="1632",
        name="DC Input Current 1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1600",
        name="DC Input Voltage 1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1664",
        name="DC Input Power 1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1633",
        name="DC Input Current 2",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1601",
        name="DC Input Voltage 2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1665",
        name="DC Input Power 2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1634",
        name="DC Input Current 3",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1602",
        name="DC Input Voltage 3",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1666",
        name="DC Input Power 3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1635",
        name="DC Input Current 4",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1603",
        name="DC Input Voltage 4",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1667",
        name="DC Input Power 4",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform for Indevolt.

    This function is called by Home Assistant when the integration is set up.
    It creates sensor entities for each defined sensor description.
    """
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    if get_device_gen(coordinator.config_entry.data.get("device_model")) == 1:
        for description in SENSORS_GEN1:
            entities.extend([IndevoltSensorEntity(coordinator=coordinator, description=description)])
    else:
        for description in SENSORS_GEN2:
            entities.extend([IndevoltSensorEntity(coordinator=coordinator, description=description)])

    async_add_entities(entities)


class IndevoltSensorEntity(CoordinatorEntity, SensorEntity):
    """Represents a sensor entity for Indevolt devices."""

    _attr_has_entity_name = True
    entity_description: IndevoltSensorEntityDescription

    def __init__(self, coordinator, description: IndevoltSensorEntityDescription) -> None:
        """Initialize the Indevolt sensor entity."""
        super().__init__(coordinator)

        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

        if description.device_class == SensorDeviceClass.ENUM:
            self._attr_options = list(set(description.state_mapping.values()))

    @property
    def native_value(self):
        """Return the current value of the sensor in its native unit."""
        raw_value = self.coordinator.data.get(self.entity_description.key)

        if raw_value is None:
            return None

        if self.entity_description.entity_category == EntityCategory.DIAGNOSTIC:
            return raw_value

        if self.entity_description.device_class == SensorDeviceClass.ENUM:
            return self.entity_description.state_mapping.get(raw_value)

        return raw_value * self.entity_description.coefficient
