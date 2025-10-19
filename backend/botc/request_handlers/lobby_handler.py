import json
import uuid

from botc.cli import new_game
from dataclasses import asdict
from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import GameRoom, rooms


class LobbyHandler(BaseHandler):
    def get(self):
        payload = []
        for room in rooms.values():
            print(room)
            #g = room.game
            payload.append({
                **asdict(room.info),
                "spectators": [{"id": s.id, "name": s.name} for s in room.spectators],
                "seats": room.seats,
                #"seats_used": len(g.players),
            })
        self.write({"rooms": payload})
