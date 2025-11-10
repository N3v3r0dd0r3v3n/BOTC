from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Callable, Any, Set

from botc.prompt import AutoPrompt
from botc.scripts import ROLE_REGISTRY
from botc.scripts import Script

Noop = lambda ev: None


class TaskStatus(Enum):
    PENDING = auto()
    DONE = auto()

@dataclass
class SetupTask:
    id: int
    kind: str
    role: str
    owner_id: int
    prompt: str
    options: List[int]
    payload: Dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING


class Team(Enum):
    GOOD = auto()
    EVIL = auto()


class RoleType(Enum):
    TOWNSFOLK = auto()
    OUTSIDER = auto()
    MINION = auto()
    DEMON = auto()


class Phase(Enum):
    CREATE = auto()
    SETUP = auto()
    NIGHT = auto()
    DAY = auto()
    VOTING = auto()
    EXECUTION = auto()
    FINAL_CHECK = auto()


@dataclass
class Spectator:
    id: int
    name: str


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
    storyteller_id: int
    storyteller_name: str
    script_name: str
    status: str = "open"  # open | started | finished


@dataclass(frozen=True)
class DomainEvent:
    type: str  # e.g. "NominationStarted", "VirginTriggered", "PlayerExecuted"
    data: Dict[str, Any]  # payload


@dataclass
class NightOneInfo:
    demon_id: Optional[int] = None
    minion_ids: List[int] = field(default_factory=list)
    demon_bluffs: List[str] = field(default_factory=list)  # role names, not in play


