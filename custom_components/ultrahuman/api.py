"""API client for Ultrahuman Ring."""

from datetime import datetime
import aiohttp

from .const import API_URL, API_TIMEOUT


class UltrahumanApiClient:
    """Client to interact with Ultrahuman API."""

    def __init__(self, api_token: str) -> None:
        """Initialize the API client."""
        self._api_token = api_token
        self._headers = {
            "Authorization": api_token,
            "Accept": "application/json",
        }

    async def async_validate_token(self) -> bool:
        """Validate the API token."""
        try:
            await self.async_get_metrics()
            return True
        except Exception:
            return False

    async def async_get_metrics(self) -> dict:
        """Fetch daily metrics from the API."""
        today = datetime.now().strftime("%Y-%m-%d")
        params = {"date": today}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                API_URL,
                headers=self._headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as resp:
                resp.raise_for_status()
                payload = await resp.json()
                return payload.get("data", {})
