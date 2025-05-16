"""Sensor platform for Planned Blackouts integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_OUTAGE_ADDRESS,
    ATTR_OUTAGE_END,
    ATTR_OUTAGE_NUMBER,
    ATTR_OUTAGE_REASON,
    DOMAIN,
    SENSOR_NEXT_OUTAGE,
    SENSOR_TODAY_COUNT,
)
from . import PlannedBlackoutsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key=SENSOR_NEXT_OUTAGE,
        name="Next Planned Outage",
        icon="mdi:flash-off",
    ),
    SensorEntityDescription(
        key=SENSOR_TODAY_COUNT,
        name="Today's Planned Outages",
        icon="mdi:calendar-today",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Planned Blackouts sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for description in SENSOR_DESCRIPTIONS:
        entities.append(PlannedBlackoutsSensor(coordinator, description))
    
    async_add_entities(entities, True)


class PlannedBlackoutsSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Planned Blackouts sensor."""

    def __init__(
        self,
        coordinator: PlannedBlackoutsDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_name = description.name
        
    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
            
        if self.entity_description.key == SENSOR_NEXT_OUTAGE:
            # Return the start time of the next outage
            next_outage = self.coordinator.data.get("next_outage")
            if next_outage:
                return next_outage["start"].isoformat()
            return None
            
        elif self.entity_description.key == SENSOR_TODAY_COUNT:
            # Return the count of today's outages
            return self.coordinator.data.get("today_count", 0)
            
        return None
        
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attrs = {}
        
        # Only add attributes for the next outage sensor
        if (
            self.entity_description.key == SENSOR_NEXT_OUTAGE
            and self.coordinator.data
            and self.coordinator.data.get("next_outage")
        ):
            next_outage = self.coordinator.data["next_outage"]
            attrs[ATTR_OUTAGE_END] = next_outage["end"].isoformat()
            attrs[ATTR_OUTAGE_REASON] = next_outage["reason"]
            attrs[ATTR_OUTAGE_ADDRESS] = next_outage["address"]
            attrs[ATTR_OUTAGE_NUMBER] = next_outage["outage_number"]
            
        return attrs
