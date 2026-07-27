from datetime import date, timedelta


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Get the nth occurrence of a weekday in a month. weekday: 0=Mon, 6=Sun."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """Get the last occurrence of a weekday in a month."""
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    offset = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=offset)


def get_us_federal_holidays(year: int) -> list[dict]:
    return [
        {
            "name": "New Year's Day",
            "slug": "new_years",
            "date": date(year, 1, 1),
            "window_start": date(year - 1, 12, 30),
            "window_end": date(year, 1, 2),
            "colors": ["#ffd700", "#ffeedd", "#00d0ff"],
            "category": "us_federal",
        },
        {
            "name": "Martin Luther King Jr. Day",
            "slug": "mlk_day",
            "date": _nth_weekday(year, 1, 0, 3),
            "window_start": _nth_weekday(year, 1, 0, 3) - timedelta(days=1),
            "window_end": _nth_weekday(year, 1, 0, 3),
            "colors": ["#ff0000", "#ffd700", "#00cc00"],
            "category": "us_federal",
        },
        {
            "name": "Presidents' Day",
            "slug": "presidents_day",
            "date": _nth_weekday(year, 2, 0, 3),
            "window_start": _nth_weekday(year, 2, 0, 3) - timedelta(days=1),
            "window_end": _nth_weekday(year, 2, 0, 3),
            "colors": ["#ff0000", "#ffffff", "#0000ff"],
            "category": "us_federal",
        },
        {
            "name": "Memorial Day",
            "slug": "memorial_day",
            "date": _last_weekday(year, 5, 0),
            "window_start": _last_weekday(year, 5, 0) - timedelta(days=1),
            "window_end": _last_weekday(year, 5, 0),
            "colors": ["#ff0000", "#ffffff", "#0000ff"],
            "category": "us_federal",
        },
        {
            "name": "Juneteenth",
            "slug": "juneteenth",
            "date": date(year, 6, 19),
            "window_start": date(year, 6, 18),
            "window_end": date(year, 6, 19),
            "colors": ["#ff0000", "#ffd700", "#00cc00"],
            "category": "us_federal",
        },
        {
            "name": "Independence Day",
            "slug": "independence_day",
            "date": date(year, 7, 4),
            "window_start": date(year, 7, 1),
            "window_end": date(year, 7, 4),
            "colors": ["#ff0000", "#ffffff", "#0000ff"],
            "category": "us_federal",
        },
        {
            "name": "Labor Day",
            "slug": "labor_day",
            "date": _nth_weekday(year, 9, 0, 1),
            "window_start": _nth_weekday(year, 9, 0, 1) - timedelta(days=1),
            "window_end": _nth_weekday(year, 9, 0, 1),
            "colors": ["#ff0000", "#ffffff", "#0000ff"],
            "category": "us_federal",
        },
        {
            "name": "Columbus Day",
            "slug": "columbus_day",
            "date": _nth_weekday(year, 10, 0, 2),
            "window_start": _nth_weekday(year, 10, 0, 2) - timedelta(days=1),
            "window_end": _nth_weekday(year, 10, 0, 2),
            "colors": ["#ff0000", "#ffffff", "#0000ff"],
            "category": "us_federal",
        },
        {
            "name": "Veterans Day",
            "slug": "veterans_day",
            "date": date(year, 11, 11),
            "window_start": date(year, 11, 10),
            "window_end": date(year, 11, 11),
            "colors": ["#ff0000", "#ffffff", "#0000ff"],
            "category": "us_federal",
        },
        {
            "name": "Thanksgiving",
            "slug": "thanksgiving",
            "date": _nth_weekday(year, 11, 3, 4),
            "window_start": _nth_weekday(year, 11, 3, 4) - timedelta(days=1),
            "window_end": _nth_weekday(year, 11, 3, 4),
            "colors": ["#ff8c00", "#ffcc00", "#b3001b"],
            "category": "us_federal",
        },
        {
            "name": "Christmas",
            "slug": "christmas",
            "date": date(year, 12, 25),
            "window_start": date(year, 12, 20),
            "window_end": date(year, 12, 26),
            "colors": ["#ff0000", "#00ff00", "#ffffff"],
            "category": "us_federal",
        },
    ]
