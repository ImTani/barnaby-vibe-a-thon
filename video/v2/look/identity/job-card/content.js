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

/* the real run (generated from video/data.js) */
window.STORY.real = {"endpoints":[{"key":"GET /api/customers/search/{name}","tool":"search","read_only":true,"description":"Find customers whose name contains the given text."},{"key":"GET /api/customers/{customer_id}","tool":"customer_detail","read_only":true,"description":"One customer: contact details, last visit, their bikes and recent jobs."},{"key":"POST /api/customers","tool":"add_customer","read_only":false,"description":"Add a new customer."},{"key":"POST /api/customers/{customer_id}/notify","tool":"notify","read_only":false,"description":"Text (channel sms, the default) or email a customer, e.g. to say their bike is ready."},{"key":"GET /api/notifications/recent","tool":"recent_notifications","read_only":true,"description":"The last texts and emails the shop sent to customers."},{"key":"GET /api/jobs/open","tool":"open_jobs","read_only":true,"description":"All repair jobs that haven't been collected yet, soonest due first, with customer, bike, mechanic, estimated hours and status."},{"key":"GET /api/jobs/due/{day}","tool":"jobs_due","read_only":true,"description":"Repair jobs due on a given day. day is YYYY-MM-DD, or the word 'today'."},{"key":"GET /api/jobs/{job_id}","tool":"job_detail","read_only":true,"description":"One repair job, including the parts it needs and how many of each are in stock."},{"key":"POST /api/jobs","tool":"book_job","read_only":false,"description":"Book a new repair job for a customer. due_date is YYYY-MM-DD (defaults to today); mechanic is a first name."},{"key":"POST /api/jobs/{job_id}/status","tool":"update_status","read_only":false,"description":"Change a job's status: booked, in progress, waiting on parts, ready, or collected."},{"key":"POST /api/jobs/{job_id}/assign","tool":"assign","read_only":false,"description":"Give a job to a different mechanic, by first name (e.g. Priya)."},{"key":"DELETE /api/jobs/{job_id}","tool":"cancel_job","read_only":false,"description":"Cancel and delete a job completely. Careful!! there is no undo."},{"key":"GET /api/mechanics","tool":"mechanics","read_only":true,"description":"The mechanics and how many hours of jobs each can take on per week (Mon-Sat)."},{"key":"GET /api/invoices/unpaid","tool":"unpaid","read_only":true,"description":"Invoices customers haven't paid yet."},{"key":"POST /api/invoices","tool":"create_invoice","read_only":false,"description":"Raise an invoice for a finished job (amount in pounds)."},{"key":"GET /api/parts","tool":"parts","read_only":true,"description":"Every part we stock: SKU, name, how many are in stock, reorder level, usual supplier and unit cost."},{"key":"GET /api/parts/low","tool":"parts_low","read_only":true,"description":"Parts at or below their reorder level (time to order more)."},{"key":"POST /api/parts/{part_id}/adjust","tool":"adjust","read_only":false,"description":"Add (positive change) or remove (negative change) stock for a part, with a reason."},{"key":"GET /api/purchase-orders","tool":"purchase_orders","read_only":true,"description":"All purchase orders to suppliers, newest first."},{"key":"POST /api/purchase-orders","tool":"create_purchase_order","read_only":false,"description":"Order more of a part from a supplier. supplier defaults to the part's usual one."},{"key":"POST /api/purchase-orders/{po_id}/receive","tool":"receive","read_only":false,"description":"Mark a purchase order as delivered and add the parts to stock."},{"key":"GET /api/reports/today","tool":"today_at_a_glance","read_only":true,"description":"Today at a glance: open jobs, jobs due today, bikes ready to collect, low-stock parts, unpaid invoices."},{"key":"GET /api/reports/takings/{day}","tool":"takings","read_only":true,"description":"Money taken (paid invoices) on a day. day is YYYY-MM-DD, or the word 'today'."}],"starter":["GET /api/jobs/open","GET /api/jobs/due/{day}","GET /api/jobs/{job_id}","GET /api/parts/low","GET /api/customers/search/{name}","GET /api/mechanics"],"diff":"diff --git a/routes_reports.py b/routes_reports.py\nindex 0168031..f5cafbe 100644\n--- a/routes_reports.py\n+++ b/routes_reports.py\n@@ -19,3 +19,14 @@ def takings(day: str):\n     if day == \"today\":\n         day = today()\n     return services.takings_on(day)\n+\n+\n+@router.get(\"/api/reports/workload/{day}\")\n+def workload(day: str):\n+    \"\"\"Mechanic workload for the shop week (Mon-Sat) containing a day. day is YYYY-MM-DD, or the word 'today';\n+    a Sunday means the Mon-Sat week just gone. Returns {ok, week_start, week_end, mechanics: [{mechanic_id, name,\n+    weekly_capacity_hours, workload_hours, spare_hours, overloaded, job_count}]}, most overloaded first.\n+    Workload is the estimated hours of jobs due that week that aren't ready or collected yet.\"\"\"\n+    if day == \"today\":\n+        day = today()\n+    return services.mechanic_workload(day)\ndiff --git a/services.py b/services.py\nindex b50fa41..066506f 100644\n--- a/services.py\n+++ b/services.py\n@@ -360,3 +360,37 @@ def week_bounds(day=None):\n     monday = date.fromordinal(d.toordinal() - d.weekday())\n     saturday = date.fromordinal(monday.toordinal() + 5)\n     return monday.isoformat(), saturday.isoformat()\n+\n+\n+def mechanic_workload(day):\n+    \"\"\"Each mechanic's workload for the shop week (Mon-Sat) containing `day` (YYYY-MM-DD).\n+\n+    A Sunday counts as the end of the Mon-Sat week just gone. Workload = hours of their jobs due\n+    that week that aren't 'ready' or 'collected' yet.\n+\n+    Returns {ok: True, week_start, week_end, mechanics: [{mechanic_id, name, weekly_capacity_hours,\n+    workload_hours, spare_hours, overloaded, job_count}]} sorted by spare_hours, most overloaded first\n+    (every mechanic is listed, even with no jobs), or {ok: False, error} if the date isn't valid.\n+    \"\"\"\n+    try:\n+        datetime.strptime(day, \"%Y-%m-%d\")\n+    except (TypeError, ValueError):\n+        return {\"ok\": False, \"error\": f\"'{day}' isn't a date. Use YYYY-MM-DD or 'today'\"}\n+    week_start, week_end = week_bounds(day)\n+    con = connect()\n+    rows = con.execute(\n+        \"\"\"SELECT m.id AS mechanic_id, m.name, m.weekly_capacity_hours,\n+                  coalesce(sum(j.estimate_hours), 0) AS workload_hours, count(j.id) AS job_count\n+           FROM mechanics m\n+           LEFT JOIN jobs j ON j.mechanic_id = m.id AND j.due_date BETWEEN ? AND ?\n+                           AND j.status NOT IN ('ready', 'collected')\n+           GROUP BY m.id ORDER BY m.id\"\"\",\n+        (week_start, week_end),\n+    ).fetchall()\n+    con.close()\n+    for r in rows:\n+        r[\"workload_hours\"] = round(r[\"workload_hours\"], 2)\n+        r[\"spare_hours\"] = round(r[\"weekly_capacity_hours\"] - r[\"workload_hours\"], 2)\n+        r[\"overloaded\"] = r[\"workload_hours\"] > r[\"weekly_capacity_hours\"]\n+    rows.sort(key=lambda r: r[\"spare_hours\"])\n+    return {\"ok\": True, \"week_start\": week_start, \"week_end\": week_end, \"mechanics\": rows}\ndiff --git a/tests/test_workload.py b/tests/test_workload.py\nnew file mode 100644\nindex 0000000..eb62311\n--- /dev/null\n+++ b/tests/test_workload.py\n@@ -0,0 +1,69 @@\n+# tests for GET /api/reports/workload/{day}. uses the throwaway database from conftest.py\n+# (\"today\" is Monday 2026-11-23, so this shop week is Mon 2026-11-23 to Sat 2026-11-28).\n+import db\n+\n+\n+def _set_jobs(client, jobs):\n+    \"\"\"Replace every job with our own: (mechanic name, hours, status, due_date).\"\"\"\n+    mech = {m[\"name\"]: m[\"id\"] for m in client.get(\"/api/mechanics\").json()}\n+    con = db.connect()\n+    con.execute(\"DELETE FROM job_parts\")\n+    con.execute(\"DELETE FROM invoices\")\n+    con.execute(\"DELETE FROM jobs\")\n+    for name, hours, status, due in jobs:\n+        con.execute(\n+            \"INSERT INTO jobs (customer_id, mechanic_id, work, estimate_hours, status, due_date, created) \"\n+            \"VALUES (1, ?, 'Service', ?, ?, ?, '2026-11-01 09:00:00')\",\n+            (mech[name], hours, status, due),\n+        )\n+    con.commit()\n+    con.close()\n+\n+\n+JOBS = [\n+    (\"Dev\", 8, \"booked\", \"2026-11-23\"),             # Monday: first day of the week, counts\n+    (\"Dev\", 15, \"in progress\", \"2026-11-28\"),       # Saturday: last day of the week, counts\n+    (\"Dev\", 5, \"booked\", \"2026-11-22\"),             # Sunday before: previous week\n+    (\"Dev\", 5, \"booked\", \"2026-11-29\"),             # Sunday after: not in this week\n+    (\"Ravi\", 2.5, \"waiting on parts\", \"2026-11-25\"),\n+    (\"Ravi\", 10, \"ready\", \"2026-11-25\"),            # ready: doesn't count\n+    (\"Ravi\", 10, \"collected\", \"2026-11-24\"),        # collected: doesn't count\n+    (\"Ravi\", 4, \"booked\", \"2026-11-21\"),            # Saturday of the previous week\n+]\n+\n+\n+def test_workload_week_and_exclusions(client):\n+    _set_jobs(client, JOBS)\n+    r = client.get(\"/api/reports/workload/2026-11-25\").json()\n+    assert r[\"ok\"] is True\n+    assert (r[\"week_start\"], r[\"week_end\"]) == (\"2026-11-23\", \"2026-11-28\")\n+    by_name = {m[\"name\"]: m for m in r[\"mechanics\"]}\n+    assert by_name[\"Dev\"] == {\"mechanic_id\": by_name[\"Dev\"][\"mechanic_id\"], \"name\": \"Dev\", \"weekly_capacity_hours\": 20,\n+                              \"workload_hours\": 23, \"spare_hours\": -3, \"overloaded\": True, \"job_count\": 2}\n+    assert by_name[\"Ravi\"][\"workload_hours\"] == 2.5 and by_name[\"Ravi\"][\"job_count\"] == 1\n+    assert by_name[\"Ravi\"][\"spare_hours\"] == 27.5 and by_name[\"Ravi\"][\"overloaded\"] is False\n+    # mechanics with nothing on are still listed\n+    assert by_name[\"Priya\"][\"workload_hours\"] == 0 and by_name[\"Priya\"][\"job_count\"] == 0\n+    assert by_name[\"Priya\"][\"spare_hours\"] == 30\n+    # most overloaded first\n+    assert [m[\"name\"] for m in r[\"mechanics\"]] == [\"Dev\", \"Ravi\", \"Priya\"]\n+\n+\n+def test_workload_week_boundaries(client):\n+    _set_jobs(client, JOBS)\n+    for day in [\"2026-11-23\", \"2026-11-28\", \"2026-11-29\", \"today\"]:  # Mon, Sat, the Sunday after, today (Mon)\n+        r = client.get(f\"/api/reports/workload/{day}\").json()\n+        assert (r[\"week_start\"], r[\"week_end\"]) == (\"2026-11-23\", \"2026-11-28\"), day\n+    # Sunday 2026-11-22 is the end of the week before\n+    r = client.get(\"/api/reports/workload/2026-11-22\").json()\n+    assert (r[\"week_start\"], r[\"week_end\"]) == (\"2026-11-16\", \"2026-11-21\")\n+    by_name = {m[\"name\"]: m for m in r[\"mechanics\"]}\n+    assert by_name[\"Ravi\"][\"workload_hours\"] == 4 and by_name[\"Dev\"][\"workload_hours\"] == 0\n+\n+\n+def test_workload_bad_date(client):\n+    for day in [\"2026-13-01\", \"next-week\"]:\n+        resp = client.get(f\"/api/reports/workload/{day}\")\n+        assert resp.status_code == 200\n+        body = resp.json()\n+        assert body[\"ok\"] is False and body[\"error\"]\n","tested":"22 passed, 1 warning in 1.55s","built":["GET /api/reports/workload/{day}"],"gitlog":[{"date":"2026-11-25","author":"Barnaby","subject":"Add GET /api/reports/workload/{day} (written by Barnaby, approved)"},{"date":"2026-11-19","author":"Theo Hartley","subject":"README: notes for whoever looks after it next. bye x"},{"date":"2019-02-23","author":"Theo Hartley","subject":"tests!! finally. seed script for the training laptop"},{"date":"2014-10-08","author":"Theo Hartley","subject":"invoices, mechanics, moved logic into services.py"},{"date":"2011-03-19","author":"Theo Hartley","subject":"parts + ordering from suppliers. reports page (coming soon)"},{"date":"2009-07-02","author":"Theo Hartley","subject":"jobs + customers pages, made it look proper"},{"date":"2009-03-14","author":"Theo Hartley","subject":"first version of the shop system!! (bye access database)"}]};
