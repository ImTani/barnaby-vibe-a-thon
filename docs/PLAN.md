# Barnaby — build plan (working name)

> **Every system deserves a butler.** *(film kicker: "…even the old ones.")*
> Product name is parked; "Barnaby" is the butler's name and the working product name.

Status: **v0.4 — 2026-11-25 ~05:00 IST.** Phases 0–1 done; Phase 2 (core) working end to end for Connect, Ask and Unlock. Build is being tested.

### Progress log
- **Phase 0 ✅** Repo-local env; Synapse pinned locally; smoke tests pass. Details in §7.
- **Phase 1 ✅** `systems/spokes-and-sprockets`: Theo's 2009 back office.
  - FastAPI + SQLite + Jinja; 23 JSON endpoints; 19 pytest tests.
  - The UI auto-refreshes, so Barnaby's changes visibly land.
  - `scripts/demo_reset.py` copies it to `.demo/` as its own git repo, with Theo's backdated history (2009 → last week), and seeds "today" as this week's Monday.
- **Phase 2 (core)** `barnaby/` package:
  - **Synapse driver:** home redirect; output moved out of the target repo; fix-up pass (error bodies, types and required params).
  - **Systems registry and process manager.**
  - **Approval tiers.**
  - **Worker:** Agent SDK on the local Claude Code login; growth tools `capabilities` / `unlock` / `build` run in-process; servers reconnect after growth.
  - **Build tier:** git worktree, builder agent, re-run tests, diff approval, fast-forward merge, `--discover`.
  - **API + SSE server and a CLI.**
  - Verified for real:
    - **Connect:** 23 endpoints discovered, 6 reads exposed, ~1 s of Synapse.
    - **Ask** ("due tomorrow, short on parts?"): 6 tool calls, correct, 7.8 s.
    - **Unlock** ("order the brake pads"): capabilities → unlock `POST /api/purchase-orders` → rebuild 0.38 s → reconnect → order placed through the write gate, ~8 s.
    - **Build** ("who's overloaded?"): Barnaby builds rather than adding up by hand → builder writes service + route + tests in a worktree (~57 s, Opus) → tests pass → merge → deterministic restart → `--discover` → new tool used → correct answer, ~85 s.
    - **`scripts/demo_check.py`: 10/10 PASS** (Arrival · Ask · Unlock · Build · Act), whole run ≈ 2.5 min.
  - Fixed along the way:
    - uvicorn `--reload` hangs on Windows, so Barnaby restarts systems himself.
    - The worker now reads the repo README ("notes") before speccing a build, and the builder's README definitions outrank the spec.
- **Display (P0 started)** `ui/`: conversation, live trace (tiers colour-coded), approval cards with a diff viewer, capability map, and connect-a-repo form.
  - **Mock mode replays a real recorded run** (`ui/fixtures/demo-run.json`, exported from `events.jsonl`).
- **Voice (P0 started)**: `runtime/voice` (Pipecat).
  - No-key path: listening → worker → Barnaby's own "say" events spoken by Kokoro; spoken "yes" for write-tier cards.
  - The Haiku front desk slots in when the key arrives.

---

## 1. What we're submitting

**Track 4: Open innovation.** We use Synapse Auto *and* Custom mode, which only Track 4 allows.

| Guide asks for | Our answer |
|---|---|
| The repo | This repo |
| Your MCP setup | Synapse-generated servers per system plus `docs/MCP_SETUP.md` |
| A short write-up of the problem and why Synapse fits | `docs/WRITEUP.md` |
| A demo of the agent solving it end to end | A cinematic film (rendered from code) and a real walkthrough (recorded by Tani, edited) |

**Judged on:** originality and real-world value · how central Synapse is · technical execution · quality of the demo.

**Demo principle (as with Quorum):** the app must genuinely work as advertised. The film and walkthrough may be staged, scripted and edited. A "real vs mocked" table in the README discloses what's staged, and a `demo_check` script proves the real path end to end.
**Deadline:** 25 Nov, end of day (assumed IST; confirm). Judging 30 Nov.

**Differentiation.** From a survey of 20 public submissions, nobody has:
- voice input;
- live bring-your-own-repo;
- an agent that **writes its own missing endpoint**.

Synaptogenesis already does unlock and compose. We do them *better*, not quieter. See §6.

---

## 2. The story: one family

