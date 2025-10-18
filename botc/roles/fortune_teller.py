from __future__ import annotations

import random
from botc.model import Team, RoleType, Game


class FortuneTeller:
    id = "Fortune Teller"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None

    def __init__(self):
        self.red_herring: int | None = None

    def on_setup(self, g: Game):
        goods = [p for p in g.alive_players() if getattr(p.role, "team", None) == Team.GOOD]
        if goods:
            self.red_herring = random.choice(goods).id

    def on_night(self, g: Game):
        me = g.player(self.owner)
        if not me.alive: return
        others = g.alive_others(self.owner)
        if len(others) < 2: return

        cand_ids = [p.id for p in others]
        pick = g.prompt.choose_two(self.owner, cand_ids, "Choose two players")
        if not pick: return
        a = g.player(pick[0]); b = g.player(pick[1])

        demon_present = any(getattr(p.role, "type", None) == RoleType.DEMON for p in (a, b))
        sees_yes = demon_present or (self.red_herring in {a.id, b.id})
        g.log.append(f"{me.name} sees {'YES' if sees_yes else 'NO'} when checking {a.name} & {b.name}")
