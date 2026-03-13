# Huey Do It — Design Document (v2)

## Overview

A Dockerized local service that dynamically controls Philips Hue lights based on configurable rules driven by holidays, weather/temperature, sunrise/sunset, and arbitrary external data via webhooks. Runs on the same LAN as the Hue bridge. Provides a simple web UI for configuration and real-time monitoring.

## Goals

- Control individual Hue lights and grouped zones (color, brightness, on/off, transitions)
- Dynamically respond to multiple data sources (holidays, weather, solar, webhooks)
- Strict priority-based conflict resolution when multiple rules apply
- Bidirectional sync with the Hue bridge — external changes (physical switches, Hue app, Alexa) are detected and respected
- Easy to extend with new data providers without touching core logic
- Single `docker compose up` deployment

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Docker Container                                                │
│                                                                  │
│  ┌───────────┐  WebSocket   ┌──────────────┐   ┌─────────────┐  │
│  │  Web UI   │◀────────────▶│  Core Engine  │──▶│ Hue Bridge  │  │
│  │ (React)   │              │              │   │ Client (v2)  │  │
│  └───────────┘              │  ┌─────────┐ │   └──────┬───────┘  │
│                             │  │Scheduler│ │          │          │
│  ┌───────────┐              │  └─────────┘ │     Commands (PUT)  │
│  │ Webhook   │─────────────▶│              │          │          │
│  │ Endpoint  │              │  ┌─────────┐ │          ▼          │
│  └───────────┘              │  │ Rule    │ │   ┌─────────────┐   │
│                             │  │ Engine  │ │   │ Hue Bridge  │   │
│  ┌───────────┐              │  └─────────┘ │   │ (physical)  │   │
│  │ Providers │─────────────▶│              │   └──────┬───────┘  │
│  │ (plugins) │              └──────────────┘          │          │
│  └───────────┘                     ▲                  │          │
│                                    │           SSE Event Stream  │
│                                    └──────────────────┘          │
│                                                                  │
│                          LAN (host network / explicit IP)        │
└──────────────────────────────────────────────────────────────────┘
```

Key data flows:

- **Commands** flow from Engine → Bridge Client → Bridge via PUT requests
- **State changes** flow from Bridge → Bridge Client → Engine via SSE (Server-Sent Events), enabling real-time awareness of external changes (physical switches, Hue app, Alexa, etc.)
- **UI updates** flow from Engine → React UI via WebSocket, eliminating polling

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.12 | Best Hue library ecosystem (`aiohue`), strong async support, fast prototyping |
| Web framework | FastAPI | Async-native, WebSocket support, auto-generated API docs |
| Real-time UI | WebSocket (`/api/stream`) | Instant state propagation to frontend without polling |
| Web UI | React (Vite), multi-stage build | SPA served as static files from FastAPI, no Node.js in production image |
| Hue client | `aiohue` (v2 CLIP API) | Maintained, async, supports v2 natively including SSE event stream |
| Scheduler | APScheduler | Cron, interval, and one-shot scheduling in one library |
| Data store | SQLite via `aiosqlite` | Zero-config, single-file, sufficient for config + state |
| Container | Single Docker image, `network_mode: host` (Linux) or explicit bridge IP (Mac/Win) | See Docker section for cross-platform notes |

## Core Concepts

### Providers

A provider is a plugin that produces **state** — a structured blob of data that rules can reference. Each provider has its own update cadence and a **TTL** that defines how long its state is considered valid.

| Provider | Update Strategy | TTL | Source |
|----------|----------------|-----|--------|
| `holiday` | Cron (midnight daily) | 25h | Built-in calendar + configurable custom dates |
| `weather` | Polling (every 15 min) | 2h | OpenWeatherMap API (free tier) |
| `solar` | Cron (midnight daily) | 25h | `astral` library for configured lat/lon |
| `webhook` | Event-driven (HTTP POST) | Configurable per webhook | Arbitrary external systems push JSON |
| `time` | Implicit (always available) | N/A | Current time, day of week |

Adding a new provider means implementing a single Python class:

```python
class Provider(ABC):
    name: str

    @abstractmethod
    async def fetch(self) -> dict:
        """Return current state as a dict."""
        ...

    @abstractmethod
    def schedule(self) -> ScheduleConfig:
        """Return how/when this provider should be polled."""
        ...

    @abstractmethod
    def ttl(self) -> timedelta:
        """How long fetched state remains valid before expiring."""
        ...