**Spokes & Sprockets** — *A Hartley family workshop · est. 1987*

| Persona | Character (names are proposals) | Need |
|---|---|---|
| Departing expert | **Theo Hartley**, the nephew. Wrote the back office in 2009 as a teenager; leaves for a job abroad on Friday | His knowledge lives in the code and a README nobody reads |
| Overloaded ops person | **Martin Hartley**, the owner. Nine tabs, greasy hands, phone ringing | Can't type mid-repair; can't drive the 2009 interface |
| Developer, day one | **Priya**, the new hire. Starts Monday as mechanic and does the shop's IT | Has to operate a system she's never seen |

The 2009 back office covers customers, bikes, repair jobs (with estimated hours and due dates), parts and stock, purchase orders, mechanics and their capacity, and invoices. It looks the part: Verdana tables and bevelled buttons.

### Demo beats (the film and the walkthrough share them)
1. **Arrival.** Theo's last week. Nobody else understands the back office he wrote in 2009, so his handover is a butler. He points Barnaby at the repo.
   - *"Barnaby, this is the shop's system. Look after them for me."*
   - Synapse scans the repo live and the endpoints appear in the display.
   - `--smart-names` reads Theo's README, so his notes become Barnaby's understanding of the system.
   - *"Twenty-three endpoints, sir. I've started with the six that only read. Your README was most illuminating."*
2. **Meet Martin.** The next Monday: Martin has nine tabs open and greasy hands. He presses the hotkey and Barnaby's display slides in over the 2009 panel.
   - *"Which repairs are due tomorrow, and are we short on parts for any?"*
   - The trace shows the calls, then the spoken answer.
3. **Unlock.**
   - *"Order the brake pads."*
   - *"I can't yet, but the system can: there's a purchase-order endpoint I haven't taken. May I?"*
   - One click, Synapse rebuilds, the tool appears, then a confirmation card for the order itself.
4. **Compose.**
   - *"You've had me do 'bike ready → fetch customer → notify → close job' four times today. Shall I make it a single motion?"*
   - `synapse build --custom` fuses the steps, a replay test verifies the result, and Martin names the skill by voice.
5. **Build (the centrepiece).**
   - *"Who's overloaded this week?"*
   - *"The system has no notion of workload. I can teach it."*
   - Barnaby writes `GET /mechanics/workload` and a test in a git worktree. The display shows the diff; Martin clicks approve.
   - Tests pass, the service reloads, `synapse build --discover` runs.
   - *"Dev has 31 hours booked against 20."* → *"Shall I move the two wheel builds to Priya?"* → approve → the **2009 interface visibly updates**.
   - Rehearsal fallback: "Who hasn't been in for a service in over a year?"
6. **Priya, day one.** *"What can this system actually do?"* Barnaby gives her the tour from Theo's notes and his own tool map, including the skill and the endpoint he grew last week.
7. **Montage, "any repo":**
   - Quorum, our last hackathon project ("Any disputed deadlines?");
   - a well-known open-source app ⏳;
   - Theo's handover;
   - Priya on day one;
   - "…your company's application estate."
8. **Close.** *"Every system deserves a butler. Even the old ones."*

---

## 3. Architecture

```
 Listening layer (pluggable)  sherpa streaming (Tani's server) · faster-whisper (local GPU) · Groq Whisper (free)
 Voice layer (pluggable)      Kokoro · Qwen3-TTS   (film: Tani voice-acts)
 Invocation                   hotkey push-to-talk · wake word "hey Barnaby" (no-training keyword spotting; Rust lib later)
 Front desk                   Claude Haiku 5.5: persona, narrates worker progress, handles approvals
 ───────────────────────────── core = the submission (works text-only) ─────────────────────────────
 Systems registry → Synapse driver → MCP manager → worker agent (Opus 5.5) → growth engine → approvals → event stream → display
```

