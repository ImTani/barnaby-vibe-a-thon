"""Pipecat STT service for a sherpa-onnx online websocket server (Tani's streaming Nemotron 0.6B on the home server).

Protocol (sherpa-onnx online-websocket-server): the client sends binary frames of float32 little-endian mono PCM
and the text frame "Done" at the end; the server replies with JSON after each decode step:
{"text": <cumulative text of the current segment>, "is_final": bool, "segment": int, ...}.
Partials become InterimTranscriptionFrames; an endpoint (is_final) becomes a TranscriptionFrame.
This is the only hand-written piece of the listening layer: Pipecat has no sherpa integration.
"""
from __future__ import annotations

import asyncio
import json

import numpy as np
import websockets
from loguru import logger
from pipecat.frames.frames import (
    CancelFrame,
    EndFrame,
    Frame,
    InterimTranscriptionFrame,
    StartFrame,
    TranscriptionFrame,
)
from pipecat.services.settings import STTSettings
from pipecat.services.stt_service import STTService
from pipecat.transcriptions.language import Language
from pipecat.utils.time import time_now_iso8601


class SherpaSTTService(STTService):
    def __init__(self, *, url: str, sample_rate: int = 16000, user_id: str = "user", **kwargs):
        kwargs.setdefault("settings", STTSettings(model="sherpa-onnx nemotron-speech-streaming-en-0.6b", language=Language.EN))
        kwargs.setdefault("ttfs_p99_latency", 0.8)       # 560 ms chunks + endpointing on the home server
        super().__init__(sample_rate=sample_rate, **kwargs)
        self._url = url
        self._user_id = user_id
        self._ws = None
        self._recv_task: asyncio.Task | None = None
        self._last_partial = ""

    async def start(self, frame: StartFrame):
        await super().start(frame)
        await self._connect()

    async def stop(self, frame: EndFrame):
        await super().stop(frame)
        await self._disconnect()

    async def cancel(self, frame: CancelFrame):
        await super().cancel(frame)
        await self._disconnect()

    async def _connect(self):
        try:
            self._ws = await websockets.connect(self._url, max_size=None, open_timeout=5)
            self._recv_task = asyncio.create_task(self._receive())
            logger.info(f"sherpa STT connected: {self._url}")
        except Exception as e:  # noqa: BLE001
            logger.error(f"sherpa STT could not connect to {self._url}: {e}")
            self._ws = None

    async def _disconnect(self):
        if self._recv_task:
            self._recv_task.cancel()
            self._recv_task = None
        if self._ws:
            try:
                await self._ws.send("Done")
                await self._ws.close()
            except Exception:  # noqa: BLE001
                pass
            self._ws = None

    async def run_stt(self, audio: bytes):
        if not self._ws:
            await self._connect()
        if self._ws:
            pcm = np.frombuffer(audio, dtype=np.int16).astype("<f4") / 32768.0
            try:
                await self._ws.send(pcm.tobytes())
            except websockets.ConnectionClosed:
                self._ws = None
        yield None

    async def _receive(self):
        try:
            async for raw in self._ws:
                if raw == "Done!":
                    break
                msg = json.loads(raw)
                text = (msg.get("text") or "").strip()
                if msg.get("is_final"):
                    self._last_partial = ""
                    if text:
                        await self.push_frame(TranscriptionFrame(text, self._user_id, time_now_iso8601(), finalized=True))
                elif text and text != self._last_partial:
                    self._last_partial = text
                    await self.push_frame(InterimTranscriptionFrame(text, self._user_id, time_now_iso8601()))
        except (asyncio.CancelledError, websockets.ConnectionClosed):
            pass
        except Exception as e:  # noqa: BLE001
            logger.error(f"sherpa STT receive error: {e}")

    def can_generate_metrics(self) -> bool:
        return False

    async def process_frame(self, frame: Frame, direction):
        await super().process_frame(frame, direction)
