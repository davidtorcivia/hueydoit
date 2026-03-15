<script>
  let { condition = {}, holidays = [], onChange, onRemove = null } = $props();

  let provider = $state(condition?.provider || '');

  // Preset-specific values
  let holidayMode = $state('any');
  let selectedHoliday = $state('');
  let weatherPreset = $state('temp_above');
  let weatherValue = $state('');
  let weatherCondition = $state('Clear');
  let solarPreset = $state('daytime');
  let solarOffsetMin = $state(0);
  let timePreset = $state('during_hours');
  let timeStart = $state(18);
  let timeEnd = $state(23);
  let timeDay = $state('monday');
  let webhookKey = $state('');
  let webhookValue = $state('');
  let calendarPreset = $state('season');
  let calendarSeason = $state('spring');
  let calendarMonth = $state('1');
  let calendarDateStart = $state('03-01');
  let calendarDateEnd = $state('05-31');

  // Parse initial condition on mount
  const _m = condition?.match;
  if (condition?.provider && _m && typeof _m === 'object') {
    const _p = condition.provider;
    if (_p === 'holiday') {
      if (_m.active_holiday && typeof _m.active_holiday === 'object' && 'gt' in _m.active_holiday) {
        holidayMode = 'any';
      } else if (_m.active_holiday) {
        holidayMode = 'specific';
        selectedHoliday = String(_m.active_holiday);
      }
    } else if (_p === 'weather') {
      if (_m.temp_f) {
        if (typeof _m.temp_f === 'object') {
          if ('gt' in _m.temp_f || 'gte' in _m.temp_f) {
            weatherPreset = 'temp_above';
            weatherValue = String(_m.temp_f.gt ?? _m.temp_f.gte ?? '');
          } else {
            weatherPreset = 'temp_below';
            weatherValue = String(_m.temp_f.lt ?? _m.temp_f.lte ?? '');
          }
        }
      } else if (_m.condition) {
        weatherPreset = 'condition_is';
        weatherCondition = String(_m.condition);
      } else if (_m.humidity) {
        if (typeof _m.humidity === 'object') {
          if ('gt' in _m.humidity || 'gte' in _m.humidity) {
            weatherPreset = 'humidity_above';
            weatherValue = String(_m.humidity.gt ?? _m.humidity.gte ?? '');
          } else {
            weatherPreset = 'humidity_below';
            weatherValue = String(_m.humidity.lt ?? _m.humidity.lte ?? '');
          }
        }
      }
    } else if (_p === 'solar') {
      if (_m.period === 'day') solarPreset = 'daytime';
      else if (_m.phase === 'before_sunrise') solarPreset = 'before_sunrise';
      else if (_m.phase === 'after_sunset') solarPreset = 'after_sunset';
      else if (_m.period === 'night') solarPreset = 'after_sunset';
      else if (_m.period) solarPreset = _m.period;
      // Parse offset from sunrise_offset or sunset_offset
      const rawOffset = _m.sunrise_offset || _m.sunset_offset || '';
      if (rawOffset) {
        const neg = rawOffset.startsWith('-');
        const abs = rawOffset.replace(/^[+-]/, '');
        let mins = 0;
        if (abs.endsWith('h')) mins = parseInt(abs) * 60;
        else if (abs.endsWith('m')) mins = parseInt(abs);
        else mins = parseInt(abs);
        solarOffsetMin = neg ? -mins : mins;
      }
    } else if (_p === 'time') {
      if (_m.is_weekend === true) timePreset = 'weekends';
      else if (_m.is_weekend === false) timePreset = 'weekdays';
      else if (_m.day_of_week) { timePreset = 'specific_day'; timeDay = String(_m.day_of_week); }
      else if (_m.hour_range) {
        timePreset = 'during_hours';
        timeStart = _m.hour_range.start ?? 18;
        timeEnd = _m.hour_range.end ?? 23;
      } else if (_m.hour) {
        // Legacy: hour: {gte: X}
        timePreset = 'during_hours';
        if (typeof _m.hour === 'object') {
          timeStart = _m.hour.gte ?? _m.hour.gt ?? 18;
        }
      }
    } else if (_p === 'calendar') {
      if (_m.season) {
        calendarPreset = 'season';
        calendarSeason = String(_m.season);
      } else if (_m.month !== undefined) {
        calendarPreset = 'month';
        calendarMonth = String(_m.month);
      } else if (_m.month_name) {
        calendarPreset = 'month';
        const monthMap = { january:1, february:2, march:3, april:4, may:5, june:6, july:7, august:8, september:9, october:10, november:11, december:12 };
        calendarMonth = String(monthMap[_m.month_name] || 1);
      } else if (_m.date_range) {
        // Detect if this is a known season range
        const s = _m.date_range.start, e = _m.date_range.end;
        if (s === '03-20' && e === '06-20') { calendarPreset = 'season'; calendarSeason = 'spring'; }
        else if (s === '06-21' && e === '09-21') { calendarPreset = 'season'; calendarSeason = 'summer'; }
        else if (s === '09-22' && e === '12-20') { calendarPreset = 'season'; calendarSeason = 'fall'; }
        else if (s === '12-21' && e === '03-19') { calendarPreset = 'season'; calendarSeason = 'winter'; }
        else {
          calendarPreset = 'date_range';
          calendarDateStart = s || '03-01';
          calendarDateEnd = e || '05-31';
        }
      }
    } else if (_p === 'webhook') {
      const keys = Object.keys(_m);
      if (keys.length > 0) {
        webhookKey = keys[0];
        webhookValue = String(_m[keys[0]]);
      }
    }
  }

  function buildCondition() {
    if (provider === 'holiday') {
      if (holidayMode === 'any') {
        return { provider: 'holiday', match: { active_holiday: { gt: '' } } };
      } else {
        return { provider: 'holiday', match: { active_holiday: selectedHoliday } };
      }
    }
    if (provider === 'weather') {
      switch (weatherPreset) {
        case 'temp_above': return { provider: 'weather', match: { temp_f: { gte: Number(weatherValue) || 80 } } };
        case 'temp_below': return { provider: 'weather', match: { temp_f: { lte: Number(weatherValue) || 32 } } };
        case 'condition_is': return { provider: 'weather', match: { condition: weatherCondition } };
        case 'humidity_above': return { provider: 'weather', match: { humidity: { gte: Number(weatherValue) || 70 } } };
        case 'humidity_below': return { provider: 'weather', match: { humidity: { lte: Number(weatherValue) || 30 } } };
      }
    }
    if (provider === 'solar') {
      let match = {};
      switch (solarPreset) {
        case 'daytime': match = { period: 'day' }; break;
        case 'after_sunset': match = { period: 'night' }; break;
        case 'before_sunrise': match = { phase: 'before_sunrise' }; break;
      }
      if (solarOffsetMin !== 0) {
        const absMin = Math.abs(solarOffsetMin);
        const sign = solarOffsetMin < 0 ? '-' : '';
        const offsetStr = absMin >= 60 ? `${sign}${Math.floor(absMin / 60)}h` : `${sign}${absMin}m`;
        // Offset applies to the event that defines the boundary:
        // "after sunset" / "daytime" → sunset_offset
        // "before sunrise" → sunrise_offset
        if (solarPreset === 'before_sunrise') {
          match.sunrise_offset = offsetStr;
        } else {
          match.sunset_offset = offsetStr;
        }
      }
      return { provider: 'solar', match };
    }
    if (provider === 'time') {
      switch (timePreset) {
        case 'during_hours': return { provider: 'time', match: { hour_range: { start: Number(timeStart), end: Number(timeEnd) } } };
        case 'weekends': return { provider: 'time', match: { is_weekend: true } };
        case 'weekdays': return { provider: 'time', match: { is_weekend: false } };
        case 'specific_day': return { provider: 'time', match: { day_of_week: timeDay } };
      }
    }
    if (provider === 'calendar') {
      if (calendarPreset === 'season') {
        const seasonDates = {
          spring: { start: '03-20', end: '06-20' },
          summer: { start: '06-21', end: '09-21' },
          fall:   { start: '09-22', end: '12-20' },
          winter: { start: '12-21', end: '03-19' },
        };
        const range = seasonDates[calendarSeason] || seasonDates.spring;
        return { provider: 'calendar', match: { date_range: range } };
      }
      if (calendarPreset === 'month') {
        return { provider: 'calendar', match: { month: Number(calendarMonth) } };
      }
      if (calendarPreset === 'date_range') {
        return { provider: 'calendar', match: { date_range: { start: calendarDateStart, end: calendarDateEnd } } };
      }
    }
    if (provider === 'webhook') {
      return { provider: 'webhook', match: { [webhookKey]: webhookValue } };
    }
    return condition;
  }

  function emitChange() {
    onChange(buildCondition());
  }
