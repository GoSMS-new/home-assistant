"""Config flow for GoSMS RU integration."""
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
    """Handle the GoSMS RU config flow."""

    VERSION = 1

    async def _async_validate_api_key(self, api_key: str) -> dict[str, str]:
        """Validate the API key with a real API call. Returns errors dict."""
        errors: dict[str, str] = {}
        session = async_get_clientsession(self.hass)
        client = GoSMSApiClient(api_key, session)

        try:
            devices = await client.get_devices()
            _LOGGER.info(
                "GoSMS RU config flow: validated API key, found %d device(s)",
                len(devices),
            )
        except GoSMSAuthError:
            errors["base"] = ERROR_INVALID_AUTH
        except GoSMSConnectionError:
            errors["base"] = ERROR_CANNOT_CONNECT
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error during GoSMS RU config flow")
            errors["base"] = ERROR_UNKNOWN

        return errors

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            errors = await self._async_validate_api_key(api_key)

            if not errors:
                # Unique ID prevents duplicate entries
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="GoSMS RU",
                    data={CONF_API_KEY: api_key},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth requested by ConfigEntryAuthFailed (просроченный/отозванный ключ)."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask the user for a new API key and update the existing entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            errors = await self._async_validate_api_key(api_key)

            if not errors:
                entry = self.hass.config_entries.async_get_entry(
                    self.context["entry_id"]
                )
                if entry is not None:
                    self.hass.config_entries.async_update_entry(
                        entry, data={CONF_API_KEY: api_key}
                    )
                    await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
