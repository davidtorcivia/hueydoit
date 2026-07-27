<script>
  import { bulbPreview } from '../lib/color.js';
  import LightCard from '../components/LightCard.svelte';
  import ProviderStatus from '../components/ProviderStatus.svelte';
  import { api } from '../lib/api.js';
  import { addWSListener } from '../lib/websocket.js';

  let lights = $state([]);
  let providers = $state([]);
  let loading = $state(true);
  let pairMessage = $state('');
  let nextTrigger = $state(null);
  let upcomingHolidays = $state([]);

  $effect(() => {
    loadStatus();
    loadNextTrigger();
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
      if (event === 'rule_activated' || event === 'override_created' || event === 'override_cleared') {
        loadStatus();
        loadNextTrigger();
      }
    });
    // Refresh predictions every 60s
    loadUpcomingHolidays();
    const interval = setInterval(() => { loadNextTrigger(); loadUpcomingHolidays(); }, 60000);
    return () => { unsub(); clearInterval(interval); };
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

  async function loadNextTrigger() {
    try {
      nextTrigger = await api.getNextTrigger();
    } catch (e) {
      console.error('Failed to load next trigger:', e);
    }
  }

  async function loadUpcomingHolidays() {
    try {
      upcomingHolidays = await api.getUpcomingHolidays(8);
    } catch (e) {
      console.error('Failed to load upcoming holidays:', e);
    }
  }

  function holidayWhen(h) {
    if (h.active) return 'Active now';
    if (h.days_until === 0) return 'Today';
    if (h.days_until === 1) return 'Tomorrow';
    if (h.days_until < 7) return `in ${h.days_until} days`;
    if (h.days_until < 14) return 'next week';
    if (h.days_until < 60) return `in ${Math.round(h.days_until / 7)} weeks`;
    return `in ${Math.round(h.days_until / 30)} months`;
  }

  function holidayDate(iso) {
    const d = new Date(iso + 'T00:00:00');
    return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
  }

  function formatTime(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  }

  function formatCountdown(isoStr) {
    if (!isoStr) return '';
    const diff = new Date(isoStr) - Date.now();
    if (diff <= 0) return 'now';
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `in ${mins}m`;
    const hrs = Math.floor(mins / 60);
    const rm = mins % 60;
    return rm > 0 ? `in ${hrs}h ${rm}m` : `in ${hrs}h`;
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
    <div class="section-title"><h2>Lights</h2></div>
    <div class="grid grid-3 mb-4">
      {#each lights as light (light.name)}
        <LightCard {light} onOverride={handleOverride} onClearOverride={handleClearOverride} />
      {/each}
    </div>
  {/if}

  {#if nextTrigger}
    <div class="section-title"><h2>Coming Up</h2></div>
    <div class="coming-up-section mb-4">
      {#if nextTrigger.current && nextTrigger.current.length > 0}
        <div class="card coming-up-card">
          <div class="coming-up-header">
            <span class="badge ok">Active Now</span>
          </div>
          <div class="coming-up-targets">
            {#each nextTrigger.current as pred}
              <div class="prediction-row">
                <div class="pred-color" style="background: {pred.color ? bulbPreview(pred.color) : '#6b7482'}"></div>
                <div class="pred-info">
                  <span class="pred-name">{pred.friendly_name || pred.target}</span>
                  <span class="pred-rule">{pred.rule_name}</span>
                </div>
                <span class="pred-mode badge info">{pred.mode}</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      {#each nextTrigger.upcoming || [] as event, i}
        <div class="card coming-up-card">
          <div class="coming-up-header">
            <span class="coming-up-time">{formatTime(event.time)}</span>
            <span class="coming-up-countdown">{formatCountdown(event.time)}</span>
          </div>
          <div class="coming-up-targets">
            {#if !event.targets?.length}
              <div class="all-off">
                <span class="off-dot"></span>
                All lights off — no rule matches
              </div>
            {/if}
            {#each event.targets as pred}
              <div class="prediction-row">
                <div class="pred-color" style="background: {pred.color ? bulbPreview(pred.color) : '#6b7482'}"></div>
                <div class="pred-info">
                  <span class="pred-name">{pred.friendly_name || pred.target}</span>
                  <span class="pred-rule">{pred.rule_name}</span>
                </div>
                <span class="pred-mode badge info">{pred.mode}</span>
              </div>
            {/each}
          </div>
        </div>
      {/each}

      {#if (!nextTrigger.current || nextTrigger.current.length === 0) && (!nextTrigger.upcoming || nextTrigger.upcoming.length === 0)}
        <div class="card">
          <p style="color: var(--text-muted); font-size: 13px;">No upcoming rule activations predicted.</p>
        </div>
      {/if}
    </div>
  {/if}

  <div class="section-title"><h2>Upcoming Holidays</h2></div>
  {#if upcomingHolidays.length === 0}
    <div class="card empty-state">Nothing scheduled in the next year.</div>
  {:else}
    <div class="holiday-queue card">
      {#each upcomingHolidays as h, i}
        <div class="hq-row" class:is-active={h.active}>
          <div class="hq-when">
            <span class="hq-rel">{holidayWhen(h)}</span>
            <span class="hq-date">{holidayDate(h.date)}</span>
          </div>
          <div class="hq-strip" title={h.colors.join('  ')}>
            {#each h.colors as c}
              <span style="background: {bulbPreview(c)}"></span>
            {/each}
          </div>
          <div class="hq-name">
            {h.name}
            {#if i > 0 && upcomingHolidays[i - 1].date === h.date}
              <span class="hq-note" title="Shares a date with {upcomingHolidays[i - 1].name}, which has higher priority">overridden</span>
            {/if}
          </div>
          <span class="badge neutral hq-cat">{h.category.replace('_', ' ')}</span>
        </div>
      {/each}
    </div>
  {/if}

  <div class="section-title"><h2>Providers</h2></div>
  <div class="grid grid-3">
    {#each providers as provider (provider.name)}
      <ProviderStatus {provider} />
    {/each}
  </div>
{/if}

<style>
  .holiday-queue { display: flex; flex-direction: column; padding: 0; }
  .hq-row {
    display: grid;
    grid-template-columns: 104px 68px 1fr auto;
    align-items: center; gap: var(--space-3);
    padding: 11px var(--space-4);
    border-bottom: 1px solid var(--border);
  }
  .hq-row:last-child { border-bottom: none; }
  .hq-row.is-active { background: rgba(52, 208, 127, .07); }
  .hq-when { display: flex; flex-direction: column; line-height: 1.3; }
  .hq-rel { font-size: 13px; font-weight: 600; color: var(--text-primary); }
  .hq-row.is-active .hq-rel { color: var(--success); }
  .hq-date { font-size: 11px; color: var(--text-muted); }
  .hq-strip {
    display: flex; height: 20px; border-radius: 5px; overflow: hidden;
    border: 1px solid rgba(255,255,255,.14);
  }
  .hq-strip span { flex: 1; }
  .hq-name { font-size: 14px; color: var(--text-primary); }
  .hq-note {
    font-size: 10px; color: var(--text-muted); border: 1px solid var(--border-light);
    border-radius: 999px; padding: 1px 7px; margin-left: 6px; vertical-align: middle;
  }
  .hq-cat { text-transform: capitalize; }

  @media (max-width: 640px) {
    .hq-row { grid-template-columns: 92px 1fr; row-gap: 6px; }
    .hq-cat { display: none; }
  }

  .all-off {
    display: flex; align-items: center; gap: 9px;
    font-size: 13px; color: var(--text-muted); padding: 6px 0;
  }
  .off-dot {
    width: 22px; height: 22px; border-radius: 50%;
    border: 2px dashed var(--border-light); flex-shrink: 0;
  }

  .coming-up-section {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }
  .coming-up-card {
    flex: 1;
    min-width: 220px;
    max-width: 400px;
  }
  .coming-up-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  .coming-up-time {
    font-size: 18px;
    font-weight: 700;
  }
  .coming-up-countdown {
    font-size: 13px;
    color: var(--text-muted);
  }
  .coming-up-targets {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .prediction-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .pred-color {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 2px solid var(--border-light);
    flex-shrink: 0;
  }
  .pred-info {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  .pred-name {
    font-size: 14px;
    font-weight: 500;
  }
  .pred-rule {
    font-size: 12px;
    color: var(--text-muted);
  }
  .pred-mode {
    flex-shrink: 0;
  }
</style>
