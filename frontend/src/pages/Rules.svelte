<script>
  import RuleEditor from '../components/RuleEditor.svelte';
  import RuleTester from '../components/RuleTester.svelte';
  import { api } from '../lib/api.js';
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
    } catch (e) {
      alert('Save failed: ' + e.message);
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

  function conditionSummary(config) {
    if (!config?.condition) return '?';
    const c = config.condition;
    if (c.match === 'always') return 'Always';
    const provider = c.provider || '';
    const match = c.match;
    if (typeof match === 'object' && match) {
      const parts = Object.entries(match).map(([k, v]) => {
        if (typeof v === 'object' && v) {
          const op = Object.keys(v)[0];
          return `${k} ${op} ${v[op]}`;
        }
        return `${k} = ${v}`;
      });
      return `${provider}: ${parts.join(', ')}`;
    }
    return provider || '?';
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
              <button class="small secondary" onclick={() => openEdit(rule)}>Edit</button>
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
  <RuleEditor
    rule={editingRule}
    {targets}
    onSave={handleSave}
    onCancel={() => showEditor = false}
  />
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
