"""GoSMS Home Assistant Integration.

Provides:
  - Sensor entities: battery level, active SIM slot per device
  - Binary sensor entities: online status, charging, SMS enabled per device
  - Notify entity: send SMS via automation / service call
  - gosms.send_sms service: rich SMS sending with device targeting
"""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GoSMSApiClient, GoSMSAuthError, GoSMSConnectionError
from .const import CONF_API_KEY, DOMAIN
from .coordinator import GoSMSCoordinator

_LOGGER = logging.getLogger(__name__)

# Platforms that this integration provides
PLATFORMS = ["sensor", "binary_sensor", "notify"]

# Schema for the gosms.send_sms service
SERVICE_SEND_SMS = "send_sms"
SERVICE_SEND_SMS_SCHEMA = vol.Schema(
    {
        vol.Required("phone"): cv.string,
        vol.Required("message"): cv.string,
        vol.Optional("device_id"): cv.string,
        vol.Optional("no_store", default=False): cv.boolean,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GoSMS from a config entry.

    Creates the API client, coordinator, performs first refresh,
    sets up all entity platforms and registers services.
    """
    api_key: str = entry.data[CONF_API_KEY]
    session = async_get_clientsession(hass)
    client = GoSMSApiClient(api_key, session)

    coordinator = GoSMSCoordinator(hass, entry, client)

    # Fetch data once before setting up entities so they have data on boot
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward setup to all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register gosms.send_sms service (callable from automations / scripts)
    async def handle_send_sms(call: ServiceCall) -> None:
        phone: str = call.data["phone"]
        message: str = call.data["message"]
        device_id: str | None = call.data.get("device_id")
        no_store: bool = call.data.get("no_store", False)

        try:
            result = await client.send_sms(
                phone=phone,
                message=message,
                device_id=device_id,
                no_store=no_store,
            )
            _LOGGER.info(
                "GoSMS service: SMS sent to %s, id=%s, status=%s",
                phone,
                result.get("id"),
                result.get("status"),
            )
        except GoSMSAuthError:
            _LOGGER.error(
                "GoSMS service: authentication failed — check your API key "
                "in Settings → Integrations → GoSMS"
            )
        except GoSMSConnectionError as err:
            _LOGGER.error("GoSMS service: connection error: %s", err)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("GoSMS service: unexpected error: %s", err)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_SMS,
        handle_send_sms,
        schema=SERVICE_SEND_SMS_SCHEMA,
    )

    _LOGGER.info(
        "GoSMS integration loaded: %d device(s) found",
        len(coordinator.data) if coordinator.data else 0,
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a GoSMS config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Remove service if no entries left
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SEND_SMS)
    return unload_ok
