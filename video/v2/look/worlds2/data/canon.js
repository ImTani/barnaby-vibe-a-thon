/* CANON for this round (worlds2). Loaded after ../worlds/data/building.js and story.js, which it reuses unchanged on
   disk. It corrects their clock to the canonical dates (video/v2/world/CONTINUITY.md, the director's brief, 25 Nov):
     Thu 19 Nov 21:47   the handover on the 2009 PC
     Mon 23 Nov 08:55   Barnaby asks for the ordering key (the order itself goes in at 09:04)
     Mon 23 Nov (afternoon, scene 5)  the two quick cards: text customers, mark bikes ready; the passage "Hand back a bike"
     Mon 23 Nov 16:08-16:16  the report: asked 16:08, added with Martin's click 16:16 (the Build moment)
     Mon 23 Nov 16:21   Dev's two wheel builds move to Priya
     Tue 24 Nov 08:34   Priya's first morning (shop-tuesday-16x10: clock 08:34)
     Tue 24 Nov 09:39-09:43  Lisbon (09:41: the Quorum answer)
   The last round's data said 15:05 / 15:08 / 14:20 for the build, the reassignment and the passage, gave the 'build'
   moment only the ordering key (scene 5's two keys were missing), said "Priya starts today" at the Build (she starts
   Tuesday), and put Lisbon on Monday. WORLDS.state() reads WORLDS.moments by reference, so fixing the moments here
   fixes every state the libraries derive. */
(function () {
  const W = window.WORLDS, B = W.building, S = W.story, M = W.moments;

  // when keys were handed over and rooms built (plain words for Martin; times only where the canon gives one)
  const GIVEN = { create_purchase_order: 'Mon 08:55', notify: 'Mon afternoon', update_status: 'Mon afternoon', assign: 'Mon 16:21' };
  B.abilities.forEach(a => { if (GIVEN[a.tool]) a.given = GIVEN[a.tool]; if (a.tool === 'workload') a.built = 'Mon 16:16'; });
  B.rooms.reports.builtWhen = 'Mon 23 Nov, 16:16';
  B.passage.when = 'Mon afternoon';   // scene 5; the canon gives no minute, so no frame prints one

  M.handover = { when: 'Thu 19 Nov 2026, 21:47', given: [], built: false, passage: false };
  M.martinKey = { when: 'Mon 23 Nov 2026, 08:55', given: [], asking: 'create_purchase_order', built: false, passage: false };
  M.build = { when: 'Mon 23 Nov 2026, 16:16', given: ['create_purchase_order', 'notify', 'update_status'], built: 'building', passage: true };
  M.priyaTuesday = { when: 'Tue 24 Nov 2026, 08:34', given: ['create_purchase_order', 'notify', 'update_status', 'assign'], built: true, passage: true };

  S.martinKey.time = '08:55';
  /* The last pair of pads is in drawer 1 of the parts cabinet on the back-office shelf (CONTINUITY.md; Theo's parts
     list: "Brake pads ... drawer 1"), not in the stockroom as building.js has it. His walk: the job board (08:53), the
     parts drawer in the back office (08:54), the back door (08:55). */
  const pads = B.fixtures.find(f => f.id === 'pads');
  Object.assign(pads, { name: 'Brake pads (LAST PAIR!!), parts cabinet drawer 1', at: [8.3, 1.65], room: 'office' });
  S.martinKey.route = [
    { time: '08:53', at: [7.3, 8.05], did: 'Looked at tomorrow’s jobs', found: 'Five bikes due Tuesday', tool: 'jobs_due' },
    { time: '08:54', at: [8.3, 1.65], did: 'Checked each bike’s parts against the parts drawer', found: 'Anika’s brakes need 2 pairs of pads; 1 in drawer 1', tool: 'job_detail', short: true },
    { time: '08:55', at: [19.2, 6.4], did: 'At the back door', found: 'Ordering needs your key', tool: 'create_purchase_order', asking: true },
  ];
  S.build.when = 'Mon 23 Nov'; S.build.time = '16:16'; S.build.asked = '16:08'; S.build.moved = '16:21';
  S.build.after = 'Dev’s carrying thirty-one hours against his twenty. Priya starts tomorrow. Shall I give her the two wheel builds?';
  /* The report's result at 16:16, after scene 5's hand-backs (the seed: Aoife's 4476 is Dev's; Sofia's, Kwame's and Jana's
     bikes are ready, so they no longer count for Ravi). [name, booked hours, weekly capacity]; story.js had Ravi 22. */
  S.build.result = [['Dev', 31, 20], ['Ravi', 10.5, 30], ['Priya', 0, 30]];
  S.priyaTuesday.time = '08:34';
  S.lisbon = { when: 'Tue 24 Nov 2026', time: '09:41', from: '09:39', to: '09:43', note: 'Theo’s second day at the studio (desk 14)',
    quorum: 13, comfyui: 28, staged: true, preset: 'quorum' };

  /* who is collecting (the shop's own Tuesday screen, shop-tuesday-16x10: "Ready to collect: 4") */
  S.priyaTuesday.ready = [['Gareth Hughes', 'Orbea Orca'], ['Marisol Delgado', 'Cube Attain'], ['Niamh Fitzgerald', 'Marin Muirwoods'], ['Chidi Okonkwo', 'Merida Scultura']];
  /* Theo's README, item 4 (CONTINUITY: README item 4) */
  S.priyaTuesday.note = { text: 'Never trust the stock count on a Friday.', from: 'Theo', where: 'Theo’s README, item 4' };

  /* what each world calls the rooms, and the one colour each room keeps in every world (Martin's plan, Priya's chips,
     Theo's multiplane background). Hues are distinct at equal weight so no two areas read alike. */
  W.ROOMS = [
    { id: 'shop',      say: 'Shop & counter', short: 'Counter',   hue: '#17756C', tint: '#D5E8E4', deep: '#0F4F49', groups: ['counter', 'till'] },
    { id: 'office',    say: 'Back office',    short: 'Office',    hue: '#6A4C9C', tint: '#E4DDF0', deep: '#45306A', groups: ['office'] },
    { id: 'workshop',  say: 'Workshop',       short: 'Workshop',  hue: '#C25E17', tint: '#F6E0CD', deep: '#83400F', groups: ['workshop'] },
    { id: 'stockroom', say: 'Stockroom',      short: 'Stockroom', hue: '#3F7A2E', tint: '#DDEAD3', deep: '#2A5420', groups: ['stockroom'] },
    { id: 'goodsin',   say: 'Back door',      short: 'Back door', hue: '#2459A6', tint: '#D6E2F3', deep: '#173C72', groups: ['backdoor'] },
    { id: 'reports',   say: 'Workload',       short: 'Workload',  hue: '#B0285F', tint: '#F3D9E3', deep: '#7A1A41', groups: [], planned: 'Reports' },
  ];
  W.roomOf = groupId => W.ROOMS.find(r => r.groups.includes(groupId)) || W.ROOMS.find(r => r.id === 'reports');
})();
/* the workload report lives in the room that was planned for it, not in the office its group names */
window.WORLDS.roomOfAbility = a => a.tool === 'workload' ? window.WORLDS.ROOMS.find(r => r.id === 'reports') : window.WORLDS.roomOf(a.group);
