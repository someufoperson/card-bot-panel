from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.v1.router import router as api_router
from app.core.activity_middleware import ActivityMiddleware
from app.core.config import settings
from app.core.database import async_session_factory
from app.core.log_handler import setup_redis_logging
from app.core.redis import close_redis, get_redis
from app.core.security import pwd_context
from app.models.user import User

setup_redis_logging(settings.redis_url, source="backend")


async def _seed_admin():
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.role == "admin"))
        if result.scalar_one_or_none() is None:
            admin = User(
                username=settings.panel_username,
                password_hash=pwd_context.hash(settings.panel_password),
                role="admin",
                must_set_password=False,
            )
            db.add(admin)
            await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()
    await _seed_admin()
    yield
    await close_redis()


app = FastAPI(title="Card Management Panel", version="1.0.0", lifespan=lifespan)

app.add_middleware(ActivityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
