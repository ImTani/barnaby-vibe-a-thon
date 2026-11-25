# Barnaby

**Every system deserves a butler.** *…even the old ones.*

Barnaby is a voice-first agent you point at any codebase. **Synapse** makes the repo agent-ready, turning its HTTP
endpoints into MCP tools, and Barnaby looks after the system from there. You ask in plain speech; he answers through
the system's own tools. When the system can't do what you asked, Barnaby **grows**, always with your approval:

| Tier | When | What Barnaby does | Synapse feature |
|---|---|---|---|
| **Ask** | The tools he has can answer | Calls the system's read-only tools and answers aloud | `build --auto --local` (MCP server from the repo) |
| **Unlock** | Synapse found an endpoint that would do it | Asks, then exposes that endpoint as a new tool (one click) | the discovery atlas, then a rebuild with `--endpoints` (under a second: 0.3–0.8 s in our runs) |
| **Compose** | You keep asking for the same chain of steps | Fuses the chain into one skill from the system's own functions | `build --custom -q "…"` (hosted Custom mode) |
| **Build** | Nothing in the code can do it | Writes the missing endpoint in a git worktree with tests, tells you in plain words what it does, and adds it when you click (the change is there to read) | `build --discover` picks up the new endpoint |

Track 4 (Open innovation) · 2nd Brain Labs × Geek Room Vibe-a-thon · built on
[Synapse CLI](https://www.npmjs.com/package/@2ndbrainlabs-ai/synapse-cli) 0.1.9.

**Videos.** The film, *Every system deserves a butler* (5:07): Blender dioramas, the real app's screens and the shop's
2009 back office composited in code, a score and sound design from code, Martin, Theo and Priya voiced by real people
and Barnaby by ElevenLabs (see [`video/v2/`](video/v2/); English captions in
[`video/v2/film/barnaby_v2.en.srt`](video/v2/film/barnaby_v2.en.srt)). It is in the Demo Video folder linked from the
submission form, with a live walkthrough of the real app to follow ([`docs/WALKTHROUGH.md`](docs/WALKTHROUGH.md)).

---

## For judges

| Criterion | Where to look |
|---|---|
| **Originality and real-world value** | Every small business runs on a system nobody has time to rewrite, and the person who wrote it eventually leaves. Barnaby is a handover: point him at the repo, and the system gets a butler who can answer, act, and grow what's missing. Voice-first, bring-your-own-repo, and an agent that writes its own missing endpoint. See [`docs/WRITEUP.md`](docs/WRITEUP.md). |
| **How central Synapse is** | Barnaby has **no tools of his own** except growth. Every system tool is a Synapse-generated MCP server. Connect, Unlock, Compose and Build each *are* a Synapse call (table above). Synapse's surface cache is his map of what the system *could* do. See [`docs/MCP_SETUP.md`](docs/MCP_SETUP.md). |
| **Technical execution** | [`scripts/demo_check.py`](scripts/demo_check.py) drives the whole story against the real stack (no mocks), in the film's order, and checks every outcome against the shop's own API and git history, plus that nothing Barnaby said aloud used the machine's words: **16/16 pass**. 28 fast unit tests cover the fix-up pass, the discovery atlas, approval tiers, habit detection, the plain-language cards and the bring-your-own-model worker (`.venv/Scripts/python -m pytest tests`). A fix-up pass repairs known Synapse 0.1.9 output issues (disclosed below). Approvals are tiered; code changes land only after the tests pass and you click to approve. |
| **Quality of the demo** | The film tells one family's story in five minutes; the walkthrough shows the same flow live in the real app. What's real and what's staged is in the table [below](#real-vs-staged). |

### The real run, end to end (`scripts/demo_check.py`, 25 Nov, 18:30 IST)

In the film's order, typed as the voice layer would pass them, with every card approved automatically (as if Martin
clicked). Times are wall-clock per beat, on the local Claude Code login.

