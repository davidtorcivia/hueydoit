import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.ws import ws_manager
from app.database import add_log

logger = logging.getLogger(__name__)


class SSEListener:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._running = False
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())
        logger.info("SSE listener started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("SSE listener stopped")

    async def _listen_loop(self):
        from app.bridge.client import bridge_client

        while self._running:
            if not bridge_client.connected or not bridge_client._bridge:
                await asyncio.sleep(5.0)
                continue

            try:
                bridge = bridge_client._bridge
                self._reconnect_delay = 1.0

                def on_event(event_type, event_data):
                    asyncio.create_task(self._handle_event(event_type, event_data))

                bridge.subscribe(on_event)
                logger.info("Subscribed to bridge events")

                while self._running and bridge_client.connected:
                    await asyncio.sleep(1.0)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("SSE listener error: %s", e)
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, self._max_reconnect_delay
                )

    async def _handle_event(self, event_type, event_data):
        from app.engine.state import state_manager

        try:
            if hasattr(event_data, "id"):
                resource_id = event_data.id
            else:
                return

            from app.database import get_db
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT name, type FROM targets WHERE hue_id = ?",
                    (resource_id,),
                )
                row = await cursor.fetchone()

            if not row:
                return

            target_name = row[0]
            target_type = row[1]

            new_state = {}
            if hasattr(event_data, "on") and event_data.on:
                new_state["on"] = event_data.on.on
            if hasattr(event_data, "dimming") and event_data.dimming:
                new_state["brightness"] = event_data.dimming.brightness
            if hasattr(event_data, "color_temperature") and event_data.color_temperature and hasattr(event_data.color_temperature, "mirek") and event_data.color_temperature.mirek:
                mirek = event_data.color_temperature.mirek
                new_state["color_temp"] = mirek
                new_state["color_hex"] = f"ct:{mirek}"
            elif hasattr(event_data, "color") and event_data.color and event_data.color.xy:
                from app.bridge.effects import xy_to_hex
                new_state["color_xy"] = {"x": event_data.color.xy.x, "y": event_data.color.xy.y}
                new_state["color_hex"] = xy_to_hex(
                    event_data.color.xy.x,
                    event_data.color.xy.y,
                    (event_data.dimming.brightness / 100.0) if event_data.dimming else 1.0,
                )

            if not new_state:
                return

            current = state_manager.get_light_state(target_name)
            state_manager.set_light_state(target_name, {**(current or {}), **new_state})

            active_rule = state_manager.get_active_rule(target_name)
            if active_rule and not self._matches_expected_state(new_state, active_rule):
                timeout = settings.external_override_timeout_min
                expires = datetime.now(timezone.utc) + timedelta(minutes=timeout)
                await state_manager.set_override(
                    target_name,
                    source="external",
                    on_state=new_state.get("on"),
                    brightness=new_state.get("brightness"),
                    color=new_state.get("color_hex"),
                    expires_at=expires,
                )
                await ws_manager.broadcast("override_created", {
                    "target": target_name,
                    "source": "external",
                    "expires_at": expires.isoformat(),
                })
                await add_log("info", "sse", f"External change detected on {target_name}, override created",
                              {"target": target_name, "new_state": new_state})

            await ws_manager.broadcast("light_state", {
                "target": target_name,
                "state": state_manager.get_light_state(target_name),
            })

        except Exception as e:
            logger.error("Error handling SSE event: %s", e)

    def _matches_expected_state(self, new_state: dict, active_rule: dict) -> bool:
        effect = active_rule.get("effect", {})
        if effect.get("mode") == "off":
            return new_state.get("on") is False
        if "on" in new_state and new_state["on"] is False and effect.get("mode") != "off":
            return False
        return True

    @property
    def running(self) -> bool:
        return self._running


sse_listener = SSEListener()
