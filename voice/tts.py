"""Barnaby's speech, prepared the way Kokoro v1.0 expects it.

Kokoro has no SSML or emotion tags: prosody comes from punctuation and sentence shape, and the model was trained
on misaki G2P phonemes (the kokoro-onnx README recommends misaki over espeak). So:
- text -> light normalisation -> pronunciation lexicon ([word](/phonemes/), misaki syntax) -> misaki phonemes
  (British; espeak-ng only as fallback) -> RP weak forms -> kokoro(is_phonemes=True)
- one sentence = one Kokoro call, at one speed. Sentences end only at . ? ! followed by a space or the end, so
  "£6.50", "v2.3", "Mr." and "e.g." never cut a sentence in two. Commas, colons and semicolons stay inside so
  Kokoro shapes them; "?" is kept, so yes/no questions rise. kokoro-onnx splits a sentence further only past its
  510-phoneme context.
- weak forms: misaki's lexicon gives function words their citation forms ("them" ðˌɛm, "for" fɔː, "me" mˌiː).
  Unstressed inside a phrase, a stressed full-vowel pronoun made Kokoro end the phrase on it: Theo's "Look after
  them | for me" got a 130 ms silence and a pitch reset before "for me" (video/v2/SPEECH.md has the evidence). RP
  uses weak forms there (ðəm fə), and so do we; strong forms stay where English keeps them (stressed or stranded).
- pauses between sentences are the audible silence research reports, longer around longer sentences
  (SPEECH.md, Pauses), measured from the audio's own quiet edges so the silence heard is the silence planned.
- a little deterministic variance: +-3% speed per sentence, slightly slower on questions and on the closing
  sentence. Same text, same delivery (the film needs that).
- the voice is a blend: George 75% + Fable 25% (Tani's pick, variant 4).

Used by the film's voice-line renderer (video/audio/voices.py, which picks the speed per line from a measured pace
target) and by the live voice bot (voice/barnaby_tts.py).

  runtime/voice/.venv/Scripts/python voice/tts.py "Text to say" out.wav [--voice bm_george] [--speed 1.06]
"""
from __future__ import annotations

import argparse
import hashlib
import re
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models" / "kokoro" / "kokoro-v1.0.onnx"
VOICES = ROOT / "models" / "kokoro" / "voices-v1.0.bin"
SR = 24000

BARNABY = {"bm_george": 0.75, "bm_fable": 0.25}
# Lands Barnaby near his 170 wpm default (SPEECH.md) on typical lines; the film sets the speed per line by measuring.
BARNABY_SPEED = 1.06

# Audible silence between sentences, in seconds: a base by end mark plus a little per syllable of the sentences
# on either side (Zvonik & Cummins 2003: pauses under 300 ms almost only between short phrases), capped well
# inside the medium-pause band of read English (Campione & Veronis 2002: peak near 500 ms).
PAUSE_BASE = {".": 0.26, "!": 0.26, "?": 0.34}
PAUSE_PER_SYL = 0.008
PAUSE_MAX = 0.70
# Typical quiet left at the edges of a trimmed Kokoro sentence (both sides together). plan() subtracts it so the
# live bot's inserted zeros add up to the planned silence; speak() measures the real edges instead.
EDGE_SILENCE = 0.07
QUIET_DB = -40.0                      # below this re the loudest 10 ms frame counts as silence (as SPEECH.md measures)

# Names and jargon misaki would guess at. British RP phonemes in misaki's notation.
LEXICON = {
    "Priya": "pɹˈiːjə", "Anika": "ˈɑːnɪkə", "Okafor": "ɒkˈɑːfɔː", "Lindqvist": "lˈɪndkvɪst",
    "Barnaby": "bˈɑːnəbi", "Synapse": "sˈInaps", "Quorum": "kwˈɔːɹəm", "ComfyUI": "kˈʌmfi jˈuː ˈI",
    "API": "ˈA pˈiː ˈI", "MCP": "ˈɛm sˈiː pˈiː", "README": "ɹˈiːd mˌiː", "Ravi": "ɹˈɑːvi",
}
_LEX_RE = re.compile(r"\b(" + "|".join(map(re.escape, LEXICON)) + r")\b")

