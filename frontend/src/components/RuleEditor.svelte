<script>
  import ColorPicker from './ColorPicker.svelte';
  import SingleColorPick from './SingleColorPick.svelte';
  import ConditionBuilder from './ConditionBuilder.svelte';
  import { suggestPalettes } from '../lib/paletteSuggest.js';

  let { rule = null, targets = [], onSave, onCancel } = $props();

  let name = $state(rule?.name || '');
  let priority = $state(rule?.priority ?? 50);
  let enabled = $state(rule?.enabled ?? true);

  let condition = $state(rule?.config?.condition || {});

  let effectMode = $state(rule?.config?.effect?.mode || 'static');
  let effectColors = $state(rule?.config?.effect?.colors || ['#ffffff']);
  let effectBrightness = $state(rule?.config?.effect?.brightness ?? 80);
  let effectTransition = $state(rule?.config?.effect?.transition ?? 1000);
  let effectCycleInterval = $state(rule?.config?.effect?.cycle_interval ?? 30);
  let useHolidayColors = $state(rule?.config?.effect?.use_holiday_colors ?? false);

  let selectedTargets = $state(rule?.config?.targets || []);

  // Per-light color & brightness assignment
  let enableColorMap = $state(!!rule?.config?.effect?.color_map || !!rule?.config?.effect?.brightness_map);
  let colorMap = $state(rule?.config?.effect?.color_map || {});
  let brightnessMap = $state(rule?.config?.effect?.brightness_map || {});

  // Sort targets alphabetically for stable display
  let sortedTargets = $derived(
    [...targets].sort((a, b) => (a.friendly_name || a.name).localeCompare(b.friendly_name || b.name))
  );
  // Keep selected targets in same order as sortedTargets for color map display
  let orderedSelectedTargets = $derived(
    sortedTargets.map(t => t.name).filter(name => selectedTargets.includes(name))
  );

  function toggleTarget(t) {
    if (selectedTargets.includes(t)) {
      selectedTargets = selectedTargets.filter(x => x !== t);
      // Clean up color map entry
      const newMap = { ...colorMap };
      delete newMap[t];
      colorMap = newMap;
    } else {
      selectedTargets = [...selectedTargets, t];
    }
  }

  function updateColorMapEntry(targetName, color) {
    colorMap = { ...colorMap, [targetName]: color };
  }

  function updateBrightnessMapEntry(targetName, brightness) {
    brightnessMap = { ...brightnessMap, [targetName]: Number(brightness) };
  }

  // Palette suggestions
  let suggestions = $state([]);

  function showSuggestions() {
    // Build a keyword from the rule name + any holiday condition
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    suggestions = suggestPalettes(slug, name);
  }

  function applySuggestion(palette) {
    effectColors = [...palette];
    suggestions = [];
  }

  function distributeColorsToLights() {
    if (effectColors.length === 0 || orderedSelectedTargets.length === 0) return;
    const newColorMap = {};
    for (let i = 0; i < orderedSelectedTargets.length; i++) {
      const colorIdx = i % effectColors.length;
      newColorMap[orderedSelectedTargets[i]] = effectColors[colorIdx];
    }
    colorMap = newColorMap;
  }

  let isHolidayProvider = $derived(
    condition?.provider === 'holiday' ||
    (condition?.all_of || []).some(c => c?.provider === 'holiday') ||
    (condition?.any_of || []).some(c => c?.provider === 'holiday')
  );

  function buildConfig() {
    const effect = { mode: effectMode };
    if (effectMode !== 'off') {
      if (!useHolidayColors) {
        effect.colors = effectColors;
      }
      effect.brightness = effectBrightness;
      if (effectTransition > 0) effect.transition = effectTransition;
      if (effectMode === 'cycle') effect.cycle_interval = effectCycleInterval;
      if (useHolidayColors) effect.use_holiday_colors = true;
      if (enableColorMap) {
        // Only include entries for selected targets
        const filteredColors = {};
        const filteredBrightness = {};
        for (const t of selectedTargets) {
          if (colorMap[t]) filteredColors[t] = colorMap[t];
          if (brightnessMap[t] !== undefined) filteredBrightness[t] = brightnessMap[t];
        }
        if (Object.keys(filteredColors).length > 0) effect.color_map = filteredColors;
        if (Object.keys(filteredBrightness).length > 0) effect.brightness_map = filteredBrightness;
      }
    }

    return { condition, effect, targets: selectedTargets };
  }

  function handleSave() {
    onSave({
      name,
      priority,
      enabled,
      config: buildConfig(),
    });
  }
</script>

