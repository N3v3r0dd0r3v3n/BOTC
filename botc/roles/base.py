from __future__ import annotations
from typing import Protocol
from botc.model import Team, RoleType, Game


class Role(Protocol):
    id: str
    team: Team
    type: RoleType
    owner: int | None

    def on_setup(self, g: Game): ...
    def on_night(self, g: Game): ...
    def on_day_start(self, g: Game): ...
    def on_death(self, g: Game): ...
    def on_execution(self, g: Game, executed_pid: int): ...

