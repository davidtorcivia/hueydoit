<script>
  import { api } from '../lib/api.js';
  import SingleCondition from './SingleCondition.svelte';

  let { condition = {}, onChange } = $props();

  let condAlways = $state(condition?.match === 'always');
  let innerOp = $state('all'); // operator WITHIN groups
  let groups = $state([]);       // array of arrays of conditions
  let groupKeys = $state([]);    // parallel arrays of keys for Svelte keying
  let groupIdKeys = $state([]);  // unique key per group
  let nextKey = $state(0);
  let showAdvanced = $state(false);
  let advancedJson = $state('');

  let outerOp = $derived(innerOp === 'all' ? 'any' : 'all');
  let outerLabel = $derived(innerOp === 'all' ? 'OR' : 'AND');
  let innerLabel = $derived(innerOp === 'all' ? 'AND' : 'OR');

  let holidays = $state([]);
  $effect(() => {
    api.getHolidays().then(h => holidays = h).catch(() => {});
  });

  // Parse initial condition
  function parseConditions(cond) {
    if (!cond || cond.match === 'always') return;

    // Nested: any_of containing all_of groups (or vice versa)
    if (cond.any_of && cond.any_of.some(c => c.all_of)) {
      innerOp = 'all';
      for (const sub of cond.any_of) {
        if (sub.all_of) {
          addGroupWith(sub.all_of);
        } else {
          addGroupWith([sub]);
        }
      }
      return;
    }
    if (cond.all_of && cond.all_of.some(c => c.any_of)) {
      innerOp = 'any';
      for (const sub of cond.all_of) {
        if (sub.any_of) {
          addGroupWith(sub.any_of);
        } else {
          addGroupWith([sub]);
        }
      }
      return;
    }

    // Flat all_of / any_of → single group
    if (cond.all_of) {
      innerOp = 'all';
      addGroupWith(cond.all_of);
      return;
    }
    if (cond.any_of) {
      innerOp = 'any';
      addGroupWith(cond.any_of);
      return;
    }

    // Single condition
    if (cond.provider) {
      addGroupWith([cond]);
      return;
    }

    // Default empty
    addGroupWith([{}]);
  }

  function addGroupWith(conds) {
    const gk = conds.map(() => nextKey++);
    groups = [...groups, [...conds]];
    groupKeys = [...groupKeys, gk];
    groupIdKeys = [...groupIdKeys, nextKey++];
  }

  parseConditions(condition);
  if (groups.length === 0) addGroupWith([{}]);

  // Hysteresis keys the visual builder doesn't model. Rebuilding the condition
  // from the groups alone would drop them, so a rule saved from the UI would
  // quietly lose its anti-flap settings. Edit them in advanced JSON.
  const extras = {};
  for (const key of ['for', 'deadband']) {
    if (condition?.[key] !== undefined) extras[key] = condition[key];
  }

  function addConditionToGroup(gi) {
    groups[gi] = [...groups[gi], {}];
    groupKeys[gi] = [...groupKeys[gi], nextKey++];
    groups = [...groups];
    groupKeys = [...groupKeys];
  }

  function removeConditionFromGroup(gi, ci) {
    groups[gi] = groups[gi].filter((_, i) => i !== ci);
    groupKeys[gi] = groupKeys[gi].filter((_, i) => i !== ci);
    if (groups[gi].length === 0) {
      // Remove empty group
      groups = groups.filter((_, i) => i !== gi);
      groupKeys = groupKeys.filter((_, i) => i !== gi);
      groupIdKeys = groupIdKeys.filter((_, i) => i !== gi);
    }
    if (groups.length === 0) addGroupWith([{}]);
    groups = [...groups];
    groupKeys = [...groupKeys];
    emitChange();
  }

  function updateConditionInGroup(gi, ci, newCond) {
    groups[gi][ci] = newCond;
    groups = [...groups];
    emitChange();
  }

  function addGroup() {
    addGroupWith([{}]);
    groups = [...groups];
    groupKeys = [...groupKeys];
  }

  function setInnerOp(op) {
    innerOp = op;
    emitChange();
  }

  function buildCondition() {
    if (condAlways) return { ...extras, match: 'always' };
    if (showAdvanced) {
      try { return JSON.parse(advancedJson); } catch { return condition; }
    }

    // Flatten groups
    const builtGroups = groups.map(g => g.filter(c => c.provider));

    // Remove empty groups
    const validGroups = builtGroups.filter(g => g.length > 0);
    if (validGroups.length === 0) return condition;

    // Single group
    if (validGroups.length === 1) {
      const g = validGroups[0];
      if (g.length === 1) return { ...extras, ...g[0] };
      return { ...extras, [`${innerOp}_of`]: g };
    }

    // Multiple groups: wrap each group, then combine with outer op
    const wrapped = validGroups.map(g => {
      if (g.length === 1) return g[0];
      return { [`${innerOp}_of`]: g };
    });
    return { ...extras, [`${outerOp}_of`]: wrapped };
  }

  function emitChange() {
    onChange(buildCondition());
  }

  $effect(() => {
    if (showAdvanced) {
      advancedJson = JSON.stringify(buildCondition(), null, 2);
    }
  });
