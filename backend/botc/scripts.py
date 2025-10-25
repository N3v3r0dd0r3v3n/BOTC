from dataclasses import dataclass
from typing import List, Type, Dict, Callable


@dataclass
class Script:
    name: str
    first_night: List[str]  # role ids in order
    other_nights: List[str]  # role ids in order
    roles: List[str]  # allowed role ids for the bag
    role_groups: dict
    role_counts: dict


# registry: role_id -> factory function (to avoid importing every class everywhere)
ROLE_REGISTRY: Dict[str, Callable[[], object]] = {}


def register_role(role_cls: Type[object]):
    ROLE_REGISTRY[role_cls.id] = role_cls
    return role_cls


def trouble_brewing_script() -> Script:
    return Script(
        name="Trouble Brewing",
        first_night=[
            "Poisoner", "Spy", "Washerwoman", "Librarian", "Investigator", "Chef", "Empath",
            "Fortune Teller", "Butler"
        ],
        other_nights=[
            "Poisoner", "Monk", "Spy", "Scarlet Woman", "Imp", "Ravenkeeper", "Undertaker",
            "Empath", "Fortune Teller", "Butler"
        ],
        roles=[
            "Washerwoman", "Librarian", "Investigator", "Chef", "Empath", "Fortune Teller", "Undertaker", "Monk",
            "Ravenkeeper", "Virgin", "Slayer", "Soldier", "Mayor", "Butler", "Drunk", "Recluse", "Saint",
            "Poisoner", "Spy", "Scarlet Woman", "Baron", "Imp"
        ],
        role_groups={
            "townsfolk": [
                "Washerwoman", "Librarian", "Investigator", "Chef", "Empath",
                "Fortune Teller", "Undertaker", "Monk", "Ravenkeeper",
                "Virgin", "Slayer", "Soldier", "Mayor",
            ],
            "outsiders": [
                "Butler", "Drunk", "Recluse", "Saint",
            ],
            "minions": [
                "Poisoner", "Spy", "Scarlet Woman", "Baron",
            ],
            "demons": [
                "Imp",
            ],
        },
        role_counts={
            5: {"townsfolk": 3, "outsiders": 0, "minions": 1, "demons": 1},
            6: {"townsfolk": 3, "outsiders": 1, "minions": 1, "demons": 1},
            7: {"townsfolk": 5, "outsiders": 0, "minions": 1, "demons": 1},
            8: {"townsfolk": 5, "outsiders": 1, "minions": 1, "demons": 1},
            9: {"townsfolk": 5, "outsiders": 2, "minions": 1, "demons": 1},
            10: {"townsfolk": 7, "outsiders": 0, "minions": 2, "demons": 1},
            11: {"townsfolk": 7, "outsiders": 1, "minions": 2, "demons": 1},
            12: {"townsfolk": 7, "outsiders": 2, "minions": 2, "demons": 1},
            13: {"townsfolk": 9, "outsiders": 0, "minions": 3, "demons": 1},
            14: {"townsfolk": 9, "outsiders": 1, "minions": 3, "demons": 1},
            15: {"townsfolk": 9, "outsiders": 2, "minions": 3, "demons": 1},
        }
    )

