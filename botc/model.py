from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from math import floor
from typing import Optional, List, Dict

from botc.prompt import AutoPrompt


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
    ghost_vote_available: bool = False


@dataclass
class Nomination:
    nominator: int
    target: int
    votes_for: int = 0
    closed: bool = False
    votes: Dict[int, bool] = field(default_factory=dict)  # voter_id -> True/False


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
    prompt: object = field(default_factory=AutoPrompt)
    force_winner: str | None = None  # "GOOD" or "EVIL"

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
        self.mark_dead(pid, "immediately")

    def step(self):
        if self.phase == Phase.SETUP:
            self.phase = Phase.NIGHT
            self.night = 1
        elif self.phase == Phase.NIGHT:
            for pid in self.pending_dawn:
                self.mark_dead(pid, "at dawn")
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
        voter = self.player(voter_id)

        can_vote_alive = voter.alive
        can_vote_dead = (not voter.alive) and voter.ghost_vote_available
        if not (can_vote_alive or can_vote_dead):
            return

        prev = self.current_nomination.votes.get(voter_id)
        if prev is True and vote_for is False:
            self.current_nomination.votes_for -= 1
        if prev is False and vote_for is True:
            self.current_nomination.votes_for += 1
        if prev is None and vote_for is True:
            self.current_nomination.votes_for += 1
        self.current_nomination.votes[voter_id] = vote_for

        if not voter.alive and voter.ghost_vote_available:
            voter.ghost_vote_available = False

    def close_nomination(self) -> bool:
        assert self.current_nomination and not self.current_nomination.closed
        n = self.current_nomination
        n.closed = True
        needed = self.majority_required()
        passes = n.votes_for >= needed

        voters_for = ", ".join(self.player(v).name for v, ok in n.votes.items() if ok)
        voters_against = ", ".join(self.player(v).name for v, ok in n.votes.items() if not ok)

        self.log.append(
            f"Votes for {self.player(n.target).name}: {n.votes_for} (needed {needed}) → {'EXECUTE' if passes else 'NO EXECUTION'}")
        self.log.append(f"For: {voters_for or '—'} | Against: {voters_against or '—'}")
        return passes

    def execute(self, pid: int):
        p = self.player(pid)
        if p.role and hasattr(p.role, "on_execution"):
            p.role.on_execution(self, pid)
        self.mark_dead(pid, "at dusk")
        self.log.append(f"{p.name} is executed at dusk")

    def mark_dead(self, pid: int, cause: str):
        """Mark a player dead, grant ghost vote, call hooks, and handle specials."""
        p = self.player(pid)
        if not p.alive:
            return  # already dead; ignore duplicates
        p.alive = False
        p.ghost_vote_available = True
        self.log.append(f"{p.name} dies {cause}")
        # role death hook
        if p.role and hasattr(p.role, "on_death"):
            p.role.on_death(self)
        # special: Scarlet Woman promotion if a Demon just died
        self._maybe_promote_scarlet_woman_on_demon_death(pid)

    def _maybe_promote_scarlet_woman_on_demon_death(self, dead_pid: int):
        dead = self.player(dead_pid)
        if getattr(dead.role, "type", None) != RoleType.DEMON:
            return
        # Only if 5+ players are alive *after* this death
        if len(self.alive_players()) < 5:
            return
        # Find a living Scarlet Woman
        sw = next((p for p in self.alive_players()
                   if getattr(p.role, "id", None) == "Scarlet Woman"), None)
        if not sw:
            return
        # Promote her to Demon (Imp). Local import avoids circulars.
        from botc.roles.imp import Imp
        self.assign_role(sw.id, Imp())
        self.log.append(f"{sw.name} becomes the Imp (Scarlet Woman)")



