"""Config flow for GoSMS integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GoSMSApiClient, GoSMSAuthError, GoSMSConnectionError
from .const import CONF_API_KEY, DOMAIN, ERROR_CANNOT_CONNECT, ERROR_INVALID_AUTH, ERROR_UNKNOWN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


class GoSMSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the GoSMS config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()

            # Validate the API key by making a real API call
            session = async_get_clientsession(self.hass)
            client = GoSMSApiClient(api_key, session)

            try:
                devices = await client.get_devices()
                _LOGGER.info(
                    "GoSMS config flow: validated API key, found %d device(s)",
                    len(devices),
                )
            except GoSMSAuthError:
                errors["base"] = ERROR_INVALID_AUTH
            except GoSMSConnectionError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during GoSMS config flow")
                errors["base"] = ERROR_UNKNOWN
            else:
                # Unique ID prevents duplicate entries
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="GoSMS",
                    data={CONF_API_KEY: api_key},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
