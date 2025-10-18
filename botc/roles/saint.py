from botc.model import Team, RoleType, Game


class Saint:
    id = "Saint"
    team = Team.GOOD
    type = RoleType.OUTSIDER
    owner = None

    def on_setup(self, g: Game): pass

    def on_night(self, g: Game): pass

    def on_day_start(self, g: Game): pass

    def on_death(self, g: Game): pass

    def on_execution(self, g: Game, executed_pid: int):
        me = g.player(self.owner)
        if executed_pid == me.id and me.alive:
            g.force_winner = "EVIL"
            g.log.append("Evil wins (Saint was executed)")
