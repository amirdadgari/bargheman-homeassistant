# Planned Blackouts

A Home Assistant custom integration for tracking planned power outages from SAAPA's API.

## Features

- Fetches scheduled power outage information from SAAPA's API
- Exposes a calendar entity showing all planned outages
- Provides sensors for next upcoming outage and today's outage count
- Automatically converts Jalali (Shamsi) dates to Gregorian/UTC
- Configurable polling interval and days to look ahead

## Installation

### HACS Installation (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. Add this repository as a custom repository in HACS:
   - Go to HACS > Integrations
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add the URL of this repository and select "Integration" as the category
3. Click "Download" next to the Planned Blackouts integration
4. Restart Home Assistant

### Manual Installation

1. Download the `planned_blackouts` folder from this repository
2. Copy it to the `custom_components` directory in your Home Assistant configuration directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Planned Blackouts" and select it
4. Enter your SAAPA bill ID and API token
5. Configure the days to look ahead (default: 7, max: 14) and polling interval (default: 3600 seconds, min: 300 seconds)

## Entities

### Calendar

- **planned_blackouts**: Shows all planned outages as calendar events with start and end times

### Sensors

- **sensor.next_planned_outage**: Shows the start time of the next upcoming outage with additional attributes:
  - `end_time`: End time of the outage
  - `reason`: Reason for the outage
  - `address`: Location of the outage
  - `outage_number`: Outage reference number

- **sensor.today_s_planned_outages**: Count of outages scheduled for today

## Sample Automation

Here's an example automation to shut down computers 5 minutes before a planned outage:

```yaml
automation:
  - alias: "Shutdown PCs before power outage"
    trigger:
      - platform: template
        value_template: >
          {% set next_outage = states('sensor.next_planned_outage') %}
          {% if next_outage != 'unknown' and next_outage != 'unavailable' %}
            {% set outage_time = strptime(next_outage, '%Y-%m-%dT%H:%M:%S%z') %}
            {% set time_diff = (outage_time - now()).total_seconds() | int %}
            {{ time_diff > 0 and time_diff <= 300 }}
          {% else %}
            false
          {% endif %}
    action:
      - service: script.shutdown_computers
```

## Troubleshooting

- If you encounter authentication issues, you may need to reauthenticate with a new API token.
- Make sure your bill ID is correct and associated with your account.
- Check the Home Assistant logs for any error messages related to the integration.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
