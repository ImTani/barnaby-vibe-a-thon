"""Barnaby's speech, prepared the way Kokoro v1.0 expects it.

Kokoro has no SSML or emotion tags: prosody comes from punctuation and sentence shape, and the model was trained
on misaki G2P phonemes (the kokoro-onnx README recommends misaki over espeak). So:
- text -> light normalisation -> pronunciation lexicon ([word](/phonemes/), misaki syntax) -> misaki phonemes
  (British; espeak-ng only as fallback) -> kokoro(is_phonemes=True)
- split ONLY at sentence ends (. ? !): commas, colons and semicolons stay inside so Kokoro shapes them; a full
  stop resets intonation, so splitting mid-thought made him sound flat. "?" is kept, so yes/no questions rise.
- pauses by sentence type (a beat longer after a question), and a little deterministic variance: +-3% speed per
  sentence, slightly slower on questions and on the closing sentence. Same text, same delivery (the film needs that).
- the voice is a blend: George 75% + Fable 25% (Tani's pick, variant 4), speed 0.92.

Used by the film's voice-line renderer and by the live voice bot (voice/barnaby_tts.py).

  runtime/voice/.venv/Scripts/python voice/tts.py "Text to say" out.wav [--voice bm_george] [--speed 0.92]
"""
from __future__ import annotations

import argparse
import hashlib
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models" / "kokoro" / "kokoro-v1.0.onnx"
VOICES = ROOT / "models" / "kokoro" / "voices-v1.0.bin"
SR = 24000

BARNABY = {"bm_george": 0.75, "bm_fable": 0.25}
BARNABY_SPEED = 0.92
PAUSE_AFTER = {".": 0.34, "?": 0.46, "!": 0.32}

# Names and jargon misaki would guess at. British RP phonemes in misaki's notation.
LEXICON = {
    "Priya": "pɹˈiːjə", "Anika": "ˈɑːnɪkə", "Okafor": "ɒkˈɑːfɔː", "Lindqvist": "lˈɪndkvɪst",
    "Barnaby": "bˈɑːnəbi", "Synapse": "sˈInaps", "Quorum": "kwˈɔːɹəm", "ComfyUI": "kˈʌmfi jˈuː ˈI",
    "API": "ˈA pˈiː ˈI", "MCP": "ˈɛm sˈiː pˈiː", "README": "ɹˈiːd mˌiː", "Ravi": "ɹˈɑːvi",
}
_LEX_RE = re.compile(r"\b(" + "|".join(map(re.escape, LEXICON)) + r")\b")


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
    t = t.replace("—", ", ").replace("–", ", ").replace("…", "...")
    t = re.sub(r"[*_`#]+", "", t)                 # stray markdown from the model
    t = re.sub(r"\s+", " ", t)
    return t


def with_lexicon(sentence: str) -> str:
    return _LEX_RE.sub(lambda m: f"[{m.group(1)}](/{LEXICON[m.group(1)]}/)", sentence)


def sentences(text: str) -> list[tuple[str, str]]:
    """(sentence, end mark) pieces, split only at . ? ! (keeping "..." as a trailing pause inside a sentence)."""
    out = []
    for p in re.findall(r".+?(?:(?<!\.)[.?!](?!\.)|\.\.\.(?=\s+[A-Z])|$)", text):
        p = p.strip()
        if not p:
            continue
        end = p[-1] if p[-1] in PAUSE_AFTER else "."
        out.append((p if p[-1] in PAUSE_AFTER else p + ".", end))
    return out


def _jitter(sentence: str) -> float:
    h = int(hashlib.sha1(sentence.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return 0.97 + 0.06 * h


def voice_style(voice: str | dict[str, float]):
    """A voice id, or a blend like {"bm_george": .75, "bm_fable": .25}."""
    if isinstance(voice, str):
        return voice
    k = _kokoro()
    return sum(k.get_voice_style(v) * w for v, w in voice.items())


def plan(text: str, speed: float = BARNABY_SPEED, british: bool = True) -> list[tuple[str, float, float]]:
    """[(phonemes, speed, pause_after_seconds)] for a text: what Kokoro will be asked to say, sentence by sentence."""
    g2p = _g2p(british)
    parts = sentences(normalise(text))
    out = []
    for i, (sent, end) in enumerate(parts):
        s = speed * _jitter(sent)
        if end == "?":
            s *= 0.97
        if i == len(parts) - 1 and len(parts) > 1:
            s *= 0.98
        phonemes, _ = g2p(with_lexicon(sent))
        out.append((phonemes, s, PAUSE_AFTER.get(end, .34)))
    return out


def speak(text: str, voice: str | dict[str, float] = BARNABY, speed: float = BARNABY_SPEED, british: bool = True,
          use_misaki: bool = True) -> tuple[np.ndarray, int]:
    k = _kokoro()
    style = voice_style(voice)
    chunks = []
    if use_misaki:
        for phonemes, s, pause in plan(text, speed, british):
            audio, _ = k.create(phonemes, voice=style, speed=s, is_phonemes=True)
            chunks += [audio, np.zeros(int(SR * pause), dtype=np.float32)]
    else:
        for sent, end in sentences(normalise(text)):
            audio, _ = k.create(sent, voice=style, speed=speed, lang="en-gb" if british else "en-us")
            chunks += [audio, np.zeros(int(SR * PAUSE_AFTER.get(end, .34)), dtype=np.float32)]
    out = np.concatenate(chunks[:-1]) if chunks else np.zeros(1, dtype=np.float32)
    return out.astype(np.float32), SR


def save(path: str | Path, samples: np.ndarray, sr: int = SR) -> None:
    import soundfile as sf
    sf.write(str(path), samples, sr, subtype="PCM_16")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("out")
    ap.add_argument("--voice", default="")
    ap.add_argument("--speed", type=float, default=BARNABY_SPEED)
    a = ap.parse_args()
    s, sr = speak(a.text, a.voice or BARNABY, a.speed)
    save(a.out, s, sr)
    print(f"{a.out}: {len(s) / sr:.1f}s")
