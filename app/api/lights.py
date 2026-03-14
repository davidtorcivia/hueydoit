from fastapi import APIRouter, HTTPException

from app.api.models import LightTargetCreate
from app.database import get_db, add_log
from app.engine.state import state_manager
from app.bridge.client import bridge_client

router = APIRouter(prefix="/api")


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
