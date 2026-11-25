/* The film's frame loop (from the animatic's main.js): builds every registered scene once, then exposes
 * window.render(t). A scene's fadeIn is a crossfade OVER the previous scene (which stays fully up until the new one is
 * in). Before __ready: every image is decoded, every live look-dev page (iframe) has signalled body[data-ready=1] and
 * its fonts are in, and each scene's optional ready() hook has run (geometry read once from the live pages).
 * Pure function of t; render.js awaits window.settle() after render(t) so swapped sequence frames are decoded. */
(function () {
'use strict';
window.DURATION = CUES.duration;
window.__errors = [];
const logErr = (where, e) => { const m = `[${where}] ${e && e.stack ? e.stack.split('\n').slice(0, 3).join(' | ') : e}`; window.__errors.push(m); console.error(m); };
window.addEventListener('error', ev => logErr('window', ev.error || ev.message));

const stage = document.getElementById('stage');
const black = document.getElementById('black');
window.Q = { t: 0, black: 0, setBlack(v) { Q.black = Math.max(Q.black, clamp(v)); }, scene: null };

SCENES.sort((a, b) => a.start - b.start);
SCENES.forEach((s, i) => { s.next = SCENES[i + 1] || null; });
for (const s of SCENES) {
  s.root = el('div', { cls: 'scene', attrs: { id: 'scene-' + s.id } }, stage);
  s.root.style.zIndex = SCENES.indexOf(s) + 1;
  try { s.build(s.root, s); } catch (e) { logErr('build ' + s.id, e); s._broken = true; }
}

function opacityOf(s, t) {
  const fi = s.start <= 0 ? 0 : (s.fadeIn || 0);
  if (t < s.start - fi) return 0;
  if (t >= (s.next ? s.next.start : s.end + 1e-6)) return 0;
  return fi > 0 ? easeInOutSine(P(t, s.start - fi, fi)) : 1;
}

window.render = function (t) {
  t = +t; Q.t = t; Q.black = 0;
  for (const s of SCENES) {
    const f = opacityOf(s, t);
    if (f <= 0.0005 || s._broken) { if (s.root.style.display !== 'none') s.root.style.display = 'none'; continue; }
    s.root.style.display = 'block';
    s.root.style.opacity = f;
    Q.scene = s;
    try { s.render(t, t - s.start, f); } catch (e) { logErr('render ' + s.id + ' @' + t.toFixed(2), e); }
    Q.scene = null;
  }
  black.style.opacity = Q.black;
  return window.__errors.length;
};

const imgReady = im => (im.complete ? Promise.resolve() : new Promise(r => { im.onload = im.onerror = r; }))
  .then(() => im.decode ? im.decode().catch(() => {}) : 0);
const frameReady = f => new Promise(res => {
  const t0 = performance.now();
  (function poll() {
    let ok = false;
    try { const d = f.contentDocument; ok = d && d.body && d.body.dataset.ready === '1'; } catch (e) { logErr('iframe', e); return res(); }
    if (ok) return f.contentDocument.fonts.ready.then(() => res());
    if (performance.now() - t0 > 60000) { logErr('iframe', 'not ready: ' + f.getAttribute('src')); return res(); }
    setTimeout(poll, 50);
  })();
});
const imgs = [...document.images];
Promise.all([document.fonts.ready, ...imgs.map(imgReady), ...LIVE_FRAMES.map(frameReady)])
  .then(() => {
    const bad = imgs.filter(im => !im.naturalWidth).map(im => im.getAttribute('src'));
    if (bad.length) logErr('images', 'missing: ' + [...new Set(bad)].join(', '));
    for (const s of SCENES) if (s.ready) try { s.ready(); } catch (e) { logErr('ready ' + s.id, e); }
    document.body.classList.remove('loading');
    window.render(0);
    return window.settle();
  })
  .then(() => { window.__ready = true; });
})();
