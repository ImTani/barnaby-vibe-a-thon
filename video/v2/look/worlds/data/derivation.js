/* new-work-world steps 1-3, one round per person, written BEFORE each concept-seed roll (the lists are what the dice
   index into). Mechanism, rut, and seven grounded candidates ordered by resonance, each already a complete direction
   (a reusable world joined to that person's key moment). Mode: experience (film showcase surfaces). */
window.DERIVATION = {
  mechanism: 'Synapse reads a system’s code and hands Barnaby a map of everything it can do; Barnaby uses only what he has keys to, asks before taking a new one, joins steps he keeps repeating into one, and builds a missing piece only with the owner’s say-so. Under every look below it is this one mechanism.',

  theo: {
    scene: 'Theo, 31, wrote the shop system at 14 and kept it alive for 17 years. Thursday 19 Nov 2026, 21:47, his last week, rain, desk lamp, the 2009 shop PC; later a laptop at an animation studio in Lisbon. He hands the system over: Synapse reads it in 0.48 s, 23 abilities found, the 6 read-only ones opened.',
    home: 'Developer culture (the 2009 teenage web he learned on, code, git, his README) and animation-studio culture (exposure sheets, light tables, pencil tests, rostrum and multiplane cameras, rigs, dailies). And the brief: to Theo, Barnaby is Jarvis, the assistant who apprehends the whole system at once and talks to him as a peer.',
    prove: 'That Barnaby takes in the entire system in half a second and reports it back to its author in his own technical language, with a presence (a voice, a form) rather than a dashboard.',
    rut: ['A dark IDE or terminal dashboard with a monospace endpoint table (the previous round, livery-5).', 'Its opposite: a friendly light chat-bubble assistant.', 'The brief’s literal picture: Jarvis as a cyan holographic HUD (at most one candidate).'],
    candidates: [
      { id: 'multiplane', name: 'The multiplane stand', why: 'Theo’s new trade’s own hardware for depth: the hologram’s layered projection translated into glass planes under a rostrum camera; tiers become depth.', look: 'Warm-black studio, glass planes catching a key light, gouache cel colours painted on glass, registration pegs, exposure numbers on the planes.', moment: 'Barnaby lowers the camera through Theo’s system: 23 abilities painted onto glass in 12 frames, the 6 he may use on the top plane, the 17 he would ask for drawn but unpainted below, the 1 kept shut frosted.' },
      { id: 'xsheet', name: 'The exposure sheet', why: 'Animation’s timing notation; 0.48 s is 12 frames at 24 fps, so Barnaby times Theo’s whole system to the frame.', look: 'Buff sheet with printed blue rules, frame numbers, columns for action, dialogue and camera; graphite and red col-erase marks.', moment: 'The action column logs each ability found on its frame; the dialogue column breaks Theo’s line and Barnaby’s reply into phonetics.' },
      { id: 'lighttable', name: 'Clean-up on the light table', why: 'Barnaby as clean-up artist and in-betweener: Theo’s roughs underneath, Barnaby’s line on top; the Build is the missing in-between.', look: 'Glowing white light box, peg bar, blue col-erase roughs, graphite clean-up line, red pencil notes, onion-skin layers.', moment: 'Theo’s 2009 system shows through as roughs; Barnaby traces every ability in clean line.' },
      { id: 'schematic', name: 'The exploded schematic', why: 'Jarvis explodes a suit into its parts; here Theo’s code explodes into its 23 parts as an engineering plate.', look: 'Buff paper, black line art with hatching, numbered leader-line callouts, a parts list.', moment: 'routes_jobs.py, services.py and the rest fly apart into an exploded view; every ability a numbered part.' },
      { id: 'rig', name: 'The rig', why: 'The animator’s working tool: the system as a skeleton whose joints are abilities and whose control curves are keys.', look: '3D viewport grey, joint spheres, coloured control curves, an outliner.', moment: 'Barnaby rigs the system; read-only joints locked, the rest keyable on request. (tool candidate)' },
      { id: 'nfo', name: 'The NFO', why: 'Teenage Theo’s internet: ASCII art and scrollers, greets to Uncle M.', look: 'Black, ASCII logo, bitmap type, raster bars, a sine scroller.', moment: 'Barnaby “presents” the system as an NFO, abilities scrolling past.' },
      { id: 'hologram', name: 'The workshop hologram', why: 'The brief’s literal Jarvis picture (the one rut candidate allowed).', look: 'Near-black, cyan volumetric wireframe, orbiting callouts.', moment: 'The system turns in the air as a wireframe; Theo pinches it open.' },
    ],
  },

  martin: {
    scene: 'Martin Hartley, 61, owner since 1987, reading glasses on a cord, asks out loud between jobs from a step back. Monday 08:55 at the shop PC: he has just asked for ten pairs of pads from Madison and Barnaby needs the ordering key.',
    home: 'The Spokes & Sprockets building and his trade: the workshop floor, stands, the counter and till, the stockroom, the back door where Madison’s van unloads, the back office; the documents and signs that live on its walls; the bike trade’s manuals.',
    prove: 'A proper floor plan of his own building (pinned): walls, doors, stands, counter, till, stockroom, back door, back office. Each ability lives in the room where it happens; Barnaby moves through the building as he works; a key is asked for at a real door.',
    pin: 'Topology pinned by the director: an architectural plan of the building. The roll decides the world it is drawn in.',
    rut: ['A grid of rooms that is really a dashboard (the previous round, livery-4).', 'Its opposite: a photoreal 3D model of the shop.', 'The brief’s literal picture: a white-on-blue blueprint (at most one candidate).'],
    candidates: [
      { id: 'evacuation', name: 'The plan by the back door', why: 'Every shop has its fire-evacuation plan framed by the back door; it is a floor plan Martin passes daily, and its YOU ARE HERE marker is exactly Barnaby moving through the building.', look: 'White ground, heavy black walls, green route arrows, square pictograms, a legend, a red YOU ARE HERE dot.', moment: 'Barnaby’s marker walks from the stockroom shelf to the back office door; the Orders door carries a key pictogram and the question.' },
      { id: 'shadowboard', name: 'The shadow board', why: 'His trade’s own inventory system: painted outlines show where each tool hangs and what is missing.', look: 'Perforated hardboard, painted silhouettes, hooks.', moment: 'The building painted on the pegboard; each ability a tool hung in its room; an outline with no tool is a key.' },
      { id: 'dealermanual', name: 'The dealer manual plate', why: 'The bike trade’s technical drawing language he has read for 40 years.', look: 'Crisp black planometric line art, numbered callouts, an index table.', moment: 'The building as a numbered plate; each ability a callout; Barnaby’s route as a dashed line.' },
      { id: 'particulars', name: 'The particulars', why: 'The estate agent’s floor plan every English owner has read.', look: 'Thick black walls, room names with metric and imperial sizes, compass, “not to scale”.', moment: 'Rooms with their sizes and abilities; Barnaby’s route drawn in.' },
      { id: 'blueprint', name: 'The 1987 conversion drawings', why: 'The literal “plan” (the one rut candidate allowed).', look: 'White line on Prussian blue, a title block.', moment: 'Ground-floor plan with a revision cloud at the Orders door.' },
      { id: 'goad', name: 'The town plan', why: 'The market town’s large-scale plan: the shop in its street, the alley where deliveries come in.', look: 'Hand-tinted building fills, hairline capitals, numbered plots.', moment: 'The shop drawn within Market Place; Barnaby crosses from the alley door to the office.' },
      { id: 'cutaway', name: 'The cross-section book', why: 'The cutaway picture books his nephew grew up on.', look: 'Isometric cutaway, tiny figures, dense detail.', moment: 'Barnaby as a small figure walking room to room.' },
    ],
  },

  priya: {
    scene: 'Priya Nair, 24, new mechanic, Tuesday morning, her second day. Sharp with bikes, wary of 2009 software, dry. At the shop PC she asks: “Sorry, what can this thing actually do?” Her bench holds the two wheel builds moved to her yesterday: Rachel’s front (due today) and Magnus’s rear (due Wednesday, spokes short: 40 on the shelf, 64 needed for both).',
    home: 'A young mechanic’s bench: the truing stand and wheel building, her new toolroll, workshop manuals, alleycat and messenger culture, the diagrams and games and phone maps her generation reads by heart.',
    prove: 'That the whole system, everything it can do for her, reads in one look from her bench, in a slightly different look from Martin’s plan but the same building and the same rooms underneath.',
    rut: ['Her jobs as paper repair tags (the previous round, livery-6).', 'Its opposite: a phone-style widget dashboard.', 'The literal picture: Martin’s plan again, recoloured.'],
    candidates: [
      { id: 'lacing', name: 'The lacing chart', why: 'Her first job is two wheel builds: the system as a wheel she would build, Barnaby at the hub, every ability a spoke, the rim divided into the shop’s rooms.', look: 'Radial lacing drawing, steel spokes, anodised nipple colours, tension readings.', moment: 'The whole wheel at once: 24 spokes, 9 tensioned (he can use them), the rest slack until someone gives a key, 1 left out.' },
      { id: 'dungeon', name: 'The dungeon map', why: 'Her generation’s floor plan: rooms, locked doors, keys, a marker; the same building as Martin’s, in a game’s top-down map.', look: 'Top-down map, explored rooms filled, unexplored dim, key icons on doors.', moment: 'The shop mapped room by room, with the room he added yesterday marked new.' },
      { id: 'linemap', name: 'The line diagram', why: 'The same building abstracted like a transit diagram: each thing she can ask is a line through the rooms.', look: 'Coloured lines at 45°, station ticks, interchanges.', moment: 'Hand back a bike rides one line through the rooms.' },
      { id: 'manifest', name: 'The alleycat manifest', why: 'Bike-messenger race culture: a manifest of checkpoints, stamped when visited.', look: 'Xerox black on fluoro paper, stamps, hand lettering.', moment: 'The rooms as checkpoints; a spoke card.' },
      { id: 'toolroll', name: 'The toolroll', why: 'Her new toolroll laid open on the bench.', look: 'Waxed canvas, leather straps, pockets.', moment: 'Each pocket a thing the system can do; empty pockets are keys.' },
      { id: 'bikecheck', name: 'The bike check', why: 'The annotated build post her generation reads.', look: 'Side-on drawing with callout labels.', moment: 'The shop annotated like a build list.' },
      { id: 'manual', name: 'The repair manual plate', why: 'Workshop procedure illustration.', look: 'Numbered steps, line illustrations.', moment: 'What it can do as procedure plates.' },
    ],
  },
};