```

#### Provider State & TTL

Provider state is cached in memory and persisted to SQLite so the engine can evaluate rules immediately on restart without waiting for the next fetch cycle. Each cached state carries a timestamp. If `now - last_fetch > ttl`, the state is marked **stale**:

- Rules referencing a stale provider are **skipped** during evaluation (fall through to the next priority level)
- Provider status page in the UI shows a warning
- Engine logs the staleness event

This prevents scenarios like 3-day-old weather data silently driving light decisions because an API went down.

### Rules

A rule maps provider state to light commands. Rules are evaluated top-down by priority (lower number = higher priority). First matching rule for a given light target wins.

```yaml
rules:
  - name: "Christmas Colors"
    priority: 10
    condition:
      provider: holiday
      match:
        active_holiday: "christmas"
    targets: ["window_1", "window_2", "window_3"]
    effect:
      mode: cycle
      colors: ["#ff0000", "#00ff00", "#ffffff"]
      cycle_interval: 30
      transition: 2000
      brightness: 80

  - name: "Hot Day (>90°F)"
    priority: 50
    condition:
      provider: weather
      match:
        temp_f:
          gte: 90
      deadband: 2
    targets: ["window_zone"]
    effect:
      mode: static
      colors: ["#0066ff"]
      brightness: 60

  - name: "Default Evening"
    priority: 100
    condition:
      provider: solar
      match:
        period: "after_sunset"
    targets: ["window_1", "window_2", "window_3"]
    effect:
      mode: static
      colors: ["#ffaa44"]
      brightness: 50
      transition: 5000

  - name: "System Default"
    priority: 9999
    condition:
      match: always
    targets: ["window_1", "window_2", "window_3"]
    effect:
      mode: "off"
```

#### Condition Matching

Conditions support:

- **Equality**: `active_holiday: "christmas"` — exact match
- **Comparison**: `temp_f: { gte: 90 }` — supports `gt`, `gte`, `lt`, `lte`
- **Set membership**: `day_of_week: { in: ["saturday", "sunday"] }`
- **Boolean AND**: multiple keys in `match` are ANDed
- **Boolean OR**: use `any_of: [...]` with a list of match blocks
- **Nested access**: `webhook.sports.team_score: { gte: 100 }` — dot-path into provider state
- **Always-true**: `match: always` — for catch-all/default rules

#### Hysteresis (Anti-Flapping)

Comparison-based rules support two mechanisms to prevent rapid toggling when values oscillate around a threshold:

**Deadband** (recommended, stateless): A numeric buffer that widens the deactivation threshold. A rule with `temp_f: { gte: 90 }, deadband: 2` activates at 90°F but won't deactivate until temp drops below 88°F. The engine tracks "was this rule active on the previous evaluation?" and applies the buffer when checking deactivation.

**Duration gate** (opt-in, stateful): `for: "15m"` requires the condition to remain continuously true for the specified duration before the rule activates. The engine tracks the first-true timestamp per rule and only fires after the duration elapses. Useful for noisy data sources.

Both can be combined on the same rule.

#### Conflict Resolution

When the engine evaluates:

1. Gather current state from all providers; skip any whose state is stale (past TTL)
2. Evaluate all enabled rules against current state, applying hysteresis
3. For each target (light or zone), collect all matching rules
4. Sort by priority (ascending — lower number wins)
5. Apply the first matching rule
6. If a manual override is active for that target (set via UI or detected from external change via SSE), skip rule evaluation for that target until the override expires or is cleared

**Explicit fallback**: The system enforces that at least one catch-all rule exists (e.g., `priority: 9999, match: always`). If no catch-all is configured, the system injects a default "off" rule at the lowest priority. Lights never end up in an undefined state.

### Light Targets

Targets can be **individual lights** or **Hue zones/rooms**:

```yaml
lights:
  window_1:
    type: light
    hue_id: "abc123-def456"
    friendly_name: "Left Window"
  window_2:
    type: light
    hue_id: "abc123-def789"
    friendly_name: "Center Window"
  window_3:
    type: light
    hue_id: "abc123-def012"
    friendly_name: "Right Window"

  window_zone:
    type: grouped_light
    hue_id: "group-abc123"
    friendly_name: "All Windows"
