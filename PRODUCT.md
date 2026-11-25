# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary: the person who runs the business, not a developer.** In the story that is **Martin Hartley**, 61, owner of
  Spokes & Sprockets (a family bike shop, est. 1987). Plain-spoken, kind, busy, impatient with computers, reading
  glasses on a cord. He asks out loud, between jobs, often from a step back from the screen, and he must be able to
  say yes or no to anything Barnaby wants to do without knowing what an endpoint, a server or a diff is.
- **Also: staff** on the same machine (Priya, a new mechanic on her first day), who ask quick questions about jobs.
- **Behind them, the real audience** (inferred from the brief and README): hackathon judges and viewers of the product
  film, and any small business whose system was written by someone who has since left.
- **Secondary: whoever looks after the code** (Theo, who wrote it, or the next developer). Not the person Barnaby
  speaks for, but someone he shows the whole truth to on request: what was found, what is open, every call, every
  change. His notes, code and checks are material Barnaby respects.
- **Barnaby shows each person the view that fits them** (director's brief, 25 Nov): Martin, the owner, gets the plan of
  the house and plain-words cards; the developer gets the full technical record; Priya's day-one view is still open
  (one proposal: her jobs as the repair tags on the bikes, plus a short list of things she can ask). One identity
  across all three.

## Product Purpose

Barnaby is a voice-first butler for a business's existing software. Point him at the repo; he answers questions about
the business through the system's own abilities, in the household's words. When the system can't yet do what was
asked, he grows it, always with the owner's say-so: he asks for a key to something the system can already do, joins
steps he keeps repeating into one, or writes the missing piece, explains it, and adds it only when told to.

Success: Martin keeps the shop running after Theo leaves, trusts Barnaby with the keys he hands over, and never has to
read code to stay in charge.

## Positioning

Barnaby has no abilities of his own except growth. Everything he does goes through the system the family already has
(made agent-ready by Synapse), so he can only ever do what that system can do, plus what the owner approves. Unlike a
chat assistant bolted onto a business, he looks after one household's own system, knows every room of it, and asks
before he goes anywhere new.

## Operating Context

- **Where:** the back office of a small shop, one desk, one PC. In the film it is a 2009 Windows 7 desktop with a
  19-inch 16:10 glossy LCD; Barnaby is the only new thing on it and must still feel part of the household. In real use
  it is a browser window (`ui/`), recorded live by the director at 1920×1080.
- **Light:** cool daylight and workshop strip lights in the morning; warm low sun into evening. Glossy screen, glare.
- **How:** voice first (hold-to-talk, or hold Space), typing as a fallback; approval by click, or a spoken "yes" for
  ordinary data changes. Code changes are approved by click only, never by voice alone.
- **Rhythm:** short spoken exchanges (one to three sentences from Barnaby), glanced at, not studied. Approvals are the
  rare moments that deserve full attention.
- **Neighbours on screen:** Theo's 2009 web system (Verdana, bevels, a blue banner with a yellow line), Windows 7
  chrome, desktop gadgets.

## Capabilities and Constraints

- **Tiers** (README): Ask (read-only abilities, no gate), Unlock (ask for a key to something the system already does;
  one click), Compose (join a repeated chain of steps into one; one click), Build (write the missing piece in an
  isolated copy, the system's own checks must pass, the owner reviews and approves; click only).
- **Data changes** (orders, reassigning, texting a customer) are confirmed on a card; a spoken "yes" works.
- **Some things stay shut for good** (a deny-list): e.g. cancelling a job, which has no undo.
- **The real system in the story** has 23 abilities found by Synapse, plus one Barnaby built (24): jobs, customers and
  texts, mechanics, parts and stock, orders to suppliers, invoices, reports. Six read-only ones are open from the start.
- **Technical detail is offered, never pushed:** the method and path of an ability, or the code of a change, sit behind
  a quiet control ("See the change") for whoever wants them.
- **A key, once given, stays given** in the app today: there is no way to take one back yet. Cards must not promise one.
- **The code-change card says exactly what the build tier knows:** what it does, what it reads, what it changes, the
  checks ("Theo's 19 checks still pass, and so do the 3 new ones": 22 in all), and that it can be undone.
- The display is plain HTML/CSS/JS with no build step, fed by server-sent events. Fonts must be ones already on the
  machine (no font downloads); the Windows 7-era faces (Segoe UI, Constantia, Corbel, Calibri, Cambria, Candara,
  Consolas) and the Office faces (Gill Sans MT, Franklin Gothic, Rockwell…) are present on the recording machine.

## Brand Commitments

- **Name:** Barnaby. Line: "Every system deserves a butler. …even the old ones."
- **Emblem:** the shop's brass service bell ("RING FOR SERVICE"). He is what answers it now.
- **Voice** (WORLD.md, binding):
  - the household's words, never the machine's: never "endpoint", "API", "tool", "MCP", "server", "deploy", "merge"
    or "diff" to Martin or Priya; he says what the system can do ("Theo built it a way to order from suppliers");
  - asks before he takes a new key; explains before he changes anything: what it does, what it touches and what it
    can't touch, and that Theo's checks still pass;
  - honest about limits ("I can't do that yet"); short, one to three spoken sentences; a dry aside now and then, never
    twice running;
  - Martin is "Martin", never "sir".
- **Character:** composed, warm, quietly witty, discreet. Unhurried, never slow.
- **Metaphor:** the system is a house. Synapse gives Barnaby the floor plan (every room the system has); Martin gives
  him the keys. Unlock = a key to an existing room; Compose = a service passage between rooms he keeps walking between;
  Build = a new room.
- **Not** a generic AI dashboard: no assistant clichés (glowing orbs, sparkles, gradients), and no developer trace on the
  owner's or staff's screen (it lives in the developer's view).
- **The display is a real professional app; identity in precise details, not a costume** (director, 25 Nov, choosing
  the standing exit after the themed skins read as gimmicks). Barnaby's display is the one part of the product that is
  actually the app, so it plays the category standard straight, at full fidelity: light by default, a workhorse UI
  face, familiar conventions, real typography and spacing. The craft bar is the products it should sit alongside:
  **Linear, Things 3, Apple Messages and Mail on macOS, and the Claude desktop app.** Barnaby lives in the details: the
  bell mark, one restrained warm accent, his voice in the copy, approvals that feel trustworthy, a native voice
  control. No themed worlds (signs, tickets, liveries) on the working display.

## Evidence on Hand

- A real recorded run: `video/data.js` (abilities, the calls Barnaby made, what he said, the real code change and its
  check result "22 passed"). `ui/fixtures/demo-run.json` replays it on the display (`?mock=1`).
- `scripts/demo_check.py` drives the whole story against the real stack: 15/15 pass.
- Theo's system and its 19 tests: `systems/spokes-and-sprockets/`. Barnaby's report added 3 tests (22 in total).
- **Fiction, labelled as such:** Spokes & Sprockets, the Hartleys, Priya, the customers. The film is a staged
  recreation of the real run. Do not invent other customers, figures, test results or abilities.

## Product Principles

1. **Plain words first, detail on request.** Every screen reads to Martin in his own words; the technical truth is one
   quiet click away and never in the way.
2. **Consent is visible.** A new key, a data change or a new piece of the system is asked for in a sentence a
   61-year-old can say yes or no to, with what it can and can't touch.
3. **Show where he has been.** Barnaby's work is shown as what a person would say they did ("looked at tomorrow's
   jobs"), so Martin can always see which rooms he went into.
4. **Belong to the household.** He is new, but he should feel like he has always been part of the shop: its objects,
   its manners, its people.
5. **Calm over clever.** Legible, unhurried, fast to scan. Nothing flashes for attention except a question that needs
   an answer.

## Accessibility & Inclusion

- The primary user is 61 and reads with glasses: generous type (body never below 18px at 1080p), strong contrast
  (WCAG AA at minimum, AAA for body and Barnaby's words), large targets.
- Voice and click are equivalent for everything except code changes (click only, by design).
- State is never colour alone (icon plus words: lit, key, shut).
- Honour reduced motion.
