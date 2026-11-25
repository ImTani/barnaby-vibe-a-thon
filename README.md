# Barnaby

**Every system deserves a butler.** *…even the old ones.*

Barnaby is a voice-first agent you point at any codebase. **Synapse** makes the repo agent-ready, turning its HTTP
endpoints into MCP tools, and Barnaby looks after the system from there. You ask in plain speech; he answers through
the system's own tools. When the system can't do what you asked, Barnaby **grows**, always with your approval:

| Tier | When | What Barnaby does | Synapse feature |
|---|---|---|---|
| **Ask** | The tools he has can answer | Calls the system's read-only tools and answers aloud | `build --auto --local` (MCP server from the repo) |
| **Unlock** | Synapse found an endpoint that would do it | Asks, then exposes that endpoint as a new tool (one click) | the discovery atlas, then a rebuild with `--endpoints` (0.3–0.5 s) |
| **Compose** | You keep asking for the same chain of steps | Fuses the chain into one skill from the system's own functions | `build --custom -q "…"` (hosted Custom mode) |
| **Build** | Nothing in the code can do it | Writes the missing endpoint in a git worktree with a test; you review the diff | `build --discover` picks up the new endpoint |

Track 4 (Open innovation) · 2nd Brain Labs × Geek Room Vibe-a-thon · built on
[Synapse CLI](https://www.npmjs.com/package/@2ndbrainlabs-ai/synapse-cli) 0.1.9.

**Videos.** The film (2:40, rendered from code; see [`video/`](video/)) and a real walkthrough (recorded on this
machine). *Links are added at submission.*

---

## For judges

| Criterion | Where to look |
|---|---|
| **Originality and real-world value** | Every small business runs on a system nobody has time to rewrite, and the person who wrote it eventually leaves. Barnaby is a handover: point him at the repo, and the system gets a butler who can answer, act, and grow what's missing. Voice-first, bring-your-own-repo, and an agent that writes its own missing endpoint. See [`docs/WRITEUP.md`](docs/WRITEUP.md). |
| **How central Synapse is** | Barnaby has **no tools of his own** except growth. Every system tool is a Synapse-generated MCP server. Connect, Unlock, Compose and Build each *are* a Synapse call (table above). Synapse's surface cache is his map of what the system *could* do. See [`docs/MCP_SETUP.md`](docs/MCP_SETUP.md). |
| **Technical execution** | [`scripts/demo_check.py`](scripts/demo_check.py) drives the whole story against the real stack (no mocks) and checks every outcome against the shop's own API and git history: **15/15 pass**. A fix-up pass repairs known Synapse 0.1.9 output issues (disclosed below). Approvals are tiered; code changes land only after tests pass and you approve the diff. |
| **Quality of the demo** | The film tells one family's story in 160 s; the walkthrough shows the same flow live. What's real and what's staged is in the table [below](#real-vs-staged). |

### The real run, end to end (`scripts/demo_check.py`, 25 Nov)

| Beat | Request (typed, as the voice layer would pass it) | What happened | Time |
|---|---|---|---|
| 1 Arrival | "Barnaby, this is the shop's system. Look after them for me." | Synapse discovered **23 endpoints**; 6 read-only tools exposed | 19.7 s (Synapse 0.5 s) |
| 2 Ask | "Which repairs are due tomorrow, and are we short on parts?" | 6 tool calls; names Anika's brake job, short one pair of pads | 8.4 s |
| 3 Unlock | "Order ten pairs of those brake pads from the usual supplier." | `capabilities` → unlock `POST /api/purchase-orders` (rebuild 0.32 s) → write card → order placed | 9.3 s |
| 4 Build | "Who's overloaded this week?" | Builder wrote `GET /api/reports/workload/{day}` + service + tests in a worktree → tests pass → diff approved → merged → restart → `--discover` (24 endpoints) → "Dev, 31 hours against 20" | 74.7 s |
| 5 Act | "Move Dev's two wheel builds to Priya, please." | Unlocked `assign`, both jobs reassigned in the 2009 UI | 11.1 s |
| 6 Compose | "Hand back job 4481 … make it a single step." | Synapse Custom composed `hand_back_finished_bike` from `get_job` + `notify_customer` + `set_job_status`; Barnaby used it: Tom texted, job ready | 49.3 s (Synapse 38 s) |

Run it yourself: `.venv/Scripts/python scripts/demo_check.py` (about 3 minutes; resets the demo world first).

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
 Worker agent (Claude Agent SDK) ◄── growth tools: capabilities · unlock · compose · build · connect
        │  every tool call ─► can_use_tool ─► tier policy ─► approvals (cards on the display)
        ▼
 Event bus (SSE) ─► display (live trace, approval cards with diffs, capability map) and the voice bridge
```

- **Synapse driver** ([`barnaby/synapse.py`](barnaby/synapse.py)) runs the pinned local CLI non-interactively, reads
  `.synapse/surface_cache.json` as the capability atlas, moves generated servers out of the target repo (so the repo
  stays clean and diffs never include generated files), and applies the fix-up pass.
- **Worker** ([`barnaby/worker.py`](barnaby/worker.py)) is the Claude Agent SDK, running on the local Claude Code login
  (or an API key). Each system's server attaches over stdio. After a growth step the servers are reconnected and the
  turn continues, so the new tool is used straight away.
- **Build** ([`barnaby/build.py`](barnaby/build.py)): a git worktree, a builder agent limited to that worktree, the
  system's own test suite, the diff on an approval card, a fast-forward merge, a deterministic restart, and
  `synapse build --discover`. The README in the repo (the departing developer's notes) outranks the spec.
- **Compose** (`build_custom` in `barnaby/synapse.py`): hosted Synapse Custom mode composes the repo's own internal
  functions into one tool. Barnaby also spots habits (the same chain of calls repeated) and offers to compose them.
- **Display** ([`ui/`](ui/)): conversation, live tool trace colour-coded by tier, approval cards with diffs, and the
  capability map. `?overlay=1` gives the compact HUD; `?mock` replays a recorded run.
- **Voice** ([`voice/`](voice/)): a separate Pipecat process. Without an LLM key, a small bridge acknowledges
  requests, narrates growth steps, and speaks Barnaby's replies; a spoken "yes" resolves write cards. The Claude Haiku
  front desk slots in when a key is present.

### Safety

| Action | Gate |
|---|---|
| Read-only tool call | none |
| Data write (POST/PUT/PATCH, composed skills) | a confirmation card (a spoken "yes" works too) |
| Unlock / Compose | one click |
| Build (writes code) | look at the diff and click. **Never by voice alone.** Worktree; tests must pass; revertable |
| Deny-list | endpoints that can never be exposed (e.g. `DELETE /api/jobs/{job_id}`) |

---

## Real vs staged

The app is real; the film and the walkthrough are staged recreations of it, like most product films.

| Thing | Status |
|---|---|
| Synapse discovery, MCP servers, Unlock rebuilds, `--discover` after Build | **Real** (every run) |
| Compose via hosted Synapse Custom mode | **Real** (needs a free `SYNAPSE_API_KEY`) |
| Barnaby's answers, tool calls, approvals, the Build diff and its tests | **Real** (`demo_check` runs them; the film's diff and figures come from a recorded run, [`video/data.js`](video/data.js)) |
| Spokes & Sprockets, Theo, Martin, Priya | **Fiction.** The shop is a purpose-built 2009-style app ([`systems/spokes-and-sprockets`](systems/spokes-and-sprockets)) with seeded data and backdated git history |
| The film | **Rendered from code** (HTML scenes → frames → ffmpeg); a staged recreation of the recorded run. Voices: Kokoro TTS, Martin voiced by Tani |
| The film's montage (Quorum, ComfyUI) | Endpoint counts are **real** Synapse scans (13 and 28); the questions on the cards are illustrative |
| Voice | **Real** (push-to-talk → sherpa ASR → Barnaby → Kokoro), verified by `scripts/smoke/voice_e2e.py`. The Haiku front desk is built for, and runs when an API key is present |
| Score | Composed in code, **played by real instrument plugins** (Ample Guitar M Lite II, MODO BASS 2, Valhalla VintageVerb) via DawDreamer |
| Not done yet | Bring-your-own-model worker (Pydantic AI; the interface is ready), the Tauri hotkey overlay (the compact display exists), a trained wake word |

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

```bash
source scripts/env.sh                         # (PowerShell: . scripts/env.ps1) keeps every cache inside the repo
npm ci                                        # Synapse CLI 0.1.9 as a local devDependency
uv sync                                       # core (.venv)
(cd runtime/mcp-servers && uv sync)           # mcp==1.30 for Synapse's generated servers
(cd runtime/legacy && uv sync)                # the 2009 shop app
cp .env.example .env                          # optional: SYNAPSE_API_KEY (Compose), ANTHROPIC_API_KEY (front desk)

python scripts/demo_reset.py                  # a fresh copy of the shop in .demo/, with Theo's git history
.venv/Scripts/python -m barnaby serve         # display + API on http://127.0.0.1:8700
```

Then type (or say) *"Barnaby, this is the shop's system."* The heavy thinking runs on your local Claude Code login
through the Claude Agent SDK, so no API key is needed for the core.

- **Text only:** `.venv/Scripts/python -m barnaby ask "Which repairs are due tomorrow?" --auto write`
- **Voice:** `(cd runtime/voice && uv sync)`, then `runtime/voice/.venv/Scripts/python voice/bot.py -t webrtc --port 7860`,
  and hold Space on the display. Listening defaults to a sherpa server (`SHERPA_WS_URL`); set `BARNABY_LISTEN=whisper` for local Whisper.
- **Any repo:** the display's *Connect a repo* form, or ask Barnaby with a repo path and the URL its API runs at.
- **Replay a recorded run** (no agent, no shop): `http://127.0.0.1:8700/?mock=1`.
- **The film:** see [`video/FRAMEWORK.md`](video/FRAMEWORK.md); `node render.js` in `video/`.

## Repo map

| Path | What |
|---|---|
| `barnaby/` | the core: Synapse driver, systems registry, worker, Build tier, policy, events, API server |
| `ui/` | the display (plain HTML/CSS/JS, SSE) |
| `voice/` | the voice layer (Pipecat bot, sherpa STT service, Kokoro voice, bridge) |
| `systems/spokes-and-sprockets/` | the demo world: Theo's 2009 back office (FastAPI, SQLite, Jinja, 19 tests) |
| `scripts/` | `demo_reset.py`, `demo_check.py`, smoke tests, dev helpers |
| `runtime/` | separate pinned runtimes: MCP servers, the legacy app, voice, audio |
| `video/` | the film: scenes, components, cue sheet, score, voice lines |
| `docs/` | [`WRITEUP.md`](docs/WRITEUP.md), [`MCP_SETUP.md`](docs/MCP_SETUP.md), the plan and the storyboard |