| Component | Pre-built choice | Notes |
|---|---|---|
| Core API and event stream | FastAPI + SSE (`sse-starlette`) | |
| Worker agent loop (heavy thinking) | **Claude Agent SDK on Tani's local Claude Code login** (P0) | Speed isn't critical here; the demo just needs the results. Synapse's servers attach through the SDK's `mcp_servers` (stdio); approvals go through `can_use_tool` → our tier policy; SDK messages feed the event stream. Uses `ANTHROPIC_API_KEY` instead when one is set (e.g. for recording timings) |
| Bring-your-own-model backend | **Pydantic AI** `Agent` + `MCPToolset` + deferred-tool approvals (P1) | Same worker interface; one string switches provider (OpenAI, Gemini, Groq, OpenRouter, Bedrock, Vertex, local Ollama). ⚠ Smoke-test its FastMCP 4 client against Synapse's mcp 1.30 servers |
| MCP servers | Synapse-generated `synapse_auto_server.py` per system | Run in their **own venv pinned to `mcp==1.30`** |
| Synapse | `npx @2ndbrainlabs-ai/synapse-cli@0.1.9`, nothing global | `build --auto --local --endpoints …`, `--discover`, `--custom --local -q …` |
| Front desk | **Claude API**, `claude-haiku-5-5` (the only latency-critical piece; also used when recording) | Built for the key in `.env`; until it's there, the front desk falls back to text mode |
| Voice pipeline | **Pipecat** (`pipecat-ai` 1.17, Python ≥3.11) + **SmallWebRTCTransport** (peer-to-peer browser audio, no media server) | Barge-in built in. Worker → speech: the hand-off is an **async tool** (`cancel_on_interruption=False`); the worker streams progress through `result_callback(..., FunctionCallResultProperties(is_final=False, run_llm=True))`, or `LLMMessagesAppendFrame(run_llm=True)`, which is held while Barnaby speaks and owed while the user speaks. Approval phrases are an `approve_pending` LLM tool. Our display uses Pipecat's JS/React client SDK (verify) |
| Front desk LLM | Pipecat `AnthropicLLMService`, set explicitly to `claude-haiku-5-5` (Pipecat defaults to sonnet-4-6) | No temperature/top_p (400 on Haiku 5.5). Pipecat also ships OpenAI, Google, Groq and Ollama services, so the front desk is swappable too |
| Listening adapters | (1) **custom sherpa `STTService`** (~100 lines; the only hand-rolled voice piece, as no integration exists): float32 PCM frames over websocket, JSON partials with `is_final`; (2) `WhisperSTTService` (faster-whisper, CUDA); (3) `GroqSTTService` | Whisper and Groq transcribe per utterance (no partials); sherpa gives live partials. Skip server hotwords (whole-server, needs restart, no `bpe.vocab`) |
| Voice adapters | (1) **`KokoroTTSService`** (`kokoro-onnx`, CPU, `Language.EN_GB`, voice **`bm_george`** or `bm_fable`); (2) **Qwen3-TTS** via `faster-qwen3-tts` (true streaming, ~0.4 s to first audio on a 4060) behind Pipecat's `OpenAITTSService(base_url=…)` | Qwen has no British male preset: design the butler voice with VoiceDesign, then clone with the 0.6B Base model. Couldn't find a "Qwen3.5 TTS"; newest found is Qwen3-TTS |
| Wake word | With sherpa listening: Pipecat **`WakePhraseUserTurnStartStrategy`** (config only; add mishearings such as "hey barney"). With Whisper/Groq: a **sherpa-onnx keyword-spotting gate** (`KeywordSpotter`, `kws-zipformer-gigaspeech-3.3M`, keywords file built with `sherpa-onnx-cli text2token`, ~40 lines) | No training. Tani's Rust library later for a trained word |
| GPU budget (6 GB) | Qwen3-TTS 0.6B (~2.7 GB) **or** faster-whisper large-v3 (~3–4.5 GB), not both | Default demo pairing: **sherpa (server) + Qwen3-TTS (GPU)**, or **Whisper (GPU) + Kokoro (CPU)** |
| Build tier code writing | **Claude Agent SDK** (`claude-agent-sdk` 0.2.188) in a **git worktree** | The Windows wheel bundles `claude.exe`, so a venv install is enough and nothing is global. Options: `tools=[Read,Glob,Grep,Edit,Write,Bash]`, `permission_mode="dontAsk"`, path-scoped `allowed_tools` (`Edit(/**)`, `Bash(python -m pytest*)`), a `PreToolUse` audit hook, `max_budget_usd`, effort set explicitly. **`setting_sources=[]` and a repo-local `CLAUDE_CONFIG_DIR`**, so your `~/.claude` plugins and settings never leak in. Claude-only; the rest of the app is provider-agnostic |
| Git | GitPython via `repo.git.worktree/diff/merge` (short-lived `Repo` per operation) | `git add -A` then `git diff --cached HEAD`, so new files show up |
| Diff view | **diff2html** (takes the raw unified diff; side-by-side; dark theme) | |
| Display (web) | React + Vite + Motion ⏳ | Design: the butler's display |
| Overlay | **Tauri v2** (2.12.x): transparent, frameless, always-on-top, skip-taskbar window on our localhost UI; `tauri-plugin-global-shortcut`; `on_permission_request` allows the mic | MSVC (VS 2022 Community) and WebView2 are already installed, so nothing new globally; CLI as a local devDependency. Fallback: Chrome `--app` + AutoHotkey |
| Process supervision | stdlib `subprocess` + **psutil** (kills whole process trees) | Legacy apps run with `uvicorn --reload` so merged code reloads. **Barnaby's own core must NOT use `--reload` on Windows** (selector loop can't spawn subprocesses: MCP servers and the Agent SDK) |
| Film | Reuse Quorum's render-from-code pipeline (`video/`) | |

