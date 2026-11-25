---
name: Barnaby · Livery
description: Barnaby wears the shop's colours. Hartley green, lined in gold like a good frame; plain words first, the technical truth one quiet click away.
colors:
  hartley-green: "#17402F"
  green-unlit: "#215443"
  green-deep: "#0F2D20"
  lining-gold: "#C9A04A"
  lining-gold-on-white: "#977629"
  white-enamel: "#F7F7F3"
  white: "#FFFFFF"
  frame-black: "#141414"
  ink-2: "#3F4A44"
  ink-3: "#5F6A64"
  mist: "#E3EAE5"
  rule: "#CBD5CE"
  on-green: "#FFFFFF"
  on-green-2: "#CFDDD4"
  on-green-3: "#A9BFB2"
  enamel-red: "#A3261B"
  red-tint: "#F7E6E2"
  added: "#E3EEE6"
  tag-manila: "#E7D8B3"
  tag-ink: "#2B2416"
  sticky-note: "#F4EAA0"
typography:
  wordmark:
    fontFamily: "Perpetua Titling MT, Gill Sans MT, serif"
    fontSize: "30px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.16em"
  room-name:
    fontFamily: "Perpetua Titling MT, Gill Sans MT, serif"
    fontSize: "23px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.07em"
  his-words:
    fontFamily: "Liv Figures, Gill Sans MT, Calibri, sans-serif"
    fontSize: "38px"
    fontWeight: 400
    lineHeight: 1.24
  card-title:
    fontFamily: "Liv Figures, Gill Sans MT, Calibri, sans-serif"
    fontSize: "40px"
    fontWeight: 700
    lineHeight: 1.15
  heading:
    fontFamily: "Liv Figures, Gill Sans MT, Calibri, sans-serif"
    fontSize: "30px"
    fontWeight: 700
    lineHeight: 1.2
  question:
    fontFamily: "Liv Figures, Gill Sans MT, Calibri, sans-serif"
    fontSize: "27px"
    fontWeight: 400
    lineHeight: 1.35
  body:
    fontFamily: "Liv Figures, Gill Sans MT, Calibri, sans-serif"
    fontSize: "21px"
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: "Liv Figures, Gill Sans MT, Calibri, sans-serif"
    fontSize: "19px"
    fontWeight: 700
    lineHeight: 1.3
  technical:
    fontFamily: "Consolas, Cascadia Mono, monospace"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
  theo-hand:
    fontFamily: "Segoe Print, Segoe Script, cursive"
    fontSize: "24px"
    fontWeight: 400
    lineHeight: 1.35
rounded:
  control: "4px"
  lined-panel: "6px"
  badge: "50%"
spacing:
  xs: "6px"
  sm: "12px"
  md: "18px"
  lg: "26px"
  xl: "40px"
  column-pad: "48px"
components:
  button-primary:
    backgroundColor: "{colors.hartley-green}"
    textColor: "{colors.white}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "0 30px"
    height: "60px"
  button-secondary:
    backgroundColor: "{colors.white}"
    textColor: "{colors.hartley-green}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "0 30px"
    height: "60px"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.frame-black}"
    typography: "{typography.body}"
    padding: "0 12px"
    height: "60px"
  button-quiet-open:
    backgroundColor: "{colors.mist}"
    textColor: "{colors.frame-black}"
  talk-button:
    backgroundColor: "{colors.hartley-green}"
    textColor: "{colors.white}"
    rounded: "{rounded.control}"
    height: "66px"
    width: "320px"
  write-input:
    backgroundColor: "{colors.white}"
    textColor: "{colors.frame-black}"
    rounded: "{rounded.control}"
    height: "58px"
    padding: "0 18px"
  conversation-column:
    backgroundColor: "{colors.hartley-green}"
    textColor: "{colors.on-green}"
    padding: "40px 48px 32px"
    width: "720px"
  work-area:
    backgroundColor: "{colors.white-enamel}"
    textColor: "{colors.frame-black}"
    padding: "40px 48px 32px"
  lined-card:
    backgroundColor: "{colors.white}"
    textColor: "{colors.frame-black}"
    rounded: "{rounded.lined-panel}"
    padding: "30px 36px 26px"
  room-lit:
    backgroundColor: "{colors.white-enamel}"
    textColor: "{colors.ink-2}"
  room-locked:
    backgroundColor: "{colors.green-unlit}"
    textColor: "{colors.on-green-2}"
  repair-tag:
    backgroundColor: "{colors.tag-manila}"
    textColor: "{colors.tag-ink}"
