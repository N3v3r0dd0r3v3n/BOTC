from math import floor

from botc.model import Game, Player, Phase, Nomination
from botc.rules import Rules
from botc.roles.imp import Imp
from botc.roles.slayer import Slayer
from botc.roles.fortune_teller import FortuneTeller
from botc.roles.empath import Empath


def new_game(names):
    players = [Player(id=i + 1, name=n, seat=i + 1) for i, n in enumerate(names)]
    g = Game(players=players, rules=Rules())

    # Assign roles only if we have enough players
    if len(players) >= 1:
        g.assign_role(players[0].id, Imp())
    if len(players) >= 2:
        g.assign_role(players[1].id, Slayer())
    if len(players) >= 3:
        g.assign_role(players[2].id, FortuneTeller())
    if len(players) >= 4:
        g.assign_role(players[3].id, Empath())

    desired_order = ["Fortune Teller", "Empath", "Imp"]
    present = {getattr(p.role, "id", None) for p in g.players if p.role}
    g.night_order = [r for r in desired_order if r in present]

    for p in g.players:
        if p.role and hasattr(p.role, "on_setup"):
            p.role.on_setup(g)
    return g


def print_state(g: Game, header: str):
    print(f"\n=== {header} ===")
    print(f"Phase: {g.phase.name}  Night: {g.night}")
    for p in g.players:
        r = getattr(p.role, "id", None)
        print(f"Seat {p.seat}: {p.name} | {'ALIVE' if p.alive else 'DEAD'} | Role: {r}")


def run():
    g = new_game(["Eve", "Sam", "Kim"])  # 3-player demo
    print_state(g, "Game created")
    safety_counter = 0

    while True:
        safety_counter += 1
        if safety_counter > 50:
            print("\n[DEBUG] Safety break (looped too long). Log so far:")
            print("\n".join(g.log))
            break

        if g.phase == Phase.SETUP:
            g.step()

        elif g.phase == Phase.NIGHT:
            print("\n[NIGHT] Running night order:", g.night_order)
            for role_name in g.night_order:
                for p in g.alive_players():
                    r = p.role
                    if r and getattr(r, "id", None) == role_name:
                        r.on_night(g)
            g.step()

        elif g.phase == Phase.DAY:
            print_state(g, "Day begins")
            alive = g.alive_players()
            if len(alive) >= 2:
                voter_ids = [p.id for p in alive]
                # nominate
                nominator_id = g.prompt.choose_one(alive[0].id, voter_ids, "Who nominates?")  # simple demo
                target_id = g.prompt.choose_one(nominator_id, [pid for pid in voter_ids if pid != nominator_id],
                                                "Nominate whom?")
                if nominator_id and target_id:
                    g.start_nomination(nominator_id, target_id)
                    # votes (everyone alive, including target; change to your table rules if needed)
                    for pid in voter_ids:
                        yes = g.prompt.confirm(pid, f"Vote to execute {g.player(target_id).name}?")
                        g.cast_vote(pid, yes)
                    if g.close_nomination():
                        g.execute(target_id)
            g.step()

        elif g.phase == Phase.FINAL_CHECK:
            ended = g.rules.check_end(g)
            if ended:
                print("\n=== LOG ===")
                print("\n".join(g.log) or "(no log lines)")
                print("\n=== GAME OVER ===")
                break
            g.step()

        else:
            # VOTING / EXECUTION placeholders
            g.step()


if __name__ == "__main__":
    run()
