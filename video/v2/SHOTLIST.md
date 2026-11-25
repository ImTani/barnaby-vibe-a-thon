# Barnaby: the shot plan (v2.2, directed)

This is the direction for the final film. The Blender, film and sound work all build from this file. It answers the
director's notes on the first animated cut:

- "Way too fast, especially before the 20-second mark: those scenes need to feel lived in."
- "Random zoom-ins."
- "Martin's lines are very fast."
- "Pacing is really important."

## v2.3 revisions: the director on review cut 2 (these override anything below)
1. **The camera feels handheld and cinematic, not a tripod.**
   - **Room shots:** a subtle operator's handheld: low-frequency drift (about ±0.5% position, ±0.2° roll, 2–5 s periods, never jittery), done over a 4% overscan on sequences and stills alike.
   - **Motivated pans and tilts** on wide plates. A 2D pan across a wide high-res render is optically a real pan.
   - **Screens stay locked** (they're the person's view); Barnaby's worlds stay still.
2. **More cinema inside the one-desk constraint:**
   - **Hero inserts with shallow focus:** Theo's WORLD'S OKAYEST NEPHEW mug in lamplight, the key, Martin's glasses, the sticky note, drawer 1, Priya's helmet.
   - **Rack focus** from a foreground prop to the monitor's glow.
   - **Angles:** low over the keyboard, past the lamp, the empty chair from behind, the window with rain.
3. **Transitions between desk states** (no plain fades or white-flash time-lapses):
   - **Thursday night → Monday:** a match cut on the mug. Theo's OKAYEST NEPHEW mug in lamplight; the lamp clicks off; dark; the same framing at dawn, light rising, Martin's mug in its place.
   - **Monday morning → afternoon:** a light wipe, the sun's shaft sweeping across the frame.
   - **Afternoon → dusk:** the lamp clicks on in a blue room (as planned).
   - **Monday dusk → Tuesday:** a match cut on the chair. The empty chair at dusk, then the same chair in morning sun with Priya's helmet hanging on it.
   - **Tuesday shop → Lisbon:** a match cut, desk to desk. The shop desk and the Lisbon desk in the same composition: the shop's greens become Lisbon's whites.
4. **The "same butler" triptych (6.10) is cut;** it read as a collage. Barnaby's line plays over Martin's plan, with the new Workload room's hours (Dev 31 of 20).
5. **Sound:**
   - beds much lower, the opening especially;
   - the crowd bed removed everywhere;
   - effects targeted: each motivated sound clear and short, nothing decorative;
   - **the repetition lands**: each of the four hand-back steps (the job, the customer, a text, the status) gets a small chime, the same four-note figure each time, quicker each time. The composed passage plays the four notes as one chord: the steps become one.
   - **Levels:** a per-category table of peaks and averages in SOUND.md.
6. **Barnaby is faster** (185 words a minute, +17%) and "me" is no longer mispronounced. His voice may move to ElevenLabs.
7. **Titles and a product end card, designed properly** (DESIGN.md is the brand):
   - a typographic hierarchy on a grid, brass as the one accent, the real mark;
   - the titles over the two desks, then a clean product card: what Barnaby is, the four growth steps, Built on Synapse, the repo, and the disclosures in small print.
8. **Timing will be re-derived from the real voice takes** (word-level alignment) when they arrive. Marks that sit on a word (the tab-five click, the "Fussy." click) follow the words.

## What went wrong in the first cut
- **The pace came from conversation research, not film.** Telephone-speed gaps (200–300 ms) and conversational speaking
  rates were squeezed to a 3-minute cap, so the picture only got the time the dialogue left over.
- **Every still got a camera move so nothing would sit static.** Most of those moves had no reason to happen: a push into
  a pen pot is the camera fidgeting, not looking.
- **The whole film ran at one tempo.** Good pacing varies:
  - slow where we are getting to know a place or feeling something (the opening, the handover, the goodnights);
  - brisk where a pattern repeats (the hand-backs);
  - a held breath before a decision (the click).

## 1. The grammar: three layers, one rule
| Layer | What it is | How it's shot |
|---|---|---|
| **The room** (Blender diorama) | The real world. People are never seen; we hear them (a sigh, a chair, keys, steps) and see their things (mug, glasses, helmet). | On a tripod at seated eye height. Held frames. At most one slow, motivated move per room scene. Shallow depth of field on close props. |
| **The screen** (HTML look-dev) | What the person sees. Their cursor is their hand. | Full frame and locked. Held long enough to read. Cursor and typing at human speed. |
| **Barnaby's world** (hologram, floor plan, bench) | Barnaby's mind made visible, a different look for each person. | The camera holds the plan; Barnaby moves inside it. Framed once per beat; one reframe only when the story points somewhere new. |

