import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws import ws_manager
from app.engine.state import state_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/api/stream")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        lights = state_manager.get_all_light_states()
        providers = state_manager.get_all_provider_states()
        overrides = await state_manager.get_all_overrides()

        await websocket.send_json({
            "event": "initial_state",
            "data": {
                "lights": lights,
                "providers": providers,
                "overrides": overrides,
            },
        })

        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug("WebSocket error: %s", e)
    finally:
        await ws_manager.disconnect(websocket)
