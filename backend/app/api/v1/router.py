from fastapi import APIRouter

from app.api.v1 import auth, cards, devices, events, groups, pending_cards, settings

router = APIRouter()

router.include_router(auth.router,          prefix="/auth",          tags=["auth"])
router.include_router(cards.router,         prefix="/cards",         tags=["cards"])
router.include_router(settings.router,      prefix="/settings",      tags=["settings"])
router.include_router(devices.router,       prefix="/devices",       tags=["devices"])
router.include_router(events.router,        prefix="/events",        tags=["events"])
router.include_router(pending_cards.router, prefix="/pending-cards", tags=["pending-cards"])
router.include_router(groups.router,        prefix="/groups",        tags=["groups"])
