from datetime import datetime, timedelta
import zoneinfo

from app.config import settings
from app.providers.base import Provider, ScheduleConfig


class TimeProvider(Provider):
    name = "time"

    async def fetch(self) -> dict:
        tz = zoneinfo.ZoneInfo(settings.tz)
        now = datetime.now(tz)
        return {
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "day_of_week": now.strftime("%A").lower(),
            "date": now.strftime("%Y-%m-%d"),
            "is_weekend": now.weekday() >= 5,
            "month": now.month,
            "day": now.day,
            "year": now.year,
        }

    def schedule(self) -> ScheduleConfig:
        # Time transitions are computed and scheduled precisely by the engine
        # scheduler — no polling needed.
        return ScheduleConfig(type="none")

    def ttl(self) -> timedelta:
        return timedelta(days=365)
