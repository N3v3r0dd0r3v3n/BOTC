from botc.scripts import register_role
from botc.model import Team, RoleType, Game


@register_role
class Investigator:
    id = "Investigator"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None
    minion = None
    wrong = None

    def on_setup(self, g: Game):
        me = g.player(self.owner)
        minions = [
            {"id": p.id,
             "name": p.name}
            for p in g.alive_players()
            if p.id != me.id and getattr(p.role, "type", None) == RoleType.MINION]
        if minions:
            g.request_setup_task(
                kind="select_minion",
                role=self.id,
                owner_id=me.id,
                prompt="Pick a minion for the Investigator",
                options=minions,
            )

    def apply_setup(self, kind: str, selection: dict, game: Game):
        if kind != "select_minion" and kind != "select_wrong":
            return
        me = game.player(self.owner)
        if kind == "select_minion":
            if selection['id'] in [p.id for p in game.alive_players()]:
                self.minion = selection

            wrong_options = [
                {"id": player.id,
                 "name": player.name}
                for player in game.alive_players()
                if player.id != me.id and player.id != selection['id']
            ]
            if wrong_options:
                game.request_setup_task(
                    kind="select_wrong",
                    role=self.id,
                    owner_id=me.id,
                    prompt="Pick wrong (bluff) for the Investigator",
                    options=wrong_options,
                )
        elif kind == "select_wrong":
            selected_wrong = selection.get("player_id")
            if selected_wrong in [p for p in game.alive_players()]:
                self.wrong = selected_wrong

    def on_night(self, g: Game):
        if g.night != 1:  # Investigator acts first night only
            return
        me = g.player(self.owner)
        if not me.alive:
            return

        # Pick a minion role that is in the bag or present; simple: prefer ones present
        present_minions = [p for p in g.players if getattr(p.role, "type", None) == RoleType.MINION]
        role_name = getattr(present_minions[0].role, "id", "Poisoner") if present_minions else "Poisoner"

        # Choose two players, exactly one is that minion (unless poisoned)
        minion = next((p for p in g.players if getattr(p.role, "id", "") == role_name), None)
        candidates = [p for p in g.players if p.id != me.id]
        if len(candidates) < 2:
            return

        # If poisoned, both shown are not the minion (wrong info).
        if g.is_poisoned(self.owner) or minion is None:
            a, b = candidates[0], candidates[1]
            g.log.append(f"{me.name} (Investigator) sees that {a.name} or {b.name} is the {role_name}")
            return

        # Unpoisoned: one true (the minion), one bluff (someone else)
        bluff = next((p for p in candidates if p.id not in (me.id, minion.id)), None)
        if not bluff:
            return
        shown = (minion, bluff)
        g.log.append(f"{me.name} (Investigator) sees that {shown[0].name} or {shown[1].name} is the {role_name}")

    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
