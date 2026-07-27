"""Date and palette correctness for the holiday system.

These cover the four bugs that shipped undetected: the dead Hijri conversion,
the Feb 29 crash, year-shifted nth-weekday holidays, and bulb-hostile colours.
"""
import colorsys
from datetime import date

import pytest

from app.holidays.cultural import (
    _easter,
    _eid_al_adha,
    _eid_al_fitr,
    _hijri_event,
    _nth_weekday,
    get_cultural_holidays,
)
from app.holidays.fun import get_fun_holidays
from app.holidays.international import get_international_holidays
from app.holidays.loader import Holiday, is_holiday_active, shift_year
from app.holidays.seasonal import get_seasonal_holidays
from app.holidays.us_federal import get_us_federal_holidays

ALL_SOURCES = [
    get_us_federal_holidays,
    get_cultural_holidays,
    get_international_holidays,
    get_fun_holidays,
    get_seasonal_holidays,
]


def all_holidays(year: int) -> list[dict]:
    return [h for src in ALL_SOURCES for h in src(year)]


# --------------------------------------------------------------------------
# Hijri conversion — was searching ~43 years off and never matching
# --------------------------------------------------------------------------

def test_hijri_event_resolves_beyond_lookup_table():
    """The lookup tables stop at 2030; computation must take over, not a fixed date."""
    assert _hijri_event(2031, 10, 1) is not None
    assert _hijri_event(2040, 10, 1) is not None


@pytest.mark.parametrize("year,expected", [
    (2025, date(2025, 3, 30)),
    (2026, date(2026, 3, 20)),
    (2027, date(2027, 3, 10)),
])
def test_eid_al_fitr_matches_known_dates(year, expected):
    """Computed dates must agree with the hand-verified table within a day."""
    assert abs((_eid_al_fitr(year) - expected).days) <= 1


@pytest.mark.parametrize("year,expected", [
    (2025, date(2025, 6, 7)),
    (2026, date(2026, 5, 27)),
])
def test_eid_al_adha_matches_known_dates(year, expected):
    assert abs((_eid_al_adha(year) - expected).days) <= 1


def test_eid_does_not_collapse_to_fixed_fallback_date():
    """The old code returned March 15 / June 15 forever after 2030."""
    fitr = [_eid_al_fitr(y) for y in range(2031, 2036)]
    assert len({(d.month, d.day) for d in fitr}) > 1, "Eid al-Fitr stuck on a fixed date"

    adha = [_eid_al_adha(y) for y in range(2031, 2036)]
    assert len({(d.month, d.day) for d in adha}) > 1, "Eid al-Adha stuck on a fixed date"


def test_eid_moves_earlier_each_year():
    """Hijri dates drift ~11 days earlier per Gregorian year."""
    a, b = _eid_al_fitr(2026), _eid_al_fitr(2027)
    assert 5 <= (a - b.replace(year=2026)).days <= 15


# --------------------------------------------------------------------------
# Feb 29 — .replace(year=...) raised ValueError 3 years out of 4
# --------------------------------------------------------------------------

def test_shift_year_handles_leap_day():
    assert shift_year(date(2028, 2, 29), 2027) == date(2027, 2, 28)
    assert shift_year(date(2028, 2, 29), 2032) == date(2032, 2, 29)


def test_leap_day_holiday_does_not_crash_evaluation():
    leap = Holiday(
        name="Leap Day", slug="leap_day", date=date(2028, 2, 29),
        window_start=date(2028, 2, 29), window_end=date(2028, 2, 29),
        colors=["#00ff00"], category="custom", recurring=True,
    )
    assert is_holiday_active(leap, date(2027, 2, 28)) is True
    assert is_holiday_active(leap, date(2027, 7, 1)) is False


def test_year_wrapping_window_stays_active():
    """Kwanzaa-style windows that cross New Year."""
    kwanzaa = Holiday(
        name="Kwanzaa", slug="kwanzaa", date=date(2026, 12, 26),
        window_start=date(2026, 12, 26), window_end=date(2027, 1, 1),
        colors=["#ff0000"], category="international", recurring=True,
    )
    assert is_holiday_active(kwanzaa, date(2026, 12, 28)) is True
    assert is_holiday_active(kwanzaa, date(2026, 6, 15)) is False


