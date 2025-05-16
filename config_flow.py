"""Config flow for Planned Blackouts integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PlannedBlackoutsApiClient
from .const import (
    CONF_API_TOKEN,
    CONF_BILL_ID,
    CONF_DAYS_AHEAD,
    CONF_POLLING_INTERVAL,
    DEFAULT_DAYS_AHEAD,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
    MAX_DAYS_AHEAD,
    MIN_POLLING_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BILL_ID): str,
        vol.Required(CONF_API_TOKEN): str,
        vol.Optional(CONF_DAYS_AHEAD, default=DEFAULT_DAYS_AHEAD): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=MAX_DAYS_AHEAD)
        ),
        vol.Optional(CONF_POLLING_INTERVAL, default=DEFAULT_POLLING_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_POLLING_INTERVAL)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Validate the API token and bill ID by making a test API call
    api = PlannedBlackoutsApiClient(
        async_get_clientsession(hass),
        data[CONF_API_TOKEN],
        data[CONF_BILL_ID],
    )
    
    try:
        # Test API connection with a minimal date range
        from datetime import datetime, timedelta
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        await api.async_get_outages(today, tomorrow)
    except ConfigEntryAuthFailed as exception:
        raise InvalidAuth from exception
    except Exception as exception:
        raise CannotConnect from exception

    # Return info that you want to store in the config entry.
    return {"title": f"SAAPA Bill ID: {data[CONF_BILL_ID]}"}


class PlannedBlackoutsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Planned Blackouts."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
    
    async def async_step_reauth(self, user_input=None):
        """Handle re-authentication with SAAPA."""
        errors = {}
        
        if user_input is not None:
            try:
                # Validate the new token
                info = await validate_input(self.hass, user_input)
                
                # Update the config entry with the new token
                existing_entry = self.hass.config_entries.async_get_entry(
                    self.context["entry_id"]
                )
                self.hass.config_entries.async_update_entry(
                    existing_entry, 
                    data={**existing_entry.data, CONF_API_TOKEN: user_input[CONF_API_TOKEN]}
                )
                
                return self.async_abort(reason="reauth_successful")
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        
        return self.async_show_form(
            step_id="reauth",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): str}),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
