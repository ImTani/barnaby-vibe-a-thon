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

## The titles over the two desks
- **One centred column** above the desks, on a scrim (rgba(12,11,10) .82 at the top, gone by 660 px) so the type
  sits on near-black without a box.
- **Hierarchy, three levels only:** the lockup (the mark, 92 px, its base on the baseline of "Barnaby", Sitka
  Subheading 600, 112 px, -0.012em); the line "Every system deserves a butler." (Sitka Text 46 px, ivory at 92%);
  the coda "Even the old ones." in the same size and face, in brass. The line and its coda read as one couplet:
  44 px above the couplet, 10 px between its lines.
- **Upright, not italic:** DESIGN.md sets his serif upright, never italic, so the coda is upright brass (the earlier
  plan said brass italic; the brand rule wins, agreed with the coordinator).
- **Motion:** the lockup fades up over 1.1 s with an 8 px settle on 'title', the mark rings once just after the real
  bell; the line follows 1.0 s later; the coda arrives on 'old_ones' as the new desk fades. All three leave together
  over 0.7 s, before the card.
- **The credit and the staged-scenes note moved to the card;** the desks carry only the name and the line.

## The product end card
- **Ground:** warm charcoal #1F1E1C (the brand's dark ground: the film ends at night, so no flash to ivory).
- **Grid:** 12 columns, 192 px margins (10%), content 1536 px; the growth row is four equal columns, 48 px gutters.
- **Head, centred:** the mark (92 px), "Barnaby" (Sitka Subheading 600, 88 px), and one line in his serif saying what
  he is: "A voice-first butler for the software your business already runs." (PRODUCT.md's purpose, 34 px, ink 2).
- **The four ways he grows**, a quiet row under a hairline: Ask / Unlock / Compose / Build in Sitka Subheading 34 px,
  each with one plain sentence in Segoe UI 20 px (ink 3): what it means for the owner, not how it works.
- **Credits** under a second hairline: **Built on Synapse** (600) and the event, 2nd Brain Labs × Geek Room
  Vibe-a-thon. The repo goes at the right of this row once its public URL is confirmed (REPO in s9.js, one line).
- **Small print** (16 px, #8A847A, 4.6:1): recreated from a real recorded run; Quorum and ComfyUI staged; endpoint
  counts from real Synapse scans; synthetic voices; Barnaby's voice: ElevenLabs; a fictional shop.
- **Brass appears once, in the mark** (the One Brass Rule). No icons, no boxes, no gradients, no decoration.
- **Motion:** the card dissolves in over 0.8 s as the titles leave; its four tiers settle in turn (0, 0.35, 0.6,
  0.8 s, a 6 px rise each); the film fades to black on 'fade_out'. With an `end_card` mark in the cue sheet the card
  starts there; without one, at 'credit' - 0.2.
