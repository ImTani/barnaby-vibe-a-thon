# Barnaby: the film (storyboard + style bible) — FROZEN v1

140 s · 1920×1080 · 30 fps. Every key time below is also in `cues.json`. The soundtrack (music, sound effects,
voice lines) is cut to these times, so **don't move key events**. If you must, list the actual times in your report.

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
  `line()` block. Human lines use `line()` or `hud.setYou`.

## Cast (voices in `cues.json → voice`)
- Theo Hartley: the nephew who wrote the system in 2009 and leaves on Friday.
- June Hartley: the owner.
- Priya: the new hire, on her first day.
- Barnaby: the butler.

## Scenes

### A · 0–11 · "Nine tabs" (cold open)
- 0.0–0.6: black. 0.6: **bell** (sfx). Then a desk monitor frame fades in.
- 1.0–6.5: nine browser tabs cascade in, each 0.6 s apart, stacking and shrinking until the titles are unreadable:
  "Back Office v2.3", "Supplier portal", "SMS box", "workload.xls", "Invoices", "Parts list", "Email",
  "Bank", "Calendar".
- 1.0–9.5: a small RAM meter in the top-right corner climbs from 38% to 94%, turning brass then red.
- Caption 4.5–10.5: *"Every small business runs on systems nobody has time to rewrite."*
- 10.2–11: the tabs fade out (whoosh at 10.4).

### B · 11–27 · "Theo's handover" (Arrival)
- 11.5: `shop2009()` slides in on the left (x≈110, y≈150, w≈1000). It's the jobs page.
- 12.5–17: on the right, a `terminal({title:'git log'})` types `DATA.gitlog`, **oldest first**, excluding Barnaby's commit:
  "2009-03-14 first version of the shop system!! (bye access database)" … "README: notes for whoever looks after it next. bye x".
- Caption 12–16.8: *"Theo wrote the shop's back office in 2009. On Friday, he leaves."*
- 17.5: Theo's line (`line()`, who: 'Theo'): *"Barnaby, this is the shop's system. Look after them for me."*
- 20.0: the git terminal fades out; `hud()` appears on the right (x≈1080, y≈120, w≈720), with state "connecting".
- 20.5: the terminal inside the HUD area shows `synapse build --auto --local --smart-names`, then
  "Extracted 23 endpoint(s)" at 21.4.
- 21.5–23.5: `endpointMap()` blooms all 23 chips in the HUD (stagger ≈ 0.085 s).
- 24.0: the six starter chips (`DATA.starter`) light brass, with a **chime**.
- 24.5: Barnaby (`hud.say`): *"Twenty-three endpoints, sir. I've started with the six that only read."*

### C · 27–42 · "Monday" (Meet June)
- 27.3–29: a chapter chip "Monday · 8:52am" (brass, top-left).
- 27.5: the shop window is visible full-width-ish (x≈80, w≈1100). 28.0: the HUD slides in over its right edge
  (x≈1000, w≈840), state "listening".
- 28.5: June (`hud.setYou('June', …)`): *"Which repairs are due tomorrow, and are we short on parts?"*
- 30.0–33.5: trace rows (read, blue) slide in 0.6 s apart: `jobs_due {day: tomorrow}`, then
  `job_detail 4471`, `4475`, `4478`, `4485`, `4490`. **Tick** sfx on each. State "thinking".
- 34.0: Barnaby says *"Five are due tomorrow. Only one is short: Anika's brake job needs two pairs of pads, and we have one."*
  State "speaking".
- 34–41: in the shop window, row 4478 (index 3) gets a soft yellow highlight from 36.

### D · 42–58 · "Unlock"
- 42.5: June: *"Order ten pairs, from the usual supplier."*
- 44.0: trace row (grow, brass): `barnaby · capabilities`.
- 45.0: Barnaby: *"I can't yet, but the system can. There's an ordering endpoint I haven't taken. May I?"*
- 47.0: `approvalCard({kind:'grow', title:'Unlock POST /api/purchase-orders', detail:'Order more of a part from a supplier.', primary:'Unlock'})`.
- 49.5: the button is pressed (`card.press`, **click**).
- 50.0: a terminal line: `synapse build --auto --local --endpoints "…,POST /api/purchase-orders"` → "rebuilt in 0.38 s".
- 50.5: the purchase-order chip lights brass, with a **chime**.
- 52.0: `approvalCard({kind:'write', title:'Order 10 × Brake pads (Shimano resin) from Madison', primary:'Approve'})`.
- 53.6: June: *"Yes."* 53.8: button press (**click**).
- 55.0: the shop window switches to the Purchase Orders tab, and a new row slides in: "3 · Brake pads (Shimano resin, pair) · 10 · Madison · ordered".
- Caption 55.5–57.8: *"Unlock: Synapse had already found it. Barnaby asked, then took it."*

