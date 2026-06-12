"""GoSMS RU Home Assistant Integration.

Provides:
  - Sensor entities: battery level, active SIM slot per device
  - Binary sensor entities: online status, charging, SMS enabled per device
  - gosms.send_sms service: SMS sending with device targeting
    (вызывается из автоматизаций и скриптов)
"""
from __future__ import annotations

import logging
from typing import Any

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
PLATFORMS = ["sensor", "binary_sensor"]

# Schema for the gosms.send_sms service
SERVICE_SEND_SMS = "send_sms"


def _coerce_no_store(value: Any) -> bool:
    """Привести no_store к bool.

    Выпадающий список в UI шлёт строки 'store' / 'no_store',
    в YAML-автоматизациях допустимы и обычные true / false.
    """
    if value == "no_store":
        return True
    if value == "store":
        return False
    return cv.boolean(value)


# Лимит длины SMS в GoSMS RU
MESSAGE_MAX_LENGTH = 170

SERVICE_SEND_SMS_SCHEMA = vol.Schema(
    {
        vol.Required("phone"): cv.string,
        vol.Required("message"): vol.All(
            cv.string, vol.Length(min=1, max=MESSAGE_MAX_LENGTH)
        ),
        vol.Optional("device_id"): cv.string,
        vol.Optional("no_store", default=False): _coerce_no_store,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GoSMS RU from a config entry.

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
                "GoSMS RU service: SMS sent to %s, id=%s, status=%s",
                phone,
                result.get("id"),
                result.get("status"),
            )
        except GoSMSAuthError:
            _LOGGER.error(
                "GoSMS RU service: authentication failed — check your API key "
                "in Settings → Integrations → GoSMS RU"
            )
        except GoSMSConnectionError as err:
            _LOGGER.error("GoSMS RU service: connection error: %s", err)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("GoSMS RU service: unexpected error: %s", err)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_SMS,
        handle_send_sms,
        schema=SERVICE_SEND_SMS_SCHEMA,
    )

    _LOGGER.info(
        "GoSMS RU integration loaded: %d device(s) found",
        len(coordinator.data) if coordinator.data else 0,
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a GoSMS RU config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Remove service if no entries left
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SEND_SMS)
    return unload_ok
