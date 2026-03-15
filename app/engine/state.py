import json
import logging
from datetime import datetime, timedelta, timezone

from app.database import get_db

logger = logging.getLogger(__name__)


class StateManager:
    def __init__(self):
        self._provider_states: dict[str, dict] = {}
        self._provider_timestamps: dict[str, datetime] = {}
        self._light_states: dict[str, dict] = {}
        self._active_rules: dict[str, dict | None] = {}
        self._overrides: dict[str, dict] = {}
        self._rule_hysteresis: dict[int, dict] = {}
        self._breathing_targets: dict[str, dict] = {}  # target_name -> {type, hue_id}

    async def load_from_db(self):
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT name, last_state, last_fetch FROM provider_config WHERE last_state IS NOT NULL"
            )
            rows = await cursor.fetchall()
            for row in rows:
                name = row[0]
                try:
                    state = json.loads(row[1]) if row[1] else {}
                    self._provider_states[name] = state
                    if row[2]:
                        self._provider_timestamps[name] = datetime.fromisoformat(row[2]).replace(
                            tzinfo=timezone.utc
                        )
                except (json.JSONDecodeError, TypeError):
                    pass

            cursor = await db.execute(
                "SELECT target_name, source, color, brightness, on_state, expires_at, overridden_rule_id FROM overrides"
            )
            rows = await cursor.fetchall()
            for row in rows:
                self._overrides[row[0]] = {
                    "source": row[1],
                    "color": row[2],
                    "brightness": row[3],
                    "on_state": bool(row[4]) if row[4] is not None else None,
                    "expires_at": datetime.fromisoformat(row[5]).replace(tzinfo=timezone.utc) if row[5] else None,
                    "overridden_rule_id": row[6],
                }

            cursor = await db.execute(
                "SELECT rule_id, was_active, condition_true_since, last_evaluated FROM rule_state"
            )
            rows = await cursor.fetchall()
            for row in rows:
                self._rule_hysteresis[row[0]] = {
                    "was_active": bool(row[1]),
                    "condition_true_since": (
                        datetime.fromisoformat(row[2]).replace(tzinfo=timezone.utc)
                        if row[2]
                        else None
                    ),
                    "last_evaluated": (
                        datetime.fromisoformat(row[3]).replace(tzinfo=timezone.utc)
                        if row[3]
                        else None
                    ),
                }

        logger.info(
            "Loaded state: %d providers, %d overrides, %d hysteresis records",
            len(self._provider_states),
            len(self._overrides),
            len(self._rule_hysteresis),
        )

    def get_provider_state(self, name: str) -> dict | None:
        return self._provider_states.get(name)

    async def set_provider_state(self, name: str, state: dict):
        self._provider_states[name] = state
        self._provider_timestamps[name] = datetime.now(timezone.utc)
        async with get_db() as db:
            await db.execute(
                """INSERT INTO provider_config (name, last_state, last_fetch)
                   VALUES (?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET last_state=excluded.last_state, last_fetch=excluded.last_fetch, error=NULL""",
                (name, json.dumps(state), datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()

    def get_provider_timestamp(self, name: str) -> datetime | None:
        return self._provider_timestamps.get(name)

    def is_stale(self, name: str, ttl: timedelta) -> bool:
        ts = self._provider_timestamps.get(name)
        if ts is None:
            return True
        return (datetime.now(timezone.utc) - ts) > ttl

    def get_all_provider_states(self) -> dict:
        return dict(self._provider_states)

    def get_light_state(self, target: str) -> dict | None:
        return self._light_states.get(target)

    def set_light_state(self, target: str, state: dict):
        self._light_states[target] = state

    def get_all_light_states(self) -> dict:
        return dict(self._light_states)

    async def get_override(self, target: str) -> dict | None:
        override = self._overrides.get(target)
        if override and override.get("expires_at"):
            if datetime.now(timezone.utc) > override["expires_at"]:
                await self.clear_override(target)
                return None
        return override

    async def set_override(self, target: str, source: str, **kwargs):
        override = {"source": source, **kwargs}
        self._overrides[target] = override
        async with get_db() as db:
            await db.execute(
                """INSERT INTO overrides (target_name, source, color, brightness, on_state, expires_at, overridden_rule_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(target_name) DO UPDATE SET
                     source=excluded.source, color=excluded.color, brightness=excluded.brightness,
                     on_state=excluded.on_state, expires_at=excluded.expires_at,
                     overridden_rule_id=excluded.overridden_rule_id, created_at=CURRENT_TIMESTAMP""",
                (
                    target,
                    source,
                    kwargs.get("color"),
                    kwargs.get("brightness"),
                    kwargs.get("on_state"),
                    kwargs.get("expires_at").isoformat() if kwargs.get("expires_at") else None,
                    kwargs.get("overridden_rule_id"),
                ),
            )
            await db.commit()

    async def clear_override(self, target: str):
        self._overrides.pop(target, None)
        async with get_db() as db:
            await db.execute("DELETE FROM overrides WHERE target_name = ?", (target,))
            await db.commit()

    async def get_all_overrides(self) -> dict:
        await self.cleanup_expired_overrides()
        return dict(self._overrides)

    async def cleanup_expired_overrides(self):
        now = datetime.now(timezone.utc)
        expired = [
            t
            for t, o in self._overrides.items()
            if o.get("expires_at") and now > o["expires_at"]
        ]
        for target in expired:
            await self.clear_override(target)
            logger.info("Override expired for %s", target)

    def get_active_rule(self, target: str) -> dict | None:
        return self._active_rules.get(target)

    def set_active_rule(self, target: str, rule: dict | None):
        self._active_rules[target] = rule

    def get_hysteresis(self, rule_id: int) -> dict:
        return self._rule_hysteresis.get(
            rule_id,
            {"was_active": False, "condition_true_since": None, "last_evaluated": None},
        )

    def clear_hysteresis(self, rule_id: int):
        self._rule_hysteresis.pop(rule_id, None)

    def set_hysteresis(self, rule_id: int, was_active: bool, condition_true_since: datetime | None):
        self._rule_hysteresis[rule_id] = {
            "was_active": was_active,
            "condition_true_since": condition_true_since,
            "last_evaluated": datetime.now(timezone.utc),
        }

    def get_breathing_targets(self) -> dict[str, dict]:
        return dict(self._breathing_targets)

    def set_breathing_targets(self, targets: dict[str, dict]):
        self._breathing_targets = targets

    async def persist_hysteresis(self):
        async with get_db() as db:
            for rule_id, state in self._rule_hysteresis.items():
                await db.execute(
                    """INSERT INTO rule_state (rule_id, was_active, condition_true_since, last_evaluated)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(rule_id) DO UPDATE SET
                         was_active=excluded.was_active,
                         condition_true_since=excluded.condition_true_since,
                         last_evaluated=excluded.last_evaluated""",
                    (
                        rule_id,
                        state["was_active"],
                        state["condition_true_since"].isoformat() if state["condition_true_since"] else None,
                        state["last_evaluated"].isoformat() if state["last_evaluated"] else None,
                    ),
                )
            await db.commit()


state_manager = StateManager()
