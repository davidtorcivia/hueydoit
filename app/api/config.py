"""Export and import the whole controller configuration as one JSON document.

Rules, targets and holiday overrides live only in SQLite, so the repository
cannot reproduce a working install and rule edits have no history. This gives a
single portable snapshot that can be committed, diffed and restored.

Bridge credentials are deliberately excluded — the export is meant to be safe to
commit to a repository.
"""
import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import add_log, get_db
from app.engine.scheduler import engine_scheduler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

CONFIG_VERSION = 1


class ConfigImport(BaseModel):
    config: dict
    replace: bool = False


def _loads(raw):
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None
    return raw


@router.get("/config/export")
async def export_config():
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT name, priority, enabled, config FROM rules ORDER BY priority, id"
        )
        rules = [
            {
                "name": r[0],
                "priority": r[1],
                "enabled": bool(r[2]),
                "config": _loads(r[3]),
            }
            for r in await cursor.fetchall()
        ]

        cursor = await db.execute(
            "SELECT name, type, hue_id, friendly_name FROM targets ORDER BY name"
        )
        targets = [
            {"name": r[0], "type": r[1], "hue_id": r[2], "friendly_name": r[3]}
            for r in await cursor.fetchall()
        ]

        cursor = await db.execute(
            "SELECT slug, colors, enabled, window_before_days, window_after_days, priority "
            "FROM holiday_config ORDER BY slug"
        )
        holiday_config = [
            {
                "slug": r[0],
                "colors": _loads(r[1]),
                "enabled": bool(r[2]),
                "window_before_days": r[3],
                "window_after_days": r[4],
                "priority": r[5],
            }
            for r in await cursor.fetchall()
        ]

        cursor = await db.execute(
            "SELECT name, date, window_start, window_end, recurring, category, colors, enabled "
            "FROM holidays ORDER BY date"
        )
        custom_holidays = [
            {
                "name": r[0],
                "date": r[1],
                "window_start": r[2],
                "window_end": r[3],
                "recurring": bool(r[4]),
                "category": r[5],
                "colors": _loads(r[6]),
                "enabled": bool(r[7]),
            }
            for r in await cursor.fetchall()
        ]

        # Provider tuning only — never last_state, and never bridge credentials.
        cursor = await db.execute("SELECT name, config, ttl_seconds FROM provider_config ORDER BY name")
        providers = [
            {"name": r[0], "config": _loads(r[1]), "ttl_seconds": r[2]}
            for r in await cursor.fetchall()
        ]

    return {
        "version": CONFIG_VERSION,
        "rules": rules,
        "targets": targets,
        "holiday_config": holiday_config,
        "custom_holidays": custom_holidays,
        "providers": providers,
    }


@router.post("/config/import")
async def import_config(payload: ConfigImport):
    """Apply an exported config.

    replace=False (default) merges: rules are matched by name and updated in
    place, anything new is added, nothing is deleted.
    replace=True clears rules, holiday overrides and custom holidays first.

    Targets are matched on hue_id and never deleted, since they are tied to
    physical lights on the bridge.
    """
    cfg = payload.config
    if not isinstance(cfg, dict):
        raise HTTPException(400, "config must be an object")
    if cfg.get("version") != CONFIG_VERSION:
        raise HTTPException(
            400, f"Unsupported config version {cfg.get('version')!r}, expected {CONFIG_VERSION}"
        )

    counts = {"rules": 0, "targets": 0, "holiday_config": 0, "custom_holidays": 0, "providers": 0}

    async with get_db() as db:
        if payload.replace:
            await db.execute("DELETE FROM rules")
            await db.execute("DELETE FROM holiday_config")
            await db.execute("DELETE FROM holidays")

        for rule in cfg.get("rules", []) or []:
            name = rule.get("name")
            config = rule.get("config")
            if not name or not isinstance(config, dict):
                continue
            config_json = json.dumps(config)
            priority = int(rule.get("priority", 50))
            enabled = bool(rule.get("enabled", True))

            cursor = await db.execute("SELECT id FROM rules WHERE name = ?", (name,))
            existing = await cursor.fetchone()
            if existing:
                await db.execute(
                    "UPDATE rules SET priority = ?, enabled = ?, config = ?, "
                    "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (priority, enabled, config_json, existing[0]),
                )
            else:
                await db.execute(
                    "INSERT INTO rules (name, priority, enabled, config) VALUES (?, ?, ?, ?)",
                    (name, priority, enabled, config_json),
                )
            counts["rules"] += 1

        for t in cfg.get("targets", []) or []:
            if not t.get("name") or not t.get("hue_id"):
                continue
            await db.execute(
                "INSERT INTO targets (name, type, hue_id, friendly_name) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(hue_id) DO UPDATE SET friendly_name = excluded.friendly_name",
                (t["name"], t.get("type", "light"), t["hue_id"], t.get("friendly_name")),
            )
            counts["targets"] += 1

        for hc in cfg.get("holiday_config", []) or []:
            if not hc.get("slug"):
                continue
            colors = hc.get("colors")
            await db.execute(
                "INSERT INTO holiday_config "
                "(slug, colors, enabled, window_before_days, window_after_days, priority) "
                "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(slug) DO UPDATE SET "
                "colors = excluded.colors, enabled = excluded.enabled, "
                "window_before_days = excluded.window_before_days, "
                "window_after_days = excluded.window_after_days, priority = excluded.priority",
                (
                    hc["slug"],
                    json.dumps(colors) if colors else None,
                    bool(hc.get("enabled", True)),
                    hc.get("window_before_days"),
                    hc.get("window_after_days"),
                    hc.get("priority"),
                ),
            )
            counts["holiday_config"] += 1

        for h in cfg.get("custom_holidays", []) or []:
            if not h.get("name") or not h.get("date"):
                continue
            await db.execute(
                "INSERT INTO holidays "
                "(name, date, window_start, window_end, recurring, category, colors, enabled) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    h["name"], h["date"], h.get("window_start"), h.get("window_end"),
                    bool(h.get("recurring", True)), h.get("category", "custom"),
                    json.dumps(h.get("colors")) if h.get("colors") else None,
                    bool(h.get("enabled", True)),
                ),
            )
            counts["custom_holidays"] += 1

        for p in cfg.get("providers", []) or []:
            if not p.get("name"):
                continue
            await db.execute(
                "INSERT INTO provider_config (name, config, ttl_seconds) VALUES (?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET config = excluded.config, "
                "ttl_seconds = excluded.ttl_seconds",
                (p["name"], json.dumps(p.get("config") or {}), int(p.get("ttl_seconds", 7200))),
            )
            counts["providers"] += 1

        await db.commit()

    await add_log("info", "api", f"Imported config (replace={payload.replace})", counts)
    await engine_scheduler.trigger_evaluation()
    return {"imported": counts, "replace": payload.replace}
