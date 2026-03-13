import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.api.models import (
    LightTargetCreate,
    LightTargetResponse,
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    ReorderRequest,
    RuleTestRequest,
    RuleTestResponse,
    OverrideCreate,
    HolidayCreate,
    HolidayResponse,
    HolidayConfigUpdate,
    ProviderStatus,
    ProviderConfigUpdate,
    BridgeStatus,
    DashboardStatus,
    LogEntry,
)
from app.database import get_db, add_log
from app.engine.state import state_manager
from app.engine.evaluator import evaluator
from app.engine.scheduler import engine_scheduler
from app.bridge.client import bridge_client
from app.bridge.discovery import discover_bridge
from app.bridge.pairing import pair_bridge, get_stored_credentials, LinkButtonNotPressed
from app.ws import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# --- Status ---
@router.get("/status")
async def get_status():
    async with get_db() as db:
        cursor = await db.execute("SELECT name, type, hue_id, friendly_name FROM targets")
        target_rows = await cursor.fetchall()

    lights = []
    for row in target_rows:
        name = row[0]
        lights.append({
            "name": name,
            "type": row[1],
            "hue_id": row[2],
            "friendly_name": row[3],
            "state": state_manager.get_light_state(name),
            "active_rule": state_manager.get_active_rule(name),
            "override": await state_manager.get_override(name),
        })

    providers = []
    async with get_db() as db:
        cursor = await db.execute("SELECT name, config, ttl_seconds, last_fetch, error FROM provider_config")
        prows = await cursor.fetchall()
    for row in prows:
        pname = row[0]
        provider = engine_scheduler.get_provider(pname)
        ttl_sec = row[2]
        is_stale = state_manager.is_stale(pname, timedelta(seconds=ttl_sec)) if provider else True
        providers.append({
            "name": pname,
            "last_fetch": row[3],
            "ttl_seconds": ttl_sec,
            "is_stale": is_stale,
            "current_state": state_manager.get_provider_state(pname),
            "error": row[4],
        })

    if not prows:
        for pname in ["holiday", "weather", "solar", "time", "webhook"]:
            provider = engine_scheduler.get_provider(pname)
            ttl_sec = int(provider.ttl().total_seconds()) if provider else 7200
            providers.append({
                "name": pname,
                "last_fetch": state_manager.get_provider_timestamp(pname).isoformat()
                if state_manager.get_provider_timestamp(pname)
                else None,
                "ttl_seconds": ttl_sec,
                "is_stale": state_manager.is_stale(pname, timedelta(seconds=ttl_sec)),
                "current_state": state_manager.get_provider_state(pname),
                "error": None,
            })

    return {
        "lights": lights,
        "providers": providers,
        "active_rules": {t: state_manager.get_active_rule(t) for t in [r[0] for r in target_rows]},
        "overrides": await state_manager.get_all_overrides(),
        "bridge_connected": bridge_client.connected,
    }


# --- Lights ---
@router.get("/lights")
async def list_lights():
    async with get_db() as db:
        cursor = await db.execute("SELECT name, type, hue_id, friendly_name FROM targets")
        rows = await cursor.fetchall()
    return [
        {
            "name": row[0],
            "type": row[1],
            "hue_id": row[2],
            "friendly_name": row[3],
            "state": state_manager.get_light_state(row[0]),
            "active_rule": state_manager.get_active_rule(row[0]),
            "override": await state_manager.get_override(row[0]),
        }
        for row in rows
    ]


@router.post("/lights", status_code=201)
async def add_light(target: LightTargetCreate):
    async with get_db() as db:
        try:
            await db.execute(
                "INSERT INTO targets (name, type, hue_id, friendly_name) VALUES (?, ?, ?, ?)",
                (target.name, target.type, target.hue_id, target.friendly_name),
            )
            await db.commit()
        except Exception as e:
            raise HTTPException(400, f"Failed to add target: {e}")
    await add_log("info", "api", f"Added light target: {target.name}")
    return {"name": target.name, "type": target.type, "hue_id": target.hue_id}


