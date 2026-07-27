import logging
import math

logger = logging.getLogger(__name__)


# Philips Hue Gamut C — the widest of the three, covering the colour-capable
# strip/bulb families. Clamping here means the xy we send is already inside the
# bulb's triangle, so the colour it renders matches what the UI previews instead
# of being silently clipped somewhere in the bridge.
GAMUT_C = ((0.6915, 0.3038), (0.1700, 0.7000), (0.1532, 0.0475))  # red, green, blue


def _closest_point_on_segment(a, b, p):
    ax, ay = a
    bx, by = b
    px, py = p
    abx, aby = bx - ax, by - ay
    denom = abx * abx + aby * aby
    if denom == 0:
        return a
    t = ((px - ax) * abx + (py - ay) * aby) / denom
    t = max(0.0, min(1.0, t))
    return (ax + abx * t, ay + aby * t)


def clamp_xy_to_gamut(x: float, y: float, gamut=GAMUT_C) -> tuple[float, float]:
    """Clamp an xy chromaticity into the bulb's reproducible triangle."""
    r, g, b = gamut

    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    p = (x, y)
    d1, d2, d3 = sign(p, r, g), sign(p, g, b), sign(p, b, r)
    has_neg = d1 < 0 or d2 < 0 or d3 < 0
    has_pos = d1 > 0 or d2 > 0 or d3 > 0
    if not (has_neg and has_pos):
        return (round(x, 4), round(y, 4))  # already inside

    candidates = [
        _closest_point_on_segment(r, g, p),
        _closest_point_on_segment(g, b, p),
        _closest_point_on_segment(b, r, p),
    ]
    best = min(candidates, key=lambda c: (c[0] - x) ** 2 + (c[1] - y) ** 2)

    # Rounding an edge point to the 4 decimals the Hue API takes can push it back
    # outside the triangle, so pull it a hair toward the centre first. The shift is
    # ~3e-4 in xy — well below any visible difference, well above rounding error.
    cx = (r[0] + g[0] + b[0]) / 3
    cy = (r[1] + g[1] + b[1]) / 3
    bx = best[0] + (cx - best[0]) * 1e-3
    by = best[1] + (cy - best[1]) * 1e-3
    return (round(bx, 4), round(by, 4))


def hex_to_xy(hex_color: str) -> tuple[float, float]:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0

    r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
    g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
    b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92

    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

    total = x + y + z
    if total == 0:
        return (0.3127, 0.3290)

    return clamp_xy_to_gamut(x / total, y / total)


def xy_to_hex(x: float, y: float, brightness: float = 1.0) -> str:
    z = 1.0 - x - y
    Y = brightness
    X = (Y / y) * x if y > 0 else 0
    Z = (Y / y) * z if y > 0 else 0

    r = X * 1.656492 - Y * 0.354851 - Z * 0.255038
    g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
    b = X * 0.051713 - Y * 0.121364 + Z * 1.011530

    r = 1.055 * (r ** (1.0 / 2.4)) - 0.055 if r > 0.0031308 else 12.92 * r
    g = 1.055 * (g ** (1.0 / 2.4)) - 0.055 if g > 0.0031308 else 12.92 * g
    b = 1.055 * (b ** (1.0 / 2.4)) - 0.055 if b > 0.0031308 else 12.92 * b

    r = max(0, min(1, r))
    g = max(0, min(1, g))
    b = max(0, min(1, b))

    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def is_ct(color: str) -> bool:
    """Check if a color string is a color temperature value (e.g., 'ct:370')."""
    return isinstance(color, str) and color.startswith("ct:")


def ct_to_mirek(color: str) -> int:
    """Extract mirek value from a ct: color string."""
    return int(color.split(":")[1])


def _brightness_to_dimming(brightness: int) -> dict:
    return {"brightness": max(1.0, min(100.0, float(brightness)))}


def _transition_to_dynamics(transition_ms: int) -> dict:
    return {"duration": transition_ms}


