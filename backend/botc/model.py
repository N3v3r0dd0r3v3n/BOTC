from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from math import floor
from typing import Optional, List, Dict

from botc.prompt import AutoPrompt
from botc.scripts import Script
from botc.scripts import ROLE_REGISTRY


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
    seat: Optional[int] = None
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
class Seat:
    number: int
    player_id: Optional[int] = None


@dataclass
class RoomInfo:
    gid: str
    name: str
    script_name: str
    max_players: int
    story_teller: str = "Mr S Teller"
    status: str = "open"  # open | started | finished
    seats: List[Seat] = None


@dataclass
class Game:
    players: List[Player]
    phase: Phase = Phase.SETUP
    night: int = 0
    pending_dawn: List[int] = field(default_factory=list)
    log: List[str] = field(default_factory=list)
    rules: Optional[object] = None
    script: Optional[Script] = None
    night_order: List[str] = field(default_factory=list)
    current_nomination: Nomination | None = None
    prompt: object = field(default_factory=AutoPrompt)
    force_winner: str | None = None  # "GOOD" or "EVIL"
    current_nomination: Nomination | None = None
    best_nomination: Nomination | None = None  # highest votes this day
    executed_today: Optional[int] = None  # seat id executed (only once per day)
    night_protected: set[int] = field(default_factory=set)  # cleared at start of each night
    last_executed_pid: int | None = None

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
            self.start_day()
        elif self.phase == Phase.DAY:
            self.phase = Phase.VOTING
        elif self.phase == Phase.VOTING:
            self.phase = Phase.EXECUTION
        elif self.phase == Phase.EXECUTION:
            self.finish_day()
            self.phase = Phase.FINAL_CHECK
        elif self.phase == Phase.FINAL_CHECK:
            ended = self.rules.check_end(self) if self.rules else False
            if not ended:
                self.night += 1
                self.phase = Phase.NIGHT
                self.night_protected.clear()
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

        # Virgin check
        target = self.player(target_id)
        if getattr(target.role, "id", "") == "Virgin" and not self.is_poisoned_like(target_id):
            nom = self.player(nominator_id)
            nom_type = getattr(nom.role, "type", None)
            if nom_type == RoleType.TOWNSFOLK and not self.is_poisoned_like(nominator_id):
                self.log.append("Virgin ability triggers: immediate execution")
                self.execute(target_id)  # dusk execution right away
                self.executed_today = target_id
                # Close nomination to stop voting
                self.current_nomination.closed = True

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

        # Butler rule: a Butler may only vote if their chosen master votes
        adjusted_for = n.votes_for
        for voter_id, voted_for in list(n.votes.items()):
            if not voted_for:
                continue
            voter = self.player(voter_id)
            if getattr(voter.role, "id", None) == "Butler":
                master = getattr(voter.role, "master_pid", None)
                if master is None or not n.votes.get(master, False):
                    # remove their 'for' vote
                    n.votes[voter_id] = False
                    adjusted_for -= 1

        n.votes_for = adjusted_for
        passes = n.votes_for >= needed

        voters_for = ", ".join(self.player(v).name for v, ok in n.votes.items() if ok)
        voters_against = ", ".join(self.player(v).name for v, ok in n.votes.items() if not ok)
        self.log.append(
            f"Votes for {self.player(n.target).name}: {n.votes_for} (needed {needed}) → {'MAJORITY' if passes else 'NO MAJORITY'}"
        )
        self.log.append(f"For: {voters_for or '—'} | Against: {voters_against or '—'}")

        # Best-on-block: strictly greater replaces (ties do not)
        if not self.best_nomination or n.votes_for > self.best_nomination.votes_for:
            self.best_nomination = n
        return passes

    def execute(self, pid: int):
        p = self.player(pid)
        # Mayor: if would be executed, no one dies instead (simple interpretation)
        if getattr(p.role, "id", "") == "Mayor":
            self.log.append("Mayor prevents an execution")
            return
        if p.role and hasattr(p.role, "on_execution"):
            p.role.on_execution(self, pid)
        self.mark_dead(pid, "at dusk")
        self.last_executed_pid = pid
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

    def start_day(self):
        self.best_nomination = None
        self.executed_today = None
        # call on_day_start for roles
        for p in self.players:
            if p.role and hasattr(p.role, "on_day_start"):
                p.role.on_day_start(self)

    def finish_day(self):
        """Execute highest on the block if any (ties = no execution)."""
        if self.executed_today is not None:
            return  # already executed via immediate effect or earlier
        n = self.best_nomination
        if not n:
            self.log.append("No execution today")
            return
        # If best_nomination didn't meet majority, do nothing
        if n.votes_for < self.majority_required():
            self.log.append("No execution (no majority)")
            return
        # Check if it is uniquely highest (i.e., no tie).
        # For our simple engine, best_nomination is only updated on strictly greater votes,
        # so a tie will never overwrite; that means ties → no execution.
        self.execute(n.target)

    def is_poisoned(self, pid: int) -> bool:
        # True if any living Poisoner set this pid last night (simple per-night poison)
        for p in self.players:
            if getattr(p.role, "id", None) == "Poisoner" and p.alive:
                if getattr(p.role, "poisoned_pid", None) == pid:
                    return True
        return False

    def is_poisoned_like(self, pid: int) -> bool:
        """Treat Drunk as 'poisoned' for ability correctness."""
        player = self.player(pid)
        return self.is_poisoned(pid) or getattr(player.role, "id", "") == "Drunk"

    def protect(self, pid: int):
        self.night_protected.add(pid)

    def demon_attack(self, target_pid: int):
        """Demon attempts to kill target at night."""
        target = self.player(target_pid)
        if not target.alive:
            return
        # Soldier immunity
        if getattr(target.role, "id", "") == "Soldier":
            self.log.append(f"{target.name} (Soldier) resists the demon")
            return
        # Monk protection
        if target_pid in self.night_protected:
            self.log.append(f"{target.name} is protected from the demon")
            return
        # Normal night death
        self.kill_at_dawn(target_pid)

    def current_night_order(self) -> List[str]:
        if self.script:
            return self.script.first_night if self.night == 1 else self.script.other_nights
        return self.night_order

    def assign_by_names(g, seat_to_role_names: list[str]):
        for seat, role_name in enumerate(seat_to_role_names, start=1):
            if role_name not in ROLE_REGISTRY:  # skip unimplemented
                continue
            g.assign_role(seat, ROLE_REGISTRY[role_name]())


# simple in-memory registry
#rooms: Dict[str, RoomInfo] = {}
