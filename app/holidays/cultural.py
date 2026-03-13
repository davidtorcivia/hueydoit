from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


def _easter(year: int) -> date:
    """Compute Easter Sunday using the Anonymous Gregorian algorithm (computus)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def _hanukkah_start(year: int) -> date:
    """Approximate Hanukkah start (25 Kislev). Uses a lookup-style approximation."""
    try:
        from hijri_converter import Hijri, Gregorian
    except ImportError:
        pass

    known = {
        2024: date(2024, 12, 25),
        2025: date(2025, 12, 14),
        2026: date(2026, 12, 4),
        2027: date(2027, 12, 24),
        2028: date(2028, 12, 12),
        2029: date(2029, 12, 1),
        2030: date(2030, 12, 20),
    }
    if year in known:
        return known[year]
    return date(year, 12, 15)


def _diwali(year: int) -> date:
    """Approximate Diwali date (new moon in Oct/Nov)."""
    known = {
        2024: date(2024, 11, 1),
        2025: date(2025, 10, 20),
        2026: date(2026, 11, 8),
        2027: date(2027, 10, 29),
        2028: date(2028, 10, 17),
        2029: date(2029, 11, 5),
        2030: date(2030, 10, 26),
    }
    if year in known:
        return known[year]
    return date(year, 10, 28)


def _lunar_new_year(year: int) -> date:
    """Approximate Lunar New Year date."""
    known = {
        2024: date(2024, 2, 10),
        2025: date(2025, 1, 29),
        2026: date(2026, 2, 17),
        2027: date(2027, 2, 6),
        2028: date(2028, 1, 26),
        2029: date(2029, 2, 13),
        2030: date(2030, 2, 3),
    }
    if year in known:
        return known[year]
    return date(year, 2, 1)


def _eid_al_fitr(year: int) -> date:
    """Compute approximate Eid al-Fitr using hijri-converter."""
    try:
        from hijri_converter import Hijri, Gregorian

        for hijri_year in range(year - 622 + 1, year - 622 + 3):
            try:
                h = Hijri(hijri_year, 10, 1)
                g = h.to_gregorian()
                if g.year == year:
                    return g
            except Exception:
                continue
    except ImportError:
        logger.warning("hijri-converter not installed, using approximate Eid dates")

    known = {
        2024: date(2024, 4, 10),
        2025: date(2025, 3, 30),
        2026: date(2026, 3, 20),
        2027: date(2027, 3, 10),
        2028: date(2028, 2, 27),
        2029: date(2029, 2, 14),
        2030: date(2030, 2, 4),
    }
    return known.get(year, date(year, 3, 15))


def _eid_al_adha(year: int) -> date:
    """Compute approximate Eid al-Adha using hijri-converter."""
    try:
        from hijri_converter import Hijri, Gregorian

        for hijri_year in range(year - 622 + 1, year - 622 + 3):
            try:
                h = Hijri(hijri_year, 12, 10)
                g = h.to_gregorian()
                if g.year == year:
                    return g
            except Exception:
                continue
    except ImportError:
        logger.warning("hijri-converter not installed, using approximate Eid dates")

    known = {
        2024: date(2024, 6, 17),
        2025: date(2025, 6, 7),
        2026: date(2026, 5, 27),
        2027: date(2027, 5, 16),
        2028: date(2028, 5, 5),
        2029: date(2029, 4, 24),
        2030: date(2030, 4, 13),
    }
    return known.get(year, date(year, 6, 15))


def get_cultural_holidays(year: int) -> list[dict]:
    easter = _easter(year)

    return [
        {
            "name": "Valentine's Day",
            "slug": "valentines_day",
            "date": date(year, 2, 14),
            "window_start": date(year, 2, 13),
            "window_end": date(year, 2, 14),
            "colors": ["#ff1493", "#ff69b4", "#ff0000"],
            "category": "cultural",
        },
        {
            "name": "St. Patrick's Day",
            "slug": "st_patricks_day",
            "date": date(year, 3, 17),
            "window_start": date(year, 3, 16),
            "window_end": date(year, 3, 17),
            "colors": ["#00ff00", "#00cc44", "#ffeedd"],
            "category": "cultural",
        },
        {
            "name": "Easter",
            "slug": "easter",
            "date": easter,
            "window_start": easter - timedelta(days=1),
            "window_end": easter,
            "colors": ["#ff69b4", "#ffff00", "#87ceeb", "#90ee90"],
            "category": "cultural",
        },
        {
            "name": "Eid al-Fitr",
            "slug": "eid_al_fitr",
            "date": _eid_al_fitr(year),
            "window_start": _eid_al_fitr(year) - timedelta(days=1),
            "window_end": _eid_al_fitr(year) + timedelta(days=2),
            "colors": ["#00ff00", "#ffd700", "#ffffff"],
            "category": "cultural",
        },
        {
            "name": "Eid al-Adha",
            "slug": "eid_al_adha",
            "date": _eid_al_adha(year),
            "window_start": _eid_al_adha(year) - timedelta(days=1),
            "window_end": _eid_al_adha(year) + timedelta(days=2),
            "colors": ["#00ff00", "#ffd700", "#ffffff"],
            "category": "cultural",
        },
        {
            "name": "Halloween",
            "slug": "halloween",
            "date": date(year, 10, 31),
            "window_start": date(year, 10, 25),
            "window_end": date(year, 10, 31),
            "colors": ["#ff6600", "#800080", "#00ff00"],
            "category": "cultural",
        },
        {
            "name": "Diwali",
            "slug": "diwali",
            "date": _diwali(year),
            "window_start": _diwali(year) - timedelta(days=2),
            "window_end": _diwali(year) + timedelta(days=2),
            "colors": ["#ffd700", "#ff6600", "#ff0000"],
            "category": "cultural",
        },
        {
            "name": "Hanukkah",
            "slug": "hanukkah",
            "date": _hanukkah_start(year),
            "window_start": _hanukkah_start(year),
            "window_end": _hanukkah_start(year) + timedelta(days=7),
            "colors": ["#4488ff", "#ffeedd", "#66aaff"],
            "category": "cultural",
        },
        {
            "name": "Lunar New Year",
            "slug": "lunar_new_year",
            "date": _lunar_new_year(year),
            "window_start": _lunar_new_year(year) - timedelta(days=1),
            "window_end": _lunar_new_year(year) + timedelta(days=1),
            "colors": ["#ff0000", "#ffd700", "#ff6600"],
            "category": "cultural",
        },
    ]
