<script>
  import ColorPicker from '../components/ColorPicker.svelte';
  import { api } from '../lib/api.js';
  import { toast } from '../lib/toast.js';
  import { suggestPalettes } from '../lib/paletteSuggest.js';
  import { bulbPreview } from '../lib/color.js';

  let holidays = $state([]);
  let loading = $state(true);
  let showAdd = $state(false);
  let editingSlug = $state(null);
  let editColors = $state([]);
  let filter = $state('all');

  let newName = $state('');
  let newDate = $state('');
  let newWindowStart = $state('');
  let newWindowEnd = $state('');
  let newRecurring = $state(true);
  let newColors = $state(['#ff0000', '#00ff00']);

  $effect(() => {
    loadHolidays();
  });

  async function loadHolidays() {
    try {
      holidays = await api.getHolidays();
    } catch (e) {
      console.error('Failed to load holidays:', e);
    }
    loading = false;
  }

  let filtered = $derived(
    filter === 'all' ? holidays : holidays.filter(h => h.category === filter)
  );

  const CATEGORY_ORDER = ['custom', 'us_federal', 'cultural', 'international', 'seasonal', 'fun'];
  const CATEGORY_LABEL = {
    custom: 'Custom', us_federal: 'US Federal', cultural: 'Cultural',
    international: 'International', seasonal: 'Seasonal', fun: 'Fun',
  };

  // Grouped by category, then by date, so the page reads as sections rather
  // than one undifferentiated wall of cards.
  let grouped = $derived(
    CATEGORY_ORDER
      .map((cat) => ({
        cat,
        label: CATEGORY_LABEL[cat] || cat,
        items: filtered
          .filter((h) => h.category === cat)
          .sort((a, b) => String(a.date).localeCompare(String(b.date))),
      }))
      .filter((g) => g.items.length > 0)
  );

  async function addHoliday() {
    try {
      await api.addHoliday({
        name: newName,
        date: newDate,
        window_start: newWindowStart || newDate,
        window_end: newWindowEnd || newDate,
        recurring: newRecurring,
        colors: newColors,
      });
      showAdd = false;
      newName = ''; newDate = ''; newWindowStart = ''; newWindowEnd = '';
      await loadHolidays();
    } catch (e) {
      toast.error('Add failed: ' + e.message);
    }
  }

  async function removeHoliday(id) {
    if (!confirm('Remove this custom holiday?')) return;
    try {
      await api.removeHoliday(id);
      await loadHolidays();
    } catch (e) {
      toast.error('Remove failed: ' + e.message);
    }
  }

  let editWindowBefore = $state(0);
  let editWindowAfter = $state(0);
  let editPriority = $state(50);
  let editName = $state('');
  let editSlugForSuggest = $state('');
  let suggestions = $state([]);

  function startEdit(h) {
    editingSlug = h.slug;
    editColors = [...(h.colors || [])];
    editWindowBefore = h.window_before_days ?? 0;
    editWindowAfter = h.window_after_days ?? 0;
    editPriority = h.priority ?? 50;
    editName = h.name;
    editSlugForSuggest = h.slug;
    suggestions = [];
  }

  function cancelEdit() {
    editingSlug = null;
    editColors = [];
    editWindowBefore = 0;
    editWindowAfter = 0;
    suggestions = [];
  }

  function showSuggestions() {
    suggestions = suggestPalettes(editSlugForSuggest, editName);
  }

  function applySuggestion(palette) {
    editColors = [...palette];
    suggestions = [];
  }

  async function saveConfig(slug) {
    try {
      await api.updateHolidayConfig(slug, {
        colors: editColors,
        window_before_days: editWindowBefore,
        window_after_days: editWindowAfter,
        priority: editPriority,
      });
      editingSlug = null;
      suggestions = [];
      await loadHolidays();
    } catch (e) {
      toast.error('Save failed: ' + e.message);
    }
  }

  async function toggleEnabled(h) {
    try {
      await api.updateHolidayConfig(h.slug, { enabled: !h.enabled });
      await loadHolidays();
    } catch (e) {
      toast.error('Toggle failed: ' + e.message);
    }
  }

  function windowPreview(dateStr, before, after) {
    const d = new Date(dateStr + 'T00:00:00');
    const ws = new Date(d.getTime() - before * 86400000);
    const we = new Date(d.getTime() + after * 86400000);
    const fmt = { month: 'short', day: 'numeric' };
    return `${ws.toLocaleDateString('en-US', fmt)} – ${we.toLocaleDateString('en-US', fmt)}`;
  }

  function isActive(h) {
    const today = new Date().toISOString().slice(0, 10);
    return h.enabled && h.window_start <= today && today <= h.window_end;
  }

  // Suggest palettes for the Add Holiday modal too
  let newSuggestions = $state([]);
  function suggestForNew() {
    const slug = newName.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    newSuggestions = suggestPalettes(slug, newName);
  }
  function applyNewSuggestion(palette) {
    newColors = [...palette];
    newSuggestions = [];
  }
