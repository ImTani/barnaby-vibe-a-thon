"""After the verdict pass: the four open items (decision footer flush, overlay keeps its name, the count keeps its noun,
the status wraps at phone width). Applied after the final verdict, verified by recapture and checks, not re-reviewed."""
p_css, p_js, p_chk = 'ui/skins/app.css', 'ui/app.js', 'video/v2/look/app2/check.js'


def patch(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:80], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8', newline='\n').write(s)


patch(p_css, [
    ("""  position: sticky; bottom: 16px; z-index: 2;""", """  position: sticky; bottom: 0; z-index: 2;"""),
    ("""  -webkit-mask-image: linear-gradient(to bottom, transparent 0, #000 16px, #000 calc(100% - 16px), transparent 100%);
  mask-image: linear-gradient(to bottom, transparent 0, #000 16px, #000 calc(100% - 16px), transparent 100%);""",
     """  -webkit-mask-image: linear-gradient(to bottom, transparent 0, #000 16px);   /* a soft edge under the toolbar; the */
  mask-image: linear-gradient(to bottom, transparent 0, #000 16px);           /* foot stays hard so a docked footer closes the card */"""),
    ("""  .brand span { display: none; }""",
     """  body:not(.overlay) .brand span { display: none; }
  .status { line-height: 1.2; }
  #status-text { white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }"""),
])
patch(p_js, [
    ("""APP ? `He can use ${x} of ${n}` : `he can use ${x} of ${n} things`""",
     """APP ? `He can use ${x} of its ${n} things` : `he can use ${x} of ${n} things`"""),
])
patch(p_chk, [
    ("""chip === 'He can use 6 of 23', chip);""", """chip === 'He can use 6 of its 23 things', chip);"""),
])
print('patched')
