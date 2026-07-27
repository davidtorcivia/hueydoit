/**
 * Palette suggestions for the holiday editor.
 *
 * Two rules, in order:
 *
 * 1. Accuracy to the holiday beats variety between holidays. Cinco de Mayo and
 *    Columbus Day both being red/white/green is correct — those are the flags.
 *    Don't invent an association to make something look different.
 *
 * 2. Only chromaticity reaches the bulb (see lib/color.js). A hex's lightness is
 *    discarded, so palettes must vary by HUE:
 *      - no black, it renders as white
 *      - no greys, they are indistinguishable from white
 *      - two different colours under ~12 deg apart read as one
 *      - warm/neutral/cool whites (#ffeedd / #ffffff / #cce6ff) DO differ, and
 *        are the right way to express a white or silver palette
 *      - an exactly repeated colour is fine; palettes round-robin across lights,
 *        so red/green/red is a deliberate three-light pattern
 *
 * The first option for each holiday is the canonical reading and matches the
 * built-in default in app/holidays/. Later options are honest variations.
 *
 * Validate with: node frontend/scripts/check-palettes.mjs
 */

const HOLIDAY_PALETTES = {
  // ---- US federal -------------------------------------------------------
  new_years:        [['#ffd700', '#ffeedd', '#00d0ff'], ['#ffd700', '#ff00cc', '#00ffff'], ['#cce6ff', '#ffffff', '#ffd700']],
  mlk_day:          [['#ff0022', '#ffd700', '#00cc44'], ['#ff0000', '#ffeedd', '#00cc00'], ['#e63946', '#ffd700', '#22aa55']],
  presidents_day:   [['#ff0000', '#ffffff', '#0000ff'], ['#ff0022', '#ffeedd', '#2244ff'], ['#ff0022', '#ffffff', '#ffd700']],
  memorial_day:     [['#ff0000', '#ffffff', '#0000ff'], ['#ff0022', '#ffffff', '#cce6ff'], ['#ff0022', '#ffeedd', '#2244ff']],
  juneteenth:       [['#ff0000', '#ffd700', '#00cc00'], ['#ff0022', '#ffffff', '#0044ff'], ['#ee0000', '#ffcc00', '#22aa55']],
  independence_day: [['#ff0000', '#ffffff', '#0000ff'], ['#ff0022', '#ffeedd', '#2244ff'], ['#ff0000', '#ffffff', '#0044ff']],
  labor_day:        [['#ff0000', '#ffffff', '#0000ff'], ['#ff0022', '#ffffff', '#ff8800'], ['#ff0022', '#ffeedd', '#2244ff']],
  columbus_day:     [['#ff0000', '#ffffff', '#00cc00'], ['#ee0000', '#ffeedd', '#22bb44'], ['#ff0022', '#ffffff', '#00aa33']],
  veterans_day:     [['#ff0000', '#ffffff', '#0000ff'], ['#ff0022', '#ffffff', '#7700ff'], ['#ff0022', '#ffeedd', '#ffd700']],
  thanksgiving:     [['#ff8c00', '#ffcc00', '#b3001b'], ['#ffb300', '#ffee00', '#e63200'], ['#ff6600', '#ffd700', '#9e0022']],
  christmas:        [['#ff0000', '#00ff00', '#ffffff'], ['#ff0000', '#00cc00', '#ffd700'], ['#ff0000', '#00ff00', '#ff0000']],

  // ---- Cultural ---------------------------------------------------------
  valentines_day:   [['#ff0033', '#ff69b4', '#ffeedd'], ['#ff0033', '#ff00aa', '#cc00ff'], ['#ff1493', '#ffeedd', '#ff1493']],
  st_patricks_day:  [['#00ff33', '#88ff00', '#ffd700'], ['#00cc44', '#ffeedd', '#ffcc00'], ['#22dd22', '#00ee66', '#ccff00']],
  easter:           [['#ff69b4', '#ffff00', '#87ceeb', '#90ee90'], ['#ff77bb', '#ffdd44', '#55bbff', '#77ee77'], ['#ff8ec4', '#ffee55', '#66ccff']],
  three_kings_day:  [['#ffd700', '#8800ff', '#00cc66'], ['#ffd700', '#ff0033', '#0055ff'], ['#ffeedd', '#ffd700', '#7700ff']],
  rosh_hashanah:    [['#ffb300', '#e0004d', '#ffeedd'], ['#ffcc00', '#ff0033', '#ffffff'], ['#ffd700', '#ff3366', '#cce6ff']],
  yom_kippur:       [['#cce6ff', '#ffffff', '#ffeedd'], ['#ffffff', '#cce6ff', '#ffffff'], ['#ffeedd', '#ffffff', '#0055ff']],
  passover:         [['#ffcc00', '#00cc44', '#cc0033'], ['#ffd700', '#22bb55', '#e0004d'], ['#ffee00', '#00aa44', '#ff0033']],
  ramadan:          [['#00cc66', '#ffd700', '#7700ff'], ['#00cc44', '#ffcc00', '#0055ff'], ['#22dd88', '#ffd700', '#cce6ff']],
  mothers_day:      [['#ff69b4', '#cc66ff', '#ffeedd'], ['#ff3388', '#aa44ff', '#ffd700'], ['#ff88cc', '#cc00ff', '#ffeedd']],
  fathers_day:      [['#0088ff', '#00d0ff', '#ffd700'], ['#0055ff', '#44ccff', '#ffcc00'], ['#0044ff', '#ffeedd', '#00cc66']],
  eid_al_fitr:      [['#00ff44', '#ffd700', '#ffffff'], ['#00cc66', '#ffcc00', '#ffeedd'], ['#22dd44', '#ffd700', '#cce6ff']],
  eid_al_adha:      [['#00ff44', '#ffd700', '#ffffff'], ['#00cc66', '#ffffff', '#0055ff'], ['#22dd44', '#ffcc00', '#ffeedd']],
  halloween:        [['#ff6600', '#aa00ff', '#00ff00'], ['#ff5500', '#9900ff', '#44ff00'], ['#ff8800', '#cc00ff', '#00ff66']],
  diwali:           [['#ffd700', '#ff6600', '#ff0066'], ['#ffcc00', '#ff5500', '#ff00aa'], ['#ffd700', '#ff4500', '#ff1493']],
  hanukkah:         [['#0055ff', '#ffeedd', '#00d0ff'], ['#0044cc', '#ffffff', '#44ccff'], ['#0055ff', '#ffd700', '#cce6ff']],
  lunar_new_year:   [['#ff0000', '#ffd700', '#ff6600'], ['#ee0000', '#ffcc00', '#ff5500'], ['#ff0022', '#ffd700', '#ff3388']],
  election_day:     [['#e0004d', '#ffeedd', '#2266ff'], ['#ff0022', '#ffffff', '#0044ff'], ['#ff3366', '#cce6ff', '#4488ff']],

  // ---- International ----------------------------------------------------
  mardi_gras:       [['#ffd700', '#9900ff', '#00cc00'], ['#ffcc00', '#aa00ff', '#00ee44'], ['#ffd700', '#cc00ff', '#00ff66']],
  intl_womens_day:  [['#cc00ff', '#ff69b4', '#ffeedd'], ['#ff00cc', '#ff88cc', '#ffffff'], ['#aa44ff', '#ff3388', '#ffeedd']],
  holi:             [['#ff0066', '#ffcc00', '#00ccff', '#88ff00', '#ff6600', '#cc00ff'], ['#ff0088', '#ffee00', '#00ddff', '#44ff00'], ['#ff2200', '#ffaa00', '#00ffaa', '#cc00ff']],
  nowruz:           [['#00e5a0', '#ffd700', '#ff3399'], ['#00cc88', '#ffcc00', '#ff69b4'], ['#00d0ff', '#88ff00', '#ffd700']],
  earth_day:        [['#00cc00', '#0088ff', '#00ff88'], ['#22dd22', '#4488ff', '#44ffaa'], ['#00aa44', '#00d0ff', '#88ff00']],
  cinco_de_mayo:    [['#00cc00', '#ffffff', '#ff0000'], ['#22ee44', '#ffeedd', '#ff2200'], ['#00aa33', '#ffffff', '#ff0022']],
  puerto_rican_day: [['#ff0033', '#ffffff', '#00a0ff'], ['#ff0022', '#ffeedd', '#0088ff'], ['#ee0000', '#ffffff', '#44bbff']],
  bastille_day:     [['#0055ff', '#ffffff', '#ff0000'], ['#3377ff', '#ffeedd', '#ff3333'], ['#0044cc', '#ffffff', '#ff0022']],
  oktoberfest:      [['#0088ff', '#ffffff', '#ffd700'], ['#4499ff', '#ffeedd', '#ffcc00'], ['#0055ff', '#ffffff', '#ffaa00']],
  west_indian_carnival: [['#00cc44', '#ffcc00', '#ff0033', '#00d0ff', '#cc00ff'], ['#00ff66', '#ffee00', '#ff0066', '#00ccff'], ['#ff3300', '#ffcc00', '#00cc44', '#0088ff', '#ff00cc']],
  day_of_the_dead:  [['#ff6600', '#ff00ff', '#ffcc00', '#00ffcc'], ['#ff5500', '#cc00ff', '#ffd700'], ['#ff8800', '#ff0099', '#ffee00', '#00e5a0']],
  guy_fawkes:       [['#ff4400', '#ff8800', '#ffd700'], ['#ff6600', '#ffaa00', '#ffee44'], ['#ff2200', '#ff9900', '#ffcc00']],
  world_aids_day:   [['#ff0022', '#ffffff', '#8800ff'], ['#ff0033', '#ffeedd', '#cc00ff'], ['#ee0000', '#ffffff', '#7700ff']],
  kwanzaa:          [['#ff0000', '#00cc00', '#ffd700'], ['#ee0000', '#22dd22', '#ffcc00'], ['#ff0022', '#00aa44', '#ffeedd']],

  // ---- Seasonal ---------------------------------------------------------
  spring_equinox:   [['#00ff88', '#ffcc00', '#ff69b4'], ['#44ffaa', '#ffdd44', '#ff88cc'], ['#88ff00', '#ffee00', '#ff3399']],
  summer_solstice:  [['#ffe600', '#ff7a00', '#ff0099'], ['#ffcc00', '#ff6600', '#ff0000'], ['#ffee00', '#ff5500', '#cc00ff']],
  fall_equinox:     [['#ffb300', '#e63200', '#9e0022'], ['#ffcc00', '#ff5500', '#cc0022'], ['#ff8c00', '#ff3300', '#b3001b']],
  winter_solstice:  [['#0066ff', '#ffeedd', '#00d0ff'], ['#0044ff', '#ffffff', '#00ccff'], ['#0055ff', '#cce6ff', '#88ddff']],

  // ---- Fun --------------------------------------------------------------
  groundhog_day:    [['#ffaa00', '#00cc44', '#ffeedd'], ['#ffcc00', '#22dd22', '#cce6ff'], ['#ff8800', '#88ff00', '#ffffff']],
  super_bowl:       [['#ffd700', '#0088ff', '#ff0000'], ['#ffcc00', '#4499ff', '#ff3333'], ['#ffee00', '#0055ff', '#00cc44']],
  pizza_day:        [['#ff2200', '#ffcc00', '#00cc44'], ['#ff0000', '#ffd700', '#22bb44'], ['#ff4400', '#ffee00', '#00aa33']],
  friday_13:        [['#ff0011', '#7700ff', '#00ff44'], ['#cc0022', '#aa00ff', '#00ffaa'], ['#ff0033', '#5500ff', '#88ff00']],
  pi_day:           [['#4488ff', '#ffcc00', '#ff4488'], ['#5599ff', '#ffdd44', '#ff5599'], ['#0088ff', '#ffee00', '#ff0088']],
  april_fools:      [['#ff00ff', '#00ffff', '#ffee00'], ['#ff44ff', '#44ffff', '#ffff44'], ['#cc00ff', '#00ff88', '#ffcc00']],
  '420':            [['#00cc00', '#88ff00', '#44ff00'], ['#22dd22', '#66ff00', '#00ff44'], ['#00ff33', '#ccff00', '#00cc66']],
  star_wars_day:    [['#0044ff', '#ff0000', '#00ff00'], ['#0066ff', '#ff2200', '#22ff22'], ['#00d0ff', '#ff0033', '#ffd700']],
  donut_day:        [['#ff69b4', '#ffcc00', '#00d0ff'], ['#ff88cc', '#ffee00', '#aa44ff'], ['#ff0099', '#ffaa00', '#00ffcc']],
  pride_month:      [['#ff0000', '#ff8800', '#ffff00', '#00cc00', '#0000ff', '#cc00ff'], ['#ff0022', '#ff6600', '#ffee00', '#00cc44', '#0044ff', '#8800ff'], ['#ff0066', '#ffaa00', '#88ff00', '#00d0ff', '#7700ff']],
  emoji_day:        [['#ffcc00', '#ff4444', '#4488ff'], ['#ffee00', '#ff0066', '#00d0ff'], ['#ffd700', '#ff8800', '#00cc44']],
  ice_cream_day:    [['#ff69b4', '#ffeedd', '#00e5a0'], ['#ff88cc', '#ffee00', '#00d0ff'], ['#ff0099', '#ffffff', '#88ff00']],
  cat_day:          [['#ff8800', '#ffeedd', '#00d0ff'], ['#ffaa00', '#ffffff', '#00ff88'], ['#ff6600', '#cce6ff', '#ffcc00']],
  pirate_day:       [['#ffd700', '#ff2200', '#0088ff'], ['#ffcc00', '#ff0044', '#00d0ff'], ['#ffee00', '#ff5500', '#0055ff']],
  coffee_day:       [['#ff6a00', '#ffcc00', '#ffeedd'], ['#ff8800', '#ffd700', '#cce6ff'], ['#ff5500', '#ffee00', '#ffffff']],
  taco_day:         [['#ffcc00', '#ff6600', '#00cc00'], ['#ffd700', '#ff4400', '#22bb44'], ['#ffee00', '#ff8800', '#00aa33']],
  nyc_marathon:     [['#0088ff', '#ff5500', '#ffee00'], ['#0055ff', '#ff6600', '#ffd700'], ['#00d0ff', '#ff3300', '#ccff00']],
  festivus:         [['#cce6ff', '#ffffff', '#ff0033'], ['#cce6ff', '#ffffff', '#ffeedd'], ['#ffffff', '#cce6ff', '#ffd700']],
  new_years_eve:    [['#ffd700', '#ff00ff', '#00ffff', '#ffeedd'], ['#ffcc00', '#ff44ff', '#44ffff'], ['#ffee00', '#cc00ff', '#00d0ff']],
};