---

# Barnaby · Livery

## Overview

**The world.** A family shop's livery (its fascia, its van, the paper bags, the head badge on the bikes it builds) is how
you know who belongs. Barnaby is dressed in Spokes & Sprockets' own colours: Hartley green, lined in gold by hand the
way a frame painter lines a lug. "Livery" is also what a butler wears. He is staff, not a visitor.

**Why Martin trusts it.** Belonging and craft pride. These are his colours, not a tech company's; the man in the shop
apron is one of ours. Whatever needs his say-so is lined twice, so it is never missed and never shouted.

**Mode: Operate.** This is a working display a 61-year-old glances at from a step back, and the director records it
live. The world lends four things only: palette, type, density and one signature move (the coachline). Layout,
navigation and controls are the ordinary ones: tabs, a segmented switch, buttons, a table, a text input.

**The signature move: the coachline.** A 2 px gold line and a 1 px gold line, 5 px apart. It frames whatever needs
Martin (approval cards), is pulled under each step as he finishes it, underlines the current tab, and draws the walls
of the house. Nothing else in the interface is gold except the badge and small labels on green.

**Two raises taken from the directions it beat** (disciplines, not looks):
- *From Bell Board: always say where he is.* The status line names the room ("Checking parts, in the stockroom"), every
  step carries its room in gold ("in the workshop"), and while he works the room he is in is the one marked on the
  plan. "Show where he has been" is never a log you have to open.
- *From Job Card: everything is filed.* Each exchange keeps its time and its outcome ("08:53 · What's due tomorrow… ·
  Five due; Anika's brakes short one pair"), listed under "Earlier today" in the conversation column; keys, passages and
  rooms each have a time.

**Per-person views, one identity.** Barnaby shows each person the view that fits them; "At the desk" switches it.
- **Martin (owner):** *Today* (conversation and the evidence) and *The house* (the plan: rooms are what the system can
  do; white enamel = he can use it; green with a key = he'd ask first; struck = kept shut; a passage; a room lined
  twice = built with your say-so).
- **Theo (developer):** *The workings*: every discovered ability with method, path, MCP tool, read/write and state; the
  Synapse runs with seconds; the live call-by-call trace; the build (tests, files, timing, who approved); the diff; the
  composed skill; git history. Exact, nothing tidied, still green and gold.
- **Priya (staff, day one, proposal):** *My bench*: her jobs as the paper repair tags hung on handlebars (bike,
  customer, work, due, parts ready?), Theo's note, and "Things you can ask me".

**Motion.** The liner's pull: one steady stroke, about 400 ms, exponential ease-out, from an already-visible state.
A finished step gets its line; a card that needs you is lined round; a new room's second line is drawn once. Nothing
bounces, nothing loops, nothing pulses. `prefers-reduced-motion`: lines simply appear.

**Sound.** One ring of the shop's brass counter bell when he answers (the film's bell). A key turning in a lock when a
key is handed over. Otherwise quiet: the workshop radio carries on. Sound is optional and off by default in `ui/`.

**Direction contract (look-dev, for the `ui/` build).**
- THESIS: Barnaby is shop staff in the shop's livery; the display refuses the dark chat-plus-developer-trace layout.
- OWN-WORLD: Hartley green shell and conversation column, white-enamel work surfaces, gold coachlines, Gill Sans MT,
  Perpetua Titling for the badge and room names, the bell in an oval head badge.
