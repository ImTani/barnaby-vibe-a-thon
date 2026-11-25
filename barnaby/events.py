"""In-process event bus. Everything Barnaby does becomes an event; the display streams them over SSE.

Event types (data shape in brackets):
  system.connecting/connected  {system, endpoints, exposed}      growth.unlock/build/compose.*  {system, ...}
  tool.call  {id, system, tool, input, tier}                       tool.result {id, ok, preview}
  approval.requested {id, kind, title, detail, technical, diff?}            approval.resolved {id, approved}
  say  {text, final}   (what Barnaby says)                          turn.start/turn.end {turn, ...}
  log  {level, text}
"""
from __future__ import annotations

import asyncio
import itertools
import json
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any

from .config import STATE


@dataclass
class Event:
    type: str
    data: dict[str, Any]
    id: int = 0
    ts: float = field(default_factory=time.time)

    def json(self) -> str:
        return json.dumps(asdict(self), default=str)


class EventBus:
    def __init__(self, history: int = 500):
        self._subs: set[asyncio.Queue[Event]] = set()
        self._history: deque[Event] = deque(maxlen=history)
        self._ids = itertools.count(1)
        STATE.mkdir(parents=True, exist_ok=True)
        self._log = open(STATE / "events.jsonl", "a", encoding="utf-8")

    def emit(self, type: str, **data: Any) -> Event:
        ev = Event(type=type, data=data, id=next(self._ids))
        self._history.append(ev)
        self._log.write(ev.json() + "\n")
        self._log.flush()
        for q in list(self._subs):
            q.put_nowait(ev)
        return ev

    def subscribe(self, replay: int = 200) -> asyncio.Queue[Event]:
        q: asyncio.Queue[Event] = asyncio.Queue()
        for ev in list(self._history)[-replay:] if replay > 0 else []:      # [-0:] would be everything
            q.put_nowait(ev)
        self._subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[Event]) -> None:
        self._subs.discard(q)

    def history(self) -> list[Event]:
        return list(self._history)


bus = EventBus()
