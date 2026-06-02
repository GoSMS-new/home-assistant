"""Notify platform for GoSMS RU — send SMS from automations."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GoSMSCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GoSMS RU notify entity."""
    coordinator: GoSMSCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([GoSMSNotifyEntity(coordinator, config_entry.entry_id)])


class GoSMSNotifyEntity(NotifyEntity):
    """Notify entity that sends SMS via GoSMS RU.

    Usage in automations:
        service: notify.gosms_send_sms
        data:
          message: "Your code: 1234"
          target: "+79001234567"           # phone number (required)
          data:
            device_id: "uuid-of-device"   # optional: specific device
            no_store: false               # optional: skip history
    """

    _attr_has_entity_name = True
    _attr_name = "Send SMS"
    _attr_supported_features = NotifyEntityFeature.TITLE

    def __init__(self, coordinator: GoSMSCoordinator, entry_id: str) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_notify"

    async def async_send_message(
        self,
        message: str,
        title: str | None = None,
        target: list[str] | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Send SMS.

        Args:
            message: SMS text body.
            title: Unused (HA notify convention).
            target: List of phone numbers to send to.
            data:
                device_id (str): Optional device UUID to send from.
                no_store (bool): If True, SMS won't be saved in GoSMS RU history.
        """
        data = data or {}
        device_id: str | None = data.get("device_id")
        no_store: bool = bool(data.get("no_store", False))

        phones = target or []
        if not phones:
            _LOGGER.error(
                "GoSMS RU notify: no target phone number provided. "
                "Set 'target' to a list of phone numbers."
            )
            return

        for phone in phones:
            try:
                result = await self._coordinator.client.send_sms(
                    phone=phone,
                    message=message,
                    device_id=device_id,
                    no_store=no_store,
                )
                _LOGGER.info(
                    "GoSMS RU: SMS sent to %s, message id=%s, status=%s",
                    phone,
                    result.get("id"),
                    result.get("status"),
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("GoSMS RU: failed to send SMS to %s: %s", phone, err)
