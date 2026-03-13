<script>
  import Sidebar from './components/Sidebar.svelte';
  import Setup from './pages/Setup.svelte';
  import Dashboard from './pages/Dashboard.svelte';
  import Rules from './pages/Rules.svelte';
  import Lights from './pages/Lights.svelte';
  import Providers from './pages/Providers.svelte';
  import Holidays from './pages/Holidays.svelte';
  import Logs from './pages/Logs.svelte';
  import { connectWS, addWSListener } from './lib/websocket.js';
  import { api } from './lib/api.js';

  let currentPage = $state('dashboard');
  let bridgeConnected = $state(false);
  let wsConnected = $state(false);

  $effect(() => {
    connectWS();
    loadBridgeStatus();

    const unsub = addWSListener((event, data) => {
      if (event === '_connected') wsConnected = true;
      if (event === '_disconnected') wsConnected = false;
    });

    // Listen for navigation events from Setup wizard
    function handleNav(e) { navigate(e.detail); }
    window.addEventListener('navigate', handleNav);

    return () => { unsub(); window.removeEventListener('navigate', handleNav); };
  });

  async function loadBridgeStatus() {
    try {
      const status = await api.getBridgeStatus();
      bridgeConnected = status.connected;
      if (!status.paired) {
        currentPage = 'setup';
      }
    } catch {
      bridgeConnected = false;
      currentPage = 'setup';
    }
  }

  function navigate(page) {
    currentPage = page;
  }
</script>

<Sidebar {currentPage} onNavigate={navigate} {bridgeConnected} />

<main class="page">
  {#if currentPage === 'setup'}
    <Setup />
  {:else if currentPage === 'dashboard'}
    <Dashboard />
  {:else if currentPage === 'rules'}
    <Rules />
  {:else if currentPage === 'lights'}
    <Lights />
  {:else if currentPage === 'providers'}
    <Providers />
  {:else if currentPage === 'holidays'}
    <Holidays />
  {:else if currentPage === 'logs'}
    <Logs />
  {/if}
</main>
