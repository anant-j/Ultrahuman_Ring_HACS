"""Ultrahuman Integration."""
from homeassistant.core import HomeAssistant

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the integration."""
    return True

async def async_setup_entry(hass, entry):
    """Set up from config entry."""
    return True
