"""Constants for the Planned Blackouts integration."""
from datetime import timedelta

DOMAIN = "planned_blackouts"

# Config flow
CONF_BILL_ID = "bill_id"
CONF_API_TOKEN = "api_token"
CONF_DAYS_AHEAD = "days_ahead"
CONF_POLLING_INTERVAL = "polling_interval"

# Defaults
DEFAULT_DAYS_AHEAD = 7
DEFAULT_POLLING_INTERVAL = 3600
MIN_POLLING_INTERVAL = 300
MAX_DAYS_AHEAD = 14

# API
API_URL = "https://uiapi.saapa.ir/api/ebills/PlannedBlackoutsReport"
API_TIMEOUT = 10

# Attributes
ATTR_OUTAGE_END = "end_time"
ATTR_OUTAGE_REASON = "reason"
ATTR_OUTAGE_ADDRESS = "address"
ATTR_OUTAGE_NUMBER = "outage_number"

# Calendar
CALENDAR_NAME = "Planned Blackouts"

# Sensors
SENSOR_NEXT_OUTAGE = "next_outage"
SENSOR_TODAY_COUNT = "today_outages_count"

# Update coordinator
UPDATE_INTERVAL = timedelta(seconds=DEFAULT_POLLING_INTERVAL)
