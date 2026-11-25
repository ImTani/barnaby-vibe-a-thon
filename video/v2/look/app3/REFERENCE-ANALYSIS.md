# What real AI apps look like: analysis before the app redesign (round 3)

The director, on round 2 (`?skin=app`, video/v2/look/app2): "Barnaby's display as a real app became way too subdued. It lost
all of its personality. We need to add some of it back, and the icon needs a lot of work. No AI apps look like this.
Take your own UI, for example. Get screenshots of the Claude desktop app UI and the Codex desktop app UI. Model it after
those. Before starting work, analyze the UI in its different aspects."

Reference captured: `refs/claude-desktop-code-tab.png`. This is the Claude desktop app (Code tab, dark), running the very
session that built Barnaby, at 1920×1080. Codex: capture its product UI yourself from the public page
https://openai.com/codex/ (scroll to the app screenshots; headless Chrome is fine), and add your own observations below.

## Claude desktop: aspect by aspect

**1. Overall structure**
- Three zones: a thin top bar, one centred conversation column, and a right-hand "inspector" panel. Nothing else competes.
- The conversation column is narrow (about 680–720 px at 1920) and centred in the space left of the inspector. That
  leaves generous, calm margins.

**2. Colour and surface**
- A neutral charcoal ground in dark mode (not navy, not blue-black). In light mode, a warm off-white/ivory.
- Surfaces are separated by tone and hairlines, not shadows. No gradients, glows or glass.
- The one brand colour (Claude's coral/orange) appears only in the logo and a few brand moments. Everything else is
  greyscale with a single blue for toggles and links.

**3. Typography**
- One clean sans for UI and prose, at about 15–16 px for body, with comfortable line height.
- Secondary text is clearly greyer, not smaller. Bold is used sparingly, as lead-ins.
- Inline code is a small monospace chip. Headings are rare.
- In Claude chat (claude.ai), the assistant's prose uses a warm serif, with the UI in sans. That is the brand's
  personality carrier: an upright reading serif, not an italic.

**4. How the assistant's work shows (the key pattern)**
- Tool activity is inline in the transcript as single muted grey lines with a chevron: "Checked tabs, opening tab,
  opening a page, 2 failed ›", "Messaged agent 2 times ›".
- Each is a collapsed, plain-language summary of a batch of actions; click to expand into the details.
- There is no separate scrolling "trace" column competing with the answer.
- While working, one live line shows an animated glyph, what it's doing in the present tense, and an elapsed timer
  ("Capturing one screenshot of the Claude desktop app 1m 58s ›").
- The answer itself is full-contrast prose.

**5. Rich cards inline**
- Results that are objects (a web page opened, a file, an artifact) appear as compact cards in the flow: thumbnail,
  title, subtitle, a primary "Open" button and a "…" menu.
- Rounded corners (about 10–12 px), a 1 px border, the surface one step lighter than the ground.

**6. The right panel ("inspector")**
- Sections with small grey headings: Environment, Outputs, Background tasks, Connectors, Context.
- Rows are icon + label, with a right-aligned value or control (a toggle, a status, "Save", a count, a small progress
  bar for context).
- Dense but quiet; it's where state lives, not where the story is told.

**7. Composer**
- A single rounded input pinned at the bottom of the column: "+" on the left, then the field, then right-side icon
  buttons (mic, send/stop).
- Big, soft corners; it feels like an object you speak into. The placeholder teaches ("Ctrl+Enter to queue").

**8. Brand and personality**
- The mark is a distinctive, ownable glyph (Claude's coral spark/asterisk), simple enough to read at 16 px and used
  consistently (app icon, wordmark, working animation).
- Personality lives in the mark, the working animation, the voice of the copy, and a reading serif (chat), not in
  costumes, textures or themed chrome.

## What round 2 got wrong against this
- It modelled a generic productivity app (Linear/Mail), not an AI assistant.
  - The separate "What he did" column is a developer trace in a nicer coat.
  - Real AI apps put the work inline, collapsed, in plain words.
- There was no personality carrier: no Barnaby voice in type, no living working state, a generic brass square for the mark.
- **The icon**: a bell glyph in a rounded brass square. It reads as a stock icon, not an ownable mark, and it doesn't
  survive at 16 px.

## Direction for round 3 (model it on these)
- **Structure.** Keep Claude's shape:
  - top bar (Barnaby's mark and wordmark, the connected system as a selector, status);
  - one centred conversation column;
  - a quiet right inspector (Systems, Keys given, Skills he made, Recent changes, Voice) that can collapse;
  - the composer pinned below.
- **Activity inline, Claude-style:** collapsed grey summary lines in plain words ("Looked at 6 jobs and the parts
  list ›"), expandable to the steps, with the technical record one level deeper. One live line while he works, with
  his animated mark, a present-tense sentence and a timer.
- **Personality back:**
  - Barnaby's words in an upright, warm reading serif (not italic), with the UI in a clean sans.
  - A warm ground (ivory in light, warm charcoal in dark).
  - Brass as the single brand colour, used like Claude's coral: the mark, the working animation, the approval
    accent, focus.
  - His copy voice stays as is.
- **Approval cards** as Claude-style rich inline cards: plain title, the facts, "See the change" folded, clear
  buttons, and the "a click, not a spoken yes" note for code.
- **The icon: a real mark.** Design an ownable glyph for Barnaby:
  - a distinctive, simplified service bell, or a bell plus a monogram, with a clear silhouette at 16, 24, 32, 64 and 512 px;
  - in brass on dark and light, plus a one-colour version;
  - its own working animation (the bell's tap or ring) in the same way Claude's spark animates.
  - Show the icon sheet at every size, the app icon (rounded square), the favicon and the in-thread avatar.
- **Composer:** a Claude-style rounded input with the hold-to-talk mic as its primary right-hand control, a "+"
  (connect a system), and the placeholder teaching the space bar.
- **Light and dark:** both, like the references; default light for the shop (daylight, glare).
