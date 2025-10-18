from botc.scripts import register_role
from botc.model import Team, RoleType, Game

@register_role
class Ravenkeeper:
    id = "Ravenkeeper"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None

    def on_setup(self, g: Game): pass

    def on_death(self, g: Game):
        # Trigger only if death happened during night processing (called before DAY)
        if g.phase.name == "NIGHT":
            me = g.player(self.owner)
            # Choose any player to learn their role
            cands = [p.id for p in g.players if p.id != me.id]
            if not cands: return
            pid = g.prompt.choose_one(self.owner, cands, "Choose a player to learn their role")
            if pid is None: return
            seen = g.player(pid)
            role_id = getattr(seen.role, "id", "Unknown")
            if g.is_poisoned_like(self.owner):
                g.log.append(f"{me.name} (Ravenkeeper) learns ???")
            else:
                g.log.append(f"{me.name} (Ravenkeeper) learns {seen.name} is the {role_id}")

    def on_night(self, g: Game): pass
    def on_day_start(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
