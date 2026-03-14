# Huey Do It

This is a very barebones Philips Hue control system for changing lights based on holidays, time of day, weather, and whatever else you feel like. It has no auth and should never be exposed outside of your local network. It's just a hacked together thing, don't expect much.

## What it does

- Rule engine that controls your Hue lights based on conditions (time, solar, weather, holidays, calendar dates, webhooks)
- 54 built-in holidays across US federal, cultural, international, fun, and seasonal categories
- Automatically distributes holiday colors across your lights
- Respects manual overrides -- if you turn a light off, it stays off for 30 minutes before the rules take back over
- Dark theme web UI for managing everything

## Running it

```
docker compose up -d
```

Then open `http://your-server:8585` and follow the setup wizard to pair your Hue bridge.

## Environment variables

- `HUE_BRIDGE_IP` -- set this if mDNS discovery doesn't work on your network
- `OPENWEATHERMAP_API_KEY` -- for weather-based rules
- `TZ` -- timezone, defaults to America/New_York
- `LATITUDE` / `LONGITUDE` -- for solar calculations
- `HUE_CONTROLLER_PORT` -- defaults to 8585
- `EXTERNAL_OVERRIDE_TIMEOUT_MIN` -- how long manual/external overrides last, defaults to 30

## Stack

- Python 3.12, FastAPI, aiohue v2, APScheduler, aiosqlite
- Svelte 5, Vite
- SQLite
- Docker

## License

MIT
