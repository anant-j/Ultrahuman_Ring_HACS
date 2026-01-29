from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import aiohttp

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)
DOMAIN = "ultrahuman"

API_URL = "https://partner.ultrahuman.com/api/v1/partner/daily_metrics"


def iso_from_epoch(ts: int | None, tz: str | None) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(
            ts,
            tz=ZoneInfo(tz) if tz else None,
        ).isoformat()
    except Exception:
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    api_token = entry.data["api_token"]

    async def _fetch():
        today = datetime.now().strftime("%Y-%m-%d")
        headers = {
            "Authorization": api_token,
            "Accept": "application/json",
        }
        params = {"date": today}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                API_URL,
                headers=headers,
                params=params,
                timeout=15,
            ) as resp:
                if resp.status != 200:
                    raise ConfigEntryNotReady(f"HTTP {resp.status}")
                payload = await resp.json()
                return payload["data"]

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Ultrahuman Ring",
        update_method=_fetch,
        update_interval=timedelta(minutes=60),
    )

    await coordinator.async_config_entry_first_refresh()

    sensors = [
        UltrahumanSensor(entry.entry_id, coordinator, "Night Resting HR", "night_rhr"),
        UltrahumanSensor(entry.entry_id, coordinator, "Sleep HRV", "avg_sleep_hrv"),
        UltrahumanSensor(entry.entry_id, coordinator, "Sleep RHR", "sleep_rhr"),
        UltrahumanSensor(entry.entry_id, coordinator, "Recovery Index", "recovery_index"),
        UltrahumanSensor(entry.entry_id, coordinator, "Movement Index", "movement_index"),
        UltrahumanSensor(entry.entry_id, coordinator, "Active Minutes", "active_minutes"),
        UltrahumanSensor(entry.entry_id, coordinator, "VO2 Max", "vo2_max"),
    ]

    async_add_entities(sensors)


class UltrahumanSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        entry_id: str,
        coordinator: DataUpdateCoordinator,
        name: str,
        metric_type: str,
    ):
        super().__init__(coordinator)

        self.metric_type = metric_type
        self._attr_name = f"Ultrahuman {name}"
        self._attr_unique_id = f"{entry_id}_{metric_type}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "ultrahuman_ring")},
            name="Ultrahuman Ring",
            manufacturer="Ultrahuman",
            model="Ring",
        )

    @property
    def native_value(self):
        data = self.coordinator.data
        metrics_by_day = data.get("metrics", {})

        if not metrics_by_day:
            return None

        # Do NOT assume local date matches API date
        day_key = next(iter(metrics_by_day))
        metrics = metrics_by_day.get(day_key, [])

        metric = next(
            (m for m in metrics if m.get("type") == self.metric_type),
            None,
        )
        if not metric:
            return None

        obj = metric.get("object", {})

        # ---- VALUE MAPPING BASED ON REAL API ----
        if self.metric_type == "night_rhr":
            return obj.get("avg")

        if self.metric_type in (
            "avg_sleep_hrv",
            "sleep_rhr",
            "recovery_index",
            "movement_index",
            "active_minutes",
            "vo2_max",
        ):
            return obj.get("value")

        return None