# RP weak forms (Cruttenden, Gimson's Pronunciation of English; Wells, Longman Pronunciation Dictionary), used when
# the word is unstressed and something follows it in the same phrase. Left alone: words misaki already reduces in
# context ("to", "a", "the", "than"), words with no safe weak form here ("sir", "your", "have" as a main verb), and
# relative "that": its weak form ðət made Kokoro break before it ("the six | that only read"; SPEECH.md).
WEAK = {"them": "ðəm", "me": "mi", "him": "hɪm", "her": "hə", "us": "əs", "for": "fə", "from": "fɹəm", "of": "əv",
        "at": "ət", "and": "ənd", "but": "bət", "can": "kən", "was": "wəz", "were": "wə", "are": "ə"}
_LINKING_R = {"for", "her", "were", "are"}         # RP links these with /r/ before a vowel: "for a", "are always"
_VOWELS = "aeiouæɑɐɒɔəɛɜɪʊʌAIOQWYᵊ"
_ONE_SYLLABLE = {"ɪə", "ɛə", "ʊə", "eə", "aɪ", "aʊ", "eɪ", "ɔɪ", "əʊ"}
_ABBREV = {"mr", "mrs", "ms", "dr", "prof", "st", "vs", "e.g", "i.e", "approx"}


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
    """(sentence, end mark) pieces. A sentence ends at . ? ! (or a run like ?! or ...) followed by a space or the
    end of the text; not after a title or "e.g.", not before a lower-case word, and "..." only before a capital."""
    out, start = [], 0
    for m in re.finditer(r"[.?!]+[\"')\]]*(?=\s|$)", text):
        run, after = m.group(0).rstrip("\"')]"), text[m.end():]
        word = re.search(r"([\w.]+)$", text[start:m.start()])
        if run == "." and word and word.group(1).lower() in _ABBREV:
            continue
        if run == "..." and not re.match(r"\s+[A-Z]", after):
            continue                                 # a trailing "..." is a pause inside the sentence
        if run[-1] == "." and re.match(r"\s+[a-z]", after):
            continue
        piece = text[start:m.end()].strip()
        if piece:
            out.append((piece, "?" if "?" in run else "!" if "!" in run else "."))
        start = m.end()
    rest = text[start:].strip()
    if rest:
        out.append((rest + ".", "."))
    return out


def syllables(phonemes: str) -> int:
    """Syllables in a misaki phoneme string: one per vowel nucleus (misaki writes diphthongs as one capital, the
    centring ones as two symbols)."""
    n, prev = 0, ""
    for c in phonemes.replace("ː", "").replace("ˈ", "").replace("ˌ", ""):
        if c in _VOWELS and not (prev and prev + c in _ONE_SYLLABLE):
            n += 1
        prev = c if c in _VOWELS else ""
    return n


def weak_forms(tokens) -> str:
    """misaki tokens -> the phoneme string, with a weak form for each function word that misaki left without a
    primary stress and that has another word after it in the phrase (no punctuation between)."""
    out = []
    for i, t in enumerate(tokens):
        ph = t.phonemes or ""
        w = (t.text or "").lower()
        nxt = next((u for u in tokens[i + 1:] if u.phonemes), None)      # skip silent tokens such as "£"
        followed = bool(t.whitespace) and nxt is not None and bool(re.search(r"\w", nxt.text or ""))
        if w in WEAK and followed and "ˈ" not in ph:
            ph = WEAK[w]
            if w in _LINKING_R and nxt.phonemes.lstrip("ˈˌ")[:1] in _VOWELS:
                ph += "ɹ"
        out.append(ph + (" " if t.whitespace else ""))
    return "".join(out).strip()


def phonemise(sentence: str, british: bool = True) -> str:
    _, tokens = _g2p(british)(with_lexicon(sentence))
    return weak_forms(tokens)


