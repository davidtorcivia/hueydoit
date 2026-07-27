"""Colour conversion and light-command construction."""
import pytest

from app.bridge.effects import (
    GAMUT_C,
    build_individual_gradient_commands,
    build_light_command,
    clamp_xy_to_gamut,
    ct_to_mirek,
    hex_to_xy,
    is_ct,
)


def _inside(x: float, y: float, tol: float = 1e-6) -> bool:
    r, g, b = GAMUT_C

    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    p = (x, y)
    d1, d2, d3 = sign(p, r, g), sign(p, g, b), sign(p, b, r)
    return not ((d1 < -tol or d2 < -tol or d3 < -tol) and (d1 > tol or d2 > tol or d3 > tol))


@pytest.mark.parametrize("hex_color", [
    "#ff0000", "#00ff00", "#0000ff", "#ffffff", "#ffe600",
    "#ff0099", "#9e0022", "#00d0ff", "#cce6ff", "#7700ff",
])
def test_hex_to_xy_always_lands_inside_gamut(hex_color):
    x, y = hex_to_xy(hex_color)
    assert _inside(x, y), f"{hex_color} -> ({x}, {y}) outside gamut C"


def test_clamp_leaves_interior_points_untouched():
    assert clamp_xy_to_gamut(0.3127, 0.3290) == (0.3127, 0.329)


def test_clamp_pulls_outside_points_to_the_edge():
    x, y = clamp_xy_to_gamut(0.9, 0.05)
    assert _inside(x, y)
    assert (x, y) != (0.9, 0.05)


def test_black_maps_to_white_point():
    """Documents the trap: a bulb has no black, so #000000 becomes D65 white."""
    assert hex_to_xy("#000000") == (0.3127, 0.3290)


def test_luminance_is_discarded():
    """Why palettes must vary by hue: dark and bright reds are the same chromaticity."""
    assert hex_to_xy("#880000") == hex_to_xy("#ff0000")


def test_greys_collapse_onto_white():
    assert hex_to_xy("#808080") == hex_to_xy("#ffffff")


def test_warm_and_cool_whites_stay_distinct():
    """These are the correct way to express a silver/white palette."""
    assert hex_to_xy("#ffeedd") != hex_to_xy("#cce6ff")


def test_ct_helpers():
    assert is_ct("ct:370") and not is_ct("#ff0000")
    assert ct_to_mirek("ct:370") == 370


def test_build_light_command_off():
    assert build_light_command({"mode": "off"}, "light") == {"on": {"on": False}}


def test_build_light_command_static():
    cmd = build_light_command(
        {"mode": "static", "colors": ["#ff0000"], "brightness": 80}, "light"
    )
    assert cmd["on"] == {"on": True}
    assert cmd["dimming"] == {"brightness": 80.0}
    assert "xy" in cmd["color"]


def test_brightness_is_clamped_to_valid_range():
    assert build_light_command({"brightness": 0}, "light")["dimming"]["brightness"] == 1.0
    assert build_light_command({"brightness": 500}, "light")["dimming"]["brightness"] == 100.0


def test_ct_colour_uses_colour_temperature_not_xy():
    cmd = build_light_command({"mode": "static", "colors": ["ct:370"]}, "light")
    assert cmd["color_temperature"] == {"mirek": 370}
    assert "color" not in cmd


def test_gradient_only_on_grouped_lights():
    effect = {"mode": "gradient", "colors": ["#ff0000", "#0000ff"]}
    assert "gradient" in build_light_command(effect, "grouped_light")
    assert "gradient" not in build_light_command(effect, "light")


def test_individual_gradient_spans_the_palette():
    cmds = build_individual_gradient_commands(["#ff0000", "#0000ff"], 3)
    assert len(cmds) == 3
    assert all(c["on"] == {"on": True} for c in cmds)
    assert cmds[0]["color"]["xy"] != cmds[-1]["color"]["xy"]


def test_individual_gradient_handles_empty_input():
    assert build_individual_gradient_commands([], 3) == []
    assert build_individual_gradient_commands(["#ff0000"], 0) == []
