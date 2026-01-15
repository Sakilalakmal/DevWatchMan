from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import APP_NAME
from app.core.logging import setup_logging
from app.services.scheduler import SnapshotScheduler
from app.storage.db import init_db

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=APP_NAME)
app.include_router(api_router)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    scheduler = SnapshotScheduler()
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("%s started", APP_NAME)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    scheduler: SnapshotScheduler | None = getattr(app.state, "scheduler", None)
    if scheduler is not None:
        await scheduler.stop()
    logger.info("%s stopped", APP_NAME)
