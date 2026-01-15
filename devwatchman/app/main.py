from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router as api_router
from app.core.config import APP_NAME
from app.core.logging import setup_logging
from app.services.scheduler import SnapshotScheduler
from app.storage.db import init_db

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=APP_NAME)
app.include_router(api_router)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request})


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
