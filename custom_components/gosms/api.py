"""GoSMS RU API client."""
from __future__ import annotations

import aiohttp
import logging
from typing import Any

from .const import API_ENDPOINT_DEVICES, API_ENDPOINT_SMS, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class GoSMSAuthError(Exception):
    """Raised when the API key is invalid or unauthorized."""


class GoSMSConnectionError(Exception):
    """Raised when the API is unreachable."""


class GoSMSApiError(Exception):
    """Raised for unexpected API errors."""


class GoSMSApiClient:
    """Async client for the GoSMS RU REST API."""

    def __init__(self, api_key: str, session: aiohttp.ClientSession) -> None:
        self._api_key = api_key
        self._session = session

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def get_devices(self) -> list[dict[str, Any]]:
        """Fetch all devices from the GoSMS RU API."""
        try:
            async with self._session.get(
                API_ENDPOINT_DEVICES,
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise GoSMSAuthError("Invalid API key")
                if response.status != 200:
                    text = await response.text()
                    raise GoSMSApiError(
                        f"Unexpected status {response.status}: {text}"
                    )
                return await response.json()
        except aiohttp.ClientConnectorError as err:
            raise GoSMSConnectionError(f"Cannot connect to GoSMS RU API: {err}") from err
        except aiohttp.ClientError as err:
            raise GoSMSConnectionError(f"GoSMS RU API request failed: {err}") from err

    async def send_sms(
        self,
        phone: str,
        message: str,
        device_id: str | None = None,
        no_store: bool = False,
    ) -> dict[str, Any]:
        """Send an SMS via the GoSMS RU API."""
        payload: dict[str, Any] = {
            "phone": phone,
            "message": message,
            "no_store": no_store,
        }
        if device_id:
            payload["device_id"] = device_id

        try:
            async with self._session.post(
                API_ENDPOINT_SMS,
                headers=self._headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise GoSMSAuthError("Invalid API key")
                if response.status not in (200, 201):
                    text = await response.text()
                    raise GoSMSApiError(
                        f"SMS send failed with status {response.status}: {text}"
                    )
                return await response.json()
        except aiohttp.ClientConnectorError as err:
            raise GoSMSConnectionError(f"Cannot connect to GoSMS RU API: {err}") from err
        except aiohttp.ClientError as err:
            raise GoSMSConnectionError(f"GoSMS RU API request failed: {err}") from err
