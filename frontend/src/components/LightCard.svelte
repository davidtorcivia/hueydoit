<script>
  import { api } from '../lib/api.js';

  let { light, onOverride, onClearOverride } = $props();

  let showOverride = $state(false);
  let overrideColor = $state('#ffffff');
  let overrideBrightness = $state(100);
  let overrideMinutes = $state(30);

  let displayColor = $derived(
    light.state?.color_hex || light.override?.color || '#888888'
  );
  let isOn = $derived(
    light.state?.on ?? light.override?.on_state ?? false
  );
  let brightness = $derived(
    light.state?.brightness ?? light.override?.brightness ?? 0
  );
  let colorLabel = $derived(
    light.state?.color_hex || light.override?.color || null
  );

  async function flash() {
    try {
      await api.testLight(light.name);
    } catch (e) {
      console.error('Flash failed:', e);
    }
  }

  async function applyOverride() {
    await onOverride(light.name, {
      color: overrideColor,
      brightness: overrideBrightness,
      on_state: true,
      expires_minutes: overrideMinutes,
    });
    showOverride = false;
  }

  async function turnOff() {
    await onOverride(light.name, { on_state: false, expires_minutes: overrideMinutes });
  }
</script>

<div class="card light-card">
  <div class="light-header">
    <div class="light-color" class:light-off={!isOn} style="background: {displayColor}"></div>
    <div class="light-info">
      <h3>{light.friendly_name || light.name}</h3>
      <div class="light-meta">
        <span class="light-type badge info">{light.type}</span>
        {#if colorLabel}
          <span class="light-color-label" style="color: {displayColor}">{colorLabel}</span>
        {/if}
      </div>
    </div>
    <div class="light-status" class:on={isOn}>{isOn ? 'ON' : 'OFF'}</div>
  </div>

  <div class="brightness-bar">
    <div class="brightness-fill" style="width: {isOn ? brightness : 0}%"></div>
    <span class="brightness-label">{isOn ? Math.round(brightness) + '%' : 'off'}</span>
  </div>

  {#if light.active_rule}
    <div class="active-rule">
      <span class="badge ok">Active Rule</span>
      <span>{light.active_rule.rule_name || light.active_rule}</span>
    </div>
  {/if}

  {#if light.override}
    <div class="override-info">
      <span class="badge warning">Override ({light.override.source})</span>
      <button class="small secondary" onclick={() => onClearOverride(light.name)}>Clear</button>
    </div>
  {/if}

  <div class="light-actions">
    <button class="small secondary" onclick={flash}>Flash</button>
    <button class="small secondary" onclick={() => showOverride = !showOverride}>
      {showOverride ? 'Cancel' : 'Override'}
    </button>
    <button class="small secondary" onclick={turnOff}>Off</button>
  </div>

  {#if showOverride}
    <div class="override-form">
      <div class="form-group">
        <label>Color</label>
        <input type="color" bind:value={overrideColor} />
      </div>
      <div class="form-group">
        <label>Brightness: {overrideBrightness}%</label>
        <input type="range" min="1" max="100" bind:value={overrideBrightness} />
      </div>
      <div class="form-group">
        <label>Expires (min)</label>
        <input type="number" bind:value={overrideMinutes} min="1" max="1440" />
      </div>
      <button class="primary small" onclick={applyOverride}>Apply</button>
    </div>
  {/if}
</div>

<style>
  .light-card { display: flex; flex-direction: column; gap: 12px; }
  .light-header { display: flex; align-items: center; gap: 12px; }
  .light-color {
    width: 48px; height: 48px; border-radius: 50%;
    border: 3px solid var(--border-light);
    flex-shrink: 0;
    transition: background 0.3s, opacity 0.3s;
  }
  .light-color.light-off { opacity: 0.35; }
  .light-info { flex: 1; }
  .light-info h3 { margin-bottom: 4px; }
  .light-meta { display: flex; align-items: center; gap: 8px; }
  .light-color-label { font-size: 11px; font-family: monospace; }
  .light-status {
    font-size: 12px; font-weight: 700;
    color: var(--text-muted);
  }
  .light-status.on { color: var(--success); }
  .brightness-bar {
    height: 6px; background: var(--border); border-radius: 3px;
    position: relative; overflow: hidden;
  }
  .brightness-fill {
    height: 100%; background: var(--accent); border-radius: 3px;
    transition: width 0.3s;
  }
  .brightness-label {
    position: absolute; right: 0; top: -16px;
    font-size: 11px; color: var(--text-muted);
  }
  .active-rule, .override-info {
    display: flex; align-items: center; gap: 8px; font-size: 13px;
  }
  .light-actions { display: flex; gap: 6px; }
  .override-form {
    padding: 12px; background: var(--bg-input);
    border-radius: var(--radius); margin-top: 4px;
  }
  .override-form .form-group { margin-bottom: 10px; }
  .override-form input[type="color"] {
    width: 60px; height: 32px; padding: 2px; cursor: pointer;
  }
  .override-form input[type="range"] { width: 100%; }
</style>
