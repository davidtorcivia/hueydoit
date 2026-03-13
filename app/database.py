import logging
from contextlib import asynccontextmanager

import aiosqlite

from app.config import settings

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS bridge (
    id INTEGER PRIMARY KEY DEFAULT 1,
    host TEXT NOT NULL,
    username TEXT NOT NULL,
    clientkey TEXT,
    paired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS targets (
    name TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('light', 'grouped_light')),
    hue_id TEXT NOT NULL UNIQUE,
    friendly_name TEXT
);

CREATE TABLE IF NOT EXISTS rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    priority INTEGER NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    config JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS provider_config (
    name TEXT PRIMARY KEY,
    config JSON NOT NULL DEFAULT '{}',
    ttl_seconds INTEGER NOT NULL DEFAULT 7200,
    last_state JSON,
    last_fetch TIMESTAMP,
    error TEXT
);

CREATE TABLE IF NOT EXISTS holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    window_start TEXT,
    window_end TEXT,
    recurring BOOLEAN DEFAULT 1,
    category TEXT DEFAULT 'custom',
    colors JSON,
    enabled BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS overrides (
    target_name TEXT PRIMARY KEY REFERENCES targets(name),
    source TEXT NOT NULL CHECK(source IN ('manual', 'external')),
    color TEXT,
    brightness INTEGER,
    on_state BOOLEAN,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rule_state (
    rule_id INTEGER PRIMARY KEY REFERENCES rules(id),
    was_active BOOLEAN DEFAULT 0,
    condition_true_since TIMESTAMP,
    last_evaluated TIMESTAMP
);

CREATE TABLE IF NOT EXISTS holiday_config (
    slug TEXT PRIMARY KEY,
    colors JSON,
    enabled BOOLEAN DEFAULT 1,
    window_before_days INTEGER,
    window_after_days INTEGER
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level TEXT NOT NULL,
    source TEXT NOT NULL,
    message TEXT NOT NULL,
    details JSON
);
"""


async def init_db():
    db_path = settings.db_path
    import os
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA)
        # Migrate: add window columns to holiday_config if missing
        cursor = await db.execute("PRAGMA table_info(holiday_config)")
        cols = {row[1] for row in await cursor.fetchall()}
        if "window_before_days" not in cols:
            await db.execute("ALTER TABLE holiday_config ADD COLUMN window_before_days INTEGER")
        if "window_after_days" not in cols:
            await db.execute("ALTER TABLE holiday_config ADD COLUMN window_after_days INTEGER")
        await db.commit()
    logger.info("Database initialized at %s", db_path)


@asynccontextmanager
async def get_db():
    db = await aiosqlite.connect(settings.db_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def add_log(level: str, source: str, message: str, details: dict | None = None):
    import json
    async with get_db() as db:
        await db.execute(
            "INSERT INTO logs (level, source, message, details) VALUES (?, ?, ?, ?)",
            (level, source, message, json.dumps(details) if details else None),
        )
        await db.commit()
