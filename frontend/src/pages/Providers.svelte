<script>
  import ProviderStatus from '../components/ProviderStatus.svelte';
  import { api } from '../lib/api.js';
  import { addWSListener } from '../lib/websocket.js';

  let providers = $state([]);
  let loading = $state(true);
  let selectedProvider = $state(null);

  $effect(() => {
    loadProviders();
    const unsub = addWSListener((event, data) => {
      if (event === 'provider_update') {
        const idx = providers.findIndex(p => p.name === data.name);
        if (idx >= 0) {
          providers[idx] = { ...providers[idx], current_state: data.state, is_stale: false };
          providers = [...providers];
        }
      }
    });
    return unsub;
  });

  async function loadProviders() {
    try {
      providers = await api.getProviders();
    } catch (e) {
      console.error('Failed to load providers:', e);
    }
    loading = false;
  }

  function showDetails(provider) {
    selectedProvider = selectedProvider?.name === provider.name ? null : provider;
  }
</script>

<div class="page-header">
  <h1>Providers</h1>
</div>

{#if loading}
  <p>Loading...</p>
{:else}
  <div class="grid grid-3 mb-4">
    {#each providers as provider (provider.name)}
      <div onclick={() => showDetails(provider)} style="cursor: pointer;">
        <ProviderStatus {provider} />
      </div>
    {/each}
  </div>

  {#if selectedProvider}
    <div class="card">
      <h3 class="mb-3">{selectedProvider.name} — Full State</h3>
      <pre class="state-dump">{JSON.stringify(selectedProvider.current_state, null, 2)}</pre>
      {#if selectedProvider.config && Object.keys(selectedProvider.config).length > 0}
        <h3 class="mb-2 mt-4">Config</h3>
        <pre class="state-dump">{JSON.stringify(selectedProvider.config, null, 2)}</pre>
      {/if}
    </div>
  {/if}
{/if}

<style>
  .state-dump {
    background: var(--bg-primary);
    padding: 12px;
    border-radius: var(--radius);
    font-size: 13px;
    color: var(--text-secondary);
    overflow-x: auto;
    max-height: 400px;
    overflow-y: auto;
  }
</style>
