from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal

RoomStatus = Literal["open", "started", "finished"]


@dataclass(frozen=True)
class Seat:
    number: int
    player_id: Optional[int] = None


@dataclass
class RoomInfo:
    gid: str
    name: str
    script_name: str
    max_players: int
    status: RoomStatus = "open"
