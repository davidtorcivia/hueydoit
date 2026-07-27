<script>
  import { api } from '../lib/api.js';
  import { toast } from '../lib/toast.js';
  import { addWSListener } from '../lib/websocket.js';

  let lights = $state([]);
  let bridgeLights = $state([]);
  let bridgeGroups = $state([]);
  let showBridge = $state(false);
  let loading = $state(true);
  let addingName = $state('');

  $effect(() => {
    loadLights();
    const unsub = addWSListener((event) => {
      if (event === 'light_state') loadLights();
    });
    return unsub;
  });

  async function loadLights() {
    try {
      lights = await api.getLights();
    } catch (e) {
      console.error('Failed to load lights:', e);
    }
    loading = false;
  }

  async function discoverBridge() {
    showBridge = true;
    try {
      const result = await api.getBridgeLights();
      bridgeLights = result.lights || [];
      bridgeGroups = result.groups || [];
    } catch (e) {
      toast.error('Failed to query bridge: ' + e.message);
      bridgeLights = [];
      bridgeGroups = [];
    }
  }

  async function addFromBridge(item, type) {
    const name = addingName || item.name.toLowerCase().replace(/\s+/g, '_');
    try {
      await api.addLight({
        name,
        type,
        hue_id: item.id,
        friendly_name: item.name,
      });
      addingName = '';
      await loadLights();
    } catch (e) {
      toast.error('Add failed: ' + e.message);
    }
  }

  async function removeLight(name) {
    if (!confirm(`Remove ${name}?`)) return;
    try {
      await api.removeLight(name);
      await loadLights();
    } catch (e) {
      console.error('Remove failed:', e);
    }
  }

  async function flashLight(name) {
    try {
      await api.testLight(name);
    } catch (e) {
      console.error('Flash failed:', e);
    }
  }
</script>

<div class="page-header">
  <h1>Lights</h1>
  <button class="primary" onclick={discoverBridge}>Add from Bridge</button>
</div>

{#if loading}
  <p>Loading...</p>
{:else if lights.length === 0}
  <div class="empty-state">
    <p>No lights configured. Add lights from your Hue bridge.</p>
    <button class="primary mt-4" onclick={discoverBridge}>Discover Lights</button>
  </div>
{:else}
  <div class="table-wrap">
    <table>
    <thead>
      <tr>
        <th>Name</th>
        <th>Friendly Name</th>
        <th>Type</th>
        <th>Hue ID</th>
        <th>Status</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {#each lights as light (light.name)}
        <tr>
          <td><strong>{light.name}</strong></td>
          <td>{light.friendly_name || '-'}</td>
          <td><span class="badge info">{light.type}</span></td>
          <td style="font-size: 12px; font-family: monospace;">{light.hue_id}</td>
          <td>
            {#if light.state}
              <span class="badge {light.state.on ? 'ok' : 'warning'}">
                {light.state.on ? 'ON' : 'OFF'}
              </span>
            {:else}
              <span class="badge warning">Unknown</span>
            {/if}
          </td>
          <td>
            <div class="flex gap-2">
              <button class="small secondary" onclick={() => flashLight(light.name)}>Flash</button>
              <button class="small ghost danger-text" onclick={() => removeLight(light.name)}>Remove</button>
            </div>
          </td>
        </tr>
      {/each}
    </tbody>
    </table>
  </div>
{/if}

{#if showBridge}
  <div class="modal-overlay" onclick={() => showBridge = false}>
    <div class="modal" onclick={(e) => e.stopPropagation()}>
      <h2 class="mb-4">Bridge Lights & Groups</h2>

      {#if bridgeLights.length === 0 && bridgeGroups.length === 0}
        <p style="color: var(--text-muted);">No lights found. Is the bridge connected?</p>
      {/if}

      {#if bridgeLights.length > 0}
        <h3 class="mb-2">Lights</h3>
        {#each bridgeLights as bl}
          <div class="bridge-item">
            <div>
              <strong>{bl.name}</strong>
              <span style="font-size: 12px; color: var(--text-muted);"> ({bl.id})</span>
            </div>
            <div class="flex gap-2 items-center">
              <input type="text" placeholder="target name" bind:value={addingName} style="width: 150px;" />
              <button class="small primary" onclick={() => addFromBridge(bl, 'light')}>Add</button>
            </div>
          </div>
        {/each}
      {/if}

      {#if bridgeGroups.length > 0}
        <h3 class="mb-2 mt-4">Groups / Zones</h3>
        {#each bridgeGroups as bg}
          <div class="bridge-item">
            <div>
              <strong>{bg.name}</strong>
              <span style="font-size: 12px; color: var(--text-muted);"> ({bg.id})</span>
            </div>
            <div class="flex gap-2 items-center">
              <input type="text" placeholder="target name" bind:value={addingName} style="width: 150px;" />
              <button class="small primary" onclick={() => addFromBridge(bg, 'grouped_light')}>Add</button>
            </div>
          </div>
        {/each}
      {/if}

      <div class="mt-4" style="text-align: right;">
        <button class="secondary" onclick={() => showBridge = false}>Close</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .bridge-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 0; border-bottom: 1px solid var(--border);
  }
</style>
