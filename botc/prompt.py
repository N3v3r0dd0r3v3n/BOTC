from __future__ import annotations

from typing import Protocol, Sequence


class Prompt(Protocol):
    def choose_one(self, requester_pid: int, candidates: Sequence[int], title: str) -> int | None: ...
    def choose_two(self, requester_pid: int, candidates: Sequence[int], title: str) -> tuple[int, int] | None: ...
    def confirm(self, requester_pid: int, title: str) -> bool: ...


class AutoPrompt:
    def choose_one(self, requester_pid, candidates, title):
        return candidates[0] if candidates else None
    def choose_two(self, requester_pid, candidates, title):
        if len(candidates) < 2: return None
        return (candidates[0], candidates[1])
    def confirm(self, requester_pid, title):
        return True


class CLIPrompt:
    """Blocking stdin prompt. Pass name_of(pid) to show nicer labels."""
    def __init__(self, name_of: Callable[[int], str] | None = None):
        self.name_of = name_of or (lambda pid: str(pid))

    def _label(self, pid: int) -> str:
        try: return f"{pid}:{self.name_of(pid)}"
        except Exception: return str(pid)

    def choose_one(self, requester_pid: int, candidates: Sequence[int], title: str) -> int | None:
        if not candidates: return None
        print(f"\n[PROMPT] {self.name_of(requester_pid)}: {title}")
        for i, pid in enumerate(candidates, 1):
            print(f"  {i}) {self._label(pid)}")
        while True:
            s = input("Pick number (or Enter to cancel): ").strip()
            if s == "": return None
            if s.isdigit() and 1 <= int(s) <= len(candidates):
                return candidates[int(s)-1]

    def choose_two(self, requester_pid: int, candidates: Sequence[int], title: str) -> tuple[int, int] | None:
        if len(candidates) < 2: return None
        print(f"\n[PROMPT] {self.name_of(requester_pid)}: {title}")
        for i, pid in enumerate(candidates, 1):
            print(f"  {i}) {self._label(pid)}")
        picks: list[int] = []
        while len(picks) < 2:
            s = input(f"Pick #{len(picks)+1} (number, Enter to cancel): ").strip()
            if s == "": return None
            if s.isdigit():
                idx = int(s)
                if 1 <= idx <= len(candidates):
                    pid = candidates[idx-1]
                    if pid not in picks:
                        picks.append(pid)
        return (picks[0], picks[1])

    def confirm(self, requester_pid: int, title: str) -> bool:
        s = input(f"\n[PROMPT] {self.name_of(requester_pid)}: {title} [y/N]: ").strip().lower()
        return s == "y"
