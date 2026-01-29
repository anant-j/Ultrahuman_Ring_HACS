import aiohttp
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging

from homeassistant.helpers.entity import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

def iso_from_epoch(ts: int | None, tz: str | None):
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(ts, tz=ZoneInfo(tz) if tz else None).isoformat()
    except Exception:
        return None

class UltrahumanSensor(SensorEntity):
    def __init__(self, coordinator, name, metric_type):
        self.coordinator = coordinator
        self._name = name
        self.metric_type = metric_type

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        metrics_by_day = self.coordinator.data.get("metrics", {})
        today = datetime.now().strftime("%Y-%m-%d")
        metrics = metrics_by_day.get(today, [])
        metric = next((m["object"] for m in metrics if m["type"] == self.metric_type), None)

        # Regular metrics
        value = metric.get("value") if metric else None
        if value is not None:
            return value

        # Special handling for sleep timestamps
        if self.metric_type in ["sleep_start", "sleep_end"]:
            sleep = next((m["object"] for m in metrics if m["type"] == "sleep"), None)
            tz = self.coordinator.data.get("latest_time_zone")
            if self.metric_type == "sleep_start":
                return iso_from_epoch(sleep.get("bedtime_start") if sleep else None, tz)
            if self.metric_type == "sleep_end":
                return iso_from_epoch(sleep.get("bedtime_end") if sleep else None, tz)

        return None

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Ultrahuman sensors from config entry."""
    
    api_url = "https://partner.ultrahuman.com/api/v1/partner/daily_metrics"
    api_token = entry.data["api_token"]

    async def fetch_ultrahuman_data():
        today = datetime.now().strftime("%Y-%m-%d")
        headers = {"Authorization": api_token, "Accept": "application/json"}
        params = {"date": today}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(api_url, headers=headers, params=params, timeout=10) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"Error fetching data: {resp.status}")
                    payload = await resp.json()
                    return payload.get("data", {})
            except Exception as e:
                raise UpdateFailed(f"Request failed: {e}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="ultrahuman",
        update_method=fetch_ultrahuman_data,
        update_interval=timedelta(minutes=15),
    )

    await coordinator.async_config_entry_first_refresh()

    sensors = [
        UltrahumanSensor(coordinator, "Heart Rate", "hr"),
        UltrahumanSensor(coordinator, "HRV", "hrv"),
        UltrahumanSensor(coordinator, "SpO2", "spo2"),
        UltrahumanSensor(coordinator, "Sleep Score", "sleep_score"),
        UltrahumanSensor(coordinator, "Sleep Start", "sleep_start"),
        UltrahumanSensor(coordinator, "Sleep End", "sleep_end"),
        UltrahumanSensor(coordinator, "Recovery Index", "recovery_index"),
        UltrahumanSensor(coordinator, "Movement Index", "movement_index"),
        UltrahumanSensor(coordinator, "VO2 Max", "vo2_max"),
        UltrahumanSensor(coordinator, "Active Minutes", "active_minutes"),
    ]

    async_add_entities(sensors)