- STORY: Martin asks out loud, sees in plain words where Barnaby went and what he found, and says yes or no on a lined
  card that tells him what it does, what it reads or touches, what stays locked, and that the checks pass.
- FIRST VIEWPORT: green header (badge, BARNABY, live status naming the room, tabs, At the desk); green conversation
  column (720 px) with Martin's question, Barnaby's words at 38 px, the steps with their rooms, keys he holds; white work
  area with the evidence (table) or the lined approval card; talk bar with Hold to talk and Or write it.
- FORM: Livery, direction B of three (A Job Card, C Bell Board); seed: none (unavailable). The impeccable launcher was
  not approved, so no roll ran; the three directions were derived by hand from the shop's own world.
- FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and
  every shipping raster carrying its provenance.

## Colors

**Strategy: Committed.** Hartley green owns the header and the conversation column, 30 to 50 % of the window. Working
and reading surfaces are white enamel. Not cream, not dark mode: the scene is a back office in cool morning daylight on
a glossy 2009 LCD, where large light surfaces read best and the green shell still makes it unmistakably the shop's.

| Role | Token | Use |
|---|---|---|
| Hartley green | `hartley-green` #17402F | Header, conversation column, primary buttons, the talk button, table rule. The shop's fascia colour (proposed: WORLD.md gives the shop no colour yet; the set's sign and the RING FOR SERVICE card should adopt it). |
| Unlit room | `green-unlit` #215443 | Rooms on the plan he would need a key for. |
| Lining gold | `lining-gold` #C9A04A | Coachlines, the badge and small labels **on green** only. |
| Lining gold on white | `lining-gold-on-white` #977629 | Coachlines and icons on white (4.25:1). Never body text. |
| White enamel | `white-enamel` #F7F7F3 | The work area. Cards and inputs are pure `white`. |
| Frame black | `frame-black` #141414 | Body text on white (17:1). |
| Mist | `mist` #E3EAE5 | Second neutral: headers of the change, the opened "See the change" button. |
| Enamel red | `enamel-red` #A3261B on `red-tint` | A shortfall only (Anika's pads), always with the warning icon and the word "Short". |
| Added | `added` #E3EEE6 | Added lines in the diff; the built row in Theo's table. |
| Tag manila | `tag-manila` #E7D8B3, ink #2B2416 | Priya's repair tags. |

