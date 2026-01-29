"""Constants for the Ultrahuman Ring integration."""

DOMAIN = "ultrahuman"

# API
API_URL = "https://partner.ultrahuman.com/api/v1/partner/daily_metrics"
API_TIMEOUT = 15

# Config keys
CONF_API_TOKEN = "api_token"
CONF_UPDATE_INTERVAL = "update_interval"

# Defaults
DEFAULT_UPDATE_INTERVAL = 60  # minutes

# Platforms
PLATFORMS = ["sensor"]
