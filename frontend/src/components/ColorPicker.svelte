<script>
  import {
    bulbPreview, ctKelvin, ctMirek, ctToHex, hexToHsl, hslToHex,
    isCt, isHex, paletteWarnings,
  } from '../lib/color.js';

  let { colors = [], onChange } = $props();
  let localColors = $state([...colors]);
  let editingIdx = $state(-1);

  // Hues roughly 30 deg apart so adjacent presets stay distinguishable on a strip.
  const presets = [
    { hex: '#ff0000', label: 'Red' },
    { hex: '#ff4400', label: 'Orange' },
    { hex: '#ff8800', label: 'Amber' },
    { hex: '#ffcc00', label: 'Yellow' },
    { hex: '#ccff00', label: 'Chartreuse' },
    { hex: '#44ff00', label: 'Lime' },
    { hex: '#00ff44', label: 'Green' },
    { hex: '#00ffaa', label: 'Mint' },
    { hex: '#00ddff', label: 'Cyan' },
    { hex: '#0088ff', label: 'Sky' },
    { hex: '#0033ff', label: 'Blue' },
    { hex: '#7700ff', label: 'Violet' },
    { hex: '#cc00ff', label: 'Purple' },
    { hex: '#ff00cc', label: 'Magenta' },
    { hex: '#ff0066', label: 'Pink' },
    { hex: '#ffeedd', label: 'Warm white' },
  ];

  const ctPresets = [
    { value: 'ct:500', label: 'Candle' },
    { value: 'ct:400', label: 'Warm' },
    { value: 'ct:333', label: 'Soft' },
    { value: 'ct:250', label: 'Neutral' },
    { value: 'ct:200', label: 'Cool' },
    { value: 'ct:154', label: 'Daylight' },
  ];

  let editHue = $state(0);
  let editSat = $state(100);
  let editMode = $state('color');
  let editMirek = $state(370);

  let warnings = $derived(paletteWarnings(localColors));
  let warningsFor = $derived((i) => warnings.filter((w) => w.index === i));

  function commit() {
    localColors = [...localColors];
    onChange(localColors);
  }

  function openEditor(idx) {
    editingIdx = idx;
    const c = localColors[idx];
    if (isCt(c)) {
      editMode = 'ct';
      editMirek = ctMirek(c);
    } else {
      editMode = 'color';
      const [h, s] = hexToHsl(isHex(c) ? c : '#ff0000');
      editHue = h;
      editSat = s;
    }
  }

  function updateFromHsl() {
    if (editingIdx < 0) return;
    localColors[editingIdx] = hslToHex(editHue, editSat, 50);
    commit();
  }

  function updateFromCt() {
    if (editingIdx < 0) return;
    localColors[editingIdx] = `ct:${editMirek}`;
    commit();
  }

  function pick(value) {
    if (editingIdx < 0) {
      localColors = [...localColors, value];
      editingIdx = localColors.length - 1;
    } else {
      localColors[editingIdx] = value;
    }
    if (isCt(value)) {
      editMode = 'ct';
      editMirek = ctMirek(value);
    } else {
      editMode = 'color';
      const [h, s] = hexToHsl(value);
      editHue = h;
      editSat = s;
    }
    commit();
  }

  function addColor() {
    localColors = [...localColors, '#ff0000'];
    onChange(localColors);
    openEditor(localColors.length - 1);
  }

  function removeColor(idx) {
    if (editingIdx === idx) editingIdx = -1;
    else if (editingIdx > idx) editingIdx--;
    localColors = localColors.filter((_, i) => i !== idx);
    onChange(localColors);
  }

  function swatch(c) {
    return isCt(c) ? ctToHex(c) : bulbPreview(c);
  }

  function label(c) {
    return isCt(c) ? `${ctKelvin(c)}K` : c;
  }

  /** True when the bulb can't match the pick, so we show both. */
  function shifted(c) {
    return !isCt(c) && isHex(c) && bulbPreview(c).toLowerCase() !== c.toLowerCase();
  }
</script>

