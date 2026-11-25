/* Mock mode (?mock=1): replays a REAL recorded run (ui/fixtures/demo-run.json, exported from
   .demo/barnaby/events.jsonl by scripts/dev/export_mock_fixture.py) with timing compressed.
   Approval cards pause the replay until you click (or press Y / N). No backend needed.

   Keys:  Space play/pause · 1-9 jump to the start of turn N · Y approve / N decline the open card · R restart
   ?speed=2 replays faster; ?auto=1 auto-approves cards after 1.2 s (for the film capture);
   ?turn=N&paused=1 holds the replay at the start of turn N (Space resumes). */
(() => {
  'use strict';
  const B = window.Barnaby;
  const params = new URLSearchParams(location.search);
  const speed = parseFloat(params.get('speed') || '1');
  const autoApprove = params.has('auto');
  const MAX_GAP = 1600, MIN_GAP = 140;

  let run = null, i = 0, playing = true, timer = null, waitingFor = null;
  const state = { busy: false, systems: [], approvals: [] };

  // fake API so app.js works unchanged
  const realFetch = window.fetch.bind(window);
  window.fetch = async (url, opts) => {
    const u = String(url);
    if (u.startsWith('/api/state')) return new Response(JSON.stringify(state), { headers: { 'Content-Type': 'application/json' } });
    if (u.startsWith('/api/approvals/')) {
      const body = JSON.parse((opts && opts.body) || '{}');
      resolveApproval(u.split('/').pop(), body.approved);
      return new Response('{"ok":true}');
    }
    if (u.startsWith('/api/ask')) return new Response('{"ok":true}');
    return realFetch(url, opts);
  };

  let builtName = '';
  function apply(ev) {
    const d = ev.data;
    // keep the fake state in step with growth so chips and the capability map update
    const sys = state.systems.find(s => s.name === d.system);
    if (ev.type === 'system.connected' && sys) { sys.exposed = d.exposed.slice(); sys.endpoints.forEach(e => (e.exposed = sys.exposed.includes(e.key))); }
    if (ev.type === 'growth.unlock.done' && sys) { sys.exposed.push(d.endpoint); const e = sys.endpoints.find(x => x.key === d.endpoint); if (e) e.exposed = true; }
    if (ev.type === 'growth.build.explained') builtName = d.name || '';
    if (ev.type === 'growth.build.done' && sys) {
      for (const k of d.endpoints || []) {
        sys.exposed.push(k);
        if (!sys.endpoints.find(x => x.key === k)) sys.endpoints.push({ key: k, path: k.split(' ').pop(), tool: (d.tools[0] || '').split('__').pop(), method: 'GET', read_only: true, exposed: true,
          description: builtName ? builtName[0].toUpperCase() + builtName.slice(1) + '. Written by Barnaby.' : 'Written by Barnaby' });
      }
    }
    if (ev.type === 'growth.compose.done' && sys) {
      sys.skills = (sys.skills || []).concat([{ server: d.server, tool: d.tool, name: d.name, description: 'Composed by Synapse' }]);
    }
    if (B.syncState) B.syncState(state);           // the skins name each ability from the state, so hand it over now
    B.onEvent(ev);
  }

  function resolveApproval(id, approved) {
    if (!waitingFor || waitingFor !== id) return;
    waitingFor = null;
    B.onEvent({ type: 'approval.resolved', data: { id, approved } });
    if (playing) schedule(250);
  }

  function step() {
    if (!run || i >= run.events.length) { playing = false; return; }
    const ev = run.events[i++];
    apply(ev);
    if (ev.type === 'approval.requested') {
      waitingFor = ev.data.id;
      if (autoApprove) setTimeout(() => resolveApproval(ev.data.id, true), 1200);
      return;                                  // wait for the click
    }
    if (ev.type === 'approval.resolved') return schedule(MIN_GAP);
    const next = run.events[i];
    const gap = next ? Math.min(MAX_GAP, Math.max(MIN_GAP, (next.ts - ev.ts) * 1000)) : 0;
    schedule(gap);
  }
  function schedule(ms) { clearTimeout(timer); if (playing) timer = setTimeout(step, ms / speed); }

  function jumpToTurn(n) {
    // replay instantly up to the start of turn n (clearing the screen first)
    document.getElementById('messages').textContent = '';
    document.getElementById('trace').textContent = '';
    document.getElementById('cards').textContent = '';
    state.systems = JSON.parse(JSON.stringify(run.state_before.systems));
    i = 0; waitingFor = null;
    builtName = '';
    while (i < run.events.length) {
      const ev = run.events[i];
      if (ev.type === 'turn.start' && ev.data.turn >= n) break;
      apply(ev);                                 // cards come and go in the same breath, so the skins keep each yes and no
      i++;
    }
    B.refreshState();
    playing = !params.has('paused'); schedule(300);   // ?paused=1 holds the replay at the start of turn n (stills)
  }

  document.addEventListener('keydown', e => {
    if (e.target && e.target.tagName === 'INPUT') return;
    if (e.key === ' ') { e.preventDefault(); playing = !playing; if (playing && !waitingFor) schedule(0); }
    else if (/^[1-9]$/.test(e.key)) jumpToTurn(+e.key);
    else if (e.key === 'r' || e.key === 'R') jumpToTurn(0);
    else if ((e.key === 'y' || e.key === 'Y') && waitingFor) resolveApproval(waitingFor, true);
    else if ((e.key === 'n' || e.key === 'N') && waitingFor) resolveApproval(waitingFor, false);
  });

  realFetch('/ui/fixtures/demo-run.json').then(r => r.json()).then(data => {
    run = data;
    state.systems = JSON.parse(JSON.stringify(run.state_before.systems));
    B.refreshState();
    if (params.has('turn')) return jumpToTurn(parseInt(params.get('turn'), 10));
    schedule(params.has('paused') ? 1e9 : 600);
  }).catch(err => B.addMsg('error note', 'Mock', 'No recorded run found (ui/fixtures/demo-run.json): ' + err));
})();