@router.delete("/lights/{name}")
async def remove_light(name: str):
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM targets WHERE name = ?", (name,))
        if cursor.rowcount == 0:
            raise HTTPException(404, "Target not found")
        await db.execute("DELETE FROM overrides WHERE target_name = ?", (name,))
        await db.commit()
    await add_log("info", "api", f"Removed light target: {name}")
    return {"deleted": name}


@router.post("/lights/{name}/test")
async def test_light(name: str):
    async with get_db() as db:
        cursor = await db.execute("SELECT hue_id FROM targets WHERE name = ?", (name,))
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(404, "Target not found")
    if bridge_client.connected:
        await bridge_client.identify_light(row[0])
    return {"identified": name}


@router.get("/lights/bridge")
async def get_bridge_lights():
    if not bridge_client.connected:
        raise HTTPException(503, "Bridge not connected")
    lights = await bridge_client.get_lights()
    groups = await bridge_client.get_groups()
    return {"lights": lights, "groups": groups}


# --- Rules ---
@router.get("/rules")
async def list_rules():
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, name, priority, enabled, config, created_at, updated_at FROM rules ORDER BY priority ASC"
        )
        rows = await cursor.fetchall()
    return [
        {
            "id": row[0],
            "name": row[1],
            "priority": row[2],
            "enabled": bool(row[3]),
            "config": json.loads(row[4]) if isinstance(row[4], str) else row[4],
            "created_at": row[5],
            "updated_at": row[6],
        }
        for row in rows
    ]


@router.post("/rules", status_code=201)
async def create_rule(rule: RuleCreate):
    config_json = json.dumps(rule.config.model_dump())
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO rules (name, priority, enabled, config) VALUES (?, ?, ?, ?)",
            (rule.name, rule.priority, rule.enabled, config_json),
        )
        rule_id = cursor.lastrowid
        await db.commit()
    await add_log("info", "api", f"Created rule: {rule.name}")
    await engine_scheduler.trigger_evaluation()
    return {"id": rule_id, "name": rule.name}


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: int, rule: RuleUpdate):
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM rules WHERE id = ?", (rule_id,))
        if not await cursor.fetchone():
            raise HTTPException(404, "Rule not found")

        updates = []
        params = []
        if rule.name is not None:
            updates.append("name = ?")
            params.append(rule.name)
        if rule.priority is not None:
            updates.append("priority = ?")
            params.append(rule.priority)
        if rule.enabled is not None:
            updates.append("enabled = ?")
            params.append(rule.enabled)
        if rule.config is not None:
            updates.append("config = ?")
            params.append(json.dumps(rule.config.model_dump()))
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(rule_id)

        await db.execute(
            f"UPDATE rules SET {', '.join(updates)} WHERE id = ?", params
        )
        await db.commit()
    await add_log("info", "api", f"Updated rule {rule_id}")
    await engine_scheduler.trigger_evaluation()
    return {"updated": rule_id}


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int):
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
        if cursor.rowcount == 0:
            raise HTTPException(404, "Rule not found")
        await db.execute("DELETE FROM rule_state WHERE rule_id = ?", (rule_id,))
        await db.commit()
    await add_log("info", "api", f"Deleted rule {rule_id}")
    await engine_scheduler.trigger_evaluation()
    return {"deleted": rule_id}


@router.put("/rules/reorder")
async def reorder_rules(request: ReorderRequest):
    async with get_db() as db:
        for item in request.rules:
            await db.execute(
                "UPDATE rules SET priority = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (item.priority, item.id),
            )
        await db.commit()
    await add_log("info", "api", "Rules reordered")
    await engine_scheduler.trigger_evaluation()
    return {"reordered": len(request.rules)}


@router.post("/rules/test")
async def test_rule(request: RuleTestRequest):
    provider_states = state_manager.get_all_provider_states()
    would_match = evaluator._match_condition(request.condition, provider_states)
    return {"would_match": would_match, "current_state": provider_states}


