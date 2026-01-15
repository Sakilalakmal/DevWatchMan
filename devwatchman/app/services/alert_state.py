from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AlertState:
    mute_until_utc: datetime | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
