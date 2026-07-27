<script>
  let { currentPage, onNavigate, bridgeConnected, setupComplete = false } = $props();

  // Inline stroke icons — emoji rendered inconsistently across platforms and
  // couldn't take the active-state colour.
  const ICONS = {
    setup: 'M10.3 4.3a4 4 0 0 0 5.4 5.4l3.6 3.6a2 2 0 1 1-2.8 2.8l-3.6-3.6a4 4 0 0 0-5.4-5.4l2.2 2.2-1.4 1.4-2.2-2.2Z',
    dashboard: 'M4 13h6V4H4v9Zm0 7h6v-5H4v5Zm10 0h6V11h-6v9Zm0-16v5h6V4h-6Z',
    rules: 'M5 4h14a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Zm3 4h8M8 12h8M8 16h5',
    lights: 'M9 21h6m-5 3h4M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2Z',
    providers: 'M12 3v6m0 6v6M5.6 5.6l4.2 4.2m4.4 4.4 4.2 4.2M3 12h6m6 0h6M5.6 18.4l4.2-4.2m4.4-4.4 4.2-4.2',
    holidays: 'M12 2 7 9h3l-4 6h4l-3 5h10l-3-5h4l-4-6h3Z',
    logs: 'M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Zm8 1v5h5M8 13h8M8 17h5',
  };

  const FILLED = new Set(['dashboard', 'holidays']);

  const allNavItems = [
    { id: 'setup', label: 'Setup' },
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'rules', label: 'Rules' },
    { id: 'lights', label: 'Lights' },
    { id: 'providers', label: 'Providers' },
    { id: 'holidays', label: 'Holidays' },
    { id: 'logs', label: 'Logs' },
  ];

  let navItems = $derived(
    setupComplete ? allNavItems.filter((i) => i.id !== 'setup') : allNavItems
  );
</script>

<nav class="sidebar" aria-label="Main">
  <div class="sidebar-header">
    <span class="logo">Huey Do It</span>
    <div class="connection-status" class:connected={bridgeConnected}>
      {bridgeConnected ? 'Bridge connected' : 'Bridge disconnected'}
    </div>
  </div>

  <ul class="nav-list">
    {#each navItems as item}
      <li>
        <button
          class="nav-item"
          class:active={currentPage === item.id}
          onclick={() => onNavigate(item.id)}
          aria-current={currentPage === item.id ? 'page' : undefined}
        >
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"
            fill={FILLED.has(item.id) ? 'currentColor' : 'none'}
            stroke="currentColor" stroke-width="1.7"
            stroke-linecap="round" stroke-linejoin="round">
            <path d={ICONS[item.id]} />
          </svg>
          <span>{item.label}</span>
        </button>
      </li>
    {/each}
  </ul>
</nav>

<style>
  .sidebar {
    width: 216px;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }
  .sidebar-header {
    padding: var(--space-5) var(--space-4) var(--space-4);
    border-bottom: 1px solid var(--border);
  }
  .logo {
    font-size: 17px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-primary);
  }
  .connection-status {
    margin-top: var(--space-2);
    font-size: 12px;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .connection-status::before {
    content: '';
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--error);
    box-shadow: 0 0 0 3px rgba(242, 85, 90, 0.15);
  }
  .connection-status.connected::before {
    background: var(--success);
    box-shadow: 0 0 0 3px rgba(52, 208, 127, 0.15);
  }

  .nav-list { list-style: none; padding: var(--space-3) var(--space-2); }
  .nav-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 9px 11px;
    border-radius: var(--radius);
    background: transparent;
    color: var(--text-secondary);
    font-size: 14px;
    font-weight: 500;
    text-align: left;
    transition: background .15s, color .15s;
  }
  .nav-item:hover { background: rgba(255, 255, 255, 0.05); color: var(--text-primary); }
  .nav-item.active { background: var(--accent-soft); color: var(--accent); font-weight: 600; }
  .nav-icon { width: 18px; height: 18px; flex-shrink: 0; }

  @media (max-width: 860px) {
    .sidebar {
      width: 100%;
      border-right: none;
      border-bottom: 1px solid var(--border);
    }
    .nav-list { display: flex; flex-wrap: wrap; gap: var(--space-1); }
    .nav-item { width: auto; }
  }
</style>
