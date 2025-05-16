"""API client for SAAPA Planned Blackouts."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import jdatetime
from aiohttp import ClientSession

from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import API_TIMEOUT, API_URL

_LOGGER = logging.getLogger(__name__)


class PlannedBlackoutsApiClient:
    """API client for SAAPA Planned Blackouts."""

    def __init__(
        self, session: ClientSession, token: str, bill_id: str
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._token = token
        self._bill_id = bill_id

    async def async_get_outages(
        self, from_date: datetime, to_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get planned outages from the API.
        
        Converts dates to Shamsi format, makes the API request,
        and returns processed outage data with Gregorian dates.
        """
        
        # Convert dates to Shamsi format (YYYY/MM/DD)
        from_date_shamsi = self._convert_to_shamsi(from_date)
        to_date_shamsi = self._convert_to_shamsi(to_date)
        
        # Prepare request payload
        payload = {
            "bill_id": self._bill_id,
            "from_date": from_date_shamsi,
            "to_date": to_date_shamsi,
        }
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}",
        }
        
        try:
            async with self._session.post(
                API_URL,
                json=payload,
                headers=headers,
                timeout=API_TIMEOUT,
            ) as response:
                if response.status == 401:
                    raise ConfigEntryAuthFailed("Invalid authentication token")
                
                if response.status != 200:
                    _LOGGER.error(
                        "Error fetching data: %s - %s",
                        response.status,
                        await response.text(),
                    )
                    return []
                
                data = await response.json()
                
                # Process the response
                return self._process_response(data)
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to API: %s", err)
            return []
    
    def _convert_to_shamsi(self, date: datetime) -> str:
        """Convert a Gregorian date to Shamsi format."""
        shamsi_date = jdatetime.date.fromgregorian(date=date.date())
        return shamsi_date.strftime("%Y/%m/%d")
    
    def _convert_from_shamsi(self, date_str: str, time_str: str) -> datetime:
        """Convert Shamsi date and time to Gregorian datetime."""
        shamsi_date = jdatetime.datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M")
        return shamsi_date.togregorian()
    
    def _process_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process the API response and convert dates."""
        outages = []
        
        # Check if data contains the expected structure
        if not data or "data" not in data:
            return outages
        
        for outage in data.get("data", []):
            # Extract all required fields
            outage_date = outage.get("outage_date")
            start_time = outage.get("outage_start_time")
            end_time = outage.get("outage_stop_time")
            reason = outage.get("reason_outage")
            address = outage.get("address")
            outage_number = outage.get("outage_number")
            
            # Skip if any required field is missing
            if not all([outage_date, start_time, end_time]):
                _LOGGER.warning("Skipping outage with missing required fields: %s", outage)
                continue
            
            try:
                # Convert date and times to Gregorian
                start_datetime = self._convert_from_shamsi(outage_date, start_time)
                end_datetime = self._convert_from_shamsi(outage_date, end_time)
                
                processed_outage = {
                    "start": start_datetime,
                    "end": end_datetime,
                    "reason": reason or "Unknown reason",
                    "address": address or "Unknown location",
                    "outage_number": outage_number or "",
                }
                
                outages.append(processed_outage)
            except (ValueError, TypeError) as err:
                _LOGGER.error("Error processing outage data: %s - %s", err, outage)
        
        return outages
