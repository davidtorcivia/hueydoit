<script>
  import { api } from '../lib/api.js';
  import ConditionBuilder from './ConditionBuilder.svelte';

  let condition = $state({});
  let result = $state(null);
  let testing = $state(false);

  async function runTest() {
    testing = true;
    result = null;
    try {
      const testCond = Object.keys(condition).length > 0 ? condition : { match: 'always' };
      result = await api.testRule(testCond);
    } catch (e) {
      result = { error: e.message };
    }
    testing = false;
  }
</script>

<div class="card">
  <h3 class="mb-3">Rule Tester (Dry Run)</h3>
  <ConditionBuilder {condition} onChange={(c) => condition = c} />
  <div class="mt-3">
    <button class="primary small" onclick={runTest} disabled={testing}>
      {testing ? 'Testing...' : 'Test Condition'}
    </button>
  </div>

  {#if result}
    {#if result.error}
      <div class="badge error mt-2">{result.error}</div>
    {:else}
      <div class="test-result">
        <span class="badge {result.would_match ? 'ok' : 'warning'}">
          {result.would_match ? 'MATCH' : 'NO MATCH'}
        </span>
      </div>
    {/if}
  {/if}
</div>

<style>
  .test-result { margin-top: 8px; }
</style>