**The rule:** every scene opens in **the room**, with the light saying what time it is, then goes in (room → screen → world)
as the conversation deepens, and comes back out to **the room** for its last beat. Breathe out, go in, breathe out.
- **Going in is always the same move.** The first time each day, a push into the monitor: the room's last frame is framed on the screen, and the live screen is corner-pinned onto the monitor's glass and grows to full frame (about 0.6 s, eased). After that, cuts.
- **Screen to world:** Barnaby's own window opens out of the screen (his bell mark leads).

## 2. The lighting arc: the day told by light
| When | Light | Feeling |
|---|---|---|
| Thu 21:47, night | Rain on the window, the lit window opposite. A warm lamp pool (2700 K) on the desk, cool monitor spill, everything else falls into dark. | Late, alone, a last week. |
| Thu, lamp off | Only the monitor's glow, then nearly nothing. | An era ends. |
| Time-lapse | Dark → blue dawn → Monday's overcast morning raking in from the window. Theo's things are gone in the bloom; Martin's appear. | Time passes, someone new. |
| Mon 08:52 | Soft, cool daylight from the window; lamp off. | A Monday, plain. |
| Mon about 14:30 | Low winter sun breaks through: a warm shaft slides across the desk. | Busy, alive. |
| Mon 16:08, dusk (**new lighting state**) | Window deep blue, rain stopped. **The lamp is on again: Martin switched it on.** | A rhyme with Theo's nights: same desk, new person. |
| Tue 08:34 | Crisp, clear morning after the rain; brighter than Monday. Priya's helmet on the chair. | A first day. |
| Lisbon, Tue 09:39 | High-key Mediterranean morning: warm whites, azulejo blues, sun on the desk. | A new life, open. |
| Shop 18:40 / Lisbon 20:07 | Night at both. Monitors fall asleep, a brass bell glyph on each; the shop's sleep LED amber. | Goodnight. |

## 3. Post and finishing (one consistent finish)
- **Room shots:**
  - a very fine film grain (about 2/255, re-seeded per frame, deterministic) and a soft vignette (corners about −12%);
  - Blender's bloom on the practical lights only (lamp, monitor, LEDs), and depth of field on close props;
  - nothing else: no colour filters on top of the lighting. The light design *is* the grade.
- **Screen and world shots:** clean, with no grain or vignette, because legibility comes first.
- **Matching:** room sequences and stills of the same set must match exposure (the same per-shot offsets as the approved stills). Never mix a sequence and a still inside one shot.
- **Transitions:**
  - hard cuts within a scene;
  - time jumps cut on a **sound bridge**: the next place's sound starts 0.6–1.0 s before the picture changes;
  - dissolves only for the night montage in scene 9 and the titles.
- **Titles:** Barnaby's wordmark in his serif, "Every system deserves a butler.", then "Even the old ones." in brass italic. They fade in over 1 s and hold; the credit line and the staged-scenes note sit small at the bottom.

## 4. Sound against picture
- **Sound leads picture at every time jump.** Rain before the first light; the shutter coming down before the
  handover's quiet; the workshop morning before Monday; the repair-stand clunk before "Sofia's bike's done"; the
  lamp switch before dusk; the Tuesday bustle; the Lisbon street; rain again for goodnight.
- **The music is Barnaby.** No music until the bell, when he arrives. It thins under "Who's got too much on this
  week?", builds to the click, lifts on the tab change, settles for Priya, brightens for Lisbon and resolves on the last
  bell. **No music under the lamp-off**: rain only.
- **Silences are written in:**
  - "Seventeen years." 1.6 s;
  - after "Look after them for me." 1.0 s;
  - "Noted." → the key 1.3 s;
  - the lamp click → dark 1.6 s;
  - before "Fussy." 0.6 s;
  - after "Show-off." 1.6 s.
- **Speaker changes are film beats:**
  - Barnaby answers promptly (0.45 s: attentive, never interrupting);
  - Martin answers an offer only after reading the card (0.8 s);
  - a comic button ("Fussy.", "Show-off.", "Noted.") gets a set-up pause and a hold after it.
