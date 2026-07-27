<script>
  import { api } from '../lib/api.js';

  let logs = $state([]);
  let loading = $state(true);
  let levelFilter = $state('');
  let sourceFilter = $state('');
  let page = $state(0);
  let total = $state(0);

  const PAGE_SIZE = 100;
  let totalPages = $derived(Math.max(1, Math.ceil(total / PAGE_SIZE)));
  let hasMore = $derived(page < totalPages - 1);

  $effect(() => {
    loadLogs();
  });

  async function loadLogs() {
    loading = true;
    try {
      const params = { limit: String(PAGE_SIZE), offset: String(page * PAGE_SIZE) };
      if (levelFilter) params.level = levelFilter;
      if (sourceFilter) params.source = sourceFilter;
      const result = await api.getLogs(params);
      logs = result.items || result;
      total = result.total ?? logs.length;
    } catch (e) {
      console.error('Failed to load logs:', e);
    }
    loading = false;
  }

  function applyFilters() {
    page = 0;
    loadLogs();
  }

  function nextPage() {
    page++;
    loadLogs();
  }

  function prevPage() {
    if (page > 0) {
      page--;
      loadLogs();
    }
  }

  function levelClass(level) {
    if (level === 'error') return 'error';
    if (level === 'warning') return 'warning';
    return 'info';
  }

  async function refresh() {
    page = 0;
    await loadLogs();
  }
</script>

<div class="page-header">
  <h1>Logs</h1>
  <div class="flex gap-2">
    <select bind:value={levelFilter} onchange={applyFilters}>
      <option value="">All Levels</option>
      <option value="info">Info</option>
      <option value="warning">Warning</option>
      <option value="error">Error</option>
    </select>
    <input type="text" bind:value={sourceFilter} placeholder="Filter source..." style="width: 150px;"
      onkeydown={(e) => e.key === 'Enter' && applyFilters()} />
    <button class="secondary small" onclick={refresh}>Refresh</button>
  </div>
</div>

{#if loading}
  <p>Loading...</p>
{:else}
  <div class="log-container">
    <div class="table-wrap">
      <table>
      <thead>
        <tr>
          <th style="width: 170px;">Timestamp</th>
          <th style="width: 70px;">Level</th>
          <th style="width: 140px;">Source</th>
          <th>Message</th>
        </tr>
      </thead>
      <tbody>
        {#each logs as log (log.id)}
          <tr>
            <td style="font-size: 12px; font-family: monospace; white-space: nowrap;">
              {new Date(log.timestamp).toLocaleString()}
            </td>
            <td><span class="badge {levelClass(log.level)}">{log.level}</span></td>
            <td style="font-size: 13px;">{log.source}</td>
            <td style="font-size: 13px;">{log.message}</td>
          </tr>
        {/each}
      </tbody>
      </table>
    </div>

    {#if logs.length === 0}
      <div class="empty-state">No logs found.</div>
    {/if}
  </div>

  <div class="flex justify-between items-center mt-4">
    <button class="secondary small" onclick={prevPage} disabled={page === 0}>Previous</button>
    <span style="font-size: 13px; color: var(--text-muted);">Page {page + 1} of {totalPages} ({total} total)</span>
    <button class="secondary small" onclick={nextPage} disabled={!hasMore}>Next</button>
  </div>
{/if}

<style>
  .log-container {
    max-height: calc(100vh - 200px);
    overflow-y: auto;
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
  }
</style>
