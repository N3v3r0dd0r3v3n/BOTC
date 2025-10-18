from __future__ import annotations

import asyncio
from typing import Sequence
from botc.prompt import Prompt
from botc.ws.prompt_bus import PromptBus

class WsPrompt(Prompt):
    """Sends prompts to the room's storyteller socket and awaits a reply."""
    def __init__(self, send_func, bus: PromptBus):
        """
        send_func(payload: dict) -> None  # sends to storyteller socket
        bus: shared PromptBus instance
        """
        self._send = send_func
        self._bus = bus

    async def _ask(self, requester_pid: int, kind: str, title: str, candidates: Sequence[int] | None = None):
        cid = self._bus.new_cid()
        payload = {
            "type": "prompt",
            "cid": cid,
            "seat": requester_pid,
            "kind": kind,
            "title": title,
        }
        if candidates is not None:
            payload["candidates"] = list(candidates)
        self._send(payload)
        answer = await self._bus.wait_for(cid)
        return answer

    # Adapter methods for your Sync Prompt Protocol – provide sync wrappers
    def choose_one(self, requester_pid: int, candidates: Sequence[int], title: str) -> int | None:
        return asyncio.get_event_loop().run_until_complete(
            self._ask(requester_pid, "choose_one", title, candidates)
        )

    def choose_two(self, requester_pid: int, candidates: Sequence[int], title: str):
        return asyncio.get_event_loop().run_until_complete(
            self._ask(requester_pid, "choose_two", title, candidates)
        )

    def confirm(self, requester_pid: int, title: str) -> bool:
        return asyncio.get_event_loop().run_until_complete(
            self._ask(requester_pid, "confirm", title)
        )
