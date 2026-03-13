<script>
  import ColorPicker from './ColorPicker.svelte';
  import ConditionBuilder from './ConditionBuilder.svelte';

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

  // Per-light color assignment
  let enableColorMap = $state(!!rule?.config?.effect?.color_map);
  let colorMap = $state(rule?.config?.effect?.color_map || {});

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

  let isHolidayProvider = $derived(condition?.provider === 'holiday');

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
      if (enableColorMap && Object.keys(colorMap).length > 0) {
        // Only include entries for selected targets
        const filtered = {};
        for (const t of selectedTargets) {
          if (colorMap[t]) filtered[t] = colorMap[t];
        }
        if (Object.keys(filtered).length > 0) effect.color_map = filtered;
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

    {#if effectMode !== 'off'}
      {#if isHolidayProvider}
        <div class="form-group">
          <label>
            <input type="checkbox" bind:checked={useHolidayColors} />
            Use active holiday's colors automatically
          </label>
          <span class="hint">When enabled, colors come from the currently active holiday</span>
        </div>
      {/if}

      {#if !useHolidayColors}
        <div class="form-group">
          <label>Colors</label>
          <ColorPicker colors={effectColors} onChange={(c) => effectColors = c} />
        </div>
      {/if}

      <div class="form-group">
        <label>Brightness: {effectBrightness}%</label>
        <input type="range" min="1" max="100" bind:value={effectBrightness} />
      </div>

      <div class="form-group">
        <label>Transition (ms)</label>
        <input type="number" bind:value={effectTransition} min="0" max="60000" />
      </div>

      {#if effectMode === 'cycle'}
        <div class="form-group">
          <label>Cycle Interval (seconds)</label>
          <input type="number" bind:value={effectCycleInterval} min="1" max="3600" />
        </div>
      {/if}
    {/if}

    <h3 class="section-title mt-4">Targets</h3>

    <div class="form-group">
      <div class="target-list">
        {#each targets as t}
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
          {#each selectedTargets as tName}
            {@const targetInfo = targets.find(t => t.name === tName)}
            <div class="color-map-row">
              <span class="color-map-label">{targetInfo?.friendly_name || tName}</span>
              <input
                type="color"
                value={colorMap[tName] || '#ffffff'}
                oninput={(e) => updateColorMapEntry(tName, e.target.value)}
              />
              <span class="color-hex">{colorMap[tName] || '#ffffff'}</span>
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
  .target-list { display: flex; flex-direction: column; gap: 4px; }
  .target-check {
    display: flex; align-items: center; gap: 8px;
    font-size: 14px; cursor: pointer;
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
  .color-map-row input[type="color"] {
    width: 36px; height: 28px; padding: 1px; cursor: pointer;
    border: 1px solid var(--border);
  }
  .color-hex { font-size: 12px; color: var(--text-muted); font-family: monospace; width: 64px; }
</style>
