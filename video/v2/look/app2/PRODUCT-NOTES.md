# Barnaby's display, in product terms

Written before any pixels, for the `?skin=app` rework (25 Nov). The director's verdict: the default has the AI tell,
and the two themed skins read as gimmicks. Barnaby's display is the only part of the product that *is* the app, so
it is designed as a shipping app a small business would trust every day.

## Who uses it, where, on what

| Who | Where and how | On what | What they need from the screen |
|---|---|---|---|
| **The owner** (Martin, 61, reading glasses) | Back office, between jobs. Talks from a step back, glances, comes closer only to approve something. Daylight, strip lights, a glossy panel with glare. | A 2009-era PC, Chrome, about **1440×900** on a 19-inch 16:10 LCD (about 89 ppi: a CSS pixel is physically as large as on a modern 24-inch 1080p screen, so type is not scaled down for it). | The latest answer readable from a step back; a plain-words yes or no; never a technical word unless he asks. |
| **Staff** (Priya, new mechanic) | Same machine, quick questions about jobs, often typed. | Same PC. | A clear place to type or hold to talk; short answers; no surprises. |
| **The developer** (Theo, or whoever comes next) | At the desk or remote, on a modern machine, **1920×1080** and up. | Chrome, Windows 11. | The whole truth on request: every call, the change itself, the technical names. One click away, never in the way. |

It also runs as a **compact window** (`?overlay=1`, about 560 wide) beside other apps.

## The jobs, in order of frequency

1. **Talk.** Hold the button (or the space bar) and speak; or type. Voice is the main input, so it is the largest
   control in the composer, but typing must never feel second-class.
2. **Read the answer.** Barnaby's latest reply is the most legible thing on screen; earlier exchanges step back.
3. **Know what he is doing, without noise.** One line of status that a person would say ("Looking at repair jobs
   due on Tue 24 Nov", "Waiting for your say-so"); a quiet list of what he did in plain words, each line openable to
   its technical record. Nothing scrolls past at speed, nothing is monospace unless it is code.
4. **Say yes or no with full understanding.** The rare moment that deserves full attention. A card that says, in
   plain words, what he wants to do and why; for a new piece of the system, what it does, what it reads, what it
   changes, that the checks pass and that it can be undone; the change itself behind "See the change". The yes and
   the no are equally easy, and the card says how it may be answered: "Or just say yes" for ordinary data changes,
   "A change like this needs a click, not a spoken yes" for code. Every decision stays in the conversation.
5. **See what he can do.** Every ability the system has, in plain words, grouped by area, with its state as an icon
   and a word (he can use it, he asks first, kept shut, new today); the technical name beside it for the developer.
6. **Connect a system.** A short form: a name, where the code lives, the address it runs at.

## The states, and what "good" feels like

| State | What the owner sees | Good feels like |
|---|---|---|
| **Empty** (first run, no system) | Barnaby says good day and what he is for; how to talk to him; a button to connect a system. | A welcome that teaches the two controls, not a blank page. |
| **Ready** | The conversation, the composer, "At your service". | Calm. Nothing moves. |
| **Working** | The status names what he is doing now; a pending line in the conversation says the same; activity fills in quietly. | Like watching a colleague work: you can see the room he is in, nothing flashes. |
| **Waiting for approval** | The card at the foot of the conversation; the status says "Waiting for your say-so"; the activity line says what he asked. | The only thing on screen that asks for attention, and it asks politely. |
| **Voice listening** | The talk button changes colour and shows the level; the status says "Listening". Let go and it stops. | Native, like dictation on a phone: immediate, no ceremony. |
| **Error** | A plain sentence in the conversation with a warning icon and what to do next. Voice unavailable says so. | Honest and recoverable, never a stack trace on the owner's screen. |

## What this rules in and out

- **In:** light by default (daylight, glare, a 61-year-old reader); one workhorse UI face already on the machine
  (Segoe UI); a restrained warm accent from the brass bell; real hierarchy from size and weight; conventions people
  already know (a toolbar, a conversation, an inspector, a sheet, a disclosure, buttons that look like buttons).
- **Out:** themes and costumes (road signs, tickets, liveries); dark navy and brass; italic serif "bot voice"; chat
  bubbles left and right; status pills; a monospace live trace; gradients, glows, pulsing dots.
- **The craft bar:** Linear, Things 3, Apple Messages and Mail on macOS, the Claude desktop app. If a screen would look
  out of place beside them, it is not finished.
- **Barnaby's identity lives in details:** the bell mark; one warm brass accent used sparingly (his mark, the
  waiting state, focus and selection); his voice in every label and empty state; approvals that feel trustworthy;
  a voice control that feels native.
