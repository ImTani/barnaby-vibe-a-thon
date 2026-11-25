"""Third pass on ui/app.js for ?skin=app, after the finish review: kept decisions in plain words, the yes before the
act, a toolbar count that follows the replay, card hints as sentences, technical names folded in the abilities list."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else 'ui/app.js'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:90], s.count(old))
    s = s.replace(old, new)


# a write card's own sentence, without "I'll" and "shall I?", names the thing: "Ten pairs of the Shimano resin pads..."
rep(r"""    S.titles[a.id] = a.title;
    if (HUMAN) return showCardHuman(a);""",
r"""    S.titles[a.id] = APP && a.tier === 'write' && a.detail ? plainAsk(a.detail) : a.title;
    if (HUMAN) return showCardHuman(a);""")
rep(r"""  async function decide(id, approved) {""",
r"""  function plainAsk(t) {
    return upperFirst(String(t).trim().replace(/,?\s*shall I\??$/i, '').replace(/^I(?:'|’)ll\s+/, '').replace(/\.$/, ''));
  }
  async function decide(id, approved) {""")
rep(r"""    const hint = el('span', 'hint', a.voice_ok ? 'Or just say “yes”.' : a.tier === 'build' ? 'A change like this needs a click, not a spoken yes.' : 'One click.');""",
r"""    const hint = el('span', 'hint', a.voice_ok ? 'Or just say “yes”.' : a.tier === 'build' ? 'A change like this needs a click, not a spoken yes.'
      : a.kind === 'unlock' ? 'A new key needs a click, not a spoken yes.' : 'A new step like this needs a click, not a spoken yes.');""")

# only the newest state answer counts (the replay's state must not be overwritten by the server's, which lands later)
rep(r"""  async function refreshState() {
    const r = await fetch('/api/state'); const st = await r.json();""",
r"""  let stateAsked = 0;
  async function refreshState() {
    const n = ++stateAsked;
    const r = await fetch('/api/state'); const st = await r.json();
    if (n !== stateAsked) return;""")
rep(r"""        chip.append(el('b', '', upperFirst(s.title || s.name)), el('span', '', `he can use ${x} of ${n} things`));""",
r"""        chip.append(el('b', '', upperFirst(s.title || s.name)), el('span', '', APP ? `He can use ${x} of ${n}` : `he can use ${x} of ${n} things`));""")

# the step: said as it happens, past tense when done; a write waits under the yes it needs
rep(r"""        const row = stepRow('doing', p.line, p.sub,""",
r"""        const row = stepRow('doing', APP ? doingNow(p.line) : p.line, p.sub,""")
rep(r"""        row.dataset.sub = p.sub;
        S.calls.set(d.id, row);""",
r"""        row.dataset.sub = p.sub; row.dataset.line = p.line; S.lastCall = row;
        S.calls.set(d.id, row);""")
rep(r"""        setStep(row, why ? 'err' : 'done', null, why ? why.slice(0, 120) : row.dataset.sub || '');""",
r"""        setStep(row, why ? 'err' : 'done', APP ? row.dataset.line : null, why ? why.slice(0, 120) : row.dataset.sub || '');""")
rep(r"""        else S.rows[d.id] = stepRow('ask', `Asked you: ${d.title}`, '', null, KIND_ICON[d.kind] || 'pen');""",
r"""        else {
          S.rows[d.id] = stepRow('ask', `Asked you: ${S.titles[d.id] || d.title}`, '', null, KIND_ICON[d.kind] || 'pen');
          const call = S.lastCall;                     // APP: the order or the change waits under the yes it needs
          if (APP && call && call.classList.contains('doing') && call.nextElementSibling === S.rows[d.id]) {
            trace.insertBefore(S.rows[d.id], call);
            if (d.detail) { call.dataset.sub = S.titles[d.id]; setStep(call, 'doing', null, S.titles[d.id]); }
          }
        }""")

# abilities: an icon that means allowed, the technical names folded behind one switch
rep(r"""    for (const [ico, cls, txt] of [['use', 'use', 'He can use it'],""",
r"""    for (const [ico, cls, txt] of [[APP ? 'can' : 'use', 'use', 'He can use it'],""")
rep(r"""          li.append(icon(keyed ? 'use' : fresh ? 'room' : state), el""",
r"""          li.append(icon(APP && (keyed || (state === 'use' && !fresh)) ? 'can' : fresh ? 'room' : state), el""")
rep(r"""    body.append(legend);
    for (const s of S.systems) {
      const sec = el('section', 'sys');""",
r"""    body.append(legend);
    if (APP) {                       // for whoever looks after the code: the technical name under each ability, on request
      const t = el('button', 'tech-toggle', 'Show technical names'); t.type = 'button';
      const show = on => { S.showTech = on; $('#map').classList.toggle('show-tech', on); t.setAttribute('aria-pressed', String(on)); t.textContent = on ? 'Hide technical names' : 'Show technical names'; };
      t.onclick = () => show(!S.showTech); show(!!S.showTech);
      body.append(t);
    }
    for (const s of S.systems) {
      const sec = el('section', 'sys');""")

# a shorter placeholder fits every width
rep("""      $('#ask-input').placeholder = 'Ask Barnaby anything…';
""", "")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched', p)
