import json
import logging
from contextlib import asynccontextmanager

import aiosqlite

from app.config import settings

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

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
    overridden_rule_id INTEGER,
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
    window_after_days INTEGER,
    priority INTEGER
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

# Versioned migrations — each entry is (version, list_of_sql_statements).
# Add new migrations at the end with the next version number.
MIGRATIONS: list[tuple[int, list[str]]] = [
    (1, [
        "ALTER TABLE holiday_config ADD COLUMN window_before_days INTEGER",
        "ALTER TABLE holiday_config ADD COLUMN window_after_days INTEGER",
    ]),
    (2, [
        "ALTER TABLE holiday_config ADD COLUMN priority INTEGER",
    ]),
    (3, [
        "ALTER TABLE overrides ADD COLUMN overridden_rule_id INTEGER",
    ]),
]


async def _get_schema_version(db: aiosqlite.Connection) -> int:
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if not await cursor.fetchone():
        return 0
    cursor = await db.execute("SELECT MAX(version) FROM schema_version")
    row = await cursor.fetchone()
    return row[0] if row and row[0] else 0


async def _run_migrations(db: aiosqlite.Connection):
    current = await _get_schema_version(db)
    for version, statements in MIGRATIONS:
        if version <= current:
            continue
        for sql in statements:
            try:
                await db.execute(sql)
            except Exception as e:
                # Column already exists etc. — safe to skip
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    logger.debug("Migration %d skipped (already applied): %s", version, e)
                else:
                    raise
        await db.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (version,))
        logger.info("Applied migration %d", version)
    await db.commit()


async def init_db():
    db_path = settings.db_path
    import os
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA)
        await _run_migrations(db)
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
    async with get_db() as db:
        await db.execute(
            "INSERT INTO logs (level, source, message, details) VALUES (?, ?, ?, ?)",
            (level, source, message, json.dumps(details) if details else None),
        )
        await db.commit()
