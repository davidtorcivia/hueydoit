from datetime import datetime, timedelta, date
import zoneinfo

from app.config import settings
from app.providers.base import Provider, ScheduleConfig

MONTH_NAMES = [
    "", "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]


def _get_season(d: date) -> str:
    """Astronomical seasons (Northern Hemisphere) based on approximate solstice/equinox dates."""
    md = (d.month, d.day)
    if (3, 20) <= md <= (6, 20):
        return "spring"
    if (6, 21) <= md <= (9, 21):
        return "summer"
    if (9, 22) <= md <= (12, 20):
        return "fall"
    return "winter"


class CalendarProvider(Provider):
    name = "calendar"

    async def fetch(self) -> dict:
        tz = zoneinfo.ZoneInfo(settings.tz)
        now = datetime.now(tz)
        today = now.date()
        return self.compute_state(today)

    @staticmethod
    def compute_state(today: date) -> dict:
        return {
            "date": today.isoformat(),
            "month": today.month,
            "month_name": MONTH_NAMES[today.month],
            "day": today.day,
            "year": today.year,
            "day_of_year": today.timetuple().tm_yday,
            "season": _get_season(today),
            "week_number": today.isocalendar()[1],
        }

    def schedule(self) -> ScheduleConfig:
        # Computed inline by the evaluator — no polling needed.
        return ScheduleConfig(type="none")

    def ttl(self) -> timedelta:
        return timedelta(days=365)
