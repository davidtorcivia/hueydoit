import asyncio
import logging
from collections import deque

from aiohue import HueBridgeV2
from aiohue.v2.models.light import Light
from aiohue.v2.models.grouped_light import GroupedLight

from app.bridge.pairing import get_stored_credentials
from app.bridge.discovery import discover_bridge

logger = logging.getLogger(__name__)

MAX_COMMANDS_PER_SECOND = 10


class HueBridgeClient:
    def __init__(self):
        self._bridge: HueBridgeV2 | None = None
        self._host: str = ""
        self._connected: bool = False
        self._command_queue: deque = deque()
        self._throttle_lock = asyncio.Lock()
        self._last_command_time: float = 0

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def host(self) -> str:
        return self._host

    async def connect(self) -> bool:
        creds = await get_stored_credentials()
        if creds:
            host, username, _ = creds
            self._host = host
            try:
                self._bridge = HueBridgeV2(host, username)
                await self._bridge.initialize()
                self._connected = True
                logger.info("Connected to Hue bridge at %s", host)
                return True
            except Exception as e:
                logger.warning("Failed to connect with stored credentials: %s", e)
                self._connected = False

        try:
            host = await discover_bridge()
            self._host = host
            logger.info("Bridge discovered at %s but not yet paired", host)
        except Exception as e:
            logger.warning("Bridge discovery failed: %s", e)

        return False

    async def disconnect(self):
        if self._bridge:
            try:
                await self._bridge.close()
            except Exception:
                pass
            self._bridge = None
        self._connected = False
        logger.info("Disconnected from Hue bridge")

    async def connect_with_credentials(self, host: str, username: str):
        self._host = host
        self._bridge = HueBridgeV2(host, username)
        await self._bridge.initialize()
        self._connected = True
        logger.info("Connected to Hue bridge at %s", host)

    def _get_light_name(self, light: Light) -> str:
        """Get light name from its parent Device via the lights controller."""
        if not self._bridge:
            return light.id
        try:
            device = self._bridge.lights.get_device(light.id)
            if device and device.metadata and device.metadata.name:
                return device.metadata.name
        except Exception:
            pass
        return light.id

    async def get_lights(self) -> list[dict]:
        if not self._bridge or not self._connected:
            return []
        lights = []
        for light in self._bridge.lights:
            xy = None
            if light.color and light.color.xy:
                xy = {"x": light.color.xy.x, "y": light.color.xy.y}
            lights.append({
                "id": light.id,
                "name": self._get_light_name(light),
                "on": light.on.on if light.on else False,
                "brightness": light.dimming.brightness if light.dimming else 0,
                "color_xy": xy,
                "type": "light",
                "reachable": True,
            })
        return lights

    async def get_groups(self) -> list[dict]:
        if not self._bridge or not self._connected:
            return []
        groups = []

        # Build a map of grouped_light id -> GroupedLight object
        gl_map = {gl.id: gl for gl in self._bridge.groups.grouped_light}

        # Rooms and zones both have a services list that references their grouped_light
        for container in list(self._bridge.groups.room) + list(self._bridge.groups.zone):
            name = container.metadata.name if container.metadata else container.id
            # Find the grouped_light service reference
            for svc in (container.services or []):
                if hasattr(svc, 'rtype') and "grouped_light" in str(svc.rtype).lower() and svc.rid in gl_map:
                    gl = gl_map[svc.rid]
                    groups.append({
                        "id": gl.id,
                        "name": name,
                        "on": gl.on.on if gl.on else False,
                        "brightness": gl.dimming.brightness if gl.dimming else 0,
                        "type": "grouped_light",
                    })
                    break

        return groups

    async def set_light_state(self, resource_type: str, hue_id: str, state: dict):
        if not self._bridge or not self._connected:
            logger.warning("Cannot set light state: bridge not connected")
            return

        await self._throttle()

        # Extract parameters from the state dict
        on_val = state.get("on", {}).get("on") if isinstance(state.get("on"), dict) else state.get("on")
        brightness = state.get("dimming", {}).get("brightness") if isinstance(state.get("dimming"), dict) else state.get("brightness")
        color_xy = None
        if isinstance(state.get("color"), dict) and "xy" in state["color"]:
            xy = state["color"]["xy"]
            if isinstance(xy, dict):
                color_xy = (xy.get("x", 0), xy.get("y", 0))
            elif isinstance(xy, (list, tuple)) and len(xy) == 2:
                color_xy = tuple(xy)
        color_temp = None
        if isinstance(state.get("color_temperature"), dict):
            color_temp = state["color_temperature"].get("mirek")
        transition = None
        if isinstance(state.get("dynamics"), dict):
            duration = state["dynamics"].get("duration")
            if duration:
                transition = duration

        try:
            if resource_type == "light":
                light = self._find_light(hue_id)
                if light:
                    kwargs = self._build_kwargs(on_val, brightness, color_xy, color_temp, transition)
                    await self._bridge.lights.set_state(light.id, **kwargs)
            elif resource_type == "grouped_light":
                gl = self._find_grouped_light(hue_id)
                if gl:
                    kwargs = self._build_kwargs(on_val, brightness, color_xy, color_temp, transition)
                    await self._bridge.groups.grouped_light.set_state(gl.id, **kwargs)
            logger.debug("Set %s %s state: %s", resource_type, hue_id, state)
        except Exception as e:
            logger.error("Failed to set %s %s state: %s", resource_type, hue_id, e)
            # Retry with minimal params
            await asyncio.sleep(1.0)
            try:
                kwargs = {}
                if on_val is not None:
                    kwargs["on"] = on_val
                if brightness is not None:
                    kwargs["brightness"] = brightness
                if resource_type == "light":
                    light = self._find_light(hue_id)
                    if light:
                        await self._bridge.lights.set_state(light.id, **kwargs)
                elif resource_type == "grouped_light":
                    gl = self._find_grouped_light(hue_id)
                    if gl:
                        await self._bridge.groups.grouped_light.set_state(gl.id, **kwargs)
            except Exception as retry_err:
                logger.error("Retry also failed for %s %s: %s", resource_type, hue_id, retry_err)

    async def identify_light(self, hue_id: str):
        if not self._bridge or not self._connected:
            return
        light = self._find_light(hue_id)
        if light:
            try:
                await self._bridge.lights.set_flash(light.id, short=True)
            except Exception as e:
                logger.error("Failed to identify light %s: %s", hue_id, e)

    @staticmethod
    def _build_kwargs(on_val, brightness, color_xy, color_temp, transition):
        kwargs = {}
        if on_val is not None:
            kwargs["on"] = on_val
        if brightness is not None:
            kwargs["brightness"] = brightness
        if color_temp is not None:
            kwargs["color_temp"] = color_temp
        elif color_xy is not None:
            kwargs["color_xy"] = color_xy
        if transition is not None:
            kwargs["transition_time"] = transition
        return kwargs

    def _find_light(self, hue_id: str) -> Light | None:
        if not self._bridge:
            return None
        for light in self._bridge.lights:
            if light.id == hue_id:
                return light
        return None

    def _find_grouped_light(self, hue_id: str) -> GroupedLight | None:
        if not self._bridge:
            return None
        for gl in self._bridge.groups.grouped_light:
            if gl.id == hue_id:
                return gl
        return None

    async def _throttle(self):
        async with self._throttle_lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_command_time
            min_interval = 1.0 / MAX_COMMANDS_PER_SECOND
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            self._last_command_time = asyncio.get_event_loop().time()


bridge_client = HueBridgeClient()
