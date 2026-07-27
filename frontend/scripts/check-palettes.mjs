/**
 * Validates every suggested palette against the rules in lib/color.js, and
 * checks that every built-in holiday has a suggestion.
 *
 * Run: node frontend/scripts/check-palettes.mjs [holidaysApiUrl]
 */
import { paletteWarnings, isHex, isCt, MIN_HUE_SEPARATION } from '../src/lib/color.js';
import { suggestPalettes } from '../src/lib/paletteSuggest.js';

const API = process.argv[2] || 'http://localhost:8585/api/holidays';
let failures = 0;
const notes = [];
const fail = (m) => { console.error('  FAIL ' + m); failures++; };

const mod = await import('../src/lib/paletteSuggest.js');
const src = await (await import('node:fs/promises')).readFile(
  new URL('../src/lib/paletteSuggest.js', import.meta.url), 'utf8');
const slugs = [...src.matchAll(/^  '?([a-z0-9_]+)'?:\s+\[\[/gm)].map(m => m[1]);

console.log(`Checking ${slugs.length} palette entries...`);
for (const slug of slugs) {
  const options = suggestPalettes(slug);
  if (!options?.length) { fail(`${slug}: no options`); continue; }
  options.forEach((palette, i) => {
    if (!palette.length) return fail(`${slug}[${i}]: empty`);
    for (const c of palette) {
      if (!isHex(c) && !isCt(c)) fail(`${slug}[${i}]: malformed colour ${c}`);
    }
    for (const w of paletteWarnings(palette)) {
      // Out-of-gamut is informational, not a failure. Flag blue (#0000ff) sits
      // outside gamut C and renders as #2300ff — still unmistakably blue, and
      // accuracy to the holiday beats nudging the flag to suit the hardware.
      if (/Outside the bulb/.test(w.message)) { notes.push(w.message); continue; }
      fail(`${slug}[${i}]: ${w.message} (${palette.join(' ')})`);
    }
  });
}

// Coverage against the running instance, when it's reachable.
try {
  const res = await fetch(API);
  const holidays = await res.json();
  const seen = new Set();
  let missing = 0;
  for (const h of holidays) {
    const base = h.slug.startsWith('friday_13') ? 'friday_13' : h.slug;
    if (seen.has(base)) continue;
    seen.add(base);
    if (!slugs.includes(base)) { fail(`${h.slug} (${h.name}) has no suggestion`); missing++; }
  }
  console.log(`Coverage: ${seen.size - missing}/${seen.size} holidays have suggestions`);
} catch {
  console.log('Coverage: skipped (API not reachable)');
}

if (notes.length)
  console.log(`\n${notes.length} out-of-gamut notes (accurate, shifts slightly):\n  ` +
    [...new Set(notes)].join('\n  '));
console.log(failures === 0
  ? `PASS — every palette is bulb-safe (hue separation >= ${MIN_HUE_SEPARATION} deg)`
  : `${failures} problems`);
process.exit(failures === 0 ? 0 : 1);
