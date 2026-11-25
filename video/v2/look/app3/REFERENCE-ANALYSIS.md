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

## Codex desktop: aspect by aspect

Captured 25 Nov from https://openai.com/codex/ (the product screenshots on the page; see `refs/codex-*.png`). Headless
Chrome got a Cloudflare bot check (403), so the page was opened in an ordinary browser (cookies: "Reject
non-essential") and only the page's own product images were rendered at their natural size by
`tools/capture-codex-images.js`. Files:
- `codex-new-task-dark.png`: the whole app, empty state;
- `codex-parallel-agents.png`: the sidebar and a thread;
- `codex-task-progress-review.png`: a finished task with its diff pane;
- `codex-edited-files-review.png`: the changes card;
- `codex-code-review-pr.png`: a PR review;
- `codex-sidebar-tasks.png` and `codex-work-location-menu.png`: close-ups.

**1. Overall structure**
- **Four zones:**
  - a slim icon rail on the far left (the mark at the top in a rounded tile, then a few nav icons);
  - a sidebar ("Codex ▾", New chat, Pinned, Recents, Projects);
  - the main thread;
  - a review pane that slides in beside the thread when there are changes (the diff, with Commit and expand/close).
- The thread's title sits in the window bar ("Refine merge conflict UI"). There is a lot of empty space, and the thread
  and composer sit in a column of about 700 px.
- **Empty state:** the mark large and centred, one question ("What should we build?"), and three suggestion rows
  (an app icon plus a sentence) just above the composer. It says what the app is for without a tour.

**2. Colour and surface**
- **Dark:** a neutral charcoal with no tint. The rail, sidebar and thread are separated by one tone step each. The
  composer is a lighter rounded slab, and cards are a darker or lighter slab, never outlined twice.
- **Primary action:** white. The send button is a white circle with a black arrow, the only high-contrast object.
- **Colour has jobs only:**
  - one blue for unread dots and links;
  - green and red only for +/− line counts and status ("Open");
  - small coloured app icons on suggestion rows.
- The purple gradients belong to the marketing page, not the app.

**3. Typography**
- One grotesk sans throughout, large and airy.
- Titles are bold ("Codex", "Prevent duplicate checkout orders"). Secondary text is the same size in grey, often in
  the same line: "Find latest PR **Miniapp**" puts the task in white and the project in grey.
- Times are grey and small ("9:04 AM"). No serif anywhere: Codex's personality is in the mark and the copy, not the
  type.

**4. How the work shows**
- Each turn's work collapses to one grey line above the answer, "Worked for 2m 30s ›", with the plain-prose answer
  below, then a quiet row of icon actions (copy, thumbs, share, more).
- A running task shows a small sparkle spinner in the sidebar list, and a waiting one a clock.
- The user's message is a soft grey rounded bubble on the right. The assistant's words are not in a bubble.

**5. Rich cards inline**
- **Changes card:** "2 files edited +123 −42 Review ↗", then one rounded row per file ("slider.tsx +83 −0 ⌄",
  collapsible), all on a darker slab with large radii (about 16–24 px). The counts are the whole summary; the diff is a
  click away.
- **PR view:** a green "Open" status pill, a bold title, the author and date, a Summary and a Test plan in plain
  prose, then one primary pill button ("Merge") top right.
- **Menus:** "Work in" with "Cloud ✓" and "This computer" in grey, i.e. icon + label + check. They are big, soft and
  quiet.

**6. The side pane**
- **Review pane:** "Unstaged changes +23 −16 ▾" on the left, "Commit ▾", expand and close on the right; file
  headers in grey; changed lines on red and green tints with line numbers. It opens beside the conversation for
  whoever wants the detail, never inside the answer.

**7. Composer**
- **The slab:** big rounded corners (about 24 px), the placeholder "Do anything" / "Do anything. @ to use plugins",
  "+" bottom left, the model selector ("5.6 Medium ⌄") bottom right, then a mic icon and the white circular send
  button.
- **Context chips** ("openai ⌄ monorepo ⌄") sit on a darker tab attached to the top of the composer: where the work
  will happen, chosen right at the point of asking.

**8. Brand and personality**
- **The mark:** a soft scalloped "cloud" outline with a ">_" prompt inside, drawn as one even line. Friendly, a
  little playful, and unmistakable at 24 px. It appears in the rail tile and as the empty-state hero.
- **Personality:** the mark's soft silhouette, the warm question in the empty state, the sparkle spinner, and the
  big soft radii everywhere. Everything else is austere.

## Claude and Codex together: what to take for Barnaby
- **From both:**
  - one centred column, the answer as plain prose, the user's words in a soft bubble on the right;
  - the work as one collapsed grey line per batch, with its duration;
  - a big rounded composer with "+" on the left and the primary control on the right;
  - a side pane for state and detail;
  - colour only where it has a job.
- **From Codex:**
  - an empty state built around the mark and one question, with suggestion rows above the composer;
  - the change summarised by its counts ("3 files · +114 −0"), opened on request;
  - the context selector at the point of asking;
  - the primary circle on the composer (for Barnaby: the brass Hold to talk, which turns into send when there is text).
- **From Claude:**
  - a warm ground and a reading serif for the assistant's words;
  - one brand colour used the way coral is (mark, working glyph, primary decision);
  - the live line (animated mark + present tense + timer);
  - the inspector's quiet sections with right-aligned values and a small progress bar.
- **Barnaby's own mark, by the same rule as theirs:**
  - one simple silhouette with one inner sign. Codex puts a prompt inside a cloud; Barnaby is a service bell wearing a
    bow tie (the butler), cut out of the brass;
  - its own working animation: the knob taps and the bell rings.

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
