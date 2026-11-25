"""The bridge between the voice pipeline and Barnaby's core (no-key path: no separate front-desk LLM).

Downstream (you -> Barnaby): a final transcript becomes POST /api/ask, unless a confirmation card is waiting and
you said yes/no, in which case it resolves the card by voice (the core only lets voice approve 'write' cards).
"Hey Barnaby" at the start is stripped (it's the wake phrase, not the request).

Upstream (Barnaby -> you): every new thing Barnaby says (from the core's event stream) becomes a TTSSpeakFrame,
so typed questions get spoken answers too.

Timing, so he feels attentive rather than silent while the worker thinks:
- an immediate, short acknowledgement chosen by intent (question, request, introduction, thanks), rotated so it
  never repeats back to back;
- brief narration for moments the worker doesn't voice itself (a confirmation card is waiting, the tests pass,
  a diff is ready for review, code merged), throttled so it never talks over itself.
"""
from __future__ import annotations

import asyncio
import itertools
import json
import re
import time

import httpx
from httpx_sse import aconnect_sse
from loguru import logger
from pipecat.frames.frames import CancelFrame, EndFrame, Frame, StartFrame, TranscriptionFrame, TTSSpeakFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

WAKE = re.compile(r"^\s*(hey|hi|okay|ok)?[\s,]*(barnaby|barney|barnab[ey]e?)[\s,.!?]*", re.I)
YES = re.compile(r"^\s*(yes|yeah|yep|yup|sure|please do|do it|go ahead|go on|approve[d]?|confirm(ed)?|that'?s fine|ok(ay)?)\b", re.I)
NO = re.compile(r"^\s*(no|nope|don'?t|do not|cancel|not now|stop|decline|leave it)\b", re.I)

INTENTS = [
    ("intro", re.compile(r"\b(this is|meet|here'?s)\b.*\b(system|repo|app|site|shop)\b", re.I),
     ["Delighted, sir.", "How do you do? Let me have a look.", "A pleasure. One moment."]),
    ("thanks", re.compile(r"^\s*(thanks|thank you|cheers|brilliant|lovely)\b", re.I),
     ["My pleasure.", "Not at all, sir.", "Glad to help."]),
    ("question", re.compile(r"(\?\s*$)|^\s*(who|what|which|when|where|why|how|is|are|do|does|did|can|could|will|would|should|have|has)\b", re.I),
     ["Let me look.", "One moment.", "Allow me a moment.", "Let me see."]),
    ("request", re.compile(r"^\s*(please\s+)?(order|move|book|send|text|add|remove|unlock|make|cancel|mark|assign|give|put|set|change|update|build|write)\b", re.I),
     ["Right away.", "Certainly.", "Very good, sir.", "Of course."]),
]

NARRATE = {
    ("approval.requested", "write"): ["Shall I go ahead?", "Shall I?", "Shall I proceed?"],
    ("approval.requested", "build"): ["It's on your display, whenever you're ready.", "Have a look on your display first."],
    ("growth.build.tested", True): ["Theo's checks all pass.", "Everything still checks out."],
    ("growth.build.tested", False): ["It doesn't check out yet, so I'll leave it there."],
    ("growth.build.merged", None): ["Added. Just a moment while the system catches up.", "It's in. One moment."],
}


class BarnabyBridge(FrameProcessor):
    def __init__(self, core: str = "http://127.0.0.1:8700", require_wake: bool = False, acknowledge: bool = True, **kwargs):
        super().__init__(**kwargs)
        self._core = core.rstrip("/")
        self._require_wake = require_wake
        self._acknowledge = acknowledge
        self._listener: asyncio.Task | None = None
        self._since = time.time()
        self._last_spoke = 0.0
        self._rot = {k: itertools.count() for k in [i[0] for i in INTENTS] + [str(k) for k in NARRATE]}

    def _pick(self, key: str, options: list[str]) -> str:
        return options[next(self._rot.setdefault(key, itertools.count())) % len(options)]

    async def _say(self, text: str):
        self._last_spoke = time.time()
        await self.push_frame(TTSSpeakFrame(text))

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, StartFrame):
            self._since = time.time()
            self._listener = asyncio.create_task(self._listen())
        elif isinstance(frame, (EndFrame, CancelFrame)) and self._listener:
            self._listener.cancel()
        elif isinstance(frame, TranscriptionFrame) and direction == FrameDirection.DOWNSTREAM:
            await self._on_utterance(frame.text)
        await self.push_frame(frame, direction)

    async def _on_utterance(self, text: str):
        woke = bool(WAKE.match(text))
        text = WAKE.sub("", text).strip()
        if (self._require_wake and not woke) or not text:
            return
        async with httpx.AsyncClient(timeout=10) as c:
            pending = (await c.get(f"{self._core}/api/state")).json().get("approvals", [])
            if pending and (YES.match(text) or NO.match(text)):
                card = pending[-1]
                await c.post(f"{self._core}/api/approvals/{card['id']}",
                             json={"approved": bool(YES.match(text)), "via": "voice"})
                return
            r = await c.post(f"{self._core}/api/ask", json={"text": text})
            if r.status_code == 409:
                await self._say("One moment, I'm still on the last request.")
                return
        if self._acknowledge:
            for key, rx, options in INTENTS:
                if rx.search(text):
                    await self._say(self._pick(key, options))
                    break

    async def _narrate(self, ev: dict):
        d = ev["data"]
        key = None
        if ev["type"] == "approval.requested":
            key = (ev["type"], d.get("tier"))
        elif ev["type"] == "growth.build.tested":
            key = (ev["type"], bool(d.get("passed")))
        elif ev["type"] == "growth.build.merged":
            key = (ev["type"], None)
        if key in NARRATE and time.time() - self._last_spoke > 1.5:
            await self._say(self._pick(str(key), NARRATE[key]))

    async def _listen(self):
        while True:
            try:
                async with httpx.AsyncClient(timeout=None) as c:
                    async with aconnect_sse(c, "GET", f"{self._core}/api/events") as es:
                        async for sse in es.aiter_sse():
                            if sse.event != "message" or not sse.data.strip():   # keep-alive pings
                                continue
                            ev = json.loads(sse.data)
                            if ev["ts"] < self._since:          # the stream replays history on connect
                                continue
                            if ev["type"] == "say" and not ev["data"].get("final"):
                                await self._say(ev["data"]["text"])
                            else:
                                await self._narrate(ev)
            except asyncio.CancelledError:
                return
            except Exception as e:  # noqa: BLE001
                logger.warning(f"bridge: core event stream dropped ({e}); retrying")
                await asyncio.sleep(1.5)
