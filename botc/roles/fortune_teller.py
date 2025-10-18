from __future__ import annotations

import random
from botc.model import Team, RoleType, Game, Player


class FortuneTeller:
    id = "Fortune Teller"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None

    def __init__(self):
        self.red_herring: int | None = None  # seat id of a random good player

    def on_setup(self, g: Game):
        goods = [p for p in g.alive_players() if getattr(p.role, "team", None) == Team.GOOD]
        if goods:
            self.red_herring = random.choice(goods).id

    def on_night(self, g: Game):
        me = g.player(self.owner)
        if not me.alive:
            return

        others = g.alive_others(self.owner)
        if len(others) < 2:
            return

        a, b = random.sample(others, 2)  # temporary stub until prompts exist

        demon_present = any(getattr(p.role, "type", None) == RoleType.DEMON for p in (a, b))
        red_herring = g.player(self.red_herring) if self.red_herring else None

        sees_yes = demon_present or (red_herring and red_herring.id in {a.id, b.id})
        g.log.append(f"{me.name} sees {'YES' if sees_yes else 'NO'} when checking {a.name} & {b.name}")

    def on_day_start(self, g: Game):
        pass

    def on_death(self, g: Game):
        pass

    def on_execution(self, g: Game, executed_pid: int):
        pass
