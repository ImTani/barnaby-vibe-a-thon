"""Second pass on ui/app.js for ?skin=app: path breaks in technical names, a short empty panel, and readable previews (by hand)."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else 'ui/app.js'
s = open(p, encoding='utf-8').read()
def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:90], s.count(old))
    s = s.replace(old, new)

rep("""      body.append(el('p', 'sys empty', 'No system yet. Point Barnaby at one below: he reads its code and lists everything it can do, and to start he only uses the things that look something up.'));""",
"""      body.append(el('p', 'sys empty', APP ? 'No system connected yet.' : 'No system yet. Point Barnaby at one below: he reads its code and lists everything it can do, and to start he only uses the things that look something up.'));""")
rep("""          li.append(el('code', 'tech', e.key));
          li.title = e.description || '';""",
"""          li.append(APP ? techName(e.key) : el('code', 'tech', e.key));
          li.title = e.description || '';""")
rep("""          li.append(el('code', 'tech', k.tool));
          ul.append(li);""",
"""          li.append(APP ? techName(k.tool) : el('code', 'tech', k.tool));
          ul.append(li);""")
rep("""  // the plan of the house, in plain words: every thing the system can do, by area, with its state as a mark and a word
  function renderMapHuman() {""",
"""  // APP: a technical name may break after a slash or an underscore (a <wbr>, so a copied name stays whole)
  function techName(t) {
    const c = el('code', 'tech');
    String(t).split(/(?<=[/_])/).forEach((part, i) => { if (i) c.append(document.createElement('wbr')); c.append(part); });
    return c;
  }
  // the plan of the house, in plain words: every thing the system can do, by area, with its state as a mark and a word
  function renderMapHuman() {""")
# previewText: edited by hand (see ui/app.js), the regex escapes do not survive a Python string well
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched', p)
