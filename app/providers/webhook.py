import logging
from datetime import datetime, timedelta, timezone

from app.providers.base import Provider, ScheduleConfig

logger = logging.getLogger(__name__)


class WebhookProvider(Provider):
    name = "webhook"

    def __init__(self):
        self._webhooks: dict[str, dict] = {}
        self._timestamps: dict[str, datetime] = {}
        self._ttls: dict[str, timedelta] = {}

    async def ingest(self, webhook_name: str, data: dict, ttl_minutes: int = 60):
        self._webhooks[webhook_name] = data
        self._timestamps[webhook_name] = datetime.now(timezone.utc)
        self._ttls[webhook_name] = timedelta(minutes=ttl_minutes)
        logger.info("Ingested webhook '%s'", webhook_name)

    async def fetch(self) -> dict:
        now = datetime.now(timezone.utc)
        result = {}
        expired = []
        for name, data in self._webhooks.items():
            ts = self._timestamps.get(name)
            ttl = self._ttls.get(name, timedelta(hours=1))
            if ts and (now - ts) > ttl:
                expired.append(name)
                continue
            result[name] = data

        for name in expired:
            del self._webhooks[name]
            del self._timestamps[name]
            if name in self._ttls:
                del self._ttls[name]
            logger.info("Webhook '%s' expired", name)

        return result

    def schedule(self) -> ScheduleConfig:
        return ScheduleConfig(type="interval", kwargs={"seconds": 300})

    def ttl(self) -> timedelta:
        return timedelta(days=365)

    def get_webhook_state(self, name: str) -> dict | None:
        return self._webhooks.get(name)

    def get_webhook_timestamp(self, name: str) -> datetime | None:
        return self._timestamps.get(name)
