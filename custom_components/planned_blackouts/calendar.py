"""Calendar platform for Planned Blackouts integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CALENDAR_NAME, DOMAIN
from . import PlannedBlackoutsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Planned Blackouts calendar platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([PlannedBlackoutsCalendar(coordinator)], True)


class PlannedBlackoutsCalendar(CoordinatorEntity, CalendarEntity):
    """Calendar entity for Planned Blackouts."""

    def __init__(self, coordinator: PlannedBlackoutsDataUpdateCoordinator) -> None:
        """Initialize the calendar entity."""
        super().__init__(coordinator)
        self._attr_name = CALENDAR_NAME
        self._attr_unique_id = f"{coordinator.entry.entry_id}_calendar"
        
    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event."""
        if not self.coordinator.data or not self.coordinator.data.get("outages"):
            return None
        
        now = datetime.now()
        current_or_next_event = None
        
        # Find current or next event
        for outage in self.coordinator.data["outages"]:
            start = outage["start"]
            end = outage["end"]
            
            # Check if this is a current event
            if start <= now <= end:
                current_or_next_event = outage
                break
            
            # Check if this is a future event and earlier than any previously found
            if start > now and (current_or_next_event is None or start < current_or_next_event["start"]):
                current_or_next_event = outage
        
        if current_or_next_event:
            return CalendarEvent(
                start=current_or_next_event["start"],
                end=current_or_next_event["end"],
                summary=f"Power Outage: {current_or_next_event['address']}",
                description=current_or_next_event["reason"],
            )
        
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Get all events in a specific time frame."""
        if not self.coordinator.data or not self.coordinator.data.get("outages"):
            return []
        
        events = []
        for outage in self.coordinator.data["outages"]:
            event_start = outage["start"]
            event_end = outage["end"]
            
            # Check if event is in the requested date range
            if event_end >= start_date and event_start <= end_date:
                events.append(
                    CalendarEvent(
                        start=event_start,
                        end=event_end,
                        summary=f"Power Outage: {outage['address']}",
                        description=outage["reason"],
                    )
                )
        
        return events