# --- Providers ---
@router.get("/providers")
async def list_providers():
    results = []
    for pname in ["holiday", "weather", "solar", "time", "webhook"]:
        provider = engine_scheduler.get_provider(pname)
        ttl_sec = int(provider.ttl().total_seconds()) if provider else 7200
        ts = state_manager.get_provider_timestamp(pname)

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT config, error FROM provider_config WHERE name = ?", (pname,)
            )
            row = await cursor.fetchone()

        results.append({
            "name": pname,
            "last_fetch": ts.isoformat() if ts else None,
            "ttl_seconds": ttl_sec,
            "is_stale": state_manager.is_stale(pname, timedelta(seconds=ttl_sec)),
            "current_state": state_manager.get_provider_state(pname),
            "error": row[1] if row else None,
            "config": json.loads(row[0]) if row and row[0] else {},
        })
    return results


@router.put("/providers/{name}")
async def update_provider_config(name: str, config: ProviderConfigUpdate):
    async with get_db() as db:
        await db.execute(
            """INSERT INTO provider_config (name, config, ttl_seconds)
               VALUES (?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET config=excluded.config, ttl_seconds=COALESCE(excluded.ttl_seconds, ttl_seconds)""",
            (name, json.dumps(config.config), config.ttl_seconds or 7200),
        )
        await db.commit()
    return {"updated": name}


@router.post("/providers/{name}/refresh")
async def refresh_provider(name: str):
    try:
        await engine_scheduler.refresh_provider(name)
    except ValueError:
        raise HTTPException(404, f"Unknown provider: {name}")
    return {"refreshed": name}


# --- Webhooks ---
@router.post("/webhooks/{name}")
async def ingest_webhook(name: str, payload: dict):
    wp = engine_scheduler.get_webhook_provider()
    if wp:
        await wp.ingest(name, payload)
        await engine_scheduler.trigger_evaluation()
    await add_log("info", "webhook", f"Webhook received: {name}", payload)
    return {"received": name}


# --- Overrides ---
@router.post("/override/{target}")
async def set_override(target: str, override: OverrideCreate):
    async with get_db() as db:
        cursor = await db.execute("SELECT name FROM targets WHERE name = ?", (target,))
        if not await cursor.fetchone():
            raise HTTPException(404, "Target not found")

    expires_at = None
    if override.expires_minutes:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=override.expires_minutes)

    await state_manager.set_override(
        target,
        source="manual",
        color=override.color,
        brightness=override.brightness,
        on_state=override.on_state,
        expires_at=expires_at,
    )

    if bridge_client.connected:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT type, hue_id FROM targets WHERE name = ?", (target,)
            )
            row = await cursor.fetchone()
        if row:
            from app.bridge.effects import build_light_command

            if override.on_state is False:
                cmd = {"on": {"on": False}}
            else:
                effect = {"mode": "static"}
                if override.color:
                    effect["colors"] = [override.color]
                if override.brightness is not None:
                    effect["brightness"] = override.brightness
                cmd = build_light_command(effect, row[0])
            await bridge_client.set_light_state(row[0], row[1], cmd)

    await ws_manager.broadcast("override_created", {
        "target": target,
        "source": "manual",
        "override": {
            "color": override.color,
            "brightness": override.brightness,
            "on_state": override.on_state,
            "expires_at": expires_at.isoformat() if expires_at else None,
        },
    })
    await add_log("info", "api", f"Manual override set for {target}")
    return {"override_set": target}


@router.delete("/override/{target}")
async def clear_override(target: str):
    await state_manager.clear_override(target)
    await ws_manager.broadcast("override_cleared", {"target": target})
    await add_log("info", "api", f"Override cleared for {target}")
    await engine_scheduler.trigger_evaluation()
    return {"override_cleared": target}


# --- Holidays ---
@router.get("/holidays")
async def list_holidays():
    from app.holidays.loader import load_all_holidays
    from datetime import date as date_type

    today = date_type.today()
    holidays = await load_all_holidays(today.year)
    # Load window overrides for display
    window_overrides = {}
    async with get_db() as db:
        cursor = await db.execute("SELECT slug, window_before_days, window_after_days FROM holiday_config")
        for row in await cursor.fetchall():
            window_overrides[row[0]] = {
                "window_before_days": row[1],
                "window_after_days": row[2],
            }

    return [
        {
            "name": h.name,
            "slug": h.slug,
            "date": h.date.isoformat(),
            "window_start": h.window_start.isoformat(),
            "window_end": h.window_end.isoformat(),
            "colors": h.colors,
            "category": h.category,
            "recurring": h.recurring,
            "enabled": h.enabled,
            "window_before_days": window_overrides.get(h.slug, {}).get("window_before_days"),
            "window_after_days": window_overrides.get(h.slug, {}).get("window_after_days"),
        }
        for h in holidays
    ]


