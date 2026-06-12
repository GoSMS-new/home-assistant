"""Sensor platform for GoSMS RU — device battery and status metrics."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SIM_AUTO, SIM_DEFAULT
from .coordinator import GoSMSCoordinator

_LOGGER = logging.getLogger(__name__)

# Sensor descriptions — one per metric we expose per device.
# Имена берутся из переводов по translation_key:
# strings.json / translations → entity.sensor.<translation_key>.name
SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="battery_level",
        translation_key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="sim_slot",
        translation_key="sim_slot",
        icon="mdi:sim",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GoSMS RU sensor entities from a config entry.

    Подписывается на coordinator: устройства, появившиеся в аккаунте
    после запуска HA, тоже получают сущности — без перезагрузки.
    """
    coordinator: GoSMSCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    known_devices: set[str] = set()

    def _add_new_devices() -> None:
        new_entities: list[GoSMSSensor] = []
        for device in coordinator.data or []:
            if device["id"] in known_devices:
                continue
            known_devices.add(device["id"])
            for description in SENSOR_DESCRIPTIONS:
                new_entities.append(
                    GoSMSSensor(coordinator, device["id"], description)
                )
        if new_entities:
            async_add_entities(new_entities)

    _add_new_devices()
    config_entry.async_on_unload(coordinator.async_add_listener(_add_new_devices))


def _sim_slot_label(selected_sim: int) -> str:
    """Convert selected_sim integer to a human-readable label."""
    if selected_sim == SIM_AUTO:
        return "Auto"
    if selected_sim == SIM_DEFAULT:
        return "Default"
    return f"SIM {selected_sim + 1}"


def _device_display_name(device: dict[str, Any]) -> str:
    """Return the best available display name for a device."""
    return device.get("name_custom") or device.get("name") or device["id"]


class GoSMSSensor(CoordinatorEntity[GoSMSCoordinator], SensorEntity):
    """A sensor entity representing one metric of a GoSMS RU device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GoSMSCoordinator,
        device_id: str,
        description: SensorEntityDescription,
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
        sim_cards = device.get("sim_cards", [])
        sim_names = ", ".join(
            s.get("name_operator", f"SIM {s.get('index', '')}") for s in sim_cards
        ) or None

        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=_device_display_name(device),
            manufacturer="GoSMS RU",
            model=device.get("type", "Android"),
            hw_version=sim_names,
            configuration_url="https://my.gosms.ru",
        )

    @property
    def native_value(self) -> Any:
        device = self._device
        if device is None:
            return None

        key = self.entity_description.key
        if key == "battery_level":
            return device.get("battery_level")
        if key == "sim_slot":
            return _sim_slot_label(device.get("selected_sim", SIM_DEFAULT))
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose additional device fields as attributes."""
        device = self._device
        if device is None:
            return {}

        key = self.entity_description.key
        if key == "battery_level":
            return {"is_charging": device.get("is_charging", False)}
        if key == "sim_slot":
            return {
                "sim_cards": [
                    {
                        "slot": s.get("index"),
                        "operator": s.get("name_operator", ""),
                    }
                    for s in device.get("sim_cards", [])
                ]
            }
        return {}

    @property
    def available(self) -> bool:
        """Mark entity unavailable if coordinator has no data for this device."""
        return super().available and self._device is not None
