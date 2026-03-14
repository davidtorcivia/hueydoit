<script>
  import RuleEditor from '../components/RuleEditor.svelte';
  import RuleTester from '../components/RuleTester.svelte';
  import { api } from '../lib/api.js';
  import { toast } from '../lib/toast.js';
  import { addWSListener } from '../lib/websocket.js';
  import { ruleTemplates } from '../lib/ruleTemplates.js';

  let rules = $state([]);
  let targets = $state([]);
  let showEditor = $state(false);
  let editingRule = $state(null);
  let loading = $state(true);
  let dragIdx = $state(-1);
  let showTemplates = $state(false);

  $effect(() => {
    loadData();
    const unsub = addWSListener((event) => {
      if (event === 'rule_activated') loadData();
    });
    return unsub;
  });

  async function loadData() {
    try {
      const [r, l] = await Promise.all([api.getRules(), api.getLights()]);
      rules = r;
      targets = l;
    } catch (e) {
      console.error('Failed to load rules:', e);
    }
    loading = false;
  }

  function openCreate() {
    editingRule = null;
    showEditor = true;
  }

  function openEdit(rule) {
    editingRule = rule;
    showEditor = true;
  }

  function cloneRule(rule) {
    // $state proxies can't be structuredCloned — serialize to plain object
    const plain = JSON.parse(JSON.stringify(rule));
    plain.id = undefined;
    plain.name = plain.name + ' (copy)';
    // Close and reopen to force full component recreation
    showEditor = false;
    editingRule = plain;
    requestAnimationFrame(() => { showEditor = true; });
  }

  function useTemplate(template) {
    editingRule = { ...structuredClone(template.rule), _isTemplate: true };
    showTemplates = false;
    showEditor = true;
  }

  async function handleSave(data) {
    try {
      if (editingRule && editingRule.id) {
        await api.updateRule(editingRule.id, data);
      } else {
        await api.createRule(data);
      }
      showEditor = false;
      await loadData();
      toast.success('Rule saved');
    } catch (e) {
      toast.error('Save failed: ' + e.message);
    }
  }

  async function handleDelete(id) {
    if (!confirm('Delete this rule?')) return;
    try {
      await api.deleteRule(id);
      await loadData();
    } catch (e) {
      console.error('Delete failed:', e);
    }
  }

  async function handleTrigger(rule) {
    try {
      const result = await api.triggerRule(rule.id);
      toast.success(`Triggered "${rule.name}" on ${result.targets_applied.length} lights`);
    } catch (e) {
      toast.error('Trigger failed: ' + e.message);
    }
  }

  async function handleToggle(rule) {
    try {
      await api.updateRule(rule.id, { enabled: !rule.enabled });
      await loadData();
    } catch (e) {
      console.error('Toggle failed:', e);
    }
  }

  function onDragStart(idx) {
    dragIdx = idx;
  }

  async function onDrop(targetIdx) {
    if (dragIdx === -1 || dragIdx === targetIdx) return;
    const reordered = [...rules];
    const [moved] = reordered.splice(dragIdx, 1);
    reordered.splice(targetIdx, 0, moved);
    rules = reordered;
    dragIdx = -1;

    const updates = reordered.map((r, i) => ({ id: r.id, priority: (i + 1) * 10 }));
    try {
      await api.reorderRules(updates);
      await loadData();
    } catch (e) {
      console.error('Reorder failed:', e);
    }
  }

  function formatHour(h) {
    if (h === 0) return '12 AM';
    if (h < 12) return h + ' AM';
    if (h === 12) return '12 PM';
    return (h - 12) + ' PM';
  }

  const dayNames = { monday: 'Mon', tuesday: 'Tue', wednesday: 'Wed', thursday: 'Thu', friday: 'Fri', saturday: 'Sat', sunday: 'Sun' };

  function singleCondSummary(c) {
    if (c.match === 'always') return 'Always';
    const p = c.provider;
    const m = c.match;
    if (!m || typeof m !== 'object') return p || '?';

    if (p === 'time') {
      if (m.hour_range) return `${formatHour(m.hour_range.start)} – ${formatHour(m.hour_range.end)}`;
      if (m.hour && typeof m.hour === 'object') return `After ${formatHour(m.hour.gte ?? m.hour.gt ?? 0)}`;
      if (m.is_weekend === true) return 'Weekends';
      if (m.is_weekend === false) return 'Weekdays';
      if (m.day_of_week) return dayNames[m.day_of_week] || m.day_of_week;
    }
    if (p === 'holiday') {
      if (m.active_holiday && typeof m.active_holiday === 'object') return 'Any holiday';
      if (m.active_holiday) return `Holiday: ${m.active_holiday}`;
    }
    if (p === 'solar') {
      if (m.period === 'day') return 'Daytime';
      if (m.phase === 'before_sunrise') return 'Before sunrise';
      if (m.period === 'night') return 'After sunset';
      return m.period || m.phase || 'Solar';
    }
    if (p === 'weather') {
      if (m.temp_f) {
        const op = Object.keys(m.temp_f)[0];
        return `Temp ${op === 'gte' || op === 'gt' ? '>' : '<'} ${m.temp_f[op]}°F`;
      }
      if (m.condition) return `Weather: ${m.condition}`;
      if (m.humidity) {
        const op = Object.keys(m.humidity)[0];
        return `Humidity ${op === 'gte' || op === 'gt' ? '>' : '<'} ${m.humidity[op]}%`;
      }
    }
    if (p === 'calendar') {
      if (m.season) return m.season.charAt(0).toUpperCase() + m.season.slice(1);
      const monthNames = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      if (m.month) return monthNames[m.month] || `Month ${m.month}`;
      if (m.month_name) return m.month_name.charAt(0).toUpperCase() + m.month_name.slice(1);
      if (m.date_range) {
        const s = m.date_range.start, e = m.date_range.end;
        if (s === '03-20' && e === '06-20') return 'Spring';
        if (s === '06-21' && e === '09-21') return 'Summer';
        if (s === '09-22' && e === '12-20') return 'Fall';
        if (s === '12-21' && e === '03-19') return 'Winter';
        return `${s} – ${e}`;
      }
      return 'Calendar';
    }
    if (p === 'webhook') {
      const k = Object.keys(m)[0];
      return k ? `Webhook: ${k}=${m[k]}` : 'Webhook';
    }
    return p || '?';
  }

  function conditionSummary(config) {
    if (!config?.condition) return '?';
    const c = config.condition;
    if (c.match === 'always') return 'Always';
    if (c.all_of) return c.all_of.map(singleCondSummary).join(' + ');
    if (c.any_of) return c.any_of.map(singleCondSummary).join(' | ');
    return singleCondSummary(c);
  }
