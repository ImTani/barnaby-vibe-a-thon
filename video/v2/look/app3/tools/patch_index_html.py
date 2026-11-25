"""ui/index.html for ?skin=app3: the skin switch learns app3, the theme before first paint, the favicon, the mark's
mask, a few icons, and the inspector's slot (hidden in every other look)."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else 'ui/index.html'
s = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'


def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl)
    assert s.count(a) == 1, (a[:70], s.count(a))
    s = s.replace(a, b)


rep('''<title>Barnaby</title>
<link rel="stylesheet" href="/ui/style.css" id="look">''', '''<title>Barnaby</title>
<link rel="icon" href="/ui/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/ui/style.css" id="look">''')
rep('''   the default, and ?skin=classic still opens the old look (style.css). */''', '''   the default, and ?skin=classic still opens the old look (style.css). ?skin=app3 is round 3, modelled on the Claude
   and Codex desktop apps; ?theme=dark|light (or the switch in app3, remembered) picks its light or dark. */''')
rep(r'''  var m = /[?&]skin=(app|signpost|ticket|classic)\b/.exec(location.search);''', r'''  var t = /[?&]theme=(light|dark)\b/.exec(location.search), theme = t ? t[1] : null;
  try { theme = theme || localStorage.getItem('barnaby-theme'); } catch (e) {}
  if (theme) document.documentElement.setAttribute('data-theme', theme);
  var m = /[?&]skin=(app3|app|signpost|ticket|classic)\b/.exec(location.search);''')
rep('''<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <defs>''', '''<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <defs>
    <!-- Barnaby's mark (app3): a counter bell wearing a bow tie; the tie is cut out of the brass by this mask -->
    <mask id="bb-tie" maskUnits="userSpaceOnUse" x="0" y="0" width="64" height="64">
      <rect width="64" height="64" fill="#fff"/>
      <path d="M22.4 31.6 L29.6 36.4 L22.4 41.2 Z M41.6 31.6 L34.4 36.4 L41.6 41.2 Z" fill="#000" stroke="#000" stroke-width="2.6" stroke-linejoin="round"/>
      <rect x="29.2" y="33.4" width="5.6" height="6" rx="2" fill="#000"/>
    </mask>''')
rep('''    <symbol fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" id="i-can"''',
    '''    <symbol fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/></symbol>
    <symbol fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" id="i-moon" viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></symbol>
    <symbol fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" id="i-panel" viewBox="0 0 24 24"><rect x="3" y="4.5" width="18" height="15" rx="2.5"/><path d="M15 4.5v15"/></symbol>
    <symbol fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" id="i-plus" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></symbol>
    <symbol fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" id="i-send" viewBox="0 0 24 24"><path d="M12 19V5.5M6 11.5l6-6 6 6"/></symbol>
    <symbol fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" id="i-can"''')
rep('''<footer class="input">''', '''<aside class="inspector" id="inspector" hidden aria-label="Barnaby at a glance"></aside>

<footer class="input">''')
open(p, 'w', encoding='utf-8', newline='').write(s)
print('patched', p)