/**
 * Last-resort pool for custom holidays with no known palette. Kept hue-spread so
 * a generated palette can't come out as three shades of the same colour, which
 * is how several built-ins originally acquired unusable palettes.
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
  // Walk the wheel in roughly even steps from a random start, so the result is
  // always a spread rather than three neighbours.
  const step = Math.floor(WLED_SAFE_POOL.length / count);
  const start = Math.floor(Math.random() * WLED_SAFE_POOL.length);
  const result = [];
  for (let i = 0; i < count; i++) {
    result.push(WLED_SAFE_POOL[(start + i * step) % WLED_SAFE_POOL.length]);
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
  if (lower.includes('rosh') || lower.includes('hashanah'))
    return HOLIDAY_PALETTES.rosh_hashanah;
  if (lower.includes('yom kippur'))
    return HOLIDAY_PALETTES.yom_kippur;
  if (lower.includes('passover') || lower.includes('pesach'))
    return HOLIDAY_PALETTES.passover;
  if (lower.includes('ramadan'))
    return HOLIDAY_PALETTES.ramadan;
  if (lower.includes('nowruz') || lower.includes('persian new year'))
    return HOLIDAY_PALETTES.nowruz;
  if (lower.includes('three kings') || lower.includes('reyes') || lower.includes('epiphany'))
    return HOLIDAY_PALETTES.three_kings_day;
  if (lower.includes('carnival') || lower.includes('carnaval'))
    return HOLIDAY_PALETTES.west_indian_carnival;
  if (lower.includes('marathon') || lower.includes('race'))
    return HOLIDAY_PALETTES.nyc_marathon;
  if (lower.includes('election') || lower.includes('vote'))
    return HOLIDAY_PALETTES.election_day;
  if (lower.includes('aids') || lower.includes('ribbon'))
    return HOLIDAY_PALETTES.world_aids_day;
  if (lower.includes('puerto ric') || lower.includes('boricua'))
    return HOLIDAY_PALETTES.puerto_rican_day;
  if (lower.includes('friday_13') || lower.includes('friday the 13'))
    return HOLIDAY_PALETTES.friday_13;
  if (lower.includes('mother'))
    return HOLIDAY_PALETTES.mothers_day;
  if (lower.includes('father'))
    return HOLIDAY_PALETTES.fathers_day;

  // Fall back to random vibrant palettes
  return [randomPalette(3), randomPalette(4), randomPalette(3)];
}
