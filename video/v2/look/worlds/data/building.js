/* THE BUILDING: one model of Spokes & Sprockets, ground floor, that every world draws (Martin's plan, Theo's form,
   Priya's roll). Units are metres. x runs from the street front (x=0, Market Place) to the back wall (x=20, the back
   lane where deliveries come in); y runs from the north party wall (y=0) to the south party wall (y=9).
   Layout follows video/v2/WORLD.md: the counter at the front with the till; behind the counter the back office (one
   desk, a window onto the workshop floor, an outside window for the rain); the workshop floor with three stands; the
   stockroom; the back door. Room for Reports was planned in 2011 and never built (drawn dashed until the Build).

   ABILITIES: all 24 (23 Synapse found in Theo's code + 1 Barnaby built), from video/data.js, each placed in the room
   where it happens, at the object it happens at (anchor [x, y]). Plain words for Martin and Priya; `key` is the
   technical truth for Theo. States per story moment are derived by WORLDS.state(moment). */
(function () {
  const B = {
    size: { w: 20, h: 9 },
    outside: {
      street: { name: 'Market Place', side: 'front', x: -1.6 },
      lane: { name: 'Back lane', side: 'back', x: 21.4, note: 'deliveries' },
    },

    /* Rooms as polygons. The workshop wraps round the planned room. */
    rooms: {
      shop:      { name: 'Shop & counter', poly: [[0, 0], [6.5, 0], [6.5, 9], [0, 9]], label: [2.0, 6.2] },
      office:    { name: 'Back office', poly: [[6.5, 0], [9.8, 0], [9.8, 3.6], [6.5, 3.6]], label: [8.15, 2.5] },
      reports:   { name: 'Reports', planned: '2011', poly: [[9.8, 0], [12.4, 0], [12.4, 3.0], [9.8, 3.0]], label: [11.1, 1.9],
                   builtName: 'Workload', builtWhen: 'Mon 23 Nov, 15:05' },
      workshop:  { name: 'Workshop', poly: [[6.5, 3.6], [9.8, 3.6], [9.8, 3.0], [12.4, 3.0], [12.4, 0], [15, 0], [15, 9], [6.5, 9]], label: [11.0, 5.2] },
      stockroom: { name: 'Stockroom', poly: [[15, 0], [20, 0], [20, 5], [15, 5]], label: [17.5, 3.9] },
      goodsin:   { name: 'Back door', poly: [[15, 5], [20, 5], [20, 9], [15, 9]], label: [17.2, 8.2] },
    },

    /* Walls as segments [x1,y1,x2,y2]. ext = outside wall (thicker). Openings are cut by the drawing code. */
    walls: [
      { seg: [0, 0, 20, 0], ext: true },  { seg: [20, 0, 20, 9], ext: true },
      { seg: [20, 9, 0, 9], ext: true },  { seg: [0, 9, 0, 0], ext: true },
      { seg: [6.5, 0, 6.5, 3.6] },        { seg: [6.5, 3.6, 9.8, 3.6] },     { seg: [9.8, 0, 9.8, 3.6] },
      { seg: [6.5, 3.6, 6.5, 9] },        { seg: [15, 0, 15, 9] },           { seg: [15, 5, 20, 5] },
      { seg: [9.8, 3.0, 12.4, 3.0], planned: true }, { seg: [12.4, 0, 12.4, 3.0], planned: true },
    ],

    /* Doors and windows. at = [x, y] of the opening's start along its wall, len in metres, dir = wall direction,
       swing = which side the leaf opens into ('+' or '-' across the wall). */
    openings: [
      { id: 'front-window', kind: 'window', wall: 'x0', from: 0.5, to: 5.8, note: 'shop window' },
      { id: 'front-door', kind: 'door', wall: 'x0', from: 6.7, to: 7.8, swing: '+', note: 'front door' },
      { id: 'office-window-out', kind: 'window', wall: 'y0', from: 7.3, to: 9.1, note: 'rain on this window' },
      { id: 'office-door', kind: 'door', wall: 'x6.5', from: 1.2, to: 2.1, swing: '+', note: 'behind the counter' },
      { id: 'office-window-in', kind: 'window', wall: 'y3.6', from: 7.1, to: 9.3, note: 'onto the workshop floor' },
      { id: 'shop-arch', kind: 'arch', wall: 'x6.5', from: 4.4, to: 6.8, note: 'the doorway (the bell sits here)' },
      { id: 'reports-door', kind: 'door', wall: 'x9.8', from: 1.0, to: 1.9, swing: '+', planned: true },
      { id: 'stock-door', kind: 'door', wall: 'x15', from: 1.2, to: 2.2, swing: '+' },
      { id: 'lobby-door', kind: 'door', wall: 'x15', from: 6.2, to: 7.4, swing: '+' },
      { id: 'stock-lobby', kind: 'door', wall: 'y5', from: 17.2, to: 18.2, swing: '-' },
      { id: 'back-door', kind: 'double', wall: 'x20', from: 5.9, to: 8.1, swing: '-', note: 'where deliveries come in' },
    ],

    /* Furniture and fixtures (rects [x, y, w, h]) */
    fixtures: [
      { id: 'counter', name: 'Counter', rect: [3.8, 0.6, 0.8, 4.2], room: 'shop' },
      { id: 'till', name: 'Till', rect: [3.9, 1.0, 0.6, 0.5], room: 'shop' },
      { id: 'bell', name: 'Service bell', at: [4.2, 4.45], room: 'shop' },
      { id: 'forsale', name: 'Bikes for sale', rect: [0.7, 8.0, 5.2, 0.8], bikes: [[1.0, 8.4], [2.8, 8.4], [4.6, 8.4]], room: 'shop' },
      { id: 'desk', name: 'Desk (the shop PC)', rect: [7.0, 0.2, 2.4, 0.75], room: 'office' },
      { id: 'cabinet', name: 'Filing cabinet', rect: [6.65, 2.7, 0.55, 0.75], room: 'office' },
      { id: 'jobboard', name: 'Job board', rect: [6.6, 7.0, 0.12, 1.6], room: 'workshop' },
      { id: 'rota', name: 'Rota', rect: [6.6, 4.0, 0.12, 0.9], room: 'workshop' },
      { id: 'stand-dev', name: 'Dev’s stand', stand: [8.2, 6.9], who: 'Dev', room: 'workshop' },
      { id: 'stand-ravi', name: 'Ravi’s stand', stand: [10.6, 6.9], who: 'Ravi', room: 'workshop' },
      { id: 'stand-priya', name: 'Priya’s stand', stand: [13.0, 6.9], who: 'Priya', room: 'workshop' },
      { id: 'wheelbench', name: 'Wheel bench, truing stand', rect: [12.6, 0.2, 2.2, 0.7], room: 'workshop' },
      { id: 'pegboard', name: 'Pegboard', rect: [14.82, 2.9, 0.12, 2.8], room: 'workshop' },
      { id: 'bench', name: 'Workbench', rect: [7.2, 8.3, 7.4, 0.6], room: 'workshop' },
      { id: 'shelf-n', name: 'Shelving', rect: [15.3, 0.2, 4.5, 0.6], room: 'stockroom' },
      { id: 'shelf-e', name: 'Shelving', rect: [19.2, 0.9, 0.6, 3.8], room: 'stockroom' },
      { id: 'shelf-mid', name: 'Shelving', rect: [16.0, 2.1, 2.6, 0.7], room: 'stockroom' },
      { id: 'pads', name: 'Brake pads (LAST PAIR!!)', at: [16.6, 2.45], room: 'stockroom' },
      { id: 'cartons', name: 'Deliveries', rect: [15.4, 7.6, 1.4, 1.1], room: 'goodsin' },
      { id: 'van', name: 'Madison’s van', rect: [20.8, 5.5, 4.6, 2.9], outside: true },
    ],

    /* Groups: where each kind of work happens, in the household's words. order = front door to back door. */
    groups: [
      { id: 'counter',   name: 'The counter',       room: 'shop',      color: 0 },
      { id: 'till',      name: 'The till',          room: 'shop',      color: 1 },
      { id: 'workshop',  name: 'The workshop floor', room: 'workshop', color: 2 },
      { id: 'stockroom', name: 'The stockroom',     room: 'stockroom', color: 3 },
      { id: 'backdoor',  name: 'The back door',     room: 'goodsin',   color: 4 },
      { id: 'office',    name: 'The back office',   room: 'office',    color: 5 },
    ],

    /* All 24. start: 'lit' (open from the start: the 6 read-only), 'key', 'shut' (deny-listed), 'built' (by Barnaby).
       given: when Martin handed over the key. anchor: where it happens. */
    abilities: [
      { tool: 'search',                key: 'GET /api/customers/search/{name}',          say: 'Find a customer',                group: 'counter',   start: 'lit',  anchor: [3.4, 3.3] },
      { tool: 'customer_detail',       key: 'GET /api/customers/{customer_id}',          say: 'A customer’s details and bikes', group: 'counter', start: 'key', anchor: [3.4, 2.6] },
      { tool: 'add_customer',          key: 'POST /api/customers',                       say: 'Add a customer',                 group: 'counter',   start: 'key',  anchor: [3.4, 3.9] },
      { tool: 'book_job',              key: 'POST /api/jobs',                            say: 'Book a bike in',                 group: 'counter',   start: 'key',  anchor: [3.4, 4.5] },
      { tool: 'notify',                key: 'POST /api/customers/{customer_id}/notify',  say: 'Text or email a customer',       group: 'counter',   start: 'key',  anchor: [4.9, 3.0] },
      { tool: 'recent_notifications',  key: 'GET /api/notifications/recent',             say: 'Recent texts and emails',        group: 'counter',   start: 'key',  anchor: [4.9, 3.7] },
      { tool: 'unpaid',                key: 'GET /api/invoices/unpaid',                  say: 'Unpaid invoices',                group: 'till',      start: 'key',  anchor: [4.2, 0.85] },
      { tool: 'create_invoice',        key: 'POST /api/invoices',                        say: 'Raise an invoice',               group: 'till',      start: 'key',  anchor: [4.9, 1.25] },
      { tool: 'takings',               key: 'GET /api/reports/takings/{day}',            say: 'Money taken on a day',           group: 'till',      start: 'key',  anchor: [4.9, 1.9] },
      { tool: 'open_jobs',             key: 'GET /api/jobs/open',                        say: 'Open jobs',                      group: 'workshop',  start: 'lit',  anchor: [7.0, 7.4] },
      { tool: 'jobs_due',              key: 'GET /api/jobs/due/{day}',                   say: 'Jobs due on a day',              group: 'workshop',  start: 'lit',  anchor: [7.0, 8.1] },
      { tool: 'job_detail',            key: 'GET /api/jobs/{job_id}',                    say: 'One job, and the parts it needs', group: 'workshop', start: 'lit',  anchor: [9.4, 6.9] },
      { tool: 'update_status',         key: 'POST /api/jobs/{job_id}/status',            say: 'Change a job’s status',     group: 'workshop',  start: 'key',  anchor: [11.8, 6.9] },
      { tool: 'assign',                key: 'POST /api/jobs/{job_id}/assign',            say: 'Give a job to another mechanic', group: 'workshop',  start: 'key',  anchor: [12.0, 5.6], given: 'Mon 15:08' },
      { tool: 'mechanics',             key: 'GET /api/mechanics',                        say: 'Who works here, and their hours', group: 'workshop', start: 'lit',  anchor: [7.0, 4.45] },
      { tool: 'cancel_job',            key: 'DELETE /api/jobs/{job_id}',                 say: 'Cancel a job (there’s no undo)', group: 'workshop', start: 'shut', anchor: [9.4, 8.0] },
      { tool: 'parts_low',             key: 'GET /api/parts/low',                        say: 'What’s running low',        group: 'stockroom', start: 'lit',  anchor: [16.6, 3.2] },
      { tool: 'parts',                 key: 'GET /api/parts',                            say: 'Everything on the shelves',      group: 'stockroom', start: 'key',  anchor: [17.6, 1.3] },
      { tool: 'adjust',                key: 'POST /api/parts/{part_id}/adjust',          say: 'Change stock levels',            group: 'stockroom', start: 'key',  anchor: [18.6, 3.4] },
      { tool: 'create_purchase_order', key: 'POST /api/purchase-orders',                 say: 'Order from a supplier',          group: 'backdoor',  start: 'key',  anchor: [19.2, 6.4], given: 'Mon 08:55' },
      { tool: 'purchase_orders',       key: 'GET /api/purchase-orders',                  say: 'Past orders',                    group: 'backdoor',  start: 'key',  anchor: [17.6, 6.2] },
      { tool: 'receive',               key: 'POST /api/purchase-orders/{po_id}/receive', say: 'Book in a delivery',             group: 'backdoor',  start: 'key',  anchor: [16.4, 7.2] },
      { tool: 'today_at_a_glance',     key: 'GET /api/reports/today',                    say: 'Today at a glance',              group: 'office',    start: 'key',  anchor: [8.2, 1.5] },
      { tool: 'workload',              key: 'GET /api/reports/workload/{day}',           say: 'Each mechanic’s hours this week', group: 'office', start: 'built', anchor: [11.1, 1.2], built: 'Mon 15:05' },
    ],

    /* The service passage Barnaby composed at 14:20 (synapse build --custom, 38 s): hand_back_finished_bike on shop-k1,
       from get_job + notify_customer + set_job_status. Drawn from the workshop floor to the counter and back. */
    passage: { name: 'Hand back a bike', when: 'Mon 14:20', tool: 'hand_back_finished_bike', server: 'shop-k1',
      steps: [['Look up the job', 'job_detail'], ['Text the customer', 'notify'], ['Mark it ready', 'update_status']],
      path: [[11.8, 6.9], [7.4, 5.6], [4.9, 3.0], [7.4, 5.6], [11.8, 6.9]] },
  };

  /* Moments in the story and what is true at each. */
  const MOMENTS = {
    handover: { when: 'Thu 19 Nov 2026, 21:47', given: [], built: false, passage: false },
    martinKey: { when: 'Mon 23 Nov, 08:55', given: [], asking: 'create_purchase_order', built: false, passage: false },
    build: { when: 'Mon 23 Nov, 15:05', given: ['create_purchase_order'], built: 'building', passage: true },
    priyaTuesday: { when: 'Tue 24 Nov, 08:40', given: ['create_purchase_order', 'assign'], built: true, passage: true },
  };

  /** state(moment) -> abilities with .state in 'lit' | 'key' | 'asking' | 'shut' | 'planned' | 'new' */
  function state(momentId) {
    const m = MOMENTS[momentId];
    return B.abilities.map(a => {
      let s = a.start;
      if (s === 'built') s = m.built === true ? 'lit' : m.built === 'building' ? 'new' : 'planned';
      if (s === 'key' && m.given.includes(a.tool)) s = 'lit';
      if (m.asking === a.tool) s = 'asking';
      return Object.assign({}, a, { state: s });
    });
  }
  function counts(momentId) {
    const st = state(momentId), c = { lit: 0, key: 0, asking: 0, shut: 0, planned: 0, new: 0 };
    st.forEach(a => c[a.state]++);
    c.found = st.filter(a => a.start !== 'built').length;   // 23, what Synapse found in Theo's code
    c.total = c.found + (MOMENTS[momentId].built ? 1 : 0);
    return c;
  }
  window.WORLDS = Object.assign(window.WORLDS || {}, { building: B, moments: MOMENTS, state, counts });
})();
