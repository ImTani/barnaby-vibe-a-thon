/* The story content every identity direction shows, in the household's words.
   Lines follow the v2 script (docs/script.html). Facts come from the real run (video/data.js), the recorded event log
   (ui/fixtures/demo-run.json, for Synapse timings) and the shop's seed (systems/spokes-and-sprockets/seed.py).
   render.js appends the real data (endpoints, the diff, the test line) and writes this into each direction's folder
   as content.js, so each folder is self-contained. Edit this file, not the copies. */
window.STORY = {
  shop: 'Spokes & Sprockets',
  strap: 'a Hartley family workshop, est. 1987',
  today: 'Monday 23 November',
  todayShort: 'Mon 23 Nov',

  /* The handover (script scene 2, Theo's last night). Real: 23 found, the 6 read-only ones open. */
  arrival: {
    when: 'Fri 20 Nov', time: '21:40', by: 'Theo',
    ask: 'Barnaby, this is the shop’s system. I wrote it when I was fourteen, so be kind. Look after them for me.',
    say: 'It’s a lovely old house, Theo. I’ll only look around for now. Nobody’s given me any keys.',
    filed: 'Twenty-three things found. Six open to start, all look-only.',
  },
  morning: { time: '08:52', ask: 'Right. Barnaby, is it?', say: 'Good morning, Martin.' },

  /* Moment 1: listening and answering (script scene 3) */
  m1: {
    time: '08:53', by: 'Martin',
    ask: 'What’s due tomorrow, and are we short on anything?',
    say: 'Five bikes due tomorrow. Only Anika’s is a problem: her brakes need two pairs of pads, and we’ve one left.',
    steps: [   // what he's doing, in a person's words; `doing` while it happens, `did` + `found` after
      { doing: 'Checking tomorrow’s jobs', did: 'Looked at tomorrow’s jobs', found: 'Five bikes due Tuesday', room: 'jobs' },
      { doing: 'Checking parts', did: 'Checked each bike’s parts against the shelf', found: 'Four covered, one short', room: 'parts' },
    ],
    due: [
      { n: 4471, who: 'Rachel Okafor', bike: 'Genesis Croix de Fer', work: 'Wheel build (front)', mech: 'Dev', parts: 'Spokes and rim on the shelf', ok: true },
      { n: 4475, who: 'Sofia Ferreira', bike: 'Giant Defy', work: 'Full service', mech: 'Ravi', parts: 'No parts needed', ok: true },
      { n: 4478, who: 'Anika Banerjee', bike: 'Trek FX 3', work: 'Brake bleed and new pads', mech: 'Dev', parts: 'Needs 2 pairs of pads; 1 on the shelf', ok: false },
      { n: 4485, who: 'Thanh Nguyen', bike: 'Surly Long Haul Trucker', work: 'Headset', mech: 'Dev', parts: 'Headset on the shelf', ok: true },
      { n: 4490, who: 'Kwame Mensah', bike: 'Boardman SLR', work: 'Bottom bracket', mech: 'Ravi', parts: 'Bottom bracket on the shelf', ok: true },
    ],
    checkedSoFar: 3,   // for the "working" frame (1a): three of the five checked, Anika's in hand
  },

  /* Moment 2: asking for a key (script scene 4) */
  m2: {
    time: '08:55', by: 'Martin',
    ask: 'Order ten from Madison, then.',
    say: 'I can’t order parts myself yet, but Theo built the system a way to. Shall I take that on?',
    card: {
      title: 'Let Barnaby order parts from your suppliers',
      lines: [
        ['What it means', 'Theo’s system can already send orders to Madison and your other suppliers. This lets me use it.'],
        ['What stays locked', 'Only placing orders. Booking in deliveries and changing stock stay locked.'],
        ['Each time', 'I’ll still check with you before an order goes in.'],
      ],
      technical: 'POST /api/purchase-orders',
      yes: 'Allow', no: 'Not now',
    },
    after: 'Ten pairs from Madison, at six pounds fifty each. Shall I place it?',
  },

  /* Compose (script scene 5): three hand-backs, then one step. Shown on the plan as a service passage. */
  compose: {
    time: '14:20',
    handed: ['Sofia', 'Kwame', 'Jana'],
    say: 'That’s three bikes handed back today, and the same four steps each time. Shall I make it one?',
  },

  /* Moment 3: explaining a change before Martin approves it (script scene 6) */
  m3: {
    time: '15:05', by: 'Martin',
    ask: 'Who’s got too much on this week?',
    before: 'The system can’t tell me; there’s no report for it. Theo always meant to write one.',
    say: 'Done. I’ve written the report on a copy, and nothing’s changed yet. Have a look before I add it.',
    spoken: 'Done. It adds up each mechanic’s booked hours for the week, the way Theo’s notes count them. It only reads the job board, it can’t change a thing, and all twenty-two of Theo’s checks still pass. Shall I add it?',
    card: {
      title: 'Add a weekly workload report',
      lines: [
        ['What it does', 'Adds up each mechanic’s booked hours for the week, Monday to Saturday, the way Theo’s notes count them.'],
        ['What it reads', 'Only the job board. It changes nothing.'],
        ['Theo’s checks', 'All 22 pass: Theo’s own 19, and 3 new ones for this report.'],
        ['If you change your mind', 'It can be undone.'],
      ],
      where: 'Written on a copy of the system. Nothing changes until you add it.',
      clickOnly: 'A change like this needs a click, not a spoken yes.',
      technical: 'GET /api/reports/workload/{day}',
      yes: 'Add it', no: 'Not now', see: 'See the change',
      files: {
        'routes_reports.py': 'Where the report can be found',
        'services.py': 'The adding-up itself',
        'tests/test_workload.py': 'Three new checks',
      },
    },
    after: 'Dev’s carrying thirty-one hours against his twenty. Priya starts today. Shall I give her the two wheel builds?',
  },

  /* Moment 4a, Martin: the floor plan. Every one of the 24 abilities (23 found + 1 built), grouped into rooms.
     state: lit (he can use it), key (he could ask), shut (never: deny-listed). given = a key Martin handed over today. */
  rooms: [
    { id: 'jobs', name: 'Jobs', place: 'the workshop', items: [
      ['GET /api/jobs/open', 'Open jobs', 'lit'],
      ['GET /api/jobs/due/{day}', 'Jobs due on a day', 'lit'],
      ['GET /api/jobs/{job_id}', 'One job, and the parts it needs', 'lit'],
      ['POST /api/jobs/{job_id}/assign', 'Give a job to another mechanic', 'lit', 'given'],
      ['POST /api/jobs', 'Book a new job', 'key'],
      ['POST /api/jobs/{job_id}/status', 'Change a job’s status', 'key'],
      ['DELETE /api/jobs/{job_id}', 'Cancel a job (no undo)', 'shut'],
    ] },
    { id: 'customers', name: 'Customers', place: 'the counter', items: [
      ['GET /api/customers/search/{name}', 'Find a customer', 'lit'],
      ['GET /api/customers/{customer_id}', 'A customer’s details and bikes', 'key'],
      ['POST /api/customers', 'Add a customer', 'key'],
      ['POST /api/customers/{customer_id}/notify', 'Text or email a customer', 'key'],
      ['GET /api/notifications/recent', 'Recent texts and emails', 'key'],
    ] },
    { id: 'mechanics', name: 'Mechanics', place: 'the rota', items: [
      ['GET /api/mechanics', 'Who works here, and their hours', 'lit'],
    ] },
    { id: 'parts', name: 'Parts', place: 'the stockroom', items: [
      ['GET /api/parts/low', 'What’s running low', 'lit'],
      ['GET /api/parts', 'Everything on the shelves', 'key'],
      ['POST /api/parts/{part_id}/adjust', 'Change stock levels', 'key'],
    ] },
    { id: 'orders', name: 'Orders', place: 'suppliers', items: [
      ['POST /api/purchase-orders', 'Order from a supplier', 'lit', 'given'],
      ['GET /api/purchase-orders', 'Past orders', 'key'],
      ['POST /api/purchase-orders/{po_id}/receive', 'Book in a delivery', 'key'],
    ] },
    { id: 'invoices', name: 'Invoices', place: 'the till', items: [
      ['GET /api/invoices/unpaid', 'Unpaid invoices', 'key'],
      ['POST /api/invoices', 'Raise an invoice', 'key'],
    ] },
    { id: 'reports', name: 'Reports', place: 'the office', items: [
      ['GET /api/reports/today', 'Today at a glance', 'key'],
      ['GET /api/reports/takings/{day}', 'Money taken on a day', 'key'],
    ] },
    { id: 'workload', name: 'Workload', place: 'built today', isNew: true, items: [
      ['GET /api/reports/workload/{day}', 'Each mechanic’s hours this week', 'lit', 'new'],
    ] },
  ],
  passage: {
    name: 'Hand back a bike',
    between: ['jobs', 'customers'],
    steps: ['Look up the job', 'Text the customer', 'Mark it ready'],
    note: 'Made this afternoon: Martin hands a bike back a dozen times a day.',
    time: '14:20',
  },
  keysGiven: [
    ['Ordering from suppliers', '08:55'],
    ['Giving jobs to another mechanic', '15:08'],
  ],
  counts: { can: 9, of: 24, passages: 1 },

  /* Moment 4b, Theo: what a developer would need. All real (data.js, demo-run.json, README). */
  theo: {
    system: { name: 'shop', title: 'the shop’s back office', repo: '.demo/spokes-and-sprockets', base: 'http://127.0.0.1:8101' },
    exposed: ['GET /api/jobs/open', 'GET /api/jobs/due/{day}', 'GET /api/jobs/{job_id}', 'GET /api/parts/low',
      'GET /api/customers/search/{name}', 'GET /api/mechanics', 'POST /api/purchase-orders',
      'GET /api/reports/workload/{day}', 'POST /api/jobs/{job_id}/assign'],
    denied: ['DELETE /api/jobs/{job_id}'],
    skill: { tool: 'hand_back_finished_bike', server: 'shop-k1', from: ['get_job', 'notify_customer', 'set_job_status'],
      description: 'Hand back a finished bike: given a job_id, look up the job’s customer and bike, text the customer by SMS (logged against that job) that their bike is ready to collect, then mark the job’s status as ready.' },
    /* every Synapse run that shaped the shop's server, in story order; seconds are Synapse's own, from the recorded log */
    synapse: [
      { when: 'Fri 21:40', cmd: 'build --auto --local', what: 'read Theo’s code', out: '23 endpoints discovered · 6 read-only exposed', s: 0.48 },
      { when: '08:55', cmd: 'build --auto --local --endpoints …,POST /api/purchase-orders', what: 'unlock', out: '7 exposed', s: 0.32 },
      { when: '14:20', cmd: 'build --custom -q "hand back a finished bike…"', what: 'compose', out: 'hand_back_finished_bike → shop-k1', s: 38.0 },
      { when: '15:06', cmd: 'build --auto --local (after merge, re-discover)', what: 'build', out: '24 endpoints discovered · 8 exposed', s: 0.41 },
      { when: '15:08', cmd: 'build --auto --local --endpoints …,POST /api/jobs/{job_id}/assign', what: 'unlock', out: '9 exposed', s: 0.32 },
    ],
    /* the m1 turn, call by call (real args); results are what the shop's API returns for the seed */
    trace: {
      ask: 'What’s due tomorrow, and are we short on anything?', ms: 8379, modelTurns: 7,
      calls: [
        { tool: 'jobs_due', args: '{"day":"2026-11-24"}', res: '5 jobs: 4471 4475 4478 4485 4490' },
        { tool: 'job_detail', args: '{"job_id":4471}', res: 'SPK-DT-292 ×32 (40) · RIM-DT-R460 ×1 (2)' },
        { tool: 'job_detail', args: '{"job_id":4475}', res: 'no parts' },
        { tool: 'job_detail', args: '{"job_id":4478}', res: 'BP-SH-RES ×2 (1) · FLD-DOT51 ×1 (2)', short: true },
        { tool: 'job_detail', args: '{"job_id":4485}', res: 'HDS-FSA-118 ×1 (4)' },
        { tool: 'job_detail', args: '{"job_id":4490}', res: 'BB-SH-HT2 ×1 (3)' },
      ],
    },
    build: { endToEnd: '74.7 s', files: 3, added: 114, removed: 0, worktree: 'git worktree, then fast-forward merge after approval' },
  },

  /* Moment 4c, Priya, day one: PROPOSAL. Her bench as repair tags. The two wheel builds moved to her at 15:08. */
  priya: {
    time: '15:30', by: 'Priya',
    ask: 'Sorry, what can this thing actually do?',
    say: 'Most of what the shop needs. Theo built nearly all of it; I added a room today.',   // script says "this morning", but the build is at 15:05: flagged
    aside: 'And he left you a note.',
    note: { text: 'Never trust the stock count on a Friday.', from: 'Theo' },
    tags: [
      { n: 4471, who: 'Rachel Okafor', bike: 'Genesis Croix de Fer', colour: 'green', work: 'Wheel build, front, 32 hole',
        hours: '6 hrs', due: 'Tue 24 Nov', dueWord: 'Tomorrow', from: 'Dev',
        parts: [['32 spokes, DT Swiss 292 mm', 'on the shelf', true], ['Rim, DT Swiss R460 700c', 'on the shelf', true]], ready: true },
      { n: 4472, who: 'Magnus Lindqvist', bike: 'Bianchi Infinito', colour: 'celeste', work: 'Wheel build, rear, 32 hole',
        hours: '5½ hrs', due: 'Wed 25 Nov', dueWord: 'Wednesday', from: 'Dev',
        parts: [['32 spokes, DT Swiss 292 mm', '40 on the shelf for both wheels; you need 64', false], ['Rim, DT Swiss R460 700c', 'on the shelf', true]], ready: false },
    ],
    asks: [
      ['What’s on my bench?', 'your jobs, soonest first'],
      ['What does Rachel’s wheel need?', 'the parts, and what’s on the shelf'],
      ['Is anything running low?', 'the stockroom'],
      ['Whose bike is the green Genesis?', 'the counter'],
      ['Rachel’s is done. Hand it back.', 'I’ll text her and mark it ready, once you say yes'],
    ],
  },
};
