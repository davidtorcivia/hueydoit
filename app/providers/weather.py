import logging
from datetime import timedelta

import httpx

from app.config import settings
from app.providers.base import Provider, ScheduleConfig

logger = logging.getLogger(__name__)

OWM_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherProvider(Provider):
    name = "weather"

    async def fetch(self) -> dict:
        if not settings.openweathermap_api_key:
            logger.warning("No OpenWeatherMap API key configured")
            return {"error": "No API key configured"}

        params = {
            "lat": settings.latitude,
            "lon": settings.longitude,
            "appid": settings.openweathermap_api_key,
            "units": "imperial",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(OWM_URL, params=params, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()

        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})

        temp_f = main.get("temp", 0)
        temp_c = (temp_f - 32) * 5 / 9

        return {
            "temp_f": round(temp_f, 1),
            "temp_c": round(temp_c, 1),
            "feels_like_f": round(main.get("feels_like", temp_f), 1),
            "humidity": main.get("humidity", 0),
            "condition": weather.get("main", "Unknown"),
            "description": weather.get("description", ""),
            "icon": weather.get("icon", ""),
            "wind_speed": round(wind.get("speed", 0), 1),
            "wind_deg": wind.get("deg", 0),
            "pressure": main.get("pressure", 0),
            "visibility": data.get("visibility", 0),
        }

    def schedule(self) -> ScheduleConfig:
        return ScheduleConfig(type="interval", kwargs={"seconds": 900})

    def ttl(self) -> timedelta:
        return timedelta(hours=2)