<div class="color-picker">
  <div class="color-list">
    {#each localColors as color, i}
      {@const issues = warningsFor(i)}
      <div class="chip-wrap">
        <button
          class="chip"
          class:active={editingIdx === i}
          class:has-error={issues.some((w) => w.level === 'error')}
          class:has-warn={issues.some((w) => w.level === 'warn')}
          style="background: {swatch(color)}"
          onclick={() => (editingIdx === i ? (editingIdx = -1) : openEditor(i))}
          title={issues.map((w) => w.message).join('\n') || label(color)}
          aria-label="Edit colour {i + 1}: {label(color)}"
        >
          {#if shifted(color)}
            <span class="shift-dot" style="background: {color}" title="Picked {color}, bulb shows {bulbPreview(color)}"></span>
          {/if}
          {#if issues.length}
            <span class="issue-badge" class:error={issues.some((w) => w.level === 'error')}>!</span>
          {/if}
        </button>
        <span class="chip-label">{label(color)}</span>
        <button class="chip-remove" onclick={() => removeColor(i)} aria-label="Remove colour {i + 1}">×</button>
      </div>
    {/each}
  </div>

  <button class="small secondary" onclick={addColor}>+ Add Colour</button>

  {#if warnings.length}
    <ul class="warnings">
      {#each warnings as w}
        <li class:error={w.level === 'error'}>
          <strong>{localColors[w.index]}</strong> — {w.message}
        </li>
      {/each}
    </ul>
  {/if}

  {#if editingIdx >= 0 && localColors[editingIdx] !== undefined}
    <div class="editor">
      <div class="tabs">
        <button class="tab" class:active={editMode === 'color'} onclick={() => (editMode = 'color')}>Colour</button>
        <button class="tab" class:active={editMode === 'ct'} onclick={() => (editMode = 'ct')}>White</button>
      </div>

      {#if editMode === 'color'}
        <div class="presets">
          {#each presets as p}
            <button class="preset" style="background: {bulbPreview(p.hex)}" title={p.label}
              onclick={() => pick(p.hex)} aria-label={p.label}></button>
          {/each}
        </div>

        <div class="slider-group">
          <label for="hue-slider">Hue <span class="val">{editHue}°</span></label>
          <input id="hue-slider" type="range" min="0" max="360" bind:value={editHue} oninput={updateFromHsl} class="hue-slider" />
        </div>

        <div class="slider-group">
          <label for="sat-slider">Saturation <span class="val">{editSat}%</span></label>
          <input id="sat-slider" type="range" min="30" max="100" bind:value={editSat} oninput={updateFromHsl} class="sat-slider" />
        </div>

        <div class="preview-row">
          <div class="preview">
            <div class="preview-swatch" style="background: {localColors[editingIdx]}"></div>
            <span>picked</span>
          </div>
          <div class="preview">
            <div class="preview-swatch" style="background: {swatch(localColors[editingIdx])}"></div>
            <span>on the bulb</span>
          </div>
          <input
            type="text"
            class="hex-input"
            value={localColors[editingIdx]}
            oninput={(e) => {
              const v = e.target.value.trim();
              if (isHex(v)) {
                localColors[editingIdx] = v.toLowerCase();
                const [h, s] = hexToHsl(v);
                editHue = h; editSat = s;
                commit();
              }
            }}
          />
        </div>
      {:else}
        <div class="presets ct">
          {#each ctPresets as p}
            <button class="ct-preset" style="background: {ctToHex(p.value)}" onclick={() => pick(p.value)}>
              <span class="ct-label">{p.label}</span>
              <span class="ct-temp">{ctKelvin(p.value)}K</span>
            </button>
          {/each}
        </div>

        <div class="slider-group">
          <label for="ct-slider">Temperature <span class="val">{Math.round(1000000 / editMirek)}K</span></label>
          <input id="ct-slider" type="range" min="153" max="500" bind:value={editMirek} oninput={updateFromCt} class="ct-slider" />
        </div>

        <div class="preview-row">
          <div class="preview">
            <div class="preview-swatch" style="background: {ctToHex(`ct:${editMirek}`)}"></div>
            <span>{Math.round(1000000 / editMirek)}K</span>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .color-picker { display: flex; flex-direction: column; gap: 10px; }
  .color-list { display: flex; flex-wrap: wrap; gap: 10px; }

  .chip-wrap { display: flex; flex-direction: column; align-items: center; gap: 4px; position: relative; }
  .chip {
    position: relative;
    width: 44px; height: 44px; border-radius: 10px;
    border: 2px solid var(--border-light); cursor: pointer; padding: 0;
    transition: border-color .15s, transform .15s, box-shadow .15s;
  }
  .chip:hover { transform: translateY(-2px); border-color: var(--accent); }
  .chip.active { border-color: var(--text-primary); box-shadow: 0 0 0 2px var(--accent); }
  .chip.has-warn { border-color: var(--warning); }
  .chip.has-error { border-color: var(--error); }

  .shift-dot {
    position: absolute; bottom: 3px; right: 3px;
    width: 12px; height: 12px; border-radius: 3px;
    border: 1px solid rgba(0,0,0,.45);
  }
  .issue-badge {
    position: absolute; top: -6px; left: -6px;
    width: 16px; height: 16px; border-radius: 50%;
    background: var(--warning); color: #1a1a2e;
    font-size: 11px; font-weight: 800; line-height: 16px;
  }
  .issue-badge.error { background: var(--error); color: #fff; }

  .chip-label { font-size: 10px; color: var(--text-muted); font-family: ui-monospace, monospace; }
  .chip-remove {
    position: absolute; top: -6px; right: -6px;
    width: 18px; height: 18px; border-radius: 50%;
    background: var(--error); color: #fff; border: none;
    font-size: 12px; line-height: 1; cursor: pointer; padding: 0;
    display: flex; align-items: center; justify-content: center;
    opacity: 0; transition: opacity .15s;
  }
  .chip-wrap:hover .chip-remove, .chip-remove:focus-visible { opacity: 1; }

  .warnings {
    list-style: none; margin: 0; padding: 10px 12px;
    background: rgba(245, 158, 11, .08);
    border: 1px solid rgba(245, 158, 11, .3);
    border-radius: var(--radius);
    font-size: 12px; color: var(--text-secondary);
    display: flex; flex-direction: column; gap: 5px;
  }
  .warnings li.error { color: var(--error); }
  .warnings strong { font-family: ui-monospace, monospace; color: var(--text-primary); }

  .editor {
    padding: 14px; background: rgba(255,255,255,.03);
    border: 1px solid var(--border); border-radius: var(--radius);
  }
  .tabs { display: flex; gap: 2px; margin-bottom: 12px; }
  .tab {
    flex: 1; padding: 7px; font-size: 12px; font-weight: 600;
    background: var(--bg-input); color: var(--text-muted);
    border: 1px solid var(--border); cursor: pointer;
  }
  .tab:first-child { border-radius: 6px 0 0 6px; }
  .tab:last-child { border-radius: 0 6px 6px 0; }
  .tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }

  .presets { display: grid; grid-template-columns: repeat(8, 1fr); gap: 5px; margin-bottom: 14px; }
  .presets.ct { grid-template-columns: repeat(3, 1fr); gap: 6px; }
  .preset {
    aspect-ratio: 1; border-radius: 5px; border: 1px solid rgba(255,255,255,.12);
    cursor: pointer; transition: transform .1s; padding: 0;
  }
  .preset:hover { transform: scale(1.15); border-color: #fff; }

  .ct-preset {
    padding: 8px 6px; border-radius: 6px; border: 1px solid rgba(255,255,255,.12);
    cursor: pointer; text-align: center;
  }
  .ct-preset:hover { border-color: #fff; }
  .ct-label { display: block; font-size: 12px; font-weight: 600; color: #1a1a2e; }
  .ct-temp { display: block; font-size: 10px; color: rgba(0,0,0,.6); }

  .slider-group { margin-bottom: 10px; }
  .slider-group label {
    display: flex; justify-content: space-between;
    font-size: 12px; color: var(--text-secondary); margin-bottom: 5px;
  }
  .val { color: var(--accent); font-weight: 600; }

  input[type="range"] {
    width: 100%; height: 8px; border-radius: 4px;
    -webkit-appearance: none; appearance: none;
    outline: none; border: none; padding: 0;
  }
  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none; width: 16px; height: 16px; border-radius: 50%;
    background: #fff; border: 2px solid rgba(0,0,0,.3); cursor: pointer;
    box-shadow: 0 1px 4px rgba(0,0,0,.35);
  }
  .hue-slider {
    background: linear-gradient(to right, #ff0000, #ffff00, #00ff00, #00ffff, #0000ff, #ff00ff, #ff0000);
  }
  .sat-slider { background: linear-gradient(to right, #9aa0aa, var(--accent)); }
  .ct-slider { background: linear-gradient(to right, #cfe3ff, #fff4e8, #ffb257); }

  .preview-row { display: flex; align-items: flex-end; gap: 14px; margin-top: 10px; }
  .preview { display: flex; flex-direction: column; align-items: center; gap: 4px; }
  .preview span { font-size: 10px; color: var(--text-muted); }
  .preview-swatch {
    width: 40px; height: 40px; border-radius: 8px;
    border: 2px solid var(--border-light);
  }
  .hex-input {
    font-family: ui-monospace, monospace; font-size: 13px; width: 110px;
    background: var(--bg-input); color: var(--text-primary);
    border: 1px solid var(--border); border-radius: var(--radius); padding: 7px 9px;
  }
</style>
