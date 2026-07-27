"""Liveness watchdog.

`restart: unless-stopped` only helps when the process dies. If the event loop
wedges — a bridge call that never returns, a blocking library — the container
stays "up" and the lights simply stop responding, with nothing to recover it.
That failure is silent and can last months on a service like this.

A plain thread (not a coroutine, so a stalled event loop can't take it down with
it) watches for scheduler heartbeats and exits the process if they stop. The
restart policy then does the recovery.
"""
import logging
import os
import threading
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_last_beat = time.monotonic()
_lock = threading.Lock()
_thread: threading.Thread | None = None


def heartbeat():
    """Called from the scheduler's periodic job to signal the loop is alive."""
    global _last_beat
    with _lock:
        _last_beat = time.monotonic()


def seconds_since_beat() -> float:
    with _lock:
        return time.monotonic() - _last_beat


def is_stalled(stall_seconds: int) -> bool:
    """Whether the heartbeat has been quiet longer than allowed."""
    return stall_seconds > 0 and seconds_since_beat() > stall_seconds


def start(stall_seconds: int, check_interval: int = 60):
    """Begin watching. stall_seconds <= 0 disables the watchdog entirely."""
    global _thread

    if stall_seconds <= 0:
        logger.info("Watchdog disabled")
        return
    if _thread and _thread.is_alive():
        return

    heartbeat()

    def _watch():
        while True:
            time.sleep(check_interval)
            if is_stalled(stall_seconds):
                stalled = seconds_since_beat()
                logger.critical(
                    "Watchdog: no scheduler heartbeat for %.0fs (limit %ds) at %s — "
                    "exiting so the restart policy can recover",
                    stalled, stall_seconds, datetime.now(timezone.utc).isoformat(),
                )
                # Flush before a hard exit; a graceful shutdown would need the
                # event loop we have just decided is not running.
                for handler in logging.getLogger().handlers:
                    try:
                        handler.flush()
                    except Exception:
                        pass
                os._exit(1)

    _thread = threading.Thread(target=_watch, name="watchdog", daemon=True)
    _thread.start()
    logger.info("Watchdog started (stall limit %ds)", stall_seconds)
