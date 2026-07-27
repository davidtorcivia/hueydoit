from datetime import date, timedelta

from app.holidays.cultural import _easter


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def get_international_holidays(year: int) -> list[dict]:
    easter = _easter(year)

    return [
        # Carnival / Mardi Gras — 47 days before Easter
        {
            "name": "Mardi Gras",
            "slug": "mardi_gras",
            "date": easter - timedelta(days=47),
            "window_start": easter - timedelta(days=50),
            "window_end": easter - timedelta(days=47),
            "colors": ["#ffd700", "#9900ff", "#00cc00"],
            "category": "international",
        },
        # International Women's Day
        {
            "name": "International Women's Day",
            "slug": "intl_womens_day",
            "date": date(year, 3, 8),
            "window_start": date(year, 3, 8),
            "window_end": date(year, 3, 8),
            "colors": ["#cc00ff", "#ff69b4", "#ffeedd"],
            "category": "international",
        },
        # Holi — approx full moon of Phalguna (lookup)
        {
            "name": "Holi",
            "slug": "holi",
            "date": _holi(year),
            "window_start": _holi(year),
            "window_end": _holi(year) + timedelta(days=1),
            "colors": ["#ff0066", "#ffcc00", "#00ccff", "#88ff00", "#ff6600", "#cc00ff"],
            "category": "international",
        },
        # Earth Day
        {
            "name": "Earth Day",
            "slug": "earth_day",
            "date": date(year, 4, 22),
            "window_start": date(year, 4, 22),
            "window_end": date(year, 4, 22),
            "colors": ["#00cc00", "#0088ff", "#00ff88"],
            "category": "international",
        },
        # Cinco de Mayo
        {
            "name": "Cinco de Mayo",
            "slug": "cinco_de_mayo",
            "date": date(year, 5, 5),
            "window_start": date(year, 5, 4),
            "window_end": date(year, 5, 5),
            "colors": ["#00cc00", "#ffffff", "#ff0000"],
            "category": "international",
        },
        # Bastille Day
        {
            "name": "Bastille Day",
            "slug": "bastille_day",
            "date": date(year, 7, 14),
            "window_start": date(year, 7, 14),
            "window_end": date(year, 7, 14),
            "colors": ["#0055ff", "#ffffff", "#ff0000"],
            "category": "international",
        },
        # Oktoberfest — starts 3rd Saturday of September
        {
            "name": "Oktoberfest",
            "slug": "oktoberfest",
            "date": _nth_weekday(year, 9, 5, 3),
            "window_start": _nth_weekday(year, 9, 5, 3),
            "window_end": _nth_weekday(year, 9, 5, 3) + timedelta(days=16),
            "colors": ["#0088ff", "#ffffff", "#ffd700"],
            "category": "international",
        },
        # Day of the Dead
        {
            "name": "Day of the Dead",
            "slug": "day_of_the_dead",
            "date": date(year, 11, 1),
            "window_start": date(year, 10, 31),
            "window_end": date(year, 11, 2),
            "colors": ["#ff6600", "#ff00ff", "#ffcc00", "#00ffcc"],
            "category": "international",
        },
        # Guy Fawkes Night
        {
            "name": "Guy Fawkes Night",
            "slug": "guy_fawkes",
            "date": date(year, 11, 5),
            "window_start": date(year, 11, 5),
            "window_end": date(year, 11, 5),
            "colors": ["#ff4400", "#ff8800", "#ffd700"],
            "category": "international",
        },
        # Kwanzaa
        {
            "name": "Kwanzaa",
            "slug": "kwanzaa",
            "date": date(year, 12, 26),
            "window_start": date(year, 12, 26),
            "window_end": date(year + 1, 1, 1),
            # Bendera colors are red/black/green, but black renders as white on a
            # bulb (hex_to_xy has no luminance) — gold stands in for the black stripe.
            "colors": ["#ff0000", "#00cc00", "#ffd700"],
            "category": "international",
        },
    ]


def _holi(year: int) -> date:
    known = {
        2024: date(2024, 3, 25),
        2025: date(2025, 3, 14),
        2026: date(2026, 3, 3),
        2027: date(2027, 3, 22),
        2028: date(2028, 3, 11),
        2029: date(2029, 2, 28),
        2030: date(2030, 3, 20),
    }
    return known.get(year, date(year, 3, 15))
