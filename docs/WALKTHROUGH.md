# Recording the walkthrough (the real app, round 3)

A live, unscripted-looking run of the real app: about three minutes once the waits are cut. You speak (or type),
Barnaby answers aloud, and the screen shows his app beside Theo's 2009 shop. The beats follow the film's order: arrive,
ask, order the pads, hand back four bikes (the fourth in one step), find out who's overloaded, move the work.
Long waits (the Build takes about 90 s, Compose about 30 s) are cut in the edit, so don't fill them: let them run.

Barnaby is a real agent, so his wording changes from run to run. The quotes below come from the real run on
25 Nov (`scripts/demo_check.py`, 16/16). Labels in "quotes" are the app's exact text (`ui/app.js`, `ui/index.html`).

## 1. Start the shop and Barnaby

Terminal 1, from the repo root (Git Bash; in PowerShell use `. scripts/env.ps1` instead of the first line):

```bash
source scripts/env.sh                                   # keeps every cache inside the repo
.venv/Scripts/python scripts/demo_reset.py              # fresh shop + Theo's history; Barnaby forgets everything
.venv/Scripts/python -m barnaby serve                   # the app on http://127.0.0.1:8700
```

You don't start the shop yourself. Barnaby starts it on http://127.0.0.1:8101 when you introduce it (beat 1).
`demo_reset.py` sets the shop's "today" to the Monday of the current week. To get the film's dates (Monday 23 Nov,
so "tomorrow" is Tue 24 Nov), run it with `--today 2026-11-23`.

