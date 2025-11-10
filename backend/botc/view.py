from dataclasses import asdict

from botc.model import Game, Seat, RoomInfo


def role_view(role):
    if role is None:
        return None
    return {
        "id": role.id,
        "team": role.team.name,
        "type": role.type.name,  # Enum to string
    }


def _build_seats(room, include_roles: bool = False, only_role_id=None):
    """
    - include_roles=True  -> include every occupant's role (storyteller)
    - only_role_id=<pid>  -> include role only for that player (player self)
    """
    seats_view = []
    for s in room.seats:  # each s is {"seat": int, "occupant": Player|None}
        occ = s["occupant"]
        if occ is None:
            seats_view.append({"seat": s["seat"], "occupant": None})
            continue

        occ_payload = {"id": occ.id, "name": occ.name, "seat": occ.seat}

        if include_roles or (only_role_id is not None and occ.id == only_role_id):
            role_obj = getattr(occ, "role", None)
            occ_payload["role"] = None if role_obj is None else {
                "id": getattr(role_obj, "id", None)
            }

        seats_view.append({"seat": s["seat"], "occupant": occ_payload})
    return seats_view


def view_for_room(room):
    return {
        "info": asdict(room.info),
        "seats": _build_seats(room, include_roles=False),
        "spectators": [{"id": s.id, "name": s.name} for s in room.spectators],
        "players": len(room.players),
    }


def view_for_player(game: Game, player_id: int, room) -> dict:
    # start from scratch so we can override seats
    base = {
        "info": asdict(room.info),
        "spectators": [{"id": s.id, "name": s.name} for s in room.spectators],
        "players": len(room.players),
        "seats": _build_seats(room, include_roles=False, only_role_id=player_id)
    }

    if game:
        you = next((p for p in game.players if p.id == player_id), None)

        # Only reveal your own seat role once the game is not open
        only_id = you.id if (you and room.info.status != "open") else None
        base["phase"] = game.phase.name
        base["night"] = game.night

        if you:
            base["player"] = {
                "you": {
                    "id": you.id,
                    "name": you.name,
                    "seat": you.seat,
                    "alive": you.alive,
                    "ghost": you.ghost_vote_available,
                    "role": {"id": getattr(you.role, "id", None)} if (you.role and room.info.status != "open") else None,
                },
                "status": room.info.status,
            }
    return base


def _get_seat_for_player_id(base_view: dict, player_id: str):
    for seat in base_view['seats']:
        if seat['occupant']['id'] == player_id:
            return seat


def _add_token(base_view: dict, seat: Seat, token: str) -> None:
    if seat is None:
        return

    seat.s.setdefault("tokens", []).append(token)


def _add_info_tokens(base_view: dict, game: Game, room) -> None:
    if not game:
        return

    for player in game.players:
        role = player.role
        if not role:
            continue
        role_key = role
        """
        if hasattr(role, "outsider"):
            player = role.outsider
            seat = _get_seat_for_player_id(base_view, player.id)
            token = role['id'] + " " + "outsider"
            _add_token(base_view, seat, token)
            
        if hasattr(role, "townsfolk"):
            player = role.townsfolk
            seat = _get_seat_for_player_id(base_view, player.id)
            token = role['id'] + " " + "townsfolk"
            _add_token(base_view, seat, token)
            
        if hasattr(role, "wrong"):
            player = role.townsfolk
            seat = _get_seat_for_player_id(base_view, player.id)
            token = role['id'] + " " + "wrong"
            _add_token(base_view, seat, token)
        """
        for attr in ["outsider", "townsfolk", "wrong", "minion", "red_herring"]:
            if hasattr(role, attr):
                attribute = getattr(role, attr)
                seat = _get_seat_for_player_id(base_view, attribute.id)
                token = role['id'] + " " + attr
                _add_token(base_view, seat, token)
                print(attribute)



def view_for_storyteller(game: Game, room=None) -> dict:
    base = {
        "info": asdict(room.info),
        "seats": _build_seats(room, include_roles=True),
        "spectators": [{"id": s.id, "name": s.name} for s in room.spectators],
        "players": len(room.players)
    }
    if game:
        base["phase"] = game.phase.name
        base["night"] = game.night
        #So far this is causing me a load of grief
        #_add_info_tokens(base, game, room)
    return base
