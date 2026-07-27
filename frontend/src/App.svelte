<script>
  import Sidebar from './components/Sidebar.svelte';
  import Toast from './components/Toast.svelte';
  import Setup from './pages/Setup.svelte';
  import Dashboard from './pages/Dashboard.svelte';
  import Rules from './pages/Rules.svelte';
  import Lights from './pages/Lights.svelte';
  import Providers from './pages/Providers.svelte';
  import Holidays from './pages/Holidays.svelte';
  import Logs from './pages/Logs.svelte';
  import { connectWS, addWSListener } from './lib/websocket.js';
  import { api } from './lib/api.js';

  const PAGES = ['dashboard', 'rules', 'lights', 'providers', 'holidays', 'logs', 'setup'];

  function pageFromHash() {
    const h = window.location.hash.replace(/^#\/?/, '');
    return PAGES.includes(h) ? h : 'dashboard';
  }

  // Page was state-only, so a refresh always dropped you back on the dashboard
  // and the back button did nothing. Mirror it into the URL hash.
  let currentPage = $state(pageFromHash());
  let bridgeConnected = $state(false);
  let wsConnected = $state(false);
  let setupComplete = $state(false);

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

    function handleHash() {
      const p = pageFromHash();
      if (p !== currentPage) currentPage = p;
    }
    window.addEventListener('hashchange', handleHash);

    return () => {
      unsub();
      window.removeEventListener('navigate', handleNav);
      window.removeEventListener('hashchange', handleHash);
    };
  });

  async function loadBridgeStatus() {
    try {
      const status = await api.getBridgeStatus();
      bridgeConnected = status.connected;
      if (!status.paired) {
        navigate('setup');
        return;
      }
      const lights = await api.getLights();
      setupComplete = lights.length > 0;
      if (!setupComplete) {
        navigate('setup');
      }
    } catch {
      bridgeConnected = false;
      navigate('setup');
    }
  }

  function navigate(page) {
    currentPage = page;
    const target = `#/${page}`;
    if (window.location.hash !== target) window.location.hash = target;
  }
</script>

<Toast />
<Sidebar {currentPage} onNavigate={navigate} {bridgeConnected} {setupComplete} />

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
