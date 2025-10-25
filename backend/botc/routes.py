from tornado.web import url

from botc.request_handlers.get_room_handler import RoomHandler
from botc.request_handlers.join_room_handler import JoinRoomHandler
from botc.request_handlers.leave_room_handler import LeaveRoomHandler
from botc.request_handlers.lobby_handler import LobbyHandler
from botc.request_handlers.lobby_room_handler import LobbyRoomHandler
from botc.request_handlers.seats_handler import SeatsHandler
from botc.request_handlers.sit_handler import SitHandler
from botc.request_handlers.start_game_handler import StartGameHandler
from botc.request_handlers.step_handler import StepHandler
from botc.request_handlers.vacate_handler import VacateHandler
from botc.socket_handlers.player_handler import PlayerSocket
from botc.socket_handlers.room_view_handler import RoomViewerSocket
from botc.socket_handlers.story_teller_handler import StorytellerSocket
from botc.request_handlers.rooms_handler import RoomsHandler
from botc.rooms import rooms


def http_routes():
    return [
        # Specific room actions FIRST (gid is a single path segment)
        url(r"/api/rooms/([^/]+)/join", JoinRoomHandler, name="room-join"),
        url(r"/api/rooms/([^/]+)/leave", LeaveRoomHandler, name="room-leave"),
        url(r"/api/rooms/([^/]+)/start", StartGameHandler, name="room-start"),
        url(r"/api/rooms/([^/]+)/seats", SeatsHandler, name="room-seats"),
        url(r"/api/rooms/([^/]+)/sit", SitHandler, name="room-sit"),
        url(r"/api/rooms/([^/]+)/vacate", VacateHandler, name="room-vacate"),
        url(r"/api/rooms/([^/]+)/step", StepHandler, name="room-step"),

        # Collections / other endpoints
        url(r"/api/lobby", LobbyHandler, name="lobby"),
        url(r"/api/lobby/([^/]+)", LobbyRoomHandler, name="lobby-room"),
        url(r"/api/rooms", RoomsHandler, name="lobby-rooms"),

        # Catch-all room details LAST
        url(r"/api/rooms/([^/]+)", RoomHandler, name="room-details"),
    ]


def ws_routes():
    return [
        (r"/ws/(.+)/st",     StorytellerSocket, {"rooms": rooms}),
        (r"/ws/(.+)/player/([^/]+)", PlayerSocket, {"rooms": rooms}),
        (r"/ws/(.+)/room",   RoomViewerSocket, {"rooms": rooms}),
    ]
