from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.api.routes import router as api_router
from app.core.config import APP_NAME
from app.core.logging import setup_logging
from app.core.profiles import get_active_profile_name, resolve_profile, set_active_profile_name
from app.services.alert_state import AlertState
from app.services.profile_state import ProfileState
from app.services.scheduler import SnapshotScheduler
from app.services.retention import RetentionService
from app.services.ws_manager import WebSocketManager
from app.storage.db import init_db
from app.storage.db import get_connection
from app.storage.alerts import get_alert_setting
from app.storage.events import insert_event

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=APP_NAME)
app.include_router(api_router)
app.state.ws_manager = WebSocketManager()
app.state.alert_state = AlertState()
app.state.profile_state = ProfileState()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.websocket("/ws/live")
async def ws_live(ws: WebSocket) -> None:
    manager: WebSocketManager = app.state.ws_manager
    await manager.connect(ws)
    try:
        from datetime import datetime, timezone

        await ws.send_json(
            {
                "type": "hello",
                "v": 1,
                "server_time_utc": datetime.now(timezone.utc).isoformat(),
                "message": "connected",
            }
        )
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(ws)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    from datetime import datetime, timezone

    ts_utc = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        try:
            event_id = insert_event(
                conn,
                {
                    "ts_utc": ts_utc,
                    "kind": "app_started",
                    "message": f"{APP_NAME} started",
                    "severity": "info",
                },
            )
            try:
                await app.state.ws_manager.broadcast_json(
                    {
                        "type": "timeline_event",
                        "v": 1,
                        "ts_utc": ts_utc,
                        "data": {
                            "id": event_id,
                            "kind": "app_started",
                            "severity": "info",
                            "message": f"{APP_NAME} started",
                        },
                    }
                )
            except Exception:
                pass
        except Exception:
            logger.exception("Failed to insert app_started event")

        mute_until = get_alert_setting(conn, "mute_until_utc")
    if mute_until:
        try:
            dt = datetime.fromisoformat(mute_until)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            app.state.alert_state.mute_until_utc = dt
        except Exception:
            app.state.alert_state.mute_until_utc = None

    stored_profile = get_active_profile_name()
    profile = resolve_profile(stored_profile)
    app.state.profile_state.active_name = profile.name
    if stored_profile != profile.name:
        try:
            set_active_profile_name(profile.name)
        except Exception:
            pass

    scheduler = SnapshotScheduler(
        ws_manager=app.state.ws_manager,
        alert_state=app.state.alert_state,
        profile_state=app.state.profile_state,
    )
    scheduler.start()
    app.state.scheduler = scheduler

    retention = RetentionService(interval_seconds=60)
    retention.start()
    app.state.retention = retention
    logger.info("%s started", APP_NAME)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    scheduler: SnapshotScheduler | None = getattr(app.state, "scheduler", None)
    if scheduler is not None:
        await scheduler.stop()
    retention: RetentionService | None = getattr(app.state, "retention", None)
    if retention is not None:
        await retention.stop()
    manager: WebSocketManager | None = getattr(app.state, "ws_manager", None)
    if manager is not None:
        await manager.close_all()
    logger.info("%s stopped", APP_NAME)
