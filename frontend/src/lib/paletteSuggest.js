/**
 * WLED-friendly palette suggestions.
 *
 * Rules for addressable LEDs:
 *  - No black (#000000) — LEDs just turn off
 *  - No brown / dark earth tones — muddy on LEDs
 *  - No grays — washed out
 *  - No very dark colors — barely visible
 *  - Prefer saturated, vibrant, high-chroma colors
 *  - Warm white (#ffeedd) is OK as a substitute for pure white
 */

const HOLIDAY_PALETTES = {
  // US Federal
  new_years:        [['#ffd700', '#ff00ff', '#00ffff'], ['#ffd700', '#ff1493', '#7b68ee'], ['#ffeedd', '#ffd700', '#ff6600']],
  mlk_day:          [['#ff0000', '#ffd700', '#00cc00'], ['#ff4500', '#ffeedd', '#22cc22'], ['#e63946', '#ffd700', '#2ec4b6']],
  presidents_day:   [['#ff0000', '#ffeedd', '#4488ff'], ['#e63946', '#ffeedd', '#1d9bf0'], ['#ff3355', '#ffeedd', '#6699ff']],
  memorial_day:     [['#ff0000', '#ffeedd', '#4488ff'], ['#ff3355', '#ffeedd', '#5588ee'], ['#e63946', '#ffeedd', '#1d9bf0']],
  juneteenth:       [['#ff0000', '#ffd700', '#00cc00'], ['#ff4500', '#ffeedd', '#22cc22'], ['#e63946', '#ffd700', '#2ec4b6']],
  independence_day: [['#ff0000', '#ffeedd', '#4488ff'], ['#ff3355', '#ffeedd', '#6699ff'], ['#e63946', '#ffeedd', '#1d9bf0']],
  labor_day:        [['#ff0000', '#ffeedd', '#4488ff'], ['#ff6600', '#ffeedd', '#5588ee']],
  columbus_day:     [['#ff0000', '#ffeedd', '#4488ff'], ['#ff6600', '#22cc22', '#ffd700']],
  veterans_day:     [['#ff0000', '#ffeedd', '#4488ff'], ['#cc0000', '#ffeedd', '#3366cc']],
  thanksgiving:     [['#ff6600', '#ffd700', '#ff4500'], ['#ff8c00', '#ffcc00', '#ff5500'], ['#ffa500', '#ffdd44', '#ff6622']],
  christmas:        [['#ff0000', '#00cc00', '#ffeedd'], ['#cc0000', '#22cc22', '#ffd700'], ['#ff2200', '#00ee44', '#ffeedd', '#ffd700']],

  // Cultural
  valentines_day:   [['#ff1493', '#ff69b4', '#ff0055'], ['#ff007f', '#ff69b4', '#ff4488'], ['#ff1493', '#ff6eb4', '#ff00aa']],
  st_patricks_day:  [['#00ff00', '#00cc44', '#ffeedd'], ['#22dd22', '#00ee66', '#44ff88'], ['#00ff00', '#00cc00', '#88ff44']],
  easter:           [['#ff69b4', '#ffff00', '#87ceeb', '#90ee90'], ['#ff8ec4', '#ffee55', '#66ccff', '#88ee88'], ['#ff77bb', '#ffdd44', '#55bbff', '#77ee77']],
  eid_al_fitr:      [['#00ff00', '#ffd700', '#ffeedd'], ['#22dd44', '#ffcc00', '#ffeedd'], ['#00ee66', '#ffd700', '#55ccff']],
  eid_al_adha:      [['#00ff00', '#ffd700', '#ffeedd'], ['#22dd44', '#ffcc00', '#55ccff'], ['#00ee66', '#ffd700', '#ffeedd']],
  halloween:        [['#ff6600', '#aa00ff', '#00ff00'], ['#ff5500', '#9900ff', '#44ff00'], ['#ff8800', '#cc00ff', '#00ff66']],
  diwali:           [['#ffd700', '#ff6600', '#ff0066'], ['#ffcc00', '#ff5500', '#ff00aa'], ['#ffd700', '#ff4500', '#ff1493']],
  hanukkah:         [['#4488ff', '#ffeedd', '#66aaff'], ['#3377ee', '#ffeedd', '#88bbff'], ['#5599ff', '#ffd700', '#ffeedd']],
  lunar_new_year:   [['#ff0000', '#ffd700', '#ff6600'], ['#ee0000', '#ffcc00', '#ff5500'], ['#ff2200', '#ffd700', '#ff3388']],
};

