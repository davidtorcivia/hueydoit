"""Watchdog liveness detection.

The failure this exists for is silent: the event loop wedges, the container
still reports "up", and the lights stop responding until someone notices.
"""
import time
from unittest.mock import patch

from app import watchdog


def test_heartbeat_resets_the_clock():
    watchdog.heartbeat()
    assert watchdog.seconds_since_beat() < 1.0


def test_a_fresh_heartbeat_is_not_stalled():
    watchdog.heartbeat()
    assert watchdog.is_stalled(60) is False


def test_a_quiet_heartbeat_is_stalled():
    watchdog._last_beat = time.monotonic() - 1200
    assert watchdog.is_stalled(60) is True
    watchdog.heartbeat()


def test_zero_disables_the_check_entirely():
    watchdog._last_beat = time.monotonic() - 99999
    assert watchdog.is_stalled(0) is False
    watchdog.heartbeat()


def test_disabled_watchdog_starts_no_thread():
    watchdog._thread = None
    with patch("threading.Thread") as thread:
        watchdog.start(0)
    thread.assert_not_called()
    assert watchdog._thread is None


def test_stalled_loop_exits_the_process():
    """End to end: a real watcher thread must call os._exit so the restart
    policy can recover. This is the whole point of the module."""
    exits = []
    watchdog._thread = None
    with patch("os._exit", side_effect=lambda code: exits.append(code)):
        watchdog.start(stall_seconds=1, check_interval=0.05)
        watchdog._last_beat = time.monotonic() - 9999
        for _ in range(100):
            if exits:
                break
            time.sleep(0.02)
    assert exits and exits[0] == 1, "watchdog should have exited with status 1"
    watchdog.heartbeat()
    watchdog._thread = None


def test_start_is_idempotent():
    watchdog._thread = None
    watchdog.heartbeat()
    watchdog.start(stall_seconds=3600, check_interval=3600)
    first = watchdog._thread
    watchdog.start(stall_seconds=3600, check_interval=3600)
    assert watchdog._thread is first, "should not spawn a second watcher"