</script>

<div class="page-header">
  <h1>Holidays</h1>
  <div class="flex gap-2">
    <select bind:value={filter}>
      <option value="all">All</option>
      <option value="us_federal">US Federal</option>
      <option value="cultural">Cultural</option>
      <option value="international">International</option>
      <option value="fun">Fun</option>
      <option value="seasonal">Seasonal</option>
      <option value="custom">Custom</option>
    </select>
    <button class="primary" onclick={() => showAdd = true}>+ Add Holiday</button>
  </div>
</div>

{#if loading}
  <p>Loading...</p>
{:else}
  {#each grouped as group}
    <div class="section-title">
      <h2>{group.label}</h2>
      <span class="count">{group.items.length}</span>
    </div>
    <div class="grid grid-3">
      {#each group.items as h}
      <div class="card holiday-card" class:active-holiday={isActive(h)} class:disabled-holiday={!h.enabled}>
        <div class="flex justify-between items-center mb-2">
          <h3>{h.name}</h3>
          <div class="flex gap-2 items-center">
            <span class="badge {h.category === 'us_federal' ? 'info' : h.category === 'cultural' ? 'ok' : 'warning'}">{h.category}</span>
            <div class="toggle" class:active={h.enabled} onclick={() => toggleEnabled(h)}></div>
          </div>
        </div>
        <div class="holiday-date" title="Priority {h.priority ?? '?'} — lower wins when holidays overlap">{h.date}</div>
        {#if h.window_start !== h.date || h.window_end !== h.date}
          <div class="holiday-window">Window: {h.window_start} — {h.window_end}</div>
        {/if}

        <div class="holiday-colors-row">
          {#if h.colors?.length}
            <div class="strip" title={h.colors.join('  ')}>
              {#each h.colors as color}
                <span class="strip-seg" style="background: {bulbPreview(color)}"></span>
              {/each}
            </div>
          {:else}
            <span class="no-colours">No colours</span>
          {/if}
          <button class="small ghost edit-btn" onclick={() => startEdit(h)}>Edit</button>
        </div>

        {#if isActive(h)}
          <span class="badge ok mt-2">Active Now</span>
        {/if}
        {#if h.category === 'custom'}
          <button class="small danger mt-2" onclick={() => removeHoliday(h.id)}>Remove</button>
        {/if}
      </div>
      {/each}
    </div>
  {/each}
{/if}

{#if editingSlug}
  {@const editing = holidays.find((x) => x.slug === editingSlug)}
  <div class="modal-overlay" onclick={cancelEdit} role="presentation">
    <div class="modal" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <h2 class="mb-4">{editing?.name ?? 'Edit holiday'}</h2>
      <div class="edit-panel">

            <div class="edit-section">
              <label class="edit-label">Colors</label>
              <ColorPicker colors={editColors} onChange={(c) => editColors = c} />
              <button class="small secondary mt-1" onclick={showSuggestions}>Suggest Palette</button>
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
            <div class="edit-section">
              <label class="edit-label">Active window</label>
              <div class="window-slider">
                <div class="slider-header">
                  <span>Days before</span>
                  <span class="slider-value">{editWindowBefore}</span>
                </div>
                <input type="range" min="0" max="60" bind:value={editWindowBefore} />
              </div>
              <div class="window-slider">
                <div class="slider-header">
                  <span>Days after</span>
                  <span class="slider-value">{editWindowAfter}</span>
                </div>
                <input type="range" min="0" max="60" bind:value={editWindowAfter} />
              </div>
              <div class="window-preview">
                Active: {windowPreview(editing.date, editWindowBefore, editWindowAfter)}
              </div>
            </div>
            <div class="edit-section">
              <label class="edit-label">Priority (lower = wins over others)</label>
              <div class="slider-header">
                <span>Priority</span>
                <span class="slider-value">{editPriority}</span>
              </div>
              <input type="range" min="1" max="100" bind:value={editPriority} />
            </div>
            <div class="flex gap-2 mt-2">
              <button class="small primary" onclick={() => saveConfig(editingSlug)}>Save</button>
              <button class="small secondary" onclick={cancelEdit}>Cancel</button>
            </div>
          
      </div>
    </div>
  </div>
{/if}

{#if showAdd}
  <div class="modal-overlay" onclick={() => showAdd = false}>
    <div class="modal" onclick={(e) => e.stopPropagation()}>
      <h2 class="mb-4">Add Custom Holiday</h2>
      <div class="form-group">
        <label>Name</label>
        <input type="text" bind:value={newName} placeholder="Holiday name" />
      </div>
      <div class="form-group">
        <label>Date (YYYY-MM-DD or MM-DD for recurring)</label>
        <input type="text" bind:value={newDate} placeholder="12-25" />
      </div>
      <div class="form-group">
        <label>Window Start</label>
        <input type="text" bind:value={newWindowStart} placeholder="Same as date if empty" />
      </div>
      <div class="form-group">
        <label>Window End</label>
        <input type="text" bind:value={newWindowEnd} placeholder="Same as date if empty" />
      </div>
      <div class="form-group">
        <label><input type="checkbox" bind:checked={newRecurring} /> Recurring yearly</label>
      </div>
      <div class="form-group">
        <label>Colors</label>
        <ColorPicker colors={newColors} onChange={(c) => newColors = c} />
        <button class="small secondary mt-1" onclick={suggestForNew} disabled={!newName}>Suggest Palette</button>
        {#if newSuggestions.length > 0}
          <div class="palette-suggestions">
            {#each newSuggestions as palette}
              <button class="palette-option" onclick={() => applyNewSuggestion(palette)}>
                {#each palette as color}
                  <span class="swatch" style="background: {color};"></span>
                {/each}
              </button>
            {/each}
          </div>
        {/if}
      </div>
      <div class="flex gap-2 mt-4" style="justify-content: flex-end;">
        <button class="secondary" onclick={() => showAdd = false}>Cancel</button>
        <button class="primary" onclick={addHoliday}>Add</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .holiday-card {
    position: relative;
    display: flex; flex-direction: column;
    min-height: 132px;
  }
  .holiday-card.active-holiday { border-color: var(--success); }
  .holiday-card.disabled-holiday { opacity: 0.5; }
  .holiday-date { font-size: 14px; color: var(--text-secondary); }
  .priority-badge { font-size: 11px; color: var(--text-muted); margin-left: 4px; }
  .holiday-window { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
  .holiday-colors-row {
    display: flex; align-items: center; justify-content: space-between;
    margin-top: auto; padding-top: var(--space-3); gap: var(--space-3);
  }
  /* Shown as one continuous strip — closer to how the rope lights read than
     separate dots, and far more legible than the old 10px circles. */
  .strip {
    display: flex; flex: 1; height: 26px;
    border-radius: 7px; overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }
  .strip-seg { flex: 1; }
  .no-colours { font-size: 12px; color: var(--text-muted); flex: 1; }
  .count {
    font-size: 11px; font-weight: 700; color: var(--text-muted);
    background: rgba(255,255,255,.06); padding: 1px 7px; border-radius: 999px;
  }
  .edit-btn { flex-shrink: 0; }
  .edit-panel {
    padding: 12px; background: var(--bg-input); border-radius: var(--radius);
    display: flex; flex-direction: column; gap: 12px;
    overflow: hidden;
  }
  .edit-section { display: flex; flex-direction: column; gap: 6px; }
  .edit-label { font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
  .window-slider { display: flex; flex-direction: column; gap: 4px; }
  .window-slider input[type="range"] { width: 100%; }
  .slider-header { display: flex; justify-content: space-between; font-size: 13px; color: var(--text-secondary); }
  .slider-value { color: var(--accent); font-weight: 600; }
  .window-preview { font-size: 12px; color: var(--accent); margin-top: 4px; }
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
    border-radius: 3px; border: 1px solid rgba(255,255,255,0.15);
  }
</style>
