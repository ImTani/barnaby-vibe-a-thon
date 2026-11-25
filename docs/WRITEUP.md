# Barnaby: write-up

## The problem

Most small businesses, and most departments in big ones, run on software nobody has time to rewrite. It was written
years ago by someone who has since moved on, or is about to. It works, but it's locked up:

- the only way in is a dated UI, one page at a time, across nine browser tabs;
- what it *could* do is buried in code nobody reads (often the API is there, and the UI never got a button for it);
- what it *can't* do (a report, a shortcut for something done twelve times a day) waits for a developer who isn't coming.

AI assistants don't help much here, because they can't touch the system. Someone has to write the integration first,
and in this setting that someone doesn't exist.

## The idea

**Point an agent at the repo, and the system gets a butler.** Barnaby is voice-first because the people who run these
systems are on the shop floor, not at a terminal. He starts with what's safe, and grows only with permission:

1. **Ask.** Synapse turns the repo's endpoints into MCP tools. Barnaby starts with the read-only ones and answers
   questions through them ("Which repairs are due tomorrow, and are we short on parts?").
2. **Unlock.** When nothing he has can do the job, he checks Synapse's map of the system. If an endpoint exists that
   would do it, he asks, then takes it ("There's an ordering endpoint I haven't taken. May I?").
3. **Compose.** When you keep asking for the same chain of steps, he fuses them into one skill, composed by Synapse
   from the system's own internal functions.
4. **Build.** When the system genuinely can't do it, he writes the missing endpoint himself, in a git worktree, with
   tests, following the departing developer's notes. Before it lands he tells you, in plain words, what it does,
   what it reads and what it changes, that the checks still pass and that it can be undone. The change itself is
   there for whoever wants to read it, and nothing lands without your click.

The person he works for runs the business, not the code, so every question and every card is in the household's words:
"Let Barnaby order parts from your suppliers", not `POST /api/purchase-orders`. The technical record is kept, folded
under each step and card, for whoever looks after the code.

The film's story is a handover: Theo wrote his uncle's bike-shop back office in 2009 and leaves on Friday. He
introduces Barnaby to the system, and the knowledge in Theo's code and README stays with the shop.

## Why Synapse fits

Synapse is the reason this is a product and not a consulting job. Each of Barnaby's tiers is a Synapse capability:

| Barnaby needs to… | Synapse provides |
|---|---|
| work with a repo he has never seen, with no integration code | `build --auto --local`: an MCP server straight from the code, in under a second, with no model call |
| know what the system *could* do beyond what he's been given | the surface cache: every endpoint discovered, with descriptions and payloads, before any is exposed |
| take a new ability in the middle of a conversation | `--endpoints` rebuilds in under a second (0.3–0.8 s in our runs), so an unlock is instant |
| turn a repeated chain into one reliable step | Custom mode composes internal functions into a verified tool |
| use the endpoint he just wrote | `--discover` picks it up after the merge |

Without Synapse, each of those is a hand-written integration per system. With it, Barnaby is the same code for every
repo, and the per-system work is zero.

## What we built

- **The core** (`barnaby/`): the Synapse driver, a systems registry and process manager, the worker agent with
  Barnaby's growth tools, a tiered approval policy, the Build tier, and an event stream. There are two workers: the
  Claude Agent SDK one (the default, on the local Claude Code login) and a bring-your-own-model one on Pydantic AI
  (`BARNABY_WORKER_BACKEND=byom`). Both share one prompt, one tier gate and one set of growth tools
  (`barnaby/toolkit.py`).
- **Plain-language approvals** (`barnaby/policy.py`, `barnaby/build.py`): every card leads with plain words; the
  endpoint, arguments and test line travel separately in the approval event's `technical` field. A Build is explained
  (does, reads, changes, checks, undo) before it can be approved. Writes take a click or a spoken "yes"; new keys,
  shortcuts and code changes take a click, never a spoken yes. Barnaby's prompt keeps "endpoint", "API", "tool",
  "server", "diff" and the rest out of what he says, and `demo_check` checks it.
