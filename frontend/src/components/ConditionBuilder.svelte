<script>
  import { api } from '../lib/api.js';

  let { condition = {}, onChange } = $props();

  // Parse initial condition
  let condAlways = $state(condition?.match === 'always');
  let provider = $state(condition?.provider || '');
  let preset = $state('');
  let showAdvanced = $state(false);
  let advancedJson = $state('');

  // Preset-specific values
  let holidayMode = $state('any'); // 'any' | 'specific'
  let selectedHoliday = $state('');

  let weatherPreset = $state('temp_above'); // temp_above, temp_below, condition_is, humidity_above, humidity_below
  let weatherValue = $state('');
  let weatherCondition = $state('Clear');

  let solarPreset = $state('daytime'); // daytime, after_sunset, before_sunrise

  let timePreset = $state('during_hours'); // during_hours, weekends, weekdays, specific_day
  let timeStart = $state(18);
  let timeEnd = $state(23);
  let timeDay = $state('monday');

  let webhookKey = $state('');
  let webhookValue = $state('');

  // Holiday list for dropdown
  let holidays = $state([]);

  $effect(() => {
    api.getHolidays().then(h => holidays = h).catch(() => {});
  });

  // Parse existing condition into preset state on mount
  $effect(() => {
    if (!condition || condition.match === 'always') return;
    const p = condition.provider;
    const m = condition.match;
    if (!p || !m || typeof m !== 'object') return;

    if (p === 'holiday') {
      if (m.active_holiday && typeof m.active_holiday === 'object' && 'gt' in m.active_holiday) {
        holidayMode = 'any';
        preset = 'holiday_any';
      } else if (m.active_holiday) {
        holidayMode = 'specific';
        selectedHoliday = String(m.active_holiday);
        preset = 'holiday_specific';
      }
    } else if (p === 'weather') {
      if (m.temp_f) {
        if (typeof m.temp_f === 'object') {
          if ('gt' in m.temp_f || 'gte' in m.temp_f) {
            weatherPreset = 'temp_above';
            weatherValue = String(m.temp_f.gt ?? m.temp_f.gte ?? '');
            preset = 'weather_temp_above';
          } else {
            weatherPreset = 'temp_below';
            weatherValue = String(m.temp_f.lt ?? m.temp_f.lte ?? '');
            preset = 'weather_temp_below';
          }
        }
      } else if (m.condition) {
        weatherPreset = 'condition_is';
        weatherCondition = String(m.condition);
        preset = 'weather_condition';
      } else if (m.humidity) {
        if (typeof m.humidity === 'object') {
          if ('gt' in m.humidity || 'gte' in m.humidity) {
            weatherPreset = 'humidity_above';
            weatherValue = String(m.humidity.gt ?? m.humidity.gte ?? '');
            preset = 'weather_humidity_above';
          } else {
            weatherPreset = 'humidity_below';
            weatherValue = String(m.humidity.lt ?? m.humidity.lte ?? '');
            preset = 'weather_humidity_below';
          }
        }
      }
    } else if (p === 'solar') {
      if (m.period === 'day') { solarPreset = 'daytime'; preset = 'solar_daytime'; }
      else if (m.period === 'night') { solarPreset = 'after_sunset'; preset = 'solar_after_sunset'; }
      else if (m.period) { solarPreset = m.period; preset = 'solar_' + m.period; }
    } else if (p === 'time') {
      if (m.is_weekend === true) { timePreset = 'weekends'; preset = 'time_weekends'; }
      else if (m.is_weekend === false) { timePreset = 'weekdays'; preset = 'time_weekdays'; }
      else if (m.day_of_week) { timePreset = 'specific_day'; timeDay = String(m.day_of_week); preset = 'time_specific_day'; }
      else if (m.hour) {
        timePreset = 'during_hours';
        if (typeof m.hour === 'object') {
          timeStart = m.hour.gte ?? m.hour.gt ?? 18;
        }
        preset = 'time_during_hours';
      }
    } else if (p === 'webhook') {
      const keys = Object.keys(m);
      if (keys.length > 0) {
        webhookKey = keys[0];
        webhookValue = String(m[keys[0]]);
      }
      preset = 'webhook';
    }
  });

  function buildCondition() {
    if (condAlways) return { match: 'always' };

    if (showAdvanced) {
      try {
        return JSON.parse(advancedJson);
      } catch {
        return condition;
      }
    }

    if (provider === 'holiday') {
      if (holidayMode === 'any') {
        return { provider: 'holiday', match: { active_holiday: { gt: '' } } };
      } else {
        return { provider: 'holiday', match: { active_holiday: selectedHoliday } };
      }
    }

    if (provider === 'weather') {
      switch (weatherPreset) {
        case 'temp_above':
          return { provider: 'weather', match: { temp_f: { gte: Number(weatherValue) || 80 } } };
        case 'temp_below':
          return { provider: 'weather', match: { temp_f: { lte: Number(weatherValue) || 32 } } };
        case 'condition_is':
          return { provider: 'weather', match: { condition: weatherCondition } };
        case 'humidity_above':
          return { provider: 'weather', match: { humidity: { gte: Number(weatherValue) || 70 } } };
        case 'humidity_below':
          return { provider: 'weather', match: { humidity: { lte: Number(weatherValue) || 30 } } };
      }
    }

    if (provider === 'solar') {
      switch (solarPreset) {
        case 'daytime':
          return { provider: 'solar', match: { period: 'day' } };
        case 'after_sunset':
          return { provider: 'solar', match: { period: 'night' } };
        case 'before_sunrise':
          return { provider: 'solar', match: { period: 'night' } };
      }
    }

    if (provider === 'time') {
      switch (timePreset) {
        case 'during_hours':
          return { provider: 'time', match: { hour: { gte: Number(timeStart) } } };
        case 'weekends':
          return { provider: 'time', match: { is_weekend: true } };
        case 'weekdays':
          return { provider: 'time', match: { is_weekend: false } };
        case 'specific_day':
          return { provider: 'time', match: { day_of_week: timeDay } };
      }
    }

    if (provider === 'webhook') {
      return { provider: 'webhook', match: { [webhookKey]: webhookValue } };
    }

    return condition;
  }

  // Emit changes whenever inputs change
  function emitChange() {
    onChange(buildCondition());
  }

  // Sync advanced JSON when toggling
  $effect(() => {
    if (showAdvanced) {
      advancedJson = JSON.stringify(buildCondition(), null, 2);
    }
  });
