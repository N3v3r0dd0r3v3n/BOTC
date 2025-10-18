from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from math import floor
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
class Nomination:
    nominator: int
    target: int
    votes_for: int = 0
    closed: bool = False

@dataclass
class Game:
    players: List[Player]
    phase: Phase = Phase.SETUP
    night: int = 0
    pending_dawn: List[int] = field(default_factory=list)
    log: List[str] = field(default_factory=list)
    rules: Optional[object] = None
    night_order: List[str] = field(default_factory=list)
    current_nomination: Nomination | None = None

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

    # --- Voting helpers ---
    def majority_required(self) -> int:
        alive = len(self.alive_players())
        # In BotC you need strictly more than half the living players
        return floor(alive / 2) + 1

    def start_nomination(self, nominator_id: int, target_id: int):
        assert self.phase == Phase.DAY
        assert self.player(nominator_id).alive and self.player(target_id).alive
        self.current_nomination = Nomination(nominator=nominator_id, target=target_id)
        self.log.append(f"Nomination: {self.player(nominator_id).name} nominates {self.player(target_id).name}")

    def cast_vote(self, voter_id: int, vote_for: bool):
        assert self.current_nomination and not self.current_nomination.closed
        assert self.player(voter_id).alive
        if vote_for:
            self.current_nomination.votes_for += 1

    def close_nomination(self) -> bool:
        """Return True if execution passes."""
        assert self.current_nomination and not self.current_nomination.closed
        self.current_nomination.closed = True
        passes = self.current_nomination.votes_for >= self.majority_required()
        n = self.current_nomination
        self.log.append(f"Votes for {self.player(n.target).name}: {n.votes_for} "
                        f"(needed {self.majority_required()}) → {'EXECUTE' if passes else 'NO EXECUTION'}")
        return passes

    def execute(self, pid: int):
        """Dusk execution."""
        self.player(pid).alive = False
        self.log.append(f"{self.player(pid).name} is executed at dusk")


