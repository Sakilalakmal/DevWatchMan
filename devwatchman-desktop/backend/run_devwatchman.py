from __future__ import annotations

import os
import signal
import socket
import sys
from pathlib import Path

import uvicorn


def _pick_free_port(host: str, start: int = 8000, end: int = 8010) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No free port available in range {start}-{end}")


def _resolve_db_path() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        # Fallback for unusual environments; LOCALAPPDATA should exist on Windows.
        local_appdata = str(Path.home() / "AppData" / "Local")

    db_dir = Path(local_appdata) / "DevWatchMan"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "devwatchman.db"


def main() -> None:
    host = "127.0.0.1"
    port = _pick_free_port(host)

    # Must be the FIRST stdout line.
    print(f"DEVWATCHMAN_PORT={port}", flush=True)

    # Ensure backend source is importable.
    backend_root = Path(__file__).resolve().parent / "devwatchman"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    # Override DB location without changing backend business logic.
    db_path = _resolve_db_path()
    import app.core.config as core_config

    core_config.DB_PATH = db_path
    try:
        import app.storage.db as storage_db

        storage_db.DB_PATH = db_path
    except Exception:
        # If storage module fails to import for any reason, uvicorn startup will surface it.
        pass

    from app.main import app as fastapi_app

    config = uvicorn.Config(
        fastapi_app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)

    def _handle_term(*_args: object) -> None:
        server.should_exit = True

    signal.signal(signal.SIGTERM, _handle_term)
    signal.signal(signal.SIGINT, _handle_term)

    server.run()


if __name__ == "__main__":
    main()
