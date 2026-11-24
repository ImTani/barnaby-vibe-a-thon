"""Tiered approvals. The gate rises with what's at stake; a misheard "yes" can never change code.

  read   any GET                                   -> no gate
  write  POST/PUT/PATCH                            -> spoken "yes" or a click on the confirmation card
  grow   Unlock / Compose (Barnaby grows a tool)   -> one click
  build  Barnaby writes code                       -> read the diff, then click (never by voice)
  denied deny-listed endpoints, DELETE by default  -> never
"""
from __future__ import annotations

import asyncio
import itertools
from dataclasses import dataclass, field

from .config import settings
from .events import bus

VOICE_OK = {"write"}          # tiers a spoken "yes" may approve; grow/build need the display


@dataclass
class Pending:
    id: str
    kind: str
    title: str
    detail: str
    tier: str
    diff: str | None = None
    future: asyncio.Future = field(default_factory=lambda: asyncio.get_running_loop().create_future())


class Approvals:
    def __init__(self):
        self.pending: dict[str, Pending] = {}
        self._ids = itertools.count(1)

    async def request(self, *, tier: str, kind: str, title: str, detail: str = "", diff: str | None = None,
                      timeout: float = 1800) -> bool:
        pid = f"a{next(self._ids)}"
        if tier in settings.auto_approve:
            # full card content, so a recorded run can be replayed with real cards (ui/mock.js)
            bus.emit("approval.auto", id=pid, tier=tier, kind=kind, title=title, detail=detail, diff=diff,
                     voice_ok=tier in VOICE_OK)
            return True
        p = Pending(pid, kind, title, detail, tier, diff)
        self.pending[pid] = p
        bus.emit("approval.requested", id=pid, tier=tier, kind=kind, title=title, detail=detail, diff=diff,
                 voice_ok=tier in VOICE_OK)
        try:
            ok = await asyncio.wait_for(p.future, timeout)
        except TimeoutError:
            ok = False
        finally:
            self.pending.pop(pid, None)
        bus.emit("approval.resolved", id=pid, approved=ok)
        return ok

    def resolve(self, pid: str, approved: bool, via: str = "click") -> bool:
        p = self.pending.get(pid)
        if not p or p.future.done():
            return False
        if via == "voice" and p.tier not in VOICE_OK:
            bus.emit("say", text="That one needs a look and a click on the display, I'm afraid.", final=True)
            return False
        p.future.set_result(approved)
        return True

    def latest(self) -> Pending | None:
        return next(reversed(self.pending.values()), None) if self.pending else None

    def summary(self) -> list[dict]:
        return [{"id": p.id, "tier": p.tier, "kind": p.kind, "title": p.title, "detail": p.detail, "diff": p.diff}
                for p in self.pending.values()]


approvals = Approvals()


def tier_for(method: str, key: str, denied: list[str]) -> str:
    if key in denied or method == "DELETE":
        return "denied"
    return "read" if method == "GET" else "write"