- **Implied people:** a chair creak and a sigh when Martin sits (scene 3); the workshop shutter (scene 2); keys and a coat (scene 9); a door (scene 9, Lisbon).
- **Pace:** Martin speaks at 148 words a minute (tired 136, brisk 157), Barnaby 158, Theo 172, Priya 165. These are film delivery speeds, not phone-call ones.

## 5. The shots
Durations are approximate; `video/v2/audio/layout.py` sets them from the rendered voices.
Source: **B-seq** = Blender sequence, **B-still** = Blender still (held; at most 2% drift), **S** = screen look-dev, **W** = world comp.

### 1 · Nine tabs: Thu 19 Nov, 21:47 (about 30 s): slow, lived in
| # | Picture | Camera | Sound and lines | Dur | Source |
|---|---|---|---|---|---|
| 1.1 | Black, then the back office comes up: the lamp pool, the glowing monitor, the chair, a mug, rain on the window. | Held wide from the doorway for about 6 s, then one slow eased approach to the desk, ending framed on the monitor. | Rain from black, the PC fan, a radio far off through the workshop door. | 13 s | B-seq `s1_open` |
| 1.2 | Into the screen: the nine-tab desktop on the monitor grows to full frame. | Corner-pin push | A hard-drive chatter. | 0.6 s | B quad + S |
| 1.3 | Nine tabs clicked through at a person's pace; the CPU and RAM needles climb with each. | Locked | Tab clicks, the drive. | 7 s | S |
| 1.4 | The cursor stops. | Locked | **Martin** (o.s., the workshop, tired): "Theo — where's the parts list again?" | 3 s | S |
| 1.5 | Tab four (wrong), then tab five: the parts list. | Locked | **Theo**: "Tab four. No — five." | 2 s | S |
| 1.6 | The spanner icon in the page header. | **Motivated push** to the spanner, eased over 1.8 s, then held. | **Theo** (a beat, fond): "It's the one with the spanner." The radio clicks off o.s.; the shutter starts to come down. | 4 s | S |

### 2 · The handover: Thu night (about 40 s): quiet, then Barnaby
| # | Picture | Camera | Sound and lines | Dur | Source |
|---|---|---|---|---|---|
| 2.1 | The 2009 photo: young Theo and Martin outside the shop. | Very slow push (memory: the one move) | The shutter finishes (o.s.): Martin has gone home. Rain. | 3.2 s | B-still `photo_2009` |
| 2.2 | The corkboard calendar: Friday 20th circled, "Theo's last day". | Held | Rain. | 2.7 s | B-still `x_board_night` |
| 2.3 | The desk at night, half packed (the box). | Held | **Theo** (quietly): "Seventeen years." Then 1.6 s of rain. | 4 s | B-still `02_medium_night` |
| 2.4 | He closes the tabs one by one; the needles fall back; the empty desktop. | Locked | Tab closes, slower than they opened. | 5 s | S |
| 2.5 | Barnaby's window opens on the desktop: the bell. | Locked | **The bell.** The music enters, warm guitar. | 1.9 s | S |
| 2.6 | Theo's hologram: Synapse reads the building room by room; endpoints appear; six light up (read-only). | Held | **Theo**: "Right. Barnaby — this is the shop's system. I wrote it when I was fourteen, so be kind. Look after them for me." (1.0 s) **Barnaby**: "Twenty-three endpoints, sir. I've taken the six that only read — nobody's given me any keys yet." | 15 s | W |
| 2.7 | The same, modest on the 2009 PC: Barnaby's small window, "The six I've taken (read-only)". | Locked | (Barnaby's line ends) | 3 s | S |
| 2.8 | The desk at night: the lamp, the empty chair. | Held | **Theo** (dry, smiling): "It's Theo. And don't call my uncle sir — he'll unplug you." **Barnaby**: "Noted." | 5 s | B-still `02_medium_night` |
| 2.9 | The keyboard: the key with its BACK OFFICE tag drops on, settles. Hold. The lamp clicks off; the room drops to the monitor's glow. Hold in the dark. | Slow push toward the key (the move), then held | The music resolves before the key. A small metal tap, the lamp click, then rain only. | 6 s | B-seq `s2_key_lamp` |

