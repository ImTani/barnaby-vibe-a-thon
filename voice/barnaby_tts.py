"""Pipecat Kokoro TTS that feeds Kokoro the way it was trained: misaki phonemes (British), one sentence at a time,
with natural pauses between sentences (see voice/tts.py). Pipecat's stock KokoroTTSService sends raw text, which
kokoro-onnx phonemises with espeak; that's what made George sound flat."""
from __future__ import annotations

import numpy as np
from pipecat.frames.frames import ErrorFrame, TTSAudioRawFrame
from pipecat.services.kokoro.tts import KokoroTTSService

from voice.tts import PAUSE_AFTER, _g2p, normalise, sentences


class BarnabyKokoroTTS(KokoroTTSService):
    async def run_tts(self, text: str, context_id: str):
        try:
            await self.start_tts_usage_metrics(text)
            voice = self._settings.voice
            speed = self._settings.speed or 0.95
            g2p = _g2p(True)
            for sent, end in sentences(normalise(text)):
                phonemes, _ = g2p(sent)
                sr = 24000
                async for samples, sr in self._kokoro.create_stream(phonemes, voice=voice, speed=speed, is_phonemes=True):
                    await self.stop_ttfb_metrics()
                    yield TTSAudioRawFrame(audio=(samples * 32767).astype(np.int16).tobytes(), sample_rate=sr,
                                           num_channels=1, context_id=context_id)
                pause = np.zeros(int(sr * PAUSE_AFTER.get(end, .3)), dtype=np.int16)
                yield TTSAudioRawFrame(audio=pause.tobytes(), sample_rate=sr, num_channels=1, context_id=context_id)
        except Exception as e:  # noqa: BLE001
            yield ErrorFrame(error=f"Barnaby TTS error: {e}")
        finally:
            await self.stop_ttfb_metrics()
