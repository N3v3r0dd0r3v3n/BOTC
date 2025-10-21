from __future__ import annotations

from collections import defaultdict
from typing import List, Set, Dict

from botc.model import RoomInfo, Player, Spectator
from botc.scripts import Script, TB_ROLE_GROUPS
from botc.view import view_for_player, view_for_storyteller, view_for_room
from botc.ws.prompt_bus import PromptBus
from botc.model import Player
from botc.model import Spectator
from botc.ws.ws_prompt import WsPrompt
import random


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
            storyteller_id=creator['id'])
        self.bus = PromptBus()
        self.spectators: List[Spectator] = []
        self.players: List[Player] = []
        self.seats = [{"seat": i + 1, "occupant": None} for i in range(initial_seat_count)]
        self.game = None
        # install WsPrompt
        """
        if self.game is not None:
            self.game.prompt = WsPrompt(self._send_to_storyteller, self.bus)
        """

        self.room_viewers: Set["RoomViewerSocket"] = set()
        self.player_sockets = defaultdict(set)

    def add_room_viewer(self, sock):
        self.room_viewers.add(sock)

    def remove_room_viewer(self, sock):
        self.room_viewers.discard(sock)

    def update_max_seats(self, new_max: int) -> tuple[bool, str | None]:
        if new_max < self.min_residents:
            return False, "min_seats_is_5"
        if new_max > self.max_residents:
            return False, "max_seats_is_20"

        # how many seats currently occupied
        occupied = sum(1 for s in self.seats if s["occupant"] is not None)

        if new_max < occupied:
            return False, "cannot_reduce_below_occupied_seats"

        current = len(self.seats)

        # grow
        if new_max > current:
            for i in range(current, new_max):
                self.seats.append({"seat": i + 1, "occupant": None})

        # shrink (safe only if seat unoccupied)
        elif new_max < current:
            # remove only from the end if empty
            for i in range(current - 1, -1, -1):
                seat = self.seats[i]
                if seat["occupant"] is None:
                    self.seats.pop(i)
                    break

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

    def build_role_deck(self) -> list[str]:
        counts = self.script.role_counts.get(len(self.players))
        if not counts:
            raise ValueError(f"Unsupported player count: {len(self.players)}")

        # Safety checks
        for k in ("townsfolk", "outsiders", "minions", "demons"):
            need = counts.get(k, 0)
            have = len(TB_ROLE_GROUPS[k])
            if need > have:
                raise ValueError(f"Not enough roles in group '{k}': need {need}, have {have}")

        deck = []
        deck += random.sample(TB_ROLE_GROUPS["townsfolk"], counts["townsfolk"])
        deck += random.sample(TB_ROLE_GROUPS["outsiders"], counts["outsiders"])
        deck += random.sample(TB_ROLE_GROUPS["minions"], counts["minions"])
        deck += random.sample(TB_ROLE_GROUPS["demons"], counts["demons"])

        if len(deck) != len(self.players):
            raise AssertionError("Role deck size does not match player count")

        random.shuffle(deck)
        return deck

    def setup_game(self):
        deck = self.build_role_deck()
        print(deck)
        return True

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
    """
    def _send_to_storyteller(self, payload: dict):
        if self.storyteller:
            # send the prompt (or whatever payload) as-is
            self.storyteller.send(payload)
    """

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
        print("Storyteller?")
        print(self.storyteller)
        if self.storyteller:
            try:
                print("Sending")
                self.storyteller.send({"type": "state", "view": view_for_storyteller(None, self)})
                print("Sent")
            except Exception as ex:
                self.storyteller = None
                print("Something went wrong")
                print(ex)


        # viewers
        if self.room_viewers:
            view = view_for_room(self)
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

    """
    def seat_map(self) -> list[dict]:
        #Return seat list 1..max_players with occupant info (or None).
        seats = []
        for n in range(1, self.info.max_players + 1):
            occ = next((p for p in self.game.players if p.seat == n), None)
            seats.append({
                "seat": n,
                "occupant": None if not occ else {"id": occ.id, "name": occ.name}
            })
        return seats
    """

    def player_by_id(self, pid: int):
        return next((p for p in self.game.players if p.id == pid), None)

    def spectator_by_id(self, sid: int):
        return next((s for s in self.spectators if s.id == sid), None)

    def is_storyteller(self, stid: int) -> bool:
        return stid == self.info.storyteller_id

    def is_spectator(self, sid: int) -> bool:
        return self.spectator_by_id(sid) is not None

    def is_player(self, pid: int) -> bool:
        if self.game and self.game.players:
            return self.player_by_id(pid) is not None
        else:
            return False

    def join_unseated(self, spectator_id, spectator_name: str) -> dict | None:
        """Add a player record with no seat yet."""
        if self.info.status != "open":
            return None

        if not self.is_storyteller(stid=spectator_id) \
                and not self.is_spectator(sid=spectator_id) \
                and not self.is_player(pid=spectator_id):
            spectator = Spectator(id=spectator_id, name=spectator_name)
            self.spectators.append(spectator)
        return {"id": spectator_id, "name": spectator_name}

    def leave(self, player_id: int) -> tuple[bool, str | None]:
        spec_idx = next((i for i, s in enumerate(self.spectators) if s.id == player_id), None)
        if spec_idx is not None:
            self.spectators.pop(spec_idx)
            return True, None

        player = next((p for p in getattr(self, "players", []) if p.id == player_id), None)
        if player is None:
            # As a safety net, if seats store full Player objects, check seats directly
            occ_seat_idx = next((i for i, s in enumerate(self.seats)
                                 if s["occupant"] is not None
                                 and getattr(s["occupant"], "id", None) == player_id), None)
            if occ_seat_idx is None:
                return False, "not_in_room"
            # Recover the player object from the seat
            player = self.seats[occ_seat_idx]["occupant"]

        #If seated, clear the seat
        seat_no = getattr(player, "seat", None)
        if seat_no is not None:
            if 1 <= seat_no <= len(self.seats):
                seat = self.seats[seat_no - 1]
                # Only clear if the occupant is this player
                if seat["occupant"] is not None and getattr(seat["occupant"], "id", None) == player.id:
                    seat["occupant"] = None
            player.seat = None

        #Remove from players list if present
        if hasattr(self, "players"):
            self.players = [p for p in self.players if p.id != player_id]

        return True, None

    def sit(self, sid: int, seat_no: int) -> tuple[bool, str | None]:
        if self.info.status != "open":
            return False, "room_not_open"

        if not (1 <= seat_no <= len(self.seats)):
            return False, "invalid_seat"

        # find spectator
        spectator = next((s for s in self.spectators if s.id == sid), None)
        if not spectator:
            return False, "spectator_not_found"

        seat = self.seats[seat_no - 1]
        if seat["occupant"] is not None:
            return False, "seat_occupied"

        # create Player and occupy the seat

        player = Player(id=spectator.id, name=spectator.name, seat=seat_no)

        seat["occupant"] = player

        # remove from spectators
        self.spectators = [s for s in self.spectators if s.id != sid]

        # ensure self.players exists
        if not hasattr(self, "players"):
            self.players = []
        self.players.append(player)

        return True, None

    def vacate(self, pid: int, seat_no: int) -> tuple[bool, str | None]:

        if self.info.status != "open":
            return False, "room_not_open"

        if not (1 <= seat_no <= len(self.seats)):
            return False, "invalid_seat"

        seat = self.seats[seat_no - 1]
        occ = seat["occupant"]  # expected to be a Player or None

        if occ is None:
            return False, "seat_empty"

        if occ.id != pid:
            return False, "seat_not_occupied_by_player"

        # find the player object in room.players (if you keep full Player objects there)
        player = next((p for p in getattr(self, "players", []) if p.id == pid), None)
        if player is None:
            # if players list missing the object, use the occupant instance
            player = occ

        # clear the seat
        seat["occupant"] = None
        if hasattr(player, "seat"):
            player.seat = None

        # move to spectators
        spec = Spectator(id=player.id, name=player.name)
        self.spectators.append(spec)

        # remove from players list if present
        if hasattr(self, "players"):
            self.players = [p for p in self.players if p.id != pid]

        return True, None

    def seated_count(self) -> int:
        return sum(1 for p in self.game.players if getattr(p, "seat", None) is not None)

    def unseated_count(self) -> int:
        return sum(1 for p in self.game.players if getattr(p, "seat", None) is None)

    def counts(self) -> dict:
        return {
            "seated": "self.seated_count()",
            "unseated": "self.unseated_count()",
            "total": "len(self.game.players)",
        }

    def as_dict(self) -> dict:
        """Return a JSON-safe representation of this room."""
        return {
            "gid": self.gid,
            "name": self.info.name,
            "script_name": self.info.script_name,
            "status": self.info.status,
            "spectators": [
                {"id": s.id, "name": s.name} for s in self.spectators
            ],
            "seats": [
                {
                    "seat": s["seat"],
                    "occupant": (
                        None if s["occupant"] is None
                        else {
                            "id": s["occupant"].id,
                            "name": s["occupant"].name,
                            "seat": s["occupant"].seat,
                        }
                    ),
                }
                for s in self.seats
            ],
        }


rooms: Dict[str, GameRoom] = {}
