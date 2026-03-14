from fastapi import APIRouter, HTTPException

from app.database import add_log
from app.bridge.client import bridge_client
from app.bridge.discovery import discover_bridge
from app.bridge.pairing import pair_bridge, get_stored_credentials, LinkButtonNotPressed

router = APIRouter(prefix="/api")


@router.post("/bridge/pair")
async def pair_bridge_endpoint():
    try:
        if bridge_client.host:
            host = bridge_client.host
        else:
            host = await discover_bridge()
        result = await pair_bridge(host)
        await bridge_client.connect_with_credentials(host, result["username"])
        await add_log("info", "bridge", f"Paired with bridge at {host}")
        return {"paired": True, "host": host}
    except LinkButtonNotPressed:
        raise HTTPException(428, "Press the link button on the Hue bridge first")
    except Exception as e:
        raise HTTPException(500, f"Pairing failed: {e}")


@router.get("/bridge/status")
async def bridge_status():
    creds = await get_stored_credentials()
    return {
        "connected": bridge_client.connected,
        "host": bridge_client.host,
        "paired": creds is not None,
    }
