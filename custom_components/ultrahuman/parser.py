"""Parser and sensor registry for Ultrahuman API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfTime,
)


@dataclass(frozen=True)
class UltrahumanMetric:
    key: str
    name: str
    icon: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    native_unit: str | None = None


# 🔑 SINGLE SOURCE OF TRUTH FOR ALL SENSORS
METRICS: tuple[UltrahumanMetric, ...] = (
    # ---- Cardio ----
    UltrahumanMetric("hr_last", "Heart Rate", "mdi:heart-pulse", None, SensorStateClass.MEASUREMENT, "bpm"),
    UltrahumanMetric("night_rhr", "Night Resting HR", "mdi:heart", None, SensorStateClass.MEASUREMENT, "bpm"),
    UltrahumanMetric("hrv_avg", "HRV", "mdi:heart-flash", None, SensorStateClass.MEASUREMENT, "ms"),
    UltrahumanMetric("sleep_rhr", "Sleep RHR", "mdi:heart-minus", None, SensorStateClass.MEASUREMENT, "bpm"),
    UltrahumanMetric("spo2_avg", "SpO2", "mdi:water-percent", None, SensorStateClass.MEASUREMENT, PERCENTAGE),
    UltrahumanMetric("vo2_max", "VO2 Max", "mdi:lungs", None, SensorStateClass.MEASUREMENT, "mL/kg/min"),

    # ---- Sleep ----
    UltrahumanMetric("sleep_score", "Sleep Score", "mdi:sleep", None, SensorStateClass.MEASUREMENT, None),
    UltrahumanMetric("total_sleep", "Total Sleep", "mdi:bed-clock", SensorDeviceClass.DURATION, SensorStateClass.MEASUREMENT, UnitOfTime.MINUTES),
    UltrahumanMetric("sleep_start", "Sleep Start", "mdi:bed", SensorDeviceClass.TIMESTAMP, None, None),
    UltrahumanMetric("sleep_end", "Sleep End", "mdi:bed-outline", SensorDeviceClass.TIMESTAMP, None, None),
    UltrahumanMetric("time_in_bed", "Time in Bed", "mdi:bed-king", SensorDeviceClass.DURATION, SensorStateClass.MEASUREMENT, UnitOfTime.MINUTES),

    # ---- Recovery & Activity ----
    UltrahumanMetric("recovery_index", "Recovery Index", "mdi:battery-heart-variant", None, SensorStateClass.MEASUREMENT, None),
    UltrahumanMetric("movement_index", "Movement Index", "mdi:run", None, SensorStateClass.MEASUREMENT, None),
    UltrahumanMetric("active_minutes", "Active Minutes", "mdi:timer", SensorDeviceClass.DURATION, SensorStateClass.MEASUREMENT, UnitOfTime.MINUTES),
    UltrahumanMetric("steps", "Steps", "mdi:shoe-print", None, SensorStateClass.TOTAL_INCREASING, "steps"),

    # ---- Temperature & Stress ----
    UltrahumanMetric("skin_temp", "Skin Temperature", "mdi:thermometer", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS),
    )


class UltrahumanDataParser:
    """Parse Ultrahuman API payload into normalized values."""

    def __init__(self, raw: dict) -> None:
        self._raw = raw
        self._tz = raw.get("latest_time_zone")

        metrics_by_day = raw.get("metrics", {})
        self._day_key = next(iter(metrics_by_day), None)
        self._metrics = metrics_by_day.get(self._day_key, []) if self._day_key else []

    # ---------- helpers ----------

    def _get_metric(self, metric_type: str) -> dict | None:
        return next(
            (m for m in self._metrics if m.get("type") == metric_type),
            None,
        )

    def _obj(self, metric_type: str) -> dict:
        metric = self._get_metric(metric_type)
        return metric.get("object", {}) if metric else {}

    def _iso(self, ts: int | None) -> str | None:
        if not ts:
            return None
        return datetime.fromtimestamp(
            ts,
            tz=ZoneInfo(self._tz) if self._tz else None,
        ).isoformat()

    # ---------- public API ----------

    def get_value(self, key: str):
        # ---- Cardio ----
        if key == "hr_last":
            return self._obj("hr").get("last_reading")

        if key == "night_rhr":
            return self._obj("night_rhr").get("avg")

        if key == "hrv_avg":
            return self._obj("avg_sleep_hrv").get("value")

        if key == "sleep_rhr":
            return self._obj("sleep_rhr").get("value")

        if key == "spo2_avg":
            return self._obj("spo2").get("avg")

        if key == "vo2_max":
            return self._obj("vo2_max").get("value")

        # ---- Sleep ----
        sleep = self._obj("sleep")

        if key == "sleep_score":
            return sleep.get("sleep_score", {}).get("score")

        if key == "total_sleep":
            return sleep.get("total_sleep", {}).get("minutes")

        if key == "sleep_start":
            return self._iso(sleep.get("bedtime_start"))

        if key == "sleep_end":
            return self._iso(sleep.get("bedtime_end"))

        if key == "time_in_bed":
            return sleep.get("time_in_bed", {}).get("minutes")

        # ---- Recovery & Activity ----
        if key == "recovery_index":
            return self._obj("recovery_index").get("value")

        if key == "movement_index":
            return self._obj("movement_index").get("value")

        if key == "active_minutes":
            return self._obj("active_minutes").get("value")

        if key == "steps":
            return self._obj("steps").get("total")

        # ---- Temperature & Stress ----
        if key == "skin_temp":
            return self._obj("skin_temperature").get("last_reading")

        return None
