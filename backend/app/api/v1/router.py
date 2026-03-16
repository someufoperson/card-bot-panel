from fastapi import APIRouter

from app.api.v1 import cards, devices, settings

router = APIRouter()

router.include_router(cards.router, prefix="/cards", tags=["cards"])
router.include_router(settings.router, prefix="/settings", tags=["settings"])
router.include_router(devices.router, prefix="/devices", tags=["devices"])
