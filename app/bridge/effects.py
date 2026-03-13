import logging
import math

logger = logging.getLogger(__name__)


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

    return (round(x / total, 4), round(y / total, 4))


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


def _brightness_to_dimming(brightness: int) -> dict:
    return {"brightness": max(1.0, min(100.0, float(brightness)))}


def _transition_to_dynamics(transition_ms: int) -> dict:
    return {"duration": transition_ms}


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
            x, y = hex_to_xy(colors[0])
            cmd["color"] = {"xy": {"x": x, "y": y}}

    elif mode == "breathe":
        if colors:
            x, y = hex_to_xy(colors[0])
            cmd["color"] = {"xy": {"x": x, "y": y}}
        cmd["alert"] = {"action": "breathe"}

    elif mode == "cycle":
        if len(colors) >= 2:
            palette_colors = []
            for c in colors:
                x, y = hex_to_xy(c)
                palette_colors.append({"color": {"xy": {"x": x, "y": y}}})

            cycle_interval = effect_config.get("cycle_interval", 30)
            cmd["dynamics"] = {"duration": cycle_interval * 1000}
            cmd["color"] = {"xy": {"x": palette_colors[0]["color"]["xy"]["x"],
                                   "y": palette_colors[0]["color"]["xy"]["y"]}}

            if target_type == "grouped_light":
                cmd["dynamics"]["palette"] = palette_colors
        elif colors:
            x, y = hex_to_xy(colors[0])
            cmd["color"] = {"xy": {"x": x, "y": y}}

    elif mode == "gradient":
        if target_type == "grouped_light" and colors:
            gradient_points = []
            for c in colors:
                x, y = hex_to_xy(c)
                gradient_points.append({"color": {"xy": {"x": x, "y": y}}})
            cmd["gradient"] = {"points": gradient_points, "mode": "interpolated_palette"}
        elif colors:
            x, y = hex_to_xy(colors[0])
            cmd["color"] = {"xy": {"x": x, "y": y}}

    return cmd


def build_individual_gradient_commands(colors: list[str], light_count: int, brightness: int | None = None) -> list[dict]:
    if not colors or light_count == 0:
        return []

    commands = []
    for i in range(light_count):
        t = i / max(1, light_count - 1)
        color_idx = t * (len(colors) - 1)
        lower = int(math.floor(color_idx))
        upper = min(lower + 1, len(colors) - 1)
        frac = color_idx - lower

        c1 = colors[lower].lstrip("#")
        c2 = colors[upper].lstrip("#")
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