</script>

<div class="page-header">
  <h1>Rules</h1>
  <div class="flex gap-2">
    <button class="secondary" onclick={() => showTemplates = !showTemplates}>
      Quick Start
    </button>
    <button class="primary" onclick={openCreate}>+ Create Rule</button>
  </div>
</div>

{#if showTemplates}
  <div class="template-grid mb-4">
    {#each ruleTemplates as t}
      <button class="template-card" onclick={() => useTemplate(t)}>
        <span class="template-icon">{t.icon}</span>
        <strong>{t.name}</strong>
        <span class="template-desc">{t.description}</span>
      </button>
    {/each}
  </div>
{/if}

{#if loading}
  <p>Loading...</p>
{:else if rules.length === 0}
  <div class="empty-state">
    <p>No rules configured yet.</p>
    <div class="flex gap-2 mt-4" style="justify-content: center;">
      <button class="secondary" onclick={() => showTemplates = true}>Use a Template</button>
      <button class="primary" onclick={openCreate}>Create from scratch</button>
    </div>
  </div>
{:else}
  <table>
    <thead>
      <tr>
        <th style="width: 40px;"></th>
        <th>Priority</th>
        <th>Name</th>
        <th>Condition</th>
        <th>Effect</th>
        <th>Targets</th>
        <th>Enabled</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {#each rules as rule, i (rule.id)}
        <tr
          draggable="true"
          ondragstart={() => onDragStart(i)}
          ondragover={(e) => e.preventDefault()}
          ondrop={() => onDrop(i)}
          style="opacity: {rule.enabled ? 1 : 0.5}"
        >
          <td style="cursor: grab;">&#x2630;</td>
          <td>{rule.priority}</td>
          <td><strong>{rule.name}</strong></td>
          <td style="font-size: 13px;">{conditionSummary(rule.config)}</td>
          <td>
            <span class="badge info">{rule.config?.effect?.mode || '?'}</span>
            {#if rule.config?.effect?.use_holiday_colors}
              <span class="badge ok" title="Uses active holiday palette">auto</span>
            {/if}
            {#if rule.config?.effect?.colors}
              {#each rule.config.effect.colors.slice(0, 3) as color}
                <span class="color-dot" style="background: {color};"></span>
              {/each}
            {/if}
          </td>
          <td style="font-size: 13px;">{rule.config?.targets?.join(', ') || '-'}</td>
          <td>
            <div class="toggle" class:active={rule.enabled} onclick={() => handleToggle(rule)}></div>
          </td>
          <td>
            <div class="flex gap-2">
              <button class="small primary" onclick={() => handleTrigger(rule)}>Run</button>
              <button class="small secondary" onclick={() => openEdit(rule)}>Edit</button>
              <button class="small secondary" onclick={() => cloneRule(rule)}>Clone</button>
              <button class="small danger" onclick={() => handleDelete(rule.id)}>Del</button>
            </div>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>

  <div class="mt-4">
    <RuleTester />
  </div>
{/if}

{#if showEditor}
  {#key editingRule}
    <RuleEditor
      rule={editingRule}
      {targets}
      onSave={handleSave}
      onCancel={() => showEditor = false}
    />
  {/key}
{/if}

<style>
  .template-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
  }
  .template-card {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
    padding: 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    cursor: pointer;
    text-align: left;
    transition: border-color 0.15s, background 0.15s;
    color: var(--text-primary);
  }
  .template-card:hover {
    border-color: var(--accent);
    background: rgba(255, 255, 255, 0.03);
  }
  .template-icon { font-size: 24px; margin-bottom: 4px; }
  .template-desc { font-size: 12px; color: var(--text-secondary); }
</style>
