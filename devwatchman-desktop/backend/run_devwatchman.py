from __future__ import annotations

import argparse
import asyncio
import os
import signal
import socket
import sys
import threading
import time
import traceback
from pathlib import Path

import uvicorn


def _bind_listen_socket(host: str, port: int) -> tuple[socket.socket, int]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(2048)
        chosen_port = int(sock.getsockname()[1])
        return sock, chosen_port
    except Exception:
        try:
            sock.close()
        finally:
            pass
        raise


def _resolve_db_path() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        # Fallback for unusual environments; LOCALAPPDATA should exist on Windows.
        local_appdata = str(Path.home() / "AppData" / "Local")

    db_dir = Path(local_appdata) / "DevWatchMan"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "devwatchman.db"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="devwatchman-backend", add_help=True)
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port to bind on 127.0.0.1. Use 0 to choose a free port (recommended).",
    )
    return parser.parse_args(argv)

def _start_parent_watchdog() -> None:
    parent_pid_raw = os.environ.get("DEVWATCHMAN_PARENT_PID")
    if not parent_pid_raw:
        return
    try:
        parent_pid = int(parent_pid_raw)
    except Exception:
        return
    if parent_pid <= 0:
        return

    def _run() -> None:
        try:
            import psutil  # type: ignore
        except Exception:
            return
        while True:
            time.sleep(1.0)
            try:
                if not psutil.pid_exists(parent_pid):
                    os._exit(0)
            except Exception:
                # If we can't check, don't crash the backend.
                continue

    threading.Thread(target=_run, name="parent-watchdog", daemon=True).start()


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(list(sys.argv[1:] if argv is None else argv))
    host = "127.0.0.1"
    if args.port < 0 or args.port > 65535:
        raise ValueError("--port must be in range 0..65535")

    listen_sock, chosen_port = _bind_listen_socket(host, int(args.port))

    # Must be the FIRST stdout line.
    print(f"DEVWATCHMAN_PORT={chosen_port}", flush=True)

    _start_parent_watchdog()

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
        port=chosen_port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)

    def _handle_term(*_args: object) -> None:
        server.should_exit = True

    signal.signal(signal.SIGTERM, _handle_term)
    signal.signal(signal.SIGINT, _handle_term)

    try:
        asyncio.run(server.serve(sockets=[listen_sock]))
    finally:
        try:
            listen_sock.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(1)
