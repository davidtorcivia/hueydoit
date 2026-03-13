<script>
  import { api } from '../lib/api.js';

  let step = $state(1);
  let bridgeStatus = $state(null);
  let pairMessage = $state('');
  let pairing = $state(false);
  let bridgeLights = $state([]);
  let bridgeGroups = $state([]);
  let discovering = $state(false);
  let addedTargets = $state([]);
  let addingName = $state('');

  $effect(() => {
    checkBridgeStatus();
  });

  async function checkBridgeStatus() {
    try {
      bridgeStatus = await api.getBridgeStatus();
      if (bridgeStatus.connected) {
        step = 2;
      }
    } catch {
      bridgeStatus = { connected: false, paired: false, host: '' };
    }
  }

  async function pairBridge() {
    pairing = true;
    pairMessage = '';
    try {
      const result = await api.pairBridge();
      pairMessage = `Paired with bridge at ${result.host}!`;
      bridgeStatus = { connected: true, paired: true, host: result.host };
      step = 2;
    } catch (e) {
      pairMessage = e.message;
    }
    pairing = false;
  }

  async function discoverLights() {
    discovering = true;
    try {
      const result = await api.getBridgeLights();
      bridgeLights = result.lights || [];
      bridgeGroups = result.groups || [];
    } catch (e) {
      alert('Discovery failed: ' + e.message);
    }
    discovering = false;
  }

  async function addTarget(item, type) {
    const name = addingName || item.name.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    try {
      await api.addLight({
        name,
        type,
        hue_id: item.id,
        friendly_name: item.name,
      });
      addedTargets = [...addedTargets, name];
      addingName = '';
    } catch (e) {
      alert('Add failed: ' + e.message);
    }
  }

  function isAdded(id) {
    return bridgeLights.concat(bridgeGroups).some(
      i => i.id === id && addedTargets.includes(i.name?.toLowerCase().replace(/[^a-z0-9]+/g, '_'))
    );
  }

  async function flashLight(name) {
    try {
      await api.testLight(name);
    } catch (e) {
      console.error('Flash failed:', e);
    }
  }
</script>

