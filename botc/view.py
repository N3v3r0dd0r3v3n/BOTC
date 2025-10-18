from botc.model import Game


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


def view_for_storyteller(g: Game) -> dict:
    """Full-information view for the storyteller socket."""
    return {
        "phase": g.phase.name,
        "night": g.night,
        "players": [
            {
                "id": p.id,
                "seat": p.seat,
                "name": p.name,
                "alive": p.alive,
                "ghost": p.ghost_vote_available,
                "role": getattr(p.role, "id", None),
            }
            for p in g.players
        ],
        "nomination": (
            {
                "nominator": g.current_nomination.nominator,
                "target": g.current_nomination.target,
                "votes_for": g.current_nomination.votes_for,
                "needed": g.majority_required(),
                "votes": dict(g.current_nomination.votes),
            }
            if g.current_nomination
            else None
        ),
        "log_len": len(g.log),
    }
