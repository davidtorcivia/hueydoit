/**
 * Colour maths for Hue lights.
 *
 * This is a direct port of app/bridge/effects.py — same sRGB D65 matrices, same
 * gamut C triangle, same centroid nudge, same 4dp rounding. It has to stay in
 * step: if the two drift, the picker previews a colour the bulb won't produce,
 * which is worse than not previewing at all. tests/test_effects.py pins the
 * Python side; check both when changing either.
 *
 * The key fact driving all of this: only chromaticity (x, y) reaches the bulb.
 * Brightness is a separate field, so a hex's lightness is thrown away —
 * #880000 and #ff0000 are the same colour on the strip. Palettes must differ in
 * HUE, not lightness.
 */

// Philips Hue Gamut C — red, green, blue primaries.
export const GAMUT_C = [[0.6915, 0.3038], [0.17, 0.7], [0.1532, 0.0475]];

// Two colours closer than this in hue read as one colour on the strip.
// Must match test_palette_hues_are_distinguishable in tests/test_holidays.py.
export const MIN_HUE_SEPARATION = 12;

function gammaExpand(c) {
  return c > 0.04045 ? Math.pow((c + 0.055) / 1.055, 2.4) : c / 12.92;
}

function gammaCompress(c) {
  return c > 0.0031308 ? 1.055 * Math.pow(c, 1 / 2.4) - 0.055 : 12.92 * c;
}

function closestPointOnSegment(a, b, p) {
  const [ax, ay] = a, [bx, by] = b, [px, py] = p;
  const abx = bx - ax, aby = by - ay;
  const denom = abx * abx + aby * aby;
  if (denom === 0) return a;
  let t = ((px - ax) * abx + (py - ay) * aby) / denom;
  t = Math.max(0, Math.min(1, t));
  return [ax + abx * t, ay + aby * t];
}

export function isInsideGamut(x, y, gamut = GAMUT_C) {
  const [r, g, b] = gamut;
  const sign = (p1, p2, p3) =>
    (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1]);
  const p = [x, y];
  const d1 = sign(p, r, g), d2 = sign(p, g, b), d3 = sign(p, b, r);
  const hasNeg = d1 < 0 || d2 < 0 || d3 < 0;
  const hasPos = d1 > 0 || d2 > 0 || d3 > 0;
  return !(hasNeg && hasPos);
}

export function clampXyToGamut(x, y, gamut = GAMUT_C) {
  const [r, g, b] = gamut;
  if (isInsideGamut(x, y, gamut)) {
    return [round4(x), round4(y)];
  }
  const p = [x, y];
  const candidates = [
    closestPointOnSegment(r, g, p),
    closestPointOnSegment(g, b, p),
    closestPointOnSegment(b, r, p),
  ];
  let best = candidates[0];
  let bestDist = Infinity;
  for (const c of candidates) {
    const d = (c[0] - x) ** 2 + (c[1] - y) ** 2;
    if (d < bestDist) { bestDist = d; best = c; }
  }
  const cx = (r[0] + g[0] + b[0]) / 3;
  const cy = (r[1] + g[1] + b[1]) / 3;
  return [round4(best[0] + (cx - best[0]) * 1e-3), round4(best[1] + (cy - best[1]) * 1e-3)];
}

function round4(v) {
  return Math.round(v * 10000) / 10000;
}

export function hexToXy(hex) {
  const h = hex.replace('#', '');
  const r = gammaExpand(parseInt(h.slice(0, 2), 16) / 255);
  const g = gammaExpand(parseInt(h.slice(2, 4), 16) / 255);
  const b = gammaExpand(parseInt(h.slice(4, 6), 16) / 255);

  const x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375;
  const y = r * 0.2126729 + g * 0.7151522 + b * 0.072175;
  const z = r * 0.0193339 + g * 0.119192 + b * 0.9503041;

  const total = x + y + z;
  if (total === 0) return [0.3127, 0.329];
  return clampXyToGamut(x / total, y / total);
}

export function xyToHex(x, y, brightness = 1.0) {
  const z = 1.0 - x - y;
  const Y = brightness;
  const X = y > 0 ? (Y / y) * x : 0;
  const Z = y > 0 ? (Y / y) * z : 0;

  let r = X * 3.2404542 - Y * 1.5371385 - Z * 0.4985314;
  let g = -X * 0.969266 + Y * 1.8760108 + Z * 0.041556;
  let b = X * 0.0556434 - Y * 0.2040259 + Z * 1.0572252;

  const peak = Math.max(r, g, b);
  if (peak > 1.0) { r /= peak; g /= peak; b /= peak; }

  const to255 = (c) => {
    const v = Math.max(0, Math.min(1, gammaCompress(c)));
    return Math.round(v * 255).toString(16).padStart(2, '0');
  };
  return `#${to255(r)}${to255(g)}${to255(b)}`;
}

/**
 * The colour the bulb will actually render for a given hex, at full brightness.
 * Differs from the input whenever the colour sits outside the bulb's gamut.
 */
export function bulbPreview(hex) {
  if (isCt(hex)) return ctToHex(hex);
  if (!isHex(hex)) return '#888888';
  const [x, y] = hexToXy(hex);
  return xyToHex(x, y);
}

