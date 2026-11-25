/* Barnaby's display. Streams /api/events (SSE) and renders the conversation, the live trace,
   approval cards (with a diff viewer for Build) and the capability map. No framework, no build step.
   ?overlay=1 gives the compact HUD for the hotkey window.
   ?skin=<name> (index.html loads ui/skins/<name>.css) turns on the household view: what Barnaby did in plain words
   with the technical detail folded under each step, every yes and no kept in the conversation, and cards that lead
   with what it does, what it reads and changes, the checks and the undo. Without a skin nothing here changes.
   ?skin=app is the professional app look: the same household view, plus a few things only it uses (a lead line on
   each card, the disclosures above the decision, a state word on every ability, a welcome that teaches the controls,
   errors in plain words). Those are marked APP below.
   ?skin=app3 (round 3) builds on it, modelled on the Claude and Codex desktop apps: one column where the conversation,
   his work and the cards interleave in time order (each new element gets a CSS order stamp, so the work stays in #trace
   and the cards in #cards); his work batched into collapsed plain-words lines, one live line with his animated mark and a
   timer while he works; a quiet inspector of what he can do and has been given; a composer with Hold to talk as its
   primary control; the bell-and-bow-tie mark; light and dark. Marked APP3 below. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
  const params = new URLSearchParams(location.search);
  if (params.has('overlay')) document.body.classList.add('overlay');
  const SKIN = document.documentElement.dataset.skin || '';
  const HUMAN = !!SKIN;
  const APP3 = SKIN === 'app3';
  const APP = SKIN === 'app' || APP3;
  const COPY = { signpost: { trace: 'Where he went' }, ticket: { trace: 'Work done' } }[SKIN] || { trace: 'What he did' };
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const S = { systems: [], calls: new Map(), turn: 0, lastSaid: '', fresh: new Set(), keyed: new Set(), busy: false,
    now: Date.now(), titles: {}, rows: {}, grow: {}, skillNames: {}, built: '', pendingGrow: null, buildRow: null, group: null };
  const messages = $('#messages'), trace = $('#trace'), cards = $('#cards');
  const convo = messages.parentElement;
  const scroller = APP3 ? $('main') : convo;          // APP3: one scrolling column holds the words, the work and the cards
  let seq = 0;                                         // APP3: time order across the three lists
  const stamp = n => { if (APP3 && n) n.style.order = n.classList.contains('pending') ? '2147483000' : String(++seq * 10); return n; };
  S.wall = Date.now();

  // ── status ──
  const STATUS = HUMAN
    ? { thinking: 'Looking into it', speaking: 'Answering', listening: 'Listening', growing: 'Waiting for your say-so' }
    : { thinking: 'thinking', speaking: 'speaking', listening: 'listening', growing: 'growing a tool' };
  let thinkingRow = null;
  function setStatus(mode, text) {
    document.body.className = document.body.className.replace(/\bs-\w+/g, '').trim();
    if (mode) document.body.classList.add('s-' + mode);
    const t = text || STATUS[mode] || (HUMAN ? 'At your service' : 'at your service');
    $('#status-text').textContent = t;
    if (HUMAN && mode === 'thinking' && text) S.doing = text;
    if (HUMAN && thinkingRow && mode === 'thinking') thinkingRow.querySelector('.thinking').textContent = S.doing || 'One moment';
  }

  // ── conversation ──
  const two = n => String(n).padStart(2, '0');
  const clock = () => { const d = new Date(S.now); return `${two(d.getHours())}:${two(d.getMinutes())}`; };
  function settle() { if (HUMAN) scroller.scrollTop = scroller.scrollHeight; else messages.scrollTop = messages.scrollHeight; }
  function addMsg(kind, who, text) {
    if (thinkingRow) { thinkingRow.remove(); thinkingRow = null; }
    if (APP3) closeBatch();
    const li = el('li', 'msg ' + kind);
    if (HUMAN) {
      li.dataset.turn = S.turn;
      li.append(el('span', 'when', clock()));
      if (/^user\b/.test(kind)) li.append(el('span', 'no', String(S.turn)));
    }
    if (APP && /\berror\b/.test(kind)) {
      const [head, next] = plainError(who);
      li.append(el('div', 'who', head), el('div', 'text', next));
      if (text) li.append(fold('tech', 'Details', el('pre', 'technical-body', String(text))));
    } else li.append(el('div', 'who', who), el('div', 'text', text));
    if (APP) li.dataset.who = who;
    messages.append(li); stamp(li);
    settle();
    return li;
  }
  // APP: an error says what happened and what to do next; the raw message is folded under Details
  function plainError(who) {
    if (who === 'Voice') return ['Voice isn’t available just now', 'I can’t hear you at the moment. Type your question below instead, and I’ll answer as usual.'];
    if (who === 'Mock') return ['The recorded run couldn’t be loaded', 'The replay needs ui/fixtures/demo-run.json.'];
    return ['Something went wrong', 'I couldn’t finish that. Ask again in a moment, or see the details below.'];
  }
  function showThinking() {
    if (thinkingRow) return;
    thinkingRow = el('li', 'msg barnaby' + (HUMAN ? ' pending' : ''));
    if (APP3) {
      const line = el('div', 'act-line live'); line.append(markSVG(true), el('span', 'thinking', S.doing || 'Thinking'), el('span', 'act-time', ''));
      thinkingRow.append(el('div', 'who', 'Barnaby'), line);
    } else if (HUMAN) {
      thinkingRow.append(el('div', 'who', 'Barnaby'), el('div', 'thinking', S.doing || 'One moment'));
    } else {
      const t = el('div', 'thinking'); t.append(el('i'), el('i'), el('i'));
      thinkingRow.append(el('div', 'who', 'Barnaby'), t);
    }
    messages.append(thinkingRow); stamp(thinkingRow);
    settle();
  }
  // APP3: Barnaby's mark, drawn inline so its working animation can move its parts (the knob taps, the bell rings)
  function markSVG(work) {
    const s = document.createElementNS(SVGNS, 'svg');
    s.setAttribute('viewBox', '0 0 64 64'); s.setAttribute('class', 'bmark' + (work ? ' work' : '')); s.setAttribute('aria-hidden', 'true');
    s.innerHTML = '<g fill="currentColor">' + (work ? '<g class="ring" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round"><path d="M8.6 31.5 A27 27 0 0 1 16.5 22.9"/><path d="M55.4 31.5 A27 27 0 0 0 47.5 22.9"/></g>' : '')
      + '<circle class="knob" cx="32" cy="14.5" r="5.6"/><g class="body"><path d="M10.5 45.2 A21.5 21.5 0 0 1 53.5 45.2 Z" mask="url(#bb-tie)"/>'
      + '<rect x="5" y="48.6" width="54" height="6.6" rx="3.3"/></g></g>';
    return s;
  }
  // APP3: his work, batched. Consecutive steps share one collapsed line in plain words; while he works it is the live
  // line (his mark at work, what he is doing now, a timer). It opens to the steps; each step opens to its record.
  const BATCHES = {}; let batchN = 0;
  const fmtDur = sec => { sec = Math.max(1, Math.round(sec)); return sec < 60 ? `${sec}s` : `${Math.floor(sec / 60)}m ${sec % 60}s`; };
  function openBatch() {
    const id = String(++batchN);
    const li = el('li', 'act live'); li.dataset.b = id;
    const btn = el('button', 'act-line'); btn.type = 'button'; btn.setAttribute('aria-expanded', 'false');
    btn.append(markSVG(true), el('span', 'act-text'), el('span', 'act-time'), icon('chev', 'act-chev'));
    li.append(btn);
    const b = { id, li, steps: [], open: false, live: true, start: S.now };
    btn.onclick = () => openSteps(b, !b.open);
    BATCHES[id] = b; S.batch = b;
    trace.append(li); stamp(li);
    document.body.classList.add('working');
    return b;
  }
  function openSteps(b, open) {
    b.open = open; b.li.classList.toggle('open', open);
    b.li.querySelector('.act-line').setAttribute('aria-expanded', String(open));
    b.steps.forEach(x => x.classList.toggle('folded', !open));
  }
  function closeBatch() {
    const b = S.batch; S.batch = null; document.body.classList.remove('working');
    if (!b) return;
    b.live = false; b.end = S.now; b.li.classList.remove('live'); renderBatch(b);
  }
  function summarise(says) {                       // "Looked at repair job 4471", "… 4475" -> "Looked at 2 repair jobs"
    const items = [];
    for (const t of says) {
      const m = /^(.*\S) (\d{3,})$/.exec(t), last = items[items.length - 1];
      if (m && last && last.key === m[1]) { last.n++; continue; }
      items.push({ key: m ? m[1] : t, n: 1, text: t });
    }
    const words = items.map(it => it.n > 1 ? it.key.replace(/^(\w+(?: at| for)?) (.+)$/, (x, v, o) => `${v} ${it.n} ${o}s`) : it.text);
    let out = [], verb = '';
    for (const w of words) {                        // the opening verb is said once: "Looked at A, B and C"
      const v = (/^(Looked at|Looked for|Read|Ran|Wrote|Checked)\s/.exec(w) || [])[1] || '';
      out.push(v && v === verb ? w.slice(v.length + 1) : out.length ? lowerFirst(w) : w);
      verb = v;
    }
    if (out.length > 3) out = out.slice(0, 2).concat([`${out.length - 2} more`]);
    return out.length > 1 ? `${out.slice(0, -1).join(', ')} and ${out[out.length - 1]}` : out[0] || '';
  }
  function renderBatch(b) {
    b.steps.sort((x, y) => x.style.order - y.style.order);
    const say = x => (x.querySelector('.say') || {}).textContent || '';
    const consent = x => x.classList.contains('ask') || /^(Asked you|Asked to make|You said|Key given|Made it one step|Allowed by)/.test(say(x));
    const work = b.steps.filter(x => !consent(x));
    b.li.classList.toggle('ask-only', !work.length);            // the card and the kept yes or no already say it
    const says = (work.length ? work : b.steps).map(say).filter(Boolean);
    const now = [...b.steps].reverse().find(x => x.classList.contains('doing'));
    const failedN = b.steps.filter(x => x.classList.contains('err')).length;
    b.li.querySelector('.act-text').textContent = b.live && now ? now.querySelector('.say').textContent
      : summarise(says) + (failedN ? `, ${failedN} didn’t work` : '');
    const sec = ((b.live ? S.now : b.end) - b.start) / 1000 + (b.live ? (Date.now() - S.wall) / 1000 : 0);
    b.li.querySelector('.act-time').textContent = fmtDur(sec);
  }
  if (APP3) setInterval(() => {                    // the live line's timer runs between events
    if (S.batch && S.batch.live && S.batch.li.isConnected) renderBatch(S.batch);
    if (thinkingRow && thinkingRow.isConnected) { const t = thinkingRow.querySelector('.act-time'); if (t) t.textContent = fmtDur((S.now - (S.turnAt || S.now)) / 1000 + (Date.now() - S.wall) / 1000); }
  }, 1000);

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

  // ── the household view: steps in plain words, technical detail folded under each ──
  const SVGNS = 'http://www.w3.org/2000/svg';
  function icon(name, cls) {
    const s = document.createElementNS(SVGNS, 'svg');
    s.setAttribute('class', 'ico' + (cls ? ' ' + cls : '')); s.setAttribute('aria-hidden', 'true');
    const u = document.createElementNS(SVGNS, 'use'); u.setAttribute('href', '#i-' + name); s.append(u);
    return s;
  }
  const MARK = { doing: 'doing', done: 'done', ask: 'key', no: 'no', err: 'warn', new: 'room' };
  function setStep(li, state, say, sub, ico) {
    li.className = 'tr step ' + state + (li.classList.contains('past') ? ' past' : '') + (li.classList.contains('folded') ? ' folded' : '');
    if (ico) li.dataset.ico = ico;
    const mark = li.querySelector('.mark'); mark.textContent = '';
    mark.append(icon(state === 'done' || state === 'doing' || state === 'no' || state === 'err' ? MARK[state] : (li.dataset.ico || MARK[state] || 'done')));
    const body = li.querySelector('.body');
    let s = body.querySelector('.say'); if (!s) { s = el('div', 'say'); body.prepend(s); }
    if (say != null) s.textContent = say;
    let u = body.querySelector('.sub');
    if (sub) { if (!u) { u = el('div', 'sub'); s.after(u); } u.textContent = sub; } else if (sub === '' && u) u.remove();
    if (APP3 && BATCHES[li.dataset.b]) renderBatch(BATCHES[li.dataset.b]);
  }
  function addTech(li, text) {
    if (!li || !text) return;
    let pre = li.querySelector('.technical-body');
    if (!pre) { pre = el('pre', 'technical-body'); li.querySelector('.body').append(fold('tech', 'Details', pre)); }
    pre.textContent += (pre.textContent ? '\n' : '') + text;
  }
  function stepRow(state, say, sub, tech, ico) {
    const li = el('li', 'tr step');
    li.append(el('span', 'mark'), el('div', 'body'));
    setStep(li, state, say, sub, ico);
    addTech(li, tech);
    const b = APP3 ? (S.batch && S.batch.li.isConnected ? S.batch : openBatch()) : null;
    trace.append(li); stamp(li);
    if (b) { li.dataset.b = b.id; b.steps.push(li); li.classList.toggle('folded', !b.open); renderBatch(b); }
    trace.scrollTop = trace.scrollHeight;
    return li;
  }

  // the status says what he is doing now: "Looked at repair jobs…" (the step, once done) -> "Looking at repair jobs…"
  const NOW = { Looked: 'Looking', Gave: 'Giving', Added: 'Adding', Booked: 'Booking', Changed: 'Changing', Marked: 'Marking',
    Raised: 'Raising', Cancelled: 'Cancelling', Ordered: 'Ordering', Sent: 'Sending', Set: 'Setting', Made: 'Making',
    Moved: 'Moving', Updated: 'Updating', Created: 'Creating', Removed: 'Removing', Deleted: 'Deleting', Recorded: 'Recording',
    Assigned: 'Assigning', Used: 'Using', Checked: 'Checking' };
  const doingNow = line => String(line || '').replace(/^\w+/, w => NOW[w] || w);
  const lowerFirst = s => (s ? s[0].toLowerCase() + s.slice(1) : s);
  const upperFirst = s => (s ? s[0].toUpperCase() + s.slice(1) : s);
  const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function plainDay(v) {
    const m = /^(\d{4})-(\d\d)-(\d\d)$/.exec(v); if (!m) return String(v);
    const d = new Date(+m[1], m[2] - 1, +m[3]);
    return `${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
  }
  function plainValue(k, v) {
    if (/(^|_)(day|date)$/.test(k)) return plainDay(v);
    if (/_id$/.test(k)) return `${k.slice(0, -3).replace(/_/g, ' ')} ${v}`;
    if (typeof v === 'string') return v.length > 48 ? `“${v.slice(0, 46)}…”` : v;
    if (typeof v === 'number') return `${k.replace(/_/g, ' ')} ${v}`;
    return '';
  }
  // the first clause of an ability's own description: "Repair jobs due on a given day. day is…" -> "Repair jobs due on a given day"
  const clause = desc => String(desc || '').replace(/\s*\([^)]*\)/g, '').split(/\.\s|\.$|:\s|,\s|;\s|\s(?:including|e\.g\.)\s/)[0].trim();
  const sentence = desc => String(desc || '').replace(/\s*\([^)]*\)/g, '').replace(/,?\s*e\.g\..*$/, '').split(/\.\s|\.$/)[0].trim();
  const VERB = { find: 'Looked for', search: 'Looked for', give: 'Gave', add: 'Added', book: 'Booked', change: 'Changed',
    mark: 'Marked', raise: 'Raised', cancel: 'Cancelled', order: 'Ordered', send: 'Sent', set: 'Set', make: 'Made', move: 'Moved',
    update: 'Updated', create: 'Created', remove: 'Removed', delete: 'Deleted', record: 'Recorded', assign: 'Assigned' };
  function plainCall(d, ep) {
    const input = d.input || {}, used = new Set();
    const skill = /-k\d+$/.test(d.system || '');
    let what = skill ? (S.skillNames[d.tool] || upperFirst(d.tool.replace(/_/g, ' '))) : (clause(ep && ep.description) || upperFirst(d.tool.replace(/_/g, ' ')));
    what = what.replace(/\b(?:a|the) given (\w+)/, (m, w) => {        // "…due on a given day" + day -> "…due on Tue 24 Nov"
      const k = Object.keys(input).find(x => !used.has(x) && (x === w || x.startsWith(w) || (w === 'text' && typeof input[x] === 'string')));
      if (!k) return m;
      used.add(k); return plainValue(k, input[k]);
    });
    const one = /^One (.+)$/.exec(what);                                 // "One repair job" + job_id -> "repair job 4471"
    if (one) { const k = Object.keys(input).find(x => /_id$/.test(x)); if (k) { what = `${one[1]} ${input[k]}`; used.add(k); } }
    let line;
    if (skill) line = `Used “${what}”`;
    else {
      const first = (what.split(' ')[0] || '').toLowerCase();
      line = VERB[first] && !/^\w+ or /.test(what) ? VERB[first] + what.slice(first.length)
        : ep && !ep.read_only ? upperFirst(what) : 'Looked at ' + lowerFirst(what);
    }
    const sub = Object.keys(input).filter(k => !used.has(k)).map(k => plainValue(k, input[k])).filter(Boolean).join(', ');
    return { line, sub };
  }
  function previewText(preview) {
    try { const j = JSON.parse(preview); return j.map ? j.map(x => x.text || '').join('\n') : preview; } catch (_) {
      // a preview cut short is no longer JSON: still unwrap the text it carries, so the record reads as the system wrote it
      const m = /^\[\{"type":\s*"text",\s*"text":\s*"([\s\S]*)$/.exec(preview || '');
      return m ? m[1].replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\\\/g, '\\') + ' …' : preview;
    }
  }
  function failed(preview) {           // a system's own "ok": false, when the preview is whole enough to read
    try { const j = JSON.parse(preview); const f = JSON.parse(j[0].text); return f && f.ok === false ? (f.error || f.detail || 'It didn’t work') : ''; } catch (_) { return ''; }
  }
  function buildLabel(tool, target) {
    if (/\bpytest\b(?!\.)|npm (run )?test|go test|cargo test|unittest/.test(target)) return 'Ran the checks';   // not pytest.ini
    if (/README|NOTES|CONTRIBUTING|\.md\b/i.test(target)) return 'Read the notes left with the code';
    if (/^(Edit|Write|MultiEdit|NotebookEdit)$/.test(tool)) return 'Wrote the change';
    return 'Read the code';
  }
  const ING = { 'Ran the checks': 'Running the checks', 'Read the notes left with the code': 'Reading the notes left with the code',
    'Wrote the change': 'Writing the change', 'Read the code': 'Reading the code' };   // said while he is still at it
  const worktree = s => String(s || '').replace(/[A-Za-z]:[\\/][^"' ]*?worktree-[^\\/"' ]+[\\/]/g, '');

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
  function diffSummary(diff) {
    const lines = diff.split('\n');
    const files = lines.filter(l => l.startsWith('diff --git')).length;
    const added = lines.filter(l => l.startsWith('+') && !l.startsWith('+++')).length;
    const removed = lines.filter(l => l.startsWith('-') && !l.startsWith('---')).length;
    return `The change, for whoever wants to read it: ${files} file${files === 1 ? '' : 's'}, ${added} line${added === 1 ? '' : 's'} added, ${removed ? removed + ' removed' : 'nothing removed'}.`;
  }
  // a folded section: technical detail and the change itself are there for whoever wants them, closed by default
  function fold(cls, label, body) {
    const d = el('details', 'fold ' + cls);
    d.append(el('summary', '', label), body);
    return d;
  }
  // what a card says, in the order a person needs it (the build summary's four lines are fixed: barnaby/build.py explain)
  function cardFacts(a) {
    const lines = String(a.detail || '').split('\n').map(s => s.trim()).filter(Boolean);
    const method = (/^(GET|POST|PUT|PATCH|DELETE)\b/.exec(a.technical || '') || [])[1];
    const eachTime = ['Each time', 'He still asks you before he does it.'];
    if (a.tier === 'build' && lines.length >= 4) {
      const fx = /^It (?:only )?reads (.+?),? and changes (.+?)\.?$/.exec(lines[1]);
      const rows = [['What it does', lines[0]]];
      if (fx) rows.push(['What it reads', upperFirst(fx[1]) + '.'], ['What it changes', upperFirst(fx[2]) + '.']);
      else rows.push(['What it touches', lines[1]]);
      rows.push(['Checks', lines[2]], ['If you change your mind', upperFirst(lines[3].replace(/^If you change your mind,\s*/i, ''))]);
      return { head: a.title, rows };
    }
    if (a.kind === 'unlock') return { head: a.title, rows: [['Why', lines.join(' ')]].concat(method && method !== 'GET' ? [eachTime] : []) };
    if (a.kind === 'compose') return { head: a.title, rows: [['What it does', lines.join(' ')], eachTime] };
    // a change: what will happen, then to what ("10 × Brake pads (Shimano resin, pair) with Madison"), then what it
    // costs; his question itself is in the conversation just above, and in the receipt
    if (a.tier === 'write') {
      const t = String(a.title || ''), i = t.indexOf(': ');
      return { head: i > 0 ? t.slice(0, i) : t, rows: (i > 0 ? [['', t.slice(i + 2)]] : []).concat((a.facts || []).filter(f => f && f[1])) };
    }
    return { head: a.title, rows: lines.length ? [['', lines.join(' ')]] : [] };
  }
  const KIND_ICON = { unlock: 'key', compose: 'passage', build: 'room', call: 'pen' };
  function bringIntoView(node) {
    const c = scroller.getBoundingClientRect(), r = node.getBoundingClientRect();
    let delta = r.bottom - c.bottom + 24;                                  // show its foot (the buttons)…
    if (r.top - delta < c.top + 24) delta = r.top - c.top - 24;            // …unless that would hide its head
    if (delta > 0) scroller.scrollBy({ top: delta, behavior: reduceMotion ? 'auto' : 'smooth' });
  }
  // Cards lead with the household's words: the plain title and summary (detail). The endpoint, the arguments,
  // the test line (technical) and the diff sit folded underneath.
  function showCard(a) {
    if (document.getElementById('card-' + a.id)) return;
    S.titles[a.id] = APP && a.tier === 'write' && a.detail ? plainAsk(a.detail) : a.title;
    if (HUMAN) return showCardHuman(a);
    const labels = { write: 'Confirm a change', grow: 'Barnaby would like a new ability', build: 'Barnaby made something new' };
    const card = el('div', 'card ' + a.tier); card.id = 'card-' + a.id;
    card.append(el('div', 'k', labels[a.tier] || 'Approval'), el('div', 'title', a.title));
    if (a.detail) card.append(el('div', 'detail', a.detail));
    if (a.diff) card.append(fold('change', 'See the change', renderDiff(a.diff)));
    if (a.technical) card.append(fold('technical', 'Technical detail', el('div', 'technical-body', a.technical)));
    const actions = el('div', 'actions');
    const yes = el('button', 'primary', a.tier === 'build' ? 'Yes, add it' : a.tier === 'grow' ? 'Yes, go ahead' : 'Approve');
    const no = el('button', '', a.tier === 'write' ? 'Decline' : 'Not now');
    yes.onclick = () => decide(a.id, true); no.onclick = () => decide(a.id, false);
    actions.append(yes, no, el('span', 'hint', a.voice_ok ? 'or say "yes"' : a.tier === 'build' ? 'a click, not by voice' : ''));
    card.append(actions);
    cards.append(card);
    card.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }
  function showCardHuman(a) {
    if (APP) return showCardApp(a);
    const f = cardFacts(a);
    const card = el('section', `card ${a.tier} k-${a.kind || 'call'}`); card.id = 'card-' + a.id;
    card.setAttribute('aria-label', f.head);
    const head = el('div', 'head'); head.append(icon(KIND_ICON[a.kind] || 'pen', 'kind'), el('h3', 'title', f.head));
    card.append(head);
    if (f.rows.length) {
      const dl = el('dl', 'facts');
      for (const [k, v] of f.rows) { const r = el('div', 'fact' + (k === 'Checks' ? ' checks' : '')); if (k) r.append(el('dt', '', k)); r.append(el('dd', '', v)); dl.append(r); }
      card.append(dl);
    }
    const actions = el('div', 'actions');
    const yes = el('button', 'primary', a.tier === 'build' ? 'Yes, add it' : a.tier === 'grow' ? 'Yes, go ahead' : 'Approve');
    const no = el('button', 'secondary', a.tier === 'write' ? 'Decline' : 'Not now');
    yes.onclick = () => decide(a.id, true); no.onclick = () => decide(a.id, false);
    actions.append(yes, no, el('span', 'hint', a.voice_ok ? 'Or just say “yes”.' : a.tier === 'build' ? 'A change like this needs a click, not a spoken yes.' : 'One click.'));
    card.append(actions);
    if (a.diff) {
      const body = el('div', 'change-body'); body.append(el('p', 'diff-sum', diffSummary(a.diff)), renderDiff(a.diff));
      const d = fold('change', 'See the change', body);
      d.addEventListener('toggle', () => {
        d.querySelector('summary').textContent = d.open ? 'Hide the change' : 'See the change';
        if (d.open) bringIntoView(d.nextElementSibling || d);      // the change and the fold under it, both in view
      });
      card.append(d);
    }
    if (a.technical) card.append(fold('technical', 'Technical detail', el('div', 'technical-body', a.technical)));
    cards.append(card);
    bringIntoView(card);
  }
  // APP: the card reads top to bottom the way a decision is made: what and why, the facts, the change and the
  // technical record for whoever wants them, and last the yes and the no, with how they may be given.
  function diffMeta(diff) {
    const lines = diff.split('\n');
    const files = lines.filter(l => l.startsWith('diff --git')).length;
    const added = lines.filter(l => l.startsWith('+') && !l.startsWith('+++')).length;
    const removed = lines.filter(l => l.startsWith('-') && !l.startsWith('---')).length;
    return `${files} file${files === 1 ? '' : 's'}, ${added} line${added === 1 ? '' : 's'} added, ${removed ? removed + ' removed' : 'nothing removed'}`;
  }
  function showCardApp(a) {
    const f = cardFacts(a);
    let rows = f.rows, lede = '';
    if (rows.length && /^(What it does|Why|)$/.test(rows[0][0])) { lede = rows[0][1]; rows = rows.slice(1); }
    const card = el('section', `card ${a.tier} k-${a.kind || 'call'}`); card.id = 'card-' + a.id;
    card.setAttribute('aria-label', f.head);
    const head = el('div', 'head');
    if (APP3) {
      const hd = el('div', 'hd');
      hd.append(el('h3', 'title', f.head), el('span', 'kind-line', { unlock: 'A new key', compose: 'A shortcut', build: 'A new piece for the system' }[a.kind] || 'A change to your records'));
      head.append(icon(KIND_ICON[a.kind] || 'pen', 'kind'), hd);
    } else head.append(icon(KIND_ICON[a.kind] || 'pen', 'kind'), el('h3', 'title', f.head));
    card.append(head);
    if (lede) card.append(el('p', 'lede', lede));
    if (rows.length) {
      const dl = el('dl', 'facts');
      for (const [k, v] of rows) {
        const r = el('div', 'fact' + (k === 'Checks' ? ' checks' : ''));
        const dd = el('dd'); if (k === 'Checks') dd.append(icon('done', 'ok')); dd.append(document.createTextNode(v));
        r.append(el('dt', '', k), dd); dl.append(r);
      }
      card.append(dl);
    }
    if (a.diff) {
      const body = el('div', 'change-body'); body.append(renderDiff(a.diff));
      const d = fold('change', '', body), sum = d.querySelector('summary'), lab = el('span', 'lab', 'See the change');
      sum.append(lab, APP3 ? diffCounts(a.diff) : el('span', 'meta', diffMeta(a.diff)));
      d.addEventListener('toggle', () => {
        lab.textContent = d.open ? 'Hide the change' : 'See the change';
        if (d.open) bringIntoView(card);
      });
      card.append(d);
    }
    if (a.technical) card.append(fold('technical', 'Technical detail', el('div', 'technical-body', a.technical)));
    const actions = el('div', 'actions');
    const yes = el('button', 'primary', a.tier === 'build' ? 'Yes, add it' : a.tier === 'grow' ? 'Yes, go ahead' : 'Approve');
    const no = el('button', 'secondary', a.tier === 'write' ? 'Decline' : 'Not now');
    yes.type = no.type = 'button';
    yes.onclick = () => decide(a.id, true); no.onclick = () => decide(a.id, false);
    const hint = el('span', 'hint', a.voice_ok ? 'Or just say “yes”.' : a.tier === 'build' ? 'A change like this needs a click, not a spoken yes.'
      : a.kind === 'unlock' ? 'A new key needs a click, not a spoken yes.' : 'A new step like this needs a click, not a spoken yes.');
    actions.append(hint, no, yes);
    card.append(actions);
    if (APP3) closeBatch();
    cards.append(card); stamp(card);
    bringIntoView(card);
  }
  function diffCounts(diff) {                      // APP3: "3 files  +114 −0", the way a change is summarised
    const lines = diff.split('\n');
    const files = lines.filter(l => l.startsWith('diff --git')).length;
    const added = lines.filter(l => l.startsWith('+') && !l.startsWith('+++')).length;
    const removed = lines.filter(l => l.startsWith('-') && !l.startsWith('---')).length;
    const m = el('span', 'meta'); m.append(el('span', '', `${files} file${files === 1 ? '' : 's'}`), el('span', 'n-add', `+${added}`), el('span', 'n-del', `−${removed}`));
    m.setAttribute('aria-label', `${files} files, ${added} lines added, ${removed ? removed + ' removed' : 'nothing removed'}`);
    return m;
  }
  function plainAsk(t) {
    return upperFirst(String(t).trim().replace(/,?\s*shall I\??$/i, '').replace(/^I(?:'|’)ll\s+/, '').replace(/\.$/, ''));
  }
  async function decide(id, approved) {
    document.querySelectorAll(`#card-${id} button`).forEach(b => (b.disabled = true));
    await fetch(`/api/approvals/${id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ approved, via: 'click' }) });
  }

  // ── systems ──
  let stateAsked = 0;
  async function refreshState() {
    const n = ++stateAsked;
    const r = await fetch('/api/state'); const st = await r.json();
    if (n !== stateAsked) return;
    S.systems = st.systems; S.busy = st.busy;
    renderChips(); renderMap(); if (APP3) renderInspector();
    st.approvals.forEach(showCard);
  }
  function renderChips() {
    const box = $('#systems-chips'); box.textContent = '';
    if (APP) document.body.classList.toggle('no-system', !S.systems.length);
    if (HUMAN && !S.systems.length) {
      const chip = el('div', 'sys-chip none'); chip.append(el('b', '', 'No system yet'), el('span', '', 'Point him at one to begin'));
      box.append(chip);
    }
    for (const s of S.systems) {
      const chip = el('div', 'sys-chip');
      const n = s.endpoints.length, x = s.exposed.length;
      if (HUMAN) {
        chip.append(el('b', '', upperFirst(s.title || s.name)), el('span', '', APP ? `He can use ${x} of its ${n} things` : `he can use ${x} of ${n} things`));
        box.append(chip); continue;
      }
      chip.innerHTML = `<b>${esc(s.name)}</b><span>${x} of ${n} tools</span>`;
      const m = el('span', 'meter'); const i = el('i'); i.style.width = (n ? (100 * x / n) : 0) + '%'; m.append(i); chip.append(m);
      box.append(chip);
    }
  }
  function renderMap() {
    if (HUMAN) return renderMapHuman();
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
      for (const k of s.skills || []) {               // composed skills (Synapse Custom mode)
        const c = el('span', 'ep skill exposed' + (S.fresh.has('skill:' + k.tool) ? ' fresh' : ''), '✦ ' + k.tool);
        c.title = k.description; eps.append(c);
      }
      sec.append(eps); body.append(sec);
    }
  }
  // APP: a technical name may break after a slash or an underscore (a <wbr>, so a copied name stays whole)
  function techName(t) {
    const c = el('code', 'tech');
    String(t).split(/(?<=[/_])/).forEach((part, i) => { if (i) c.append(document.createElement('wbr')); c.append(part); });
    return c;
  }
  // the plan of the house, in plain words: every thing the system can do, by area, with its state as a mark and a word
  function renderMapHuman() {
    const body = $('#map-body'); body.textContent = '';
    if (!S.systems.length) {
      body.append(el('p', 'sys empty', APP ? 'No system connected yet.' : 'No system yet. Point Barnaby at one below: he reads its code and lists everything it can do, and to start he only uses the things that look something up.'));
      return;
    }
    const legend = el('ul', 'legend');
    for (const [ico, cls, txt] of [[APP ? 'can' : 'use', 'use', 'He can use it'], ['key', 'key', 'He asks you first'], ['shut', 'shut', 'Kept shut, whoever asks'], ['room', 'new', APP ? 'Added today' : 'New today']]) {
      const li = el('li', cls); li.append(icon(ico), el('span', '', txt)); legend.append(li);
    }
    body.append(legend);
    if (APP) {                       // for whoever looks after the code: the technical name under each ability, on request
      const t = el('button', 'tech-toggle', 'Show technical names'); t.type = 'button';
      const show = on => { S.showTech = on; $('#map').classList.toggle('show-tech', on); t.setAttribute('aria-pressed', String(on)); t.textContent = on ? 'Hide technical names' : 'Show technical names'; };
      t.onclick = () => show(!S.showTech); show(!!S.showTech);
      body.append(t);
    }
    for (const s of S.systems) {
      const sec = el('section', 'sys');
      sec.append(el('h3', '', upperFirst(s.title || s.name)), el('p', 'sub', `He can use ${s.exposed.length} of the ${s.endpoints.length} things it can do.`));
      const areas = new Map();
      for (const e of s.endpoints) {
        const path = e.path || String(e.key || '').split(' ').pop();
        const seg = path.split('/').filter(x => x && x !== 'api' && !x.startsWith('{'))[0] || 'other';
        const area = upperFirst(seg.replace(/[-_]/g, ' '));
        if (!areas.has(area)) areas.set(area, []);
        areas.get(area).push(e);
      }
      for (const [area, list] of areas) {
        sec.append(el('h4', '', area));
        const ul = el('ul', 'abilities');
        for (const e of list) {
          const state = e.denied ? 'shut' : e.exposed ? 'use' : 'key';
          const fresh = S.fresh.has(e.key), keyed = APP && S.keyed.has(e.key);   // APP: a key given today is not a new piece
          const li = el('li', `ab ${state}${fresh ? ' new' : ''}`);
          li.append(icon(APP && (keyed || (state === 'use' && !fresh)) ? 'can' : fresh ? 'room' : state), el('span', 'what', upperFirst(sentence(e.description) || e.tool.replace(/_/g, ' '))));
          if (APP) li.append(el('span', fresh ? 'today' : 'state', keyed ? 'Key given today' : fresh ? 'Added today' : { use: 'Can use', key: 'Asks first', shut: 'Kept shut' }[state]));
          else if (fresh) li.append(el('span', 'today', 'today'));
          li.append(APP ? techName(e.key) : el('code', 'tech', e.key));
          li.title = e.description || '';
          ul.append(li);
        }
        sec.append(ul);
      }
      if ((s.skills || []).length) {
        sec.append(el('h4', '', 'Made from several steps'));
        const ul = el('ul', 'abilities');
        for (const k of s.skills) {
          const fresh = S.fresh.has('skill:' + k.tool);
          const li = el('li', `ab use${fresh ? ' new' : ''}`);
          li.append(icon('passage'), el('span', 'what', S.skillNames[k.tool] || k.name || upperFirst(k.tool.replace(/_/g, ' '))));
          if (APP) li.append(el('span', fresh ? 'today' : 'state', fresh ? 'Added today' : 'Can use'));
          else if (fresh) li.append(el('span', 'today', 'today'));
          li.append(APP ? techName(k.tool) : el('code', 'tech', k.tool));
          ul.append(li);
        }
        sec.append(ul);
      }
      body.append(sec);
    }
  }

  // ── events ──
  function onEvent(ev) {
    const d = ev.data;
    if (ev.ts) S.now = ev.ts * 1000;
    S.wall = Date.now();
    if (HUMAN) return household(ev);
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
        const skill = /-k\d+$/.test(d.system || '');     // a composed skill's own server, e.g. shop-k1
        const tier = !d.system || d.system === 'barnaby' ? (d.tool === 'build' ? 'build' : 'grow') : (ep && ep.read_only ? 'read' : 'write');
        const label = d.system === 'barnaby' || !d.system ? `<b>Barnaby</b> · ${esc(d.tool)}`
          : skill ? `<b>${esc(d.system.replace(/-k\d+$/, ''))}</b> · ✦ ${esc(d.tool)}` : `<b>${esc(d.system)}</b> · ${esc(d.tool)}`;
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
      case 'growth.compose.proposed':
        traceRow('grow', '<b>Compose</b> · a new skill', d.description, 'proposed'); setStatus('growing', 'composing'); break;
      case 'growth.compose.done':
        S.fresh.add('skill:' + d.tool);
        traceRow('grow ok', `<b>Composed</b> · ${esc(d.tool)}`, `Synapse Custom mode, ${d.seconds}s`, 'live'); refreshState(); break;
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

  // The same events, told the way a person would: where he went, what he asked, what you said.
  // synapse.*, system.reloaded/started/restarted and turn.result are the developer's record and stay out of it.
  function household(ev) {
    const d = ev.data;
    switch (ev.type) {
      case 'turn.start': {
        S.turn = d.turn; S.lastSaid = ''; S.group = null; S.doing = ''; S.turnAt = S.now;
        messages.querySelectorAll('.msg:not(.past)').forEach(n => n.classList.add('past'));
        trace.querySelectorAll('li:not(.past)').forEach(n => n.classList.add('past'));
        const own = !d.text.startsWith('[Barnaby system]');
        if (own) addMsg('user', 'You', d.text);
        const sep = el('li', 'turn-sep');
        if (APP) sep.append(el('span', 'q', own ? d.text : 'Getting started'), el('span', 'when', clock()));
        else sep.append(el('span', 'no', `No. ${d.turn} · ${clock()}`), el('span', 'q', own ? d.text : 'Getting started'));
        trace.append(sep); stamp(sep);
        setStatus('thinking'); showThinking(); break;
      }
      case 'say':
        if (d.text !== S.lastSaid) addMsg('barnaby', 'Barnaby', d.text);
        S.lastSaid = d.text;
        setStatus('speaking'); break;
      case 'tool.call': {
        if (!d.system || d.system === 'barnaby') {         // unlock, compose and build appear as their own steps
          if (d.tool === 'capabilities') S.calls.set(d.id, stepRow('doing', 'Checked what the system can do', '', `barnaby · capabilities ${JSON.stringify(d.input || {})}`, 'plan'));
          else if (d.tool === 'connect') S.calls.set(d.id, stepRow('doing', 'Connecting a system', '', `barnaby · connect ${JSON.stringify(d.input || {})}`, 'plan'));
          showThinking(); break;
        }
        const ep = endpointFor(d.system, d.tool);
        const p = plainCall(d, ep);
        const row = stepRow('doing', APP ? doingNow(p.line) : p.line, p.sub,
          `${d.system} · ${d.tool}${ep ? ' · ' + ep.key : ''}\n${JSON.stringify(d.input || {})}`, ep && !ep.read_only ? 'pen' : 'look');
        row.dataset.sub = p.sub; row.dataset.line = p.line; S.lastCall = row;
        S.calls.set(d.id, row); setStatus('thinking', doingNow(p.line)); showThinking(); break;
      }
      case 'tool.result': {
        const row = S.calls.get(d.id); if (!row) break;
        const why = d.ok ? failed(d.preview) : (previewText(d.preview) || 'It didn’t work');
        setStep(row, why ? 'err' : 'done', APP ? row.dataset.line : null, why ? why.slice(0, 120) : row.dataset.sub || '');
        addTech(row, '→ ' + previewText(d.preview).slice(0, 1600)); break;
      }
      case 'approval.requested': {
        if (thinkingRow) { thinkingRow.remove(); thinkingRow = null; }
        if (APP3) S.titles[d.id] = d.tier === 'write' && d.detail ? plainAsk(d.detail) : d.title;
        if (!APP3) showCard(d);                       // APP3: the ask joins his work first, then the card closes it
        if ((d.kind === 'unlock' || d.kind === 'compose') && S.pendingGrow) { S.rows[d.id] = S.pendingGrow; S.pendingGrow = null; }
        else {
          S.rows[d.id] = stepRow('ask', `Asked you: ${S.titles[d.id] || d.title}`, '', null, KIND_ICON[d.kind] || 'pen');
          const call = S.lastCall;                     // APP: the order or the change waits under the yes it needs
          if (APP && call && call.classList.contains('doing') && call.nextElementSibling === S.rows[d.id]) {
            trace.insertBefore(S.rows[d.id], call);
            if (APP3) { const o = call.style.order; call.style.order = S.rows[d.id].style.order; S.rows[d.id].style.order = o; }
            if (d.detail) { call.dataset.sub = S.titles[d.id]; setStep(call, 'doing', null, S.titles[d.id]); }
          }
        }
        if (APP3) showCard(d);
        setStatus('growing'); break;
      }
      case 'approval.resolved': case 'approval.auto': {
        const c = document.getElementById('card-' + d.id); if (c) c.remove();
        const title = S.titles[d.id] || d.title || '';
        const yes = ev.type === 'approval.auto' || !!d.approved;
        const said = ev.type === 'approval.auto' ? 'Allowed by your settings' : yes ? 'You said yes' : 'You said not now';
        if (title) {
          const li = addMsg('decision ' + (yes ? 'yes' : 'no'), 'You', '');
          li.querySelector('.text').append(el('b', 'said', said), el('span', 'sep', ': '), title);
          const b = APP3 && S.rows[d.id] && BATCHES[S.rows[d.id].dataset.b];   // APP3: the yes sits before the work it allowed
          if (b && !b.li.classList.contains('ask-only')) li.style.order = String(Number(b.li.style.order) - 5);
        }
        const row = S.rows[d.id];
        if (row) setStep(row, yes ? 'done' : 'no', `${said}: ${title}`, '');
        break;
      }
      case 'growth.unlock.proposed':
        S.grow[d.endpoint] = d.ability;
        S.pendingGrow = stepRow('ask', `Asked you for a key: ${d.ability}`, '', `unlock ${d.endpoint}\n${d.reason || ''}`, 'key');
        S.grow['row:' + d.endpoint] = S.pendingGrow;
        setStatus('growing'); break;
      case 'growth.unlock.done': {
        S.fresh.add(d.endpoint); S.keyed.add(d.endpoint);
        const row = S.grow['row:' + d.endpoint], ability = S.grow[d.endpoint] || d.tool;
        if (row) { setStep(row, 'done', `Key given: ${ability}`, '', 'key'); addTech(row, `unlocked ${d.endpoint} as ${d.tool} (${d.seconds}s)`); }
        else stepRow('done', `Key given: ${ability}`, '', `unlocked ${d.endpoint}`, 'key');
        refreshState(); break;
      }
      case 'growth.compose.proposed':
        S.grow.compose = d.name || 'one step';
        S.pendingGrow = S.grow.composeRow = stepRow('ask', `Asked to make it one step: ${S.grow.compose}`, '', d.description, 'passage');
        setStatus('growing', 'Waiting for your say-so'); break;
      case 'growth.compose.done': {
        S.fresh.add('skill:' + d.tool);
        S.skillNames[d.tool] = d.name || S.grow.compose || upperFirst(d.tool.replace(/_/g, ' '));
        const row = S.grow.composeRow;
        if (row) { setStep(row, 'done', `Made it one step: ${S.skillNames[d.tool]}`, '', 'passage'); addTech(row, `composed ${d.tool} (${d.seconds}s)`); }
        refreshState(); break;
      }
      case 'growth.build.started':
        S.buildRow = stepRow('done', 'Started on the missing piece', '', `${d.method} ${d.path}\n${d.spec}`, 'room');
        S.checksRow = null;
        setStatus('thinking', 'Writing the missing piece'); break;
      case 'growth.build.step': {
        const label = buildLabel(d.tool, String(d.target || ''));
        const tech = `${d.tool}: ${worktree(d.target)}`;
        if (S.group && S.group.label === label) {
          S.group.n++; addTech(S.group.row, tech);
          if (label === 'Wrote the change') setStep(S.group.row, 'doing', null, `${S.group.n} files`);
        } else {
          if (S.group) setStep(S.group.row, 'done', S.group.label);
          S.group = { label, n: 1, row: stepRow('doing', ING[label] || label, label === 'Wrote the change' ? '1 file' : '', tech, label === 'Wrote the change' ? 'pen' : 'look') };
          if (label === 'Ran the checks') S.checksRow = S.group.row;
        }
        setStatus('thinking', ING[label] || label); break;
      }
      case 'growth.build.tested': {          // may arrive after the write-up, so the checks row is kept by name
        const m = /(\d+) passed/.exec(d.result || '');
        const row = S.checksRow || stepRow('doing', 'Ran the checks', '', null, 'done');
        if (S.group && S.group.row !== row) setStep(S.group.row, 'done', S.group.label);
        S.checksRow = null;
        setStep(row, d.passed ? 'done' : 'err', 'Ran the checks', d.passed ? (m ? `All ${m[1]} pass` : 'They pass') : 'Some did not pass');
        addTech(row, d.result); S.group = null; break;
      }
      case 'growth.build.written':
        if (S.group) { setStep(S.group.row, 'done', S.group.label); S.group = null; }
        stepRow(d.ok ? 'done' : 'err', d.ok ? 'Finished writing it' : 'Could not write the missing piece', d.seconds ? `in ${Math.round(d.seconds)} seconds` : '', null, 'room');
        break;
      case 'growth.build.explained': S.built = d.name || ''; break;
      case 'growth.build.merged': stepRow('done', 'Added it to the system', '', `merged ${d.branch}`, 'room'); break;
      case 'growth.build.done':
        (d.endpoints || []).forEach(k => S.fresh.add(k));
        stepRow('new', `Ready to use: ${S.built || 'the new piece'}`, '', `${(d.tools || []).join(', ')}\n${(d.endpoints || []).join(', ')}`, 'room');
        refreshState(); break;
      case 'system.connecting':
        S.connectRow = stepRow('doing', `Reading ${d.title}`, '', d.repo, 'plan');
        setStatus('thinking', `Reading ${d.title}`); break;
      case 'system.connected': {
        addMsg('note', 'Connected', `${upperFirst(d.title)}: it can do ${d.discovered} things. To start, Barnaby may use the ${d.exposed.length} that only look something up.`);
        if (S.connectRow) setStep(S.connectRow, 'done', `Read ${d.title}`, `${d.discovered} things it can do`);
        else stepRow('done', `Read ${d.title}`, `${d.discovered} things it can do`, null, 'plan');
        refreshState(); break;
      }
      case 'turn.end': setStatus(null); if (thinkingRow) { thinkingRow.remove(); thinkingRow = null; } if (APP3) closeBatch(); break;
      case 'log': if (d.level === 'error') addMsg('error note', 'Error', d.text); break;
    }
    if (APP3 && /^growth\.|^approval\.|^system\.connected/.test(ev.type)) renderInspector();
  }

  // APP3: the inspector, Claude-style: what he is connected to, how much he can use, the keys you gave him, what he made,
  // and how to talk to him. Quiet rows with right-aligned values; where state lives, not where the story is told.
  function renderInspector() {
    const box = $('#inspector'); if (!box) return;
    box.textContent = '';
    const section = (title, rows, empty) => {
      const sec = el('section', 'isec'); sec.append(el('h2', '', title));
      const ul = el('ul', 'irows');
      if (!rows.length && empty) { const li = el('li', 'irow empty'); li.append(el('span', 'ilabel', empty)); ul.append(li); }
      for (const [ico, label, value, cls] of rows) {
        const li = el('li', 'irow' + (cls ? ' ' + cls : '')); li.append(icon(ico), el('span', 'ilabel', label));
        if (value != null) li.append(typeof value === 'string' ? el('span', 'ivalue', value) : value);
        ul.append(li);
      }
      sec.append(ul); box.append(sec);
    };
    const sys = S.systems[0];
    if (!sys) section('System', [], 'No system connected yet');
    else {
      const x = sys.exposed.length, n = sys.endpoints.length;
      const meter = el('span', 'ivalue meter'); const bar = el('i'); bar.style.width = (n ? 100 * x / n : 0) + '%';
      meter.append(`${x} of ${n}`, el('b', 'bar')); meter.lastChild.append(bar);
      section('System', [['plug', upperFirst(sys.title || sys.name), null], ['can', 'He can use', meter]]);
    }
    const keys = [...S.keyed].map(k => ['key', upperFirst(S.grow[k] || k), 'today']);
    section('Keys you gave him', keys, 'None yet. He only looks things up.');
    const made = [];
    for (const k of S.fresh) if (!S.keyed.has(k) && !k.startsWith('skill:')) made.push(['room', upperFirst(S.built || 'A new piece'), 'today']);
    for (const t of Object.keys(S.skillNames)) made.push(['passage', S.skillNames[t], 'today']);
    section('Made with your say-so', made, 'Nothing yet.');
    section('Talking to him', [['mic', 'Hold to talk', 'Space'], ['done', 'A spoken yes', 'for orders and changes'], ['key', 'Keys and new pieces', 'a click']]);
    const more = el('button', 'imore', 'What he can do'); more.type = 'button'; more.append(icon('chev'));
    more.onclick = () => toggleMap(true); box.append(more);
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

  // the household view's words and marks on the fixed parts of the page
  if (HUMAN) {
    const brandUse = $('.brand use'); if (brandUse) brandUse.setAttribute('href', '#i-bell');
    $('#toggle-map').textContent = 'What he can do';
    $('#map .panel-head h2').textContent = 'What he can do';
    const tr = trace.closest('section'); tr.setAttribute('aria-label', COPY.trace); $('h2', tr).textContent = COPY.trace;
    const talk = $('#talk'); talk.prepend(icon('mic', 'mic'));
    talk.after(el('span', 'talk-hint', 'or hold the space bar'));
    if (APP3) {
      const brand = $('.brand'); brand.textContent = ''; brand.append(markSVG(false), el('span', '', 'Barnaby'));
      const insp = $('#inspector'); if (insp) insp.hidden = false;
      const tools = el('div', 'tbar-tools');
      const themeBtn = el('button', 'icon-btn theme'); themeBtn.type = 'button';
      const setTheme = t => { document.documentElement.dataset.theme = t; themeBtn.setAttribute('aria-label', t === 'dark' ? 'Light mode' : 'Dark mode'); themeBtn.title = themeBtn.getAttribute('aria-label'); themeBtn.textContent = ''; themeBtn.append(icon(t === 'dark' ? 'sun' : 'moon')); };
      setTheme(document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light');
      themeBtn.onclick = () => { const t = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'; setTheme(t); try { localStorage.setItem('barnaby-theme', t); } catch (_) {} };
      const panelBtn = el('button', 'icon-btn panel'); panelBtn.type = 'button'; panelBtn.setAttribute('aria-label', 'Show or hide the side panel'); panelBtn.title = 'Side panel';
      panelBtn.append(icon('panel')); panelBtn.onclick = () => document.body.classList.toggle('insp-closed');
      tools.append(themeBtn, panelBtn);
      $('.top').append(tools);
      $('#systems-chips').addEventListener('click', () => toggleMap(map.hidden));
      const plus = el('button', 'plus'); plus.type = 'button'; plus.setAttribute('aria-label', 'Connect a system'); plus.title = 'Connect a system';
      plus.append(icon('plus')); plus.onclick = () => { toggleMap(true); const f = $('#connect-form input'); if (f) f.focus(); };
      $('#talk').before(plus);
      $('#ask-input').placeholder = 'Ask Barnaby anything, or hold the space bar and talk';
      $('#ask-form button').setAttribute('aria-label', 'Ask'); $('#ask-form button').prepend(icon('send'));
      $('.talk-hint').textContent = 'Space';
    }
    if (APP) {
      $('#toggle-map').prepend(icon('plan'));
      const h = $('#connect-form h3');
      h.textContent = 'Connect a system';
      h.after(el('p', 'help', 'Barnaby reads its code and lists everything it can do. To begin, he only uses the things that look something up.'));
    }
    setStatus(null);
  }

  // empty state: Barnaby introduces himself (removed by the first real message)
  const hello = addMsg('barnaby intro', 'Barnaby', 'Good day. Point me at a system and ask me anything about it; if it can’t do what you need yet, I’ll see what can be done.');
  if (APP) {                       // a welcome that teaches the two controls, and the way in when there is no system yet
    const how = el('ul', 'how');
    for (const [ico, txt] of [['mic', 'Hold the button below, or the space bar, and ask out loud.'], ['keys', 'Or type your question and press Enter.']]) {
      const li = el('li'); li.append(icon(ico), el('span', '', txt)); how.append(li);
    }
    const go = el('button', 'connect-first', 'Connect a system'); go.type = 'button';
    go.prepend(icon('plug'));
    go.onclick = () => { toggleMap(true); const f = $('#connect-form input'); if (f) f.focus(); };
    if (APP3) {
      hello.querySelector('.text').textContent = 'Good day. What can I look into?';
      hello.prepend(markSVG(false));
      hello.append(el('p', 'sub', 'Point me at a system and ask me anything about it. If it can’t do what you need yet, I’ll see what can be done.'));
    }
    hello.append(how, go);
  }
  const observer = new MutationObserver(() => { if (messages.children.length > 1) { hello.remove(); observer.disconnect(); } });
  observer.observe(messages, { childList: true });

  // syncState: mock replay hands over its state synchronously so plain words can name each ability (skins only)
  const syncState = st => { if (HUMAN && st && st.systems) S.systems = st.systems; };
  window.Barnaby = { onEvent, setStatus, addMsg, refreshState, showCard, syncState };   // used by the voice layer and mock mode
  refreshState().catch(() => {});
  if (params.has('mock')) {
    const s = document.createElement('script'); s.src = '/ui/mock.js'; document.body.append(s);
  } else if (!params.has('static')) {
    connectEvents();
  }
})();
