"""Ultrahuman integration for Home Assistant."""

from homeassistant.core import HomeAssistant

DOMAIN = "ultrahuman"

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Ultrahuman integration."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up Ultrahuman from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
