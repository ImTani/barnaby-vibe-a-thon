---
name: Barnaby · App
description: A real professional app, played straight. Calm light workspace; Barnaby in the details (the bell, one brass accent, his words). Pending the director's approval.
colors:
  canvas: "#FFFFFF"
  panel: "#F6F5F3"
  panel-hover: "#EEEDE9"
  hairline: "#E6E4DF"
  line: "#D6D4CE"
  line-strong: "#C4C2BB"
  ink: "#1D1C1A"
  ink-hover: "#3A3834"
  ink-2: "#4F4D48"
  ink-3: "#6B6963"
  shade: "rgba(29, 28, 26, 0.06)"
  brass: "#AA7C27"
  brass-ink: "#8A6318"
  brass-tint: "#F7F0E0"
  brass-select: "#F0E1BD"
  focus: "#A67A26"
  ok: "#1E7A4C"
  ok-tint: "#E9F4EE"
  bad: "#B3261E"
  bad-tint: "#FBECEA"
  diff-add: "#E6F4EA"
  diff-add-ink: "#14532D"
  diff-del: "#FBEAEA"
  diff-del-ink: "#7F1D1D"
typography:
  answer:
    fontFamily: "Segoe UI Variable Display, Segoe UI, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "-0.005em"
  card-title:
    fontFamily: "Segoe UI Variable Display, Segoe UI, system-ui, sans-serif"
    fontSize: "21px"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "-0.01em"
  question:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 600
    lineHeight: 1.45
  section-title:
    fontFamily: "Segoe UI Variable Display, Segoe UI, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  history:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 400
    lineHeight: 1.55
  fact:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: "26px"
  ui:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  button:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1
  small:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.4
  meta:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: "22px"
  caption:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.4
  code:
    fontFamily: "Cascadia Mono, Consolas, monospace"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  sm: "6px"
  md: "8px"
  lg: "12px"
  xl: "14px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  2xl: "40px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.canvas}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "0 20px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.ink-hover}"
  button-secondary:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "0 20px"
    height: "44px"
  button-secondary-hover:
    backgroundColor: "{colors.panel-hover}"
  button-talk:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.canvas}"
    typography: "{typography.button}"
    rounded: "{rounded.lg}"
    padding: "0 20px 0 16px"
    height: "52px"
  button-talk-listening:
    backgroundColor: "{colors.brass-ink}"
    textColor: "{colors.canvas}"
  button-toolbar:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.small}"
    rounded: "{rounded.md}"
    padding: "0 14px 0 11px"
    height: "36px"
  composer-field:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.fact}"
    rounded: "{rounded.lg}"
    padding: "0 6px 0 16px"
    height: "52px"
  decision-card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.xl}"
    padding: "22px 24px 0"
  decision-footer:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-2}"
    typography: "{typography.small}"
    padding: "14px 24px"
  inspector:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    typography: "{typography.ui}"
    width: "clamp(380px, 26vw, 440px)"
  avatar-tile:
    backgroundColor: "{colors.brass}"
    textColor: "{colors.canvas}"
    rounded: "{rounded.sm}"
    size: "22px"
  thread-note:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-2}"
    typography: "{typography.small}"
    rounded: "{rounded.lg}"
    padding: "12px 16px"
---

# Design System: Barnaby · App

> **Pending the director's approval.** This describes `?skin=app` (`ui/skins/app.css`), built to become the default
> display. Until it is approved, the default look is still `ui/style.css`. This file replaces the earlier "Livery"
> look-dev, which was never built into `ui/`; its text is in git history (`git show f7ebf84:DESIGN.md`). The working
> record for this round is `video/v2/look/app2/` (product notes, frames, checks).

## Overview

