<script>
  let { value = '#ffffff', onChange } = $props();
  let open = $state(false);
  let hue = $state(0);
  let sat = $state(100);

  const presets = [
    '#ff0000', '#ff4400', '#ff8800', '#ffcc00', '#88ff00', '#00ff00',
    '#00ff88', '#00ccff', '#0044ff', '#8800ff', '#ff00cc', '#ff0066',
  ];
  const ctPresets = [
    { value: 'ct:500', label: '2000K' },
    { value: 'ct:370', label: '2700K' },
    { value: 'ct:250', label: '4000K' },
    { value: 'ct:154', label: '6500K' },
  ];

  function isCt(c) { return typeof c === 'string' && c.startsWith('ct:'); }

  function hslToHex(h, s, l) {
    s /= 100; l /= 100;
    const a = s * Math.min(l, 1 - l);
    const f = (n) => {
      const k = (n + h / 30) % 12;
      const color = l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
      return Math.round(255 * Math.max(0, Math.min(1, color)));
    };
    return `#${f(0).toString(16).padStart(2,'0')}${f(8).toString(16).padStart(2,'0')}${f(4).toString(16).padStart(2,'0')}`;
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
    return [Math.round(h), Math.round(s * 100)];
  }

  function displayColor(c) {
    if (!c) return '#888';
    if (isCt(c)) {
      const mirek = parseInt(c.replace('ct:', ''));
      const t = (mirek - 153) / (500 - 153);
      const r = Math.round(255 * (0.8 + 0.2 * t));
      const g = Math.round(255 * (0.7 + 0.15 * t - 0.15 * t * t));
      const b = Math.round(255 * (0.5 + 0.5 * (1 - t)));
      return `#${r.toString(16).padStart(2,'0')}${g.toString(16).padStart(2,'0')}${b.toString(16).padStart(2,'0')}`;
    }
    return c;
  }

  function openPicker() {
    if (!isCt(value)) {
      const [h, s] = hexToHsl(value);
      hue = h; sat = s;
    }
    open = !open;
  }

  function pick(c) { onChange(c); open = false; }
  function updateHsl() { onChange(hslToHex(hue, sat, 50)); }
</script>

<div class="scp">
  <button class="scp-swatch" style="background: {displayColor(value)};" onclick={openPicker}></button>
  {#if open}
    <div class="scp-popup">
      <div class="scp-presets">
        {#each presets as p}
          <button class="scp-dot" style="background: {p};" onclick={() => pick(p)}></button>
        {/each}
      </div>
      <div class="scp-ct">
        {#each ctPresets as ct}
          <button class="scp-ct-btn" style="background: {displayColor(ct.value)};" onclick={() => pick(ct.value)}>{ct.label}</button>
        {/each}
      </div>
      <input type="range" min="0" max="360" bind:value={hue} oninput={updateHsl} class="scp-hue" />
      <input type="range" min="20" max="100" bind:value={sat} oninput={updateHsl} class="scp-sat" />
    </div>
  {/if}
</div>

<style>
  .scp { position: relative; }
  .scp-swatch {
    width: 32px; height: 32px; border-radius: 6px;
    border: 2px solid var(--border-light); cursor: pointer;
    padding: 0; transition: border-color 0.15s;
  }
  .scp-swatch:hover { border-color: var(--accent); }
  .scp-popup {
    position: absolute; top: 38px; left: 0; z-index: 100;
    background: var(--bg-secondary); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 10px;
    display: flex; flex-direction: column; gap: 8px;
    min-width: 200px; box-shadow: 0 4px 16px rgba(0,0,0,0.5);
  }
  .scp-presets { display: grid; grid-template-columns: repeat(6, 1fr); gap: 3px; }
  .scp-dot {
    width: 24px; height: 24px; border-radius: 4px;
    border: 1px solid rgba(255,255,255,0.1); cursor: pointer; padding: 0;
  }
  .scp-dot:hover { border-color: white; transform: scale(1.15); }
  .scp-ct { display: flex; gap: 3px; }
  .scp-ct-btn {
    flex: 1; padding: 3px; border-radius: 4px; font-size: 9px; font-weight: 600;
    border: 1px solid rgba(255,255,255,0.1); cursor: pointer; color: #1a1a2e;
  }
  .scp-ct-btn:hover { border-color: white; }
  .scp-hue {
    width: 100%; height: 8px; border-radius: 4px; -webkit-appearance: none; appearance: none;
    background: linear-gradient(to right, #ff0000, #ffff00, #00ff00, #00ffff, #0000ff, #ff00ff, #ff0000);
    outline: none; border: none; padding: 0;
  }
  .scp-hue::-webkit-slider-thumb {
    -webkit-appearance: none; width: 14px; height: 14px; border-radius: 50%;
    background: white; border: 2px solid rgba(0,0,0,0.3); cursor: pointer;
  }
  .scp-sat {
    width: 100%; height: 8px; border-radius: 4px; -webkit-appearance: none; appearance: none;
    background: linear-gradient(to right, #808080, var(--accent));
    outline: none; border: none; padding: 0;
  }
  .scp-sat::-webkit-slider-thumb {
    -webkit-appearance: none; width: 14px; height: 14px; border-radius: 50%;
    background: white; border: 2px solid rgba(0,0,0,0.3); cursor: pointer;
  }
</style>
