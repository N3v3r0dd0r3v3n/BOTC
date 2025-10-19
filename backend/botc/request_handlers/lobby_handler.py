import json
import uuid

from botc.cli import new_game
from dataclasses import asdict
from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import GameRoom, rooms
from botc.scripts import trouble_brewing_script


class LobbyHandler(BaseHandler):
    def get(self):
        # list rooms
        payload = []
        for room in rooms.values():  # <-- iterate the registry
            g = room.game
            payload.append({
                **asdict(room.info),
                "players": [{"id": p.id, "name": p.name, "alive": p.alive} for p in g.players],
                "seats_used": len(g.players),
            })
        self.write({"rooms": payload})