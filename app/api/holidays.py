import json

from fastapi import APIRouter, HTTPException

from app.api.models import HolidayCreate, HolidayConfigUpdate
from app.database import get_db, add_log
from app.engine.scheduler import engine_scheduler

router = APIRouter(prefix="/api")


@router.get("/holidays")
async def list_holidays():
    from app.holidays.loader import load_all_holidays
    from datetime import date as date_type

    today = date_type.today()
    holidays = await load_all_holidays(today.year)
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
            "priority": h.priority,
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
            if config.priority is not None:
                updates.append("priority = ?")
                params.append(config.priority)
            if updates:
                params.append(slug)
                await db.execute(
                    f"UPDATE holiday_config SET {', '.join(updates)} WHERE slug = ?", params
                )
        else:
            await db.execute(
                "INSERT INTO holiday_config (slug, colors, enabled, window_before_days, window_after_days, priority) VALUES (?, ?, ?, ?, ?, ?)",
                (slug, colors_json, config.enabled if config.enabled is not None else True,
                 config.window_before_days, config.window_after_days, config.priority),
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