@router.post("/holidays", status_code=201)
async def add_holiday(holiday: HolidayCreate):
    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO holidays (name, date, window_start, window_end, recurring, category, colors, enabled)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                holiday.name,
                holiday.date,
                holiday.window_start,
                holiday.window_end,
                holiday.recurring,
                holiday.category,
                json.dumps(holiday.colors),
                holiday.enabled,
            ),
        )
        holiday_id = cursor.lastrowid
        await db.commit()
    await add_log("info", "api", f"Added holiday: {holiday.name}")
    await engine_scheduler.refresh_provider("holiday")
    return {"id": holiday_id, "name": holiday.name}


@router.put("/holidays/{slug}/config")
async def update_holiday_config(slug: str, config: HolidayConfigUpdate):
    async with get_db() as db:
        colors_json = json.dumps(config.colors) if config.colors is not None else None
        # Check if override exists
        cursor = await db.execute("SELECT slug FROM holiday_config WHERE slug = ?", (slug,))
        existing = await cursor.fetchone()
        if existing:
            updates = []
            params = []
            if config.colors is not None:
                updates.append("colors = ?")
                params.append(colors_json)
            if config.enabled is not None:
                updates.append("enabled = ?")
                params.append(config.enabled)
            if config.window_before_days is not None:
                updates.append("window_before_days = ?")
                params.append(config.window_before_days)
            if config.window_after_days is not None:
                updates.append("window_after_days = ?")
                params.append(config.window_after_days)
            if updates:
                params.append(slug)
                await db.execute(
                    f"UPDATE holiday_config SET {', '.join(updates)} WHERE slug = ?", params
                )
        else:
            await db.execute(
                "INSERT INTO holiday_config (slug, colors, enabled, window_before_days, window_after_days) VALUES (?, ?, ?, ?, ?)",
                (slug, colors_json, config.enabled if config.enabled is not None else True,
                 config.window_before_days, config.window_after_days),
            )
        await db.commit()
    await add_log("info", "api", f"Updated holiday config for {slug}")
    await engine_scheduler.refresh_provider("holiday")
    return {"updated": slug}


@router.delete("/holidays/{holiday_id}")
async def remove_holiday(holiday_id: int):
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM holidays WHERE id = ? AND category = 'custom'", (holiday_id,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(404, "Holiday not found or not a custom holiday")
        await db.commit()
    await add_log("info", "api", f"Removed holiday {holiday_id}")
    await engine_scheduler.refresh_provider("holiday")
    return {"deleted": holiday_id}


# --- Bridge ---
@router.post("/bridge/pair")
async def pair_bridge_endpoint():
    try:
        if bridge_client.host:
            host = bridge_client.host
        else:
            host = await discover_bridge()
        result = await pair_bridge(host)
        await bridge_client.connect_with_credentials(host, result["username"])
        await add_log("info", "bridge", f"Paired with bridge at {host}")
        return {"paired": True, "host": host}
    except LinkButtonNotPressed:
        raise HTTPException(428, "Press the link button on the Hue bridge first")
    except Exception as e:
        raise HTTPException(500, f"Pairing failed: {e}")


@router.get("/bridge/status")
async def bridge_status():
    creds = await get_stored_credentials()
    return {
        "connected": bridge_client.connected,
        "host": bridge_client.host,
        "paired": creds is not None,
    }


# --- Logs ---
@router.get("/logs")
async def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    level: str | None = None,
    source: str | None = None,
):
    query = "SELECT id, timestamp, level, source, message, details FROM logs"
    params: list = []
    conditions = []

    if level:
        conditions.append("level = ?")
        params.append(level)
    if source:
        conditions.append("source LIKE ?")
        params.append(f"%{source}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    async with get_db() as db:
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "level": row[2],
            "source": row[3],
            "message": row[4],
            "details": json.loads(row[5]) if row[5] else None,
        }
        for row in rows
    ]
