"""Barnaby's voice from ElevenLabs (eleven_v3, audio tags), for the film. Free plan: non-commercial, attribution
("Barnaby's voice: ElevenLabs" in the end card).

  runtime/voice/.venv/Scripts/python video/v2/audio/eleven.py voices            British/English male voices
  runtime/voice/.venv/Scripts/python video/v2/audio/eleven.py audition ID ...   one line per voice -> .demo/review/
  runtime/voice/.venv/Scripts/python video/v2/audio/eleven.py render ID [NN ...]
        Barnaby's lines (barnaby_v3.json: the cue text with v3 tags) -> video/v2/audio/takes/NN_Barnaby.wav,
        which voices.py --takes copies in place of the generated line (then layout.py re-times the film).

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


def tts(voice_id: str, text: str, out_wav: Path) -> None:
    r = requests.post(f"{API}/v1/text-to-speech/{voice_id}", params={"output_format": "mp3_44100_128"},
                      headers=headers(), json={"text": text, "model_id": MODEL, "voice_settings": SETTINGS}, timeout=120)
    if r.status_code != 200:
        sys.exit(f"ElevenLabs {r.status_code}: {r.text[:300]}")
    mp3 = out_wav.with_suffix(".mp3")
    mp3.write_bytes(r.content)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3), "-ar", "48000", "-ac", "1",
                    "-c:a", "pcm_s24le", str(out_wav)], check=True)


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


def cmd_render(vid: str, only: list[str]) -> None:
    lines = {k: v for k, v in TAGGED.items() if not k.startswith("_") and (not only or k in only)}
    for k in lines:                                   # the words must match the cue sheet's line (minus tags/caps)
        cue = CUES["voice"][int(k) - 1]
        assert cue["who"] == "Barnaby", (k, cue["who"])
    print(f"render: {len(lines)} lines, {sum(len(t) for t in lines.values())} chars")
    TAKES.mkdir(parents=True, exist_ok=True)
    for k, text in lines.items():
        dest = TAKES / f"{k}_Barnaby.wav"
        tts(vid, text, dest)
        dest.with_suffix(".mp3").unlink(missing_ok=True)
        print("wrote", dest)


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