def _apply_color(cmd: dict, color: str):
    """Apply a color (hex or ct:mirek) to a light command dict."""
    if is_ct(color):
        cmd["color_temperature"] = {"mirek": ct_to_mirek(color)}
    else:
        x, y = hex_to_xy(color)
        cmd["color"] = {"xy": {"x": x, "y": y}}


def _color_to_palette_entry(color: str) -> dict:
    """Convert a color to a palette/gradient entry dict."""
    if is_ct(color):
        return {"color_temperature": {"mirek": ct_to_mirek(color)}}
    x, y = hex_to_xy(color)
    return {"color": {"xy": {"x": x, "y": y}}}


def build_light_command(effect_config: dict, target_type: str) -> dict:
    mode = effect_config.get("mode", "static")

    if mode == "off":
        return {"on": {"on": False}}

    cmd: dict = {"on": {"on": True}}

    brightness = effect_config.get("brightness")
    if brightness is not None:
        cmd["dimming"] = _brightness_to_dimming(brightness)

    transition = effect_config.get("transition")
    if transition is not None:
        cmd["dynamics"] = _transition_to_dynamics(transition)

    colors = effect_config.get("colors", [])

    if mode == "static":
        if colors:
            _apply_color(cmd, colors[0])

    elif mode == "breathe":
        # Set color only; the continuous pulse is handled by the scheduler's breathe loop
        if colors:
            _apply_color(cmd, colors[0])

    elif mode == "cycle":
        if len(colors) >= 2:
            palette_colors = []
            for c in colors:
                palette_colors.append(_color_to_palette_entry(c))

            cycle_interval = effect_config.get("cycle_interval", 30)
            cmd["dynamics"] = {"duration": cycle_interval * 1000}
            _apply_color(cmd, colors[0])

            if target_type == "grouped_light":
                cmd["dynamics"]["palette"] = palette_colors
        elif colors:
            _apply_color(cmd, colors[0])

    elif mode == "gradient":
        if target_type == "grouped_light" and colors:
            gradient_points = []
            for c in colors:
                gradient_points.append(_color_to_palette_entry(c))
            cmd["gradient"] = {"points": gradient_points, "mode": "interpolated_palette"}
        elif colors:
            _apply_color(cmd, colors[0])

    return cmd


def build_individual_gradient_commands(colors: list[str], light_count: int, brightness: int | None = None) -> list[dict]:
    if not colors or light_count == 0:
        return []

    # Filter to only hex colors for interpolation; ct: colors can't be interpolated in RGB space
    hex_colors = [c for c in colors if not is_ct(c)]
    if not hex_colors:
        # All color temperature — just spread them evenly
        commands = []
        for i in range(light_count):
            idx = min(int(i / max(1, light_count - 1) * (len(colors) - 1)), len(colors) - 1)
            cmd: dict = {"on": {"on": True}}
            _apply_color(cmd, colors[idx])
            if brightness is not None:
                cmd["dimming"] = _brightness_to_dimming(brightness)
            commands.append(cmd)
        return commands

    commands = []
    for i in range(light_count):
        t = i / max(1, light_count - 1)
        color_idx = t * (len(hex_colors) - 1)
        lower = int(math.floor(color_idx))
        upper = min(lower + 1, len(hex_colors) - 1)
        frac = color_idx - lower

        c1 = hex_colors[lower].lstrip("#")
        c2 = hex_colors[upper].lstrip("#")
        r = int(int(c1[0:2], 16) * (1 - frac) + int(c2[0:2], 16) * frac)
        g = int(int(c1[2:4], 16) * (1 - frac) + int(c2[2:4], 16) * frac)
        b = int(int(c1[4:6], 16) * (1 - frac) + int(c2[4:6], 16) * frac)
        interpolated = f"#{r:02x}{g:02x}{b:02x}"

        cmd = {"on": {"on": True}}
        x, y = hex_to_xy(interpolated)
        cmd["color"] = {"xy": {"x": x, "y": y}}
        if brightness is not None:
            cmd["dimming"] = _brightness_to_dimming(brightness)
        commands.append(cmd)

    return commands
