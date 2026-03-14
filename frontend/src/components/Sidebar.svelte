<script>
  let { currentPage, onNavigate, bridgeConnected, setupComplete = false } = $props();

  const allNavItems = [
    { id: 'setup', label: 'Setup', icon: '🔧' },
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'rules', label: 'Rules', icon: '📋' },
    { id: 'lights', label: 'Lights', icon: '💡' },
    { id: 'providers', label: 'Providers', icon: '🔌' },
    { id: 'holidays', label: 'Holidays', icon: '🎄' },
    { id: 'logs', label: 'Logs', icon: '📜' },
  ];

  let navItems = $derived(
    setupComplete ? allNavItems.filter(i => i.id !== 'setup') : allNavItems
  );
</script>

<nav class="sidebar">
  <div class="sidebar-header">
    <h1 class="logo">Huey Do It</h1>
    <div class="connection-status" class:connected={bridgeConnected}>
      {bridgeConnected ? 'Bridge Connected' : 'Bridge Disconnected'}
    </div>
  </div>

  <ul class="nav-list">
    {#each navItems as item}
      <li>
        <button
          class="nav-item"
          class:active={currentPage === item.id}
          onclick={() => onNavigate(item.id)}
        >
          <span class="nav-icon">{item.icon}</span>
          <span class="nav-label">{item.label}</span>
        </button>
      </li>
    {/each}
  </ul>
</nav>

<style>
  .sidebar {
    width: 220px;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }
  .sidebar-header {
    padding: 20px 16px;
    border-bottom: 1px solid var(--border);
  }
  .logo {
    font-size: 20px;
    font-weight: 700;
    color: var(--accent);
  }
  .connection-status {
    margin-top: 8px;
    font-size: 12px;
    color: var(--error);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .connection-status::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--error);
  }
  .connection-status.connected {
    color: var(--success);
  }
  .connection-status.connected::before {
    background: var(--success);
  }
  .nav-list {
    list-style: none;
    padding: 8px;
  }
  .nav-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: var(--radius);
    background: transparent;
    color: var(--text-secondary);
    font-size: 14px;
    text-align: left;
    transition: all 0.15s;
  }
  .nav-item:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
  }
  .nav-item.active {
    background: var(--accent);
    color: white;
  }
  .nav-icon {
    font-size: 16px;
  }
</style>
