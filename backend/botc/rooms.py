from __future__ import annotations

from collections import defaultdict
from typing import List, Set, Dict

# spectator_joined_message
# player_taken_seat,
from botc.messages import player_vacated_seat, player_left_message, \
    role_assigned_info_message, night_prepared_message
from botc.model import RoomInfo, Game, DomainEvent, SetupTask, TaskStatus, Phase
from botc.scripts import Script
from botc.view import view_for_player, view_for_storyteller, view_for_room
from botc.ws.prompt_bus import PromptBus
from botc.model import Player
from botc.model import Spectator


class GameRoom:
    def __init__(self, gid: str, name: str, script: Script, creator, initial_seat_count: int = 5):
        self.min_residents = 5
        self.max_residents = 20
        self.script = script
        self.info = RoomInfo(
            gid=gid,
            name=name,
            script_name=script.name,
            storyteller_name=creator['name'],
            storyteller_id=creator['id']
        )
        self.bus = PromptBus()
        self.spectators: List[Spectator] = []
        self.players: List[Player] = []
        self.seats = [{"seat": i + 1, "occupant": None} for i in range(initial_seat_count)]
        self.game: Game | None = None

        self.room_viewers: Set["RoomViewerSocket"] = set()
        self.player_sockets: Dict[int, Set] = defaultdict(set)

        self.storytellerSocket = None  # set by StorytellerSocket.open

        self._next_task_id = 1
        self.setup_tasks: List[SetupTask] = []

    # ---------------------------
    # Room viewers (spectators of the room state, not players)
    # ---------------------------
    def add_room_viewer(self, sock):
        self.room_viewers.add(sock)

    def remove_room_viewer(self, sock):
        self.room_viewers.discard(sock)

    # ---------------------------
    # Seats management
    # ---------------------------
    def update_max_seats(self, new_max: int) -> tuple[bool, str | None]:
        if new_max < self.min_residents:
            return False, "min_seats_is_5"
        if new_max > self.max_residents:
            return False, "max_seats_is_20"

        occupied = sum(1 for s in self.seats if s["occupant"] is not None)
        if new_max < occupied:
            return False, "cannot_reduce_below_occupied_seats"

        current = len(self.seats)

        if new_max > current:
            for i in range(current, new_max):
                self.seats.append({"seat": i + 1, "occupant": None})
        elif new_max < current:
            for i in range(current - 1, -1, -1):
                seat = self.seats[i]
                if seat["occupant"] is None:
                    self.seats.pop(i)
                    break

        self.broadcast()
        return True, None

    # ---------------------------
    # Players (pre-game)
    # ---------------------------
    def is_full(self) -> bool:
        # If you track max players elsewhere, adjust this check accordingly.
        # Fallback: cannot exceed seat count.
        return len([s for s in self.seats if s["occupant"] is not None]) >= len(self.seats)

    def add_player(self, player_name: str) -> dict | None:
        if getattr(self.info, "status", "open") != "open":
            return None
        free_seats = [s for s in self.seats if s["occupant"] is None]
        if not free_seats:
            return None

        seat_no = free_seats[0]["seat"]
        p = Player(id=seat_no, name=player_name, seat=seat_no)
        free_seats[0]["occupant"] = p
        self.players.append(p)

        return {"id": p.id, "seat": p.seat, "name": p.name}

    # ---------------------------
    # Start Game
    # ---------------------------
    def start_game(self) -> bool:
        if len(self.players) < self.min_residents:
            return False

        # a bit naughty but roles should be assigned to seats, not players!
        # what happens if a player leaves a seat and a new one joins?  they'd be the role that the other person was!

        # collapse to occupied seats only
        self.seats = [seat for seat in self.seats if seat["occupant"] is not None]

        slots = [seat["occupant"].id for seat in self.seats if seat["occupant"]]

        # Clear out any player roles (seat roles too once i've fixed that poor design decision)
        for player in self.players:
            player.role = None

        self.game = Game(
            slots=slots,
            players=self.players,
            script=self.script
        )

        # Broadcast here to clear out existing roles etc
        self.broadcast()

        # Single domain event hook
        self.game._emit = self.domain_event
        self.info.status = "In-play"

        # Assign roles and run role on_setup (roles may request setup tasks)
        self.game.setup()
        # Only storyteller knows roles at this point.
        self.send_to_storyteller({"type": "state", "view": view_for_storyteller(self.game, self)})
        return True

    # ---------------------------
    # Messaging to ST and clients
    # ---------------------------
    def send_to_storyteller(self, msg):
        import json
        if not self.storytellerSocket:
            return
        if isinstance(msg, str):
            self.storytellerSocket.write_message(msg)
        else:
            self.storytellerSocket.write_message(json.dumps(msg))

    def _notify_st(self, msg: dict) -> None:
        if getattr(self, "storytellerSocket", None):
            self.storytellerSocket.send(msg)

    def broadcast(self):
        # players (per-player view)
        for pid, socks in list(self.player_sockets.items()):
            msg = {"type": "state", "view": view_for_player(self.game, pid, self)}
            dead = []
            for sock in list(socks):
                try:
                    sock.send(msg)
                except Exception:
                    dead.append(sock)
            for d in dead:
                socks.discard(d)
            if not socks:
                del self.player_sockets[pid]

        # storyteller
        if self.storytellerSocket:
            try:
                self.storytellerSocket.send({"type": "state", "view": view_for_storyteller(self.game, self)})
            except Exception:
                self.storytellerSocket = None

        # room viewers
        if self.room_viewers:
            room_view = {"type": "state", "view": view_for_room(self)}
            gone = []
            for v in list(self.room_viewers):
                try:
                    v.send(room_view)
                except Exception:
                    gone.append(v)
            for g in gone:
                self.room_viewers.discard(g)

    # ---------------------------
    # Prompt responses (for choose_one/two, etc.)
    # ---------------------------
    def respond(self, cid: int, answer):
        self.bus.fulfill(cid, answer)
        self.broadcast()

    # ---------------------------
    # Lookups
    # ---------------------------
    def player_by_id(self, pid: int):
        return next((p for p in self.players if p.id == pid), None)

    def is_spectator(self, sid: int) -> bool:
        return self.spectator_by_id(sid) is not None

    def spectator_by_id(self, sid: int):
        return next((s for s in self.spectators if s.id == sid), None)

    def is_storyteller(self, stid: int) -> bool:
        return stid == self.info.storyteller_id

    def is_player(self, pid: int) -> bool:
        if self.game and self.game.players:
            return self.player_by_id(pid) is not None
        else:
            return False

    # ---------------------------
    # Join / Leave / Seat
    # ---------------------------
    def join_unseated(self, spectator_id, spectator_name: str) -> dict | None:
        if not self.is_storyteller(stid=spectator_id) \
                and not self.is_spectator(sid=spectator_id) \
                and not self.is_player(pid=spectator_id):
            spectator = Spectator(id=spectator_id, name=spectator_name)
            self.spectators.append(spectator)
            self.broadcast()

        return {"id": spectator_id, "name": spectator_name}

    def leave(self, player_id: int) -> tuple[bool, str | None]:
        spec_idx = next((i for i, s in enumerate(self.spectators) if s.id == player_id), None)
        if spec_idx is not None:
            self.spectators.pop(spec_idx)
            return True, None

        player = next((p for p in getattr(self, "players", []) if p.id == player_id), None)
        if player is None:
            occ_seat_idx = next((i for i, s in enumerate(self.seats)
                                 if s["occupant"] is not None
                                 and getattr(s["occupant"], "id", None) == player_id), None)
            if occ_seat_idx is None:
                return False, "not_in_room"
            player = self.seats[occ_seat_idx]["occupant"]

        seat_no = getattr(player, "seat", None)
        if seat_no is not None:
            if 1 <= seat_no <= len(self.seats):
                seat = self.seats[seat_no - 1]
                if seat["occupant"] is not None and getattr(seat["occupant"], "id", None) == player.id:
                    seat["occupant"] = None
            player.seat = None

        spec = Spectator(id=player.id, name=player.name)
        self.spectators.append(spec)

        if hasattr(self, "players"):
            self.players = [p for p in self.players if p.id != player_id]

        # do i need to do this if i am broadcasting
        # self.send_to_storyteller(player_left_message(self.info.gid, player.id, player.name, seat_no))
        self.broadcast()
        return True, None

    def sit(self, sid: int, seat_no: int) -> tuple[bool, str | None]:
        if not (1 <= seat_no <= len(self.seats)):
            return False, "invalid_seat"

        spectator = next((s for s in self.spectators if s.id == sid), None)
        if not spectator:
            return False, "spectator_not_found"

        seat = self.seats[seat_no - 1]
        if seat["occupant"] is not None:
            return False, "seat_occupied"

        player = Player(id=spectator.id, name=spectator.name, seat=seat_no)
        seat["occupant"] = player

        self.spectators = [s for s in self.spectators if s.id != sid]

        if not hasattr(self, "players"):
            self.players = []
        self.players.append(player)

        #self.send_to_storyteller(player_taken_seat(self.info.gid, spectator.id, spectator.name, seat_no))
        self.broadcast()
        return True, None

    def vacate(self, pid: int, seat_no: int) -> tuple[bool, str | None]:
        if not (1 <= seat_no <= len(self.seats)):
            return False, "invalid_seat"

        seat = self.seats[seat_no - 1]
        occ = seat["occupant"]

        if occ is None:
            return False, "seat_empty"

        if occ.id != pid:
            return False, "seat_not_occupied_by_player"

        player = next((p for p in getattr(self, "players", []) if p.id == pid), None)
        if player is None:
            player = occ

        seat["occupant"] = None
        if hasattr(player, "seat"):
            player.seat = None

        spec = Spectator(id=player.id, name=player.name)
        self.spectators.append(spec)

        if hasattr(self, "players"):
            self.players = [p for p in self.players if p.id != pid]

        msg = player_vacated_seat(self.info.gid, player.id, player.name, seat_no)
        self.send_to_storyteller(msg)
        self.broadcast()
        return True, None

    # ---------------------------
    # Domain events (single entry point)
    # ---------------------------
    def domain_event(self, ev: DomainEvent) -> None:
        """Single entry point for all Game -> Room domain events."""
        t = ev.type
        d = ev.data

        # Night flow to ST
        if t == "NightPrepared":
            msg = night_prepared_message(self.info.gid, d)
            self.send_to_storyteller(msg)
            return

        # Setup tasks (requested by roles during Game.setup() / role.on_setup)
        if t == "SetupTaskRequested":
            task = SetupTask(
                id=self._next_task_id,
                kind=d["kind"],
                role=d["role"],
                owner_id=d["owner_id"],
                prompt=d["prompt"],
                options=list(d.get("options", [])),
                payload=dict(d.get("payload", {})),
            )
            self._next_task_id += 1
            self.setup_tasks.append(task)
            self._notify_st({"type": "event", "event": "setup_tasks", "tasks": [self._public_task(task)]})
            return

        # (Add other event types here as needed...)

    # ---------------------------
    # Setup task helpers
    # ---------------------------
    def perform_setup_task(self, *, task_id: int, answer: Dict) -> bool:
        t = next((x for x in self.setup_tasks if x.id == task_id), None)
        if not t or t.status != TaskStatus.PENDING:
            return False
        if t.options:
            pid = answer.get("player_id")
            if pid not in t.options:
                raise ValueError("invalid_choice")

        owner = self.game.player(t.owner_id)
        role = getattr(owner, "role", None)
        if not role or getattr(role, "id", "") != t.role or not hasattr(role, "apply_setup"):
            raise ValueError("role_mismatch")

        role.apply_setup(t.kind, answer, self.game)

        t.status = TaskStatus.DONE
        self._notify_st({"type": "event", "event": "task_done", "id": t.id})
        self.broadcast()

        if not any(x.status == TaskStatus.PENDING for x in self.setup_tasks) and self.game.phase == Phase.SETUP:
            self._notify_st({"type": "event", "event": "setup_complete"})
        return True

    @staticmethod
    def _public_task(t: SetupTask) -> Dict:
        return {
            "id": t.id,
            "kind": t.kind,
            "role": t.role,
            "owner_id": t.owner_id,
            "prompt": t.prompt,
            "options": list(t.options),
            "status": t.status.name,
        }


rooms: Dict[str, GameRoom] = {}
