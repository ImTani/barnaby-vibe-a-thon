"""app3, second pass: the kept yes sits before the work it allowed; order stamps leave gaps for that; compose's kind line."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else 'ui/app.js'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:90], s.count(old))
    s = s.replace(old, new)


rep(r"""  const stamp = n => { if (APP3 && n) n.style.order = n.classList.contains('pending') ? '2147483000' : String(++seq); return n; };""",
    r"""  const stamp = n => { if (APP3 && n) n.style.order = n.classList.contains('pending') ? '2147483000' : String(++seq * 10); return n; };""")
rep(r"""{ unlock: 'A new key', compose: 'One step instead of several', build: 'A new piece for the system' }""",
    r"""{ unlock: 'A new key', compose: 'A shortcut', build: 'A new piece for the system' }""")
rep(r"""        if (title) {
          const li = addMsg('decision ' + (yes ? 'yes' : 'no'), 'You', '');
          li.querySelector('.text').append(el('b', 'said', said), el('span', 'sep', ': '), title);
        }""",
    r"""        if (title) {
          const li = addMsg('decision ' + (yes ? 'yes' : 'no'), 'You', '');
          li.querySelector('.text').append(el('b', 'said', said), el('span', 'sep', ': '), title);
          const b = APP3 && S.rows[d.id] && BATCHES[S.rows[d.id].dataset.b];   // APP3: the yes sits before the work it allowed
          if (b && !b.li.classList.contains('ask-only')) li.style.order = String(Number(b.li.style.order) - 5);
        }""")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched', p)