**Who thinks where.**
- **Heavy thinking and code writing:** Tani's **local Claude Code** (Agent SDK), at no extra cost.
- **Latency-critical front desk:** the **Claude API** (startup credits), also used when recording timings.
- **Bring your own model:** others can run the worker on any provider through the Pydantic AI backend (P1).
- **Claude-only:** the Build tier's code writer.
- **Agent SDK hygiene:** it runs with `setting_sources=[]`, so your `~/.claude` settings, plugins and hooks don't load. It does use your login, so session transcripts land in `~/.claude/projects` as with any Claude Code session.

**Keys and config.** One fresh Claude API key (startup credits) in a repo-local, gitignored `.env`. The OpenAI key in the environment is not used. Every venv, `node_modules`, model cache and `.synapse/` config stays inside this folder: delete the folder and nothing remains.

---

## 4. Safety: tiered approvals

| Action | Gate |
|---|---|
| Read-only tool call | None |
| Data write (POST/PUT/PATCH/DELETE) | Spoken "yes" **and** a visible confirmation card |
| Unlock (expose a discovered endpoint) / Compose (fuse a skill) | One click |
| Build (write code) | Look at the diff and click. **Never by voice alone.** Runs in a git worktree; tests must pass; the change can be reverted |
| Policy deny-list | Endpoints that can never be exposed |

---

## 5. Known Synapse 0.1.9 pitfalls → mitigation

Source: another team's notes ([Synaptogenesis README](https://github.com/Baqir376/Vibe-a-thon)). Verify each in the smoke test.

| Pitfall | Mitigation |
|---|---|
| Local Auto mode drops query parameters | Design legacy endpoints with path params or JSON bodies; or patch generated servers after the build (P1, disclosed) |
| `--local --auto` asks for a model key even though it calls no model | Set `SYNAPSE_LLM_PROVIDER` / the key env for the run |
| Repeated local builds write `_2.py`, `_3.py`… | Driver renames or cleans output after every build |
| Generated servers need `mcp==1.30` | Separate pinned venv |
| `raise_for_status` hides API error bodies from the agent | Patch generated servers after the build (P1), or return 200 with error JSON from our own legacy app |
| Body fields typed `Literal` or with a trailing `# comment` are dropped | Plain `str` fields; comments on their own line |
| Custom mode scans its own earlier outputs | Park outputs before each Custom build |
| Custom code generation invents keys when return shapes are undocumented | Docstrings that document every returned dict |
| Hosted Express/TypeScript is broken | Only matters for non-Python montage repos |
| **Router/blueprint prefixes are dropped**: tool URL = `ENDPOINT_BASE_URL` + the decorator's path (confirmed in source) | Our apps declare **full paths in every decorator** (no `prefix=`); the Build tier must follow the same rule |
| `@router.get("")` (empty path) is skipped | Never use empty paths |
| **No auth headers are ever sent** (`headers_hint: []`) | Our legacy app has no auth (local, single shop); disclosed. Auth-gated open-source apps can't be the montage app |
| **POST bodies only work if the Pydantic model is defined in the same file as the route** | Keep each router's models in its own file; the Build tier writes models beside routes |
| Flask `<int:id>` path params are pasted literally | FastAPI `{id}` style only |
| Language = most source files among languages with a root marker file | Keep JS/TS assets out of scanned dirs, or keep Python dominant |
| Route keyword must appear in a file's **first 64 KB**; files over 2 MB skipped | Small route files |
| **Confirmed:** writes `~/.synapse/.version-check.json` and `telemetry-salt` even with `SYNAPSE_TELEMETRY=0` | The driver runs Synapse with `USERPROFILE`/`HOME` set to `.cache/synapse-home`. Verified: nothing lands in the user profile |
| **New:** every tool parameter is typed `Any = None`, so nothing is required and there are no types | Fix-up step adds types and required flags from the FastAPI signature; tool descriptions state units and formats |

