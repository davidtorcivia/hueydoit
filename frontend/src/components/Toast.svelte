<script>
  import { onToast } from '../lib/toast.js';

  let toasts = $state([]);

  $effect(() => {
    return onToast((t) => {
      toasts = [...toasts, t];
      setTimeout(() => {
        toasts = toasts.filter(x => x.id !== t.id);
      }, t.duration);
    });
  });

  function dismiss(id) {
    toasts = toasts.filter(t => t.id !== id);
  }
</script>

{#if toasts.length > 0}
  <div class="toast-container">
    {#each toasts as t (t.id)}
      <div class="toast toast-{t.type}" onclick={() => dismiss(t.id)}>
        <span class="toast-icon">
          {#if t.type === 'success'}&#10003;{:else if t.type === 'error'}&#10007;{:else if t.type === 'warning'}&#9888;{:else}&#8505;{/if}
        </span>
        <span class="toast-msg">{t.message}</span>
      </div>
    {/each}
  </div>
{/if}

<style>
  .toast-container {
    position: fixed;
    top: 16px;
    right: 16px;
    z-index: 2000;
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-width: 380px;
  }
  .toast {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    border-radius: var(--radius);
    font-size: 14px;
    color: white;
    cursor: pointer;
    animation: slideIn 0.2s ease-out;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  }
  .toast-success { background: var(--success); }
  .toast-error { background: var(--error); }
  .toast-warning { background: var(--warning); color: #1a1a2e; }
  .toast-info { background: var(--accent); }
  .toast-icon { font-size: 16px; flex-shrink: 0; }
  .toast-msg { flex: 1; }
  @keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
</style>
