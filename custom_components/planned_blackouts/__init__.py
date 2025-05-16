"""The Planned Blackouts integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

import jdatetime
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_API_TOKEN,
    CONF_BILL_ID,
    CONF_DAYS_AHEAD,
    CONF_POLLING_INTERVAL,
    DOMAIN,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# Supported platforms
PLATFORMS = [Platform.CALENDAR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Planned Blackouts from a config entry."""
    # Create API client
    api = PlannedBlackoutsApiClient(
        async_get_clientsession(hass),
        entry.data[CONF_API_TOKEN],
        entry.data[CONF_BILL_ID],
    )

    # Create coordinator
    coordinator = PlannedBlackoutsDataUpdateCoordinator(
        hass,
        entry=entry,
        api=api,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for config entry changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class PlannedBlackoutsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Planned Blackouts data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: PlannedBlackoutsApiClient,
    ) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.api = api
        
        # Calculate update interval from config
        update_interval = timedelta(
            seconds=entry.data.get(CONF_POLLING_INTERVAL, UPDATE_INTERVAL.total_seconds())
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            # Calculate the date range (today to days_ahead)
            from datetime import datetime, timedelta
            today = datetime.now()
            days_ahead = self.entry.data.get(CONF_DAYS_AHEAD, 7)
            end_date = today + timedelta(days=days_ahead)
            
            # Make the API request
            outages = await self.api.async_get_outages(today, end_date)
            
            if not outages:
                return {
                    "outages": [],
                    "next_outage": None,
                    "today_count": 0,
                }
            
            # Process the data for Home Assistant
            today_date = today.date()
            today_count = sum(1 for outage in outages if outage["start"].date() == today_date)
            
            # Find the next upcoming outage
            next_outage = None
            for outage in outages:
                if outage["start"] > today:
                    if next_outage is None or outage["start"] < next_outage["start"]:
                        next_outage = outage
            
            return {
                "outages": outages,
                "next_outage": next_outage,
                "today_count": today_count,
            }
            
        except ConfigEntryAuthFailed as err:
            # Handle authentication errors to trigger reauthentication
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}")
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
