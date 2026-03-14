import json
from datetime import timedelta

from fastapi import APIRouter

from app.database import get_db
from app.engine.state import state_manager
from app.engine.scheduler import engine_scheduler
from app.bridge.client import bridge_client

router = APIRouter(prefix="/api")


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
        for pname in ["holiday", "weather", "solar", "time", "calendar", "webhook"]:
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
