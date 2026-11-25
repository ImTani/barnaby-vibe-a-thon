---
name: Barnaby · App
description: Barnaby's display, modelled on the Claude and Codex desktop apps. One warm column of his words and his work, brass as the one brand colour, a counter bell wearing a bow tie for a mark. Light and dark.
colors:
  ground: "#F6F4EE"
  surface: "#FFFFFF"
  surface-2: "#ECE8DF"
  inspector: "#EFECE5"
  hairline: "#E2DDD2"
  line: "#D3CCBE"
  ink: "#24211C"
  ink-2: "#534F47"
  ink-3: "#6A655B"
  brass: "#A8772A"
  brass-strong: "#87590F"
  on-brass: "#FFFFFF"
  brass-tint: "#F1E5C9"
  brass-select: "#EADBB4"
  ok: "#2B7A4B"
  bad: "#A93A2B"
  bad-tint: "#F8E5E0"
  diff-add: "#E3F1E6"
  diff-add-ink: "#1C5530"
  diff-del: "#F7E2DD"
  diff-del-ink: "#7A2418"
  shade: "rgba(60, 45, 20, 0.08)"
  ground-dark: "#1F1E1C"
  surface-dark: "#2A2926"
  surface-2-dark: "#34322E"
  inspector-dark: "#242321"
  hairline-dark: "#36342F"
  line-dark: "#48453F"
  ink-dark: "#EEEAE1"
  ink-2-dark: "#C2BBAE"
  ink-3-dark: "#9A9488"
  brass-dark: "#D3A14A"
  brass-strong-dark: "#D9A852"
  on-brass-dark: "#1E1709"
  brass-tint-dark: "#3A301E"
  brass-select-dark: "#5A4720"
  ok-dark: "#78C796"
  bad-dark: "#F08F7E"
  bad-tint-dark: "#3B2421"
  diff-add-dark: "#1D3325"
  diff-add-ink-dark: "#AEE2BF"
  diff-del-dark: "#3C2320"
  diff-del-ink-dark: "#F4B6AB"
  shade-dark: "rgba(0, 0, 0, 0.35)"
  icon-brass: "#AA7C27"
  icon-ivory: "#FFF8EB"
typography:
  words:
    fontFamily: "Sitka Text, Constantia, Georgia, serif"
    fontSize: "19px"
    fontWeight: 400
    lineHeight: 1.62
  words-earlier:
    fontFamily: "Sitka Text, Constantia, Georgia, serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.62
  card-lede:
    fontFamily: "Sitka Text, Constantia, Georgia, serif"
    fontSize: "16.5px"
    fontWeight: 400
    lineHeight: 1.55
  welcome:
    fontFamily: "Sitka Subheading, Sitka Text, Constantia, Georgia, serif"
    fontSize: "32px"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  wordmark:
    fontFamily: "Sitka Subheading, Sitka Text, Constantia, Georgia, serif"
    fontSize: "19px"
    fontWeight: 600
    lineHeight: 1
  your-words:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  card-title:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 600
    lineHeight: 1.35
  ui:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  button:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "14.5px"
    fontWeight: 600
    lineHeight: 1
  work-line:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: "20px"
  small:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "13.5px"
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 600
    lineHeight: 1.3
  code:
    fontFamily: "Cascadia Mono, Consolas, monospace"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  sm: "6px"
  md: "8px"
  control: "10px"
  lg: "12px"
  card: "16px"
  bubble: "18px"
  composer: "22px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "18px"
  2xl: "28px"
