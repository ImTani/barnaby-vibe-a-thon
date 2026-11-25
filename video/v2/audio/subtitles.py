"""English captions for the film, from the cue sheet: every voice line, timed to its speech, named by speaker
(nobody is ever on screen, so the name says who's talking).

  runtime/voice/.venv/Scripts/python video/v2/audio/subtitles.py   -> video/v2/film/barnaby_v2.en.srt

A caption shows from the speech onset to 0.35 s after the speech ends (at least 1.0 s on screen), never overlapping
the next one; lines wrap at about 42 characters, two lines at most.
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
OUT = V2 / "film" / "barnaby_v2.en.srt"


def ts(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> None:
    voice = json.loads((V2 / "cues.json").read_text(encoding="utf-8"))["voice"]
    rows = []
    for i, v in enumerate(voice):
        a, b = v["speech"]
        end = max(b + 0.35, a + 1.0)
        if i + 1 < len(voice):
            end = min(end, voice[i + 1]["speech"][0] - 0.05)
        text = f"{v['who'].upper()}: {v['text']}"
        lines = textwrap.wrap(text, 42)
        if len(lines) > 2:
            lines = textwrap.wrap(text, (len(text) + 1) // 2 + 4)
        rows.append(f"{i + 1}\n{ts(a)} --> {ts(end)}\n" + "\n".join(lines) + "\n")
    OUT.write_text("\n".join(rows), encoding="utf-8")
    print(f"wrote {OUT} ({len(rows)} captions)")


if __name__ == "__main__":
    main()
