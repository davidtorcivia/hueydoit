import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings, get_encryption_key
from app.database import init_db
from app.engine.state import state_manager
from app.engine.scheduler import engine_scheduler
from app.bridge.client import bridge_client
from app.bridge.sse_listener import sse_listener
from app.api.routes import router as api_router
from app.api.ws_routes import router as ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Huey Do It...")

    get_encryption_key()
    await init_db()
    await state_manager.load_from_db()

    try:
        connected = await bridge_client.connect()
        if connected:
            await sse_listener.start()
            logger.info("Bridge connected and SSE listener started")
        else:
            logger.warning("Bridge not connected — pair via the UI")
    except Exception as e:
        logger.warning("Bridge connection failed: %s", e)

    try:
        await engine_scheduler.start()
        logger.info("Scheduler started")
    except Exception as e:
        logger.error("Scheduler failed to start: %s", e)

    yield

    logger.info("Shutting down...")
    await engine_scheduler.stop()
    await sse_listener.stop()
    await bridge_client.disconnect()


app = FastAPI(title="Huey Do It", version="1.0.0", lifespan=lifespan)

app.include_router(api_router)
app.include_router(ws_router)

if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
        return HTMLResponse("<h1>Frontend not built</h1>", status_code=404)
else:
    @app.get("/")
    async def no_frontend():
        return HTMLResponse(
            "<h1>Huey Do It</h1><p>Frontend not built. API available at /api/</p>"
        )
