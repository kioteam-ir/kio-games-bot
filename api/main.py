from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from redis.asyncio import Redis

import bot.i18n_bootstrap  # noqa: F401
from api.config.database import DatabaseConfigClass
from api.infrastructure.database.connection import close_database, init_database
from api.presentation.routes.admin import router as admin_router
from api.presentation.routes.games import router as games_router
from bot.config.redis import RedisConfigClass
from bot.config.session import SessionConfigClass
from bot.core.container import AppContainer


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_database(DatabaseConfigClass())
    session_cfg = SessionConfigClass()
    redis_client: Redis | None = None
    if session_cfg.session_backend == "redis":
        redis_client = Redis.from_url(RedisConfigClass().redis_url, decode_responses=False)
    container = AppContainer.build(redis_client=redis_client)
    app.state.container = container
    yield
    await container.close()
    await close_database()


app = FastAPI(title="Kio Games API", lifespan=lifespan)
app.include_router(admin_router)
app.include_router(games_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def run() -> None:
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    run()
