"""Film state: Martin's latest line in the side panel of his comps (martin-key.html, martin-build.html), as he says it
(the panel always shows his last words: "Order ten from Madison, then." in the approved 08:55 frame). Key `martinSay`
(a string; none = the approved line). Run once from the repo root: python video/v2/film/tools/patch_martin_say.py"""
import pathlib
C = pathlib.Path('video/v2/look/worlds2/comps')

def sub(path, a, b, count=1):
    p = C / path
    s = p.read_text(encoding='utf-8')
    assert s.count(a) == count, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

sub('martin-key.html', """    martinEl.style.opacity = st.martin == null || st.martin >= 1 ? '' : String(st.martin);""",
"""    martinEl.style.opacity = st.martin == null || st.martin >= 1 ? '' : String(st.martin);
    martinEl.textContent = '“' + (st.martinSay || S.martin) + '”';          // film: his latest line, as he says it""")
sub('martin-build.html', """  const hbSay = sideHB.querySelector('.hb-say'), hbCards = [...sideHB.querySelectorAll('.card')], cardEl = sideCard.querySelector('.card');""",
"""  const hbSay = sideHB.querySelector('.hb-say'), hbCards = [...sideHB.querySelectorAll('.card')], cardEl = sideCard.querySelector('.card');
  const sayEls = { card: [sideCard.querySelector('.martin-says'), S.martin], handback: [sideHB.querySelector('.martin-says'), HB.martin] };""")
sub('martin-build.html', """    when.textContent = st.time || '16:16';""", """    if (sayEls[which]) sayEls[which][0].textContent = '“' + (st.martinSay || sayEls[which][1]) + '”';   // his latest line
    when.textContent = st.time || '16:16';""")
print('patched martinSay')
