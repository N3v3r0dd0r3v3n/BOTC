from botc.model import Team, RoleType, Game


class Empath:
    id = "Empath"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None

    def on_setup(self, g: Game): pass

    def on_night(self, g: Game):
        me = g.player(self.owner)
        if not me.alive:
            return

        # Seats are arranged numerically; wrap around at ends
        left = g.players[(me.seat - 2) % len(g.players)]
        right = g.players[(me.seat) % len(g.players)]
        neighbours = [left, right]

        evil_neighbours = sum(
            1 for p in neighbours if getattr(p.role, "team", None) == Team.EVIL
        )
        g.log.append(f"{me.name} (Empath) senses {evil_neighbours} evil neighbours")

    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
