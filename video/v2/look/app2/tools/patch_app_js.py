"""One-off patch of ui/app.js for the ?skin=app look (kept beside the frames as a record of what changed)."""
import sys

p = sys.argv[1] if len(sys.argv) > 1 else 'ui/app.js'
s = open(p, encoding='utf-8').read()
orig = s


def rep(old, new):
    global s
    n = s.count(old)
    assert n == 1, (old[:90], n)
    s = s.replace(old, new)


rep("""   with what it does, what it reads and changes, the checks and the undo. Without a skin nothing here changes. */""",
"""   with what it does, what it reads and changes, the checks and the undo. Without a skin nothing here changes.
   ?skin=app is the professional app look: the same household view, plus a few things only it uses (a lead line on
   each card, the disclosures above the decision, a state word on every ability, a welcome that teaches the controls,
   errors in plain words). Those are marked APP below. */""")

rep("""  const HUMAN = !!SKIN;
""", """  const HUMAN = !!SKIN;
  const APP = SKIN === 'app';
""")

rep("""  const lowerFirst = s => (s ? s[0].toLowerCase() + s.slice(1) : s);""",
"""  // the status says what he is doing now: "Looked at repair jobs…" (the step, once done) -> "Looking at repair jobs…"
  const NOW = { Looked: 'Looking', Gave: 'Giving', Added: 'Adding', Booked: 'Booking', Changed: 'Changing', Marked: 'Marking',
    Raised: 'Raising', Cancelled: 'Cancelling', Ordered: 'Ordering', Sent: 'Sending', Set: 'Setting', Made: 'Making',
    Moved: 'Moving', Updated: 'Updating', Created: 'Creating', Removed: 'Removing', Deleted: 'Deleting', Recorded: 'Recording',
    Assigned: 'Assigning', Used: 'Using', Checked: 'Checking' };
  const doingNow = line => String(line || '').replace(/^\\w+/, w => NOW[w] || w);
  const lowerFirst = s => (s ? s[0].toLowerCase() + s.slice(1) : s);""")

rep("""        S.calls.set(d.id, row); setStatus('thinking', p.line); showThinking(); break;""",
"""        S.calls.set(d.id, row); setStatus('thinking', doingNow(p.line)); showThinking(); break;""")

rep("""    li.append(el('div', 'who', who), el('div', 'text', text));
    messages.append(li);
    settle();
    return li;
  }""",
"""    if (APP && /\\berror\\b/.test(kind)) {
      const [head, next] = plainError(who);
      li.append(el('div', 'who', head), el('div', 'text', next));
      if (text) li.append(fold('tech', 'Details', el('pre', 'technical-body', String(text))));
    } else li.append(el('div', 'who', who), el('div', 'text', text));
    if (APP) li.dataset.who = who;
    messages.append(li);
    settle();
    return li;
  }
  // APP: an error says what happened and what to do next; the raw message is folded under Details
  function plainError(who) {
    if (who === 'Voice') return ['Voice isn’t available just now', 'I can’t hear you at the moment. Type your question below instead, and I’ll answer as usual.'];
    if (who === 'Mock') return ['The recorded run couldn’t be loaded', 'The replay needs ui/fixtures/demo-run.json.'];
    return ['Something went wrong', 'I couldn’t finish that. Ask again in a moment, or see the details below.'];
  }""")

rep("""        const sep = el('li', 'turn-sep');
        sep.append(el('span', 'no', `No. ${d.turn} · ${clock()}`), el('span', 'q', own ? d.text : 'Getting started'));""",
"""        const sep = el('li', 'turn-sep');
        if (APP) sep.append(el('span', 'q', own ? d.text : 'Getting started'), el('span', 'when', clock()));
        else sep.append(el('span', 'no', `No. ${d.turn} · ${clock()}`), el('span', 'q', own ? d.text : 'Getting started'));""")

rep("""  function showCardHuman(a) {
    const f = cardFacts(a);""",
"""  function showCardHuman(a) {
    if (APP) return showCardApp(a);
    const f = cardFacts(a);""")