<div class="modal-overlay" onclick={onCancel}>
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <div class="modal rule-modal" onclick={(e) => e.stopPropagation()}>
    <h2 class="mb-4">{rule ? 'Edit Rule' : 'Create Rule'}</h2>

    <div class="form-group">
      <label>Name</label>
      <input type="text" bind:value={name} placeholder="Rule name" />
    </div>

    <div class="form-group">
      <label>Priority (lower = higher priority)</label>
      <input type="number" bind:value={priority} min="1" max="9999" />
    </div>

    <h3 class="section-title">Condition</h3>
    <ConditionBuilder {condition} onChange={(c) => condition = c} />

    <h3 class="section-title mt-4">Effect</h3>

    <div class="form-group">
      <label>Effect Mode</label>
      <select bind:value={effectMode}>
        <option value="static">Static</option>
        <option value="off">Off</option>
        <option value="breathe">Breathe</option>
        <option value="cycle">Cycle</option>
        <option value="gradient">Gradient</option>
      </select>
    </div>

    {#if effectMode === 'off'}
      <span class="hint">Lights will be turned off</span>
    {:else}
      {#if isHolidayProvider}
        <div class="form-group">
          <label>
            <input type="checkbox" bind:checked={useHolidayColors} />
            Use active holiday's colors automatically
          </label>
          <span class="hint">Colors come from the currently active holiday</span>
        </div>
      {/if}

      {#if !useHolidayColors}
        <div class="form-group">
          <label>Colors</label>
          <ColorPicker colors={effectColors} onChange={(c) => effectColors = c} />
          <div class="colors-toolbar">
            <button class="small secondary" onclick={showSuggestions} disabled={!name}>Suggest Palette</button>
            {#if effectMode === 'static' || effectMode === 'breathe'}
              <span class="hint">Only the first color is used</span>
            {:else if effectMode === 'cycle'}
              <span class="hint">Add 2+ colors to cycle through as a palette</span>
            {:else if effectMode === 'gradient'}
              <span class="hint">Add 2+ colors to spread across lights as a gradient</span>
            {/if}
          </div>
          {#if suggestions.length > 0}
            <div class="palette-suggestions">
              {#each suggestions as palette, i}
                <button class="palette-option" onclick={() => applySuggestion(palette)}>
                  {#each palette as color}
                    <span class="swatch" style="background: {color};"></span>
                  {/each}
                </button>
              {/each}
            </div>
          {/if}
        </div>
      {/if}

      <div class="form-group">
        <label>Brightness: {effectBrightness}%</label>
        <input type="range" min="1" max="100" bind:value={effectBrightness} />
      </div>

      {#if effectMode !== 'cycle'}
        <div class="form-group">
          <label>Transition (ms)</label>
          <input type="number" bind:value={effectTransition} min="0" max="60000" />
        </div>
      {/if}

      {#if effectMode === 'cycle'}
        <div class="form-group">
          <label>Cycle Interval (seconds)</label>
          <input type="number" bind:value={effectCycleInterval} min="1" max="3600" />
          <span class="hint">Time to transition between colors in the palette</span>
        </div>
      {/if}
    {/if}

    <h3 class="section-title mt-4">Targets</h3>

    <div class="form-group">
      <div class="target-list">
        {#each sortedTargets as t}
          <label class="target-check">
            <input type="checkbox" checked={selectedTargets.includes(t.name)} onchange={() => toggleTarget(t.name)} />
            {t.friendly_name || t.name}
          </label>
        {/each}
        {#if targets.length === 0}
          <span class="text-muted">No lights configured</span>
        {/if}
      </div>
    </div>

    {#if selectedTargets.length >= 2 && effectMode !== 'off'}
      <div class="form-group">
        <label>
          <input type="checkbox" bind:checked={enableColorMap} />
          Assign colors per light
        </label>
      </div>

      {#if enableColorMap}
        <div class="color-map-section">
          {#if effectColors.length > 0 && orderedSelectedTargets.length > 0}
            <button class="small secondary distribute-btn" onclick={distributeColorsToLights}>
              Distribute palette to lights
            </button>
          {/if}
          {#each orderedSelectedTargets as tName}
            {@const targetInfo = targets.find(t => t.name === tName)}
            <div class="color-map-row">
              <span class="color-map-label">{targetInfo?.friendly_name || tName}</span>
              <SingleColorPick
                value={colorMap[tName] || '#ffffff'}
                onChange={(c) => updateColorMapEntry(tName, c)}
              />
              <input
                type="range"
                min="1" max="100"
                value={brightnessMap[tName] ?? effectBrightness}
                oninput={(e) => updateBrightnessMapEntry(tName, e.target.value)}
                class="brightness-slider"
              />
              <span class="brightness-val">{brightnessMap[tName] ?? effectBrightness}%</span>
            </div>
          {/each}
        </div>
      {/if}
    {/if}

    <div class="flex gap-2 mt-4" style="justify-content: flex-end;">
      <button class="secondary" onclick={onCancel}>Cancel</button>
      <button class="primary" onclick={handleSave}>Save</button>
    </div>
  </div>
</div>

<style>
  .rule-modal { max-height: 90vh; overflow-y: auto; }
  .section-title { font-size: 14px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 16px; margin-bottom: 8px; }
  .target-list { display: flex; flex-direction: column; gap: 8px; }
  .target-check {
    display: flex; align-items: center; gap: 10px;
    font-size: 14px; cursor: pointer;
    padding: 6px 10px;
    border-radius: var(--radius);
    transition: background 0.15s;
  }
  .target-check:hover {
    background: rgba(255, 255, 255, 0.04);
  }
  .target-check input { cursor: pointer; }
  .hint { display: block; font-size: 12px; color: var(--text-muted); margin-top: 2px; }
  .color-map-section {
    display: flex; flex-direction: column; gap: 8px;
    padding: 12px; background: rgba(255, 255, 255, 0.03);
    border-radius: var(--radius); border: 1px solid var(--border);
  }
  .color-map-row {
    display: flex; align-items: center; gap: 10px;
  }
  .color-map-label { flex: 1; font-size: 14px; }
  .brightness-slider { width: 80px; }
  .brightness-val { font-size: 12px; color: var(--text-muted); width: 36px; text-align: right; }
  .colors-toolbar { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
  .colors-toolbar .hint { margin-top: 0; }
  .palette-suggestions {
    display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;
  }
  .palette-option {
    display: flex; gap: 3px; padding: 6px 10px;
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--radius); cursor: pointer;
    transition: border-color 0.15s;
  }
  .palette-option:hover { border-color: var(--accent); }
  .swatch {
    display: inline-block; width: 20px; height: 20px;
    border-radius: 3px; border: 1px solid rgba(255, 255, 255, 0.15);
  }
  .distribute-btn { margin-bottom: 8px; }
</style>
