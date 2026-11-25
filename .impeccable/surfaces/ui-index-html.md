---
version: 1
slug: "ui-index-html"
primary_target: "ui/index.html"
related_targets: ["ui/style.css","ui/app.js","ui/skins/signpost.css","ui/skins/ticket.css"]
---

# Surface: Barnaby's display (ui/), skins

Scope: the real working display (ui/index.html, style.css, app.js, voice.js, mock.js). Mode: operate.
Audience: Martin (61, shop owner) reading from a step back, voice first; Priya; the developer on request.
Job: ask out loud, read the answer, see where Barnaby went in plain words, say yes or no to a key, a passage or a
new room. Constraints: installed fonts only (no downloads), plain HTML/CSS/JS, no build step, app.js's contract
kept for every skin, the default look unchanged until the director picks (skins via ?skin=<name>).
Built as skins: signpost (assigned direction) and ticket (competitive challenger, fused). Decision page:
video/v2/look/app/index.html; frames in video/v2/look/app/frames/ (capture.js), behaviour check in check.js.

## Direction contract

THESIS: Barnaby is signed like a cycle route: legends you can read from a step back, the route he took posted as a
sign, and anything that needs Martin's say-so on a yellow temporary panel. It refuses the dark chat-plus-developer
trace (bubbles left and right, italic serif, a status pill, a monospace log).

OWN-WORLD: White ground, black legends in Corbel, sentence case, Kinneir's two weights (heavier black on white,
lighter white on blue). Route blue for the bell tile and the route sign; works yellow with a black inset border for
say-so panels; red only for the prohibition ring (kept shut) and a real shortfall. Panels carry a rounded inset
border; pictogram tiles (bell, key, tick, ring, passage, new room) in one stroke.

STORY: Martin asks; reads the answer large; sees each stop Barnaby made in plain words with the technical detail
folded under it; says yes or no on the yellow panel, which says what it does, what it reads and changes, the checks
and the undo; his decisions stay listed in the conversation.

FIRST VIEWPORT: 1920x1080. Header 88px white over a 6px route-blue rule: bell tile and "Barnaby", the status as a
sentence, the system line ("the shop's back office, 9 of 24 things he can do"), the "What he can do" button. Left,
white: earlier exchanges compact, the current question 28px, the answer 40px, the yellow panel under it. Right,
560px route-blue sign "Where he went": this request's stops at 26px, earlier requests folded. Footer: Hold to talk
(blue, mic, 340px), input, Ask.

FORM: Signpost, candidate 3 of my 7 (British cycle-route and road signage, Kinneir & Calvert); seed:a758c6367eb7924e.
Raises: hierarchy by scale alone (from the type specimen); every gap a whole multiple of a 6px tile (from
the bitmap specimen); every exchange numbered and timed, the drawer is the index (from the Factory catalogue); a
full printed-mark state vocabulary, never colour alone (from the centre-rail setting).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Challenger built alongside: ticket
Fused from the jet-age ticket wallet with the shop's own numbered repair-ticket book: each exchange a numbered,
timed ticket on white coupon stock in carrier-navy ink; the work done as the canary carbon copy in carbon purple;
the say-so as a coupon with a perforated tear line; decisions stamped and kept ("nothing disappears, it cancels").

## Open
The director picks a skin (or neither) before DESIGN.md is rewritten and before the default changes.
