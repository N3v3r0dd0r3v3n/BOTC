from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import GameRoom, rooms
from botc.view import view_for_room


class LobbyHandler(BaseHandler):
    def get(self):
        payload = []

        for room in rooms.values():
            payload.append(view_for_room(room))

        print(payload)
        self.write({"lobby": payload})
