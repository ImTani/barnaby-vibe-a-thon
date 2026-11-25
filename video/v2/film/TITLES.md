# Titles and the product end card

The film's last 10 s: the titles over the two desks, then a product card on a clean ground. The brand is DESIGN.md and
PRODUCT.md (the real mark, `ui/assets/barnaby-mark.svg`; Sitka Subheading / Sitka Text and Segoe UI; brass as the one
accent; warm ivory on warm charcoal). Built in `scenes/s9.js` and the `.t-titles` / `.t-card` rules in `index.html`.

## What I took from where
- **Apple product films:** one idea per card, the product's name as the hero, a short line that says what it is, and
  nothing else in the frame. Long holds and quiet fades: the card is allowed to sit.
- **Linear and Arc launch videos:** the closing card is a layout, not a poster: a strict grid, a hairline or two to
  separate tiers of information, small sans for the facts, and one colour doing real work.
- **A24 title cards:** a centred serif, sentence case, generous tracking left alone, white space as the subject, and a
  slow, even fade with the music rather than motion graphics.
- **Impeccable (docs only):** no eyebrows or kickers, no cards for structure, hierarchy from size and weight together,
  more space above a group than inside it, one authored motion moment, contrast checked on the real ground.

## The titles over the two desks (round 3: the wordmark at the centre, the line in Theo's hand)
- **The wordmark at the centre of the frame:** the mark (100 px, its base on the baseline of "Barnaby") and "Barnaby"
  in Sitka Subheading 600, 124 px, -0.012em, ivory; the lockup's top at 396 px so its cap height sits on the frame's
  centre line. It fades up over 1.1 s with an 8 px settle on 'title'; the mark rings once just after the real bell.
- **The line in Theo's hand:** "Every system deserves a butler." in Segoe Print (`segoepr.ttf`, loaded by @font-face
  from its file URL as "TheoHand": the hand on his sticky note, make_note.py and CONTINUITY.md), 58 px, warm ivory,
  58 px under the lockup. The coda "Even the old ones." in the same hand in brass (#D3A14A), 56 px, turned -1.6 deg and
  set 34 px right, like a line added after. The serif is Barnaby; the hand is Theo, who built the old system.
- **Written on, not faded:** each word in turn behind a soft-edged mask (30 px feather) moving left to right at a
  pen's pace, time per word by its letters, a 90 ms lift between words. The line starts 1.2 s after 'title' and
  takes 2.1 s; the coda starts on 'old_ones' (as the new desk fades) and takes 1.2 s. Nothing bounces.
- **Legibility:** a soft oval scrim (warm near-black, .8 at the centre, gone by the frame's edges) under the group
  instead of a top band; the type keeps a faint dark text-shadow over the lit desk.
- **Out:** everything leaves together over 0.7 s from 'end_card' - 0.75, so the titles are gone before the card's
  dissolve and its own name never doubles over theirs.
- Styles are injected by `scenes/s9.js` (`#s9-titles`); the old `.t-titles` rules in index.html are no longer used.

## The product end card
- **Ground:** warm charcoal #1F1E1C (the brand's dark ground: the film ends at night, so no flash to ivory).
- **Grid:** 12 columns, 192 px margins (10%), content 1536 px; the growth row is four equal columns, 48 px gutters.
- **Head, centred:** the mark (92 px), "Barnaby" (Sitka Subheading 600, 88 px), and one line in his serif saying what
  he is: "A voice-first butler for the software your business already runs." (PRODUCT.md's purpose, 34 px, ink 2).
- **The four ways he grows**, a quiet row under a hairline: Ask / Unlock / Compose / Build in Sitka Subheading 34 px,
  each with one plain sentence in Segoe UI 21 px (#B1AA9C, about 7:1): what it means for the owner, not how it works.
- **Credits** under a second hairline: **Built on Synapse** (600) and the event, 2nd Brain Labs × Geek Room
  Vibe-a-thon, and at the right end of that row, quieter (#A8A194), the shoutout "Voices: zoonie and
  sylenthsnares"; under them, its own quiet line in the same sans and grey, the repo: github.com/ImTani/barnaby-vibe-a-thon.
- **One spacing scale** (round 2): 48 between tiers, 32 from a rule to its content, 24 to the small print, 12 inside
  a step; the whole card is one column on the grid, centred in the frame.
- **Small print** (16 px, #A39C8F, about 6:1): recreated from a real recorded run; Quorum and ComfyUI staged; endpoint
  counts from real Synapse scans; synthetic voices; Barnaby's voice: ElevenLabs; a fictional shop.
- **Brass appears once, in the mark** (the One Brass Rule). No icons, no boxes, no gradients, no decoration.
- **Motion:** the card dissolves in over 0.8 s as the titles leave; then a calm build in reading order: the mark and
  the name, the line (0.4 s), the four steps 120 ms apart (from 0.85 s, their rule drawing with them), the credit
  (1.55 s), the repo (1.65 s), the small print (1.8 s), each with a 10 px upward ease, no bounce; the film fades to
  black on 'fade_out'. With an `end_card` mark in the cue sheet the card
  starts there; without one, at 'credit' - 0.2.
