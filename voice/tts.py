"""Barnaby's speech, prepared the way Kokoro v1.0 expects it.

Kokoro was trained on phonemes from the misaki G2P, not espeak (the kokoro-onnx README recommends misaki), so:
- text -> misaki phonemes (British English; espeak-ng only as fallback for unknown words) -> kokoro(is_phonemes=True)
- one sentence at a time (Kokoro's style vector is chosen by phoneme length; short, whole sentences keep prosody
  natural), joined with natural pauses: longer after a full stop or question, shorter after a comma-like break
- light normalisation first: smart quotes, "ma'am" and friends, ellipses, dashes

Used by the film's voice-line renderer and (via BarnabyKokoroTTS) by the live voice bot.

  runtime/voice/.venv/Scripts/python voice/tts.py "Text to say" out.wav [--voice bm_george] [--speed 0.95]
"""
from __future__ import annotations

import argparse
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models" / "kokoro" / "kokoro-v1.0.onnx"
VOICES = ROOT / "models" / "kokoro" / "voices-v1.0.bin"
SR = 24000

PAUSE_AFTER = {".": 0.34, "?": 0.38, "!": 0.32, ";": 0.22, ":": 0.2}


@lru_cache(maxsize=1)
def _kokoro():
    from kokoro_onnx import Kokoro
    return Kokoro(str(MODEL), str(VOICES))


@lru_cache(maxsize=2)
def _g2p(british: bool = True):
    from misaki import en, espeak
    return en.G2P(trf=False, british=british, fallback=espeak.EspeakFallback(british=british))


def normalise(text: str) -> str:
    t = text.strip()
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = t.replace("—", ", ").replace("–", ", ").replace("...", ".").replace("…", ".")
    t = re.sub(r"\s+", " ", t)
    return t


def sentences(text: str) -> list[tuple[str, str]]:
    """Split into (sentence, closing punctuation) pieces; colons/semicolons also break, with shorter pauses."""
    parts = re.findall(r"[^.?!;:]+[.?!;:]?", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        end = p[-1] if p[-1] in PAUSE_AFTER else "."
        out.append((p if p[-1] in PAUSE_AFTER else p + ".", end))
    return out


def voice_style(voice: str | dict[str, float]):
    """A voice id, or a blend like {"bm_george": .8, "bm_fable": .2}."""
    k = _kokoro()
    if isinstance(voice, str):
        return voice
    return sum(k.get_voice_style(v) * w for v, w in voice.items())


def speak(text: str, voice: str | dict[str, float] = "bm_george", speed: float = 0.95, british: bool = True,
          use_misaki: bool = True) -> tuple[np.ndarray, int]:
    k, g2p = _kokoro(), _g2p(british)
    style = voice_style(voice)
    chunks = []
    for sent, end in sentences(normalise(text)):
        if use_misaki:
            phonemes, _ = g2p(sent)
            audio, sr = k.create(phonemes, voice=style, speed=speed, is_phonemes=True)
        else:
            audio, sr = k.create(sent, voice=style, speed=speed, lang="en-gb" if british else "en-us")
        chunks += [audio, np.zeros(int(SR * PAUSE_AFTER.get(end, .3)), dtype=np.float32)]
    out = np.concatenate(chunks[:-1]) if chunks else np.zeros(1, dtype=np.float32)
    return out.astype(np.float32), SR


def save(path: str | Path, samples: np.ndarray, sr: int = SR) -> None:
    import soundfile as sf
    sf.write(str(path), samples, sr, subtype="PCM_16")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("out")
    ap.add_argument("--voice", default="bm_george")
    ap.add_argument("--speed", type=float, default=0.95)
    a = ap.parse_args()
    s, sr = speak(a.text, a.voice, a.speed)
    save(a.out, s, sr)
    print(f"{a.out}: {len(s) / sr:.1f}s")