</script>

<div class="single-condition">
  <div class="condition-header">
    <select bind:value={provider} onchange={emitChange} class="provider-select">
      <option value="">Select provider...</option>
      <option value="holiday">Holiday</option>
      <option value="weather">Weather</option>
      <option value="solar">Solar</option>
      <option value="time">Time</option>
      <option value="calendar">Calendar</option>
      <option value="webhook">Webhook</option>
    </select>
    {#if onRemove}
      <button class="remove-btn" onclick={onRemove} title="Remove condition">&times;</button>
    {/if}
  </div>

  {#if provider === 'holiday'}
    <div class="condition-fields">
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
    <div class="condition-fields">
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
          <label>{weatherPreset.includes('temp') ? 'Temperature (\u00b0F)' : 'Humidity (%)'}</label>
          <input type="number" bind:value={weatherValue} oninput={emitChange}
            placeholder={weatherPreset.includes('temp') ? '32' : '50'} />
        </div>
      {/if}
    </div>
  {/if}

  {#if provider === 'solar'}
    <div class="condition-fields">
      <div class="form-group">
        <label>When</label>
        <select bind:value={solarPreset} onchange={emitChange}>
          <option value="daytime">During daytime</option>
          <option value="after_sunset">After sunset</option>
          <option value="before_sunrise">Before sunrise</option>
        </select>
      </div>
      <div class="form-group">
        <label>Offset (minutes, negative = earlier)</label>
        <div class="offset-row">
          <input type="number" bind:value={solarOffsetMin} oninput={emitChange}
            placeholder="0" style="width: 80px;" />
          <span class="offset-hint">
            {#if solarOffsetMin < 0}
              {Math.abs(solarOffsetMin)}min earlier
            {:else if solarOffsetMin > 0}
              {solarOffsetMin}min later
            {:else}
              exact time
            {/if}
          </span>
        </div>
      </div>
    </div>
  {/if}

  {#if provider === 'time'}
    <div class="condition-fields">
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
            <label>End hour</label>
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

  {#if provider === 'calendar'}
    <div class="condition-fields">
      <div class="form-group">
        <label>When</label>
        <select bind:value={calendarPreset} onchange={emitChange}>
          <option value="season">During a season</option>
          <option value="month">During a month</option>
          <option value="date_range">Custom date range</option>
        </select>
      </div>
      {#if calendarPreset === 'season'}
        <div class="form-group">
          <label>Season</label>
          <select bind:value={calendarSeason} onchange={emitChange}>
            <option value="spring">Spring (Mar 20 – Jun 20)</option>
            <option value="summer">Summer (Jun 21 – Sep 21)</option>
            <option value="fall">Fall (Sep 22 – Dec 20)</option>
            <option value="winter">Winter (Dec 21 – Mar 19)</option>
          </select>
        </div>
      {/if}
      {#if calendarPreset === 'month'}
        <div class="form-group">
          <label>Month</label>
          <select bind:value={calendarMonth} onchange={emitChange}>
            <option value="1">January</option>
            <option value="2">February</option>
            <option value="3">March</option>
            <option value="4">April</option>
            <option value="5">May</option>
            <option value="6">June</option>
            <option value="7">July</option>
            <option value="8">August</option>
            <option value="9">September</option>
            <option value="10">October</option>
            <option value="11">November</option>
            <option value="12">December</option>
          </select>
        </div>
      {/if}
      {#if calendarPreset === 'date_range'}
        <div class="flex gap-2">
          <div class="form-group" style="flex:1">
            <label>Start (MM-DD)</label>
            <input type="text" bind:value={calendarDateStart} oninput={emitChange} placeholder="03-01" />
          </div>
          <div class="form-group" style="flex:1">
            <label>End (MM-DD)</label>
            <input type="text" bind:value={calendarDateEnd} oninput={emitChange} placeholder="05-31" />
          </div>
        </div>
      {/if}
    </div>
  {/if}

  {#if provider === 'webhook'}
    <div class="condition-fields">
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
</div>

<style>
  .single-condition {
    padding: 12px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: var(--radius);
    border: 1px solid var(--border);
  }
  .condition-header {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  .provider-select { flex: 1; }
  .remove-btn {
    width: 28px;
    height: 28px;
    padding: 0;
    font-size: 16px;
    line-height: 1;
    background: transparent;
    color: var(--text-muted);
    border: 1px solid var(--border);
    border-radius: 4px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
  }
  .remove-btn:hover { color: var(--error); border-color: var(--error); }
  .condition-fields { margin-top: 8px; }
  .offset-row { display: flex; align-items: center; gap: 8px; }
  .offset-hint { font-size: 0.85em; color: var(--text-muted); }
</style>
