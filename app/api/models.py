from pydantic import BaseModel
from typing import Any


class LightTargetCreate(BaseModel):
    name: str
    type: str  # "light" or "grouped_light"
    hue_id: str
    friendly_name: str = ""


class LightTargetResponse(BaseModel):
    name: str
    type: str
    hue_id: str
    friendly_name: str | None = None
    state: dict | None = None
    active_rule: str | None = None
    override: dict | None = None


class RuleCondition(BaseModel):
    provider: str | None = None
    match: Any = None
    any_of: list[dict] | None = None
    deadband: float | None = None
    for_duration: str | None = None


class RuleEffect(BaseModel):
    mode: str = "static"
    colors: list[str] = []
    brightness: int | None = None
    transition: int | None = None
    cycle_interval: int | None = None


class RuleConfig(BaseModel):
    condition: dict
    effect: dict
    targets: list[str]


class RuleCreate(BaseModel):
    name: str
    priority: int
    enabled: bool = True
    config: RuleConfig


class RuleUpdate(BaseModel):
    name: str | None = None
    priority: int | None = None
    enabled: bool | None = None
    config: RuleConfig | None = None


class RuleResponse(BaseModel):
    id: int
    name: str
    priority: int
    enabled: bool
    config: dict
    created_at: str | None = None
    updated_at: str | None = None


class ReorderItem(BaseModel):
    id: int
    priority: int


class ReorderRequest(BaseModel):
    rules: list[ReorderItem]


class RuleTestRequest(BaseModel):
    condition: dict


class RuleTestResponse(BaseModel):
    would_match: bool
    current_state: dict


class OverrideCreate(BaseModel):
    color: str | None = None
    brightness: int | None = None
    on_state: bool | None = None
    expires_minutes: int | None = None


class HolidayCreate(BaseModel):
    name: str
    date: str
    window_start: str | None = None
    window_end: str | None = None
    recurring: bool = True
    category: str = "custom"
    colors: list[str] = []
    enabled: bool = True


class HolidayResponse(BaseModel):
    id: int
    name: str
    date: str
    window_start: str | None = None
    window_end: str | None = None
    recurring: bool
    category: str
    colors: list[str]
    enabled: bool


class HolidayConfigUpdate(BaseModel):
    colors: list[str] | None = None
    enabled: bool | None = None
    window_before_days: int | None = None
    window_after_days: int | None = None


class ProviderStatus(BaseModel):
    name: str
    last_fetch: str | None = None
    ttl_seconds: int
    is_stale: bool
    current_state: dict | None = None
    error: str | None = None


class ProviderConfigUpdate(BaseModel):
    config: dict = {}
    ttl_seconds: int | None = None


class BridgeStatus(BaseModel):
    connected: bool
    host: str = ""
    paired: bool = False


class DashboardStatus(BaseModel):
    lights: list[dict]
    providers: list[dict]
    active_rules: dict
    overrides: dict
    bridge_connected: bool


class LogEntry(BaseModel):
    id: int
    timestamp: str
    level: str
    source: str
    message: str
    details: dict | None = None