**Creative North Star: "A careful colleague's desk."** Barnaby's display is the one part of the product that *is* the
app, so it is a real professional app, played straight: the conventions of Mail, Linear, Things 3 and the Claude
desktop app, at their craft level, light by default. The owner (61, reading glasses) talks to it from a step back on a
2009-era PC at about 1440×900; staff ask quick questions; the developer opens the record on request. Nothing is a
costume. Barnaby lives in the details: the bell tile, one brass accent, his words in every label and empty state,
approvals that read like a colleague asking before he does something, and a voice control that feels native.

The layout is the category standard: a toolbar, the conversation in a 760px measure, a quiet inspector of what he did,
decision cards at the foot of the thread, and a composer whose main control is Hold to talk. Hierarchy comes from size
and weight on one face, not from colour or ornament.

**Key Characteristics:**
- Light white canvas, a warm-neutral inspector, hairlines; one soft shadow, only on the card that needs an answer.
- Segoe UI throughout (Variable on Windows 11), one fixed scale; mono only for code and technical names.
- The current answer is the largest text on screen (22px); history steps back to 18px in a softer ink.
- Plain words first everywhere; the technical record is one disclosure away, never in the way.
- Brass means "Barnaby" or "your turn", and nothing else.

## Colors

**Strategy: Restrained.** Neutrals carry the surface; one brass accent and two state colours do real jobs. Light was
chosen from the scene: a back office in daylight and strip lights, a glossy panel with glare, a reader with glasses.

