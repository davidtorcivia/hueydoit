"""Solar provider — the error path in particular.

The fallback used to return period="daytime", but rules match `period` against
"day"/"night" ("daytime" is a *phase* value). So whenever astral failed, every
solar-conditioned rule silently stopped matching and the lights went dark.
"""
from unittest.mock import patch

import pytest

from app.providers.solar import SolarProvider

VALID_PERIODS = {"day", "night"}
VALID_PHASES = {"daytime", "before_sunrise", "after_sunset"}


def test_compute_fresh_returns_valid_period():
    state = SolarProvider.compute_fresh("America/New_York", 40.704941, -73.914642)
    assert state["period"] in VALID_PERIODS
    assert state["phase"] in VALID_PHASES


def test_compute_fresh_fallback_uses_a_matchable_period():
    with patch("app.providers.solar.sun", side_effect=RuntimeError("astral down")):
        state = SolarProvider.compute_fresh("America/New_York", 40.704941, -73.914642)
    assert state["period"] in VALID_PERIODS, "fallback period must be matchable by rules"
    assert state["phase"] in VALID_PHASES


@pytest.mark.asyncio_compat
def test_fetch_fallback_uses_a_matchable_period():
    import asyncio

    with patch("app.providers.solar.sun", side_effect=RuntimeError("astral down")):
        state = asyncio.run(SolarProvider().fetch())
    assert state["period"] in VALID_PERIODS
    assert state["phase"] in VALID_PHASES
    assert "error" in state, "the failure should still be surfaced"


def test_solar_period_matches_a_rule_condition():
    """End to end: the value the provider emits must satisfy a real condition."""
    from app.engine.evaluator import evaluator

    with patch("app.providers.solar.sun", side_effect=RuntimeError("astral down")):
        state = SolarProvider.compute_fresh("America/New_York", 40.704941, -73.914642)

    matched = any(
        evaluator._match_condition({"provider": "solar", "match": {"period": p}}, {"solar": state})
        for p in VALID_PERIODS
    )
    assert matched, f"period {state['period']!r} matches no rule"