```

**Why zones matter**: Sending a command to a Hue `grouped_light` resource issues a single Zigbee broadcast/multicast. All lights in the zone change simultaneously. Looping over individual lights and sending sequential commands produces a visible "popcorn effect" where lights change milliseconds apart. Rules that target all window lights should prefer the zone target.

New lights and zones are added through the UI — the system queries the bridge for available lights, rooms, and zones.

## Hue Bridge Integration

### Pairing Flow

On first run (no stored credentials):

1. UI shows "Press the button on your Hue bridge, then click Pair"
2. Backend discovers bridge via mDNS (`zeroconf`) or falls back to `https://discovery.meethue.com/`, or uses explicit `HUE_BRIDGE_IP` if configured
3. Backend sends `POST /api` with `{"devicetype": "huey-do-it#docker", "generateclientkey": true}`
4. If bridge button wasn't pressed, returns link-button error — UI prompts retry
5. On success, stores `username` and `clientkey` in SQLite (encrypted at rest with a configurable secret)
6. Subsequent startups use stored credentials; re-pair only if bridge rejects them

### SSE Event Stream (Two-Way Sync)

The Hue v2 API pushes state changes via Server-Sent Events at `/eventstream/clip/v2`. The bridge client maintains a persistent async SSE listener that:

- Receives real-time state changes for all resources (lights, zones, sensors)
- Updates the in-memory light state cache
- Broadcasts changes to the UI via WebSocket
- Detects **external manual changes** (light toggled via physical switch, Hue app, Alexa, etc.)

When an external change is detected for a light currently under rule control:

1. Engine marks the light as having an **implicit manual override**
2. Override has a configurable timeout (default: 30 minutes) — after which rule evaluation resumes
3. UI shows the override with its source ("Changed externally") and expiry countdown
4. User can clear the override immediately from the UI

This prevents the system from fighting with someone who just walked over and turned a light off.

### Native Hue Effects (Not Server-Side)

Effects are **not driven by server-side polling loops**. The Hue v2 API supports native dynamics that run on the bridge/bulb firmware:

| Effect Type | Hue API Implementation |
|-------------|----------------------|
| `static` | Single `PUT` with color + brightness |
| `off` | Single `PUT` with `on: false` |
| `breathe` | `PUT` with `alert.action: "breathe"` — bridge firmware handles the pulse natively |
| `cycle` | `PUT` with `dynamics` object specifying color palette + duration — bridge firmware loops natively |
| `gradient` | For gradient-capable strips: `PUT` with `gradient.points` array. For separate bulbs: engine calculates color per bulb once and sends a single static command to each |

This eliminates continuous bridge traffic. The server sends one command to initiate an effect; the bridge sustains it independently.

### Command Batching

The Hue v2 API rate-limits to ~10 requests/second. The engine:

- Collects all pending state changes from a rule evaluation pass
- Deduplicates (skip if light is already in target state, known from SSE-fed cache)
- Prefers zone-level commands over individual light commands when all lights in a zone share the same target state
- Sends grouped PUT requests with throttling
- Logs failures, retries once after 1s

## Web UI

Single-page React app built via multi-stage Docker build and served as static files from FastAPI. Real-time updates via WebSocket — no polling.

### Real-Time Communication

**WebSocket endpoint**: `ws://{host}:{port}/api/stream`

The server broadcasts events to all connected UI clients:

- Light state changes (from rule evaluation or SSE bridge events)
- Provider state updates
- Rule activation/deactivation events
- Override creation/expiry
- Error events

The React app maintains a persistent WebSocket connection and updates component state reactively.

### Pages

**Dashboard** — Current state at a glance: each light shown with its current color/brightness, which rule is active, and provider states (current temp, active holiday, solar period). Manual override controls (color picker, brightness slider, on/off toggle) with optional expiration timer. Real-time updates via WebSocket.

**Rules** — List, create, edit, delete, reorder rules. Drag-and-drop priority ordering. Each rule shows its condition, target lights, and effect. Enable/disable toggle per rule. Live "matching now" indicator. **Dry-run tester**: submit a hypothetical rule and see whether it would match against current provider state.

**Lights** — Manage light and zone mappings. Add new lights/zones from bridge discovery. Rename, remove. Quick-test button to flash a light for identification. Shows real-time state including externally-triggered changes.

**Providers** — Status of each provider (last fetch time, TTL countdown, current state, staleness warnings, errors). Configure provider-specific settings (API keys, lat/lon for solar, webhook URLs). Manual "refresh now" button.

**Holidays** — Calendar view of configured holidays. Toggle US federal, cultural/religious presets. Add custom dates with name, date window, and associated color scheme. Import/export holiday configs.

**Logs** — Scrollable event log. Rule evaluations, provider fetches, Hue commands sent, SSE events received, errors.