### Primary
- **Ink** (#1D1C1A): text, primary buttons, Hold to talk. 17:1 on white. Hover **#3A3834**.

### Secondary
- **Brass** (#AA7C27): his mark only (the bell tile, the avatar). A graphic, never text (3.7:1 on white; the white bell on it 3.7:1, above the 3:1 for graphics).
- **Brass ink** (#8A6318): brass words and icons: "Waiting for your say-so", "Listening", the ask step, "Key given
  today", the talk button while held. 5.4:1 on white.
- **Brass tint** (#F7F0E0): the card's kind-icon tile. **Brass select** (#F0E1BD): text selection. **Focus** (#A67A26):
  the 2px focus ring.

### Tertiary
- **OK** (#1E7A4C; 5.3:1 on white, 4.7:1 on #E9F4EE): checks that pass, "You said yes", "He can use it".
- **Bad** (#B3261E on #FBECEA): errors and "Kept shut" only, always with an icon and words. 6.5:1.
- **Diff**: added #E6F4EA / #14532D, removed #FBEAEA / #7F1D1D.

### Neutral
- **Canvas** #FFFFFF (conversation, cards, inputs). **Panel** #F6F5F3 (inspector, card footer, notes, code). **Panel
  hover** #EEEDE9. **Hairline** #E6E4DF (separators). **Line** #D6D4CE (control and card borders), **line strong**
  #C4C2BB (border under the pointer, scrollbar). **Shade** rgba(29, 28, 26, .06) (hairline shadows).
- Text: **ink-2** #4F4D48 (secondary, history; 8.4:1 on white, 7.8:1 on the panel), **ink-3** #6B6963 (meta, labels,
  placeholders; 5.5:1 on white, 5.0:1 on the panel). Nothing lighter carries text.

### Named Rules
**The Brass Rule.** Brass appears only on his mark, the waiting and listening states, focus and selection. If brass
shows up anywhere else, it is decoration and comes out.
**The Never-Colour-Alone Rule.** Every state carries an icon and a word: a tick and "You said yes", a key and "Asks
first", a no-entry sign and "Kept shut".

## Typography

**Display:** Segoe UI Variable Display (falls back to Segoe UI on Windows 7) for the answer, card titles and section titles.
**Body:** Segoe UI Variable Text / Segoe UI for everything else. **Code:** Cascadia Mono, Consolas.

**Character:** the platform's own workhorse face, tuned. On the shop's PC and the developer's alike it reads as a
Windows app made with care; no download, no display costume.

### Hierarchy
- **Answer** (400, 22px, 1.5): Barnaby's words in the current exchange. The thing read from a step back.
- **Card title** (600, 21px, 1.35): what he is asking for, in plain words.
- **Question** (600, 19px, 1.45): what you asked; the "subject" of an exchange.
- **History** (400, 18px, 1.55, ink-2): earlier answers; also card lead lines.
- **Fact** (400, 17px, 26px): card facts, the composer's text.
- **UI** (16px; 600 for buttons): steps in the inspector, buttons, the welcome's hints.
- **Small** (15px): toolbar, status, card hints, disclosures, thread notes.
- **Meta** (600, 14px): author lines ("Barnaby 09:07"), form labels. **Caption** (13px): times in the inspector,
  group headings in the abilities list, state words.
- **Code** (12.5px, 1.6, mono): the diff, technical records, technical names. Nowhere else.
- Compact window (560) and phone width: answer 19, question 17, history 16; a card title is never smaller than the
  answer above it.

### Named Rules
**The One Face Rule.** One family carries every word; scale and weight make the hierarchy. Mono is for code only.
**The Fixed Scale Rule.** Sizes are fixed pixels, not fluid: a pixel on the shop's 19-inch 1440×900 panel is as large
as on a 24-inch 1080p screen, so nothing shrinks for the smaller screen.

## Layout

- **Shell:** toolbar 56px across the top; below it, the conversation column (left, flexible) and the inspector
  (right, `clamp(380px, 26vw, 440px)`, full height); the composer sits under the conversation only.
- **Toolbar:** bell tile + "Barnaby", a hairline, the system's name · "He can use 6 of its 23 things", then (right)
  the status sentence and "What he can do".
- **Conversation:** a 760px measure, centred, anchored to the bottom like Messages; 40px side padding. An exchange
  starts with a hairline and 28px above "You 09:07"; Barnaby's reply 22px below; his consecutive lines 14px apart under
  one author line; kept decisions and notes 16-18px apart. The welcome centres in the column when the thread is empty.
- **Decision card:** at the foot of the thread, the same measure. Icon column 40px + 14px; title, lead, facts and
  disclosures hang from the title's edge (54px); the footer runs full width and docks to the bottom edge of the
  conversation while the card is taller than the view.
- **Inspector:** 20px header with a hairline; steps 8px from the edge, 20px icon column, 10px gap; the current
  request's header sticks to the top; earlier requests fold to short, quieter lines.
- **What he can do:** takes the inspector's place and widens to `clamp(420px, 32vw, 560px)`; inset grouped lists by
  area, rows 10px × 14px.
- **Composer:** Hold to talk (52px) beside the field (52px), "or hold the space bar" under the button.
- **Below 960px** the inspector folds away and "What he can do" opens as a sheet from the right. **Below 600px** the
  brand word hides (never in the compact window), the status may wrap to two lines, cards stack their facts.
- **Rhythm:** 4, 8, 12, 16, 24, 40; more space above a heading than below it.

## Elevation & Depth

Flat, with hairlines and one tonal step (canvas and panel). The only raised object is the decision card: it is the one
thing waiting for an answer. Scroll edges under the toolbar fade over 16px; the foot stays hard so a docked footer
closes the card.

### Shadow Vocabulary
- **Card** (`0 1px 2px rgba(29,28,26,.06), 0 10px 28px -8px rgba(29,28,26,.16)`): the decision card only.
- **Control** (`0 1px 1px rgba(29,28,26,.06)` / `0 1px 2px …`): the toolbar button and the composer field.
- **Pressed** (`inset 0 1px 2px rgba(29,28,26,.06)`): the toolbar button while its panel is open.
- **Sheet** (`-12px 0 32px -12px rgba(29,28,26,.25)`): "What he can do" as a sheet below 960px.

### Named Rules
**The One Raised Thing Rule.** Only a card that needs an answer casts a real shadow. Never a zero-offset glow.

## Shapes

Radii 6 (avatar tile, small icon buttons), 8 (buttons, inputs, code blocks), 12 (composer, notes, grouped lists,
icon tiles, the bell tile), 14 (the decision card, the welcome's bell). Circles only for spinners and status dots.
Icons: one inline SVG set, 2px stroke, round ends (bell, mic, keys, key, tick, check-circle, no-entry, passage, new
piece, pen, look, plan, plug, chevron, warning). No emoji or Unicode glyphs as icons.

## Components

### Buttons
- **Primary** ("Yes, go ahead", "Yes, add it", "Approve", "Connect"): ink fill, white text, 44px, radius 8; hover
  #3A3834; pressed moves 1px. Always the rightmost in a footer.
- **Secondary** ("Not now", "Decline", "Close"): white, 1px line border, ink text; hover panel-hover.
- **Toolbar** ("What he can do"): 36px, plan icon, pressed state while the panel is open.
- **Hold to talk:** ink, mic icon, 52px, min 158px; held, it turns brass-ink, the mic becomes five level bars and the
  label reads "Listening…"; the hint under it reads "Let go when you've finished."
- **Ask:** inside the field, quiet (panel-hover) until there is text, then primary.

### Cards / Containers
- **Decision card:** kind icon on a brass-tint tile (key, passage, new piece, pen), the plain title, a lead line (the
  why, or what it does), a facts table (label 15px ink-3 / value 17px ink: What it reads, What it changes, Checks with
  a green tick, If you change your mind, Each time), then "See the change" with its size ("3 files, 102 lines added,
  nothing removed") and "Technical detail" as disclosures; the footer says how it may be answered ("Or just say
  “yes”." / "A change like this needs a click, not a spoken yes.") with Not now and Yes.
- **Thread note:** panel tint, icon, bold lead ("Connected", "Voice isn't available just now"), one sentence; errors on
  bad-tint with a warning icon and the raw message under Details.
- **Kept decision:** a line in the thread: tick or cross, "You said yes:" and the thing in plain words, the time.

### Inputs / Fields
- **Composer field:** 52px, radius 12, line border, a 1px focus ring in focus brass; brass border while listening.
- **Form fields** (connect): 40px, radius 8, labels 14px semibold above; focus ring 2px brass; invalid after
  interaction shows a bad border.

### Navigation
- The toolbar is the only navigation: brand, system, status, "What he can do". The panel closes with Close.

### Signature: the activity inspector
"What he did": per request, the question and its time, then each step in plain words with a mark (tick, key, cross,
warning, new piece, a still arc while in progress) and a quiet sub-line; a chevron on hover opens the technical record
in mono. The yes is listed before the act it allowed. Only the line in the conversation animates while he works.

## Do's and Don'ts

### Do:
- **Do** speak in the household's words on every surface the owner sees; technical names only in Details, "See the
  change" and "Show technical names".
- **Do** say the status as a sentence in the present tense ("Looking at repair jobs due on Tue 24 Nov").
- **Do** keep every yes and no in the thread, naming the thing, not its arguments.
- **Do** keep the decision reachable: the card's footer docks while the card runs past the fold.
- **Do** give every state an icon and a word; keep body text at ink or ink-2.
- **Do** honour reduced motion (all animation off) and keep transitions at 150-220ms.

### Don't:
- **Don't** add themes or costumes: road signs, tickets, liveries, paper, enamel, brass gradients.
- **Don't** bring back the AI tell: dark navy and brass, italic serif bot voice, bubbles left and right, status pills,
  a monospace live trace.
- **Don't** put a kicker or eyebrow above a heading, or a capsule around a state word.
- **Don't** use brass for anything but his mark, the waiting and listening states, focus and selection.
- **Don't** run more than one moving indicator at a time.
- **Don't** promise what the app can't do: there is no way to take a key back yet, so no card says there is.
- **Don't** call Barnaby's 3 new tests Theo's: "Theo's 19 checks still pass, and so do the 3 new ones."
