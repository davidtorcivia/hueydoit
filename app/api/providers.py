import json
from datetime import timedelta

from fastapi import APIRouter, HTTPException

from app.api.models import ProviderConfigUpdate
from app.database import get_db, add_log
from app.engine.state import state_manager
from app.engine.scheduler import engine_scheduler

router = APIRouter(prefix="/api")


@router.get("/providers")
async def list_providers():
    results = []
    for pname in ["holiday", "weather", "solar", "time", "calendar", "webhook"]:
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


@router.post("/webhooks/{name}")
async def ingest_webhook(name: str, payload: dict):
    wp = engine_scheduler.get_webhook_provider()
    if wp:
        await wp.ingest(name, payload)
        await engine_scheduler.trigger_evaluation()
    await add_log("info", "webhook", f"Webhook received: {name}", payload)
    return {"received": name}
