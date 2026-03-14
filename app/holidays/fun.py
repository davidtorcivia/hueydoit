from datetime import date, timedelta


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _first_weekday(year: int, month: int, weekday: int) -> date:
    return _nth_weekday(year, month, weekday, 1)


def _fridays_13(year: int) -> list[date]:
    result = []
    for month in range(1, 13):
        d = date(year, month, 13)
        if d.weekday() == 4:
            result.append(d)
    return result


def get_fun_holidays(year: int) -> list[dict]:
    holidays = [
        # Groundhog Day
        {
            "name": "Groundhog Day",
            "slug": "groundhog_day",
            "date": date(year, 2, 2),
            "window_start": date(year, 2, 2),
            "window_end": date(year, 2, 2),
            "colors": ["#8B4513", "#00cc00", "#ffeedd"],
            "category": "fun",
        },
        # Super Bowl Sunday — 2nd Sunday of February
        {
            "name": "Super Bowl Sunday",
            "slug": "super_bowl",
            "date": _nth_weekday(year, 2, 6, 2),
            "window_start": _nth_weekday(year, 2, 6, 2),
            "window_end": _nth_weekday(year, 2, 6, 2),
            "colors": ["#ffd700", "#0088ff", "#ff0000"],
            "category": "fun",
        },
        # National Pizza Day
        {
            "name": "National Pizza Day",
            "slug": "pizza_day",
            "date": date(year, 2, 9),
            "window_start": date(year, 2, 9),
            "window_end": date(year, 2, 9),
            "colors": ["#ff4400", "#ffcc00", "#ff8800"],
            "category": "fun",
        },
        # Pi Day
        {
            "name": "Pi Day",
            "slug": "pi_day",
            "date": date(year, 3, 14),
            "window_start": date(year, 3, 14),
            "window_end": date(year, 3, 14),
            "colors": ["#4488ff", "#ffcc00", "#ff4488"],
            "category": "fun",
        },
        # April Fools' Day
        {
            "name": "April Fools' Day",
            "slug": "april_fools",
            "date": date(year, 4, 1),
            "window_start": date(year, 4, 1),
            "window_end": date(year, 4, 1),
            "colors": ["#ff00ff", "#00ffff", "#ffff00"],
            "category": "fun",
        },
        # 4/20
        {
            "name": "4/20",
            "slug": "420",
            "date": date(year, 4, 20),
            "window_start": date(year, 4, 20),
            "window_end": date(year, 4, 20),
            "colors": ["#00cc00", "#88ff00", "#44ff00"],
            "category": "fun",
        },
        # Star Wars Day
        {
            "name": "Star Wars Day",
            "slug": "star_wars_day",
            "date": date(year, 5, 4),
            "window_start": date(year, 5, 4),
            "window_end": date(year, 5, 4),
            "colors": ["#0044ff", "#ff0000", "#00ff00"],
            "category": "fun",
        },
        # National Donut Day — first Friday of June
        {
            "name": "National Donut Day",
            "slug": "donut_day",
            "date": _first_weekday(year, 6, 4),
            "window_start": _first_weekday(year, 6, 4),
            "window_end": _first_weekday(year, 6, 4),
            "colors": ["#ff69b4", "#ffcc00", "#8B4513"],
            "category": "fun",
        },
        # Pride Month kickoff
        {
            "name": "Pride Month",
            "slug": "pride_month",
            "date": date(year, 6, 1),
            "window_start": date(year, 6, 1),
            "window_end": date(year, 6, 30),
            "colors": ["#ff0000", "#ff8800", "#ffff00", "#00cc00", "#0000ff", "#cc00ff"],
            "category": "fun",
        },
        # World Emoji Day
        {
            "name": "World Emoji Day",
            "slug": "emoji_day",
            "date": date(year, 7, 17),
            "window_start": date(year, 7, 17),
            "window_end": date(year, 7, 17),
            "colors": ["#ffcc00", "#ff4444", "#4488ff"],
            "category": "fun",
        },
        # National Ice Cream Day — 3rd Sunday of July
        {
            "name": "National Ice Cream Day",
            "slug": "ice_cream_day",
            "date": _nth_weekday(year, 7, 6, 3),
            "window_start": _nth_weekday(year, 7, 6, 3),
            "window_end": _nth_weekday(year, 7, 6, 3),
            "colors": ["#ff69b4", "#ffeedd", "#8B4513"],
            "category": "fun",
        },
        # International Cat Day
        {
            "name": "International Cat Day",
            "slug": "cat_day",
            "date": date(year, 8, 8),
            "window_start": date(year, 8, 8),
            "window_end": date(year, 8, 8),
            "colors": ["#ff8800", "#ffeedd", "#888888"],
            "category": "fun",
        },
        # Talk Like a Pirate Day
        {
            "name": "Talk Like a Pirate Day",
            "slug": "pirate_day",
            "date": date(year, 9, 19),
            "window_start": date(year, 9, 19),
            "window_end": date(year, 9, 19),
            "colors": ["#ffd700", "#ff0000", "#000000"],
            "category": "fun",
        },
        # National Coffee Day
        {
            "name": "National Coffee Day",
            "slug": "coffee_day",
            "date": date(year, 9, 29),
            "window_start": date(year, 9, 29),
            "window_end": date(year, 9, 29),
            "colors": ["#8B4513", "#ffd700", "#ffeedd"],
            "category": "fun",
        },
        # National Taco Day
        {
            "name": "National Taco Day",
            "slug": "taco_day",
            "date": date(year, 10, 4),
            "window_start": date(year, 10, 4),
            "window_end": date(year, 10, 4),
            "colors": ["#ffcc00", "#ff6600", "#00cc00"],
            "category": "fun",
        },
        # Festivus
        {
            "name": "Festivus",
            "slug": "festivus",
            "date": date(year, 12, 23),
            "window_start": date(year, 12, 23),
            "window_end": date(year, 12, 23),
            "colors": ["#c0c0c0", "#808080", "#ffeedd"],
            "category": "fun",
        },
        # New Year's Eve
        {
            "name": "New Year's Eve",
            "slug": "new_years_eve",
            "date": date(year, 12, 31),
            "window_start": date(year, 12, 31),
            "window_end": date(year, 12, 31),
            "colors": ["#ffd700", "#ff00ff", "#00ffff", "#ffeedd"],
            "category": "fun",
        },
    ]

    # Friday the 13th — computed, could be 1-3 per year
    for f13 in _fridays_13(year):
        holidays.append({
            "name": "Friday the 13th",
            "slug": f"friday_13_{f13.month:02d}",
            "date": f13,
            "window_start": f13,
            "window_end": f13,
            "colors": ["#ff0000", "#000000", "#880000"],
            "category": "fun",
        })

    return holidays
