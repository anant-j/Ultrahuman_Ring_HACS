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
from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)
DOMAIN = "ultrahuman"


def iso_from_epoch(ts: int | None, tz: str | None) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(
            ts, tz=ZoneInfo(tz) if tz else None
        ).isoformat()
    except Exception:
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    api_url = "https://partner.ultrahuman.com/api/v1/partner/daily_metrics"
    api_token = entry.data["api_token"]

    async def _fetch():
        today = datetime.now().strftime("%Y-%m-%d")
        headers = {
            "Authorization": api_token,
            "Accept": "application/json",
        }
        params = {"date": today}

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers, params=params, timeout=15) as resp:
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
        UltrahumanSensor(coordinator, "Heart Rate", "hr"),
        UltrahumanSensor(coordinator, "HRV", "hrv"),
        UltrahumanSensor(coordinator, "SpO2", "spo2"),
        UltrahumanSensor(coordinator, "Steps", "steps"),
        UltrahumanSensor(coordinator, "Sleep Score", "sleep_score"),
        UltrahumanSensor(coordinator, "Sleep Start", "sleep_start"),
        UltrahumanSensor(coordinator, "Sleep End", "sleep_end"),
        UltrahumanSensor(coordinator, "Recovery Index", "recovery_index"),
        UltrahumanSensor(coordinator, "Movement Index", "movement_index"),
        UltrahumanSensor(coordinator, "VO2 Max", "vo2_max"),
        UltrahumanSensor(coordinator, "Active Minutes", "active_minutes"),
    ]

    async_add_entities(sensors)


class UltrahumanSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, name: str, metric_type: str):
        super().__init__(coordinator)
        self._attr_name = f"Ultrahuman {name}"
        self.metric_type = metric_type

    @property
    def native_value(self):
        data = self.coordinator.data
        metrics_by_day = data.get("metrics", {})

        if not metrics_by_day:
            return None

        # Do NOT assume local date matches API date
        day_key = next(iter(metrics_by_day))
        metrics = metrics_by_day.get(day_key, [])

        metric = next((m for m in metrics if m["type"] == self.metric_type), None)
        if not metric:
            return None

        obj = metric["object"]

        if self.metric_type == "hr":
            return obj.get("last_reading")

        if self.metric_type in ("hrv", "spo2"):
            return obj.get("avg")

        if self.metric_type == "steps":
            return obj.get("total")

        if self.metric_type == "sleep_score":
            return obj.get("score")

        if self.metric_type in (
            "recovery_index",
            "movement_index",
            "vo2_max",
            "active_minutes",
        ):
            return obj.get("value")

        if self.metric_type == "sleep_start":
            return iso_from_epoch(
                obj.get("bedtime_start"),
                data.get("latest_time_zone"),
            )

        if self.metric_type == "sleep_end":
            return iso_from_epoch(
                obj.get("bedtime_end"),
                data.get("latest_time_zone"),
            )

        return None
