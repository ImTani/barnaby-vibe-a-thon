# Recording the walkthrough

A real, unscripted-looking run of the app, about 2½ minutes after editing. You speak; Barnaby answers aloud; the
display and the 2009 shop are on screen. Long waits (Build ≈ 75 s, Compose ≈ 50 s) are cut in the edit, so don't
fill them: just let them run.

## Before you hit record (5 minutes)

Run each in its own terminal, from the repo root:

```bash
source scripts/env.sh
python scripts/demo_reset.py                           # fresh shop + Theo's history; Barnaby forgets everything
.venv/Scripts/python -m barnaby serve                  # display on http://127.0.0.1:8700
```
```bash
source scripts/env.sh
runtime/voice/.venv/Scripts/python voice/bot.py -t webrtc --port 7860   # voice (sherpa on your server by default)
```

- `.env` has `SYNAPSE_API_KEY` (needed for Compose). If the Claude key has arrived, set
  `BARNABY_WORKER_BACKEND=api` there for snappier turns; otherwise the worker uses your Claude Code login.
- Screen: the display at about 1440 px wide on the right, and a browser window on the left that you'll point at the
  shop (http://127.0.0.1:8101) once Barnaby has connected it. The shop page refreshes itself.
- Audio: record your mic **and** system audio (Barnaby's voice comes out of the browser tab).
- Click once in the display so it has focus; **hold Space to talk**, release when you're done.
- Do a 10-second sound check first: hold Space, say "Barnaby, are you there?" and check he answers.
  Then rerun `demo_reset.py` and restart `serve` so the recording starts clean.

## The run (say these, or your own words)

| # | You | What to do / what happens | Expect |
|---|---|---|---|
| 1 | *"Barnaby, this is the shop's system. Look after them for me."* | Synapse scans the repo; the capability map fills | "It can do twenty-three things… I'll start with the six that only look" (≈ 20 s) |
| 2 | *(open the shop at :8101 on the left)* | Show the 2009 UI for a beat | |
| 3 | *"Which repairs are due tomorrow, and are we short on parts?"* | Read rows in the trace (blue) | Anika's brake job, one pair short (≈ 8 s) |
| 4 | *"Order ten pairs from the usual supplier."* | Barnaby asks ("I can't order parts myself yet… Shall I take that on?"); a brass card, **Let Barnaby order parts…**: click **Yes, go ahead**. Then an orange write card: say **"Yes"** (or click) | Order placed; show the shop's Purchase Orders tab |
| 5 | *"Who's overloaded this week?"* | Violet Build rows stream (cut most of this). Barnaby says what he made, what it reads and changes; the Build card says the same, with the diff under **See the change**: open it, scroll, then click **Yes, add it** (never by voice) | "Dev has thirty-one hours booked against twenty…" (≈ 75 s) |
| 6 | *"Yes, move the two wheel builds to Priya."* | Barnaby asks to take on reassigning jobs (click **Yes, go ahead**), then say **"Yes"** to each write card | The shop's Jobs table flips Dev → Priya |
| 7 | *"Tom's bike is done, job 4481. Hand it back, and make that a single step, would you?"* | A brass card, **Hand back a bike in one step**: click. Then **"Yes"** to the skill's write card | "Handing back a bike is now a single step…" (≈ 50 s) |
| 8 | *(click Capabilities, top right)* | 24 endpoints, the new one marked, and the ✦ skill | end on this |

If a beat goes sideways, keep going: it's a real agent. Say "Not now" or click Decline, then rephrase. If you need to
restart: stop `serve`, rerun `demo_reset.py`, start `serve`.

## After recording

Drop the file in `.demo/recordings/` (gitignored) and tell me. I'll cut the waits, add captions for the tiers, and
level the audio to match the film (−16 LUFS).
