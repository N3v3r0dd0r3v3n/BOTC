from botc.model import Game, Player


def view_for_seat(g: Game, seat_id: int) -> dict:
    you = next((p for p in g.players if p.seat == seat_id), None)
    role_pub = {"name": getattr(you.role, "id", None)} if you and you.role else None
    return {
        "phase": g.phase.name,
        "night": g.night,
        "you": {"seat": you.seat, "name": you.name, "alive": you.alive, "role": role_pub} if you else None,
        "players": [{"seat": p.seat, "name": p.name, "alive": p.alive} for p in g.players],
        "public": {
            "nomination": (
                {
                    "nominator": g.current_nomination.nominator,
                    "target": g.current_nomination.target,
                    "votes_for": g.current_nomination.votes_for,
                    "needed": g.majority_required(),
                }
                if g.current_nomination else None
            )
        }
    }
