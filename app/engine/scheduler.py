import json
import logging
from datetime import datetime, timedelta
import zoneinfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.engine.state import state_manager
from app.engine.evaluator import evaluator
from app.providers.base import Provider
from app.providers.holiday import HolidayProvider
from app.providers.weather import WeatherProvider
from app.providers.solar import SolarProvider
from app.providers.webhook import WebhookProvider
from app.providers.time_provider import TimeProvider
from app.providers.calendar_provider import CalendarProvider
from app.ws import ws_manager
from app.database import add_log, get_db

logger = logging.getLogger(__name__)


class EngineScheduler:
    def __init__(self):
        self._scheduler = AsyncIOScheduler()
        self._providers: dict[str, Provider] = {}
        self._webhook_provider: WebhookProvider | None = None

    async def start(self):
        self._providers = {
            "holiday": HolidayProvider(),
            "weather": WeatherProvider(),
            "solar": SolarProvider(),
            "time": TimeProvider(),
            "calendar": CalendarProvider(),
            "webhook": WebhookProvider(),
        }
        self._webhook_provider = self._providers["webhook"]

        for name, provider in self._providers.items():
            schedule = provider.schedule()

            if schedule.type == "cron":
                trigger = CronTrigger(**schedule.kwargs)
            elif schedule.type == "interval":
                trigger = IntervalTrigger(**schedule.kwargs)
            else:
                continue

            self._scheduler.add_job(
                self._run_provider,
                trigger=trigger,
                args=[provider],
                id=f"provider_{name}",
                name=f"Provider: {name}",
                replace_existing=True,
            )

        self._scheduler.add_job(
            state_manager.cleanup_expired_overrides,
            IntervalTrigger(minutes=1),
            id="cleanup_overrides",
            name="Cleanup expired overrides",
            replace_existing=True,
        )

        self._breathe_phase = False
        self._scheduler.add_job(
            self._breathe_loop,
            IntervalTrigger(seconds=8),
            id="breathe_loop",
            name="Continuous breathe effect",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info("Scheduler started with %d providers", len(self._providers))

        for provider in self._providers.values():
            try:
                await self._run_provider(provider)
            except Exception as e:
                logger.error("Initial fetch for %s failed: %s", provider.name, e)

        # Compute first time-based evaluation
        await self._schedule_next_time_eval()

    async def stop(self):
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    async def _run_provider(self, provider: Provider):
        try:
            old_state = state_manager.get_provider_state(provider.name)
            new_state = await provider.fetch()
            await state_manager.set_provider_state(provider.name, new_state)

            await ws_manager.broadcast("provider_update", {
                "name": provider.name,
                "state": new_state,
                "stale": False,
            })

            if old_state != new_state:
                logger.info("Provider %s state changed, triggering evaluation", provider.name)
                await evaluator.evaluate_all()

            await add_log(
                "info",
                f"provider.{provider.name}",
                f"Provider {provider.name} fetched successfully",
                {"state_keys": list(new_state.keys()) if new_state else []},
            )
        except Exception as e:
            logger.error("Provider %s fetch failed: %s", provider.name, e)
            async with get_db() as db:
                await db.execute(
                    "UPDATE provider_config SET error = ? WHERE name = ?",
                    (str(e), provider.name),
                )
                await db.commit()
            await ws_manager.broadcast("provider_error", {
                "name": provider.name,
                "error": str(e),
            })
            await add_log(
                "error",
                f"provider.{provider.name}",
                f"Provider {provider.name} fetch failed: {e}",
            )

    async def trigger_evaluation(self):
        await evaluator.evaluate_all()
        await self._schedule_next_time_eval()

    async def refresh_provider(self, name: str):
        provider = self._providers.get(name)
        if not provider:
            raise ValueError(f"Unknown provider: {name}")
        await self._run_provider(provider)

    def get_webhook_provider(self) -> WebhookProvider | None:
        return self._webhook_provider

    def get_provider(self, name: str) -> Provider | None:
        return self._providers.get(name)

    # ------------------------------------------------------------------
    # Computed time scheduling — no polling
    # ------------------------------------------------------------------

    async def _schedule_next_time_eval(self):
        """Scan rules for time conditions and schedule a one-shot evaluation
        at the exact moment the next condition transitions."""
        try:
            self._scheduler.remove_job("time_eval")
        except Exception:
            pass

        tz = zoneinfo.ZoneInfo(settings.tz)
        now = datetime.now(tz)

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT config FROM rules WHERE enabled = 1"
            )
            rows = await cursor.fetchall()

        transitions: set[datetime] = set()
        for row in rows:
            try:
                config = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            except (json.JSONDecodeError, TypeError):
                continue
            self._extract_time_transitions(config.get("condition", {}), now, tz, transitions)

        future = sorted(t for t in transitions if t > now)
        if not future:
            return

        next_time = future[0]
        logger.info("Next time evaluation scheduled for %s", next_time.strftime("%Y-%m-%d %H:%M"))

        self._scheduler.add_job(
            self._on_time_transition,
            trigger=DateTrigger(run_date=next_time),
            id="time_eval",
            name="Time condition transition",
            replace_existing=True,
        )

    def _extract_time_transitions(
        self, condition: dict, now: datetime, tz: zoneinfo.ZoneInfo, transitions: set[datetime]
    ):
        """Recursively find time-condition transition points from a condition tree."""
        if condition.get("match") == "always":
            return

        if "all_of" in condition:
            for sub in condition["all_of"]:
                self._extract_time_transitions(sub, now, tz, transitions)
            return
        if "any_of" in condition:
            for sub in condition["any_of"]:
                self._extract_time_transitions(sub, now, tz, transitions)
            return

        provider = condition.get("provider")

        # Solar conditions — schedule at sunrise/sunset
        if provider == "solar":
            self._add_solar_transitions(now, tz, transitions)
            return

        if provider not in ("time", "calendar"):
            return

        match = condition.get("match", {})
        if not isinstance(match, dict):
            return

        base = now.replace(minute=0, second=0, microsecond=0)

        # hour_range: {start: 23, end: 3} — transitions at start and end hours
        if "hour_range" in match:
            hr = match["hour_range"]
            start_h = hr.get("start", 0)
            end_h = hr.get("end", 0)
            for h in (start_h, end_h):
                t = base.replace(hour=h)
                if t <= now:
                    t += timedelta(days=1)
                transitions.add(t)

        # Legacy: hour: {gte: X} — transitions at hour X and midnight
        if "hour" in match:
            h_cond = match["hour"]
            if isinstance(h_cond, dict):
                h = h_cond.get("gte") or h_cond.get("gt")
                if h is not None:
                    h = int(h)
                    on = base.replace(hour=h)
                    if on <= now:
                        on += timedelta(days=1)
                    transitions.add(on)
                    midnight = (base + timedelta(days=1)).replace(hour=0)
                    if midnight <= now:
                        midnight += timedelta(days=1)
                    transitions.add(midnight)

        # is_weekend — transitions at Saturday 00:00 and Monday 00:00
        if "is_weekend" in match:
            dow = now.weekday()
            for target_dow in (5, 0):  # Saturday, Monday
                days = (target_dow - dow) % 7
                t = (base + timedelta(days=days)).replace(hour=0)
                if t <= now:
                    t += timedelta(days=7)
                transitions.add(t)

        # date_range — transitions at start and end dates (midnight)
        if "date_range" in match:
            dr = match["date_range"]
            for md_str in (dr.get("start", ""), dr.get("end", "")):
                if not md_str:
                    continue
                try:
                    m, d = map(int, md_str.split("-"))
                    t = base.replace(month=m, day=d, hour=0)
                    if t <= now:
                        t = t.replace(year=t.year + 1)
                    transitions.add(t)
                except (ValueError, OverflowError):
                    pass

        # season — transitions at season boundaries (1st of Mar, Jun, Sep, Dec)
        if "season" in match:
            for m in (3, 6, 9, 12):
                t = base.replace(month=m, day=1, hour=0)
                if t <= now:
                    t = t.replace(year=t.year + 1)
                transitions.add(t)

        # month / month_name — transitions at 1st of each month
        if "month" in match or "month_name" in match:
            for m in range(1, 13):
                t = base.replace(month=m, day=1, hour=0)
                if t <= now:
                    t = t.replace(year=t.year + 1)
                transitions.add(t)

        # day_of_week — transitions at start and end of the target day
        if "day_of_week" in match:
            day_name = str(match["day_of_week"]).lower()
            day_map = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6,
            }
            target_dow = day_map.get(day_name)
            if target_dow is not None:
                dow = now.weekday()
                days = (target_dow - dow) % 7
                start = (base + timedelta(days=days)).replace(hour=0)
                if start <= now:
                    start += timedelta(days=7)
                transitions.add(start)
                transitions.add(start + timedelta(days=1))

    def _add_solar_transitions(self, now: datetime, tz: zoneinfo.ZoneInfo, transitions: set[datetime]):
        """Add sunrise/sunset as transition points."""
        from app.providers.solar import SolarProvider
        solar = SolarProvider.compute_fresh(settings.tz, settings.latitude, settings.longitude)
        sunrise_dt = solar.get("_sunrise_dt")
        sunset_dt = solar.get("_sunset_dt")
        if sunrise_dt and sunrise_dt > now:
            transitions.add(sunrise_dt)
        if sunset_dt and sunset_dt > now:
            transitions.add(sunset_dt)
        # Also schedule for tomorrow's sunrise if both have passed
        if sunrise_dt and sunset_dt and sunrise_dt <= now and sunset_dt <= now:
            tomorrow = now.date() + timedelta(days=1)
            try:
                from astral import LocationInfo
                from astral.sun import sun
                location = LocationInfo(
                    name="Home", region="", timezone=settings.tz,
                    latitude=settings.latitude, longitude=settings.longitude,
                )
                s = sun(location.observer, date=tomorrow, tzinfo=tz)
                transitions.add(s["sunrise"])
            except Exception:
                # Fallback: midnight + 6h
                transitions.add(now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1, hours=6))

    async def _breathe_loop(self):
        """Gently oscillate brightness for all targets with active breathe effects."""
        from app.bridge.client import bridge_client

        targets = state_manager.get_breathing_targets()
        if not targets or not bridge_client.connected:
            return

        self._breathe_phase = not self._breathe_phase

        for target_name, info in targets.items():
            override = await state_manager.get_override(target_name)
            if override and override.get("source") == "external":
                continue

            full = info.get("brightness", 80)
            low = max(1, int(full * 0.70))
            target_brightness = full if self._breathe_phase else low
            transition_ms = 8000

            try:
                kwargs = {
                    "brightness": float(target_brightness),
                    "transition_time": transition_ms,
                }
                if info["type"] == "light":
                    light = bridge_client._find_light(info["hue_id"])
                    if light:
                        await bridge_client._bridge.lights.set_state(light.id, **kwargs)
                elif info["type"] == "grouped_light":
                    gl = bridge_client._find_grouped_light(info["hue_id"])
                    if gl:
                        await bridge_client._bridge.groups.grouped_light.set_state(gl.id, **kwargs)
            except Exception as e:
                logger.debug("Breathe pulse failed for %s: %s", target_name, e)

    async def _on_time_transition(self):
        """Fired at a computed time-condition transition point."""
        logger.info("Time transition reached, evaluating rules")
        time_provider = self._providers.get("time")
        if time_provider:
            await self._run_provider(time_provider)
        else:
            await evaluator.evaluate_all()
        await self._schedule_next_time_eval()


engine_scheduler = EngineScheduler()
