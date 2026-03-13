from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import timedelta


@dataclass
class ScheduleConfig:
    type: str  # "cron" or "interval"
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