def test_disabled_holiday_never_active():
    h = Holiday(
        name="Off", slug="off", date=date(2026, 7, 4),
        window_start=date(2026, 7, 4), window_end=date(2026, 7, 4),
        colors=[], category="custom", enabled=False,
    )
    assert is_holiday_active(h, date(2026, 7, 4)) is False


# --------------------------------------------------------------------------
# nth-weekday holidays must be recomputed per year, never year-shifted
# --------------------------------------------------------------------------

@pytest.mark.parametrize("year,expected", [
    (2026, date(2026, 1, 19)),
    (2027, date(2027, 1, 18)),
    (2028, date(2028, 1, 17)),
])
def test_mlk_day_is_third_monday_of_january(year, expected):
    mlk = next(h for h in get_us_federal_holidays(year) if h["slug"] == "mlk_day")
    assert mlk["date"] == expected
    assert mlk["date"].weekday() == 0


def test_year_shifting_an_nth_weekday_holiday_is_wrong():
    """Guards the bug directly: shifting the year lands on the wrong weekday."""
    mlk_2026 = next(h for h in get_us_federal_holidays(2026) if h["slug"] == "mlk_day")["date"]
    mlk_2027 = next(h for h in get_us_federal_holidays(2027) if h["slug"] == "mlk_day")["date"]
    assert shift_year(mlk_2026, 2027) != mlk_2027


def test_mothers_and_fathers_day():
    mothers = next(h for h in get_cultural_holidays(2026) if h["slug"] == "mothers_day")
    fathers = next(h for h in get_cultural_holidays(2026) if h["slug"] == "fathers_day")
    assert mothers["date"] == date(2026, 5, 10)
    assert fathers["date"] == date(2026, 6, 21)
    assert mothers["date"].weekday() == 6
    assert fathers["date"].weekday() == 6


def test_nth_weekday_helper():
    assert _nth_weekday(2026, 1, 0, 3) == date(2026, 1, 19)
    assert _nth_weekday(2026, 11, 3, 4) == date(2026, 11, 26)


@pytest.mark.parametrize("year,expected", [
    (2026, date(2026, 4, 5)),
    (2027, date(2027, 3, 28)),
])
def test_easter_computus(year, expected):
    assert _easter(year) == expected


# --------------------------------------------------------------------------
# Palettes must be reproducible on a bulb (chromaticity only — see effects.py)
# --------------------------------------------------------------------------

def _hsl(hex_color: str):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, light, sat = colorsys.rgb_to_hls(r, g, b)
    return hue * 360, sat, light


@pytest.mark.parametrize("year", [2026, 2027])
def test_no_black_in_any_palette(year):
    """#000000 hits the total==0 branch in hex_to_xy and renders as white."""
    offenders = [
        (h["slug"], c) for h in all_holidays(year) for c in h["colors"] if c == "#000000"
    ]
    assert offenders == []


@pytest.mark.parametrize("year", [2026, 2027])
def test_no_greys_in_any_palette(year):
    """Greys are indistinguishable from white once luminance is discarded."""
    offenders = []
    for h in all_holidays(year):
        for c in h["colors"]:
            _, sat, light = _hsl(c)
            if sat < 0.25 and 0.15 < light < 0.9:
                offenders.append((h["slug"], c))
    assert offenders == []


@pytest.mark.parametrize("year", [2026, 2027])
def test_palette_hues_are_distinguishable(year):
    """Two saturated colours under ~12 deg apart read as one colour on the strip."""
    offenders = []
    for h in all_holidays(year):
        sats = [(_hsl(c)[0], c) for c in h["colors"] if _hsl(c)[1] > 0.5 and _hsl(c)[2] < 0.85]
        for i in range(len(sats)):
            for j in range(i + 1, len(sats)):
                delta = abs(sats[i][0] - sats[j][0]) % 360
                if min(delta, 360 - delta) < 12:
                    offenders.append((h["slug"], sats[i][1], sats[j][1]))
    assert offenders == []


@pytest.mark.parametrize("year", [2026, 2027])
def test_every_holiday_is_well_formed(year):
    for h in all_holidays(year):
        assert h["colors"], f"{h['slug']} has no colours"
        assert h["window_start"] <= h["window_end"], f"{h['slug']} window inverted"
        for c in h["colors"]:
            assert c.startswith("#") and len(c) == 7, f"{h['slug']} bad colour {c}"


def test_slugs_are_unique_within_a_year():
    slugs = [h["slug"] for h in all_holidays(2026)]
    assert len(slugs) == len(set(slugs))
