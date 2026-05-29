from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.config.database import DatabaseConfigClass
from api.infrastructure.database.connection import close_database, init_database
from api.presentation.routes.admin import router as admin_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_database(DatabaseConfigClass())
    yield
    await close_database()


app = FastAPI(title="Kio Games API", lifespan=lifespan)
app.include_router(admin_router)


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
