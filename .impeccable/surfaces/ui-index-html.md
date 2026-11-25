---
version: 1
slug: "ui-index-html"
primary_target: "ui/index.html"
related_targets: ["ui/app.js","ui/voice.js","ui/mock.js","ui/skins/app.css"]
---

# Surface: Barnaby's display (ui/)

Scope: the real working display (ui/index.html, app.js, voice.js, mock.js; the look in ui/skins/app.css as
`?skin=app`, ready to become the default). Mode: operate.
Audience: the owner (61, reading glasses) talking from a step back to a 2009-era PC at about 1440x900 in Chrome;
staff on the same machine; the developer on a modern machine at 1920x1080. Also a compact window (`?overlay=1`, ~560).
Job: talk (hold to talk or type), read the answer, know what Barnaby is doing without noise, say yes or no with full
understanding, see what he can do, connect a system. States: empty, ready, working, waiting, listening, error.
Product notes: video/v2/look/app2/PRODUCT-NOTES.md. Constraints: installed fonts only, plain HTML/CSS/JS, no build
step, app.js's event contract and the check harness selectors kept; old default and the two themed skins stay
reachable for comparison until the director approves.

## Direction contract

THESIS: Barnaby's display is a real professional app, played straight: a calm light workspace with a conversation, a
quiet activity inspector and decision cards a 61-year-old can trust. It refuses every costume (signs, tickets, livery)
and every AI tell (dark navy and brass, italic serif bot voice, bubbles left and right, status pills, a mono trace).

OWN-WORLD: White canvas, a neutral inspector (#F6F5F3) behind hairlines, near-black ink, one restrained brass accent
from the bell (his mark tile, the waiting state, focus, selection). Segoe UI (Variable on Windows 11) for everything;
Cascadia Mono / Consolas only for code. Rounded 8-14px controls, real buttons, inset grouped lists, one soft shadow
for the card that needs you.

STORY: The owner holds to talk or types, reads the latest answer large, glances at one status line and a plain-words
activity list, and answers a card that says what, why, what it reads and changes, that the checks pass and how to
undo; the change and the technical record are one disclosure away; every yes and no stays in the thread.

FIRST VIEWPORT: Toolbar 56px (bell tile + Barnaby, the system and how much he can use, status, "What he can do").
Centre: conversation column, 760px measure, author lines, current answer 22px, history 18px, the decision card under
it. Right: inspector 380-440px "What he did", the current request's steps at full size. Bottom of the centre column:
composer (Hold to talk 52px, input with Ask, "or hold the space bar").

FORM: The standing exit: the category standard played straight, at the craft level of the named products.
seed: none (pinned). The world, in the director's words: "Both look too much like gimmicks and not like real apps...
Barnaby is a real app... Think about this in product terms and then do the rework with impeccable", and the brief's
craft bar: "Linear, Things 3, Apple Messages and Mail on macOS, and the Claude desktop app. Calm, legible, precise,
familiar conventions, real typography and spacing, light by default." The first surface, in the brief's words: "Build
it as ?skin=app ... ready to become the new default", keeping "the conversation and activity (plain words first,
technical detail folded); approval cards (plain title; the Build card's what-it-does / reads / changes / checks /
undo; 'See the change' with the diff; technical detail); the capabilities view and the connect form; hold-to-talk and
its states; mock replay, overlay mode, the empty state; errors", with identity in "the bell mark, a restrained warm
accent, his voice in the copy, how approvals feel ... and a voice affordance that feels native".

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## History
Last round built two themed skins from an operate roll (seed a758c6367eb7924e): signpost (assigned) and ticket
(competitive). Both rejected as gimmicks; they stay reachable (`?skin=signpost`, `?skin=ticket`) as evidence only.

## Finish
Fresh finish review (a general-purpose agent following reference/degraded/finish-reviewer.md; the shipped reviewer
type was not available): disposition fix, 8 material fixes. One correction batch, then the verdict pass: 7 resolved,
#8 partial, 3 regressions, disposition fix (final for this unattended run). The four open items (decision footer flush
at the edge, overlay keeps its name, the count keeps its noun, the status wraps at phone width) were applied after the
verdict and verified by recapture and the check scripts, not re-reviewed. DESIGN.md and .impeccable/design.json
written for this look, marked pending.

## Current (round 3, approved)
The contract above is round 2's (`?skin=app`), kept as history. The director found round 2 too subdued ("No AI apps
look like this") and approved round 3, modelled on the Claude and Codex desktop apps (study:
video/v2/look/app3/REFERENCE-ANALYSIS.md): `ui/skins/app3.css` is now the default (index.html DEFAULT = 'app3');
`?skin=app` and `?skin=classic` stay reachable. DESIGN.md and .impeccable/design.json describe round 3. Checks:
video/v2/look/app/check.js (default = app3, plus classic) and video/v2/look/app3/check.js.
