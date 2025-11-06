from dataclasses import asdict

from botc.model import Game


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


def view_for_player(g: Game, player_id: int, room) -> dict:
    # start from scratch so we can override seats
    base = {
        "info": asdict(room.info),
        "spectators": [{"id": s.id, "name": s.name} for s in room.spectators],
        "players": len(room.players),
        "random": "Hello player",
    }

    if g:
        you = next((p for p in g.players if p.id == player_id), None)

        # Only reveal your own seat role once the game is not open
        only_id = you.id if (you and room.info.status != "open") else None
        base["seats"] = _build_seats(room, include_roles=False, only_role_id=only_id)

        if you:
            base["player"] = {
                "phase": g.phase.name,
                "night": g.night,
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
    else:
        base["seats"] = _build_seats(room, include_roles=False)

    return base


def view_for_storyteller(game: Game, room=None) -> dict:
    base = {
        "info": asdict(room.info),
        "seats": _build_seats(room, include_roles=True),
        "spectators": [{"id": s.id, "name": s.name} for s in room.spectators],
        "players": len(room.players),
        "random": "Hello storyteller",
    }
    if game:
        base["phase"] = game.phase.name
        base["night"] = game.night
    return base