### API Endpoints (FastAPI)

```
# Status & real-time
GET    /api/status              — dashboard state snapshot
WS     /api/stream              — WebSocket for real-time event stream

# Lights & zones
GET    /api/lights              — list configured lights and zones
POST   /api/lights              — add light or zone mapping
DELETE /api/lights/{name}       — remove target
POST   /api/lights/{name}/test  — flash for identification

# Rules
GET    /api/rules               — list rules
POST   /api/rules               — create rule
PUT    /api/rules/{id}          — update rule
DELETE /api/rules/{id}          — delete rule
PUT    /api/rules/reorder       — bulk priority update
POST   /api/rules/test          — dry-run: evaluate hypothetical rule against current state

# Providers
GET    /api/providers           — provider statuses (including TTL/staleness)
PUT    /api/providers/{name}    — update provider config
POST   /api/providers/{name}/refresh — force immediate fetch

# Webhooks
POST   /api/webhooks/{name}     — ingest external webhook data

# Overrides
POST   /api/override/{target}   — manual override (color, brightness, expiry)
DELETE /api/override/{target}   — clear override (manual or implicit)

# Holidays
GET    /api/holidays            — list holidays
POST   /api/holidays            — add custom holiday
DELETE /api/holidays/{id}       — remove holiday

# Bridge
POST   /api/bridge/pair         — initiate pairing flow
GET    /api/bridge/status       — bridge connection + SSE stream status

# Logs
GET    /api/logs                — recent event log (paginated)
```

## Data Model (SQLite)

```sql
-- Bridge credentials
CREATE TABLE bridge (
    id INTEGER PRIMARY KEY DEFAULT 1,
    host TEXT NOT NULL,
    username TEXT NOT NULL,
    clientkey TEXT,
    paired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Light and zone mappings
CREATE TABLE targets (
    name TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('light', 'grouped_light')),
    hue_id TEXT NOT NULL UNIQUE,
    friendly_name TEXT
);

-- Rules (stored as JSON for flexibility)
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    priority INTEGER NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    config JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Provider configs
CREATE TABLE provider_config (
    name TEXT PRIMARY KEY,
    config JSON NOT NULL,
    ttl_seconds INTEGER NOT NULL DEFAULT 7200,
    last_state JSON,
    last_fetch TIMESTAMP,
    error TEXT
);

-- Custom holidays
CREATE TABLE holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    window_start TEXT,
    window_end TEXT,
    recurring BOOLEAN DEFAULT TRUE,
    category TEXT DEFAULT 'custom',
    colors JSON,
    enabled BOOLEAN DEFAULT TRUE
);

-- Manual and implicit overrides
CREATE TABLE overrides (
    target_name TEXT PRIMARY KEY REFERENCES targets(name),
    source TEXT NOT NULL CHECK(source IN ('manual', 'external')),
    color TEXT,
    brightness INTEGER,
    on_state BOOLEAN,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hysteresis tracking
CREATE TABLE rule_state (
    rule_id INTEGER PRIMARY KEY REFERENCES rules(id),
    was_active BOOLEAN DEFAULT FALSE,
    condition_true_since TIMESTAMP,
    last_evaluated TIMESTAMP
);

-- Event log
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level TEXT NOT NULL,
    source TEXT NOT NULL,
    message TEXT NOT NULL,
    details JSON
);
```

## Docker Setup

### Cross-Platform Notes

**Linux (native Docker)**: `network_mode: host` works correctly. The container shares the host's network stack, enabling mDNS discovery of the Hue bridge.

**macOS / Windows (Docker Desktop)**: `host` networking bridges to Docker's lightweight VM, not the physical LAN. mDNS discovery will fail. Use the `HUE_BRIDGE_IP` environment variable to explicitly point to the bridge.

```yaml
# docker-compose.yml
services:
  huey-do-it:
    build: .
    network_mode: host
    restart: unless-stopped
    environment:
      - HUE_CONTROLLER_PORT=8080
      - OPENWEATHERMAP_API_KEY=${OPENWEATHERMAP_API_KEY}
      - LATITUDE=${LATITUDE}
      - LONGITUDE=${LONGITUDE}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - TZ=${TZ:-America/New_York}
      - HUE_BRIDGE_IP=${HUE_BRIDGE_IP:-}
      - EXTERNAL_OVERRIDE_TIMEOUT_MIN=${EXTERNAL_OVERRIDE_TIMEOUT_MIN:-30}
    volumes:
      - ./data:/app/data
```

