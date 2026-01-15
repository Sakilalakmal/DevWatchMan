from __future__ import annotations

import asyncio
import logging
from typing import Any

from starlette.websockets import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(ws)

    async def broadcast_json(self, message: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._connections)

        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)
            for ws in dead:
                try:
                    await ws.close(code=1001)
                except Exception:
                    pass

    async def close_all(self, code: int = 1001) -> None:
        async with self._lock:
            targets = list(self._connections)
            self._connections.clear()

        for ws in targets:
            try:
                await ws.close(code=code)
            except Exception:
                pass

