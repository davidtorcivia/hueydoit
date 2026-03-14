import logging
from datetime import date, datetime, timedelta
import zoneinfo

from app.config import settings
from app.providers.base import Provider, ScheduleConfig
from app.holidays.loader import load_all_holidays, is_holiday_active

logger = logging.getLogger(__name__)


class HolidayProvider(Provider):
    name = "holiday"

    async def fetch(self) -> dict:
        tz = zoneinfo.ZoneInfo(settings.tz)
        now = datetime.now(tz)
        today = now.date()

        holidays = await load_all_holidays(today.year)

        active = []
        upcoming = []

        for h in holidays:
            if is_holiday_active(h, today):
                active.append({
                    "name": h.name,
                    "slug": h.slug,
                    "colors": h.colors,
                    "category": h.category,
                    "priority": h.priority,
                })
            else:
                h_date = h.date
                if h.recurring:
                    h_date = h_date.replace(year=today.year)
                    if h_date < today:
                        h_date = h_date.replace(year=today.year + 1)
                days_until = (h_date - today).days
                if 0 < days_until <= 30:
                    upcoming.append({
                        "name": h.name,
                        "slug": h.slug,
                        "date": h_date.isoformat(),
                        "days_until": days_until,
                        "colors": h.colors,
                    })

        upcoming.sort(key=lambda x: x["days_until"])

        # Sort active by priority (lower = higher priority), already pre-sorted from loader
        active.sort(key=lambda x: x.get("priority", 50))

        # Collect colors from the highest-priority active holiday
        active_colors = active[0]["colors"] if active else []

        return {
            "active_holidays": [h["slug"] for h in active],
            "active_holiday": active[0]["slug"] if active else None,
            "active_colors": active_colors,
            "active_details": active,
            "upcoming": upcoming[:5],
        }

    def schedule(self) -> ScheduleConfig:
        return ScheduleConfig(type="cron", kwargs={"hour": 0, "minute": 0})

    def ttl(self) -> timedelta:
        return timedelta(hours=25)
