<script>
  import ProviderStatus from '../components/ProviderStatus.svelte';
  import { api } from '../lib/api.js';
  import { toast } from '../lib/toast.js';
  import { addWSListener } from '../lib/websocket.js';

  let providers = $state([]);
  let loading = $state(true);
  let selectedProvider = $state(null);
  let webhookName = $state('test');
  let webhookPayload = $state('{\n  "key": "value"\n}');
  let showWebhookTest = $state(false);

  async function sendTestWebhook() {
    try {
      const payload = JSON.parse(webhookPayload);
      await api.sendWebhook(webhookName, payload);
      toast.success(`Webhook "${webhookName}" sent`);
    } catch (e) {
      toast.error('Webhook failed: ' + e.message);
    }
  }

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

  <div class="mt-4">
    <button class="secondary" onclick={() => showWebhookTest = !showWebhookTest}>
      {showWebhookTest ? 'Hide' : 'Test Webhook'}
    </button>
  </div>

  {#if showWebhookTest}
    <div class="card mt-2 webhook-test">
      <h3 class="mb-3">Send Test Webhook</h3>
      <div class="form-group">
        <label>Webhook Name</label>
        <input type="text" bind:value={webhookName} placeholder="e.g. motion" />
      </div>
      <div class="form-group">
        <label>JSON Payload</label>
        <textarea bind:value={webhookPayload} rows="4" class="json-editor"></textarea>
      </div>
      <button class="primary small" onclick={sendTestWebhook}>Send</button>
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
  .json-editor {
    font-family: monospace;
    font-size: 13px;
    width: 100%;
    background: var(--bg-input);
    color: var(--text-primary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 8px;
    resize: vertical;
  }
</style>
