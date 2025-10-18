from __future__ import annotations
import asyncio
from typing import Any, Dict


class PromptBus:
    def __init__(self):
        self._next_cid = 1
        self._waiters: Dict[int, asyncio.Future] = {}

    def new_cid(self) -> int:
        cid = self._next_cid
        self._next_cid += 1
        return cid

    def wait_for(self, cid: int) -> asyncio.Future:
        fut = asyncio.get_event_loop().create_future()
        self._waiters[cid] = fut
        return fut

    def fulfill(self, cid: int, value: Any):
        fut = self._waiters.pop(cid, None)
        if fut and not fut.done():
            fut.set_result(value)

    def cancel_all(self, exc: Exception | None = None):
        for cid, fut in list(self._waiters.items()):
            if not fut.done():
                if exc:
                    fut.set_exception(exc)
                else:
                    fut.cancel()
            self._waiters.pop(cid, None)