/**
 * Curated pool of vibrant WLED-safe colors for random palette generation.
 */
const WLED_SAFE_POOL = [
  '#ff0000', '#ff3300', '#ff4500', '#ff6600', '#ff8800', '#ffaa00',
  '#ffcc00', '#ffd700', '#ffee00', '#ffff00', '#ccff00', '#88ff00',
  '#44ff00', '#00ff00', '#00ff44', '#00ff88', '#00ffaa', '#00ffcc',
  '#00ffee', '#00ffff', '#00ccff', '#0099ff', '#0066ff', '#4488ff',
  '#5500ff', '#7700ff', '#9900ff', '#aa00ff', '#cc00ff', '#ff00ff',
  '#ff00cc', '#ff00aa', '#ff0088', '#ff0066', '#ff0044',
  '#ff1493', '#ff69b4', '#ffeedd',
];

/**
 * Generate a random WLED-friendly palette of `count` colors.
 */
function randomPalette(count = 3) {
  const pool = [...WLED_SAFE_POOL];
  const result = [];
  for (let i = 0; i < count && pool.length > 0; i++) {
    const idx = Math.floor(Math.random() * pool.length);
    result.push(pool.splice(idx, 1)[0]);
  }
  return result;
}

/**
 * Suggest palettes for a holiday.
 *
 * @param {string} slug - Holiday slug (e.g. "christmas")
 * @param {string} [name] - Holiday name (fallback for keyword matching)
 * @returns {string[][]} Array of 2-3 palette options, each an array of hex colors
 */
export function suggestPalettes(slug, name = '') {
  const known = HOLIDAY_PALETTES[slug];
  if (known) return known;

  // Keyword fallback for custom holidays
  const lower = (slug + ' ' + name).toLowerCase();

  if (lower.includes('christmas') || lower.includes('xmas'))
    return HOLIDAY_PALETTES.christmas;
  if (lower.includes('halloween') || lower.includes('spooky'))
    return HOLIDAY_PALETTES.halloween;
  if (lower.includes('valentine') || lower.includes('love'))
    return HOLIDAY_PALETTES.valentines_day;
  if (lower.includes('easter'))
    return HOLIDAY_PALETTES.easter;
  if (lower.includes('patriot') || lower.includes('flag') || lower.includes('america'))
    return HOLIDAY_PALETTES.independence_day;
  if (lower.includes('st patrick') || lower.includes('irish'))
    return HOLIDAY_PALETTES.st_patricks_day;
  if (lower.includes('new year') || lower.includes('nye'))
    return HOLIDAY_PALETTES.new_years;
  if (lower.includes('hanukkah') || lower.includes('chanukah'))
    return HOLIDAY_PALETTES.hanukkah;
  if (lower.includes('diwali') || lower.includes('deepavali'))
    return HOLIDAY_PALETTES.diwali;
  if (lower.includes('eid'))
    return HOLIDAY_PALETTES.eid_al_fitr;
  if (lower.includes('thanksgiving') || lower.includes('harvest'))
    return HOLIDAY_PALETTES.thanksgiving;
  if (lower.includes('lunar') || lower.includes('chinese'))
    return HOLIDAY_PALETTES.lunar_new_year;

  // Fall back to random vibrant palettes
  return [randomPalette(3), randomPalette(4), randomPalette(3)];
}