### Multi-Stage Dockerfile

Node.js is used only at build time. The production image contains only Python and the compiled static assets.

```dockerfile
# Stage 1: Build React UI
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python image
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY --from=frontend-builder /frontend/dist ./app/static
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Project Structure

```
huey-do-it/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py                 # FastAPI app, startup/shutdown, WebSocket manager
│   ├── config.py               # env var loading, defaults
│   ├── database.py             # SQLite setup, migrations
│   ├── ws.py                   # WebSocket connection manager + broadcast
│   ├── bridge/
│   │   ├── client.py           # aiohue wrapper, command batching
│   │   ├── discovery.py        # mDNS + meethue.com fallback + explicit IP
│   │   ├── pairing.py          # button-press registration flow
│   │   ├── sse_listener.py     # SSE event stream consumer, external change detection
│   │   └── effects.py          # translate effect configs to Hue v2 native dynamics
│   ├── engine/
│   │   ├── evaluator.py        # rule evaluation, priority resolution, hysteresis
│   │   ├── scheduler.py        # APScheduler setup, provider orchestration
│   │   └── state.py            # in-memory state cache, staleness checks
│   ├── providers/
│   │   ├── base.py             # ABC for providers (fetch, schedule, ttl)
│   │   ├── holiday.py          # holiday calendar provider
│   │   ├── weather.py          # OpenWeatherMap provider
│   │   ├── solar.py            # sunrise/sunset via astral
│   │   ├── webhook.py          # arbitrary webhook ingest
│   │   └── time_provider.py    # current time/day
│   ├── api/
│   │   ├── routes.py           # REST endpoints
│   │   ├── ws_routes.py        # WebSocket endpoint
│   │   └── models.py           # Pydantic request/response models
│   └── holidays/
│       ├── us_federal.py
│       ├── cultural.py
│       └── loader.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── hooks/
│       │   └── useWebSocket.ts
│       ├── pages/
│       │   ├── Dashboard.tsx
│       │   ├── Rules.tsx
│       │   ├── Lights.tsx
│       │   ├── Providers.tsx
│       │   ├── Holidays.tsx
│       │   └── Logs.tsx
│       └── components/
│           ├── LightCard.tsx
│           ├── RuleEditor.tsx
│           ├── RuleTester.tsx
│           ├── ColorPicker.tsx
│           └── ProviderStatus.tsx
└── data/
    └── huey-do-it.db
```

## Update Propagation

Three mechanisms working together:

**Cron-scheduled** — Holiday provider runs at midnight. Solar provider recalculates at midnight. Both trigger rule re-evaluation immediately after.

**Polling** — Weather provider polls every 15 minutes (configurable). Each poll triggers rule re-evaluation only if state actually changed.

**Event-driven** — Webhook POSTs trigger immediate rule re-evaluation. Manual overrides via UI take effect immediately. Rule changes in UI trigger immediate re-evaluation. External light changes detected via SSE create implicit overrides.

No server-side heartbeat for effect cycling — effects are delegated to bridge firmware via native Hue v2 dynamics.

## Holiday System

### Built-in Calendars

**US Federal**: New Year's, MLK Day, Presidents' Day, Memorial Day, Juneteenth, Independence Day, Labor Day, Columbus Day, Veterans Day, Thanksgiving, Christmas. Computed dynamically (handles floating holidays like "third Monday of January").

**Cultural/Religious**: Hanukkah, Diwali, Lunar New Year, Easter, Eid al-Fitr, Eid al-Adha, etc. Uses `hijri-converter` and lunar calendar libraries for dates that shift yearly.

**Custom**: User-defined via UI. Fixed date (MM-DD, recurring) or specific date (YYYY-MM-DD, one-time).

Each holiday can define an activation **window** (e.g., Christmas activates Dec 20–26). Holidays can specify a default color scheme that rules can reference.

## Open Questions / Future Considerations

- **Multi-bridge support**: Currently assumes one bridge. Architecture doesn't preclude multiple, but not first-pass.
- **Scenes**: Could layer on Hue scene support (pre-configured on bridge) as an effect type.
- **Home Assistant integration**: Could expose as an MQTT device or HA add-on later.
- **Auth on the UI**: Currently no auth (local network assumed trusted). Could add basic auth or API key if needed.
- **Backup/restore**: Export/import of all config as a single JSON blob for migration.
- **Notification on provider failure**: Optional webhook/email alert when a provider goes stale, rather than silent fallthrough.