---

## 6. Beating the competition on Unlock and Compose
- **Any repo, unseen.** No pre-built company of services.
- **Barnaby explains why** it picked an endpoint, out loud.
- **Barnaby proposes compositions himself.** You name the new skill by voice.
- **Live before/after counter.** Turns, tokens and seconds saved by each composition.
- **Fix-up step** over generated servers (query params, error bodies). It's a measurable reliability win, disclosed in the README.

---

## 7. Schedule (25 Nov, IST; adjust for sleep)

| Window | Phase | Done when |
|---|---|---|
| 02:00–03:00 | **0. Scaffold + smoke tests** | Repo-local envs; Synapse via npx on a 2-endpoint FastAPI app; pitfalls confirmed; keyword spotter checked |
| 03:00–05:00 | **1. Spokes & Sprockets** | FastAPI + SQLite + 2009 interface + seed data tuned for the demo + pytest |
| 05:00–09:00 | **2. Core** | Synapse driver, MCP manager, worker agent, event stream, approvals, **Unlock**; text chat works end to end |
| 09:00–12:00 | **3. Display + voice** | Barnaby's display; listening/voice layers; front desk; hotkey; wake word |
| 12:00–15:00 | **4. Build + Compose** | Centrepiece Build beat works 5/5 rehearsals; Compose works |
| 15:00–16:30 | **5. Montage + overlay** | Quorum, ComfyUI; overlay window |
| 16:30–20:00 | **6. Film + docs** | Film rendered; README with a "For judges" table; WRITEUP; MCP_SETUP; real-vs-mocked; tests green; Tani records the walkthrough |
| 20:00–23:00 | **7. Edit + buffer + submit** | Walkthrough edited; submitted |

### Priorities (cut from the bottom)
- **P0:** Spokes & Sprockets · connect any repo · worker + Unlock · Build centrepiece · display · voice (push-to-talk) · README/write-up
- **P1:** Compose · wake word · Quorum scene · film · fix-up step
- **P2:** overlay · open-source app scene · Rust wake word

---

### Montage: well-known open-source app
**ComfyUI** (148k stars):
- aiohttp `@routes.get("/system_stats")` style with full paths; no auth; pure Python.
- Shot: *"What GPU is ComfyUI using, how much VRAM is free, and is anything queued?"* → `GET /system_stats` + `GET /queue`.
- Build with `--endpoints` to keep it to about 4 tools (`/system_stats`, `/queue`, `/models`, `/history`); avoid `/object_info`, which is huge.
- Install about 1–2 GB, repo-local.

Fallbacks:
- **Open WebUI** (most recognisable; only `/api/version` and `/api/changelog` work without a token);
- **dvf/blockchain** (the famous Flask tutorial; zero risk, but a toy).

### Phase 0 results (25 Nov, 03:00–03:40 IST) ✅
**Environment:**
- `scripts/env.ps1` / `env.sh` override the machine-wide `X:\Caches\*` exports, so every cache stays repo-local.
- Synapse 0.1.9 is a local devDependency.
- `.venv` (core): claude-agent-sdk 0.2.188, pydantic-ai-slim 2.73, fastmcp-slim 4.2.5, mcp 2.3.
- `runtime/mcp-servers/.venv`: mcp 1.30.0.

**Synapse** (`sandbox/smoke_app`, every route probes one pitfall):
- **Confirmed:** query param dropped (422); `Literal` field dropped; router prefix dropped (404); `raise_for_status` hides the 409 reason; `_2.py` written on rebuild; `~/.synapse` written. Fixed by the HOME redirect.
- **Not reproduced:** a trailing-comment field survived.
- **New:** every parameter is `Any`, and none is required.
- `--local --auto` with `SYNAPSE_LLM_PROVIDER=ollama` needs no key and calls no model.
- Generated code uses Python 3.12 f-string syntax, so the runtime must be 3.12+.

