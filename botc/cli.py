from __future__ import annotations

import botc.roles
from botc.model import Game, Player, Phase
from botc.prompt import CLIPrompt, AutoPrompt
from botc.rules import Rules
from botc.scripts import trouble_brewing_script, ROLE_REGISTRY

DEFAULT_TB_PRIORITY = [
    "Imp", "Slayer", "Fortune Teller", "Empath", "Poisoner",  # Empath now in top 5
    "Scarlet Woman",
    "Washer Woman", "Investigator", "Librarian", "Chef",
    "Undertaker", "Monk", "Ravenkeeper",
    "Butler", "Mayor", "Soldier", "Saint", "Virgin", "Drunk", "Recluse", "Baron", "Spy"
]


def assign_by_names(g: Game, seat_to_role_names: list[str]):
    for seat, role_name in enumerate(seat_to_role_names, start=1):
        ctor = ROLE_REGISTRY.get(role_name)
        if ctor:
            g.assign_role(seat, ctor())


def default_roles_for(n: int) -> list[str]:
    # Filter to roles you’ve implemented so far
    implemented = [r for r in DEFAULT_TB_PRIORITY if r in ROLE_REGISTRY]
    return implemented[:n]


def new_game(names: list[str], role_names: list[str] | None = None) -> Game:
    players = [Player(id=i + 1, name=n, seat=i + 1) for i, n in enumerate(names)]
    g = Game(players=players, rules=Rules())
    g.script = trouble_brewing_script()

    # Back-compat for existing tests
    if role_names is None and len(players) == 3:
        role_names = ["Imp", "Slayer", "Fortune Teller"]

    chosen = (role_names if role_names is not None else default_roles_for(len(players)))
    assign_by_names(g, chosen)

    g.prompt = AutoPrompt()

    # Call on_setup hooks
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
    g = new_game(["Eve", "Sam", "Kim", "Luke", "Anna", "Ben", "Veronica"],
                 ["Imp", "Poisoner", "Scarlet Woman", "Fortune Teller", "Empath", "Investigator", "Undertaker"])
    g.prompt = CLIPrompt(lambda pid: g.player(pid).name)
    print_state(g, "Game created")
    safety = 0
    while True:
        safety += 1
        if safety > 200:
            print("\n[DEBUG] Safety break.")
            print("\n".join(g.log))
            break

        if g.phase == Phase.SETUP:
            g.step()

        elif g.phase == Phase.NIGHT:
            order = g.current_night_order()
            print("\n[NIGHT] Running night order:", order)
            for role_name in order:
                for p in g.alive_players():
                    r = p.role
                    if r and getattr(r, "id", None) == role_name:
                        r.on_night(g)
            g.step()

        elif g.phase == Phase.DAY:
            print_state(g, "Day begins")
            alive_ids = [p.id for p in g.alive_players()]
            if len(alive_ids) >= 2:
                while True:
                    do_nom = g.prompt.confirm(alive_ids[0], "Make a nomination? (y=yes, Enter=no)")
                    if not do_nom:
                        break
                    nominator_id = g.prompt.choose_one(alive_ids[0], alive_ids, "Who nominates?")
                    if not nominator_id: break
                    target_pool = [pid for pid in alive_ids if pid != nominator_id]
                    if not target_pool: break
                    target_id = g.prompt.choose_one(nominator_id, target_pool, "Nominate whom?")
                    if not target_id: break

                    g.start_nomination(nominator_id, target_id)

                    # One voting pass, circular from the seat after nominator (allow ghost votes)
                    order = [p.id for p in sorted(g.players, key=lambda x: x.seat)
                             if p.alive or p.ghost_vote_available]
                    # rotate so seat after nominator starts
                    start_seat = (g.player(nominator_id).seat % len(g.players)) + 1
                    while order and g.player(order[0]).seat != start_seat:
                        order.append(order.pop(0))

                    for pid in order:
                        yes = g.prompt.confirm(pid, f"Vote to execute {g.player(target_id).name}?")
                        g.cast_vote(pid, yes)

                    g.close_nomination()
            g.step()

        elif g.phase == Phase.EXECUTION:
            g.finish_day()  # will execute best-on-block if unique and with majority
            g.step()

        elif g.phase == Phase.FINAL_CHECK:
            if g.rules.check_end(g):
                print("\n=== LOG ===")
                print("\n".join(g.log) or "(no log lines)")
                print("\n=== GAME OVER ===")
                break
            g.step()

        else:
            g.step()


if __name__ == "__main__":
    run()
