from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import APP_NAME
from app.storage.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title=APP_NAME)
app.include_router(api_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("%s started", APP_NAME)