### 3 · Monday: Mon 23 Nov, 08:52 (about 30 s)
| # | Picture | Camera | Sound and lines | Dur | Source |
|---|---|---|---|---|---|
| 3.1 | Time-lapse: dark → dawn → Monday. Daylight rakes across the desk; Theo's things go in the bloom, Martin's arrive (mug, reading glasses, rag, job card). | Held | A soft swell; the workshop morning fades in (radio, tools). | 5.5 s | B-seq `s3_timelapse` |
| 3.2 | The Monday desk. | Held | A chair creaks, a sigh (Martin sits). | 1.5 s | (end of `s3_timelapse`) |
| 3.3 | Into the screen: the Back Office with the clock gadget readable, 08:52 Monday 23. | Corner-pin push, then locked | **Martin** (sitting, a sigh): "Right. Barnaby, is it?" **Barnaby**: "Good morning, Martin." | 4 s | S |
| 3.4 | Martin's floor plan: the whole shop. Barnaby walks the workshop floor, then up to the back office (08:53). | Plan held; one gentle reframe to the back-office wing at the callout | **Martin** (brisk): "What's due tomorrow — and are we short on anything?" **Barnaby**: "Five bikes due tomorrow. Only Anika's is a problem — her brakes need two pairs of pads, and we've one left." The pads callout (08:54) appears at drawer 1. | 13 s | W |
| 3.5 | Back-office drawer 1 slides open: one pair of pads. | Held, shallow focus | The drawer slides. | 3 s | B-seq `s3_shelf` |

### 4 · A key: Mon 08:55–09:04 (about 25 s)
| # | Picture | Camera | Sound and lines | Dur | Source |
|---|---|---|---|---|---|
| 4.1 | The plan. Barnaby walks to the back door (locked; ordering lives there); the key icon. The card slides in: "Let Barnaby order parts from your suppliers" (what it means, what stays locked, each time). | Held | **Martin**: "Order ten from Madison, then." **Barnaby**: "I can't order parts myself yet — but Theo built the system a way to. Shall I take that on?" (0.8 s: he reads) **Martin**: "Go on, then." | 11 s | W |
| 4.2 | The cursor goes to Allow and clicks; the key turns in the back-door lock; the door's pip fills; the engine line ticks (rebuilt with 1 more capability). | **Motivated push** into the back door | A click, a real lock turning, the bell's soft confirm. | 2.5 s | W |
| 4.3 | The plan. | Held | **Barnaby**: "Ten pairs from Madison, at six pounds fifty a pair. Shall I?" **Martin**: "Yes." | 5 s | W |
| 4.4 | Purchase Orders: order 3 slides in, highlighted. | Locked; held 3 s | A click, a soft pop. The afternoon workshop sound comes in under the last second. | 3.5 s | S |

### 5 · The same four steps: Mon about 14:30 (about 35 s): brisk, rhythmic
| # | Picture | Camera | Sound and lines | Dur | Source |
|---|---|---|---|---|---|
| 5.1 | The Monday desk in afternoon light: a warm shaft of low sun slides across it. | Held | The repair-stand clunk (o.s.), then **Martin** (busy): "Barnaby — Sofia's bike's done." | 4 s | B-seq `s5_afternoon` |
| 5.2 | The plan, workshop wing. Two quick cards (text customers, mark bikes ready); the cursor clicks both. | Held | **Barnaby**: "I'll need to text her and mark it ready. May I?" **Martin**: "Go on." | 6 s | W |
| 5.3 | One continuous shot: Barnaby walks the four stops (the job, the customer, a text, the status) from Ravi's stand. Clunk: the same walk, quicker. Clunk: quicker still. The same dotted path is traced three times. | Plan held | Steps quicken. **Martin**: "Kwame's." … "And Jana's." | 7 s | W |
| 5.4 | The passage draws itself: "Hand back a bike". The engine line: composed from Theo's own functions. | **Motivated slow push** as it forms | **Barnaby**: "That's three bikes handed back, and the same four steps each time. Shall I make it one?" **Martin**: "Can you?" **Barnaby**: "Give me a moment." A soft bell. | 10 s | W |
| 5.5 | A ring at **Dev's** stand; Barnaby takes the passage in one step. | Held | Clunk. **Martin**: "Tom's Brompton." **Barnaby**: "Tom's been texted, and it's marked ready." Held 1.3 s; the lamp switch clicks on (the next scene) under the cut. | 5 s | W |