| Beat | Request | What happened | Time |
|---|---|---|---|
| 1 Arrival | "Barnaby, this is the shop's system. Look after them for me." | Synapse discovered **23 endpoints** (its two builds took 0.75 s and 0.65 s); 6 read-only tools exposed | 25.3 s |
| 2 Ask | "Which repairs are due tomorrow, and are we short on parts for any of them?" | 7 tool calls; five due, and Anika Banerjee's brake job is one pair of pads short | 13.4 s |
| 3 Unlock | "Order ten pairs of those brake pads from the usual supplier." | card "Let Barnaby order parts from your suppliers" → unlock `POST /api/purchase-orders` (rebuild 0.76 s) → write card → order placed (ten pairs from Madison, £65) | 15.0 s |
| 4 Compose | Sofia's (4475), Kwame's (4490) and Jana's (4488) bikes: "Text her it's ready to collect and mark it ready." Then Tom's (4481): "… And make handing back a bike a single step, would you?" | the first hand-back unlocks texting and job status (0.43 s, 0.41 s rebuilds); after the repeats Barnaby offers a single step; Synapse Custom composed `notify_bike_ready_and_update_job` ("Hand back a bike in one step") from the shop's own functions in 27 s, and Barnaby used it for Tom: all four texted and marked ready | 78.3 s (all four) |
| 5 Build | "Who's overloaded this week?" | the builder wrote `GET /api/reports/workload/{day}` + service + 4 tests in a worktree (64 s) → 23 tests pass (Theo's 19 + 4) → plain-words card approved → merged → restart → `--discover` (24 endpoints) → "Dev … thirty-one hours … against his twenty" (the report reads exactly 31.0 h) | 95.6 s |
| 6 Act | "Move Dev's two wheel builds to Priya, please." | unlocked `assign` (0.48 s); jobs 4471 and 4472 now Priya's in the 2009 system; "Dev's down to nineteen and a half hours" | 14.8 s |
| Speech | everything Barnaby said in the run | 26 lines, none with endpoint, API, tool, MCP, server, deploy, merge, diff, worktree or Synapse | |

Run it yourself: `.venv/Scripts/python scripts/demo_check.py` (about 4 minutes; it resets the demo world first and
needs `SYNAPSE_API_KEY` for the Compose checks).

---

## How it works

```
 Listening (pluggable)   sherpa streaming ASR (own server) · faster-whisper (local) · Groq Whisper
 Voice (pluggable)       Kokoro (George 75% + Fable 25%, misaki G2P, British) · Qwen3-TTS
 Voice pipeline          Pipecat + SmallWebRTC (browser mic, hold-to-talk or hands-free), spoken "yes" for write cards
 ─────────────────────────────── core (the submission; works text-only) ───────────────────────────────
 Systems registry ─► Synapse driver ─► MCP servers (one per system + one per composed skill)
        │                                   │ stdio
        ▼                                   ▼
 Worker agent (Claude Agent SDK, or any model on Pydantic AI) ◄── growth tools: capabilities · unlock · compose · build · connect
        │  every tool call ─► can_use_tool ─► tier policy ─► approvals (cards on the display)
        ▼
 Event bus (SSE) ─► display (his work inline in plain words, approval cards, What he can do) and the voice bridge
```

- **Synapse driver** ([`barnaby/synapse.py`](barnaby/synapse.py)) runs the pinned local CLI non-interactively, reads
  `.synapse/surface_cache.json` as the capability atlas, moves generated servers out of the target repo (so the repo
  stays clean and diffs never include generated files), and applies the fix-up pass.
- **Worker** ([`barnaby/worker.py`](barnaby/worker.py)) is the Claude Agent SDK, running on the local Claude Code login
  (or an API key). Each system's server attaches over stdio. After a growth step the servers are reconnected and the
  turn continues, so the new tool is used straight away.
- **Bring your own model** ([`barnaby/worker_byom.py`](barnaby/worker_byom.py)): the same worker on Pydantic AI, so
  any provider works (`BARNABY_WORKER_BACKEND=byom`, `BARNABY_BYOM_MODEL=openai:…`, `groq:…`, `ollama:…`). Both
  workers share one prompt, one tier gate and one set of growth tools ([`barnaby/toolkit.py`](barnaby/toolkit.py)).
  Only the Build tier's code writer is Claude-specific.
- **Build** ([`barnaby/build.py`](barnaby/build.py)): a git worktree, a builder agent limited to that worktree, the
  system's own test suite, then a plain-words explanation (what it does, what it reads and changes, the checks, that
  it can be undone), spoken and on the approval card with the diff folded underneath, a fast-forward merge on your
  click, a deterministic restart, and `synapse build --discover`. The README in the repo (the departing developer's notes) outranks the spec.
- **Compose** (`build_custom` in `barnaby/synapse.py`): hosted Synapse Custom mode composes the repo's own internal
  functions into one tool. Barnaby also spots habits (the same chain of calls repeated) and offers to compose them.
- **Display** ([`ui/`](ui/)), round 3, the default: modelled on the Claude and Codex desktop apps, for the person
  who runs the business rather than a developer. One column holds his words, his work and the cards in the order they
  happened. His work shows inline and collapsed, as one grey line in plain words ("Looked at repair jobs due on Tue 24
  Nov, … 7s ›"), with a live line (his mark at work, what he's doing now, a timer) while he works; each step opens to
  its technical record. His words are set in an upright serif; brass is the one brand colour; his mark is a counter
  bell wearing a bow tie. A side panel shows what he's connected to, the keys you gave him and what he made with your
  say-so; "What he can do" lists every ability in plain words with its state, and holds the "Connect a system" form.
  The design is written up in [`DESIGN.md`](DESIGN.md) and [`PRODUCT.md`](PRODUCT.md); the look is
  [`ui/skins/app3.css`](ui/skins/app3.css). `?skin=classic` keeps the old developer look (live trace and capability
  map), `?theme=dark` gives dark, `?overlay=1` the compact window, and `?mock=1` replays a recorded run (recorded before
  the film's order, so it has no hand-backs).
- **Voice** ([`voice/`](voice/)): a separate Pipecat process. Without an LLM key, a small bridge acknowledges
  requests, narrates growth steps, and speaks Barnaby's replies; a spoken "yes" resolves write cards. The Claude Haiku
  front desk slots in when a key is present.

### Safety, in plain language

Every card speaks to the household, not a developer: what it does, what it reads and changes, the checks and the
undo. The endpoint, the arguments and the test line travel in each approval event's `technical` field, and the card
keeps them folded under "Technical detail" for whoever wants them; a Build card also folds the change itself under
"See the change". Barnaby's prompt keeps the machine's words out of what he says aloud, and `demo_check` fails the run
if any slip through ([`barnaby/policy.py`](barnaby/policy.py), [`barnaby/toolkit.py`](barnaby/toolkit.py)).

| Action | Gate |
|---|---|
| Read-only tool call | none |
| Data write (POST/PUT/PATCH, composed skills) | a card ("A change to your records"): click "Approve", or just say "yes" |
| Unlock / Compose | one click ("A new key", "A shortcut"); a spoken yes doesn't count |
| Build (writes code) | Barnaby says what he made, what it reads and changes, that the checks pass and that it can be undone; the card says the same. Approve with a click on "Yes, add it". **Never by voice alone** ("That one needs a look and a click on the display, I'm afraid."). Worktree; tests must pass; revertable |
| Deny-list | endpoints that can never be exposed (e.g. `DELETE /api/jobs/{job_id}`) |

---

## Real vs staged

The app is real, and the walkthrough is a live run of it with the requests read from a script. The film is a staged
recreation of a real run, like most product films.

| Thing | Status |
|---|---|
| Synapse discovery, MCP servers, Unlock rebuilds, `--discover` after Build | **Real** (every run) |
| Compose via hosted Synapse Custom mode | **Real** (needs a free `SYNAPSE_API_KEY`) |
| Barnaby's answers, tool calls, approvals, the Build diff and its tests | **Real** (`demo_check` runs them; the film's diff and figures come from a recorded run, [`video/data.js`](video/data.js), and the demo shop's seed) |
| Spokes & Sprockets, Theo, Martin, Priya | **Fiction.** The shop, its people and its data are made up: a purpose-built 2009-style app ([`systems/spokes-and-sprockets`](systems/spokes-and-sprockets)) with 29 invented customers, seeded jobs and backdated git history |
| The film (v2, [`video/v2/`](video/v2/)) | **Rendered from code**: procedural Blender dioramas of the shop desk and a Lisbon desk, animated ([`desk.py`](video/v2/world/desk.py), [`lisbon.py`](video/v2/world/lisbon.py), [`anim.py`](video/v2/world/anim.py)), screens designed as HTML pages and composited live onto the monitors, and an HTML film engine in which every frame is a pure function of time, encoded with ffmpeg (1080p, 24 fps, 5:07). It's a staged recreation of the real run. Voices: Martin, Theo and Priya by real people; Barnaby by ElevenLabs. The file itself (gitignored, too large for the repo) is in the submission's Demo Video folder; the low-res animatic (960×540, 15 fps) is in [`video/v2/animatic/`](video/v2/animatic/) |
| The film's voices | Martin, Theo and Priya: **real people**, recorded in DubMate against the picture; the film is re-timed around their reads (word timings by Whisper). Barnaby: **ElevenLabs v4** (voice "George"), performed scene by scene; free plan, non-commercial, credited on the end card |
| The film's Lisbon scene (Quorum, ComfyUI) | **Staged** (an on-screen note says so). The endpoint counts are **real** Synapse scans (13 and 28) |
| Brands | No real brand logos are used in the film |
| Score and sound | Music composed in code and **played by real instrument plugins** (Ample Guitar M Lite II, MODO BASS 2, Valhalla VintageVerb) via DawDreamer. Sound effects from Ableton Live 12's Core Library samples, being finished for the final mix |
| Voice (the app) | **Real** (push-to-talk → sherpa ASR → Barnaby → Kokoro), verified by `scripts/smoke/voice_e2e.py`. The Haiku front desk is built for, and runs when an API key is present |
| Bring-your-own-model worker | **Built and unit-tested** against a real stdio MCP server with a scripted model; not yet run against a live third-party model. Each provider needs its pydantic-ai extra |
| Not done yet | The Tauri hotkey overlay (the compact display exists), a trained wake word, the v2 film's final render |

### Synapse 0.1.9: issues we hit, and the disclosed fix-up pass

| Issue (confirmed in our smoke tests) | What Barnaby does |
|---|---|
| Every generated parameter is `Any = None`: no types, nothing required | `fixup()` restores types and required flags from the discovered signature and payload examples |
| `raise_for_status()` hides the API's error body from the agent | `fixup()` returns the status code and error body instead |
| Writes `~/.synapse` even with telemetry off | Synapse runs with `HOME`/`USERPROFILE` set to a repo-local folder |
| Repeated builds write `_2.py`, `_3.py`…; Custom mode scans its own earlier outputs | Outputs are moved out of the repo after every build |
| Query params, router prefixes and `Literal` body fields are dropped | Our demo app uses full paths in decorators and path params; disclosed for other repos |
| Generated servers need `mcp==1.30` | A separate pinned runtime (`runtime/mcp-servers`) |

Synapse's original output is kept beside each fixed server (`server.synapse.py`), so the fix-up is auditable.

---

## Run it

Everything is repo-local: venvs, `node_modules`, model and package caches, Synapse's home. Delete the folder and
nothing remains (except that, as with any Claude Code session, the Agent SDK's transcripts land in `~/.claude/projects`;
it runs with `setting_sources=[]`, so your own Claude Code settings, plugins and hooks never load). Windows 11, Python 3.12, Node 20+, [uv](https://docs.astral.sh/uv/).

Run these from the repo root in Git Bash:

```bash
source scripts/env.sh                         # (PowerShell: . scripts/env.ps1) keeps every cache inside the repo
npm ci                                        # Synapse CLI 0.1.9 as a local devDependency
uv sync                                       # core (.venv)
(cd runtime/mcp-servers && uv sync)           # mcp==1.30 for Synapse's generated servers
uv venv runtime/legacy/.venv --python 3.12    # the 2009 shop app (it has a requirements.txt, not a pyproject)
uv pip install --python runtime/legacy/.venv/Scripts/python.exe -r systems/spokes-and-sprockets/requirements.txt
cp .env.example .env                          # optional; add SYNAPSE_API_KEY=... for Compose (not in the example)

.venv/Scripts/python scripts/demo_reset.py    # a fresh copy of the shop in .demo/, with Theo's git history
.venv/Scripts/python -m barnaby serve         # the app + API on http://127.0.0.1:8700
```

Open http://127.0.0.1:8700 and type (or say) *"Barnaby, this is the shop's system."* He starts the shop on
http://127.0.0.1:8101 himself. The heavy thinking runs on your local Claude Code login through the Claude Agent SDK,
so the core needs no API key. A step-by-step demo, with what to say and what appears, is in
[`docs/WALKTHROUGH.md`](docs/WALKTHROUGH.md).

- **Text only:** `.venv/Scripts/python -m barnaby connect shop`, then
  `.venv/Scripts/python -m barnaby ask "Which repairs are due tomorrow?"`. There's no display to click in a
  terminal, so a request that needs a card wants `--auto write,grow,build` (approve every card, as `demo_check` does).
  `demo_reset.py` stops the shop again.
- **Tests:** `.venv/Scripts/python -m pytest tests` (27 unit tests, a few seconds) and
  `.venv/Scripts/python scripts/demo_check.py` (the whole story, about 4 minutes).
- **Voice:** `(cd runtime/voice && uv sync)`, then `runtime/voice/.venv/Scripts/python voice/bot.py -t webrtc --port 7860`,
  then click an empty part of the app and hold Space. Listening defaults to a sherpa server (`SHERPA_WS_URL`); set
  `BARNABY_LISTEN=whisper` for local Whisper.
- **Any repo:** start its HTTP API, then use *Connect a system* ("+" in the composer, or the foot of *What he can do*)
  with a name, the repo path and the API's URL; or tell Barnaby the repo path and the URL its API runs at.
- **Bring your own model:** `BARNABY_WORKER_BACKEND=byom` and `BARNABY_BYOM_MODEL=<provider>:<model>` in `.env`
  (that provider's pydantic-ai extra and key needed; only `anthropic` ships in `.venv`).
- **Replay a recorded run** (no agent, no shop): `http://127.0.0.1:8700/?mock=1`.
- **The film:** `node video/v2/film/render.js` renders the v2 film to `video/v2/film/out/barnaby_v2.mp4`, with the
  soundtrack from `video/v2/audio/` muxed in (the engine is still being finished); `node video/v2/animatic/render.js`
  renders the low-res animatic. Both need `npm ci` in `video/` first, and use the installed Chrome and `ffmpeg` on
  PATH. The v1 film: [`video/FRAMEWORK.md`](video/FRAMEWORK.md), `node render.js` in `video/`.

## Repo map

| Path | What |
|---|---|
| `barnaby/` | the core: Synapse driver, systems registry, workers (Claude Agent SDK and bring-your-own-model, sharing `toolkit.py`), Build tier, policy, events, API server |
| `ui/` | the app (plain HTML/CSS/JS, SSE); round 3 is `ui/skins/app3.css`, the mark is in `ui/assets/` |
| `DESIGN.md`, `PRODUCT.md` | the app's design system and who it's for |
| `tests/` | unit tests (core and the bring-your-own-model worker) |
| `voice/` | the voice layer (Pipecat bot, sherpa STT service, Kokoro voice, bridge) |
| `systems/spokes-and-sprockets/` | the demo world: Theo's 2009 back office (FastAPI, SQLite, Jinja, 19 tests) |
| `scripts/` | `demo_reset.py`, `demo_check.py`, smoke tests, dev helpers |
| `runtime/` | separate pinned runtimes: MCP servers, the legacy app, voice, audio |
| `video/v2/` | the v2 film: world bible ([`WORLD.md`](video/v2/WORLD.md)), speech pacing ([`SPEECH.md`](video/v2/SPEECH.md)), the Blender diorama (`world/`), look-dev pages and review stills (`look/`), cue sheet, animatic, soundtrack |
| `video/` | the v1 film (scenes, components, cue sheet, score, voice lines) and the shared voice renderer |
| `docs/` | [`WRITEUP.md`](docs/WRITEUP.md), [`WALKTHROUGH.md`](docs/WALKTHROUGH.md), [`MCP_SETUP.md`](docs/MCP_SETUP.md), the v2 script (`script.html`), the plan and the v1 storyboard |
