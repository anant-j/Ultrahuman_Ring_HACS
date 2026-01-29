import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

DOMAIN = "ultrahuman"

class UltrahumanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ultrahuman Sensors."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Step when user initializes the integration via UI."""
        errors = {}
        if user_input is not None:
            # Optional: validate API credentials
            if await self._validate_credentials(user_input):
                return self.async_create_entry(
                    title="Ultrahuman",
                    data=user_input
                )
            else:
                errors["base"] = "invalid_credentials"

        data_schema = vol.Schema({
            vol.Required("api_token"): str
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    async def _validate_credentials(self, user_input: dict) -> bool:
        """Optional: test if the API token works."""
        import aiohttp
        api_url = "https://partner.ultrahuman.com/api/v1/partner/daily_metrics"
        api_token = user_input["api_token"]
        headers = {"Authorization": api_token, "Accept": "application/json"}

        today = datetime.now().strftime("%Y-%m-%d")
        params = {"date": today}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers, params=params, timeout=10) as resp:
                    return resp.status == 200
        except Exception:
            return False
