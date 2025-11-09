from botc.scripts import register_role
from botc.model import Team, RoleType, Game


@register_role
class WasherWoman:
    id = "Washer Woman"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None

    def on_setup(self, g: Game):
        # Find townsfolk, excluding me
        me = g.player(self.owner)
        townsfolk = [
            {"id": p.id,
             "name": p.name}
            for p in g.alive_players()
            if p.id != me.id and getattr(p.role, "type", None) == RoleType.TOWNSFOLK]
        if townsfolk:
            g.request_setup_task(
                kind="select_townsfolk",
                role=self.id,
                owner_id=me.id,
                prompt="Pick a tolksfolk for the Washer Woman",
                options=townsfolk,
            )

        #TODO The other selection bit.

    def on_night(self, g: Game):
        # first night only
        if g.night != 1:
            return
        me = g.player(self.owner)
        if not me.alive:
            return
        # find a townsfolk (excluding me)
        townsfolk = [p for p in g.alive_players()
                     if p.id != me.id and getattr(p.role, "type", None) == RoleType.TOWNSFOLK]
        if not townsfolk:
            return
        t = townsfolk[0]
        # pick 1 correct, 1 random incorrect name (simple variant)
        others = [p for p in g.alive_players() if p.id not in {me.id, t.id}]
        if not others:
            return
        bluff = others[0]
        # POISON: invert truth (show two wrong names) – simple approach
        if g.is_poisoned(self.owner):
            g.log.append(f"{me.name} (Washerwoman) sees that {bluff.name} or {others[-1].name} is a townsfolk")
        else:
            g.log.append(f"{me.name} (Washerwoman) sees that {t.name} or {bluff.name} is a townsfolk")

    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
