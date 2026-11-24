"""Pipecat Kokoro TTS that feeds Kokoro the way it was trained (see voice/tts.py): misaki phonemes (British) with a
pronunciation lexicon, split only at sentence ends so intonation carries (questions rise), natural pauses by
sentence type, slight per-sentence variance, and Barnaby's blended voice (George 75% + Fable 25%).
Pipecat's stock KokoroTTSService sends raw text, which kokoro-onnx phonemises with espeak; that made him flat."""
from __future__ import annotations

import numpy as np
from pipecat.frames.frames import ErrorFrame, TTSAudioRawFrame
from pipecat.services.kokoro.tts import KokoroTTSService

from voice.tts import BARNABY, BARNABY_SPEED, plan, voice_style


class BarnabyKokoroTTS(KokoroTTSService):
    def __init__(self, *, blend: dict[str, float] | None = None, speed: float = BARNABY_SPEED, **kwargs):
        super().__init__(**kwargs)
        self._blend = blend or BARNABY
        self._speed = speed
        self._style = None

    async def run_tts(self, text: str, context_id: str):
        try:
            await self.start_tts_usage_metrics(text)
            if self._style is None:
                self._style = voice_style(self._blend)
            for phonemes, speed, pause in plan(text, self._speed):
                sr = 24000
                async for samples, sr in self._kokoro.create_stream(phonemes, voice=self._style, speed=speed, is_phonemes=True):
                    await self.stop_ttfb_metrics()
                    yield TTSAudioRawFrame(audio=(samples * 32767).astype(np.int16).tobytes(), sample_rate=sr,
                                           num_channels=1, context_id=context_id)
                yield TTSAudioRawFrame(audio=np.zeros(int(sr * pause), dtype=np.int16).tobytes(), sample_rate=sr,
                                       num_channels=1, context_id=context_id)
        except Exception as e:  # noqa: BLE001
            yield ErrorFrame(error=f"Barnaby TTS error: {e}")
        finally:
            await self.stop_ttfb_metrics()
