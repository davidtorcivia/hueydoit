import json

from fastapi import APIRouter, HTTPException

from app.api.models import RuleCreate, RuleUpdate, ReorderRequest, RuleTestRequest
from app.database import get_db, add_log
from app.engine.state import state_manager
from app.engine.evaluator import evaluator
from app.engine.scheduler import engine_scheduler

router = APIRouter(prefix="/api")


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
    state_manager.clear_hysteresis(rule_id)
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


@router.post("/rules/{rule_id}/trigger")
async def trigger_rule(rule_id: int, minutes: int = 30):
    """Force-apply a rule's effect to its targets, bypassing condition checks.
    Creates temporary overrides so the evaluator doesn't undo it."""
    from datetime import datetime, timedelta, timezone

    async with get_db() as db:
        cursor = await db.execute("SELECT name, config FROM rules WHERE id = ?", (rule_id,))
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(404, "Rule not found")

    rule_name = row[0]
    try:
        config = json.loads(row[1]) if isinstance(row[1], str) else row[1]
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(400, "Invalid rule config")

    effect = dict(config.get("effect", {}))
    rule_targets = config.get("targets", [])

    # Resolve holiday colors if needed
    if effect.get("use_holiday_colors"):
        holiday_state = state_manager.get_provider_state("holiday") or {}
        active_colors = holiday_state.get("active_colors", [])
        if active_colors:
            effect["colors"] = active_colors

    from app.bridge.client import bridge_client
    from app.bridge.effects import build_light_command

    async with get_db() as db:
        cursor = await db.execute("SELECT name, type, hue_id FROM targets")
        all_targets = {r[0]: {"type": r[1], "hue_id": r[2]} for r in await cursor.fetchall()}

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    applied = []

    for i, target_name in enumerate(rule_targets):
        if target_name not in all_targets:
            continue
        target_info = all_targets[target_name]
        t_effect = dict(effect)

        # Per-light color distribution for holiday colors
        colors = t_effect.get("colors", [])
        if len(colors) > 1 and len(rule_targets) > 1:
            t_effect["colors"] = [colors[i % len(colors)]]

        # Per-light color/brightness map
        color_map = t_effect.pop("color_map", None)
        if color_map and target_name in color_map:
            t_effect["colors"] = [color_map[target_name]]
        brightness_map = t_effect.pop("brightness_map", None)
        if brightness_map and target_name in brightness_map:
            t_effect["brightness"] = brightness_map[target_name]

        cmd = build_light_command(t_effect, target_info["type"])
        if bridge_client.connected:
            await bridge_client.set_light_state(target_info["type"], target_info["hue_id"], cmd)

        # Create override so the evaluator doesn't undo the trigger
        resolved_color = t_effect.get("colors", [None])[0] if t_effect.get("colors") else None
        on_state = t_effect.get("mode") != "off"
        await state_manager.set_override(
            target_name,
            source="manual",
            color=resolved_color,
            brightness=t_effect.get("brightness"),
            on_state=on_state,
            expires_at=expires_at,
        )
        applied.append(target_name)

    # Register breathing targets if this is a breathe rule
    if effect.get("mode") == "breathe":
        breathing = state_manager.get_breathing_targets()
        for target_name in applied:
            if target_name in all_targets:
                t = all_targets[target_name]
                breathing[target_name] = {
                    "type": t["type"],
                    "hue_id": t["hue_id"],
                    "brightness": effect.get("brightness", 80),
                    "transition": effect.get("transition", 4000),
                }
        state_manager.set_breathing_targets(breathing)

    await add_log("info", "api", f"Manually triggered rule '{rule_name}' on {len(applied)} targets ({minutes}m)")
    return {"triggered": rule_id, "rule_name": rule_name, "targets_applied": applied, "expires_minutes": minutes}


@router.post("/rules/test")
async def test_rule(request: RuleTestRequest):
    provider_states = state_manager.get_all_provider_states()
    would_match = evaluator._match_condition(request.condition, provider_states)
    return {"would_match": would_match, "current_state": provider_states}
