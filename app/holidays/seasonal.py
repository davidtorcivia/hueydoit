from datetime import date
import logging

logger = logging.getLogger(__name__)


def _spring_equinox(year: int) -> date:
    known = {
        2024: date(2024, 3, 20), 2025: date(2025, 3, 20), 2026: date(2026, 3, 20),
        2027: date(2027, 3, 20), 2028: date(2028, 3, 20), 2029: date(2029, 3, 20),
        2030: date(2030, 3, 20),
    }
    return known.get(year, date(year, 3, 20))


def _summer_solstice(year: int) -> date:
    known = {
        2024: date(2024, 6, 20), 2025: date(2025, 6, 20), 2026: date(2026, 6, 21),
        2027: date(2027, 6, 21), 2028: date(2028, 6, 20), 2029: date(2029, 6, 21),
        2030: date(2030, 6, 21),
    }
    return known.get(year, date(year, 6, 21))


def _fall_equinox(year: int) -> date:
    known = {
        2024: date(2024, 9, 22), 2025: date(2025, 9, 22), 2026: date(2026, 9, 23),
        2027: date(2027, 9, 23), 2028: date(2028, 9, 22), 2029: date(2029, 9, 22),
        2030: date(2030, 9, 22),
    }
    return known.get(year, date(year, 9, 22))


def _winter_solstice(year: int) -> date:
    known = {
        2024: date(2024, 12, 21), 2025: date(2025, 12, 21), 2026: date(2026, 12, 21),
        2027: date(2027, 12, 22), 2028: date(2028, 12, 21), 2029: date(2029, 12, 21),
        2030: date(2030, 12, 21),
    }
    return known.get(year, date(year, 12, 21))


def get_seasonal_holidays(year: int) -> list[dict]:
    return [
        {
            "name": "Spring Equinox",
            "slug": "spring_equinox",
            "date": _spring_equinox(year),
            "window_start": _spring_equinox(year),
            "window_end": _spring_equinox(year),
            "colors": ["#00ff88", "#ffcc00", "#ff69b4"],
            "category": "seasonal",
        },
        {
            "name": "Summer Solstice",
            "slug": "summer_solstice",
            "date": _summer_solstice(year),
            "window_start": _summer_solstice(year),
            "window_end": _summer_solstice(year),
            "colors": ["#ffcc00", "#ff6600", "#ff0000"],
            "category": "seasonal",
        },
        {
            "name": "Fall Equinox",
            "slug": "fall_equinox",
            "date": _fall_equinox(year),
            "window_start": _fall_equinox(year),
            "window_end": _fall_equinox(year),
            "colors": ["#ff6600", "#ff4400", "#ffd700"],
            "category": "seasonal",
        },
        {
            "name": "Winter Solstice",
            "slug": "winter_solstice",
            "date": _winter_solstice(year),
            "window_start": _winter_solstice(year),
            "window_end": _winter_solstice(year),
            "colors": ["#88bbff", "#ffeedd", "#aaddff"],
            "category": "seasonal",
        },
    ]
