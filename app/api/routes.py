from fastapi import APIRouter

from app.api.status import router as status_router
from app.api.lights import router as lights_router
from app.api.rules import router as rules_router
from app.api.providers import router as providers_router
from app.api.holidays import router as holidays_router
from app.api.overrides import router as overrides_router
from app.api.bridge import router as bridge_router
from app.api.logs import router as logs_router

router = APIRouter()
router.include_router(status_router)
router.include_router(lights_router)
router.include_router(rules_router)
router.include_router(providers_router)
router.include_router(holidays_router)
router.include_router(overrides_router)
router.include_router(bridge_router)
router.include_router(logs_router)
