/* Barnaby's display. Streams /api/events (SSE) and renders the conversation, the live trace,
   approval cards (with a diff viewer for Build) and the capability map. No framework, no build step.
   ?overlay=1 gives the compact HUD for the hotkey window. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
  const params = new URLSearchParams(location.search);
  if (params.has('overlay')) document.body.classList.add('overlay');

  const S = { systems: [], calls: new Map(), turn: 0, lastSaid: '', fresh: new Set(), busy: false };
  const messages = $('#messages'), trace = $('#trace'), cards = $('#cards');

  // ── status ──
  function setStatus(mode, text) {
    document.body.className = document.body.className.replace(/\bs-\w+/g, '').trim();
    if (mode) document.body.classList.add('s-' + mode);
    $('#status-text').textContent = text || { thinking: 'thinking', speaking: 'speaking', listening: 'listening', growing: 'growing a tool' }[mode] || 'at your service';
  }

  // ── conversation ──
  let thinkingRow = null;
  function addMsg(kind, who, text) {
    if (thinkingRow) { thinkingRow.remove(); thinkingRow = null; }
    const li = el('li', 'msg ' + kind);
    li.append(el('div', 'who', who), el('div', 'text', text));
    messages.append(li);
    messages.scrollTop = messages.scrollHeight;
    return li;
  }
  function showThinking() {
    if (thinkingRow) return;
    thinkingRow = el('li', 'msg barnaby');
    const t = el('div', 'thinking'); t.append(el('i'), el('i'), el('i'));
    thinkingRow.append(el('div', 'who', 'Barnaby'), t);
    messages.append(thinkingRow);
    messages.scrollTop = messages.scrollHeight;
  }

  // ── trace ──
  const sysColour = name => name || 'barnaby';
  function traceRow(kind, nameHtml, args, tag) {
    const li = el('li', 'tr ' + kind);
    const name = el('div', 'name'); name.innerHTML = nameHtml;
    const right = el('span', 'tag', tag || '');
    const body = el('div'); body.append(name); if (args) body.append(el('div', 'args', args));
    li.append(el('span', 'dot'), body, right, el('div', 'res'));
    li.addEventListener('click', () => li.classList.toggle('open'));
    trace.append(li);
    trace.scrollTop = trace.scrollHeight;
    return li;
  }
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function endpointFor(system, tool) {
    const s = S.systems.find(x => x.name === system);
    return s && s.endpoints.find(e => e.tool === tool);
  }

  // ── approval cards ──
  function renderDiff(diff) {
    const box = el('div', 'diff');
    for (const line of diff.split('\n')) {
      if (line.startsWith('diff --git')) { box.append(el('div', 'file', line.replace(/^diff --git a\/(\S+).*$/, '$1'))); continue; }
      if (/^(index |--- |\+\+\+ |new file mode)/.test(line)) continue;
      const cls = line.startsWith('@@') ? 'hunk' : line.startsWith('+') ? 'add' : line.startsWith('-') ? 'del' : '';
      box.append(el('div', 'ln ' + cls, line || ' '));
    }
    return box;
  }
  function showCard(a) {
    if (document.getElementById('card-' + a.id)) return;
    const labels = { write: 'Confirm a change', grow: 'Barnaby would like to grow', build: 'Barnaby wrote new code' };
    const card = el('div', 'card ' + a.tier); card.id = 'card-' + a.id;
    card.append(el('div', 'k', labels[a.tier] || 'Approval'), el('div', 'title', a.title));
    if (a.detail) card.append(el('div', 'detail', a.detail));
    if (a.diff) card.append(renderDiff(a.diff));
    const actions = el('div', 'actions');
    const yes = el('button', 'primary', a.tier === 'build' ? 'Approve and merge' : a.tier === 'grow' ? 'Unlock' : 'Approve');
    const no = el('button', '', a.tier === 'grow' ? 'Not now' : 'Decline');
    yes.onclick = () => decide(a.id, true); no.onclick = () => decide(a.id, false);
    actions.append(yes, no, el('span', 'hint', a.voice_ok ? 'or say "yes"' : a.tier === 'build' ? 'read the diff first' : ''));
    card.append(actions);
    cards.append(card);
    card.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }
  async function decide(id, approved) {
    document.querySelectorAll(`#card-${id} button`).forEach(b => (b.disabled = true));
    await fetch(`/api/approvals/${id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ approved, via: 'click' }) });
  }

  // ── systems ──
  async function refreshState() {
    const r = await fetch('/api/state'); const st = await r.json();
    S.systems = st.systems; S.busy = st.busy;
    renderChips(); renderMap();
    st.approvals.forEach(showCard);
  }
  function renderChips() {
    const box = $('#systems-chips'); box.textContent = '';
    for (const s of S.systems) {
      const chip = el('div', 'sys-chip');
      const n = s.endpoints.length, x = s.exposed.length;
      chip.innerHTML = `<b>${esc(s.name)}</b><span>${x} of ${n} tools</span>`;
      const m = el('span', 'meter'); const i = el('i'); i.style.width = (n ? (100 * x / n) : 0) + '%'; m.append(i); chip.append(m);
      box.append(chip);
    }
  }
  function renderMap() {
    const body = $('#map-body'); body.textContent = '';
    if (!S.systems.length) { body.append(el('p', 'sys muted', 'No systems yet. Point Barnaby at a repo below.')); return; }
    const legend = el('div', 'legend'); legend.innerHTML = '<span>■ exposed</span><span>□ discovered, unlockable</span><span>✦ grown this session</span>';
    body.append(legend);
    for (const s of S.systems) {
      const sec = el('div', 'sys');
      sec.append(el('h3', '', s.title), el('div', 'sub', `${s.name} · ${s.repo} · ${s.running ? 'running' : 'not running'}`));
      const eps = el('div', 'eps');
      for (const e of s.endpoints) {
        const c = el('span', 'ep' + (e.exposed ? ' exposed' : '') + (e.denied ? ' denied' : '') + (S.fresh.has(e.key) ? ' fresh' : ''), e.key);
        c.title = e.description; eps.append(c);
      }
      sec.append(eps); body.append(sec);
    }
  }

  // ── events ──
  function onEvent(ev) {
    const d = ev.data;
    switch (ev.type) {
      case 'turn.start':
        S.turn = d.turn; S.lastSaid = '';
        if (!d.text.startsWith('[Barnaby system]')) addMsg('user', 'You', d.text);
        trace.append(el('li', 'turn-sep', `Turn ${d.turn}`));
        setStatus('thinking'); showThinking(); break;
      case 'say':
        if (d.final) { if (d.text !== S.lastSaid) addMsg('barnaby', 'Barnaby', d.text); S.lastSaid = d.text; }
        else if (d.text !== S.lastSaid) { addMsg('barnaby', 'Barnaby', d.text); S.lastSaid = d.text; }
        setStatus('speaking'); break;
      case 'tool.call': {
        const ep = endpointFor(d.system, d.tool);
        const tier = !d.system || d.system === 'barnaby' ? (d.tool === 'build' ? 'build' : 'grow') : (ep && ep.read_only ? 'read' : 'write');
        const label = d.system === 'barnaby' || !d.system ? `<b>Barnaby</b> · ${esc(d.tool)}` : `<b>${esc(d.system)}</b> · ${esc(d.tool)}`;
        const args = Object.keys(d.input || {}).length ? JSON.stringify(d.input) : (ep ? ep.key : '');
        const row = traceRow(tier + ' pending', label, args, tier);
        S.calls.set(d.id, row); showThinking(); break;
      }
      case 'tool.result': {
        const row = S.calls.get(d.id); if (!row) break;
        row.classList.remove('pending'); row.classList.add(d.ok ? 'ok' : 'err');
        let text = d.preview; try { const j = JSON.parse(d.preview); text = j.map ? j.map(x => x.text || '').join('\n') : d.preview; } catch (_) { /* keep raw */ }
        row.querySelector('.res').textContent = text; break;
      }
      case 'approval.requested': showCard(d); break;
      case 'approval.resolved': case 'approval.auto': {
        const c = document.getElementById('card-' + d.id); if (c) c.remove(); break;
      }
      case 'growth.unlock.proposed':
        traceRow('grow', `<b>Unlock</b> · ${esc(d.endpoint)}`, d.reason, 'proposed'); setStatus('growing'); break;
      case 'growth.unlock.done':
        S.fresh.add(d.endpoint); traceRow('grow ok', `<b>Unlocked</b> · ${esc(d.tool)}`, `Synapse rebuilt the server in ${d.seconds}s`, 'live'); refreshState(); break;
      case 'growth.build.started':
        traceRow('build', `<b>Build</b> · ${esc(d.method)} ${esc(d.path)}`, d.spec, 'writing'); setStatus('growing', 'writing code'); break;
      case 'growth.build.step':
        traceRow('build ok', `<b>builder</b> · ${esc(d.tool)}`, String(d.target || '').replace(/[A-Za-z]:[\\/][^"' ]*?worktree-[^\\/"' ]+[\\/]/g, ''), ''); break;
      case 'growth.build.tested': traceRow('build ' + (d.passed ? 'ok' : 'err'), '<b>tests</b>', d.result, d.passed ? 'pass' : 'fail'); break;
      case 'growth.build.merged': traceRow('build ok', '<b>merged</b>', d.branch, 'landed'); break;
      case 'growth.build.done':
        (d.endpoints || []).forEach(k => S.fresh.add(k));
        traceRow('build ok', `<b>New tool</b> · ${esc((d.tools || []).join(', '))}`, (d.endpoints || []).join(', '), 'live'); refreshState(); break;
      case 'synapse.built': traceRow('synapse ok', `<b>Synapse</b> · built ${esc(d.system)}`, `${d.exposed} tools from ${d.discovered} endpoints, ${d.seconds}s`, ''); break;
      case 'system.connecting': traceRow('synapse pending', `<b>Connecting</b> · ${esc(d.title)}`, d.repo, 'scanning'); break;
      case 'system.connected':
        addMsg('note', 'Synapse', `${d.title}: ${d.discovered} endpoints discovered, ${d.exposed.length} read-only tools exposed to start.`);
        refreshState(); break;
      case 'system.reloaded': traceRow('synapse ok', `<b>Reconnected</b> · ${esc(d.system)}`, 'new tools are live', ''); break;
      case 'turn.result': $('#trace-meta').textContent = `last turn ${(d.ms / 1000).toFixed(1)}s · ${d.turns} model turns`; break;
      case 'turn.end': setStatus(null); if (thinkingRow) { thinkingRow.remove(); thinkingRow = null; } break;
      case 'log': if (d.level === 'error') addMsg('error note', 'Error', d.text); break;
    }
  }

  function connectEvents() {
    const es = new EventSource('/api/events');
    es.onmessage = m => { try { onEvent(JSON.parse(m.data)); } catch (e) { console.error(e); } };
    es.onerror = () => { es.close(); setTimeout(connectEvents, 1500); };
  }

  // ── input ──
  $('#ask-form').addEventListener('submit', async e => {
    e.preventDefault();
    const input = $('#ask-input'); const text = input.value.trim(); if (!text) return;
    input.value = '';
    const r = await fetch('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) });
    if (r.status === 409) addMsg('note', 'Barnaby', 'One moment, I am still on the last request.');
  });
  $('#connect-form').addEventListener('submit', async e => {
    e.preventDefault();
    const f = new FormData(e.target);
    await fetch('/api/connect', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: f.get('name'), title: f.get('name'), repo: f.get('repo'), base_url: f.get('base_url') }) });
  });
  const map = $('#map');
  const toggleMap = open => { map.hidden = !open; $('#toggle-map').setAttribute('aria-expanded', String(open)); };
  $('#toggle-map').onclick = () => toggleMap(map.hidden);
  $('#close-map').onclick = () => toggleMap(false);

  // empty state: Barnaby introduces himself (removed by the first real message)
  const hello = addMsg('barnaby intro', 'Barnaby', 'Good day. Point me at a system and ask me anything about it; if it can’t do what you need yet, I’ll see what can be done.');
  const observer = new MutationObserver(() => { if (messages.children.length > 1) { hello.remove(); observer.disconnect(); } });
  observer.observe(messages, { childList: true });

  window.Barnaby = { onEvent, setStatus, addMsg, refreshState, showCard };   // used by the voice layer and mock mode
  refreshState().catch(() => {});
  if (params.has('mock')) {
    const s = document.createElement('script'); s.src = '/ui/mock.js'; document.body.append(s);
  } else if (!params.has('static')) {
    connectEvents();
  }
})();
