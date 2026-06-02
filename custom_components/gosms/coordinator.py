"""DataUpdateCoordinator for GoSMS."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GoSMSApiClient, GoSMSAuthError, GoSMSConnectionError, GoSMSApiError
from .const import DOMAIN, UPDATE_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class GoSMSCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator that polls the GoSMS API for device data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: GoSMSApiClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch device list from GoSMS API."""
        try:
            devices = await self.client.get_devices()
            _LOGGER.debug("Fetched %d devices from GoSMS", len(devices))
            return devices
        except GoSMSAuthError as err:
            # Auth failure → HA shows "re-auth required" UI automatically
            raise ConfigEntryAuthFailed("GoSMS API key is invalid") from err
        except (GoSMSConnectionError, GoSMSApiError) as err:
            raise UpdateFailed(f"GoSMS API error: {err}") from err
