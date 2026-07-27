<script>
  import { bulbPreview, ctKelvin, ctToHex, hexToHsl, hslToHex, isCt, isHex } from '../lib/color.js';

  let { value = '#ffffff', onChange } = $props();
  let open = $state(false);
  let hue = $state(0);
  let sat = $state(100);
  let popup = $state(null);

  const presets = [
    '#ff0000', '#ff4400', '#ff8800', '#ffcc00', '#ccff00', '#44ff00',
    '#00ffaa', '#00ddff', '#0033ff', '#7700ff', '#ff00cc', '#ff0066',
  ];
  const ctPresets = ['ct:500', 'ct:370', 'ct:250', 'ct:154'];

  function display(c) {
    if (!c) return '#888888';
    return isCt(c) ? ctToHex(c) : bulbPreview(c);
  }

  function toggle() {
    if (!isCt(value) && isHex(value)) {
      const [h, s] = hexToHsl(value);
      hue = h; sat = s;
    }
    open = !open;
  }

  function pick(c) { onChange(c); open = false; }
  function updateHsl() { onChange(hslToHex(hue, sat, 50)); }

  $effect(() => {
    if (!open) return;
    function onDocClick(e) {
      if (popup && !popup.contains(e.target) && !e.target.closest('.scp-swatch')) open = false;
    }
    function onKey(e) { if (e.key === 'Escape') open = false; }
    document.addEventListener('mousedown', onDocClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      document.removeEventListener('keydown', onKey);
    };
  });
</script>

<div class="scp">
  <button
    class="scp-swatch"
    style="background: {display(value)}"
    onclick={toggle}
    aria-label="Pick colour, currently {isCt(value) ? ctKelvin(value) + 'K' : value}"
    aria-expanded={open}
  ></button>

  {#if open}
    <div class="scp-popup" bind:this={popup}>
      <div class="scp-presets">
        {#each presets as p}
          <button class="scp-dot" style="background: {bulbPreview(p)}" onclick={() => pick(p)} aria-label={p}></button>
        {/each}
      </div>
      <div class="scp-ct">
        {#each ctPresets as ct}
          <button class="scp-ct-btn" style="background: {ctToHex(ct)}" onclick={() => pick(ct)}>{ctKelvin(ct)}K</button>
        {/each}
      </div>
      <label class="scp-row">
        <span>Hue</span>
        <input type="range" min="0" max="360" bind:value={hue} oninput={updateHsl} class="scp-hue" />
      </label>
      <label class="scp-row">
        <span>Sat</span>
        <input type="range" min="30" max="100" bind:value={sat} oninput={updateHsl} class="scp-sat" />
      </label>
      <div class="scp-foot">
        <span class="scp-hex">{isCt(value) ? ctKelvin(value) + 'K' : value}</span>
        {#if !isCt(value) && isHex(value) && bulbPreview(value).toLowerCase() !== value.toLowerCase()}
          <span class="scp-shift">bulb: {bulbPreview(value)}</span>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .scp { position: relative; }
  .scp-swatch {
    width: 32px; height: 32px; border-radius: 7px;
    border: 2px solid var(--border-light); cursor: pointer;
    padding: 0; transition: border-color .15s, transform .15s;
  }
  .scp-swatch:hover { border-color: var(--accent); transform: translateY(-1px); }
  .scp-popup {
    position: absolute; top: 40px; left: 0; z-index: 100;
    background: var(--bg-secondary); border: 1px solid var(--border-light);
    border-radius: var(--radius); padding: 12px;
    display: flex; flex-direction: column; gap: 9px;
    min-width: 220px; box-shadow: 0 8px 28px rgba(0,0,0,.55);
  }
  .scp-presets { display: grid; grid-template-columns: repeat(6, 1fr); gap: 4px; }
  .scp-dot {
    width: 26px; height: 26px; border-radius: 5px;
    border: 1px solid rgba(255,255,255,.12); cursor: pointer; padding: 0;
    transition: transform .1s;
  }
  .scp-dot:hover { border-color: #fff; transform: scale(1.12); }
  .scp-ct { display: flex; gap: 4px; }
  .scp-ct-btn {
    flex: 1; padding: 4px 2px; border-radius: 5px; font-size: 10px; font-weight: 700;
    border: 1px solid rgba(255,255,255,.12); cursor: pointer; color: #1a1a2e;
  }
  .scp-ct-btn:hover { border-color: #fff; }

  .scp-row { display: flex; align-items: center; gap: 8px; }
  .scp-row span { font-size: 11px; color: var(--text-muted); width: 24px; }
  input[type="range"] {
    flex: 1; height: 8px; border-radius: 4px;
    -webkit-appearance: none; appearance: none; outline: none; border: none; padding: 0;
  }
  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none; width: 14px; height: 14px; border-radius: 50%;
    background: #fff; border: 2px solid rgba(0,0,0,.3); cursor: pointer;
  }
  .scp-hue {
    background: linear-gradient(to right, #ff0000, #ffff00, #00ff00, #00ffff, #0000ff, #ff00ff, #ff0000);
  }
  .scp-sat { background: linear-gradient(to right, #9aa0aa, var(--accent)); }

  .scp-foot { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
  .scp-hex { font-family: ui-monospace, monospace; font-size: 11px; color: var(--text-secondary); }
  .scp-shift { font-size: 10px; color: var(--warning); }
</style>
