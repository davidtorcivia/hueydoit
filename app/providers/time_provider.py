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
        # Time is computed fresh inline by the evaluator before each evaluation.
        # This schedule exists only as a fallback — runs once per hour to keep
        # the provider_config row updated, but is NOT the primary time source.
        return ScheduleConfig(type="interval", kwargs={"seconds": 3600})

    def ttl(self) -> timedelta:
        return timedelta(days=365)
