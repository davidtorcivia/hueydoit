import logging

import httpx

from app.config import encrypt_value, decrypt_value
from app.database import get_db

logger = logging.getLogger(__name__)


class PairingError(Exception):
    pass


class LinkButtonNotPressed(PairingError):
    pass


async def pair_bridge(host: str) -> dict:
    url = f"https://{host}/api"
    payload = {"devicetype": "huey-do-it#docker", "generateclientkey": True}

    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.post(url, json=payload, timeout=10.0)
        resp.raise_for_status()
        result = resp.json()

    if isinstance(result, list):
        result = result[0]

    if "error" in result:
        error = result["error"]
        if error.get("type") == 101:
            raise LinkButtonNotPressed("Press the link button on the Hue bridge first")
        raise PairingError(f"Pairing failed: {error.get('description', str(error))}")

    success = result.get("success", result)
    username = success.get("username")
    clientkey = success.get("clientkey", "")

    if not username:
        raise PairingError("Pairing response missing username")

    async with get_db() as db:
        await db.execute("DELETE FROM bridge")
        await db.execute(
            "INSERT INTO bridge (host, username, clientkey) VALUES (?, ?, ?)",
            (host, encrypt_value(username), encrypt_value(clientkey) if clientkey else ""),
        )
        await db.commit()

    logger.info("Successfully paired with bridge at %s", host)
    return {"username": username, "clientkey": clientkey, "host": host}


async def get_stored_credentials() -> tuple[str, str, str] | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT host, username, clientkey FROM bridge LIMIT 1")
        row = await cursor.fetchone()
        if not row:
            return None
        host = row[0]
        username = decrypt_value(row[1])
        clientkey = decrypt_value(row[2]) if row[2] else ""
        return host, username, clientkey


async def clear_credentials():
    async with get_db() as db:
        await db.execute("DELETE FROM bridge")
        await db.commit()
    logger.info("Bridge credentials cleared")
