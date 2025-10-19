from __future__ import annotations

from collections import defaultdict
from typing import List, Set, Dict

from botc.model import RoomInfo
from botc.scripts import Script
from botc.view import view_for_player, view_for_storyteller, view_for_room
from botc.ws.prompt_bus import PromptBus
from botc.ws.ws_prompt import WsPrompt


class GameRoom:
    def __init__(self, gid: str, game, name: str, script: Script, max_players: int):
        self.gid = gid
        self.game = game
        self.info = RoomInfo(gid=gid, name=name, script_name=script.name, max_players=max_players)
        self.bus = PromptBus()
        self.storyteller = None
        self.players = {}
        # install WsPrompt
        self.game.prompt = WsPrompt(self._send_to_storyteller, self.bus)

        self.room_viewers: Set["RoomViewerSocket"] = set()  # 👈 NEW: anonymous viewers
        self.player_sockets = defaultdict(set)  # (from earlier patch)

    def add_room_viewer(self, sock):
        self.room_viewers.add(sock)

    def remove_room_viewer(self, sock):
        self.room_viewers.discard(sock)

    def update_max_players(self, new_max: int) -> tuple[bool, str | None]:
        if new_max < 5:
            return False, "min_seats_is_5"
        if new_max > 20:
            return False, "max_seats_is_20"
        current = len(self.game.players)
        if new_max < current:
            # Can't reduce below occupied seats
            return False, "cannot_reduce_below_current_player_count"
        self.info.max_players = new_max
        return True, None

    def is_full(self) -> bool:
        return len(self.game.players) >= self.info.max_players

    def add_player(self, player_name: str) -> dict | None:
        if self.info.status != "open" or self.is_full():
            return None
        seat = len(self.game.players) + 1
        from botc.model import Player
        p = Player(id=seat, name=player_name, seat=seat)
        self.game.players.append(p)
        return {"id": p.id, "seat": p.seat, "name": p.name}

    def start_game(self, role_names: List[str] | None = None):
        import random
        from botc.scripts import ROLE_REGISTRY
        from botc.cli import assign_by_names, default_roles_for

        # must be seated and within capacity
        if any(p.seat is None for p in self.game.players):
            return False  # some players unseated
        if len(self.game.players) > self.info.max_players:
            return False
        # normalize players by seat order 1..N
        seated = sorted([p for p in self.game.players if p.seat is not None], key=lambda p: p.seat)
        # reassign ids 1..N for engine consistency (optional, but tidy)
        #for i, p in enumerate(seated, start=1):
        #    p.id = i
        #self.game.players = seated
        self.game.players = seated

        n = len(self.game.players)
        if n == 0:
            return False

        if role_names is None:
            allowed = [r for r in self.game.script.roles if r in ROLE_REGISTRY]
            if len(allowed) < n:
                allowed = default_roles_for(n)
            chosen = random.sample(allowed, n) if len(allowed) >= n else allowed[:n]
        else:
            chosen = role_names

        # clear and assign
        for p in self.game.players:
            p.role = None
            p.alive = True
            p.ghost_vote_available = False

        assign_by_names(self.game, chosen)

        for p in self.game.players:
            if p.role and hasattr(p.role, "on_setup"):
                p.role.on_setup(self.game)

        self.info.status = "started"
        return True

    # broadcast helpers
    def _send_to_storyteller(self, payload: dict):
        if self.storyteller:
            self.storyteller.send({"type": "state", "view": view_for_storyteller(self.game, self)})

    def broadcast(self):
        # players
        for pid, socks in list(self.player_sockets.items()):
            view = view_for_player(self.game, pid, self)
            msg = {"type": "state", "view": view}
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
        if self.storyteller:
            try:
                self.storyteller.send({"type": "state", "view": view_for_storyteller(self.game, self)})
            except Exception:
                self.storyteller = None

        # viewers
        if self.room_viewers:
            view = view_for_room(self.game, self)
            view["unseated"] = self.unseated_players()
            room_view = {"type": "state", "view": view}
            gone = []
            for v in list(self.room_viewers):
                try:
                    v.send(room_view)
                except Exception:
                    gone.append(v)
            for g in gone:
                self.room_viewers.discard(g)

    # called by sockets
    def respond(self, cid: int, answer):
        self.bus.fulfill(cid, answer)
        self.broadcast()

    # ----- capacity & seating -----
    def seats_used(self) -> int:
        return sum(1 for p in self.game.players if p.seat is not None)

    def seat_map(self) -> list[dict]:
        """Return seat list 1..max_players with occupant info (or None)."""
        seats = []
        for n in range(1, self.info.max_players + 1):
            occ = next((p for p in self.game.players if p.seat == n), None)
            seats.append({
                "seat": n,
                "occupant": None if not occ else {"id": occ.id, "name": occ.name}
            })
        return seats

    def player_by_id(self, pid: int):
        return next((p for p in self.game.players if p.id == pid), None)

    def join_unseated(self, player_name: str) -> dict | None:
        """Add a player record with no seat yet."""
        if self.info.status != "open":
            return None
        # Generate a new player id (unique, independent from seat numbers)
        new_id = (max([p.id for p in self.game.players] or [0]) + 1)
        from botc.model import Player
        p = Player(id=new_id, name=player_name, seat=None)
        self.game.players.append(p)
        return {"id": p.id, "name": p.name, "seat": p.seat}

    def sit(self, pid: int, seat_no: int) -> tuple[bool, str | None]:
        if self.info.status != "open":
            return False, "room_not_open"
        if not (1 <= seat_no <= self.info.max_players):
            return False, "invalid_seat"
        p = self.player_by_id(pid)
        if not p:
            return False, "player_not_found"
        # seat must be empty
        if any(x.seat == seat_no for x in self.game.players):
            return False, "seat_occupied"
        p.seat = seat_no
        return True, None

    def vacate(self, pid: int) -> tuple[bool, str | None]:
        if self.info.status != "open":
            return False, "room_not_open"
        p = self.player_by_id(pid)
        if not p:
            return False, "player_not_found"
        p.seat = None
        return True, None

    def unseated_players(self) -> list[dict]:
        return [{"id": p.id, "name": p.name}
                for p in self.game.players if getattr(p, "seat", None) is None]

    def seated_count(self) -> int:
        return sum(1 for p in self.game.players if getattr(p, "seat", None) is not None)

    def unseated_count(self) -> int:
        return sum(1 for p in self.game.players if getattr(p, "seat", None) is None)

    def counts(self) -> dict:
        return {
            "seated": self.seated_count(),
            "unseated": self.unseated_count(),
            "total": len(self.game.players),
        }


rooms: Dict[str, GameRoom] = {}
