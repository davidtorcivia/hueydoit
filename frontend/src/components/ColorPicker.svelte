<script>
  let { colors = [], onChange } = $props();
  let localColors = $state([...colors]);

  function addColor() {
    localColors = [...localColors, '#ffffff'];
    onChange(localColors);
  }

  function removeColor(idx) {
    localColors = localColors.filter((_, i) => i !== idx);
    onChange(localColors);
  }

  function updateColor(idx, value) {
    localColors[idx] = value;
    localColors = [...localColors];
    onChange(localColors);
  }
</script>

<div class="color-picker">
  <div class="color-list">
    {#each localColors as color, i}
      <div class="color-item">
        <input
          type="color"
          value={color}
          oninput={(e) => updateColor(i, e.target.value)}
        />
        <span class="color-hex">{color}</span>
        <button class="small danger" onclick={() => removeColor(i)}>x</button>
      </div>
    {/each}
  </div>
  <button class="small secondary" onclick={addColor}>+ Add Color</button>
</div>

<style>
  .color-picker { display: flex; flex-direction: column; gap: 8px; }
  .color-list { display: flex; flex-wrap: wrap; gap: 8px; }
  .color-item { display: flex; align-items: center; gap: 6px; }
  .color-item input[type="color"] {
    width: 36px; height: 28px; padding: 1px; cursor: pointer; border: 1px solid var(--border);
  }
  .color-hex { font-size: 12px; color: var(--text-muted); font-family: monospace; }
</style>