rep("""  async function decide(id, approved) {""",
"""  // APP: the card reads top to bottom the way a decision is made: what and why, the facts, the change and the
  // technical record for whoever wants them, and last the yes and the no, with how they may be given.
  function diffMeta(diff) {
    const lines = diff.split('\\n');
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
    const head = el('div', 'head'); head.append(icon(KIND_ICON[a.kind] || 'pen', 'kind'), el('h3', 'title', f.head));
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
      sum.append(lab, el('span', 'meta', diffMeta(a.diff)));
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
    const hint = el('span', 'hint', a.voice_ok ? 'Or just say “yes”.' : a.tier === 'build' ? 'A change like this needs a click, not a spoken yes.' : 'One click, and he asks again before each order or change.');
    actions.append(hint, no, yes);
    card.append(actions);
    cards.append(card);
    bringIntoView(card);
  }
  async function decide(id, approved) {""")

rep("""  function renderChips() {
    const box = $('#systems-chips'); box.textContent = '';""",
"""  function renderChips() {
    const box = $('#systems-chips'); box.textContent = '';
    if (APP) document.body.classList.toggle('no-system', !S.systems.length);""")

rep("""          li.append(icon(fresh ? 'room' : state), el('span', 'what', upperFirst(sentence(e.description) || e.tool.replace(/_/g, ' '))));
          if (fresh) li.append(el('span', 'today', 'today'));""",
"""          li.append(icon(fresh ? 'room' : state), el('span', 'what', upperFirst(sentence(e.description) || e.tool.replace(/_/g, ' '))));
          if (APP) li.append(el('span', fresh ? 'today' : 'state', fresh ? 'Added today' : { use: 'Can use', key: 'Asks first', shut: 'Kept shut' }[state]));
          else if (fresh) li.append(el('span', 'today', 'today'));""")

rep("""          li.append(icon('passage'), el('span', 'what', S.skillNames[k.tool] || k.name || upperFirst(k.tool.replace(/_/g, ' '))));
          if (fresh) li.append(el('span', 'today', 'today'));""",
"""          li.append(icon('passage'), el('span', 'what', S.skillNames[k.tool] || k.name || upperFirst(k.tool.replace(/_/g, ' '))));
          if (APP) li.append(el('span', fresh ? 'today' : 'state', fresh ? 'Added today' : 'Can use'));
          else if (fresh) li.append(el('span', 'today', 'today'));""")

rep("""['room', 'new', 'New today']]) {""", """['room', 'new', APP ? 'Added today' : 'New today']]) {""")

rep("""    talk.after(el('span', 'talk-hint', 'or hold the space bar'));
    setStatus(null);
  }""",
"""    talk.after(el('span', 'talk-hint', 'or hold the space bar'));
    if (APP) {
      $('#toggle-map').prepend(icon('plan'));
      $('#ask-input').placeholder = 'Ask Barnaby anything…';
      const h = $('#connect-form h3');
      h.textContent = 'Connect a system';
      h.after(el('p', 'help', 'Barnaby reads its code and lists everything it can do. To begin, he only uses the things that look something up.'));
    }
    setStatus(null);
  }""")

rep("""  const hello = addMsg('barnaby intro', 'Barnaby', 'Good day. Point me at a system and ask me anything about it; if it can’t do what you need yet, I’ll see what can be done.');""",
"""  const hello = addMsg('barnaby intro', 'Barnaby', 'Good day. Point me at a system and ask me anything about it; if it can’t do what you need yet, I’ll see what can be done.');
  if (APP) {                       // a welcome that teaches the two controls, and the way in when there is no system yet
    const how = el('ul', 'how');
    for (const [ico, txt] of [['mic', 'Hold the button below, or the space bar, and ask out loud.'], ['keys', 'Or type your question and press Enter.']]) {
      const li = el('li'); li.append(icon(ico), el('span', '', txt)); how.append(li);
    }
    const go = el('button', 'connect-first', 'Connect a system'); go.type = 'button';
    go.prepend(icon('plug'));
    go.onclick = () => { toggleMap(true); const f = $('#connect-form input'); if (f) f.focus(); };
    hello.append(how, go);
  }""")

open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched', p, len(orig), '->', len(s))
