"""The bridge between the voice pipeline and Barnaby's core (no-key path: no separate front-desk LLM).

Downstream (you -> Barnaby): a final transcript becomes POST /api/ask, unless a confirmation card is waiting and
you said yes/no, in which case it resolves the card by voice (the core only lets voice approve 'write' cards).
"Hey Barnaby" at the start is stripped (it's the wake phrase, not the request).

Upstream (Barnaby -> you): the bridge subscribes to the core's event stream and turns every new thing Barnaby
says into a TTSSpeakFrame, so typed questions get spoken answers too. Status changes are mirrored as well.
"""
from __future__ import annotations

import asyncio
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


class BarnabyBridge(FrameProcessor):
    def __init__(self, core: str = "http://127.0.0.1:8700", require_wake: bool = False, **kwargs):
        super().__init__(**kwargs)
        self._core = core.rstrip("/")
        self._require_wake = require_wake
        self._listener: asyncio.Task | None = None
        self._since = time.time()

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
        if self._require_wake and not woke:
            return
        if not text:
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
                await self.push_frame(TTSSpeakFrame("One moment, I'm still on the last request."))

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
                                await self.push_frame(TTSSpeakFrame(ev["data"]["text"]))
            except asyncio.CancelledError:
                return
            except Exception as e:  # noqa: BLE001
                logger.warning(f"bridge: core event stream dropped ({e}); retrying")
                await asyncio.sleep(1.5)
