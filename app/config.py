from pathlib import Path

from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    hue_controller_port: int = 8585
    openweathermap_api_key: str = ""
    latitude: float = 40.704941
    longitude: float = -73.914642
    encryption_key: str = ""
    tz: str = "America/New_York"
    hue_bridge_ip: str = ""
    external_override_timeout_min: int = 30
    db_path: str = "data/huey-do-it.db"
    # Restart if the scheduler stops beating for this long. Periodic
    # evaluation runs every 5 minutes, so this is 4 missed cycles. 0 disables.
    watchdog_stall_minutes: int = 20
    log_retention_days: int = 14
    log_max_rows: int = 20000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

_fernet: Fernet | None = None


def get_encryption_key() -> bytes:
    global _fernet
    if settings.encryption_key:
        key = settings.encryption_key.encode()
    else:
        key_path = Path(settings.db_path).parent / "encryption.key"
        if key_path.exists():
            key = key_path.read_bytes().strip()
        else:
            key = Fernet.generate_key()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            key_path.write_bytes(key)
    _fernet = Fernet(key)
    return key


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        get_encryption_key()
    assert _fernet is not None
    return _fernet


def encrypt_value(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()
