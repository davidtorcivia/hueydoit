import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.engine.state import state_manager
from app.engine.evaluator import evaluator
from app.providers.base import Provider
from app.providers.holiday import HolidayProvider
from app.providers.weather import WeatherProvider
from app.providers.solar import SolarProvider
from app.providers.webhook import WebhookProvider
from app.providers.time_provider import TimeProvider
from app.ws import ws_manager
from app.database import add_log

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

        self._scheduler.start()
        logger.info("Scheduler started with %d providers", len(self._providers))

        for provider in self._providers.values():
            try:
                await self._run_provider(provider)
            except Exception as e:
                logger.error("Initial fetch for %s failed: %s", provider.name, e)

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
            from app.database import get_db
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

    async def refresh_provider(self, name: str):
        provider = self._providers.get(name)
        if not provider:
            raise ValueError(f"Unknown provider: {name}")
        await self._run_provider(provider)

    def get_webhook_provider(self) -> WebhookProvider | None:
        return self._webhook_provider

    def get_provider(self, name: str) -> Provider | None:
        return self._providers.get(name)


engine_scheduler = EngineScheduler()
