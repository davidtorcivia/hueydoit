from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from app.api.models import OverrideCreate
from app.database import get_db, add_log
from app.engine.state import state_manager
from app.engine.scheduler import engine_scheduler
from app.bridge.client import bridge_client
from app.ws import ws_manager

router = APIRouter(prefix="/api")


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
