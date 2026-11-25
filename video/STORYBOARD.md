# Barnaby: the film (storyboard + style bible) — FROZEN v1.1, approved by Tani 2026-11-25

160 s · 1920×1080 · 30 fps. v1.1 re-times the approved v1 to the real voice-line lengths (no clashes); the content
is unchanged. Every key time below is also in `cues.json`, and the soundtrack (music, sound effects, voice lines) is
cut to those times, so **don't move key events**. If you must, list the actual times in your report.

**Honesty:** the film is a staged recreation of a real recorded run. The numbers, lines, diff and test result come
from `window.DATA` (`data.js`, exported from that run) or from this storyboard. Don't invent other figures.

## Style bible
- **Palette** (`COL`): ink background `#0E1117`, brass `#D4A85A` for accents and anything "Barnaby", ink text `#F1ECE1`,
  secondary `#C2BBA9`, muted `#8D8778`. Tool tiers: read `#3987E5`, write `#D95926`, grow (brass), build `#9085E9`,
  success `#22C55E`. Never use a tier colour for anything else.
- **Type:**
  - Barnaby's words and all titles: Palatino (`.serif`, italic for speech).
  - UI: Segoe UI.
  - Code and the trace: Cascadia Mono / Consolas (`.mono`).
  - The 2009 system: Verdana / Trebuchet, via `shop2009()`.
- **Motion:** calm, like a good butler.
  - Entrances use `show()` (easeOutExpo, 0.4–0.6 s), with 60–120 ms staggers.
  - Slow scene drift (`drift: .02`).
  - Springs (`pop`) only for button presses and for the moment a new tool appears.
  - Nothing frantic, except the tab pile-up in A, which should feel overwhelming.
- **Contrast is the joke:** the crusty 2009 window (bevels, Verdana, IE7) next to Barnaby's dark, brass display.
- **Captions:** at most one per scene, only in moments without speech, held at least 3 words per second.
  Keep the bottom 160 px clear while one is up.
- **Speech on screen:** spoken lines appear as text too. Barnaby's lines type out in his display (`hud.say`) or as a
  `line()` block, timed to the voice line's real length (`cues.json → voice`, durations in
  `audio/voice/manifest.json`; type at roughly the speaking rate, about 15 characters per second).
  Human lines use `line()` or `hud.setYou`.

## Cast (voices in `cues.json → voice`)
- Theo Hartley: the nephew who wrote the system in 2009 and leaves on Friday.
- Martin Hartley: the owner, Theo's uncle (voiced by Tani; placeholder Kokoro bm_fable).
- Priya: the new hire, on her first day.
- Barnaby: the butler (always TTS: Kokoro George 75% + Fable 25%, misaki input).

## Scenes

### A · 0–11 · "Nine tabs" (cold open)
- 0.0–0.6: black. 0.6: **bell** (sfx). Then a desk monitor frame fades in.
- 1.0–6.5: nine browser tabs cascade in, each 0.6 s apart, stacking and shrinking until the titles are unreadable:
  "Back Office v2.3", "Supplier portal", "SMS box", "workload.xls", "Invoices", "Parts list", "Email",
  "Bank", "Calendar".
- 1.0–9.5: a small RAM meter in the top-right corner climbs from 38% to 94%, turning brass then red.
- Caption 4.5–10.5: *"Every small business runs on systems nobody has time to rewrite."*
- 10.2–11: the tabs fade out (whoosh at 10.4).

### B · 11–30 · "Theo's handover" (Arrival)
- 11.5: `shop2009()` slides in on the left (x≈110, y≈150, w≈1000). It's the jobs page.
- 12.5–17: on the right, a `terminal({title:'git log'})` types `DATA.gitlog`, **oldest first**, excluding Barnaby's commit:
  "2009-03-14 first version of the shop system!! (bye access database)" … "README: notes for whoever looks after it next. bye x".
- Caption 12–16.8: *"Theo wrote the shop's back office in 2009. On Friday, he leaves."*
- 17.3: Theo's line (`line()`, who: 'Theo'): *"Barnaby, this is the shop's system. Look after them for me."* (4.3 s)
- 20.0: the git terminal fades out; `hud()` appears on the right (x≈1080, y≈120, w≈720), with state "connecting".
- 20.5: the terminal inside the HUD area shows `synapse build --auto --local`, then "Extracted 23 endpoint(s)" at 21.4.
- 21.6–23.6: `endpointMap()` blooms all 23 chips in the HUD (stagger ≈ 0.085 s).
- 24.0: the six starter chips (`DATA.starter`) light brass, with a **chime**.
- 24.3: Barnaby (`hud.say`): *"Twenty-three endpoints, sir. I've started with the six that only read."* (5.3 s)

### C · 30–47 · "Monday" (Meet Martin)
- 30.3–32: a chapter chip "Monday · 8:52am" (brass, top-left).
- 30.0: the shop window is visible full-width-ish (x≈80, w≈1100). 30.5: the HUD slides in over its right edge
  (x≈1000, w≈840), state "listening".
- 31.2: Martin (`hud.setYou('Martin', …)`): *"Which repairs are due tomorrow, and are we short on parts?"* (3.7 s)
- 35.2–38.2: trace rows (read, blue) slide in 0.6 s apart: `jobs_due {day: tomorrow}`, then
  `job_detail 4471`, `4475`, `4478`, `4485`, `4490`. **Tick** sfx on each. State "thinking".
- 38.6: Barnaby says *"Five are due tomorrow. Only one is short: Anika's brake job needs two pairs of pads, and we have one."*
  (7.7 s) State "speaking".
- From 41.0: in the shop window, row 4478 (index 3) gets a soft yellow highlight.