@dataclass
class Game:
    slots: List[str]
    players: List[Player]
    roles_by_slot: dict[int, str] = field(default_factory=dict)
    phase: Phase = Phase.CREATE
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
    _emit: Callable[[DomainEvent], None] = Noop
    wake_list: List[Dict] = field(default_factory=list)
    wake_index = -1
    n1_info = NightOneInfo()

    def setup(self):
        deck = self._build_role_deck()
        for role, slot in zip(deck, self.slots):
            self.roles_by_slot[slot] = role
            player = self.player(slot)
            player.role = role

    def request_setup_task(self, *, kind: str, role: str, owner_id: int,
                           prompt: str, options: list[int] | None = None,
                           payload: dict | None = None) -> None:
        self._emit(DomainEvent("SetupTaskRequested", {
            "kind": kind,
            "role": role,
            "owner_id": owner_id,
            "prompt": prompt,
            "options": options or [],
            "payload": payload or {},
        }))

    def _build_role_deck(self) -> list[str]:
        import importlib, pkgutil, botc.roles

        # dynamically import role modules without touching roles.__init__ imports
        for _, modname, _ in pkgutil.iter_modules(botc.roles.__path__, prefix="botc.roles."):
            importlib.import_module(modname)
        counts = self.script.role_counts.get(len(self.players))
        if not counts:
            raise ValueError(f"Unsupported player count: {len(self.players)}")

        # Safety checks
        for k in ("townsfolk", "outsiders", "minions", "demons"):
            need = counts.get(k, 0)
            have = len(self.script.role_groups[k])
            if need > have:
                raise ValueError(f"Not enough roles in group '{k}': need {need}, have {have}")

        role_selections = []
        role_selections += random.sample(self.script.role_groups["townsfolk"], counts["townsfolk"])
        role_selections += random.sample(self.script.role_groups["outsiders"], counts["outsiders"])
        role_selections += random.sample(self.script.role_groups["minions"], counts["minions"])
        role_selections += random.sample(self.script.role_groups["demons"], counts["demons"])

        if len(role_selections) != len(self.players):
            raise AssertionError("Role deck size does not match player count")

        deck = [ROLE_REGISTRY.get(role)() for role in role_selections]

        random.shuffle(deck)
        return deck

    def player(self, pid: str) -> Player:
        return next(p for p in self.players if p.id == pid)

    def alive_players(self) -> List[Player]:
        return [p for p in self.players if p.alive]

    def advance(self) -> Phase:
        """Leave current phase, enter next phase, stay there, and return the new current phase."""
        cur = self.phase
        self._on_exit(cur)
        self.phase = self._next_phase(cur)
        self._on_enter(self.phase)
        # Broadcast here rather than in the handler?
        return self.phase

    @staticmethod
    def _next_phase(p: Phase) -> Phase:
        return {
            Phase.CREATE: Phase.SETUP,
            Phase.SETUP: Phase.NIGHT,
            Phase.NIGHT: Phase.DAY,
            Phase.DAY: Phase.VOTING,
            Phase.VOTING: Phase.EXECUTION,
            Phase.EXECUTION: Phase.FINAL_CHECK,
            Phase.FINAL_CHECK: Phase.NIGHT,
        }[p]

    def _on_exit(self, p: Phase) -> None:
        if p == Phase.NIGHT:
            # resolve dawn deaths
            for pid in self.pending_dawn:
                self.mark_dead(pid, "at dawn")
            self.pending_dawn.clear()
        elif p == Phase.EXECUTION:
            self.finish_day()

    def _on_enter(self, p: Phase) -> None:
        if p == Phase.SETUP:
            print("Setting up")
            self._setup()
        if p == Phase.NIGHT:
            # increment night on entry
            self.night = 1 if self.night == 0 else self.night + 1
            self.night_protected.clear()

            if self.night == 1:
                self._compute_night_one_info()

            self.wake_list = self.build_wake_list()
            self.wake_index = 0

            self._emit(DomainEvent("NightPrepared", {
                "night": self.night,
                "wake_list": self.wake_list
            }))

        elif p == Phase.DAY:
            self.start_day()

    def _setup(self):
        for player in self.players:
            role = getattr(player, "role", None)
            if not role:
                continue
            if getattr(role, "owner", None) != player.id:
                setattr(role, "owner", player.id)
            if getattr(role, "on_setup"):
                role.on_setup(self)

    def start_day(self) -> None:
        # ready the day; call role hooks later as needed
        # self.best_nomination = None
        # self.executed_today = None
        pass

    def finish_day(self) -> None:
        # resolve block, if any
        pass

    def start_day(self):
        return
        self.best_nomination = None
        self.executed_today = None
        # call on_day_start for roles
        for p in self.players:
            if p.role and hasattr(p.role, "on_day_start"):
                p.role.on_day_start(self)

    def finish_day(self):
        return
        # Execute highest on the block if any (ties = no execution).
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

    def build_wake_list(self) -> List[Dict]:
        self.wake_list = []
        self.wake_index = -1

        # map role name -> player
        alive_by_role: Dict[str, int] = {}
        for p in self.players:
            if not p.alive:
                continue
            r = getattr(p, "role", None)
            if not r:
                continue
            # r.name should match the strings in the Script
            alive_by_role[r.id] = p.id

        order = self.script.night_order(self.night)

        for role_name in order:
            pid = alive_by_role.get(role_name)
            if pid is None:
                continue  # role not in play or dead
            pl = self.player(pid)  # assume you have g.player(id)
            self.wake_list.append({
                "role": role_name,
                "owner": pid,
                "name": pl.name
            })

        return self.wake_list

    def _compute_night_one_info(self):
        """Call this once after setup, before Night 1 starts."""
        # Identify demon and minions in play
        demon = None
        minions = []
        in_play_role_names: Set[str] = set()

        for p in self.players:
            if not getattr(p, "role", None):
                continue
            in_play_role_names.add(p.role.id)
            rtype = getattr(p.role, "type", None)
            if rtype == RoleType.DEMON:
                demon = p
            elif rtype == RoleType.MINION:
                minions.append(p)

        demon_id = demon.id if demon else None
        minion_ids = [m.id for m in minions]

        # Choose 3 bluff roles from townsfolk not in play
        townsfolk_all = set(self.script.role_groups.get("townsfolk", []))
        available_bluffs = list(townsfolk_all - in_play_role_names)
        random.shuffle(available_bluffs)
        bluffs = available_bluffs[:3]

        self.n1_info = NightOneInfo(
            demon_id=demon_id,
            minion_ids=minion_ids,
            demon_bluffs=bluffs
        )

    """
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
        #Mark a player dead, grant ghost vote, call hooks, and handle specials.
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

   

    

    def is_poisoned(self, pid: int) -> bool:
        # True if any living Poisoner set this pid last night (simple per-night poison)
        for p in self.players:
            if getattr(p.role, "id", None) == "Poisoner" and p.alive:
                if getattr(p.role, "poisoned_pid", None) == pid:
                    return True
        return False

    def is_poisoned_like(self, pid: int) -> bool:
        #Treat Drunk as 'poisoned' for ability correctness.
        player = self.player(pid)
        return self.is_poisoned(pid) or getattr(player.role, "id", "") == "Drunk"

    def protect(self, pid: int):
        self.night_protected.add(pid)

    def demon_attack(self, target_pid: int):
        #Demon attempts to kill target at night.
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
    """




