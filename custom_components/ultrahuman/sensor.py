"""Sensor platform for Ultrahuman Ring integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import UltrahumanApiClient
from .const import (
    CONF_API_TOKEN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Sensor definitions: (name, metric_type, value_key)
SENSORS: tuple[tuple[str, str, str], ...] = (
    ("Night Resting HR", "night_rhr", "avg"),
    ("Sleep HRV", "avg_sleep_hrv", "value"),
    ("Sleep RHR", "sleep_rhr", "value"),
    ("Recovery Index", "recovery_index", "value"),
    ("Movement Index", "movement_index", "value"),
    ("Active Minutes", "active_minutes", "value"),
    ("VO2 Max", "vo2_max", "value"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ultrahuman sensors from a config entry."""
    client = UltrahumanApiClient(entry.data[CONF_API_TOKEN])
    update_interval = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Ultrahuman Ring",
        update_method=client.async_get_metrics,
        update_interval=timedelta(minutes=update_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    async_add_entities(
        UltrahumanSensor(entry.entry_id, coordinator, name, metric_type, value_key)
        for name, metric_type, value_key in SENSORS
    )


class UltrahumanSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Ultrahuman sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        coordinator: DataUpdateCoordinator,
        name: str,
        metric_type: str,
        value_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._metric_type = metric_type
        self._value_key = value_key
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{metric_type}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, "ultrahuman_ring")},
            name="Ultrahuman Ring",
            manufacturer="Ultrahuman",
            model="Ring AIR",
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        if not self.coordinator.data:
            return None

        metrics_by_day = self.coordinator.data.get("metrics", {})
        if not metrics_by_day:
            return None

        # Get the first available day's metrics
        day_key = next(iter(metrics_by_day), None)
        if not day_key:
            return None

        metrics = metrics_by_day.get(day_key, [])
        metric = next(
            (m for m in metrics if m.get("type") == self._metric_type),
            None,
        )

        if not metric:
            return None

        return metric.get("object", {}).get(self._value_key)