from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List


class Team(Enum):
    GOOD = auto()
    EVIL = auto()


class RoleType(Enum):
    TOWNSFOLK = auto()
    OUTSIDER = auto()
    MINION = auto()
    DEMON = auto()


class Phase(Enum):
    SETUP = auto()
    NIGHT = auto()
    DAY = auto()
    VOTING = auto()
    EXECUTION = auto()
    FINAL_CHECK = auto()


@dataclass
class Player:
    id: int
    name: str
    seat: int
    alive: bool = True
    role: Optional[object] = None


@dataclass
class Game:
    players: List[Player]
    phase: Phase = Phase.SETUP
    night: int = 0
    pending_dawn: List[int] = field(default_factory=list)
    log: List[str] = field(default_factory=list)
    rules: Optional[object] = None
    night_order: List[str] = field(default_factory=list)

    def player(self, pid: int) -> Player:
        return next(p for p in self.players if p.id == pid)

    def alive_players(self) -> List[Player]:
        return [p for p in self.players if p.alive]

    def alive_others(self, pid: int) -> List[Player]:
        return [p for p in self.alive_players() if p.id != pid]

    def assign_role(self, pid: int, role: object):
        p = self.player(pid)
        p.role = role
        setattr(role, "owner", pid)

    def kill_at_dawn(self, pid: int):
        if pid not in self.pending_dawn:
            self.pending_dawn.append(pid)

    def kill_now(self, pid: int):
        self.player(pid).alive = False
        self.log.append(f"Player {pid} dies immediately")

    def step(self):
        if self.phase == Phase.SETUP:
            self.phase = Phase.NIGHT
            self.night = 1
        elif self.phase == Phase.NIGHT:
            for pid in self.pending_dawn:
                self.player(pid).alive = False
                self.log.append(f"Player {pid} dies at dawn")
            self.pending_dawn.clear()
            self.phase = Phase.DAY
        elif self.phase == Phase.DAY:
            self.phase = Phase.VOTING
        elif self.phase == Phase.VOTING:
            self.phase = Phase.EXECUTION
        elif self.phase == Phase.EXECUTION:
            self.phase = Phase.FINAL_CHECK
        elif self.phase == Phase.FINAL_CHECK:
            ended = self.rules.check_end(self) if self.rules else False
            if not ended:
                self.night += 1
                self.phase = Phase.NIGHT
        return self.phase