Terminal 2, for voice (skip it if you'll type):

```bash
source scripts/env.sh
runtime/voice/.venv/Scripts/python voice/bot.py -t webrtc --port 7860
```

By default, listening uses the sherpa server at `SHERPA_WS_URL`. Set `BARNABY_LISTEN=whisper` in `.env` for local
Whisper.

Check `.env` (copy it from `.env.example`):
- `SYNAPSE_API_KEY` is needed for beat 5 (Compose: hosted Synapse Custom mode). Without it, hand Tom's bike back the
  long way and skip the single step.
- The worker runs on your local Claude Code login by default. `BARNABY_WORKER_BACKEND=api` uses `ANTHROPIC_API_KEY`
  instead.

## 2. Set up the screen

- Open **http://127.0.0.1:8700**. Round 3 is the default look, so you need no `?skin=`. It's light by default; the
  moon button in the top bar (or `?theme=dark`) switches to dark, and the choice is remembered. Don't record
  `?skin=classic` (the old look) or `?mock=1` (a recorded replay, not the live app).
- Put the app about 1440 px wide on the right. On the left, put a browser window that you'll point at the shop
  (http://127.0.0.1:8101) once Barnaby has connected it. The shop's pages refresh themselves.
- Record your mic **and** the system audio (Barnaby's voice comes out of the browser tab).
- **Hold Space to talk** after clicking an empty part of the page. If the cursor is in the text box, Space types a
  space. The brass **"Hold to talk"** pill works too; while you hold it, it reads "Listening…". If the voice bot
  isn't running, a note says "Voice isn’t available just now"; type instead.
- To approve a change by voice, say **"Yes"** while holding Space. Typing "yes" doesn't approve anything (Barnaby is
  still busy with the request and replies "One moment, I am still on the last request."), so click the button instead.
- Do a sound check: hold Space and say "Barnaby, are you there?". Then reset (section 5) so the recording starts clean.

### What you'll see before you start

| Where | What it says |
|---|---|
| Top bar | the bell-with-a-bow-tie mark and "Barnaby"; "No system yet ⌄"; the status "At your service"; "What he can do"; the light/dark switch; the side-panel switch |
| Middle | his mark, "Good day. What can I look into?", "Hold the button below, or the space bar, and ask out loud.", "Or type your question and press Enter.", and a brass "Connect a system" button |
| Side panel | **System:** "No system connected yet". **Keys you gave him:** "None yet. He only looks things up." **Made with your say-so:** "Nothing yet." **Talking to him:** "Hold to talk · Space", "A spoken yes · for orders and changes", "Keys and new pieces · a click". Then "What he can do ›" |
| Composer | "+" (Connect a system), "Ask Barnaby anything, or hold the space bar and talk", a "Space" key hint, "Hold to talk" |

### How the round-3 app shows his work

- **His words** are in an upright serif, with his mark in the margin. Your words sit on the right, in a bubble.
- **While he works**, one **live line** shows his mark ringing, what he's doing right now ("Looking at repair job
  4475") and a running timer. The status in the top bar says the same thing.
- **When he's done**, the work collapses into **one grey line** in plain words, with how long it took. For example:
  "Looked at repair jobs due on Tue 24 Nov, parts at or below their reorder level and 5 repair jobs 7s ›". Click it to
  open the steps; each step has **Details** (the technical record).
- **Cards** appear inline whenever he needs your say-so. Each card has a kind line, then the facts, then the folded
  **"Technical detail"**, and at the bottom how you may answer and the buttons:

| Card | Kind line | Buttons | How you answer it |
|---|---|---|---|
| A change to your records (an order, a text, a job moved) | "A change to your records" | "Decline" · "Approve" | "Or just say “yes”." |
| A new key (Unlock) | "A new key" | "Not now" · "Yes, go ahead" | "A new key needs a click, not a spoken yes." |
| A shortcut (Compose) | "A shortcut" | "Not now" · "Yes, go ahead" | "A new step like this needs a click, not a spoken yes." |
| A new piece (Build) | "A new piece for the system" | "Not now" · "Yes, add it" | "A change like this needs a click, not a spoken yes." |

- Every answer you give is kept in the thread as one line: "**You said yes**: …" or "**You said not now**: …".
- The status reads "Waiting for your say-so" while a card is open.

## 3. The run (say these, or your own words)

Times are from the 25 Nov run, which approved everything automatically. Your clicks and yeses add to them.

| # | You | What happens on screen | Expect |
|---|---|---|---|
| 1 | *"Barnaby, this is the shop's system. Look after them for me."* | The live line reads the shop. Then a "Connected" note appears: "The shop's back office: it can do 23 things. To start, Barnaby may use the 6 that only look something up." The top bar shows "The shop's back office"; the side panel shows "He can use 6 of 23". | He's taken it on, Theo left notes, and he lists what he can look up (≈ 25 s) |
| 2 | *(show the shop at :8101 on the left)* | Theo's 2009 back office, for a beat | |
| 3 | *"Which repairs are due tomorrow, and are we short on parts for any of them?"* | The live line ("Looking at repair jobs due on Tue 24 Nov" …), then one grey line. Open it to show the steps. | "Five repairs are due tomorrow, and only one is short of parts. Anika Banerjee's brake bleed needs two pairs of brake pads, and we've just the one." (≈ 13 s) |
| 4 | *"Order ten pairs of those brake pads from the usual supplier."* | A new-key card, **"Let Barnaby order parts from your suppliers"**, "A new key", with "Each time: He still asks you before he does it." Click **"Yes, go ahead"**. The side panel adds the key under "Keys you gave him" with "today". Then he asks: "Ten pairs of the Shimano resin brake pads from Madison, at six pounds fifty a pair. Shall I?" On the change card, say **"Yes"** (or click "Approve"). | "I've ordered ten pairs from Madison, which comes to sixty-five pounds…" Show it on the shop's "Purchase Orders" tab. (≈ 15 s) |
| 5a | *"Barnaby, Sofia's bike's done, job 4475. Text her it's ready to collect and mark it ready."* | "I can't text customers or change a job's status myself yet, but Theo built the system a way to do both. Shall I take those on?" Two new-key cards: texting customers, and marking repairs ready. Click **"Yes, go ahead"** on each. Then say **"Yes"** to the text card and to "Change a job's status: job 4475 to ready". | Sofia texted, job ready (≈ 10 s) |
| 5b | *"Kwame's bike's done too, job 4490. Text him it's ready to collect and mark it ready."* then *"And Jana's, job 4488. Text her it's ready to collect and mark it ready."* | No new keys this time: just the two change cards each, so say **"Yes"** to each. After the repeats, he may offer to make it one step ("That's three today, so if you'd like, I can make texting and marking ready a single step."). | Cut most of this in the edit |
| 5c | *"Tom's bike is done, job 4481. Hand it back: text him it's ready and mark it ready. And make handing back a bike a single step, would you? I do it a dozen times a day."* | A shortcut card, **"Hand back a bike in one step"**, "A shortcut": "One step instead of several, made from things the shop's back office already does." Click **"Yes, go ahead"** (≈ 30 s while it's made). Then say **"Yes"** to its change card. The work line reads "Used “Hand back a bike in one step”"; the side panel lists it under "Made with your say-so". | "That's one step now…", then Tom's Brompton handed back (≈ 40 s) |
| 6 | *"Who's overloaded this week?"* | "The system can't tell me that yet, so I'll make it a way to work it out…" The live line runs through "Reading the notes left with the code", "Reading the code", "Writing the change" and "Running the checks". Cut most of this. Then he says what he made, what it reads and changes, that Theo's checks pass and that it can be undone. Card: **"Add a weekly workload report to the shop's back office"**, "A new piece for the system", with "What it reads", "What it changes: Nothing.", "Checks: ✓ Theo's 19 checks still pass, and so do the 4 new ones." and "If you change your mind: It can be undone." Open **"See the change"** (it shows the counts, e.g. "3 files +130 −0", and becomes "Hide the change"), scroll a little, then click **"Yes, add it"**. *(Optional: first say "Yes". He replies "That one needs a look and a click on the display, I'm afraid.")* The steps "Added it to the system" and "Ready to use: …" follow. | "Dev's overloaded: he has thirty-one hours of work due this week against his twenty, so he's eleven over. Ravi has nineteen and a half hours spare, and Priya has nothing booked at all." (≈ 95 s) |
| 7 | *"Move Dev's two wheel builds to Priya, please."* | A new-key card, **"Let Barnaby give a job to a different mechanic"**: click **"Yes, go ahead"**. Then "I'll give Rachel Okafor's front wheel build and Magnus Lindqvist's rear wheel build to Priya. Shall I?" Say **"Yes"** to each change card (jobs 4471 and 4472). | "I've moved both wheel builds to Priya, and Dev's down to nineteen and a half hours, just inside his twenty." On the shop's "Jobs" tab, both jobs flip from Dev to Priya. (≈ 15 s) |
| 8 | *(click "What he can do", top right)* | The sheet lists every ability in plain words, by area, each with a state word: "Can use", "Asks first", "Kept shut" (cancelling a job, struck through), "Key given today" and "Added today" (the workload report). "Made from several steps" shows "Hand back a bike in one step". At the top: "He can use 11 of the 24 things it can do." "Show technical names" reveals the paths. | End on this |

The numbers on cards (new tests, files, lines) are whatever the builder wrote this time. The film shows "3 new ones"
and "+114"; the 25 Nov run wrote 4 tests and +130. Card titles and the skill's name are Barnaby's words and can vary.

If a beat goes sideways, keep going: it's a real agent. Click "Not now" or "Decline", then rephrase.

### Optional: connect another system

This shows the bring-your-own-repo step from the film's last scene. Start the other repo's HTTP API first (Barnaby only
starts the shop himself). Then click "+" in the composer, or open "What he can do" and scroll to the foot.

- **"Connect a system"**: "Barnaby reads its code and lists everything it can do. To begin, he only uses the things
  that look something up." Fill in **Name**, **Repo path** and **API base URL**, then click **"Connect"**.
- A work line reads "Reading …", then a "Connected" note says how many things it can do and how many he may use.
- By voice instead: *"Barnaby, this is our inventory service, in D:/code/inventory, running on port 9000."*

## 4. Without voice

Type each line in the composer and press Enter. Click "Approve" on change cards instead of saying "Yes". Barnaby
doesn't speak without the voice bot, so his answers appear only in the thread.

## 5. Reset (between takes)

1. Stop `serve` (Ctrl+C in terminal 1). The voice bot can keep running.
2. `.venv/Scripts/python scripts/demo_reset.py` (add `--today 2026-11-23` for the film's dates). It stops a shop
   left running on :8101, clears Barnaby's registry and generated servers, makes a fresh copy of Theo's repo with
   its history, and reseeds the shop. Run it while `serve` is stopped, because `serve` keeps the registry in memory.
3. Start `serve` again and reload the page. A reload without a restart replays the session's recent events, so
   always restart for a clean take.

## After recording

Put the file in `.demo/recordings/` (gitignored). For the edit: cut the waits, add captions for the tiers if they
help, and level the audio to match the film (−16 LUFS). The shop, its people and its data are fictional (see the
README's [Real vs staged](../README.md#real-vs-staged)).
