from dataclasses import asdict

from botc.model import Game


def view_for_room(room):
    seats_view = [
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
        for s in room.seats
    ]
    return {
        "info": asdict(room.info),
        "seats": seats_view,
        "spectators": [{"id": s.id, "name": s.name} for s in room.spectators],
        "players": len(room.players)
    }


def view_for_player(g: Game, player_id: int, room) -> dict:
    """Pre-game + in-game view for a player (id-based), including seat map."""
    base = view_for_room(room)
    base['random'] = "Hello player"

    if g:
        you = next((p for p in g.players if p.id == player_id), None)
        if you:
            base['player'] =  {
                "phase": g.phase.name,
                "night": g.night,
                "you": None if not you else {
                    "id": you.id,
                    "name": you.name,
                    "seat": you.seat,
                    "alive": you.alive,
                    "ghost": you.ghost_vote_available,
                    "role": {"id": getattr(you.role, "id", None)} if (you.role and room.info.status != "open") else None
                },
                "status": room.info.status,  # open | started | finished
            }
        return base


def view_for_seat(g: Game, seat: int) -> dict:
    """Redacted view for a specific seat (used for player sockets)."""
    you = next((p for p in g.players if p.seat == seat), None)
    return {
        "phase": g.phase.name,
        "night": g.night,
        "you": None if not you else {
            "id": you.id,
            "seat": you.seat,
            "name": you.name,
            "alive": you.alive,
            # players should see their own role; others' roles are hidden
            "role": {"id": getattr(you.role, "id", None)} if you.role else None,
            "ghost": you.ghost_vote_available,
        },
        "players": [
            {
                "id": p.id,
                "seat": p.seat,
                "name": p.name,
                "alive": p.alive,
                "ghost": p.ghost_vote_available,
                # hide other roles from players
            }
            for p in g.players
        ],
        "public": {
            "nomination": (
                {
                    "nominator": g.current_nomination.nominator,
                    "target": g.current_nomination.target,
                    "votes_for": g.current_nomination.votes_for,
                    "needed": g.majority_required(),
                }
                if g.current_nomination
                else None
            )
        },
    }


def view_for_storyteller(game: Game, room=None) -> dict:
    """
    base = {
        "phase": g.phase.name,
        "night": g.night,
        "players": [
            {"id": p.id, "seat": p.seat, "name": p.name, "alive": p.alive,
             "ghost": p.ghost_vote_available, "role": getattr(p.role, "id", None)}
            for p in g.players
        ],
        "nomination": (
            {"nominator": g.current_nomination.nominator,
             "target": g.current_nomination.target,
             "votes_for": g.current_nomination.votes_for,
             "needed": g.majority_required(),
             "votes": dict(g.current_nomination.votes)}
            if g.current_nomination else None
        ),
        "log_len": len(g.log),
    }
    if room:
        base["seats"] = room.seat_map()
        base["status"] = room.info.status
    """
    base = view_for_room(room)
    if game:
        base['phase'] = game.phase.name
        base['night'] = game.night
    base['random'] = "Hello storyteller"
    return base
