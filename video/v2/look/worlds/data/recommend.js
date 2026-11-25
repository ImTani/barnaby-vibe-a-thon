/* The design director's recommendation per person (filled after every frame was looked at), and the substitutions
   this round made for impeccable's interactive steps. */
window.RECOMMEND = {
  theo: { card: 'theo-hologram',
    why: 'The only card that reads as Jarvis at a glance, and it stays in Theo’s own language: every one of the 23 routes printed beside the building, the scan plane showing Synapse reading, the six he may use filled. It is situated (rain on the back-office window, the lamp), so it is the film’s world, not a HUD in a void. It arrives modest on the 2009 PC and becomes fully himself on the Lisbon desk (frame below). The console is the more legible runner-up if the homage risk is acceptable.',
    lisbonCard: 'theo-hologram', lisbon: 'frames/theo-lisbon.png',
    lisbonText: 'Lisbon, Mon 23 Nov, his first day at the studio (scene 8, staged): the form in his tile on the tiled main monitor, a companion beside ComfyUI on the second. Desk and tiling layout are a stand-in until video/v2/look/lisbon-pc/ is built.' },
  martin: { card: 'martin-manual',
    why: 'The world the dice dealt, and the one that answers the brief best: a real plan of his building (walls, doors, stands, counter, till, shelves, the back door), drawn in the language of the dealer manuals he has read at the bench for forty years, not in an app’s. Every number sits on the object where the work happens, his route runs like a cable, and the key is asked for at the back door where Madison’s van unloads. Needs a camera push to the back-door corner on film. The evacuation plan is the most legible from a step back; choose it if clarity at a glance matters more than distinctiveness.' },
  priya: { card: 'priya-toolroll',
    why: 'Her own object on her own bench, and it answers her question the way she would check a kit: a tool in its pocket he can use, an empty outline waits for a key, one pocket sewn shut, yesterday’s pocket in bright thread. Every pocket carries the words to ask, and the sections are Martin’s rooms in the same order, so it is his plan folded into her world. The lacing chart is the stronger single image; choose it if the film wants the poster over the answer.' },
  sameText: 'Scene 6, the moment the report lands (Mon 23 Nov 2026, 15:05): Theo (in Lisbon, his first day) sees the diff and the tests passing; Martin sees a new room built where Reports was planned in 2011; Priya sees two jobs arrive on her bench. Same build, same result, three worlds: the hologram, the dealer manual plate and the toolroll.',
  substitutions: [
    'Decision page: impeccable serves a live page (serve-question --start / --wait) that returns the choice. A subagent cannot hold that wait or reach the director, so this is a static page built from the same payload fields (kind, catalogId, verdicts, raises, risk); the choice comes back through the coordinator.',
    'Interview (new-work step 2): no structured questions could reach the director, so the brief, WORLD.md, the script (v2.1 lines from the coordinator) and PRODUCT.md stood in for the answers.',
    'Comps: impeccable wants image-generated decision comps. Image generation was forbidden by the director, so every hero frame is built in HTML/CSS/SVG and rendered with headless Chrome (render.js). No OpenAI key used, no generate-image run.',
    'QUALITY BAR boards: the catalogue’s reference images are remote; downloads were not allowed, so challengers were weighed from their printed system grammar only.',
    'Fonts: the craft floor asks for a sourced display face (font-fetch). Downloads were not allowed and the real app may only use fonts already on the machine, so every world uses installed faces only.',
    'Build path: without image generation impeccable makes the build code-led and offers no toggle; nothing here is a build yet, these are look frames for the film.',
    'One discarded roll: an early "concept-seed --help" call printed an unscoped surface roll before any derivation. It was ignored; the three direction rolls (seed references on each section) are the only ones used.',
    'No surface brief or DESIGN.md was written: these are film surfaces for choosing a world (phase 1). Direction contracts get written once the director picks.',
  ],
};
