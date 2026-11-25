"""Barnaby's voice from ElevenLabs (eleven_v3, audio tags), for the film. Free plan: non-commercial, attribution
("Barnaby's voice: ElevenLabs" in the end card).

  runtime/voice/.venv/Scripts/python video/v2/audio/eleven.py voices            British/English male voices
  runtime/voice/.venv/Scripts/python video/v2/audio/eleven.py audition ID ...   one line per voice -> .demo/review/
  runtime/voice/.venv/Scripts/python video/v2/audio/eleven.py render ID [NN ...]
        Barnaby's lines (barnaby_v3.json: the cue text with v3 tags), two seeds each, with ElevenLabs' character
        timestamps -> .demo/review/eleven/takes/NN_s<seed>.wav (+ .align.json). Takes already on disk are skipped.
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


def tts(voice_id: str, text: str, out_wav: Path, seed: int | None = None) -> dict | None:
    """One render. Uses /with-timestamps (character alignment) and falls back to plain TTS if the model refuses it.
    Returns the alignment ({characters, character_start_times_seconds, ...}) or None."""
    import base64
    body = {"text": text, "model_id": MODEL, "voice_settings": SETTINGS, "language_code": "en"}
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
    else:
        sys.exit(__doc__)
