from __future__ import annotations

from typing import Protocol, Sequence


class Prompt(Protocol):
    # These return indices/ids; the UI is free to render however it wants.
    def choose_one(self, requester_pid: int, candidates: Sequence[int], title: str) -> int | None: ...

    def choose_two(self, requester_pid: int, candidates: Sequence[int], title: str) -> tuple[int, int] | None: ...

    def confirm(self, requester_pid: int, title: str) -> bool: ...


class AutoPrompt:

    def choose_one(self, requester_pid, candidates, title):
        return candidates[0] if candidates else None

    def choose_two(self, requester_pid, candidates, title):
        if len(candidates) < 2: return None
        return candidates[0], candidates[1]

    def confirm(self, requester_pid, title):  # always yes
        return True
