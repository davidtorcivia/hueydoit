import json
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta

from app.database import get_db
from app.holidays.us_federal import get_us_federal_holidays
from app.holidays.cultural import get_cultural_holidays
from app.holidays.international import get_international_holidays
from app.holidays.fun import get_fun_holidays
from app.holidays.seasonal import get_seasonal_holidays

logger = logging.getLogger(__name__)


CATEGORY_DEFAULT_PRIORITY = {
    "us_federal": 10,
    "cultural": 20,
    "international": 30,
    "fun": 40,
    "seasonal": 50,
    "custom": 15,
}


@dataclass
class Holiday:
    name: str
    slug: str
    date: date
    window_start: date
    window_end: date
    colors: list[str] = field(default_factory=list)
    category: str = "custom"
    recurring: bool = True
    enabled: bool = True
    priority: int = 50


def shift_year(d: date, year: int) -> date:
    """Move a date to another year, tolerating Feb 29.

    date.replace(year=...) raises ValueError for Feb 29 in a non-leap year,
    which would take down the whole holiday provider for any leap-day holiday
    in 3 years out of 4. Fall back to Feb 28.
    """
    try:
        return d.replace(year=year)
    except ValueError:
        return d.replace(year=year, day=28)


def is_holiday_active(holiday: Holiday, check_date: date) -> bool:
    if not holiday.enabled:
        return False
    start = holiday.window_start
    end = holiday.window_end
    if holiday.recurring:
        start = shift_year(start, check_date.year)
        end = shift_year(end, check_date.year)
        if start > end:
            return check_date >= start or check_date <= end
    return start <= check_date <= end


async def load_all_holidays(year: int) -> list[Holiday]:
    holidays: list[Holiday] = []

    # Load user overrides for built-in holiday colors/enabled/window
    overrides: dict[str, dict] = {}
    async with get_db() as db:
        cursor = await db.execute("SELECT slug, colors, enabled, window_before_days, window_after_days, priority FROM holiday_config")
        for row in await cursor.fetchall():
            colors = []
            if row[1]:
                try:
                    colors = json.loads(row[1])
                except (json.JSONDecodeError, TypeError):
                    pass
            overrides[row[0]] = {
                "colors": colors,
                "enabled": bool(row[2]),
                "window_before_days": row[3],
                "window_after_days": row[4],
                "priority": row[5],
            }

    def _apply_window_override(h_date, h_ws, h_we, ovr):
        """Apply window_before_days / window_after_days overrides if set."""
        before = ovr.get("window_before_days")
        after = ovr.get("window_after_days")
        ws = h_date - timedelta(days=before) if before is not None else h_ws
        we = h_date + timedelta(days=after) if after is not None else h_we
        return ws, we

    all_sources = [get_us_federal_holidays, get_cultural_holidays, get_international_holidays, get_fun_holidays, get_seasonal_holidays]
    for source in all_sources:
        for h in source(year):
            slug = h["slug"]
            cat = h["category"]
            ovr = overrides.get(slug, {})
            ws, we = _apply_window_override(h["date"], h["window_start"], h["window_end"], ovr)
            holidays.append(Holiday(
                name=h["name"],
                slug=slug,
                date=h["date"],
                window_start=ws,
                window_end=we,
                colors=ovr.get("colors") or h["colors"],
                category=cat,
                enabled=ovr.get("enabled", True),
                priority=ovr.get("priority") or CATEGORY_DEFAULT_PRIORITY.get(cat, 50),
            ))

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, name, date, window_start, window_end, recurring, category, colors, enabled FROM holidays"
        )
        rows = await cursor.fetchall()
        for row in rows:
            colors = []
            if row[7]:
                try:
                    colors = json.loads(row[7])
                except (json.JSONDecodeError, TypeError):
                    pass

            holiday_date = date.fromisoformat(row[2])
            ws = date.fromisoformat(row[3]) if row[3] else holiday_date
            we = date.fromisoformat(row[4]) if row[4] else holiday_date

            slug = row[1].lower().replace(" ", "_").replace("'", "")

            cat = row[6] or "custom"
            holidays.append(Holiday(
                name=row[1],
                slug=slug,
                date=holiday_date,
                window_start=ws,
                window_end=we,
                colors=colors,
                category=cat,
                recurring=bool(row[5]),
                enabled=bool(row[8]),
                priority=CATEGORY_DEFAULT_PRIORITY.get(cat, 15),
            ))

    # Sort by priority (lower = higher priority)
    holidays.sort(key=lambda h: h.priority)

    return holidays
