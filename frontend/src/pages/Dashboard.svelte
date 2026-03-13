<script>
  import LightCard from '../components/LightCard.svelte';
  import ProviderStatus from '../components/ProviderStatus.svelte';
  import { api } from '../lib/api.js';
  import { addWSListener } from '../lib/websocket.js';

  let lights = $state([]);
  let providers = $state([]);
  let loading = $state(true);
  let pairMessage = $state('');

  $effect(() => {
    loadStatus();
    const unsub = addWSListener((event, data) => {
      if (event === 'light_state') {
        const idx = lights.findIndex(l => l.name === data.target);
        if (idx >= 0) {
          lights[idx] = { ...lights[idx], state: data.state };
          lights = [...lights];
        }
      }
      if (event === 'provider_update') {
        const idx = providers.findIndex(p => p.name === data.name);
        if (idx >= 0) {
          providers[idx] = { ...providers[idx], current_state: data.state, is_stale: data.stale };
          providers = [...providers];
        }
      }
      if (event === 'override_created' || event === 'override_cleared') {
        loadStatus();
      }
    });
    return unsub;
  });

  async function loadStatus() {
    try {
      const status = await api.getStatus();
      lights = status.lights || [];
      providers = status.providers || [];
    } catch (e) {
      console.error('Failed to load status:', e);
    }
    loading = false;
  }

  async function handleOverride(target, override) {
    try {
      await api.setOverride(target, override);
      await loadStatus();
    } catch (e) {
      console.error('Override failed:', e);
    }
  }

  async function handleClearOverride(target) {
    try {
      await api.clearOverride(target);
      await loadStatus();
    } catch (e) {
      console.error('Clear override failed:', e);
    }
  }

  async function pairBridge() {
    pairMessage = 'Pairing...';
    try {
      await api.pairBridge();
      pairMessage = 'Paired successfully!';
      await loadStatus();
    } catch (e) {
      pairMessage = e.message;
    }
  }
</script>

<div class="page-header">
  <h1>Dashboard</h1>
</div>

{#if loading}
  <p>Loading...</p>
{:else}
  {#if lights.length === 0}
    <div class="card mb-4">
      <h3>Getting Started</h3>
      <p class="mt-2" style="color: var(--text-secondary);">
        No lights configured yet. First, pair your Hue bridge, then add lights from the Lights page.
      </p>
      <button class="primary mt-2" onclick={pairBridge}>Pair Hue Bridge</button>
      {#if pairMessage}
        <p class="mt-2" style="font-size: 13px;">{pairMessage}</p>
      {/if}
    </div>
  {/if}

  {#if lights.length > 0}
    <h2 class="mb-3">Lights</h2>
    <div class="grid grid-3 mb-4">
      {#each lights as light (light.name)}
        <LightCard {light} onOverride={handleOverride} onClearOverride={handleClearOverride} />
      {/each}
    </div>
  {/if}

  <h2 class="mb-3">Providers</h2>
  <div class="grid grid-3">
    {#each providers as provider (provider.name)}
      <ProviderStatus {provider} />
    {/each}
  </div>
{/if}