</script>

<div class="condition-builder">
  <div class="form-group">
    <label>
      <input type="checkbox" bind:checked={condAlways} onchange={emitChange} /> Always match (catch-all)
    </label>
  </div>

  {#if !condAlways}
    {#each groups as group, gi (groupIdKeys[gi])}
      {#if gi > 0}
        <div class="group-separator">
          <span class="group-sep-line"></span>
          <span class="group-sep-label">{outerLabel}</span>
          <span class="group-sep-line"></span>
        </div>
      {/if}

      <div class="condition-group" class:multi-group={groups.length > 1}>
        {#each group as cond, ci (groupKeys[gi][ci])}
          {#if ci > 0}
            <div class="operator-row">
              <button class="operator-btn" class:active={innerOp === 'all'} onclick={() => setInnerOp('all')}>AND</button>
              <button class="operator-btn" class:active={innerOp === 'any'} onclick={() => setInnerOp('any')}>OR</button>
            </div>
          {/if}
          <SingleCondition
            condition={cond}
            {holidays}
            onChange={(c) => updateConditionInGroup(gi, ci, c)}
            onRemove={(group.length > 1 || groups.length > 1) ? () => removeConditionFromGroup(gi, ci) : null}
          />
        {/each}
        <button class="add-condition-btn" onclick={() => addConditionToGroup(gi)}>+ Add Condition</button>
      </div>
    {/each}

    <button class="add-group-btn" onclick={addGroup}>+ Add Group</button>

    <div class="advanced-toggle">
      <label>
        <input type="checkbox" bind:checked={showAdvanced} /> Advanced (raw JSON)
      </label>
    </div>

    {#if showAdvanced}
      <div class="form-group">
        <textarea
          bind:value={advancedJson}
          oninput={() => { try { onChange(JSON.parse(advancedJson)); } catch {} }}
          rows="6"
          class="json-editor"
        ></textarea>
      </div>
    {/if}
  {/if}
</div>

<style>
  .condition-builder { display: flex; flex-direction: column; gap: 4px; }
  .condition-group { display: flex; flex-direction: column; gap: 0; }
  .condition-group.multi-group {
    padding: 10px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: rgba(255, 255, 255, 0.02);
  }
  .group-separator {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 0;
  }
  .group-sep-line { flex: 1; height: 1px; background: var(--border-light); }
  .group-sep-label {
    font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
    color: var(--accent); padding: 2px 10px;
    border: 1px solid var(--accent); border-radius: 4px;
    background: rgba(79, 134, 247, 0.1);
  }
  .operator-row {
    display: flex; justify-content: center; gap: 2px; padding: 6px 0;
  }
  .operator-btn {
    padding: 3px 14px; font-size: 11px; font-weight: 700;
    letter-spacing: 0.5px; background: var(--bg-input);
    color: var(--text-muted); border: 1px solid var(--border);
    cursor: pointer; transition: all 0.15s;
  }
  .operator-btn:first-child { border-radius: 4px 0 0 4px; }
  .operator-btn:last-child { border-radius: 0 4px 4px 0; }
  .operator-btn.active {
    background: var(--accent); color: white; border-color: var(--accent);
  }
  .add-condition-btn {
    align-self: flex-start; margin-top: 6px;
    padding: 5px 14px; font-size: 13px;
    background: transparent; color: var(--accent);
    border: 1px dashed var(--border); border-radius: var(--radius);
    cursor: pointer; transition: all 0.15s;
  }
  .add-condition-btn:hover {
    border-color: var(--accent); background: rgba(79, 134, 247, 0.1);
  }
  .add-group-btn {
    align-self: flex-start; margin-top: 8px;
    padding: 5px 14px; font-size: 13px;
    background: transparent; color: var(--text-secondary);
    border: 1px dashed var(--border-light); border-radius: var(--radius);
    cursor: pointer; transition: all 0.15s;
  }
  .add-group-btn:hover {
    border-color: var(--accent); color: var(--accent);
    background: rgba(79, 134, 247, 0.05);
  }
  .advanced-toggle {
    font-size: 13px; color: var(--text-secondary); margin-top: 4px;
  }
  .advanced-toggle label {
    display: flex; align-items: center; gap: 8px; cursor: pointer;
  }
  .json-editor {
    font-family: monospace; font-size: 13px; width: 100%;
    background: var(--bg-input); color: var(--text-primary);
    border: 1px solid var(--border); border-radius: var(--radius);
    padding: 8px; resize: vertical;
  }
</style>
