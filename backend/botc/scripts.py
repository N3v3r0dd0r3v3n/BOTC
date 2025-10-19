from dataclasses import dataclass
from typing import List, Type, Dict, Callable


@dataclass
class Script:
    name: str
    first_night: List[str]  # role ids in order
    other_nights: List[str]  # role ids in order
    roles: List[str]  # allowed role ids for the bag


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
        ]
    )
