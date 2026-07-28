import json
import logging
from datetime import datetime, timedelta, timezone

from app.database import get_db, add_log
from app.engine.state import state_manager
from app.bridge.client import bridge_client
from app.bridge.effects import build_light_command
from app.ws import ws_manager

logger = logging.getLogger(__name__)


def _parse_duration(s: str) -> timedelta:
    """Parse duration strings like '15m', '1h', '30s'."""
    s = s.strip().lower()
    if s.endswith("m"):
        return timedelta(minutes=int(s[:-1]))
    if s.endswith("h"):
        return timedelta(hours=int(s[:-1]))
    if s.endswith("s"):
        return timedelta(seconds=int(s[:-1]))
    return timedelta(minutes=int(s))


def _parse_signed_duration(s: str) -> timedelta:
    """Parse optionally-signed duration: '-30m', '1h', '30m', '-1h'."""
    s = s.strip().lower()
    negative = s.startswith("-")
    if negative or s.startswith("+"):
        s = s[1:]
    td = _parse_duration(s)
    return -td if negative else td


class RuleEvaluator:
    def __init__(self):
        self._now_override: datetime | None = None

    async def evaluate_all(self):
        await state_manager.cleanup_expired_overrides()

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, name, priority, config FROM rules WHERE enabled = 1 ORDER BY priority ASC"
            )
            rules = await cursor.fetchall()

            cursor = await db.execute("SELECT name, type, hue_id FROM targets")
            targets = await cursor.fetchall()

        if not rules:
            return

        target_map = {row[0]: {"name": row[0], "type": row[1], "hue_id": row[2]} for row in targets}
        if not target_map:
            return

        provider_states = state_manager.get_all_provider_states()

        # Always inject fresh time state — no need to poll for this
        import zoneinfo
        from app.config import settings
        tz = zoneinfo.ZoneInfo(settings.tz)
        now_local = datetime.now(tz)
        provider_states["time"] = {
            "hour": now_local.hour,
            "minute": now_local.minute,
            "second": now_local.second,
            "day_of_week": now_local.strftime("%A").lower(),
            "date": now_local.strftime("%Y-%m-%d"),
            "is_weekend": now_local.weekday() >= 5,
            "month": now_local.month,
            "day": now_local.day,
            "year": now_local.year,
        }

        # Always inject fresh calendar state
        from app.providers.calendar_provider import CalendarProvider
        provider_states["calendar"] = CalendarProvider.compute_state(now_local.date())

        # Always inject fresh solar state (period must reflect current time)
        from app.providers.solar import SolarProvider
        solar_fresh = SolarProvider.compute_fresh(settings.tz, settings.latitude, settings.longitude)
        # Merge with existing solar state (preserves dawn/dusk/noon from daily fetch)
        existing_solar = provider_states.get("solar", {})
        provider_states["solar"] = {**existing_solar, **solar_fresh}

        # Update cached state so the status endpoint shows fresh data
        state_manager.update_provider_state_memory("time", provider_states["time"])
        state_manager.update_provider_state_memory("calendar", provider_states["calendar"])
        solar_display = {k: v for k, v in provider_states["solar"].items() if not k.startswith("_")}
        state_manager.update_provider_state_memory("solar", solar_display)

        target_assignments: dict[str, dict] = {}
        new_breathing: dict[str, dict] = {}  # targets that need continuous breathe

        for rule_row in rules:
            rule_id = rule_row[0]
            rule_name = rule_row[1]
            rule_priority = rule_row[2]
            try:
                config = json.loads(rule_row[3]) if isinstance(rule_row[3], str) else rule_row[3]
            except (json.JSONDecodeError, TypeError):
                logger.warning("Invalid config for rule %s", rule_name)
                continue

            condition = config.get("condition", {})
            effect = config.get("effect", {})
            rule_targets = config.get("targets", [])

            raw_match = self._match_condition(condition, provider_states)
            final_match = self._apply_hysteresis(rule_id, condition, raw_match, provider_states)

            logger.info(
                "Rule '%s' (id=%d, pri=%d): raw=%s final=%s targets=%s",
                rule_name, rule_id, rule_priority, raw_match, final_match, rule_targets,
            )

            self._record_hysteresis(rule_id, raw_match, final_match)

            if not final_match:
                continue

            for target_name in rule_targets:
                if target_name in target_assignments:
                    continue
                if target_name not in target_map:
                    continue
                target_assignments[target_name] = {
                    "rule_id": rule_id,
                    "rule_name": rule_name,
                    "priority": rule_priority,
                    "effect": effect,
                    "condition": condition,
                    "_targets": rule_targets,
                }

        has_catchall = False
        for rule_row in rules:
            try:
                config = json.loads(rule_row[3]) if isinstance(rule_row[3], str) else rule_row[3]
            except (json.JSONDecodeError, TypeError):
                continue
            cond = config.get("condition", {})
            if cond.get("match") == "always":
                has_catchall = True
                break

        for target_name, target_info in target_map.items():
            override = await state_manager.get_override(target_name)
            if override:
                overridden_rule_id = override.get("overridden_rule_id")
                if overridden_rule_id is not None:
                    # Override is tied to a specific rule — clear it when the
                    # winning rule changes so the new rule can take effect.
                    assignment = target_assignments.get(target_name)
                    current_rule_id = assignment["rule_id"] if assignment else None
                    if current_rule_id != overridden_rule_id:
                        await state_manager.clear_override(target_name)
                        logger.info(
                            "Override cleared for %s: winning rule changed from %s",
                            target_name, overridden_rule_id,
                        )
                        # Fall through to apply the new rule below
                    else:
                        continue  # Same rule still active — respect the override
                else:
                    continue  # Fixed-expiration or manual override — respect it

            assignment = target_assignments.get(target_name)

            if assignment:
                prev_rule = state_manager.get_active_rule(target_name)
                prev_id = prev_rule.get("rule_id") if prev_rule else None

                state_manager.set_active_rule(target_name, assignment)

                effect = dict(assignment["effect"])

                # Dynamic holiday colors: inject active holiday palette
                if effect.get("use_holiday_colors"):
                    holiday_state = provider_states.get("holiday", {})
                    active_colors = holiday_state.get("active_colors", [])
                    if active_colors:
                        effect["colors"] = active_colors
                        # Auto-distribute colors across targets in round-robin
                        rule_targets = assignment.get("_targets", [])
                        if len(active_colors) > 1 and len(rule_targets) > 1:
                            try:
                                idx = rule_targets.index(target_name)
                                effect["colors"] = [active_colors[idx % len(active_colors)]]
                            except ValueError:
                                pass

                # Per-light color map: override colors for this specific target
                color_map = effect.pop("color_map", None)
                if color_map and target_name in color_map:
                    effect["colors"] = [color_map[target_name]]

                # Per-light brightness map
                brightness_map = effect.pop("brightness_map", None)
                if brightness_map and target_name in brightness_map:
                    effect["brightness"] = brightness_map[target_name]

                cmd = build_light_command(effect, target_info["type"])

                logger.info(
                    "Applying rule '%s' to %s: colors=%s brightness=%s mode=%s cmd_keys=%s",
                    assignment["rule_name"], target_name,
                    effect.get("colors"), effect.get("brightness"),
                    effect.get("mode"), list(cmd.keys()),
                )

                if bridge_client.connected:
                    await bridge_client.set_light_state(
                        target_info["type"], target_info["hue_id"], cmd
                    )

                if effect.get("mode") == "breathe":
                    new_breathing[target_name] = {
                        "type": target_info["type"],
                        "hue_id": target_info["hue_id"],
                        "brightness": effect.get("brightness", 80),
                        "transition": effect.get("transition", 4000),
                    }

                if prev_id != assignment["rule_id"]:
                    await ws_manager.broadcast(
                        "rule_activated",
                        {"target": target_name, "rule": assignment["rule_name"]},
                    )
                    await add_log(
                        "info",
                        "evaluator",
                        f"Rule '{assignment['rule_name']}' activated for {target_name}",
                        {"rule_id": assignment["rule_id"], "target": target_name},
                    )
            elif not has_catchall:
                state_manager.set_active_rule(target_name, None)
                if bridge_client.connected:
                    await bridge_client.set_light_state(
                        target_info["type"],
                        target_info["hue_id"],
                        {"on": {"on": False}},
                    )

        state_manager.set_breathing_targets(new_breathing)
        await state_manager.persist_hysteresis()

    def _match_condition(self, condition: dict, provider_states: dict) -> bool:
        if condition.get("match") == "always":
            return True

        if "all_of" in condition:
            return all(
                self._match_condition(sub, provider_states) for sub in condition["all_of"]
            )

        if "any_of" in condition:
            return any(
                self._match_condition(sub, provider_states) for sub in condition["any_of"]
            )

        provider_name = condition.get("provider")
        match_block = condition.get("match", {})

        if isinstance(match_block, str):
            return match_block == "always"

        if provider_name:
            state = provider_states.get(provider_name)
            if state is None:
                return False
            if provider_name == "solar":
                state, match_block = self._apply_solar_offsets(state, match_block)
            return self._match_block(match_block, state)
        else:
            return self._match_block(match_block, provider_states)

    def _match_block(self, match: dict, state: dict) -> bool:
        for key, expected in match.items():
            # Special handling for date_range (MM-DD format, supports year wrap)
            if key == "date_range" and isinstance(expected, dict):
                current_date = state.get("date", "")  # YYYY-MM-DD
                if not current_date:
                    return False
                # Extract MM-DD from current date
                md = current_date[5:]  # "MM-DD"
                start = expected.get("start", "01-01")
                end = expected.get("end", "12-31")
                if start <= end:
                    if not (start <= md <= end):
                        return False
                else:
                    # Year wrap: e.g. start=11-01, end=02-28
                    if not (md >= start or md <= end):
                        return False
                continue

            # Special handling for hour_range (supports overnight wrap)
            if key == "hour_range" and isinstance(expected, dict):
                current_hour = state.get("hour")
                if current_hour is None:
                    return False
                start = expected.get("start", 0)
                end = expected.get("end", 0)
                if start == end:
                    pass  # always matches (24h)
                elif start < end:
                    if not (start <= current_hour < end):
                        return False
                else:
                    # Overnight wrap: e.g. start=23, end=3 → 23,0,1,2
                    if not (current_hour >= start or current_hour < end):
                        return False
                continue

            value = self._resolve_dot_path(state, key)
            if value is None:
                return False

            if isinstance(expected, dict):
                if "gt" in expected and not (value > expected["gt"]):
                    return False
                if "gte" in expected and not (value >= expected["gte"]):
                    return False
                if "lt" in expected and not (value < expected["lt"]):
                    return False
                if "lte" in expected and not (value <= expected["lte"]):
                    return False
                if "in" in expected:
                    if isinstance(value, str):
                        value_lower = value.lower()
                    else:
                        value_lower = value
                    expected_set = [
                        v.lower() if isinstance(v, str) else v for v in expected["in"]
                    ]
                    if value_lower not in expected_set:
                        return False
            else:
                if isinstance(value, str) and isinstance(expected, str):
                    if value.lower() != expected.lower():
                        return False
                elif value != expected:
                    return False
        return True

    def _apply_solar_offsets(self, state: dict, match_block: dict) -> tuple[dict, dict]:
        """Shift sunrise/sunset by offsets and recompute period/phase."""
        sunrise_offset = match_block.get("sunrise_offset")
        sunset_offset = match_block.get("sunset_offset")
        if not sunrise_offset and not sunset_offset:
            return state, match_block

        filtered = {k: v for k, v in match_block.items()
                    if k not in ("sunrise_offset", "sunset_offset")}

        sunrise_dt = state.get("_sunrise_dt")
        sunset_dt = state.get("_sunset_dt")
        if not sunrise_dt or not sunset_dt:
            return state, filtered

        if sunrise_offset:
            sunrise_dt = sunrise_dt + _parse_signed_duration(sunrise_offset)
        if sunset_offset:
            sunset_dt = sunset_dt + _parse_signed_duration(sunset_offset)

        import zoneinfo
        from app.config import settings
        now = self._now_override or datetime.now(zoneinfo.ZoneInfo(settings.tz))

        if now < sunrise_dt:
            period, phase = "night", "before_sunrise"
        elif now > sunset_dt:
            period, phase = "night", "after_sunset"
        else:
            period, phase = "day", "daytime"

        adjusted = {
            **state,
            "period": period,
            "phase": phase,
            "sunrise": sunrise_dt.strftime("%H:%M"),
            "sunset": sunset_dt.strftime("%H:%M"),
            "_sunrise_dt": sunrise_dt,
            "_sunset_dt": sunset_dt,
        }
        return adjusted, filtered

    def _record_hysteresis(self, rule_id: int, raw_match: bool, final_match: bool):
        """Persist the rule's hysteresis state after evaluation.

        The pending timer is kept alive on raw_match, not final_match: while a
        `for` gate counts down the rule is not yet active, and clearing the
        timestamp then reset the countdown every tick so it never elapsed.
        """
        state_manager.set_hysteresis(
            rule_id,
            was_active=final_match,
            condition_true_since=(
                state_manager.get_hysteresis(rule_id)["condition_true_since"]
                if raw_match
                else None
            ),
        )

    def _apply_hysteresis(
        self, rule_id: int, condition: dict, raw_match: bool, provider_states: dict
    ) -> bool:
        hyst = state_manager.get_hysteresis(rule_id)
        was_active = hyst["was_active"]

        deadband = condition.get("deadband")
        if deadband is not None and was_active and not raw_match:
            match_block = condition.get("match", {})
            if isinstance(match_block, dict):
                provider_name = condition.get("provider")
                state = provider_states.get(provider_name, {}) if provider_name else provider_states
                still_in_band = True
                for key, expected in match_block.items():
                    if isinstance(expected, dict):
                        value = self._resolve_dot_path(state, key)
                        if value is None:
                            still_in_band = False
                            break
                        if "gte" in expected and value < (expected["gte"] - deadband):
                            still_in_band = False
                        if "gt" in expected and value <= (expected["gt"] - deadband):
                            still_in_band = False
                        if "lte" in expected and value > (expected["lte"] + deadband):
                            still_in_band = False
                        if "lt" in expected and value >= (expected["lt"] + deadband):
                            still_in_band = False
                if still_in_band:
                    return True

        duration_str = condition.get("for")
        if duration_str and raw_match:
            duration = _parse_duration(duration_str)
            now = datetime.now(timezone.utc)
            condition_true_since = hyst["condition_true_since"]
            if condition_true_since is None:
                state_manager.set_hysteresis(rule_id, was_active=False, condition_true_since=now)
                return False
            if (now - condition_true_since) < duration:
                return False

        if raw_match and not hyst["condition_true_since"]:
            state_manager.set_hysteresis(
                rule_id,
                was_active=was_active,
                condition_true_since=datetime.now(timezone.utc),
            )

        return raw_match

    def _resolve_dot_path(self, data: dict, path: str):
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current


    async def predict_at(self, target_time: datetime) -> list[dict]:
        """Dry-run evaluation at a future time. Returns predicted target assignments."""
        import zoneinfo
        from app.config import settings
        from app.providers.calendar_provider import CalendarProvider
        from app.providers.solar import SolarProvider

        tz = zoneinfo.ZoneInfo(settings.tz)
        target_local = target_time.astimezone(tz) if target_time.tzinfo else target_time

        # Build simulated provider states
        provider_states = state_manager.get_all_provider_states()

        provider_states["time"] = {
            "hour": target_local.hour,
            "minute": target_local.minute,
            "second": target_local.second,
            "day_of_week": target_local.strftime("%A").lower(),
            "date": target_local.strftime("%Y-%m-%d"),
            "is_weekend": target_local.weekday() >= 5,
            "month": target_local.month,
            "day": target_local.day,
            "year": target_local.year,
        }

        provider_states["calendar"] = CalendarProvider.compute_state(target_local.date())

        # Holiday state was reused from the cached "today" value, so a preview of a
        # future date showed the seasonal rule winning when a holiday would actually
        # take it at a higher priority. Recompute for the simulated date.
        provider_states["holiday"] = await self._holiday_state_for(target_local.date())

        # Compute solar for today but determine period at the target time
        solar_fresh = SolarProvider.compute_fresh(settings.tz, settings.latitude, settings.longitude)
        sunrise_dt = solar_fresh.get("_sunrise_dt")
        sunset_dt = solar_fresh.get("_sunset_dt")
        if sunrise_dt and sunset_dt:
            if target_local < sunrise_dt:
                solar_fresh["period"] = "night"
                solar_fresh["phase"] = "before_sunrise"
            elif target_local > sunset_dt:
                solar_fresh["period"] = "night"
                solar_fresh["phase"] = "after_sunset"
            else:
                solar_fresh["period"] = "day"
                solar_fresh["phase"] = "daytime"
        existing_solar = provider_states.get("solar", {})
        provider_states["solar"] = {**existing_solar, **solar_fresh}

        # Fetch rules and targets
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, name, priority, config FROM rules WHERE enabled = 1 ORDER BY priority ASC"
            )
            rules = await cursor.fetchall()
            cursor = await db.execute("SELECT name, type, hue_id, friendly_name FROM targets")
            targets = await cursor.fetchall()

        target_map = {row[0]: {"name": row[0], "type": row[1], "hue_id": row[2], "friendly_name": row[3]} for row in targets}

        # Use time override so solar offset checks use the simulated time
        self._now_override = target_local
        try:
            return self._predict_rules(rules, provider_states, target_map)
        finally:
            self._now_override = None

    async def _holiday_state_for(self, on_date) -> dict:
        """Holiday provider state as it would be on `on_date`."""
        from app.holidays.loader import load_all_holidays, is_holiday_active

        try:
            holidays = await load_all_holidays(on_date.year)
        except Exception as e:
            logger.warning("Could not load holidays for %s: %s", on_date.year, e)
            return {}

        active = [
            {
                "name": h.name, "slug": h.slug, "colors": h.colors,
                "category": h.category, "priority": h.priority,
            }
            for h in holidays
            if is_holiday_active(h, on_date)
        ]
        active.sort(key=lambda x: x.get("priority", 50))

        return {
            "active_holidays": [h["slug"] for h in active],
            "active_holiday": active[0]["slug"] if active else None,
            "active_colors": active[0]["colors"] if active else [],
            "active_details": active,
            "upcoming": [],
        }

    def _predict_rules(self, rules, provider_states, target_map) -> list[dict]:
        target_assignments: dict[str, dict] = {}

        for rule_row in rules:
            rule_id, rule_name = rule_row[0], rule_row[1]
            try:
                config = json.loads(rule_row[3]) if isinstance(rule_row[3], str) else rule_row[3]
            except (json.JSONDecodeError, TypeError):
                continue

            condition = config.get("condition", {})
            effect = config.get("effect", {})
            rule_targets = config.get("targets", [])

            if not self._match_condition(condition, provider_states):
                continue

            for target_name in rule_targets:
                if target_name in target_assignments or target_name not in target_map:
                    continue

                # Resolve color for this target
                t_effect = dict(effect)
                color = None

                if t_effect.get("use_holiday_colors"):
                    holiday_state = provider_states.get("holiday", {})
                    active_colors = holiday_state.get("active_colors", [])
                    if active_colors:
                        try:
                            idx = rule_targets.index(target_name)
                            color = active_colors[idx % len(active_colors)]
                        except ValueError:
                            color = active_colors[0]

                color_map = t_effect.get("color_map", {})
                if color_map and target_name in color_map:
                    color = color_map[target_name]

                if color is None:
                    colors = t_effect.get("colors", [])
                    color = colors[0] if colors else None

                brightness = t_effect.get("brightness_map", {}).get(
                    target_name, t_effect.get("brightness")
                )

                target_assignments[target_name] = {
                    "target": target_name,
                    "friendly_name": target_map[target_name].get("friendly_name", target_name),
                    "rule_name": rule_name,
                    "rule_id": rule_id,
                    "color": color,
                    "brightness": brightness,
                    "mode": t_effect.get("mode", "static"),
                }

        return list(target_assignments.values())


evaluator = RuleEvaluator()