components:
  thread-column:
    width: "720px"
    padding: "28px 28px 0"
  barnaby-words:
    textColor: "{colors.ink}"
    typography: "{typography.words}"
  your-words:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.ink}"
    typography: "{typography.your-words}"
    rounded: "{rounded.bubble}"
    padding: "10px 16px"
  work-line:
    textColor: "{colors.ink-3}"
    typography: "{typography.work-line}"
    height: "26px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "16px 18px 0"
  button-primary:
    backgroundColor: "{colors.brass-strong}"
    textColor: "{colors.on-brass}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    padding: "0 16px"
    height: "38px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    padding: "0 16px"
    height: "38px"
  composer:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.composer}"
    padding: "12px 10px 10px 16px"
  hold-to-talk:
    backgroundColor: "{colors.brass-strong}"
    textColor: "{colors.on-brass}"
    typography: "{typography.button}"
    rounded: "{rounded.pill}"
    padding: "0 16px 0 12px"
    height: "38px"
  send:
    backgroundColor: "{colors.brass-strong}"
    textColor: "{colors.on-brass}"
    rounded: "{rounded.pill}"
    size: "38px"
  inspector:
    backgroundColor: "{colors.inspector}"
    textColor: "{colors.ink}"
    typography: "{typography.small}"
    width: "clamp(280px, 20vw, 336px)"
  top-bar:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    height: "48px"
  app-icon:
    backgroundColor: "{colors.icon-brass}"
    textColor: "{colors.icon-ivory}"
    rounded: "116px"
    size: "512px"
---

# Design System: Barnaby · App

> **Current design, approved by the director (round 3, 25 Nov).** `ui/skins/app3.css` is the default look: the display
> with no `?skin` is this one. For comparison, round 2 (`?skin=app`, the subdued "professional app") and the old look
> (`?skin=classic`, `ui/style.css`) stay reachable, as do last round's themed skins (`?skin=signpost`, `?skin=ticket`).
> The reference study is `video/v2/look/app3/REFERENCE-ANALYSIS.md`; the frames, icon sheet and checks are in
> `video/v2/look/app3/`.

## Overview

**Creative North Star: "The butler at the counter."** Barnaby is an AI assistant, so his display looks like the AI
apps people already use: the Claude and Codex desktop apps. It has one centred column for the conversation, his work
shown inline as quiet grey lines, rich cards when he needs your say-so, a big rounded composer and a side panel where
state lives. What makes it his and no one else's: his words set in an upright reading serif, a warm ground, brass as
the one brand colour, and a mark of his own, a counter bell wearing a bow tie. It is the shop's "ring for service"
bell, and the butler who answers it.

It is light by default (a back office in daylight and strip lights, a glossy panel, a reader with glasses), with a
warm charcoal dark mode. Fonts are the machine's own, nothing is downloaded. Sitka and Segoe are on Windows 10/11;
Constantia and Segoe are on the shop's 2009-era PC.

**Key Characteristics:**
- One 720px column where his words, his work and the cards appear in the order they happened.
- His work as collapsed plain-words lines; one live line while he works, with his mark at work and a timer.
- Barnaby speaks in a serif; the interface and your words are in a sans.
- Warm ivory or warm charcoal; brass for the mark, the working animation, the decision and focus, and nothing else.
- Claude-style rich cards for every ask: a plain title, the facts, the change by its counts, a clear yes and no.
- A mark with one silhouette and one inner sign, readable at 16px, with its own animation.

## Colors

**Strategy: Restrained, warm.** Tinted neutrals carry the surface; brass is the single brand colour, used the way
Claude uses coral; green and red appear only where they mean something.

