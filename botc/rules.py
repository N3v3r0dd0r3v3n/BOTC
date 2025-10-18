from __future__ import annotations
from botc.model import Game, Team, RoleType

class Rules:
    def check_end(self, g: Game) -> bool:
        demon_alive = any(getattr(p.role, "type", None) == RoleType.DEMON and p.alive for p in g.players)
        good_alive = sum(1 for p in g.players if getattr(p.role, "team", None) == Team.GOOD and p.alive)
        evil_alive = sum(1 for p in g.players if getattr(p.role, "team", None) == Team.EVIL and p.alive)
        if not demon_alive:
            g.log.append("Good wins")
            return True
        if evil_alive >= good_alive:
            g.log.append("Evil wins")
            return True
        return False

