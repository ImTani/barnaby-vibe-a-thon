# The world of the film (v2 bible)

Everyone working on the v2 film reads this first. It's the single source for who these people are, where the film
happens, and how Barnaby speaks. The script (`SCRIPT.md` / `docs/script.html`) is written from it.

## What changed from v1, and why (Tani's review)
- v1 was a pitch about software: UI floating on a dark grid, captions carrying the story, developer language. v2 is a
  **product film about people**: a real place, characters with histories, the story told by what they say and what's
  on the desk. No caption should be needed to understand a beat.
- **Barnaby faces a person, not a developer.** Martin can't consent to "POST /api/purchase-orders" and can't read a
  diff. Barnaby explains in the household's words; technical detail exists, tucked away, for whoever wants it.
- **Era consistency.** The shop's PC is a 2009 Windows 7 machine on a period LCD. Everything on it belongs to that era,
  except Barnaby, who is new and must still feel like part of the household.
- **Craft everywhere:** real recorded sound, natural speech at real speaking rates, a world with depth and jokes.
- **Process:** nothing is rendered at full length until the script, the look and an animatic have each been approved.

## The place
**Spokes & Sprockets**, *a Hartley family workshop, est. 1987*. A small bike shop in an English market town. Behind
the counter is the **back office**: one desk, one window onto the workshop floor. **The desk is the stage.** We model
it, the corner of the room around it, and a glimpse of the workshop through the doorway, in low poly but high effort.
Who is "at the desk" is implied by the objects on it and the voice we hear; we never need to show faces.

### Theo's desk (the hero set)
- **The PC:** a black 2009 desktop tower with worn stickers (no real brand logos), and a 19-inch 16:10 glossy-black LCD
  on a slim stand. Speakers, a keyboard with shiny worn keys, an optical mouse on a faded mousepad.
- **Sticky notes on the bezel,** in Theo's handwriting: "THE SYSTEM = this PC. don't unplug!!",
  "backup = USB stick, drawer 2", "Reports: coming soon (sorry Uncle M)".
- **Corkboard:**
  - a printed, dog-eared "README: for whoever looks after it next";
  - a parts-supplier calendar (November), with **Friday** circled: "THEO'S LAST DAY :(";
  - a photo from 2009: teenage Theo and Martin outside the shop, Theo holding a CD-R marked "SHOP SYSTEM v1".
- **On the desk:**
  - a spindle of CD-Rs and a ring binder, "INVOICES 2009–";
  - a mug, "WORLD'S OKAYEST NEPHEW" (Martin's joke gift);
  - a desk lamp.
- **On the floor or chair:** a half-packed moving box, "THEO, LISBON". His new job abroad is at an animation studio.
- **Shelf above:**
  - a box of brake pads with a note, "LAST PAIR!!", which pays off Anika's shortfall;
  - parts drawers with hand-written labels.
- **Through the doorway:** bikes on stands, a truing stand, a pegboard of tools, an inner tube hanging, a radio.
- **On the counter at the doorway:** the shop's **brass service bell** with a card, "RING FOR SERVICE". This bell is
  Barnaby's emblem: he is what answers it now.

### The desk changes hands (props tell the story)
- **Theo's last week (night):** his things everywhere; the box half-packed; desk lamp, monitor glow, rain on the window.
- **Monday (morning, Martin):**
  - Theo's things gone; the "OKAYEST NEPHEW" mug left behind on purpose;
  - Martin's reading glasses on a cord, a greasy workshop rag, a paper job card, a pencil behind… the keyboard;
  - cool daylight and workshop strip lights.
- **Priya's first day (later Monday):** a new toolroll, a lanyard, a "HELLO my name is PRIYA" sticker, a fresh notebook.
- **Close (evening):** warm low sun turning to night; the bell on the counter; the PC asleep, Barnaby's bell glowing
  softly in the corner of the screen.

## The people
| Who | Age | Voice and manner | What they want |
|---|---|---|---|
| **Martin Hartley**: owner, Theo's uncle (voiced by Tani) | 61 | Plain-spoken, kind, busy, short sentences. "Right." "Go on, then." Impatient with computers (the nine tabs). Doesn't know what an endpoint is and shouldn't have to. Doesn't want to be called "sir". | Keep the shop running without Theo; look after his people. |
| **Theo Hartley**: nephew, wrote the system | 31 | Quick, funny, a bit sentimental about leaving. Wrote the system at 14 ("bye access database!!") and kept it going for 17 years. | To leave without leaving his uncle stranded. |
| **Priya Nair**: new mechanic, first day | 24 | Sharp with bikes, wary of 2009 software, dry humour. | To be useful on day one. |
| **Barnaby**: the butler, lives on the shop PC | timeless | Composed, warm, quietly witty, discreet. Unhurried, never slow. | To look after the household and its system, and to earn its trust. |

Off-screen: Dev and Ravi (mechanics), Anika and Tom (customers), Madison (the usual supplier).

## How Barnaby speaks (the film and the real app)
- **The household's words, never the machine's:**
  - never "endpoint", "API", "tool", "MCP", "server", "deploy", "merge" or "diff" to Martin or Priya;
  - he says what the system *can do*: "Theo built it a way to order from suppliers";
  - technical detail is offered, never pushed: "the change is there if anyone wants to read it".
- **He asks before he takes a new key,** and **explains before he changes anything:**
  - what it does;
  - what it touches, and what it can't touch;
  - that Theo's checks still pass.
- **He's honest about limits:** "I can't do that yet."
- **He's short.** One to three spoken sentences. A dry aside now and then, never twice running.
- **Martin is "Martin".** Martin tells him off for "sir" once; Barnaby complies: "Very good, Martin."

## The metaphor that makes Synapse legible
**Synapse gives Barnaby the floor plan of the house; Martin gives him the keys.**
- **Connect:** Synapse reads Theo's code and hands Barnaby a floor plan of every room the system has, meaning everything
  it can do.
- **Read-only start:** Barnaby walks only the rooms that are safe to look in.
- **Unlock:** he asks for a key to a room that already exists (ordering from suppliers).
- **Compose:** he builds a service passage that joins rooms he keeps walking between (handing back a bike).
- **Build:** he adds a room that was never built: Reports, "coming soon!!" since 2011.

## Era and design rules
- **The shop PC:**
  - a Windows 7-era desktop: glass taskbar, a round Start button, a wallpaper, desktop gadgets (the RAM meter is a
    gadget);
  - evoke the era, but **no Microsoft logos, no Windows system sounds, no real product logos**.
- **Theo's system:** teenage 2009 web design (Verdana, bevels, "coming soon!!", a visitor counter). Keep and add more of
  this personality.
- **Barnaby's look:** his own identity, chosen in the look book. It belongs to the household (brass bell, the shop's
  ledger, warmth), not a generic AI dashboard.
- **No abstract voids.** Every shot is somewhere: the room, or the screen inside the room.

## Honesty
The film is a staged recreation of the real app. Figures, the code change and the test result come from a real
recorded run (`video/data.js`). The Quorum and ComfyUI beats are staged (their endpoint counts are real Synapse scans);
a small on-screen note and the README disclose this.
