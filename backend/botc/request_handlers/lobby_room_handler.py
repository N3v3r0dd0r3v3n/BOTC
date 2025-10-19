from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import rooms


class LobbyRoomHandler(BaseHandler):
    def delete(self, gid: str):
        room = rooms.get(gid)
        if not room:
            self.set_status(404);
            self.write({"error": "room_not_found"});
            return
        room.bus.cancel_all()
        # close ST
        if room.storyteller:
            try:
                room.storyteller.close()
            except:
                pass
            room.storyteller = None
        # close players
        for pid, socks in list(room.player_sockets.items()):
            for s in list(socks):
                try:
                    s.close()
                except:
                    pass
        # close viewers
        for v in list(room.room_viewers):
            try:
                v.close()
            except:
                pass
        del rooms[gid]
        self.write({"ok": True})
