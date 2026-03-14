from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import timedelta


@dataclass
class ScheduleConfig:
    type: str  # "cron", "interval", or "none"
    kwargs: dict = field(default_factory=dict)


class Provider(ABC):
    name: str

    @abstractmethod
    async def fetch(self) -> dict:
        ...

    @abstractmethod
    def schedule(self) -> ScheduleConfig:
        ...

    @abstractmethod
    def ttl(self) -> timedelta:
        ...
