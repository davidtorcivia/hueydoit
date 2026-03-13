import asyncio
import logging

import httpx
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

from app.config import settings

logger = logging.getLogger(__name__)

HUE_MDNS_TYPE = "_hue._tcp.local."
DISCOVERY_URL = "https://discovery.meethue.com/"


async def discover_bridge() -> str:
    if settings.hue_bridge_ip:
        logger.info("Using configured bridge IP: %s", settings.hue_bridge_ip)
        return settings.hue_bridge_ip

    ip = await _discover_mdns()
    if ip:
        return ip

    ip = await _discover_meethue()
    if ip:
        return ip

    raise RuntimeError(
        "Could not discover Hue bridge. Set HUE_BRIDGE_IP in your environment."
    )


async def _discover_mdns(timeout: float = 10.0) -> str | None:
    logger.info("Attempting mDNS bridge discovery...")
    found_ip: str | None = None
    event = asyncio.Event()

    def on_state_change(zc: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange):
        nonlocal found_ip
        if state_change is ServiceStateChange.Added:
            info = zc.get_service_info(service_type, name)
            if info and info.parsed_addresses():
                found_ip = info.parsed_addresses()[0]
                logger.info("Found Hue bridge via mDNS: %s", found_ip)
                event.set()

    try:
        zc = Zeroconf()
    except OSError as e:
        logger.warning("mDNS discovery unavailable (Zeroconf init failed: %s)", e)
        return None

    browser = ServiceBrowser(zc, HUE_MDNS_TYPE, handlers=[on_state_change])
    try:
        loop = asyncio.get_event_loop()
        await asyncio.wait_for(loop.run_in_executor(None, event.wait), timeout=timeout)
    except asyncio.TimeoutError:
        logger.info("mDNS discovery timed out after %.0fs", timeout)
    except OSError as e:
        logger.warning("mDNS discovery failed: %s", e)
    finally:
        browser.cancel()
        zc.close()

    return found_ip


async def _discover_meethue() -> str | None:
    logger.info("Attempting meethue.com discovery...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(DISCOVERY_URL, timeout=10.0)
            resp.raise_for_status()
            bridges = resp.json()
            if bridges and isinstance(bridges, list):
                ip = bridges[0].get("internalipaddress")
                if ip:
                    logger.info("Found Hue bridge via meethue.com: %s", ip)
                    return ip
    except Exception as e:
        logger.warning("meethue.com discovery failed: %s", e)
    return None
