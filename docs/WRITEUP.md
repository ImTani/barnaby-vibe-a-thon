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
   a test, following the departing developer's notes. You see the diff; nothing lands without your click.

The film's story is a handover: Theo wrote his uncle's bike-shop back office in 2009 and leaves on Friday. He
introduces Barnaby to the system, and the knowledge in Theo's code and README stays with the shop.

## Why Synapse fits

Synapse is the reason this is a product and not a consulting job. Each of Barnaby's tiers is a Synapse capability:

| Barnaby needs to… | Synapse provides |
|---|---|
| work with a repo he has never seen, with no integration code | `build --auto --local`: an MCP server straight from the code, in under a second, with no model call |
| know what the system *could* do beyond what he's been given | the surface cache: every endpoint discovered, with descriptions and payloads, before any is exposed |
| take a new ability in the middle of a conversation | `--endpoints` rebuilds in 0.3–0.5 s, so an unlock is instant |
| turn a repeated chain into one reliable step | Custom mode composes internal functions into a verified tool |
| use the endpoint he just wrote | `--discover` picks it up after the merge |

Without Synapse, each of those is a hand-written integration per system. With it, Barnaby is the same code for every
repo, and the per-system work is zero.

## What we built

- **The core** (`barnaby/`): the Synapse driver, a systems registry and process manager, the worker agent (Claude
  Agent SDK) with Barnaby's growth tools, a tiered approval policy, the Build tier, and an event stream.
- **The display** (`ui/`): the conversation, a live tool trace colour-coded by tier, approval cards with diffs, and a
  capability map of everything Synapse found.
- **The voice layer** (`voice/`): Pipecat over WebRTC, streaming speech recognition (sherpa on our own server, or
  local Whisper), and Barnaby's voice (Kokoro, a George/Fable blend, with misaki phonemes and question intonation).
- **The demo world** (`systems/spokes-and-sprockets/`): a purpose-built 2009-style back office with 23 endpoints,
  seeded data, 19 tests, a README full of Theo's notes, and git history going back to 2009.
- **Proof** (`scripts/demo_check.py`): the whole story, run against the real stack, checked against the shop's own
  API and git history. 15 of 15 checks pass.
- **The film** (`video/`): 160 s rendered from code, with a score composed in code and played by real instrument
  plugins.

## Results (one real run, 25 Nov)

| Beat | Time | Notes |
|---|---|---|
| Connect | 19.7 s | 23 endpoints discovered; Synapse itself took 0.5 s |
| Ask | 8.4 s | 6 tool calls; correct shortfall |
| Unlock + order | 9.3 s | rebuild 0.32 s |
| Build + answer | 74.7 s | endpoint, service and tests written in 56 s; the shop's 19 tests plus the builder's 4 pass; merged, restarted, rediscovered; exact answer (31 h vs 20) |
| Act | 11.1 s | unlocked `assign`; both jobs moved in the 2009 UI |
| Compose + use | 49.3 s | Synapse Custom 38 s; Tom texted, job marked ready |

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
- The voice front desk on Claude Haiku is built for but was not used in the film; the recorded voice lines are TTS
  (and one human).

## What's next

A trained wake word (our own Rust library), the hotkey overlay as a real always-on-top window, a live run of the
bring-your-own-model worker on an open model, and Barnaby proposing compositions on his own from habits (the detection is in; the
prompt to offer is in; it needs real-world tuning).