### 6 · A room Theo never built: Mon 16:08–16:21 (about 60 s): the heart; a held breath, then release
| # | Picture | Camera | Sound and lines | Dur | Source |
|---|---|---|---|---|---|
| 6.1 | **Dusk.** We cut into a deep-blue room; half a second later the lamp clicks on (Martin's hand, o.s.): the same desk as Theo's nights, Martin's things on it. | Held | The lamp click. A quieter workshop. Then **Martin** (tired, thinking aloud): "Who's got too much on this week?" | 4.5 s | B-seq `s6_lamp_on` (new: the lamp comes on in a blue room), then B-still `06_medium_dusk` |
| 6.2 | The sticky note on the bezel, in Theo's hand. | Held, shallow focus | **Barnaby**: "The system can't tell me — there's no report for it. Theo always meant to write one." | 3 s | B-still `x_sticky_dusk` (new) |
| 6.3 | Reports (coming soon!!) with the under-construction sign. | Locked, held for the joke | (Barnaby's line ends) | 2.5 s | S |
| 6.4 | The dusk desk. | Held | **Barnaby**: "I could write it, if you like." **Martin** (surprised): "You can do that?" **Barnaby**: "With your say-so. I'll work on a copy — nothing changes until you've seen it." | 9 s | B-still `06_medium_dusk` |
| 6.5 | The change: code written line by line; then the checks run, 11 → 22 passed, one by one. | Locked | Keyboard foley; the music starts to build; the checks' ding. | 6.5 s | S |
| 6.6 | Martin's plan with the explanation card: "Add a weekly workload report" (what it does, what it reads, Theo's checks, if you change your mind). Mid-line, a cut to Martin's reading glasses on the desk at dusk, then back to the card. | Held | **Barnaby**: "Done. It adds up each mechanic's hours, the way Theo's notes count them. It only reads, and all of Theo's checks still pass. Shall I add it?" | 10 s | W + B-still `x_glasses_dusk` (new) |
| 6.7 | The card; the cursor drifts toward Add it. | Held | **Martin**: "Add it." **Barnaby**: "That one needs your click, Martin. I don't change the system on a word." (0.6 s) **Martin** (dry): "Fussy." The click lands on "Fussy." | 7 s | W |
| 6.8 | Theo's system reloads; the tab "Reports (coming soon!!)" becomes "Reports". | Locked | **The music lifts on the tab change.** | 1.8 s | S |
| 6.9 | The new room appears on the plan: Workload, with its NEW sticker. | **Motivated push** to the new room | A soft bell. | 2.5 s | W |
| 6.10 | The same event through all three: Theo's hologram, Martin's plan, Priya's bench. | Held ≥ 4 s: it's the film's thesis | **Barnaby**: "Dev's carrying thirty-one hours against his twenty. Priya starts tomorrow — shall I give her the two wheel builds?" **Martin**: "Good idea." | 9 s | W |
| 6.11 | The jobs page: two rows change from Dev to Priya. | Locked; held 3 s | A soft pop. The Tuesday bustle comes in under the last second. | 3.5 s | S |

### 7 · Priya, day one: Tue 24 Nov, 08:34 (about 25 s)
| # | Picture | Camera | Sound and lines | Dur | Source |
|---|---|---|---|---|---|
| 7.1 | The Tuesday desk: crisp sun, Priya's helmet on the chair. | Held | The bustle. After 2.4 s, **Priya** (dry): "So you're why I've got two wheel builds on my first day?" | 5 s | B-still `05_medium_tuesday` |
| 7.2 | Priya's bench: the two job tags (4471, 4472) slide on. | Held | **Barnaby**: "Guilty. Dev had thirty-one hours booked. You had none." | 4 s | W |
| 7.3 | The bench: her jobs, the parts (spokes short), who's collecting, then Theo's README note. | Held; one reframe to the note | **Priya**: "Fair. What else can this thing do?" **Barnaby**: "Your jobs, the parts they need, who's collecting what. And Theo left you a note: never trust the stock count on a Friday." | 11 s | W |
| 7.4 | Back to the Tuesday desk. | Held 1.6 s | **Priya** (a small laugh): "Noted." The Lisbon street comes in under the cut. | 3 s | B-still `05_medium_tuesday` |

### 8 · Any house: Lisbon, Tue 09:39 (about 35 s): open, bright
| # | Picture | Camera | Sound and lines | Dur | Source |
|---|---|---|---|---|---|
| 8.1 | Theo's Lisbon studio in morning sun: azulejos, plants, two monitors. | **Motivated slow approach** (arriving at his new life) | The street below, a tram far off. The music brightens. | 3.4 s | B-seq `s8_lisbon_day` |
| 8.2 | Espresso and a pastel de nata beside his keyboard. | Held | A cup set down. | 1.8 s | B-still `x_lisbon_detail_day` |
| 8.3 | Into the main monitor: the real Barnaby app in a browser tile. What he can do → Connect a system: he types "quorum", pastes the repo path, types the URL (about 8 characters a second), and moves to Connect. | Corner-pin push, then locked | Modern keyboard typing, a click. | 7.5 s | S (real-app captures) |
| 8.4 | Barnaby's log streams in the tmux pane: Synapse reads Quorum, 13 endpoints. | Locked | **Theo**: "Barnaby — new job. This is the crew's memory." | 4 s | S |
| 8.5 | Theo's Lisbon world, fully himself. | Held | **Barnaby**: "Thirteen endpoints, sir — and two deadlines in dispute. Shall I flag them?" **Theo** (dry): "Still Theo." **Barnaby**: "Theo." | 8 s | W |
| 8.6 | The studio monitor: ComfyUI, the queue moving, three jobs. | Locked | **Theo** (nodding at it): "And the render box?" **Barnaby**: "Twenty-eight endpoints. It's on the big card, and three jobs are queued." | 7 s | S |
| 8.7 | The Lisbon desk. | Held 1.6 s | **Theo** (grinning): "Show-off." Rain comes in under the cut. | 3 s | B-still `lisbon_02_medium_day` |

### 9 · Goodnight: Shop 18:40, Lisbon 20:07 (about 27 s): slow
| # | Picture | Camera | Sound and lines | Dur | Source |
|---|---|---|---|---|---|
| 9.1 | The shop desk at night: the lamp off, the monitor still on; it falls asleep (the bell glyph, the LED amber). | Held | Rain, keys, a coat. **Martin** (o.s., leaving): "Night, Barnaby." **Barnaby**: "Goodnight, Martin." A door. | 7 s | B-seq `s9_shop_night` |
| 9.2 | Slow dissolve to the Lisbon desk at night: the monitors dim to sleep, a bell glyph on each. | Held | A quiet street. **Theo** (o.s., leaving): "Night, Barnaby." **Barnaby**: "Goodnight, Theo." A door. | 6 s | B-stills `lisbon_03_medium_night` on → asleep (crossfade = the light dimming) |
| 9.3 | Dissolve to the two desks side by side, both asleep, a bell on each screen. | **Slow matched push** (the last move) | The real bell, once. | 3 s | B-stills `x_close_half_*` at 2× |
| 9.4 | Titles over the two desks: Barnaby / Every system deserves a butler. → Even the old ones. → credit and the staged-scenes note. | (push continues) | The music resolves. | 10 s | titles |

## 6. Runtime
About 4:15–4:30 at this pace; the exact figure comes from the layout once the slower voices render. The brisk
hand-back sequence and the held openings are both deliberate. If it has to come down, cut whole beats (for example 2.7
or 8.2), never the air around lines.

## 7. Who does what
- **Blender:**
  - sequences: `s1_open` (long), `s2_key_lamp`, `s3_timelapse`, `s3_shelf`, `s5_afternoon`, **`s6_lamp_on` (new: a dusk lighting state, lighting only)**, `s8_lisbon_day`, `s9_shop_night`;
  - stills at 2560×1440 (or 2× for the halves): `06_medium_dusk`, `x_sticky_dusk`, `x_glasses_dusk`, `lisbon_03_medium_night` asleep, and `x_close_half_*` at 2×;
  - for `s1_open`, the Monday desk (end of `s3_timelapse`) and `lisbon_02_medium_day`, export the monitor glass's four corners in the frame, for the corner-pin push.
- **Film:**
  - the three-layer grammar;
  - the corner-pin push into the screen;
  - held framing (no unmotivated moves);
  - human-speed cursor and typing;
  - grain and vignette on room shots only;
  - dissolves only in scene 9;
  - the shots above, on the new cue sheet.
- **Sound:**
  - the new cue sheet;
  - the new effects: the radio off, the shutter, the chair and sigh, the lamp-on click, a cup set down, a coat, doors;
  - the sound bridges at every time jump;
  - no music under the lamp-off;
  - the music re-fitted to the new length.
