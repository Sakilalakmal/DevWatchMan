from __future__ import annotations

import asyncio
from dataclasses import dataclass, field


@dataclass
class ProfileState:
    active_name: str = "default"
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