/** True when the bulb cannot reproduce the chosen colour faithfully. */
export function isOutOfGamut(hex) {
  if (!isHex(hex)) return false;
  const h = hex.replace('#', '');
  const r = gammaExpand(parseInt(h.slice(0, 2), 16) / 255);
  const g = gammaExpand(parseInt(h.slice(2, 4), 16) / 255);
  const b = gammaExpand(parseInt(h.slice(4, 6), 16) / 255);
  const X = r * 0.4124564 + g * 0.3575761 + b * 0.1804375;
  const Y = r * 0.2126729 + g * 0.7151522 + b * 0.072175;
  const Z = r * 0.0193339 + g * 0.119192 + b * 0.9503041;
  const total = X + Y + Z;
  if (total === 0) return false;
  return !isInsideGamut(X / total, Y / total);
}

// ---------------------------------------------------------------------------
// Colour temperature
// ---------------------------------------------------------------------------

export function isCt(c) {
  return typeof c === 'string' && c.startsWith('ct:');
}

export function ctMirek(c) {
  return parseInt(String(c).replace('ct:', ''), 10);
}

export function ctKelvin(c) {
  return Math.round(1000000 / ctMirek(c));
}

/** Approximate on-screen appearance of a colour temperature. */
export function ctToHex(c) {
  const kelvin = ctKelvin(c) / 100;
  let r, g, b;
  if (kelvin <= 66) {
    r = 255;
    g = 99.47 * Math.log(kelvin) - 161.12;
    b = kelvin <= 19 ? 0 : 138.52 * Math.log(kelvin - 10) - 305.04;
  } else {
    r = 329.7 * Math.pow(kelvin - 60, -0.1332);
    g = 288.12 * Math.pow(kelvin - 60, -0.0755);
    b = 255;
  }
  const clamp = (v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0');
  return `#${clamp(r)}${clamp(g)}${clamp(b)}`;
}

// ---------------------------------------------------------------------------
// HSL helpers
// ---------------------------------------------------------------------------

export function isHex(c) {
  return typeof c === 'string' && /^#[0-9a-f]{6}$/i.test(c);
}

export function hslToHex(h, s, l) {
  s /= 100; l /= 100;
  const a = s * Math.min(l, 1 - l);
  const f = (n) => {
    const k = (n + h / 30) % 12;
    const color = l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
    return Math.round(255 * Math.max(0, Math.min(1, color))).toString(16).padStart(2, '0');
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

export function hexToHsl(hex) {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16) / 255;
  const g = parseInt(h.slice(2, 4), 16) / 255;
  const b = parseInt(h.slice(4, 6), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let hue = 0, sat = 0;
  const light = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    sat = light > 0.5 ? d / (2 - max - min) : d / (max + min);
    if (max === r) hue = ((g - b) / d + (g < b ? 6 : 0)) * 60;
    else if (max === g) hue = ((b - r) / d + 2) * 60;
    else hue = ((r - g) / d + 4) * 60;
  }
  return [Math.round(hue), Math.round(sat * 100), Math.round(light * 100)];
}

// ---------------------------------------------------------------------------
// Palette diagnostics — the checks that would have prevented the bad palettes
// ---------------------------------------------------------------------------

export function hueDistance(a, b) {
  const d = Math.abs(a - b) % 360;
  return Math.min(d, 360 - d);
}

/**
 * Problems that only show up on a bulb, never in a colour picker.
 * Returns [{ level, index, otherIndex, message }].
 */
export function paletteWarnings(colors = []) {
  const warnings = [];
  const hexes = colors.map((c, i) => ({ c, i })).filter(({ c }) => !isCt(c));

  hexes.forEach(({ c, i }) => {
    if (!isHex(c)) return;
    if (c.toLowerCase() === '#000000') {
      warnings.push({
        level: 'error', index: i,
        message: 'Black renders as white — a bulb has no black. Use "Off" instead.',
      });
      return;
    }
    const [, sat, light] = hexToHsl(c);
    if (sat < 25 && light > 15 && light < 90) {
      warnings.push({
        level: 'warn', index: i,
        message: 'Greys look identical to white on a bulb. Use a warm or cool white.',
      });
    }
    if (isOutOfGamut(c)) {
      warnings.push({
        level: 'warn', index: i,
        message: `Outside the bulb's range — it will render as ${bulbPreview(c)}.`,
      });
    }
  });

  // Near-identical hues waste a slot. Lightness differences don't survive.
  const vivid = hexes
    .filter(({ c }) => isHex(c))
    .map(({ c, i }) => ({ i, c, hsl: hexToHsl(c) }))
    .filter(({ hsl }) => hsl[1] > 50 && hsl[2] < 85);

  for (let a = 0; a < vivid.length; a++) {
    for (let b = a + 1; b < vivid.length; b++) {
      // An exactly repeated colour is deliberate — palettes are round-robined
      // across lights, so red/green/red is a real pattern, not a mistake. Only
      // near-misses (different colour, same apparent hue) are worth flagging.
      if (vivid[a].c.toLowerCase() === vivid[b].c.toLowerCase()) continue;
      const dist = hueDistance(vivid[a].hsl[0], vivid[b].hsl[0]);
      if (dist < MIN_HUE_SEPARATION) {
        warnings.push({
          level: 'warn',
          index: vivid[b].i,
          otherIndex: vivid[a].i,
          message: dist < 1
            ? `Effectively the same hue as ${vivid[a].c} — these read as one colour.`
            : `Only ${Math.round(dist)}° from ${vivid[a].c} — these read as one colour.`,
        });
      }
    }
  }

  return warnings;
}