def _jitter(sentence: str) -> float:
    h = int(hashlib.sha1(sentence.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return 0.97 + 0.06 * h


def pause_after(end: str, syl_before: int, syl_after: int) -> float:
    """Audible silence after a sentence, from its end mark and the length of the sentences either side."""
    return min(PAUSE_MAX, PAUSE_BASE.get(end, PAUSE_BASE["."]) + PAUSE_PER_SYL * (syl_before + syl_after))


def voice_style(voice: str | dict[str, float]):
    """A voice id, or a blend like {"bm_george": .75, "bm_fable": .25}."""
    if isinstance(voice, str):
        return voice
    k = _kokoro()
    return sum(k.get_voice_style(v) * w for v, w in voice.items())


def plan(text: str, speed: float = BARNABY_SPEED, british: bool = True,
         pause_scale: float = 1.0) -> list[tuple[str, float, float]]:
    """[(phonemes, speed, seconds of zeros to insert after)] for a text: what Kokoro will be asked to say, sentence
    by sentence. The last sentence gets a pause too (the live bot is fed one sentence at a time)."""
    parts = sentences(normalise(text))
    phs = [phonemise(sent, british) for sent, _ in parts]
    syl = [syllables(p) for p in phs]
    out = []
    for i, ((sent, end), ph) in enumerate(zip(parts, phs)):
        s = speed * _jitter(sent)
        if end == "?":
            s *= 0.97
        if i == len(parts) - 1 and len(parts) > 1:
            s *= 0.98
        after = syl[i + 1] if i + 1 < len(parts) else syl[i]
        silence = pause_after(end, syl[i], after) * pause_scale
        out.append((ph, min(2.0, max(0.5, s)), max(0.0, silence - EDGE_SILENCE)))
    return out


def _quiet_edge(audio: np.ndarray, tail: bool) -> float:
    """Seconds of near-silence at the start (or end) of a trimmed sentence, below QUIET_DB re its loudest frame."""
    hop = SR // 100
    n = len(audio) // hop
    if not n:
        return 0.0
    rms = np.sqrt((audio[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    loud = np.flatnonzero(20 * np.log10(rms / rms.max()) > QUIET_DB)
    if not loud.size:
        return 0.0
    return (n - 1 - loud[-1]) * 0.01 if tail else loud[0] * 0.01


class Speech(NamedTuple):
    audio: np.ndarray
    sr: int
    inserted: float                    # seconds of silence added between sentences (fixed, whatever the speed)
    plan: list[tuple[str, float, float]]


def synthesise(text: str, voice: str | dict[str, float] = BARNABY, speed: float = BARNABY_SPEED,
               british: bool = True, pause_scale: float = 1.0) -> Speech:
    """One Kokoro call per sentence, joined by the planned silence (measured against each sentence's quiet edges)."""
    k = _kokoro()
    style = voice_style(voice)
    pl = plan(text, speed, british, pause_scale)
    parts = [k.create(ph, voice=style, speed=s, is_phonemes=True)[0].astype(np.float32) for ph, s, _ in pl]
    if not parts:
        return Speech(np.zeros(1, dtype=np.float32), SR, 0.0, pl)
    out, inserted = [parts[0]], 0.0
    for i in range(1, len(parts)):
        want = pl[i - 1][2] + EDGE_SILENCE
        add = max(0.0, want - _quiet_edge(parts[i - 1], tail=True) - _quiet_edge(parts[i], tail=False))
        out += [np.zeros(int(SR * add), dtype=np.float32), parts[i]]
        inserted += add
    return Speech(np.concatenate(out), SR, inserted, pl)


def speak(text: str, voice: str | dict[str, float] = BARNABY, speed: float = BARNABY_SPEED, british: bool = True,
          use_misaki: bool = True, pause_scale: float = 1.0) -> tuple[np.ndarray, int]:
    if use_misaki:
        sp = synthesise(text, voice, speed, british, pause_scale)
        return sp.audio, sp.sr
    k = _kokoro()
    style = voice_style(voice)
    chunks = []
    for sent, end in sentences(normalise(text)):
        audio, _ = k.create(sent, voice=style, speed=speed, lang="en-gb" if british else "en-us")
        chunks += [audio, np.zeros(int(SR * PAUSE_BASE.get(end, .26)), dtype=np.float32)]
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
