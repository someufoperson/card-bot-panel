from fastapi import APIRouter

router = APIRouter()

# Роутеры подключаются по мере реализации
# from app.api.v1 import cards, transactions, devices, settings
# router.include_router(cards.router, prefix="/cards", tags=["cards"])
# router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
# router.include_router(devices.router, prefix="/devices", tags=["devices"])
# router.include_router(settings.router, prefix="/settings", tags=["settings"])
