<script>
  let { colors = [], onChange } = $props();
  let localColors = $state([...colors]);
  let editingIdx = $state(-1);

  // LED-optimized preset swatches
  const presets = [
    { hex: '#ff0000', label: 'Red' },
    { hex: '#ff4400', label: 'Orange' },
    { hex: '#ff8800', label: 'Amber' },
    { hex: '#ffcc00', label: 'Yellow' },
    { hex: '#88ff00', label: 'Lime' },
    { hex: '#00ff00', label: 'Green' },
    { hex: '#00ff88', label: 'Mint' },
    { hex: '#00ffcc', label: 'Aqua' },
    { hex: '#00ccff', label: 'Cyan' },
    { hex: '#0088ff', label: 'Sky' },
    { hex: '#0044ff', label: 'Blue' },
    { hex: '#4400ff', label: 'Indigo' },
    { hex: '#8800ff', label: 'Violet' },
    { hex: '#cc00ff', label: 'Purple' },
    { hex: '#ff00cc', label: 'Magenta' },
    { hex: '#ff0066', label: 'Pink' },
  ];

  const ctPresets = [
    { value: 'ct:500', label: 'Candle', temp: '2000K' },
    { value: 'ct:400', label: 'Warm', temp: '2500K' },
    { value: 'ct:333', label: 'Soft', temp: '3000K' },
    { value: 'ct:250', label: 'Neutral', temp: '4000K' },
    { value: 'ct:200', label: 'Cool', temp: '5000K' },
    { value: 'ct:154', label: 'Daylight', temp: '6500K' },
  ];

  // Conversion helpers
  function hslToHex(h, s, l) {
    s /= 100; l /= 100;
    const a = s * Math.min(l, 1 - l);
    const f = (n) => {
      const k = (n + h / 30) % 12;
      const color = l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
      return Math.round(255 * Math.max(0, Math.min(1, color)));
    };
    return `#${f(0).toString(16).padStart(2, '0')}${f(8).toString(16).padStart(2, '0')}${f(4).toString(16).padStart(2, '0')}`;
  }

  function hexToHsl(hex) {
    hex = hex.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16) / 255;
    const g = parseInt(hex.substring(2, 4), 16) / 255;
    const b = parseInt(hex.substring(4, 6), 16) / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h = 0, s = 0, l = (max + min) / 2;
    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) * 60;
      else if (max === g) h = ((b - r) / d + 2) * 60;
      else h = ((r - g) / d + 4) * 60;
    }
    return [Math.round(h), Math.round(s * 100), Math.round(l * 100)];
  }

  function isCt(color) {
    return typeof color === 'string' && color.startsWith('ct:');
  }

  function ctToDisplay(ct) {
    const mirek = parseInt(ct.replace('ct:', ''));
    const kelvin = Math.round(1000000 / mirek);
    // Approximate warm-to-cool color
    const t = (mirek - 153) / (500 - 153);
    const r = Math.round(255 * (0.8 + 0.2 * t));
    const g = Math.round(255 * (0.7 + 0.15 * t - 0.15 * t * t));
    const b = Math.round(255 * (0.5 + 0.5 * (1 - t)));
    return `#${r.toString(16).padStart(2,'0')}${g.toString(16).padStart(2,'0')}${b.toString(16).padStart(2,'0')}`;
  }

  function ctLabel(ct) {
    const mirek = parseInt(ct.replace('ct:', ''));
    return `${Math.round(1000000 / mirek)}K`;
  }

  // Edit state for the active color
  let editHue = $state(0);
  let editSat = $state(100);
  let editMode = $state('color'); // 'color' or 'ct'
  let editMirek = $state(370);

  function openEditor(idx) {
    editingIdx = idx;
    const c = localColors[idx];
    if (isCt(c)) {
      editMode = 'ct';
      editMirek = parseInt(c.replace('ct:', ''));
    } else {
      editMode = 'color';
      const [h, s] = hexToHsl(c);
      editHue = h;
      editSat = s;
    }
  }

  function closeEditor() {
    editingIdx = -1;
  }

  function updateFromHsl() {
    if (editingIdx < 0) return;
    localColors[editingIdx] = hslToHex(editHue, editSat, 50);
    localColors = [...localColors];
    onChange(localColors);
  }

  function updateFromCt() {
    if (editingIdx < 0) return;
    localColors[editingIdx] = `ct:${editMirek}`;
    localColors = [...localColors];
    onChange(localColors);
  }

  function pickPreset(hex) {
    if (editingIdx < 0) {
      localColors = [...localColors, hex];
    } else {
      localColors[editingIdx] = hex;
      localColors = [...localColors];
    }
    editMode = 'color';
    const [h, s] = hexToHsl(hex);
    editHue = h;
    editSat = s;
    onChange(localColors);
  }

  function pickCtPreset(value) {
    if (editingIdx < 0) {
      localColors = [...localColors, value];
    } else {
      localColors[editingIdx] = value;
      localColors = [...localColors];
    }
    editMode = 'ct';
    editMirek = parseInt(value.replace('ct:', ''));
    onChange(localColors);
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

  function displayColor(c) {
    return isCt(c) ? ctToDisplay(c) : c;
  }

  function displayLabel(c) {
    return isCt(c) ? ctLabel(c) : c;
  }
</script>

<div class="color-picker">
  <div class="color-list">
    {#each localColors as color, i}
      <div class="color-chip-wrap">
        <button
          class="color-chip"
          class:active={editingIdx === i}
          style="background: {displayColor(color)};"
          onclick={() => editingIdx === i ? closeEditor() : openEditor(i)}
          title={displayLabel(color)}
        ></button>
        <span class="chip-label">{displayLabel(color)}</span>
        <button class="chip-remove" onclick={() => removeColor(i)}>x</button>
      </div>
    {/each}
  </div>

  <button class="small secondary" onclick={addColor}>+ Add Color</button>

  {#if editingIdx >= 0}
    <div class="color-editor">
      <div class="editor-tabs">
        <button class="tab" class:active={editMode === 'color'} onclick={() => { editMode = 'color'; if (!isCt(localColors[editingIdx])) { const [h,s] = hexToHsl(localColors[editingIdx]); editHue = h; editSat = s; } }}>Color</button>
        <button class="tab" class:active={editMode === 'ct'} onclick={() => { editMode = 'ct'; }}>White</button>
      </div>

      {#if editMode === 'color'}
        <div class="presets-grid">
          {#each presets as p}
            <button
              class="preset"
              style="background: {p.hex};"
              title={p.label}
              onclick={() => pickPreset(p.hex)}
            ></button>
          {/each}
        </div>

        <div class="slider-group">
          <label class="slider-label">Hue <span class="slider-val">{editHue}°</span></label>
          <input type="range" min="0" max="360" bind:value={editHue} oninput={updateFromHsl} class="hue-slider" />
        </div>

        <div class="slider-group">
          <label class="slider-label">Saturation <span class="slider-val">{editSat}%</span></label>
          <input type="range" min="20" max="100" bind:value={editSat} oninput={updateFromHsl} class="sat-slider" />
        </div>

        <div class="preview-row">
          <div class="preview-swatch" style="background: {displayColor(localColors[editingIdx])};"></div>
          <input
            type="text"
            class="hex-input"
            value={localColors[editingIdx]}
            oninput={(e) => {
              const v = e.target.value;
              if (/^#[0-9a-f]{6}$/i.test(v)) {
                localColors[editingIdx] = v.toLowerCase();
                localColors = [...localColors];
                const [h, s] = hexToHsl(v);
                editHue = h; editSat = s;
                onChange(localColors);
              }
            }}
          />
        </div>

      {:else}
        <div class="ct-presets">
          {#each ctPresets as p}
            <button
              class="ct-preset"
              style="background: {ctToDisplay(p.value)};"
              onclick={() => pickCtPreset(p.value)}
            >
              <span class="ct-label">{p.label}</span>
              <span class="ct-temp">{p.temp}</span>
            </button>
          {/each}
        </div>

        <div class="slider-group">
          <label class="slider-label">Temperature <span class="slider-val">{Math.round(1000000 / editMirek)}K</span></label>
          <input type="range" min="153" max="500" bind:value={editMirek} oninput={updateFromCt} class="ct-slider" />
        </div>

        <div class="preview-row">
          <div class="preview-swatch" style="background: {displayColor(localColors[editingIdx])};"></div>
          <span class="ct-display">{Math.round(1000000 / editMirek)}K ({editMirek} mirek)</span>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .color-picker { display: flex; flex-direction: column; gap: 8px; }
  .color-list { display: flex; flex-wrap: wrap; gap: 8px; }
  .color-chip-wrap { display: flex; flex-direction: column; align-items: center; gap: 2px; position: relative; }
  .color-chip {
    width: 40px; height: 40px; border-radius: 8px;
    border: 2px solid var(--border-light); cursor: pointer;
    transition: border-color 0.15s, transform 0.15s;
    padding: 0;
  }
  .color-chip:hover { border-color: var(--accent); transform: scale(1.1); }
  .color-chip.active { border-color: white; transform: scale(1.1); box-shadow: 0 0 0 2px var(--accent); }
  .chip-label { font-size: 10px; color: var(--text-muted); font-family: monospace; max-width: 48px; overflow: hidden; text-overflow: ellipsis; }
  .chip-remove {
    position: absolute; top: -4px; right: -4px;
    width: 16px; height: 16px; border-radius: 50%;
    background: var(--error); color: white; border: none;
    font-size: 10px; line-height: 1; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    opacity: 0; transition: opacity 0.15s; padding: 0;
  }
  .color-chip-wrap:hover .chip-remove { opacity: 1; }

  .color-editor {
    padding: 12px; background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border); border-radius: var(--radius);
  }
  .editor-tabs { display: flex; gap: 2px; margin-bottom: 12px; }
  .tab {
    flex: 1; padding: 6px; font-size: 12px; font-weight: 600;
    background: var(--bg-input); color: var(--text-muted);
    border: 1px solid var(--border); cursor: pointer;
    transition: all 0.15s;
  }
  .tab:first-child { border-radius: 6px 0 0 6px; }
  .tab:last-child { border-radius: 0 6px 6px 0; }
  .tab.active { background: var(--accent); color: white; border-color: var(--accent); }

  .presets-grid {
    display: grid; grid-template-columns: repeat(8, 1fr); gap: 4px;
    margin-bottom: 12px;
  }
  .preset {
    aspect-ratio: 1; border-radius: 4px; border: 1px solid rgba(255,255,255,0.1);
    cursor: pointer; transition: transform 0.1s; padding: 0;
  }
  .preset:hover { transform: scale(1.2); border-color: white; }

  .ct-presets { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 12px; }
  .ct-preset {
    padding: 8px 6px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1);
    cursor: pointer; text-align: center; transition: all 0.15s;
  }
  .ct-preset:hover { border-color: white; transform: scale(1.03); }
  .ct-label { display: block; font-size: 12px; font-weight: 600; color: #1a1a2e; }
  .ct-temp { display: block; font-size: 10px; color: rgba(0,0,0,0.6); }

  .slider-group { margin-bottom: 8px; }
  .slider-label { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
  .slider-val { color: var(--accent); font-weight: 600; }

  .hue-slider {
    width: 100%; height: 8px; border-radius: 4px; -webkit-appearance: none; appearance: none;
    background: linear-gradient(to right, #ff0000, #ffff00, #00ff00, #00ffff, #0000ff, #ff00ff, #ff0000);
    outline: none; border: none; padding: 0;
  }
  .hue-slider::-webkit-slider-thumb {
    -webkit-appearance: none; width: 16px; height: 16px; border-radius: 50%;
    background: white; border: 2px solid rgba(0,0,0,0.3); cursor: pointer;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
  }
  .sat-slider {
    width: 100%; height: 8px; border-radius: 4px; -webkit-appearance: none; appearance: none;
    background: linear-gradient(to right, #808080, var(--accent));
    outline: none; border: none; padding: 0;
  }
  .sat-slider::-webkit-slider-thumb {
    -webkit-appearance: none; width: 16px; height: 16px; border-radius: 50%;
    background: white; border: 2px solid rgba(0,0,0,0.3); cursor: pointer;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
  }
  .ct-slider {
    width: 100%; height: 8px; border-radius: 4px; -webkit-appearance: none; appearance: none;
    background: linear-gradient(to right, #a0c4ff, #fff4e0, #ffb347);
    outline: none; border: none; padding: 0;
  }
  .ct-slider::-webkit-slider-thumb {
    -webkit-appearance: none; width: 16px; height: 16px; border-radius: 50%;
    background: white; border: 2px solid rgba(0,0,0,0.3); cursor: pointer;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
  }

  .preview-row {
    display: flex; align-items: center; gap: 10px; margin-top: 8px;
  }
  .preview-swatch {
    width: 36px; height: 36px; border-radius: 8px;
    border: 2px solid var(--border-light); flex-shrink: 0;
  }
  .hex-input {
    font-family: monospace; font-size: 13px; width: 100px;
    background: var(--bg-input); color: var(--text-primary);
    border: 1px solid var(--border); border-radius: var(--radius);
    padding: 6px 8px;
  }
  .ct-display { font-size: 13px; color: var(--text-secondary); }
</style>
