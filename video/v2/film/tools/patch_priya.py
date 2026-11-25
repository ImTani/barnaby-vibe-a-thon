"""Film state for Priya's bench (worlds2 priya-tuesday.html): the two job tags sliding onto her bench, Barnaby's line
typed as he says it, the collecting list and Theo's README slip arriving. No state = the approved frame. Run once
from the repo root: python video/v2/film/tools/patch_priya.py"""
import pathlib
C = pathlib.Path('video/v2/look/worlds2/comps')

def sub(path, a, b, count=1):
    p = C / path
    s = p.read_text(encoding='utf-8')
    assert s.count(a) == count, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

sub('priya-tuesday.html', """  document.fonts.ready.then(() => { document.body.dataset.ready = '1'; });
})();""", """  /* film use: COMP.render(state); keys (all optional; none = this frame): her 0..1 her line, say 0..1 Barnaby's line
     typed, cards 0..2 the two tags sliding onto the bench, rc 0..1 the collecting list, note 0..1 Theo's slip */
  const tags = [...$('tags').children], rots = tags.map(t => t.style.transform), col = document.querySelector('.col'), slip = document.querySelector('.slip');
  const ease = k => 1 - Math.pow(1 - Math.max(0, Math.min(1, k)), 3);
  window.COMP = { render(st) {
    st = st || {};
    const cards = st.cards == null ? 2 : st.cards;
    tags.forEach((t, i) => { const k = cards - i * .55; t.style.opacity = k >= 1 ? '' : Math.max(0, Math.min(1, k * 2)).toFixed(3); t.style.transform = k >= 1 ? rots[i] : `translate(${((1 - ease(k)) * (i ? 90 : -90)).toFixed(1)}px,${((1 - ease(k)) * -110).toFixed(1)}px) ` + rots[i].replace(/rotate\\(([-\\d.]+)deg\\)/, (m, a) => `rotate(${(+a + (1 - ease(k)) * (i ? 9 : -9)).toFixed(2)}deg)`); });
    $('her').parentNode.style.opacity = st.her == null || st.her >= 1 ? '' : String(st.her);
    const say = st.say == null ? 1 : st.say;
    $('him').textContent = S.barnaby.slice(0, Math.round(S.barnaby.length * Math.max(0, Math.min(1, say))));
    $('him').parentNode.style.opacity = say > 0 ? '' : '0';
    const rc = st.rc == null ? 1 : st.rc;
    [...col.children].forEach(e => { if (e !== slip) e.style.opacity = rc >= 1 ? '' : ease(rc).toFixed(3); });
    const nk = st.note == null ? 1 : st.note;
    slip.style.opacity = nk >= 1 ? '' : Math.min(1, nk * 2.5).toFixed(3);
    slip.style.transform = nk >= 1 ? '' : `translate(${((1 - ease(nk)) * 60).toFixed(1)}px,${((1 - ease(nk)) * 26).toFixed(1)}px) rotate(${(-1.6 + (1 - ease(nk)) * 4).toFixed(2)}deg)`;
  } };
  document.fonts.ready.then(() => { document.body.dataset.ready = '1'; });
})();""")
print('patched priya')
