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

# Имена берутся из переводов по translation_key:
# strings.json / translations → entity.binary_sensor.<translation_key>.name
BINARY_SENSOR_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="is_online",
        translation_key="is_online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key="is_charging",
        translation_key="is_charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
    BinarySensorEntityDescription(
        key="can_send_sms",
        translation_key="can_send_sms",
        icon="mdi:message-check",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GoSMS RU binary sensor entities from a config entry.

    Подписывается на coordinator: устройства, появившиеся в аккаунте
    после запуска HA, тоже получают сущности — без перезагрузки.
    """
    coordinator: GoSMSCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    known_devices: set[str] = set()

    def _add_new_devices() -> None:
        new_entities: list[GoSMSBinarySensor] = []
        for device in coordinator.data or []:
            if device["id"] in known_devices:
                continue
            known_devices.add(device["id"])
            for description in BINARY_SENSOR_DESCRIPTIONS:
                new_entities.append(
                    GoSMSBinarySensor(coordinator, device["id"], description)
                )
        if new_entities:
            async_add_entities(new_entities)

    _add_new_devices()
    config_entry.async_on_unload(coordinator.async_add_listener(_add_new_devices))


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