### E · 58–70 · "Compose"
- 58.5–61.0: four identical trace sequences stack quickly, each one row of four chips:
  `get_job → get_customer → notify → set_status`, labelled "×1"…"×4".
- 61.5: Barnaby: *"You've had me do these four steps four times today. Shall I make it a single motion?"*
- 64.0: a terminal: `synapse build --custom -q "hand back a finished bike"`.
- 65.0: the four rows fuse (collapse) into one glowing row: `hand_back_bike` (brass with a violet edge), with a **pop**.
- Caption 67.2–69.8: *"Compose: one verified skill instead of four steps."*

### F · 70–102 · "Build" (centrepiece)
- 70.5: June: *"Who's overloaded this week?"*
- 72.0: Barnaby: *"The system has no notion of workload, ma'am. I can teach it."*
- 74.0: an editor/terminal panel opens, titled `worktree · barnaby/api-reports-workload`.
- 74.5–80.0: the added lines of the real diff (`DATA.build.diff`, `+` lines of services.py, then routes_reports.py)
  scroll and type in. **Typing** sfx bed.
- 80.5: a terminal: `python -m pytest -q`. 82.0: `22 passed` in green, with a **success** sfx.
- 83.0: `approvalCard({kind:'build', title:'Add GET /api/reports/workload/{day} to the shop's back office', diff: DATA.build.diff, primary:'Approve and merge'})`.
  Show 12–14 diff lines.
- 86.5: June clicks "Approve and merge" (**click**).
- 87.0–89.0: status lines: "merged into main" → "shop restarted" → `synapse build --discover` → "Extracted 24 endpoint(s)".
- 89.5: a new violet chip "GET /api/reports/workload/{day}" appears, with **pop** and **chime**. It's endpoint 24.
- 90.5: trace row (read): `shop · workload {day: today}`.
- 91.0: Barnaby: *"Dev has thirty-one hours booked against twenty. Shall I move the two wheel builds to Priya?"*
- 97.6: June: *"Yes, please."*
- 98.4–99.4: in the shop window, rows 4471 and 4472 (indices 0 and 1), mechanic column (index 1), flip "Dev" → "Priya"
  with a yellow highlight (`shop.set(r, 1, 'Priya', hl)`), with a **tick**.
- Caption 98.5–101.8: *"Build: the report Theo never wrote. Tested, approved, live."*

### G · 102–112 · "Priya, day one"
- 102.5: Priya (`line()`): *"What can this system actually do?"*
- 104.0: a large `endpointMap` with all 24 chips. Exposed ones are brass: the 6 starters + `POST /api/purchase-orders`
  + `POST /api/jobs/{job_id}/assign`. The new one (`GET /api/reports/workload/{day}`) is violet.
- 105.0: Barnaby: *"Twenty-four things. Theo wrote twenty-three; I wrote one more."*
- Caption 109.2–111.8: *"The departing expert's knowledge, kept."*

### H · 112–127 · "Any repo"
- 112.5: four cards appear in a 2×2 grid, staggered 0.35 s, each with a repo name, a question and a real endpoint count:
  - "Quorum · offline team memory" · *"Any disputed deadlines?"* · **13 endpoints**
  - "ComfyUI" · *"What GPU is it using, and is anything queued?"* · **28 endpoints**
  - "clipd · game clipper" · *"Clip that."* · "control API + hosted build"
  - "Your company" · a grid of 40 small system tiles lighting up brass one by one (115–124)
- Caption 112.5–118.5: *"Point Barnaby at any repo."*
- Caption 119–126.5: *"Synapse makes it agent-ready. Barnaby makes it grow."*

### I · 127–140 · "Close"
- 127.5: **bell**. 128.0: the bell icon plus the wordmark "Barnaby" (Palatino, about 150 px) fade in, centred.
- 129.5: Barnaby says, as a title, *"Every system deserves a butler."* (serif, about 64 px).
- 132.0: *"Even the old ones."* (brass italic, about 48 px).
- 134.0: a small line: "Built on Synapse · 2nd Brain Labs × Geek Room Vibe-a-thon".
- 135.0–139.5: a tiny disclosure, bottom-left, muted 16 px: "Scenes recreated from a real recorded run. See the README for what's real."
- 138.5–140: fade to black (`Q.setBlack`).