<div class="setup-container">
  <div class="setup-header">
    <h1>Setup Huey Do It</h1>
    <p style="color: var(--text-secondary); margin-top: 8px;">
      Connect your Hue bridge and add lights to get started.
    </p>
  </div>

  <div class="steps">
    <div class="step-indicator">
      <div class="step-dot" class:active={step >= 1} class:done={step > 1}>1</div>
      <div class="step-line" class:done={step > 1}></div>
      <div class="step-dot" class:active={step >= 2} class:done={step > 2}>2</div>
      <div class="step-line" class:done={step > 2}></div>
      <div class="step-dot" class:active={step >= 3}>3</div>
    </div>
    <div class="step-labels">
      <span>Bridge</span>
      <span>Lights</span>
      <span>Done</span>
    </div>
  </div>

  {#if step === 1}
    <div class="card setup-step">
      <h2>Step 1: Connect Your Hue Bridge</h2>
      <div class="step-body">
        <div class="instruction">
          <div class="instruction-number">1</div>
          <p>Make sure your Hue bridge is on the same network as this device.</p>
        </div>
        <div class="instruction">
          <div class="instruction-number">2</div>
          <p>Press the large round button on top of your Hue bridge.</p>
        </div>
        <div class="instruction">
          <div class="instruction-number">3</div>
          <p>Click the button below within 30 seconds.</p>
        </div>

        <button class="primary pair-button" onclick={pairBridge} disabled={pairing}>
          {pairing ? 'Connecting...' : 'Connect to Bridge'}
        </button>

        {#if pairMessage}
          <p class="pair-message" class:error={!bridgeStatus?.connected}>
            {pairMessage}
          </p>
        {/if}
      </div>
    </div>

  {:else if step === 2}
    <div class="card setup-step">
      <h2>Step 2: Add Your Lights</h2>
      <div class="step-body">
        <p style="color: var(--text-secondary); margin-bottom: 16px;">
          Discover lights and zones from your bridge. Give each a short name for use in rules.
        </p>

        <button class="primary" onclick={discoverLights} disabled={discovering}>
          {discovering ? 'Discovering...' : 'Discover Lights'}
        </button>

        {#if bridgeLights.length > 0}
          <h3 class="mt-4 mb-2">Individual Lights</h3>
          {#each bridgeLights as bl}
            <div class="discover-item">
              <div class="discover-info">
                <strong>{bl.name}</strong>
                <span class="badge {bl.on ? 'ok' : 'warning'}">{bl.on ? 'ON' : 'OFF'}</span>
              </div>
              <div class="flex gap-2 items-center">
                <input type="text" placeholder="target name" bind:value={addingName} style="width: 140px;" />
                <button class="small primary" onclick={() => addTarget(bl, 'light')}>Add</button>
                <button class="small secondary" onclick={() => { api.testLight(bl.name.toLowerCase().replace(/[^a-z0-9]+/g, '_')).catch(() => {}); }}>Flash</button>
              </div>
            </div>
          {/each}
        {/if}

        {#if bridgeGroups.length > 0}
          <h3 class="mt-4 mb-2">Rooms & Zones</h3>
          <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 8px;">
            Using zones sends a single command to all lights — no popcorn effect.
          </p>
          {#each bridgeGroups as bg}
            <div class="discover-item">
              <div class="discover-info">
                <strong>{bg.name}</strong>
                <span class="badge info">zone</span>
              </div>
              <div class="flex gap-2 items-center">
                <input type="text" placeholder="target name" bind:value={addingName} style="width: 140px;" />
                <button class="small primary" onclick={() => addTarget(bg, 'grouped_light')}>Add</button>
              </div>
            </div>
          {/each}
        {/if}

        {#if addedTargets.length > 0}
          <div class="added-summary mt-4">
            <span class="badge ok">{addedTargets.length} light(s) added</span>
            <button class="primary mt-2" onclick={() => step = 3}>Continue</button>
          </div>
        {/if}
      </div>
    </div>

  {:else if step === 3}
    <div class="card setup-step">
      <h2>All Set!</h2>
      <div class="step-body">
        <p style="color: var(--text-secondary); margin-bottom: 16px;">
          Your Hue bridge is connected and {addedTargets.length} light(s) are configured.
          Head to the Dashboard to see them, or create Rules to automate them.
        </p>
        <div class="flex gap-2">
          <button class="primary" onclick={() => window.dispatchEvent(new CustomEvent('navigate', { detail: 'dashboard' }))}>
            Go to Dashboard
          </button>
          <button class="secondary" onclick={() => window.dispatchEvent(new CustomEvent('navigate', { detail: 'rules' }))}>
            Create Rules
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .setup-container {
    max-width: 640px;
    margin: 0 auto;
  }
  .setup-header { text-align: center; margin-bottom: 32px; }
  .steps { margin-bottom: 32px; }
  .step-indicator {
    display: flex; align-items: center; justify-content: center; gap: 0;
  }
  .step-dot {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--border); color: var(--text-muted);
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 14px;
    transition: all 0.2s;
  }
  .step-dot.active { background: var(--accent); color: white; }
  .step-dot.done { background: var(--success); color: white; }
  .step-line {
    width: 80px; height: 3px; background: var(--border);
    transition: background 0.2s;
  }
  .step-line.done { background: var(--success); }
  .step-labels {
    display: flex; justify-content: center; gap: 80px;
    margin-top: 8px; font-size: 12px; color: var(--text-muted);
  }
  .setup-step { }
  .step-body { margin-top: 16px; }
  .instruction {
    display: flex; align-items: flex-start; gap: 12px;
    margin-bottom: 12px;
  }
  .instruction-number {
    width: 28px; height: 28px; border-radius: 50%;
    background: var(--bg-input); color: var(--accent);
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 14px; flex-shrink: 0;
  }
  .instruction p { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }
  .pair-button { margin-top: 16px; padding: 12px 32px; font-size: 16px; }
  .pair-message { margin-top: 12px; font-size: 14px; color: var(--success); }
  .pair-message.error { color: var(--error); }
  .discover-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 0; border-bottom: 1px solid var(--border);
  }
  .discover-info { display: flex; align-items: center; gap: 8px; }
  .added-summary { text-align: center; }
</style>