- **The app** (`ui/`, round 3, approved and now the default): modelled on the Claude and Codex desktop apps. His work
  shows inline and collapsed as plain-words lines, with one live line (his mark at work, what he's doing, a timer)
  while he works. His words are set in an upright serif, brass is the one brand colour, and his mark is a counter bell
  wearing a bow tie. A side panel shows the keys you gave him and what he made with your say-so; "What he can do"
  lists every ability in plain words. The design is documented in `DESIGN.md` and `PRODUCT.md`; `?skin=classic`
  keeps the first, developer-facing display.
- **The voice layer** (`voice/`): Pipecat over WebRTC, streaming speech recognition (sherpa on our own server, or
  local Whisper), and Barnaby's voice (Kokoro, a George/Fable blend, with misaki phonemes and question intonation).
- **The demo world** (`systems/spokes-and-sprockets/`): a purpose-built 2009-style back office with 23 endpoints,
  29 made-up customers and their jobs, 19 tests, a README full of Theo's notes, and git history going back to 2009.
- **Proof** (`scripts/demo_check.py`): the whole story in the film's order, run against the real stack and checked
  against the shop's own API and git history, plus a check that nothing Barnaby said used the machine's words.
  16 of 16 checks pass. There are also 27 unit tests.
- **The film** (`video/v2/`, `video/v2/film/out/barnaby_v2_final_cast.mp4`, about five minutes), rendered from
  code and directed from a written shot plan (`video/v2/SHOTLIST.md`). It uses a procedural Blender diorama of the
  shop desk and a Lisbon desk (animated shots tied to the story's marks), screens designed as HTML and driven live,
  real people voicing Martin, Theo and Priya (recorded in DubMate, the film re-timed around their reads by Whisper
  word timings), and ElevenLabs v4 for Barnaby. The score is composed in code and played by real instrument plugins
  through DawDreamer; the sound effects come from Ableton's Core Library samples. An HTML film engine draws every
  frame as a pure function of time, and ffmpeg encodes them.

## Results (one real run, 25 Nov, 18:30 IST)

`demo_check`, in the film's order, every card approved automatically:

| Beat | Time | Notes |
|---|---|---|
| Connect | 25.3 s | 23 endpoints discovered; Synapse's two builds took 0.75 s and 0.65 s |
| Ask | 13.4 s | 7 tool calls; correct shortfall (Anika's brake job, one pair of pads short) |
| Unlock + order | 15.0 s | rebuild 0.76 s; ten pairs ordered from Madison |
| Four hand-backs + Compose | 78.3 s | texting and job status unlocked on the first (0.43 s, 0.41 s); Barnaby offered a single step after the repeats; Synapse Custom composed it in 27 s; Tom's bike handed back with it; all four customers texted and jobs marked ready |
| Build + answer | 95.6 s | endpoint, service and 4 tests written in 64 s; the shop's 19 tests plus the builder's 4 pass; explained, approved, merged, restarted, rediscovered; exact answer (Dev 31 h against 20) |
| Act | 14.8 s | unlocked `assign`; both wheel builds moved to Priya; Dev down to 19.5 h |
| Speech | | 26 lines said, none in the machine's words |

The Build answer is exact because of a rule we learned the hard way: early on, Barnaby added up the hours himself from
raw listings and got it subtly wrong (he counted finished jobs). Now totals are the system's job. If no report exists,
he builds one, and the departing developer's README outranks his own spec, so "workload" means what the shop means.

## What we learned about Synapse 0.1.9

We hit and confirmed a handful of issues, all worked around in the driver and disclosed in the README: untyped
optional parameters (`Any = None` everywhere), error bodies hidden by `raise_for_status`, writes to `~/.synapse` even
with telemetry off, `_2.py` files on rebuild, Custom mode scanning its own earlier outputs, and dropped query params,
router prefixes and `Literal` fields. Barnaby's fix-up pass keeps Synapse's original output beside the fixed one.

## Limits, honestly

- The Build tier writes code with Claude (Agent SDK). The rest of Barnaby runs on any model through the
  bring-your-own-model worker (Pydantic AI), which is unit-tested but hasn't yet been run against a live third-party
  model.
- Synapse sends no auth headers in local Auto mode, so systems behind auth need a proxy or a token-aware fix-up.
- Compose uses hosted Synapse (a free key); everything else runs locally.
- The voice front desk on Claude Haiku is built for but was not used in the film. In the film, Martin, Theo and
  Priya are voiced by real people (recorded in DubMate); Barnaby is ElevenLabs v4, credited on the end card.
- The film is a staged recreation of a real run. Its Lisbon scene (Quorum and ComfyUI) is staged, though the endpoint
  counts on screen (13 and 28) come from real Synapse scans. The shop, its people and its data are fictional, and no
  real brand logos are used.
- There's no way yet to take a key back from Barnaby in the app: once given, a key stays given (resetting the demo
  world clears them).

## What's next

A trained wake word (our own Rust library), the hotkey overlay as a real always-on-top window, a live run of the
bring-your-own-model worker on an open model, a way to take a key back, and tuning when Barnaby offers to compose
(today he offers once a chain of calls has repeated three times in a session).
