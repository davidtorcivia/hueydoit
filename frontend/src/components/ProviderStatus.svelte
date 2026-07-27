<script>
  import { api } from '../lib/api.js';

  let { provider } = $props();

  let refreshing = $state(false);

  let statusClass = $derived(
    provider.error ? 'error' : provider.is_stale ? 'warning' : 'ok'
  );
  let statusText = $derived(
    provider.error ? 'Error' : provider.is_stale ? 'Stale' : 'OK'
  );

  function formatState(state) {
    if (!state) return 'No data';
    const keys = Object.keys(state);
    if (keys.length === 0) return 'Empty';
    const highlights = [];
    if (state.temp_f !== undefined) highlights.push(`${state.temp_f}°F`);
    if (state.condition) highlights.push(state.condition);
    if (state.period) highlights.push(state.period);
    if (state.active_holiday) highlights.push(state.active_holiday);
    if (state.hour !== undefined) highlights.push(`${String(state.hour).padStart(2,'0')}:${String(state.minute).padStart(2,'0')}`);
    if (highlights.length > 0) return highlights.join(' · ');
    return `${keys.length} fields`;
  }

  async function refresh() {
    refreshing = true;
    try {
      await api.refreshProvider(provider.name);
    } catch (e) {
      console.error('Refresh failed:', e);
    }
    refreshing = false;
  }

  function formatTtl(seconds) {
    if (!seconds) return '—';
    if (seconds >= 86400) return `${Math.round(seconds / 86400)}d`;
    if (seconds >= 3600) return `${Math.round(seconds / 3600)}h`;
    return `${Math.round(seconds / 60)}m`;
  }
</script>

<div class="card provider-card">
  <div class="provider-header">
    <h3>{provider.name}</h3>
    <span class="badge {statusClass}">{statusText}</span>
  </div>

  <div class="provider-summary">{formatState(provider.current_state)}</div>

  {#if provider.error}
    <div class="provider-error">{provider.error}</div>
  {/if}

  <div class="provider-meta">
    <span>TTL: {formatTtl(provider.ttl_seconds)}</span>
    {#if provider.last_fetch}
      <span>Last: {new Date(provider.last_fetch).toLocaleTimeString()}</span>
    {/if}
  </div>

  <button class="small secondary" onclick={refresh} disabled={refreshing}>
    {refreshing ? 'Refreshing...' : 'Refresh Now'}
  </button>
</div>

<style>
  .provider-card { display: flex; flex-direction: column; gap: 8px; }
  .provider-header { display: flex; justify-content: space-between; align-items: center; }
  .provider-summary { font-size: 14px; color: var(--text-secondary); }
  .provider-error { font-size: 12px; color: var(--error); }
  .provider-meta { font-size: 12px; color: var(--text-muted); display: flex; gap: 12px; }
</style>
