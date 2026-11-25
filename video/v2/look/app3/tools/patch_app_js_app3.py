"""ui/app.js for ?skin=app3 (round 3): Claude-shaped. One column holds the conversation, the work and the cards in time
order; the work is batched into collapsed lines (a live line with his animated mark and a timer while he works); a quiet
inspector; a Claude-style composer; the mark; light and dark. Everything else is the app look's (APP) behaviour."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else 'ui/app.js'
s = open(p, encoding='utf-8').read()


def rep(old, new, n=1):
    global s
    assert s.count(old) == n, (old[:90], s.count(old))
    s = s.replace(old, new)


rep(r"""   errors in plain words). Those are marked APP below. */""",
r"""   errors in plain words). Those are marked APP below.
   ?skin=app3 (round 3) builds on it, modelled on the Claude and Codex desktop apps: one column where the conversation,
   his work and the cards interleave in time order (each new element gets a CSS order stamp, so the work stays in #trace
   and the cards in #cards); his work batched into collapsed plain-words lines, one live line with his animated mark and a
   timer while he works; a quiet inspector of what he can do and has been given; a composer with Hold to talk as its
   primary control; the bell-and-bow-tie mark; light and dark. Marked APP3 below. */""")

rep(r"""  const APP = SKIN === 'app';""",
r"""  const APP3 = SKIN === 'app3';
  const APP = SKIN === 'app' || APP3;""")

rep(r"""  const messages = $('#messages'), trace = $('#trace'), cards = $('#cards');
  const convo = messages.parentElement;""",
r"""  const messages = $('#messages'), trace = $('#trace'), cards = $('#cards');
  const convo = messages.parentElement;
  const scroller = APP3 ? $('main') : convo;          // APP3: one scrolling column holds the words, the work and the cards
  let seq = 0;                                         // APP3: time order across the three lists
  const stamp = n => { if (APP3 && n) n.style.order = n.classList.contains('pending') ? '2147483000' : String(++seq); return n; };
  S.wall = Date.now();""")

# scrolling
rep(r"""  function settle() { if (HUMAN) convo.scrollTop = convo.scrollHeight; else messages.scrollTop = messages.scrollHeight; }""",
r"""  function settle() { if (HUMAN) scroller.scrollTop = scroller.scrollHeight; else messages.scrollTop = messages.scrollHeight; }""")
rep(r"""    const c = convo.getBoundingClientRect(), r = node.getBoundingClientRect();
    let delta = r.bottom - c.bottom + 24;                                  // show its foot (the buttons)…
    if (r.top - delta < c.top + 24) delta = r.top - c.top - 24;            // …unless that would hide its head
    if (delta > 0) convo.scrollBy({ top: delta, behavior: reduceMotion ? 'auto' : 'smooth' });""",
r"""    const c = scroller.getBoundingClientRect(), r = node.getBoundingClientRect();
    let delta = r.bottom - c.bottom + 24;                                  // show its foot (the buttons)…
    if (r.top - delta < c.top + 24) delta = r.top - c.top - 24;            // …unless that would hide its head
    if (delta > 0) scroller.scrollBy({ top: delta, behavior: reduceMotion ? 'auto' : 'smooth' });""")

# messages: stamp, close the batch, the pending line as a live line
rep(r"""  function addMsg(kind, who, text) {
    if (thinkingRow) { thinkingRow.remove(); thinkingRow = null; }""",
r"""  function addMsg(kind, who, text) {
    if (thinkingRow) { thinkingRow.remove(); thinkingRow = null; }
    if (APP3) closeBatch();""")
rep(r"""    if (APP) li.dataset.who = who;
    messages.append(li);
    settle();
    return li;""",
r"""    if (APP) li.dataset.who = who;
    messages.append(li); stamp(li);
    settle();
    return li;""")
rep(r"""    if (HUMAN) {
      thinkingRow.append(el('div', 'who', 'Barnaby'), el('div', 'thinking', S.doing || 'One moment'));
    } else {""",
r"""    if (APP3) {
      const line = el('div', 'act-line live'); line.append(markSVG(true), el('span', 'thinking', S.doing || 'Thinking'), el('span', 'act-time', ''));
      thinkingRow.append(el('div', 'who', 'Barnaby'), line);
    } else if (HUMAN) {
      thinkingRow.append(el('div', 'who', 'Barnaby'), el('div', 'thinking', S.doing || 'One moment'));
    } else {""")
rep(r"""    messages.append(thinkingRow);
    settle();
  }""",
r"""    messages.append(thinkingRow); stamp(thinkingRow);
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
    const says = b.steps.map(x => (x.querySelector('.say') || {}).textContent || '').filter(Boolean);
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
  }, 1000);""")

rep(r"""  function setStep(li, state, say, sub, ico) {
    li.className = 'tr step ' + state + (li.classList.contains('past') ? ' past' : '');""",
r"""  function setStep(li, state, say, sub, ico) {
    li.className = 'tr step ' + state + (li.classList.contains('past') ? ' past' : '') + (li.classList.contains('folded') ? ' folded' : '');""")
rep(r"""    if (sub) { if (!u) { u = el('div', 'sub'); s.after(u); } u.textContent = sub; } else if (sub === '' && u) u.remove();
  }""",
r"""    if (sub) { if (!u) { u = el('div', 'sub'); s.after(u); } u.textContent = sub; } else if (sub === '' && u) u.remove();
    if (APP3 && BATCHES[li.dataset.b]) renderBatch(BATCHES[li.dataset.b]);
  }""")
rep(r"""    setStep(li, state, say, sub, ico);
    addTech(li, tech);
    trace.append(li);
    trace.scrollTop = trace.scrollHeight;
    return li;""",
r"""    setStep(li, state, say, sub, ico);
    addTech(li, tech);
    const b = APP3 ? (S.batch && S.batch.li.isConnected ? S.batch : openBatch()) : null;
    trace.append(li); stamp(li);
    if (b) { li.dataset.b = b.id; b.steps.push(li); li.classList.toggle('folded', !b.open); renderBatch(b); }
    trace.scrollTop = trace.scrollHeight;
    return li;""")

# cards: a kind line under the title, the change summarised by its counts, stamped into time order
rep(r"""    const head = el('div', 'head'); head.append(icon(KIND_ICON[a.kind] || 'pen', 'kind'), el('h3', 'title', f.head));
    card.append(head);
    if (lede) card.append(el('p', 'lede', lede));""",
r"""    const head = el('div', 'head');
    if (APP3) {
      const hd = el('div', 'hd');
      hd.append(el('h3', 'title', f.head), el('span', 'kind-line', { unlock: 'A new key', compose: 'One step instead of several', build: 'A new piece for the system' }[a.kind] || 'A change to your records'));
      head.append(icon(KIND_ICON[a.kind] || 'pen', 'kind'), hd);
    } else head.append(icon(KIND_ICON[a.kind] || 'pen', 'kind'), el('h3', 'title', f.head));
    card.append(head);
    if (lede) card.append(el('p', 'lede', lede));""")
rep(r"""      sum.append(lab, el('span', 'meta', diffMeta(a.diff)));""",
r"""      sum.append(lab, APP3 ? diffCounts(a.diff) : el('span', 'meta', diffMeta(a.diff)));""")
rep(r"""    actions.append(hint, no, yes);
    card.append(actions);
    cards.append(card);
    bringIntoView(card);
  }""",
r"""    actions.append(hint, no, yes);
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
    const m = el('span', 'meta'); m.append(`${files} file${files === 1 ? '' : 's'} `, el('span', 'plus', `+${added}`), ' ', el('span', 'minus', `−${removed}`));
    m.setAttribute('aria-label', `${files} files, ${added} lines added, ${removed ? removed + ' removed' : 'nothing removed'}`);
    return m;
  }""")

# the inspector follows the state
rep(r"""    S.systems = st.systems; S.busy = st.busy;
    renderChips(); renderMap();""",
r"""    S.systems = st.systems; S.busy = st.busy;
    renderChips(); renderMap(); if (APP3) renderInspector();""")

# events: time for the timers; the ask joins the work before the card; the yes before the act in time order
rep(r"""    if (ev.ts) S.now = ev.ts * 1000;""", r"""    if (ev.ts) S.now = ev.ts * 1000;
    S.wall = Date.now();""")
rep(r"""        S.turn = d.turn; S.lastSaid = ''; S.group = null; S.doing = '';""",
r"""        S.turn = d.turn; S.lastSaid = ''; S.group = null; S.doing = ''; S.turnAt = S.now;""")
rep(r"""        trace.append(sep);
        setStatus('thinking'); showThinking(); break;""",
r"""        trace.append(sep); stamp(sep);
        setStatus('thinking'); showThinking(); break;""")
rep(r"""      case 'approval.requested': {
        if (thinkingRow) { thinkingRow.remove(); thinkingRow = null; }
        showCard(d);
        if ((d.kind === 'unlock' || d.kind === 'compose') && S.pendingGrow) { S.rows[d.id] = S.pendingGrow; S.pendingGrow = null; }""",
r"""      case 'approval.requested': {
        if (thinkingRow) { thinkingRow.remove(); thinkingRow = null; }
        if (APP3) S.titles[d.id] = d.tier === 'write' && d.detail ? plainAsk(d.detail) : d.title;
        if (!APP3) showCard(d);                       // APP3: the ask joins his work first, then the card closes it
        if ((d.kind === 'unlock' || d.kind === 'compose') && S.pendingGrow) { S.rows[d.id] = S.pendingGrow; S.pendingGrow = null; }""")
rep(r"""            trace.insertBefore(S.rows[d.id], call);
            if (d.detail) { call.dataset.sub = S.titles[d.id]; setStep(call, 'doing', null, S.titles[d.id]); }
          }
        }
        setStatus('growing'); break;""",
r"""            trace.insertBefore(S.rows[d.id], call);
            if (APP3) { const o = call.style.order; call.style.order = S.rows[d.id].style.order; S.rows[d.id].style.order = o; }
            if (d.detail) { call.dataset.sub = S.titles[d.id]; setStep(call, 'doing', null, S.titles[d.id]); }
          }
        }
        if (APP3) showCard(d);
        setStatus('growing'); break;""")
rep(r"""      case 'turn.end': setStatus(null); if (thinkingRow) { thinkingRow.remove(); thinkingRow = null; } break;
      case 'log': if (d.level === 'error') addMsg('error note', 'Error', d.text); break;
    }
  }

  function connectEvents() {""",
r"""      case 'turn.end': setStatus(null); if (thinkingRow) { thinkingRow.remove(); thinkingRow = null; } if (APP3) closeBatch(); break;
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

  function connectEvents() {""")

# fixed parts: the mark, the system selector, theme and inspector switches, the composer's "+" and send
rep(r"""    if (APP) {
      $('#toggle-map').prepend(icon('plan'));""",
r"""    if (APP3) {
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
      $('#toggle-map').prepend(icon('plan'));""")

# the welcome, Codex-style: the mark, a question in his voice, what he is for, the two controls, the way in
rep(r"""    const go = el('button', 'connect-first', 'Connect a system'); go.type = 'button';
    go.prepend(icon('plug'));
    go.onclick = () => { toggleMap(true); const f = $('#connect-form input'); if (f) f.focus(); };
    hello.append(how, go);
  }""",
r"""    const go = el('button', 'connect-first', 'Connect a system'); go.type = 'button';
    go.prepend(icon('plug'));
    go.onclick = () => { toggleMap(true); const f = $('#connect-form input'); if (f) f.focus(); };
    if (APP3) {
      hello.querySelector('.text').textContent = 'Good day. What can I look into?';
      hello.prepend(markSVG(false));
      hello.append(el('p', 'sub', 'Point me at a system and ask me anything about it. If it can’t do what you need yet, I’ll see what can be done.'));
    }
    hello.append(how, go);
  }""")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched', p)
