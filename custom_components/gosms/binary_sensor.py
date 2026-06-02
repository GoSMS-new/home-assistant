"""Binary sensor platform for GoSMS RU — device online/offline and charging."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GoSMSCoordinator
from .sensor import _device_display_name

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="is_online",
        name="Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key="is_charging",
        name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
    BinarySensorEntityDescription(
        key="can_send_sms",
        name="SMS Sending Enabled",
        icon="mdi:message-check",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GoSMS RU binary sensor entities from a config entry."""
    coordinator: GoSMSCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[GoSMSBinarySensor] = []
    if coordinator.data:
        for device in coordinator.data:
            for description in BINARY_SENSOR_DESCRIPTIONS:
                entities.append(
                    GoSMSBinarySensor(coordinator, device["id"], description)
                )

    async_add_entities(entities)


class GoSMSBinarySensor(CoordinatorEntity[GoSMSCoordinator], BinarySensorEntity):
    """A binary sensor entity for a GoSMS RU device boolean metric."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GoSMSCoordinator,
        device_id: str,
        description: BinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def _device(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        return next(
            (d for d in self.coordinator.data if d["id"] == self._device_id), None
        )

    @property
    def device_info(self) -> DeviceInfo:
        device = self._device or {}
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=_device_display_name(device),
            manufacturer="GoSMS RU",
            model=device.get("type", "Android"),
            configuration_url="https://my.gosms.ru",
        )

    @property
    def is_on(self) -> bool | None:
        device = self._device
        if device is None:
            return None
        return bool(device.get(self.entity_description.key, False))

    @property
    def available(self) -> bool:
        return super().available and self._device is not None
