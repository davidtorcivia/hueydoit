from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

# Hindu festival dates are reckoned in Indian local time.
IST_OFFSET = timedelta(hours=5, minutes=30)
# Pradosh (dusk) is roughly 18:00 IST across the Diwali window.
PRADOSH_HOUR_IST = 18


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Get the nth occurrence of a weekday in a month. weekday: 0=Mon, 6=Sun."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


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


def _hijri_event(year: int, hijri_month: int, hijri_day: int) -> date | None:
    """Gregorian date of a Hijri calendar event falling in the given Gregorian year.

    Hijri years are ~354 days, so they drift against the Gregorian calendar by
    roughly one year every 33. The mapping is therefore h ~= (g - 622) * 33/32,
    not the naive (g - 622) — searching the naive range lands ~43 years early
    and never matches, which silently disabled this path entirely.

    Returns None if hijri-converter is unavailable or the year is outside the
    range it supports, so callers can fall back to a lookup table.
    """
    try:
        from hijri_converter import Hijri
    except ImportError:
        logger.warning("hijri-converter not installed, using approximate dates")
        return None

    approx = round((year - 622) * 33 / 32)
    for hijri_year in range(approx - 1, approx + 2):
        try:
            g = Hijri(hijri_year, hijri_month, hijri_day).to_gregorian()
        except (ValueError, OverflowError):
            continue
        if g.year == year:
            return date(g.year, g.month, g.day)
    return None


def _hanukkah_start(year: int) -> date:
    """First night of Hanukkah — the eve of 25 Kislev.

    Jewish days begin at sunset, so the first candle is lit the evening before
    25 Kislev, which is the date that matters for lights.
    """
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

    try:
        from convertdate import hebrew

        return date(*hebrew.to_gregorian(year + 3761, hebrew.KISLEV, 25)) - timedelta(days=1)
    except Exception as e:
        logger.warning("Hanukkah computation failed for %s (%s); using approximation", year, e)
        return date(year, 12, 15)


def _new_moons(year: int) -> list:
    """New moon instants during `year`, shifted to IST — Hindu festival dates are
    reckoned against Indian local time."""
    return _moon_phases(year, "next_new_moon")


def _full_moons(year: int) -> list:
    return _moon_phases(year, "next_full_moon")


def _moon_phases(year: int, which: str) -> list:
    import ephem

    fn = getattr(ephem, which)
    cursor = ephem.Date(f"{year - 1}/12/1")
    out = []
    while True:
        cursor = fn(cursor)
        moment = ephem.Date(cursor).datetime() + IST_OFFSET
        if moment.year > year:
            return out
        if moment.year == year:
            out.append(moment)


def _diwali(year: int) -> date:
    """Diwali (Lakshmi Puja) — the Amavasya of Kartika.

    Celebrated on the day Amavasya is present at pradosh (dusk), so the new moon
    instant counts for that day only if it falls after roughly sunset in India;
    otherwise the previous day holds. Matches the verified table exactly for
    2024-2030.
    """
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

    try:
        for moment in _new_moons(year):
            if (moment.month == 10 and moment.day >= 15) or (moment.month == 11 and moment.day <= 15):
                if moment.hour < PRADOSH_HOUR_IST:
                    return moment.date() - timedelta(days=1)
                return moment.date()
    except Exception as e:
        logger.warning("Diwali computation failed for %s (%s); using approximation", year, e)
    return date(year, 10, 28)


def _lunar_new_year(year: int) -> date:
    """Lunar New Year — first day of the first month of the Chinese calendar."""
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

    try:
        from lunardate import LunarDate

        return LunarDate(year, 1, 1).toSolarDate()
    except Exception as e:
        logger.warning("Lunar New Year computation failed for %s (%s); using approximation", year, e)
        return date(year, 2, 1)


def _eid_al_fitr(year: int) -> date:
    """Eid al-Fitr — 1 Shawwal (Hijri month 10)."""
    computed = _hijri_event(year, 10, 1)
    if computed:
        return computed

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
    """Eid al-Adha — 10 Dhu al-Hijjah (Hijri month 12)."""
    computed = _hijri_event(year, 12, 10)
    if computed:
        return computed

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



def _hebrew_eve(year: int, hebrew_month: int, hebrew_day: int, year_offset: int = 3761) -> date | None:
    """Gregorian date of the *eve* of a Hebrew calendar date.

    Jewish days begin at sunset, so the observance starts the evening before —
    which is the day that matters for lights. Tishri falls at the start of the
    Hebrew year (offset 3761); Nisan is in the second half (offset 3760).
    """
    try:
        from convertdate import hebrew

        return date(*hebrew.to_gregorian(year + year_offset, hebrew_month, hebrew_day)) - timedelta(days=1)
    except Exception as e:
        logger.warning("Hebrew date %s/%s for %s failed: %s", hebrew_month, hebrew_day, year, e)
        return None


def _rosh_hashanah(year: int) -> date:
    from convertdate import hebrew

    return _hebrew_eve(year, hebrew.TISHRI, 1) or date(year, 9, 15)


def _yom_kippur(year: int) -> date:
    from convertdate import hebrew

    return _hebrew_eve(year, hebrew.TISHRI, 10) or date(year, 9, 24)


def _passover(year: int) -> date:
    from convertdate import hebrew

    return _hebrew_eve(year, hebrew.NISAN, 15, year_offset=3760) or date(year, 4, 10)


