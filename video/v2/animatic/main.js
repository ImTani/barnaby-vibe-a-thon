/* The animatic's frame loop. Adapted from video/main.js (v1): builds every registered scene once, then exposes
 * window.render(t). Differences: no brass grid, no captions (v2 has none); a scene's fadeIn is a crossfade OVER the
 * previous scene (which stays fully up until the new one is in), so stills never dip through grey; images are decoded
 * before __ready so the first frames are complete. Pure function of t. */
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

/* A scene is up from (start - fadeIn) until the next scene's start: the next one fades in OVER it, finishing at its
 * own start, so this one stays fully up underneath until then. Its first shot should begin at start - fadeIn. */
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

// decode every image before declaring ready (render.js waits for __ready)
const imgs = [...document.images];
Promise.all(imgs.map(im => (im.complete ? Promise.resolve() : new Promise(r => { im.onload = im.onerror = r; }))
  .then(() => im.decode ? im.decode().catch(() => {}) : 0)))
  .then(() => {
    const bad = imgs.filter(im => !im.naturalWidth).map(im => im.getAttribute('src'));
    if (bad.length) logErr('images', 'missing: ' + [...new Set(bad)].join(', '));
    window.render(0);
    window.__ready = true;
  });
})();