### D · 47–69 · "Unlock"
- 47.6: Martin: *"Order ten pairs, from the usual supplier."* (3.0 s)
- 50.8: trace row (grow, brass): `barnaby · capabilities`.
- 51.2: Barnaby: *"I can't yet, but the system can. There's an ordering endpoint I haven't taken. May I?"* (7.5 s)
- 58.9: `approvalCard({kind:'grow', title:'Unlock POST /api/purchase-orders', detail:'Order more of a part from a supplier.', primary:'Unlock'})`.
- 60.6: the button is pressed (`card.press`, **click**).
- 61.0: a terminal line: `synapse build --auto --local --endpoints "…,POST /api/purchase-orders"` → "rebuilt in 0.38 s".
- 61.6: the purchase-order chip lights brass, with a **chime**.
- 62.6: `approvalCard({kind:'write', title:'Order 10 × Brake pads (Shimano resin) from Madison', primary:'Approve'})`.
- 64.0: Martin: *"Yes."* 64.3: button press (**click**).
- 65.4: the shop window switches to the Purchase Orders tab, and a new row slides in: "3 · Brake pads (Shimano resin, pair) · 10 · Madison · ordered".
- Caption 66.0–68.6: *"Unlock: Synapse had already found it. Barnaby asked, then took it."*

### E · 69–82 · "Compose"
- 69.5–72.0: four identical trace sequences stack quickly, each one row of four chips:
  `job_detail → customer_detail → notify → update_status`, labelled "×1"…"×4".
- 72.4: Barnaby: *"You've had me do these four steps four times today. Shall I make it a single motion?"* (6.0 s)
- 76.4: a terminal: `synapse build --custom -q "hand back a finished bike"` → "Composing MCP tool … 16 s" →
  `finish_bike_and_notify_customer_server.py` (the real output of a hosted Synapse Custom build).
- 78.8: the four rows fuse (collapse) into one glowing row: `finish_bike_and_notify_customer` (brass with a violet
  edge), with a **pop**.
- Caption 79.2–81.8: *"Compose: one verified skill instead of four steps."*

### F · 82–120 · "Build" (centrepiece)
- 82.6: Martin: *"Who's overloaded this week?"* (2.3 s)
- 85.2: Barnaby: *"The system has no notion of workload, sir. I can teach it."* (5.0 s)
- 90.4: an editor/terminal panel opens, titled `worktree · barnaby/api-reports-workload`.
- 90.8–96.3: the added lines of the real diff (`DATA.build.diff`, `+` lines of services.py, then routes_reports.py)
  scroll and type in. **Typing** sfx bed.
- 96.8: a terminal: `python -m pytest -q`. 98.3: `22 passed` in green, with a **success** sfx.
- 99.3: `approvalCard({kind:'build', title:'Add GET /api/reports/workload/{day} to the shop's back office', diff: DATA.build.diff, primary:'Approve and merge'})`.
  Show 12–14 diff lines.
- 102.8: Martin clicks "Approve and merge" (**click**).
- 103.3–105.3: status lines: "merged into main" → "shop restarted" → `synapse build --discover` → "Extracted 24 endpoint(s)".
- 105.8: a new violet chip "GET /api/reports/workload/{day}" appears, with **pop** and **chime**. It's endpoint 24.
- 106.8: trace row (read): `shop · workload {day: today}`.
- 107.3: Barnaby: *"Dev has thirty-one hours booked against twenty. Shall I move the two wheel builds to Priya?"* (6.8 s)
- 114.5: Martin: *"Yes, please."* (1.6 s)
- 116.3–117.3: in the shop window, rows 4471 and 4472 (indices 0 and 1), mechanic column (index 1), flip "Dev" → "Priya"
  with a yellow highlight (`shop.set(r, 1, 'Priya', hl)`), with a **tick** each.
- Caption 116.6–119.8: *"Build: the report Theo never wrote. Tested, approved, live."*

### G · 120–131 · "Priya, day one"
- 120.6: Priya (`line()`): *"What can this system actually do?"* (2.2 s)
- 122.0: a large `endpointMap` with all 24 chips. Exposed ones are brass: the 6 starters + `POST /api/purchase-orders`
  + `POST /api/jobs/{job_id}/assign`. The new one (`GET /api/reports/workload/{day}`) is violet.
- 123.2: Barnaby: *"Twenty-four things. Theo wrote twenty-three; I wrote one more."* (5.0 s)
- Caption 128.4–130.8: *"The departing expert's knowledge, kept."*

### H · 131–146 · "Any repo"
- 131.5: three cards appear, staggered 0.35 s: two repo cards (name, question, real endpoint count) and a wide "Your company" card:
  - "Quorum · offline team memory" · *"Any disputed deadlines?"* · **13 endpoints**
  - "ComfyUI" · *"What GPU is it using, and is anything queued?"* · **28 endpoints**
  - "Your company" · a grid of 40 small system tiles lighting up brass one by one (134–143)
- Caption 131.5–137.5: *"Point Barnaby at any repo."*
- Caption 138–145.5: *"Synapse makes it agent-ready. Barnaby makes it grow."*

### I · 146–160 · "Close"
- 146.5: **bell**. 147.0: the bell icon plus the wordmark "Barnaby" (Palatino, about 150 px) fade in, centred.
- 148.5: Barnaby says, as a title, *"Every system deserves a butler."* (serif, about 64 px; 2.7 s).
- 151.6: *"Even the old ones."* (brass italic, about 48 px; 1.7 s).
- 154.0: a small line: "Built on Synapse · 2nd Brain Labs × Geek Room Vibe-a-thon".
- 155.0–159.5: a tiny disclosure, bottom-left, muted 16 px: "Scenes recreated from a real recorded run. See the README for what's real."
- 158.5–160: fade to black (`Q.setBlack`).
