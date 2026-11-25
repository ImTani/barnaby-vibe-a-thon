"""Barnaby's voice from ElevenLabs (eleven_v3, audio tags), for the film. Free plan: non-commercial, attribution
("Barnaby's voice: ElevenLabs" in the end card).

  runtime/voice/.venv/Scripts/python video/v2/audio/eleven.py voices            British/English male voices
  runtime/voice/.venv/Scripts/python video/v2/audio/eleven.py audition ID ...   one line per voice -> .demo/review/
  runtime/voice/.venv/Scripts/python video/v2/audio/eleven.py render ID [NN ...]
        Barnaby's lines (barnaby_v3.json: the cue text with v3 tags), two seeds each, with ElevenLabs' character
        timestamps -> .demo/review/eleven/takes/NN_s<seed>.wav (+ .align.json). Takes already on disk are skipped.
  runtime/voice/.venv/Scripts/python video/v2/audio/eleven.py passages ID [NN ...]
        eleven_v4, Barnaby performed as passages (barnaby_v4.json "_passages": one request per scene, so his voice
        stays one voice), split into lines at the silences by the character alignment -> .demo/review/eleven/v4/NN.wav
  then choose_eleven.py keeps the better take per line -> video/v2/audio/takes/NN_Barnaby.wav (voices.py --takes).

The key is read from .env (ELEVENLABS_API_KEY) by this script and only sent to api.elevenlabs.io; it is never printed.
Each render costs about one credit per character of the tagged text; the script prints the total before it runs.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
API = "https://api.elevenlabs.io"
MODEL = "eleven_v3"
SETTINGS = {"stability": 0.5, "similarity_boost": 0.75}          # v3: 0.5 = "Natural", lets the tags act
TAGGED = json.loads((HERE / "barnaby_v3.json").read_text(encoding="utf-8"))
CUES = json.loads((HERE.parent / "cues.json").read_text(encoding="utf-8"))
TAKES = HERE / "takes"
AUDITION_LINE = "06"


def key() -> str:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("ELEVENLABS_API_KEY="):
            v = line.split("=", 1)[1].strip().strip('"').strip("'")
            if v:
                return v
    sys.exit("ELEVENLABS_API_KEY is not set in .env")


def headers() -> dict:
    return {"xi-api-key": key(), "accept": "audio/mpeg"}


def tts(voice_id: str, text: str, out_wav: Path, seed: int | None = None, model: str = MODEL) -> dict | None:
    """One render. Uses /with-timestamps (character alignment) and falls back to plain TTS if the model refuses it.
    Returns the alignment ({characters, character_start_times_seconds, ...}) or None."""
    import base64
    body = {"text": text, "model_id": model, "voice_settings": SETTINGS, "language_code": "en"}
    if seed is not None:
        body["seed"] = seed
    q = {"output_format": "mp3_44100_128"}
    r = requests.post(f"{API}/v1/text-to-speech/{voice_id}/with-timestamps", params=q,
                      headers={"xi-api-key": key()}, json=body, timeout=180)
    align = None
    if r.status_code == 200:
        j = r.json()
        audio = base64.b64decode(j["audio_base64"])
        align = j.get("alignment")
    else:
        r = requests.post(f"{API}/v1/text-to-speech/{voice_id}", params=q, headers=headers(), json=body, timeout=180)
        if r.status_code != 200:
            sys.exit(f"ElevenLabs {r.status_code}: {r.text[:300]}")
        audio = r.content
    mp3 = out_wav.with_suffix(".mp3")
    mp3.write_bytes(audio)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3), "-ar", "48000", "-ac", "1",
                    "-c:a", "pcm_s24le", str(out_wav)], check=True)
    mp3.unlink(missing_ok=True)
    if align:
        out_wav.with_suffix(".align.json").write_text(json.dumps(align), encoding="utf-8")
    return align


def cmd_voices() -> None:
    r = requests.get(f"{API}/v2/voices", params={"page_size": 100}, headers={"xi-api-key": key()}, timeout=60)
    if r.status_code != 200:
        r = requests.get(f"{API}/v1/voices", headers={"xi-api-key": key()}, timeout=60)
    r.raise_for_status()
    for v in r.json().get("voices", []):
        lab = v.get("labels") or {}
        print(f"{v['voice_id']}  {v['name']:24} {lab.get('gender', ''):7} {lab.get('accent', ''):12} "
              f"{lab.get('age', ''):12} {lab.get('description', lab.get('descriptive', ''))} {lab.get('use_case', '')}")


def cmd_audition(ids: list[str]) -> None:
    out = ROOT / ".demo" / "review" / "eleven"
    out.mkdir(parents=True, exist_ok=True)
    text = TAGGED[AUDITION_LINE]
    print(f"audition: {len(ids)} x {len(text)} chars")
    for vid in ids:
        tts(vid, text, out / f"audition_{vid}.wav")
        print("wrote", out / f"audition_{vid}.wav")


SEEDS = (1101, 2202)                                   # two takes per line; choose.py keeps the better one
CAND = ROOT / ".demo" / "review" / "eleven" / "takes"


def cmd_render(vid: str, only: list[str]) -> None:
    lines = {k: v for k, v in TAGGED.items() if not k.startswith("_") and (not only or k in only)}
    for k in lines:                                   # the words must match the cue sheet's line (minus tags/caps)
        cue = CUES["voice"][int(k) - 1]
        assert cue["who"] == "Barnaby", (k, cue["who"])
    cost = sum(len(t) for t in lines.values()) * len(SEEDS)
    print(f"render: {len(lines)} lines x {len(SEEDS)} takes, about {cost} credits")
    CAND.mkdir(parents=True, exist_ok=True)
    for k, text in lines.items():
        for sd in SEEDS:
            dest = CAND / f"{k}_s{sd}.wav"
            if dest.exists():
                continue                              # never pay twice for a take we have
            al = tts(vid, text, dest, seed=sd)
            print("wrote", dest.name, "(timestamps)" if al else "")



# ── v4, performed as passages: one request per scene, split back into lines by the character alignment ──────────
V4 = json.loads((HERE / "barnaby_v4.json").read_text(encoding="utf-8"))
V4DIR = ROOT / ".demo" / "review" / "eleven" / "v4"
SEP = "\n\n"


def _wav(path: Path):
    import wave
    import numpy as np
    with wave.open(str(path)) as w:
        sr, raw, sw = w.getframerate(), w.readframes(w.getnframes()), w.getsampwidth()
    if sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        x = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
        x = np.where(x >= 1 << 23, x - (1 << 24), x).astype(np.float32) / (1 << 23)
    else:
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    return x, sr


def cmd_passages(vid: str, which: list[str], seed: int | None = None, tag: str = "") -> None:
    """Render the passages that contain any of `which` (all if empty) with eleven_v4, then split into lines."""
    import numpy as np
    import soundfile as sf
    V4DIR.mkdir(parents=True, exist_ok=True)
    todo = [ps for ps in V4["_passages"] if not which or set(ps) & set(which)]
    cost = sum(len(SEP.join(V4[k] for k in ps)) for ps in todo)
    print(f"v4 passages: {len(todo)}, about {cost} credits")
    for ps in todo:
        text = SEP.join(V4[k] for k in ps)
        whole = V4DIR / f"passage_{ps[0]}-{ps[-1]}{tag}.wav"
        al = tts(vid, text, whole, seed=seed, model="eleven_v4")
        if not al:
            sys.exit("no alignment returned; can't split the passage")
        chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
        assert "".join(chars) == text, "alignment text differs from the request"
        x, sr = _wav(whole)
        spans, pos = [], 0
        for k in ps:
            a, b = pos, pos + len(V4[k])
            idx = [i for i in range(a, b) if not chars[i].isspace()]
            spans.append((k, st[idx[0]], en[idx[-1]], a))
            pos = b + len(SEP)
        for j, (k, t0, t1, a) in enumerate(spans):
            c0 = 0.0 if j == 0 else (spans[j - 1][2] + t0) / 2
            c1 = len(x) / sr if j == len(spans) - 1 else (t1 + spans[j + 1][1]) / 2
            seg = x[int(c0 * sr):int(c1 * sr)]
            sf.write(str(V4DIR / f"{k}{tag}.wav"), seg, sr, subtype="PCM_24")
            n = len(V4[k])
            sub = {"characters": chars[a:a + n], "character_start_times_seconds": [v - c0 for v in st[a:a + n]],
                   "character_end_times_seconds": [v - c0 for v in en[a:a + n]]}
            (V4DIR / f"{k}{tag}.align.json").write_text(json.dumps(sub), encoding="utf-8")
            print(f"  {k}: {t1 - t0:.2f} s of speech, cut {c0:.2f}-{c1:.2f}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    c = sys.argv[1]
    if c == "voices":
        cmd_voices()
    elif c == "audition":
        cmd_audition(sys.argv[2:])
    elif c == "render":
        cmd_render(sys.argv[2], sys.argv[3:])
    elif c == "passages":
        rest = sys.argv[3:]
        sd = next((int(a.split("=")[1]) for a in rest if a.startswith("seed=")), None)
        cmd_passages(sys.argv[2], [a for a in rest if not a.startswith("seed=")], seed=sd, tag=f"_s{sd}" if sd else "")
    else:
        sys.exit(__doc__)