### Primary
- **Brass** (#A8772A light, #D3A14A dark): his mark, in the bar, the margin, the welcome and the live line. A graphic,
  never body text (3.6:1 on ivory, 7.1:1 on charcoal).
- **Brass strong** (#87590F light, #D9A852 dark): the decision button, Hold to talk, Send, "Connect a system", brass
  words ("Waiting for your say-so", "Key given today"). White on it 6.1:1; on dark, #1E1709 on it 8.2:1.
- **Brass tint** (#F1E5C9 / #3A301E): the card's kind-icon tile and the halo while listening. **Brass select**
  (#EADBB4 / #5A4720): text selection.

### Tertiary
- **OK** (#2B7A4B / #78C796): checks that pass, a kept yes, "He can use it", lines added.
- **Bad** (#A93A2B on #F8E5E0 / #F08F7E on #3B2421): errors, "Kept shut", lines removed. Always with an icon and words.
- **Diff:** added #E3F1E6 with #1C5530 (dark #1D3325 with #AEE2BF); removed #F7E2DD with #7A2418 (dark #3C2320 with
  #F4B6AB).

### Neutral
| Role | Light | Dark |
|---|---|---|
| Ground (the page, the top bar) | #F6F4EE warm ivory | #1F1E1C warm charcoal |
| Surface (cards, the composer) | #FFFFFF | #2A2926 |
| Surface 2 (your words, hovers, chips) | #ECE8DF | #34322E |
| Inspector | #EFECE5 | #242321 |
| Hairline / line | #E2DDD2 / #D3CCBE | #36342F / #48453F |
| Ink / ink 2 / ink 3 | #24211C (14.6:1) / #534F47 (7.4:1) / #6A655B (5.3:1; 4.7:1 on the hover tint) | #EEEAE1 (13.9:1) / #C2BBAE (8.7:1) / #9A9488 (5.5:1; 4.8:1 on a surface) |

### Named Rules
**The One Brass Rule.** Brass is his mark, his working animation, the decision you make, Hold to talk and focus.
Nothing else is brass. If it shows up as decoration, it comes out.
**The Never-Colour-Alone Rule.** Every state carries an icon and a word: a tick and "You said yes", a key and "Asks
first", a no-entry sign and "Kept shut".

## Typography

**His words:** Sitka Text (Windows 10/11), falling back to Constantia (the shop's 2009 PC), then Georgia. Upright,
never italic. **Headings in his voice** (the welcome, the wordmark, section titles): Sitka Subheading.
**The interface and your words:** Segoe UI Variable Text / Segoe UI. **Code:** Cascadia Mono / Consolas, only for the
diff, technical records and technical names.

**Character:** the serif is the personality carrier, as in Claude's chat: a warm, legible reading face for the one who
speaks; the sans keeps every control familiar.

### Hierarchy
- **Words** (serif 19px / 1.62): his replies in the current exchange. **Earlier** (serif 17px, ink 2): replies in
  earlier exchanges.
- **Welcome** (serif heading 32px): "Good day. What can I look into?" **Wordmark** (serif heading 19px, 600).
- **Card lede** (serif 16.5px): what a card is for, in his words.
- **Your words** (sans 16px) in a soft bubble; **card title** (sans 17px, 600).
- **UI** (sans 15px); **buttons** (sans 14.5px, 600); **work lines** (sans 14px / 20px, ink 3); **small** (13.5px):
  the bar, the inspector, hints; **labels** (12.5px, 600): inspector headings, form labels.
- **Code** (mono 12.5px / 1.6).
- Compact window (560): his words 17.5px; nothing else shrinks.

### Named Rules
**The Two Voices Rule.** Barnaby speaks in the serif; everything you operate is in the sans. Never set a control, a
label or your own words in the serif, and never set his reply in the sans.

## Layout

- **Shell:** a 48px top bar across the window. Below it sit the conversation (flexible) and the inspector (right,
  `clamp(280px, 20vw, 336px)`, full height, collapsible). The composer floats at the foot of the conversation.
- **Top bar:** the mark (24px) and "Barnaby" in the serif; the connected system as a selector ("The shop's back
  office ⌄", opens "What he can do"); then, on the right, the status sentence, "What he can do", light/dark, and the
  side-panel switch.
- **The column:** 720px, centred in the space left of the inspector, anchored to the foot. One scroller holds the
  words, the work lines and the cards, ordered as they happened.
- **The inspector:** sections with small grey headings: System (the system; "He can use 6 of 23" with a small brass
  bar), Keys you gave him, Made with your say-so, Talking to him, then "What he can do ›".
- **What he can do:** a sheet over the side panel (`clamp(380px, 28vw, 460px)`); the conversation narrows, nothing is
  covered.
- **The composer:** the column's width plus 40px, 18px above the window's foot.
- **The compact window** (`?overlay=1`, about 560): bar (mark, name, status), the column, the composer; no inspector, no
  work lines (the pending line says what he is doing).
- **Below 960px** the inspector folds away and "What he can do" opens as a sheet; **below 600px** the cards stack their
  facts and their buttons.
- **Rhythm:** 4, 8, 12, 16, 18, 28. Your message starts an exchange 30px down; his replies 14–16px apart; work lines
  and kept decisions 12px.

## Elevation & Depth

Tone and hairlines, as in the references: the ground, a lighter surface for things you act on, the inspector one step
darker. Two things float with a soft shadow: a **card** that needs your say-so (`0 1px 2px` shade +
`0 12px 32px -16px` shade) and the **composer** (`0 1px 2px` + `0 10px 30px -18px`). The "What he can do" sheet casts
`-18px 0 40px -28px` toward the conversation. No glows, no gradients, no glass.

## Shapes

Radii: 6 (small icon buttons), 8 (bar buttons, chips), 10 (card buttons, code blocks), 12 (inspector rows' groups,
grouped lists, the error note), 16 (cards), 18 (your words), 22 (the composer), pill (Hold to talk, Send, Connect). The
app icon's corner is 116 on 512. Icons are one inline SVG set, 2px stroke, round ends.

## Components

### The thread
- **Your words:** a soft surface-2 bubble on the right, 16px sans, at most 80% of the column.
- **His words:** plain serif prose, full contrast, no bubble. His mark (24px, brass) hangs in the left margin at the
  start of each reply after your message.
- **Kept decisions:** one quiet line, a green tick (or grey cross) and "**You said yes**: ten pairs of the Shimano
  resin pads from Madison…". It names the thing, not the system's arguments, and sits before the work it allowed.
- **Notes:** "Connected", with a plug icon and one sentence. **Errors:** a red-tinted note with a warning icon, a plain
  heading ("Voice isn't available just now"), what to do next, and the raw message under Details.

### Work lines and the live line (signature)
- Consecutive steps collapse into **one grey line** in plain words, with the shared verb said once and repeats counted:
  "Looked at repair jobs due on Tue 24 Nov, parts at or below their reorder level and 5 repair jobs · 7s ›". The
  duration is the recorded one.
- A line opens to its **steps** (tick, key, cross, warning; a quiet sub-line). A step opens, from a chevron on hover,
  to its **technical record** in mono.
- A line that is only a consent step is not shown; the card and the kept decision say it.
- **While he works**, one **live line** replaces it: his mark at work (brass), what he is doing now in the present
  tense ("Looking at repair job 4475"), and a running timer. Only one thing moves on the screen.

### Cards (anything that needs your say-so)
- **Header:** a kind tile (key, shortcut, new piece, pen) on brass tint; the plain title (sans 17px, 600); a kind line
  ("A new key", "A shortcut", "A new piece for the system", "A change to your records").
- **Lede:** in his serif. **Facts:** What it reads, What it changes, Checks (a green tick: "Theo's 19 checks still
  pass, and so do the 3 new ones."), If you change your mind, Each time.
- **Folded rows:** "See the change", with its counts on the right ("3 files +114 −0"), opening to the diff with sticky
  file headers; and Technical detail.
- **Footer:** how it may be answered ("Or just say “yes”." / "A change like this needs a click, not a spoken yes.")
  with Not now (secondary) and the brass Yes on the right. The footer docks to the bottom edge while the card is taller
  than the view.

### Composer
- A white rounded slab (22px). The placeholder teaches: "Ask Barnaby anything, or hold the space bar and talk".
- Bottom row: "+" (connect a system) on the left, a Space key hint, and the primary control on the right: the brass
  **Hold to talk** pill. When you type, it becomes a round brass **Send**.
- **Held:** level bars replace the mic, the label reads "Listening…", the composer border and status turn brass, and
  there is a soft halo.

### Inspector
- Quiet sections and rows: an icon, a label, a right-aligned value or a small bar ("He can use 6 of 23"). The keys you
  gave him and what he made with your say-so are listed with "today". Where state lives, not where the story is told.

### What he can do
- The system's abilities in plain words, grouped by area in inset lists. Each has a state icon and a word: Can use
  (green check), Asks first (key), Kept shut (no-entry, struck through), Key given today, Added today.
- Technical names are behind "Show technical names". The connect form ("Connect a system") is at the foot.

### Welcome
- His mark at 64px, "Good day. What can I look into?" in the serif, one sentence on what he is for, the two controls
  (hold to talk, or type), and "Connect a system" when there is none.

### Signature: Barnaby's mark
- **Drawing:** a counter bell wearing a bow tie. The knob, the dome and the base each stand clear of the next (gaps
  of 3.5 units on the 64 grid). The bow tie (two wings and a knot) is cut out of the dome, so the mark works on any
  ground and in one colour.
- **Files** (`ui/assets/`):
  - `barnaby-mark.svg`: master, 64 grid;
  - `barnaby-mark-16.svg`: drawn on its own 16-pixel grid with 1px gaps;
  - `barnaby-app-icon.svg`: ivory #FFF8EB on brass #AA7C27, 512 with 116 corners;
  - `favicon.svg`: the 16px version on brass, linked from `ui/index.html`.
  - In the page, the mark is drawn inline (mask `#bb-tie` in `ui/index.html`) so it can animate.
- **Sizes:** 16 (favicon, pixel-fitted), 18 (live line), 24 (top bar, margin), 32, 64 (welcome), 512 (app icon). At
  24–32px the tie reads as a light notch; the silhouette carries it.
- **Colours:** brass on ivory, light brass on charcoal; ink or ivory in one colour.
- **Working animation** (1.4s loop, live line only): the knob taps down 3.4 units at 14% and returns by 40%; the dome
  dips (scaleY .955 from the base); two sound waves ring off the dome's shoulders (fade in by 22%, out by 62%,
  growing 0.9→1.14). Reduced motion: still.
- The sheet showing every size, ground and phase: `video/v2/look/app3/icon-sheet.html` and `frames/app3-icons.png`.

## Do's and Don'ts

### Do:
- **Do** keep the work inline and collapsed in plain words; one live line while he works; the technical record two
  clicks down.
- **Do** set his words in the serif and everything you operate in the sans.
- **Do** keep every yes and no in the thread, naming the thing, before the work it allowed.
- **Do** keep the decision reachable: the card's footer docks while the card runs past the fold.
- **Do** say how a card may be answered: a spoken yes for ordinary changes, a click for keys, shortcuts and new pieces.
- **Do** keep light the default for the shop, with dark one switch away (`?theme=dark` or the bar's switch, remembered).
- **Do** honour reduced motion (everything still) and keep transitions at 150–220ms.

### Don't:
- **Don't** bring back a separate trace column, a monospace log, italic serif, dark navy, or bubbles on both sides.
- **Don't** add a second brand colour, gradients, glows or glass; brass is the only accent.
- **Don't** animate anything but his mark on the live line and the level bars while listening.
- **Don't** redraw the mark: no outline version, no tie without the cut-out, no ring arcs when he is idle.
- **Don't** put a kicker above a heading or a capsule around a state word.
- **Don't** promise what the app can't do: there is no way to take a key back yet, so no card says there is.
- **Don't** call Barnaby's 3 new tests Theo's: "Theo's 19 checks still pass, and so do the 3 new ones."
