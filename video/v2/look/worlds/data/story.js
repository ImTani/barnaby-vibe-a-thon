/* THE STORY: lines and facts every world shows. Sources: docs/script.html (v2), the director's later notes (Barnaby
   calls Theo "sir" once; Priya's scene on Tuesday morning; technical with Theo, plain with Martin and Priya),
   video/data.js (the real run), video/v2/look/shop-pc/shop-data.js and systems/spokes-and-sprockets/seed.py.
   Dialogue follows script v2.1 (coordinator, 25 Nov). Scene 6 split: at the moment the report lands, Theo sees the diff
   and the tests passing, Martin a new room, Priya two new jobs on her bench (the wheel builds moved to her at 15:08). */
window.WORLDS = Object.assign(window.WORLDS || {}, {
  story: {
    shop: 'Spokes & Sprockets', strap: 'a Hartley family workshop, est. 1987',

    /* THEO: the handover. Thu 19 Nov 2026, 21:47, the shop PC, rain. Synapse: build --auto --local, 0.48 s,
       23 endpoints discovered, 6 read-only exposed (recorded log). */
    handover: {
      when: 'Thu 19 Nov 2026', time: '21:47',
      theo: 'Right. Barnaby, this is the shop’s system. I wrote it when I was fourteen, so be kind. Look after them for me.',
      barnaby: 'Twenty-three endpoints, sir. I’ve taken the six that only read; nobody’s given me any keys yet.',
      theo2: 'It’s Theo. And don’t call my uncle sir: he’ll unplug you.',
      synapse: { cmd: 'synapse build --auto --local', seconds: 0.48, found: 23, exposed: 6, denied: 1,
        repo: '.demo/spokes-and-sprockets', base: 'http://127.0.0.1:8101', frames24: 11.5 },
      files: ['app.py', 'db.py', 'services.py', 'routes_customers.py', 'routes_jobs.py', 'routes_mechanics.py', 'routes_money.py', 'routes_parts.py', 'routes_reports.py'],
      routesPerFile: { 'routes_customers.py': 5, 'routes_jobs.py': 7, 'routes_mechanics.py': 1, 'routes_money.py': 2, 'routes_parts.py': 6, 'routes_reports.py': 2 },
      readme: 'README: notes for whoever looks after it next. bye x',
      history: [['2009-03-14', 'first version of the shop system!! (bye access database)'], ['2009-07-02', 'jobs + customers pages, made it look proper'],
        ['2011-03-19', 'parts + ordering from suppliers. reports page (coming soon)'], ['2014-10-08', 'invoices, mechanics, moved logic into services.py'],
        ['2019-02-23', 'tests!! finally. seed script for the training laptop'], ['2026-11-19', 'README: notes for whoever looks after it next. bye x']],
    },

    /* MARTIN: the key. Mon 23 Nov. 08:53 he asked what's due tomorrow; Barnaby walked Jobs then Parts. 08:55 the key. */
    martinKey: {
      when: 'Mon 23 Nov 2026', time: '08:55',
      earlier: { time: '08:53', ask: 'What’s due tomorrow, and are we short on anything?',
        say: 'Five bikes due tomorrow. Only Anika’s is a problem: her brakes need two pairs of pads, and we’ve one left.' },
      route: [
        { time: '08:53', at: [7.0, 8.1], did: 'Looked at tomorrow’s jobs', found: 'Five bikes due Tuesday', tool: 'jobs_due' },
        { time: '08:53', at: [16.6, 2.45], did: 'Checked each bike’s parts against the shelf', found: 'Anika’s brakes need 2 pairs of pads; 1 on the shelf', tool: 'job_detail', short: true },
        { time: '08:55', at: [19.2, 6.4], did: 'At the back door', found: 'Ordering needs your key', tool: 'create_purchase_order', asking: true },
      ],
      martin: 'Order ten from Madison, then.',
      barnaby: 'I can’t order parts myself yet, but Theo built the system a way to. Shall I take that on?',
      card: {
        title: 'Let Barnaby order parts from your suppliers',
        lines: [
          ['What it means', 'Theo’s system can already send orders to Madison and your other suppliers. This lets me use it.'],
          ['What stays locked', 'Only placing orders. Booking in deliveries and changing stock stay locked.'],
          ['Each time', 'I’ll still check with you before an order goes in.'],
        ],
        technical: 'POST /api/purchase-orders', yes: 'Allow', no: 'Not now',
      },
      martinYes: 'Go on, then.',
      after: 'Ten pairs from Madison, at six pounds fifty each. Shall I place it?',
      order: { part: 'Brake pads (Shimano resin, pair)', qty: 10, supplier: 'Madison', each: 6.5, po: 3 },
      anika: { job: 4478, who: 'Anika Banerjee', bike: 'Trek FX 3', needs: 2, onShelf: 1 },
    },

    /* THE BUILD: Mon 15:05. The same moment for all three. */
    build: {
      when: 'Mon 23 Nov', time: '15:05',
      split: { theo: 'the diff and the tests passing', martin: 'a new room', priya: 'two new jobs on her bench' },
      martin: 'Who’s got too much on this week?',
      before: 'The system can’t tell me; there’s no report for it. Theo always meant to write one.',
      barnaby: 'Done. It adds up each mechanic’s booked hours for the week, the way Theo’s notes count them. It only reads the job board, it can’t change a thing, and all twenty-two of Theo’s checks still pass. Shall I add it?',
      card: {
        title: 'Add a weekly workload report',
        lines: [
          ['What it does', 'Adds up each mechanic’s booked hours for the week, Monday to Saturday, the way Theo’s notes count them.'],
          ['What it reads', 'Only the job board. It changes nothing.'],
          ['Theo’s checks', 'All 22 pass: Theo’s own 19, and 3 new ones for this report.'],
          ['If you change your mind', 'It can be undone.'],
        ],
        yes: 'Add it', no: 'Not now', see: 'See the change',
      },
      technical: { endpoint: 'GET /api/reports/workload/{day}', tool: 'mcp__shop__workload',
        files: [['routes_reports.py', '+11'], ['services.py', '+34'], ['tests/test_workload.py', '+69']], added: 114, removed: 0,
        tested: '22 passed, 1 warning in 1.55s', where: 'git worktree; fast-forward merge after approval', endToEnd: '74.7 s',
        rediscover: 'synapse build --auto --local · 24 endpoints · 0.41 s',
        fn: 'def mechanic_workload(day):', route: '@router.get("/api/reports/workload/{day}")' },
      result: [['Dev', 31, 20], ['Ravi', 22, 30], ['Priya', 0, 30]],   // [name, booked hours, weekly capacity]
      after: 'Dev’s carrying thirty-one hours against his twenty. Priya starts today. Shall I give her the two wheel builds?',
    },

    /* LISBON (scene 8, staged): Mon 23 Nov 2026, Theo's first day at the studio. Counts from real Synapse scans. */
    lisbon: { when: 'Mon 23 Nov 2026', note: 'Theo’s first day at the studio', quorum: 13, comfyui: 28, staged: true },

    /* PRIYA: Tuesday morning (moved by the director). Her bench: the two wheel builds moved to her Mon 15:08. */
    priyaTuesday: {
      when: 'Tue 24 Nov 2026', time: '08:40',
      priya: 'So you’re why I’ve got two wheel builds on my first day?',
      barnaby: 'Guilty. Dev had thirty-one hours booked. You had none.',
      priya2: 'Fair. What else can this thing do?',
      barnaby2: 'Your jobs, the parts they need, who’s collecting what. And Theo left you a note: never trust the stock count on a Friday.',
      note: { text: 'Never trust the stock count on a Friday.', from: 'Theo', where: 'Theo’s README' },
      collecting: 'ready',   // "who's collecting what": jobs whose status is ready (open_jobs lists them, with customer and bike)
      bench: [
        { job: 4471, who: 'Rachel Okafor', bike: 'Genesis Croix de Fer', work: 'Wheel build, front, 32 hole', hours: 6, due: 'Today', dueDate: 'Tue 24 Nov', from: 'Dev',
          parts: [['32 spokes, DT Swiss 292 mm', true], ['Rim, DT Swiss R460 700c', true]] },
        { job: 4472, who: 'Magnus Lindqvist', bike: 'Bianchi Infinito', work: 'Wheel build, rear, 32 hole', hours: 5.5, due: 'Wednesday', dueDate: 'Wed 25 Nov', from: 'Dev',
          parts: [['32 spokes, DT Swiss 292 mm', false, '40 on the shelf; both wheels need 64'], ['Rim, DT Swiss R460 700c', true]] },
      ],
      week: { booked: 11.5, capacity: 30 },
      asks: [   // things she can say, each one a real ability that's open to Barnaby on Tuesday
        ['What’s on my bench?', 'open_jobs'], ['What does Rachel’s wheel need?', 'job_detail'],
        ['Is anything running low?', 'parts_low'], ['Whose is the Genesis on my stand?', 'open_jobs'],
        ['Rachel’s is done. Hand it back.', 'passage'], ['Who’s got too much on?', 'workload'],
        ['Order more spokes.', 'create_purchase_order'],
      ],
    },
  },
});
