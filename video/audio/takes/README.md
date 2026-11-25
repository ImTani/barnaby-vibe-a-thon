# Recorded takes

Drop recorded lines here, named like the generated file they replace (see `../voice/manifest.json`):
`03_Martin.wav`, `05_Martin.wav`, `07_Martin.wav`, `09_Martin.wav`, `12_Martin.wav`.
Keep each about as long as the current line (3.7, 3.0, 0.9, 2.3, 1.6 s) so it ends before the next one.

Then, from the repo root:

```bash
source scripts/env.sh
runtime/voice/.venv/Scripts/python video/audio/voices.py      # takes replace the TTS lines; reports any overlaps
runtime/audio/.venv/Scripts/python video/audio/score.py       # remix (about a minute)
(cd video && node render.js mux)                              # new soundtrack onto the same picture
```
