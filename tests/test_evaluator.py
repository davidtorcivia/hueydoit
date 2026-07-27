"""Rule condition matching — pure logic, no bridge or DB required."""
import pytest

from app.engine.evaluator import _parse_duration, _parse_signed_duration, evaluator

STATES = {
    "time": {"hour": 21, "day_of_week": "monday", "is_weekend": False, "date": "2026-10-15"},
    "calendar": {"season": "fall", "month": 10, "date": "2026-10-15"},
    "solar": {"period": "night", "phase": "after_sunset"},
    "weather": {"temp_f": 48, "condition": "Clear"},
    "holiday": {"active_holiday": "halloween"},
}


def match(condition, states=None):
    return evaluator._match_condition(condition, states or STATES)


def test_always_matches():
    assert match({"match": "always"}) is True


def test_simple_equality_is_case_insensitive():
    assert match({"provider": "calendar", "match": {"season": "FALL"}}) is True
    assert match({"provider": "calendar", "match": {"season": "spring"}}) is False


def test_missing_provider_does_not_match():
    assert match({"provider": "nonexistent", "match": {"x": 1}}) is False


def test_comparison_operators():
    assert match({"provider": "weather", "match": {"temp_f": {"lte": 50}}}) is True
    assert match({"provider": "weather", "match": {"temp_f": {"gt": 50}}}) is False
    assert match({"provider": "weather", "match": {"temp_f": {"gte": 48, "lt": 60}}}) is True


def test_in_operator():
    assert match({"provider": "weather", "match": {"condition": {"in": ["clear", "clouds"]}}}) is True
    assert match({"provider": "weather", "match": {"condition": {"in": ["rain"]}}}) is False


def test_all_of_and_any_of():
    assert match({"all_of": [
        {"provider": "calendar", "match": {"season": "fall"}},
        {"provider": "solar", "match": {"period": "night"}},
    ]}) is True
    assert match({"all_of": [
        {"provider": "calendar", "match": {"season": "fall"}},
        {"provider": "solar", "match": {"period": "day"}},
    ]}) is False
    assert match({"any_of": [
        {"provider": "calendar", "match": {"season": "spring"}},
        {"provider": "solar", "match": {"period": "night"}},
    ]}) is True


@pytest.mark.parametrize("hour,start,end,expected", [
    (21, 18, 23, True),
    (12, 18, 23, False),
    (1, 23, 3, True),     # overnight wrap
    (23, 23, 3, True),
    (5, 23, 3, False),
    (12, 0, 0, True),     # start == end means 24h
])
def test_hour_range_including_overnight_wrap(hour, start, end, expected):
    states = {"time": {**STATES["time"], "hour": hour}}
    cond = {"provider": "time", "match": {"hour_range": {"start": start, "end": end}}}
    assert match(cond, states) is expected


@pytest.mark.parametrize("today,start,end,expected", [
    ("2026-10-15", "09-22", "12-20", True),
    ("2026-08-15", "09-22", "12-20", False),
    ("2026-01-05", "12-21", "03-19", True),   # year wrap
    ("2027-03-19", "12-21", "03-19", True),   # inclusive end
    ("2026-06-15", "12-21", "03-19", False),
])
def test_date_range_including_year_wrap(today, start, end, expected):
    states = {"calendar": {"date": today}}
    cond = {"provider": "calendar", "match": {"date_range": {"start": start, "end": end}}}
    assert match(cond, states) is expected


def test_season_ranges_tile_the_year_without_gaps():
    """Every day must be claimed by exactly one seasonal rule."""
    from datetime import date, timedelta

    seasons = {
        "spring": ("03-20", "06-20"),
        "summer": ("06-21", "09-21"),
        "fall": ("09-22", "12-20"),
        "winter": ("12-21", "03-19"),
    }
    day = date(2026, 1, 1)
    while day < date(2027, 1, 1):
        states = {"calendar": {"date": day.isoformat()}}
        hits = [
            name for name, (s, e) in seasons.items()
            if match({"provider": "calendar", "match": {"date_range": {"start": s, "end": e}}}, states)
        ]
        assert len(hits) == 1, f"{day} matched {hits}"
        day += timedelta(days=1)


def test_dot_path_resolution():
    states = {"webhook": {"payload": {"nested": {"value": 42}}}}
    assert match({"provider": "webhook", "match": {"payload.nested.value": 42}}, states) is True
    assert match({"provider": "webhook", "match": {"payload.missing.value": 42}}, states) is False


@pytest.mark.parametrize("text,seconds", [
    ("30s", 30), ("15m", 900), ("1h", 3600), ("45", 2700),
])
def test_parse_duration(text, seconds):
    assert _parse_duration(text).total_seconds() == seconds


@pytest.mark.parametrize("text,seconds", [
    ("-30m", -1800), ("+1h", 3600), ("30m", 1800), ("-1h", -3600),
])
def test_parse_signed_duration(text, seconds):
    assert _parse_signed_duration(text).total_seconds() == seconds
