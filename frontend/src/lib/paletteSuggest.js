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
  new_years:        [['#ffd700', '#ffeedd', '#00d0ff'], ['#ffd700', '#ff00ff', '#00ffff'], ['#ffeedd', '#ffd700', '#ff6600']],
  mlk_day:          [['#ff0000', '#ffd700', '#00cc00'], ['#ff4500', '#ffeedd', '#22cc22'], ['#e63946', '#ffd700', '#2ec4b6']],
  presidents_day:   [['#ff0000', '#ffeedd', '#4488ff'], ['#e63946', '#ffeedd', '#1d9bf0'], ['#ff3355', '#ffeedd', '#6699ff']],
  memorial_day:     [['#ff0000', '#ffeedd', '#4488ff'], ['#ff3355', '#ffeedd', '#5588ee'], ['#e63946', '#ffeedd', '#1d9bf0']],
  juneteenth:       [['#ff0000', '#ffd700', '#00cc00'], ['#ff4500', '#ffeedd', '#22cc22'], ['#e63946', '#ffd700', '#2ec4b6']],
  independence_day: [['#ff0000', '#ffeedd', '#4488ff'], ['#ff3355', '#ffeedd', '#6699ff'], ['#e63946', '#ffeedd', '#1d9bf0']],
  labor_day:        [['#ff0000', '#ffeedd', '#4488ff'], ['#ff6600', '#ffeedd', '#5588ee']],
  columbus_day:     [['#ff0000', '#ffeedd', '#4488ff'], ['#ff6600', '#22cc22', '#ffd700']],
  veterans_day:     [['#ff0000', '#ffeedd', '#4488ff'], ['#cc0000', '#ffeedd', '#3366cc']],
  thanksgiving:     [['#ff8c00', '#ffcc00', '#b3001b'], ['#ffb300', '#ffee00', '#e63200'], ['#ff6600', '#ffd700', '#9e0022']],
  christmas:        [['#ff0000', '#00cc00', '#ffeedd'], ['#cc0000', '#22cc22', '#ffd700'], ['#ff2200', '#00ee44', '#ffeedd', '#ffd700']],

  // Cultural
  valentines_day:   [['#ff0033', '#ff69b4', '#ffeedd'], ['#ff0055', '#ff4d9e', '#cc00ff'], ['#ff1493', '#ff6eb4', '#ff00aa']],
  st_patricks_day:  [['#00ff33', '#88ff00', '#ffd700'], ['#22dd22', '#00ee66', '#44ff88'], ['#00ff00', '#ccff00', '#ffeedd']],
  easter:           [['#ff69b4', '#ffff00', '#87ceeb', '#90ee90'], ['#ff8ec4', '#ffee55', '#66ccff', '#88ee88'], ['#ff77bb', '#ffdd44', '#55bbff', '#77ee77']],
  eid_al_fitr:      [['#00ff00', '#ffd700', '#ffeedd'], ['#22dd44', '#ffcc00', '#ffeedd'], ['#00ee66', '#ffd700', '#55ccff']],
  eid_al_adha:      [['#00ff00', '#ffd700', '#ffeedd'], ['#22dd44', '#ffcc00', '#55ccff'], ['#00ee66', '#ffd700', '#ffeedd']],
  mothers_day:      [['#ff69b4', '#cc66ff', '#ffeedd'], ['#ff3388', '#aa44ff', '#ffd700']],
  fathers_day:      [['#0088ff', '#00d0ff', '#ffd700'], ['#0055ff', '#44ccff', '#ffcc00']],
  halloween:        [['#ff6600', '#aa00ff', '#00ff00'], ['#ff5500', '#9900ff', '#44ff00'], ['#ff8800', '#cc00ff', '#00ff66']],
  diwali:           [['#ffd700', '#ff6600', '#ff0066'], ['#ffcc00', '#ff5500', '#ff00aa'], ['#ffd700', '#ff4500', '#ff1493']],
  hanukkah:         [['#0055ff', '#ffeedd', '#00d0ff'], ['#3377ee', '#ffeedd', '#ffd700'], ['#0044cc', '#ffffff', '#44ccff']],
  lunar_new_year:   [['#ff0000', '#ffd700', '#ff6600'], ['#ee0000', '#ffcc00', '#ff5500'], ['#ff2200', '#ffd700', '#ff3388']],

  // International
  mardi_gras:       [['#ffd700', '#9900ff', '#00cc00'], ['#ffcc00', '#aa00ff', '#00ee44'], ['#ffd700', '#cc00ff', '#00ff66']],
  intl_womens_day:  [['#cc00ff', '#ff69b4', '#ffeedd'], ['#ff00cc', '#ff88cc', '#ffeedd']],
  holi:             [['#ff0066', '#ffcc00', '#00ccff', '#88ff00', '#ff6600', '#cc00ff']],
  earth_day:        [['#00cc00', '#0088ff', '#00ff88'], ['#22dd22', '#4488ff', '#44ffaa']],
  cinco_de_mayo:    [['#00cc00', '#ffffff', '#ff0000'], ['#22ee44', '#ffeedd', '#ff2200']],
  bastille_day:     [['#0055ff', '#ffffff', '#ff0000'], ['#3377ff', '#ffeedd', '#ff3333']],
  oktoberfest:      [['#0088ff', '#ffffff', '#ffd700'], ['#4499ff', '#ffeedd', '#ffcc00']],
  day_of_the_dead:  [['#ff6600', '#ff00ff', '#ffcc00', '#00ffcc'], ['#ff5500', '#cc00ff', '#ffd700']],
  guy_fawkes:       [['#ff4400', '#ff8800', '#ffd700'], ['#ff6600', '#ffaa00', '#ffee44']],
  kwanzaa:          [['#ff0000', '#00cc00', '#ffd700'], ['#ee0000', '#22dd22', '#ffeedd']],

  // Fun
  pi_day:           [['#4488ff', '#ffcc00', '#ff4488'], ['#5599ff', '#ffdd44', '#ff5599']],
  april_fools:      [['#ff00ff', '#00ffff', '#ffff00'], ['#ff44ff', '#44ffff', '#ffff44']],
  star_wars_day:    [['#0044ff', '#ff0000', '#00ff00'], ['#0066ff', '#ff2200', '#22ff22']],
  pride_month:      [['#ff0000', '#ff8800', '#ffff00', '#00cc00', '#0000ff', '#cc00ff']],
  pirate_day:       [['#ffd700', '#ff2200', '#0088ff'], ['#ffcc00', '#ff0044', '#00d0ff']],
  festivus:         [['#cce6ff', '#ffffff', '#ffeedd'], ['#aaddff', '#ffffff', '#ffd700']],
  new_years_eve:    [['#ffd700', '#ff00ff', '#00ffff', '#ffeedd'], ['#ffcc00', '#ff44ff', '#44ffff']],
  super_bowl:       [['#ffd700', '#0088ff', '#ff0000'], ['#ffcc00', '#4499ff', '#ff3333']],
  '420':            [['#00cc00', '#88ff00', '#44ff00'], ['#22dd22', '#66ff00', '#00ff44']],

  groundhog_day:    [['#ffaa00', '#00cc44', '#ffeedd'], ['#ffcc00', '#22dd22', '#cce6ff']],
  pizza_day:        [['#ff2200', '#ffcc00', '#00cc44'], ['#ff0000', '#ffd700', '#88ff00']],
  donut_day:        [['#ff69b4', '#ffcc00', '#00d0ff'], ['#ff88cc', '#ffee00', '#aa44ff']],
  emoji_day:        [['#ffcc00', '#ff4444', '#4488ff'], ['#ffee00', '#ff0066', '#00d0ff']],
  ice_cream_day:    [['#ff69b4', '#ffeedd', '#00e5a0'], ['#ff88cc', '#ffee00', '#00d0ff']],
  cat_day:          [['#ff8800', '#ffeedd', '#00d0ff'], ['#ffaa00', '#ffffff', '#00ff88']],
  coffee_day:       [['#ff6a00', '#ffcc00', '#ffeedd'], ['#ff8800', '#ffd700', '#cce6ff']],
  taco_day:         [['#ffcc00', '#ff6600', '#00cc00'], ['#ffee00', '#ff2200', '#22dd22']],
  friday_13:        [['#ff0011', '#7700ff', '#00ff44'], ['#cc0022', '#aa00ff', '#00ffaa']],

  // Seasonal
  spring_equinox:   [['#00ff88', '#ffcc00', '#ff69b4'], ['#44ffaa', '#ffdd44', '#ff88cc']],
  summer_solstice:  [['#ffe600', '#ff7a00', '#ff0099'], ['#ffcc00', '#ff6600', '#ff0000']],
  fall_equinox:     [['#ffb300', '#e63200', '#9e0022'], ['#ffcc00', '#ff5500', '#cc0022']],
  winter_solstice:  [['#0066ff', '#ffeedd', '#00d0ff'], ['#0044ff', '#ffffff', '#00ccff']],
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
  if (lower.includes('mardi gras') || lower.includes('carnival'))
    return HOLIDAY_PALETTES.mardi_gras;
  if (lower.includes('holi'))
    return HOLIDAY_PALETTES.holi;
  if (lower.includes('earth'))
    return HOLIDAY_PALETTES.earth_day;
  if (lower.includes('cinco') || lower.includes('mexico'))
    return HOLIDAY_PALETTES.cinco_de_mayo;
  if (lower.includes('oktoberfest') || lower.includes('beer'))
    return HOLIDAY_PALETTES.oktoberfest;
  if (lower.includes('dead') || lower.includes('muerto'))
    return HOLIDAY_PALETTES.day_of_the_dead;
  if (lower.includes('star wars') || lower.includes('may the'))
    return HOLIDAY_PALETTES.star_wars_day;
  if (lower.includes('pride') || lower.includes('rainbow') || lower.includes('lgbtq'))
    return HOLIDAY_PALETTES.pride_month;
  if (lower.includes('pirate'))
    return HOLIDAY_PALETTES.pirate_day;
  if (lower.includes('solstice') && lower.includes('summer'))
    return HOLIDAY_PALETTES.summer_solstice;
  if (lower.includes('solstice') && lower.includes('winter'))
    return HOLIDAY_PALETTES.winter_solstice;
  if (lower.includes('equinox') && lower.includes('spring'))
    return HOLIDAY_PALETTES.spring_equinox;
  if (lower.includes('equinox') && lower.includes('fall'))
    return HOLIDAY_PALETTES.fall_equinox;
  if (lower.includes('kwanzaa'))
    return HOLIDAY_PALETTES.kwanzaa;
  if (lower.includes('friday_13') || lower.includes('friday the 13'))
    return HOLIDAY_PALETTES.friday_13;
  if (lower.includes('mother'))
    return HOLIDAY_PALETTES.mothers_day;
  if (lower.includes('father'))
    return HOLIDAY_PALETTES.fathers_day;

  // Fall back to random vibrant palettes
  return [randomPalette(3), randomPalette(4), randomPalette(3)];
}