**Checks:**
- `scripts/smoke/smoke_mcp.py`: the FastMCP 4 client (what Pydantic AI wraps) drives the mcp 1.30 server fine; connects in ~1.2 s. **PASS.**
- `scripts/smoke/smoke_agent_sdk.py`: **the P0 worker path works on the local Claude Code login with no API key.** The Agent SDK attached the generated server, called `list_items`, our `can_use_tool` hook allowed the read and **denied** `create_order`, and the agent reported the denial correctly. 3 turns, 8 s wall time on Haiku. **PASS.**
- `scripts/smoke/smoke_sherpa.py`: the server is reachable from the laptop in 175 ms; JSON partials (`text`, `is_final`, `segment`…) then `Done!`. **PASS.**

**Deferred to Phase 3:** Pipecat hello-world, keyword spotting.

### Demo production (learned from Quorum, `ImTani/quorum-edge-memory`)
**Real demo kit:**
- `scripts/demo.ps1`: reset to seed, start everything hidden, `-Stop`.
- `scripts/demo_check.py`: drives every beat over HTTP; one PASS/FAIL line with timing per step; `--until N` for rehearsals.
- `?mock=1` UI mode: a scripted in-browser fake backend, keys 1–8 play the beats. We build the display against it before the backend exists.

**Film: rendered from code** (Quorum `video/v4/`):
- A page with a pure `render(t)` per scene.
- `vclock.js` virtualises time; `puppeteer-core` (local, uses the installed Chrome) screenshots every frame; ffmpeg encodes.
- "Real UI" shots are a copy of the app (`mockstage/`) driven by a scripted fake backend with injected clicks and keys. The real app is never edited for the film.
- **Reuse as-is:** `vclock.js`, `render.js`, `main.js`, the generic parts of `lib.js`, `scenes/_TEMPLATE.js`, `FRAMEWORK.md`, the DSP/`fx_*` helpers in `audio/compose.py`.
- **Rewrite:** the whiteboard look, the stage selectors, and the music and sound-effect timeline.
- **Unlike Quorum,** Barnaby talks: voice lines are generated locally (Kokoro / Qwen3-TTS), or Tani voice-acts.

**Process:**
- Freeze `STORYBOARD.md` and `cues.json` first.
- Then parallel agents write one scene file each against `FRAMEWORK.md`, and the audio is composed against the same cues.
- Fixed "mocked demo numbers" are used everywhere.
- Disclosure: a small on-screen tag plus a real-vs-mocked table.

**Fallback if short on time:** Quorum's simpler v3 film (crossfading scenes, ~2 h of work).

**Sound (decided after storyboard review, 25 Nov):**
- **Music** is composed in code (Quorum's approach), but **played by Tani's own plugins** through DawDreamer, an offline VST2/VST3 host.
  - Verified rendering headlessly: Ample Guitar M Lite II, MODO BASS 2, Valhalla VintageVerb, FabFilter Pro-L 2.
  - Ample needs about 8 s of real time to load its samples.
  - SSD5 drums would need a saved kit preset.
  - No synths, so no "tell". Runtime: `runtime/audio`; probe: `video/audio/vst_probe.py`.
- **Barnaby** is always TTS: Kokoro `bm_george`, fed the way Kokoro v1.0 was trained (`voice/tts.py`).
  - Input: misaki G2P phonemes (British), one sentence at a time, with natural pauses. Stock espeak phonemisation made him sound flat.
  - The live bot uses the same pipeline (`voice/barnaby_tts.py`).
- **Cast:**
  - **Martin Hartley** (the owner, renamed from June) is voiced by Tani; placeholder `bm_fable`.
  - Theo (`bm_lewis`) and Priya (`bf_isabella`) keep generated voices unless friends record them.
- **Compose** stays in the film. Making it real needs a free Synapse console key (hosted Custom mode) or the Claude API key (`--local`). Claude Code's login can't act as Synapse's model provider.
- clipd is out of the montage.

## 8. Open questions
- Product name (parked); character names (proposals above).
- "Qwen3.5 TTS": couldn't find it; newest found is Qwen3-TTS (Jan 2026).
- Synapse console key (free tier): Compose via hosted Custom mode, and `--smart-names`.
- Exact submission cutoff and timezone.