</script>

<div class="condition-builder">
  <div class="form-group">
    <label>
      <input type="checkbox" bind:checked={condAlways} onchange={emitChange} /> Always match (catch-all)
    </label>
  </div>

  {#if !condAlways}
    <div class="form-group">
      <label>Provider</label>
      <select bind:value={provider} onchange={() => { preset = ''; emitChange(); }}>
        <option value="">Select a provider...</option>
        <option value="holiday">Holiday</option>
        <option value="weather">Weather</option>
        <option value="solar">Solar</option>
        <option value="time">Time</option>
        <option value="webhook">Webhook</option>
      </select>
    </div>

    {#if provider === 'holiday'}
      <div class="preset-section">
        <div class="form-group">
          <label>When</label>
          <select bind:value={holidayMode} onchange={emitChange}>
            <option value="any">Any holiday is active</option>
            <option value="specific">A specific holiday is active</option>
          </select>
        </div>
        {#if holidayMode === 'specific'}
          <div class="form-group">
            <label>Holiday</label>
            <select bind:value={selectedHoliday} onchange={emitChange}>
              <option value="">Select...</option>
              {#each holidays.filter(h => h.enabled) as h}
                <option value={h.name}>{h.name}</option>
              {/each}
            </select>
          </div>
        {/if}
      </div>
    {/if}

    {#if provider === 'weather'}
      <div class="preset-section">
        <div class="form-group">
          <label>When</label>
          <select bind:value={weatherPreset} onchange={emitChange}>
            <option value="temp_above">Temperature is above</option>
            <option value="temp_below">Temperature is below</option>
            <option value="condition_is">Weather condition is</option>
            <option value="humidity_above">Humidity is above</option>
            <option value="humidity_below">Humidity is below</option>
          </select>
        </div>
        {#if weatherPreset === 'condition_is'}
          <div class="form-group">
            <label>Condition</label>
            <select bind:value={weatherCondition} onchange={emitChange}>
              <option value="Clear">Clear</option>
              <option value="Clouds">Clouds</option>
              <option value="Rain">Rain</option>
              <option value="Snow">Snow</option>
              <option value="Thunderstorm">Thunderstorm</option>
              <option value="Drizzle">Drizzle</option>
              <option value="Mist">Mist</option>
              <option value="Fog">Fog</option>
            </select>
          </div>
        {:else}
          <div class="form-group">
            <label>{weatherPreset.includes('temp') ? 'Temperature (°F)' : 'Humidity (%)'}</label>
            <input type="number" bind:value={weatherValue} oninput={emitChange}
              placeholder={weatherPreset.includes('temp') ? '32' : '50'} />
          </div>
        {/if}
      </div>
    {/if}

    {#if provider === 'solar'}
      <div class="preset-section">
        <div class="form-group">
          <label>When</label>
          <select bind:value={solarPreset} onchange={emitChange}>
            <option value="daytime">During daytime</option>
            <option value="after_sunset">After sunset</option>
            <option value="before_sunrise">Before sunrise</option>
          </select>
        </div>
      </div>
    {/if}

    {#if provider === 'time'}
      <div class="preset-section">
        <div class="form-group">
          <label>When</label>
          <select bind:value={timePreset} onchange={emitChange}>
            <option value="during_hours">During specific hours</option>
            <option value="weekends">On weekends</option>
            <option value="weekdays">On weekdays</option>
            <option value="specific_day">On a specific day</option>
          </select>
        </div>
        {#if timePreset === 'during_hours'}
          <div class="flex gap-2">
            <div class="form-group" style="flex:1">
              <label>Start hour</label>
              <select bind:value={timeStart} onchange={emitChange}>
                {#each Array.from({length: 24}, (_, i) => i) as h}
                  <option value={h}>{h.toString().padStart(2, '0')}:00</option>
                {/each}
              </select>
            </div>
            <div class="form-group" style="flex:1">
              <label>End hour (display only)</label>
              <select bind:value={timeEnd} onchange={emitChange}>
                {#each Array.from({length: 24}, (_, i) => i) as h}
                  <option value={h}>{h.toString().padStart(2, '0')}:00</option>
                {/each}
              </select>
            </div>
          </div>
        {/if}
        {#if timePreset === 'specific_day'}
          <div class="form-group">
            <label>Day</label>
            <select bind:value={timeDay} onchange={emitChange}>
              <option value="monday">Monday</option>
              <option value="tuesday">Tuesday</option>
              <option value="wednesday">Wednesday</option>
              <option value="thursday">Thursday</option>
              <option value="friday">Friday</option>
              <option value="saturday">Saturday</option>
              <option value="sunday">Sunday</option>
            </select>
          </div>
        {/if}
      </div>
    {/if}

    {#if provider === 'webhook'}
      <div class="preset-section">
        <div class="flex gap-2">
          <div class="form-group" style="flex:1">
            <label>Key</label>
            <input type="text" bind:value={webhookKey} oninput={emitChange} placeholder="e.g. motion_detected" />
          </div>
          <div class="form-group" style="flex:1">
            <label>Value</label>
            <input type="text" bind:value={webhookValue} oninput={emitChange} placeholder="e.g. true" />
          </div>
        </div>
      </div>
    {/if}

    <div class="advanced-toggle">
      <label>
        <input type="checkbox" bind:checked={showAdvanced} /> Advanced (raw JSON)
      </label>
    </div>

    {#if showAdvanced}
      <div class="form-group">
        <textarea
          bind:value={advancedJson}
          oninput={() => { try { onChange(JSON.parse(advancedJson)); } catch {} }}
          rows="6"
          class="json-editor"
        ></textarea>
      </div>
    {/if}
  {/if}
</div>

<style>
  .condition-builder { display: flex; flex-direction: column; gap: 4px; }
  .preset-section {
    padding: 12px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: var(--radius);
    border: 1px solid var(--border);
  }
  .advanced-toggle {
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 4px;
  }
  .json-editor {
    font-family: monospace;
    font-size: 13px;
    width: 100%;
    background: var(--bg-input);
    color: var(--text-primary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 8px;
    resize: vertical;
  }
</style>