def _ramadan_start(year: int) -> date:
    """First day of Ramadan — 1 Ramadan (Hijri month 9)."""
    return _hijri_event(year, 9, 1) or date(year, 3, 1)


def _nowruz(year: int) -> date:
    """Persian New Year — 1 Farvardin."""
    try:
        from convertdate import persian

        return date(*persian.to_gregorian(year - 621, 1, 1))
    except Exception as e:
        logger.warning("Nowruz computation failed for %s: %s", year, e)
        return date(year, 3, 20)


def _election_day(year: int) -> date:
    """US general election — the Tuesday after the first Monday in November."""
    first_monday = _nth_weekday(year, 11, 0, 1)
    return first_monday + timedelta(days=1)


def get_cultural_holidays(year: int) -> list[dict]:
    easter = _easter(year)

    return [
        {
            "name": "Valentine's Day",
            "slug": "valentines_day",
            "date": date(year, 2, 14),
            "window_start": date(year, 2, 13),
            "window_end": date(year, 2, 14),
            "colors": ["#ff0033", "#ff69b4", "#ffeedd"],
            "category": "cultural",
        },
        {
            "name": "St. Patrick's Day",
            "slug": "st_patricks_day",
            "date": date(year, 3, 17),
            "window_start": date(year, 3, 16),
            "window_end": date(year, 3, 17),
            "colors": ["#00ff33", "#88ff00", "#ffd700"],
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
            "name": "Mother's Day",
            "slug": "mothers_day",
            "date": _nth_weekday(year, 5, 6, 2),
            "window_start": _nth_weekday(year, 5, 6, 2),
            "window_end": _nth_weekday(year, 5, 6, 2),
            "colors": ["#ff69b4", "#cc66ff", "#ffeedd"],
            "category": "cultural",
        },
        {
            "name": "Father's Day",
            "slug": "fathers_day",
            "date": _nth_weekday(year, 6, 6, 3),
            "window_start": _nth_weekday(year, 6, 6, 3),
            "window_end": _nth_weekday(year, 6, 6, 3),
            "colors": ["#0088ff", "#00d0ff", "#ffd700"],
            "category": "cultural",
        },
        {
            "name": "Eid al-Fitr",
            "slug": "eid_al_fitr",
            "date": _eid_al_fitr(year),
            "window_start": _eid_al_fitr(year) - timedelta(days=1),
            "window_end": _eid_al_fitr(year) + timedelta(days=2),
            "colors": ["#00ff44", "#ffd700", "#ffffff"],
            "category": "cultural",
        },
        {
            "name": "Eid al-Adha",
            "slug": "eid_al_adha",
            "date": _eid_al_adha(year),
            "window_start": _eid_al_adha(year) - timedelta(days=1),
            "window_end": _eid_al_adha(year) + timedelta(days=2),
            "colors": ["#00ff44", "#ffd700", "#ffffff"],
            "category": "cultural",
        },
        {
            "name": "Three Kings Day",
            "slug": "three_kings_day",
            "date": date(year, 1, 6),
            "window_start": date(year, 1, 5),
            "window_end": date(year, 1, 6),
            # Gold, frankincense and myrrh — gift gold, royal purple, resin green.
            "colors": ["#ffd700", "#8800ff", "#00cc66"],
            "category": "cultural",
        },
        {
            "name": "Rosh Hashanah",
            "slug": "rosh_hashanah",
            "date": _rosh_hashanah(year),
            "window_start": _rosh_hashanah(year),
            "window_end": _rosh_hashanah(year) + timedelta(days=2),
            # Apples and honey.
            "colors": ["#ffb300", "#e0004d", "#ffeedd"],
            "category": "cultural",
        },
        {
            "name": "Yom Kippur",
            "slug": "yom_kippur",
            "date": _yom_kippur(year),
            "window_start": _yom_kippur(year),
            "window_end": _yom_kippur(year) + timedelta(days=1),
            # Deliberately colourless — white is the colour of the day. Cool,
            # neutral and warm whites are the one white trio a bulb can tell apart.
            "colors": ["#cce6ff", "#ffffff", "#ffeedd"],
            "category": "cultural",
        },
        {
            "name": "Passover",
            "slug": "passover",
            "date": _passover(year),
            "window_start": _passover(year),
            "window_end": _passover(year) + timedelta(days=2),
            # Seder plate: matzah gold, bitter herbs, wine.
            "colors": ["#ffcc00", "#00cc44", "#cc0033"],
            "category": "cultural",
        },
        {
            "name": "Ramadan",
            "slug": "ramadan",
            "date": _ramadan_start(year),
            "window_start": _ramadan_start(year) - timedelta(days=1),
            "window_end": _ramadan_start(year) + timedelta(days=2),
            # Lantern gold against a night sky. Window covers the first nights
            # rather than the whole month so it doesn't sit on top of everything
            # else for four weeks — widen it in the UI if you want the full month.
            "colors": ["#00cc66", "#ffd700", "#7700ff"],
            "category": "cultural",
        },
        {
            "name": "Election Day",
            "slug": "election_day",
            "date": _election_day(year),
            "window_start": _election_day(year),
            "window_end": _election_day(year),
            # Patriotic but softer than the flag palettes, so it reads as civic.
            "colors": ["#e0004d", "#ffeedd", "#2266ff"],
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
            "colors": ["#0055ff", "#ffeedd", "#00d0ff"],
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