Measured contrast: white on green 11.6:1 (Barnaby's words, AAA); on-green-2 on green 8.3:1; on-green-3 on green 6.0:1;
gold on green 4.8:1 (AA, so gold text stays at 19 px bold or above and short); frame black on enamel 17.2:1; ink-2 on
enamel 8.6:1; red on red-tint 6.1:1; manila ink on manila 10.9:1. State is never colour alone: lit rooms carry a filled
square, locked ones a key, shut ones a no-entry sign and strike-through.

## Typography

All faces are already on the shop PC (Office 2007-era) and on the recording machine; nothing is downloaded.

- **Gill Sans MT** carries everything: Barnaby's words, Martin's questions, headings, cards, tables, buttons. The English
  shop-sign and railway sans; Bold for headings, cards and buttons.
- **Perpetua Titling MT** (Gill's engraved capitals) only for the wordmark BARNABY, the shop's name and room names on
  the plan, letter-spaced 0.07 to 0.16em.
- **Figures come from Segoe UI.** Gill Sans MT's "1" reads as a capital I in job numbers and times. The `Liv Figures`
  face maps digits only (`unicode-range: U+0030-0039`) to Segoe UI / Segoe UI Semibold, placed first in the stack.
- **Consolas** only for code and technical names (`POST /api/purchase-orders`, the diff, Theo's tables).
- **Segoe Print** only for Theo's handwriting on a sticky note.

Scale (at 1920×1080): his words 38/1.24; card title 40 bold; heading 30 bold; question 27; step 22; body and table
21/1.4; labels 19 bold; small print 19; technical 15. Body is never below 19 px on Martin's and Priya's screens; Theo's
tables run at 14 to 16 px by design (dense, developer-only).

Font loading on Windows Chrome (measured): family names that do not resolve, such as "Gill Sans Ultra Bold",
"Franklin Gothic Medium Cond" and "Copperplate Gothic Bold", load through `@font-face { src: local("…") }` aliases.
Set `font-weight` explicitly after any `font:` shorthand.

## Layout

- **Shell, every view:** header 96 px (green, ending in a gold double rule), main, talk bar 104 px (white). The header
  holds the badge and wordmark, the live status (icon plus words, naming the room while he works), the tabs for the
  person at the desk, and the "At the desk: Martin | Theo | Priya" segmented switch.
- **Martin, Today:** two columns, green conversation 720 px and white work area. The conversation column stacks the
  question, his words, "What he did" (steps with rooms), "Earlier today", and "Keys you've given him" pinned to the foot.
  The work area holds the evidence (a table) or the lined approval card plus the mini-room it affects; "See the change"
  opens the change below the card, in the work area, never in a modal.
- **Martin, The house:** the plan on green (left) and a white "Key to the plan" column of 560 px (legend, "9 of 24
  things he can do, and one passage", keys given, passages and rooms made, each with a time).
- **Theo, The workings:** 520 px green summary column (system, counts, Synapse runs) and a dense white area (abilities
  table; live trace, build, history).
- **Priya, My bench:** 640 px green column (her question, his answer, Theo's note, her first day) and the bench: a rail,
  two tags, "Things you can ask me".
- **Rhythm:** 48 px column padding, 26 px between groups, 12 to 18 px inside them; more space above a heading than
  below.
- **Smaller windows (`ui/` in a browser):** below 1400 px the conversation column takes 40 %; below 1000 px the columns
  stack, conversation first, and the talk bar stays fixed at the bottom.

## Elevation & Depth

Flat. Depth comes from the colour fields (green shell, enamel work area, white cards), not from shadows. The coachline
is a line, not a glow; implement it with a border plus `outline` and `outline-offset` (or a pseudo-element), and never as
a zero-offset coloured shadow standing in for depth. The one real shadow is under Theo's sticky note on Priya's bench
(a paper object), with a real offset and soft blur.

## Shapes

- Controls (buttons, the input, the segmented switch): 4 px radius.
- Lined panels (approval cards, the coachline sample): 6 px radius on the inner line.
- Rooms on the plan: square corners, 2 px gold walls; the passage has no top wall (it opens into the rooms).
- The badge: an upright oval head-tube plate with the bell drawn in line.
- Repair tags: a rectangle with clipped top corners, a reinforced eyelet and a string to the rail.
- Icons: one set, drawn in SVG at a single stroke weight with round ends, like lining (mic, key, tick, see, passage,
  arrow, no-entry, warning, plus, bell). No emoji or Unicode glyphs as icons.

## Components

- **Header status:** icon plus words, always a sentence a person would say: "At your service", "Checking parts, in the
  stockroom", "Waiting for your say-so", "Answering Priya".
- **Asked / said:** the asker's name and time in gold, the question in quotes at 27 px; Barnaby's line with the small
  badge, at 38 px white. An earlier line in the same exchange sits above at 24 px on-green-2.
- **Step ("What he did"):** tick (or dots while working), what he did, the room in gold ("in the workshop"), what he
  found, and for parts the per-bike line ("Rachel · Sofia · **Anika: short** · Thanh · Kwame"). The coachline is pulled
  under it as it finishes; while working, it is drawn in proportion (3 of 5).
- **Earlier today:** time, the question in quotes, the outcome in one line. Newest first.
- **Keys you've given him:** key or passage icon, the plain name, the time. "None yet. He can only look." when empty.
- **Approval card, key (Unlock):** lined twice. Title in plain words ("Let Barnaby order parts from your suppliers"),
  then a label/value list: What it means, What stays locked, Each time. Allow (primary, key icon) and Not now; "One click.
  Nothing is ordered until you've said yes to the order itself." The technical name (`POST /api/purchase-orders`) is
  15 px Consolas, ink-3, right-aligned at the foot. Beside it, the mini-room showing "this key" and what "stays locked".
- **Approval card, change (Build):** lined twice. "Add a weekly workload report"; What it does, What it reads (only the
  job board; it changes nothing), Theo's checks (tick: "All 22 pass: Theo's own 19, and 3 new ones for this report"), If
  you change your mind (it can be undone). Add it, Not now, and the quiet "See the change" (underlined text button;
  "Hide the change" when open). "A change like this needs a click, not a spoken yes." Beside it, the new room lined
  twice: "a new room, once you add it".
- **Approval card, data change (write):** the same lined card with the action in plain words, Approve and Decline, and
  "or say yes".
- **See the change:** a white sheet under the card: "The change, for whoever wants to read it · 3 files · 114 lines
  added · nothing removed", then each file with its plain caption ("services.py · The adding-up itself") and the real
  diff in Consolas, added lines on `added`.
- **Evidence table:** bold 18 px headers over a 2 px green rule; rows of 21 px; a shortfall row on red-tint with icon
  and "Short."; pending cells show dots and "Checking…".
- **The house:** rooms as squares with gold walls; lit rooms white enamel with a filled square per thing he can use;
  locked rooms green with keys; "your key" in bold on abilities handed over today; "kept shut" struck through with a
  no-entry icon; the passage "Hand back a bike" (Look up the job → Text the customer → Mark it ready) as a corridor; the
  built room lined twice, "built today".
- **Theo's abilities table:** method, path, MCP tool, read/write, state (exposed with a filled square, unlockable with a
  key, denied in red with a no-entry sign, built on `added`).
- **Repair tag (Priya, proposal):** SPOKES & SPROCKETS, "Repair · from Dev's bench", the job number large, customer,
  bike and colour, work and hours, due ("Tomorrow, Tue 24 Nov"), parts with ticks or a warning, and a stamp: PARTS READY
  or SPOKES SHORT.
- **Proposal banner:** dashed gold-on-white box with a "Proposal" label, on any view not yet decided.
- **Talk bar:** Hold to talk (green, mic icon, 320 px), "or hold the space bar", "Or write it:" and the input, Ask.
- **Browser surfaces:** selection in gold with black text; focus ring 3 px `lining-gold-on-white` with a 3 px offset;
  caret in green; tabular figures from Segoe UI.

## Do's and Don'ts

- **Do** speak in the household's words on Martin's and Priya's screens. Never "endpoint", "API", "tool", "MCP",
  "server", "deploy", "merge" or "diff" there; the technical name appears only as a quiet 15 px detail or behind "See the
  change". Theo's view may be fully technical.
- **Do** name the room in every step and in the status while he works.
- **Do** keep gold for lines, the badge and short labels on green. **Don't** set gold body text, or gold on white text.
- **Do** keep red for a real shortfall, always with the icon and a word. **Don't** use it for emphasis or errors of
  style.
- **Don't** put a kicker or eyebrow label above a heading; the heading speaks. Form-style labels beside values are fine.
- **Don't** add gradients, glass, glows, pulsing dots, orbs or sparkles. **Don't** use zero-offset coloured shadows as
  depth.
- **Don't** promise what the app can't do: there is no way to take a key back yet, so no card says there is.
- **Don't** call Barnaby's 3 new tests Theo's: "All 22 pass: Theo's own 19, and 3 new ones."
- **Don't** add wood, paper or enamel textures. The world is carried by colour, type and the coachline.
- **Do** honour reduced motion, and keep every transition under 400 ms.
