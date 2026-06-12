"""Constants for the GoSMS integration."""

DOMAIN = "gosms"

# API
API_BASE_URL = "https://api.gosms.ru/api/ext/v1"
API_ENDPOINT_DEVICES = f"{API_BASE_URL}/devices"
API_ENDPOINT_SMS = f"{API_BASE_URL}/sms"

# Timeouts
API_TIMEOUT = 10  # seconds

# Update interval
UPDATE_INTERVAL_SECONDS = 60

# Config entry keys
CONF_API_KEY = "api_key"

# SIM slot codes
SIM_AUTO = -2
SIM_DEFAULT = -1

# Error codes (for config flow)
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_INVALID_AUTH = "invalid_auth"
ERROR_UNKNOWN = "unknown"
