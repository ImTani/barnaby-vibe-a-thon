/* Animatic helpers: still images with a camera, laid out on the cue sheet's clock (cues.js, from layout.py).
 * Everything is a pure function of t, as in v1's FRAMEWORK.md: DOM is created once in build(); render() sets every
 * animated property every frame. Coordinates: 1920x1080 stage; cameras are given in SOURCE-image pixels.
 *
 *   V(n) / VE(n)       speech onset / end of voice line n (1-based, cues.json -> voice[n-1].speech)
 *   M('mark')          a picture mark from cues.json -> marks
 *   seq(root, items, end)   a run of shots, each {src, at, fi, cam, grade, blur, fit, z, over}; returns {render(t)}
 *     at   start time; fi = crossfade-in seconds (0 = cut). A shot stays fully up until the next one has faded in.
 *     cam  [x, y, s] (static) or [[t, x, y, s], ...] keyframes (eased): (x, y) is the source point at frame centre,
 *          s the zoom over "cover" (1 = the image just fills 1920x1080). The view is clamped to the image.
 *     grade CSS filter string, or (t) => string.   blur px, or (t) => px.   fit 'contain' letterboxes on black.
 *     over (t, el, shotLocalT) optional per-frame hook for a shot's own overlays (children of el, in source px).
 */
(function (G) {
'use strict';
const SRC = {
  world: '../world/out/', look: '../look/frames/', worlds: '../look/worlds2/frames/', app3: '../look/app3/frames/',
  scr: 'assets/screens/', realapp: '../look/lisbon-pc/realapp/',
};
// natural sizes (checked against the files); anything not listed is 1920x1080
const SIZE = {
  'world/photo_2009.png': [1500, 1000], 'world/x_close_half_shop.png': [960, 1080], 'world/x_close_half_lisbon.png': [960, 1080],
  'look/shop-pc-12-desktop-16x10.png': [1920, 1200], 'realapp/barnaby-connect.png': [1424, 1277],
  'look/lisbon-02-realapp-main.png': [2560, 1440], 'look/lisbon-03-quorum-main.png': [2560, 1440],
  'look/lisbon-04-comfy-studio.png': [2560, 1440], 'look/lisbon-04-comfy-main.png': [2560, 1440],
  'look/lisbon-03b-quorum-theo-main.png': [2560, 1440], 'look/lisbon-05-night-main.png': [2560, 1440],
  'app3/app3-icons.png': [1600, 2190],
};
const path = key => { const i = key.indexOf('/'); return SRC[key.slice(0, i)] + key.slice(i + 1); };
const sizeOf = key => SIZE[key] || [1920, 1080];

const V = n => CUES.voice[n - 1].speech[0];
const VE = n => CUES.voice[n - 1].speech[1];
const M = k => { const v = CUES.marks[k]; if (v == null) throw new Error('no mark ' + k); return v; };

function camAt(cam, t) {
  if (!cam) return null;
  if (typeof cam[0] === 'number') return cam;
  const keys = cam.map(k => [k[0], k.slice(1)]);
  return keyframes(t, keys, easeInOutSine);
}

/** Place an <img> of natural size (w, h) so source point (x, y) is at the frame centre, zoom s over cover. */
function frameImg(img, w, h, x, y, s, fit) {
  const k0 = fit === 'contain' ? Math.min(W / w, H / h) : Math.max(W / w, H / h);
  const k = k0 * s, vw = w * k, vh = h * k;
  let L = W / 2 - x * k, T = H / 2 - y * k;
  if (vw >= W) L = clamp(L, W - vw, 0); else L = (W - vw) / 2;
  if (vh >= H) T = clamp(T, H - vh, 0); else T = (H - vh) / 2;
  img.style.transform = `translate(${L.toFixed(2)}px,${T.toFixed(2)}px) scale(${k.toFixed(5)})`;
  return { L, T, k };
}

/** One still: a 1920x1080 box with the image and an overlay layer that moves with the image (source px). */
function still(parent, key, o = {}) {
  const [w, h] = sizeOf(key);
  const box = el('div', { cls: 'shot' + (o.fit === 'contain' ? ' contain' : '') }, parent);
  const img = el('img', { attrs: { src: path(key), width: w, height: h, decoding: 'sync' } }, box);
  css(img, { width: w + 'px', height: h + 'px' });
  const layer = el('div', { cls: 'layer' }, box);
  css(layer, { width: w + 'px', height: h + 'px' });
  return {
    box, img, layer, key, w, h,
    place(t, cam, fit) {
      const c = camAt(cam, t) || [w / 2, h / 2, 1];
      const r = frameImg(img, w, h, c[0], c[1], c[2], fit);
      layer.style.transform = img.style.transform;
      return r;
    },
  };
}

/** A run of shots on one clock. Each shot is fully opaque until the next shot has finished fading in. */
function seq(root, items, end) {
  const list = items.map(it => ({ ...it, s: still(root, it.src, it) }));
  list.forEach((it, i) => {
    const nx = list[i + 1];
    it.end = it.until != null ? it.until : nx ? nx.at + (nx.fi || 0) : end;
    if (it.build) it.build(it.s.layer, it.s);
  });
  return {
    list,
    render(t) {
      for (const it of list) {
        const vis = t >= it.at - 1e-6 && t < it.end;
        if (!vis) { if (it.s.box.style.display !== 'none') it.s.box.style.display = 'none'; continue; }
        it.s.box.style.display = 'block';
        const fi = it.fi || 0;
        const fo = it.fo || 0;                          // optional fade OUT (to what is underneath, e.g. black)
        let op = fi > 0 ? easeInOutSine(P(t, it.at, fi)) : 1;
        if (fo > 0) op = Math.min(op, 1 - easeInOutSine(P(t, it.end - fo, fo)));
        it.s.box.style.opacity = op.toFixed(4);
        it.s.box.style.zIndex = it.z || 0;
        it.s.place(t, it.cam, it.fit);
        const g = typeof it.grade === 'function' ? it.grade(t) : (it.grade || '');
        const b = typeof it.blur === 'function' ? it.blur(t) : (it.blur || 0);
        const f = (g + (b > .05 ? ` blur(${b.toFixed(2)}px)` : '')).trim();
        it.s.img.style.filter = f || 'none';
        if (it.over) it.over(t, it.s.layer, t - it.at, it.s);
      }
    },
  };
}

/** A small text element in screen space (titles, notes). */
function label(parent, html, style) { return el('div', { cls: 'label', html, style }, parent); }

/** Fade an element in at a (over d) and out at b (over d2). Writes opacity every frame. */
function fadeEl(e, t, a, b, d = .5, d2 = .5) {
  const k = Math.min(easeInOutSine(P(t, a, d)), b == null ? 1 : 1 - easeInOutSine(P(t, b - d2, d2)));
  e.style.opacity = k.toFixed(4);
  e.style.display = k > .001 ? 'block' : 'none';
  return k;
}

/** Barnaby's mark (ui/assets/barnaby-mark.svg, the approved master), inline, with the working animation's knob tap
 * and bell dip (app3.css: 1.4 s loop, tap 3.4 px at 14%). k = 0..1 phase of one ring; ring = arcs 0..1. */
let _mk = 0;
function markSVG(color = '#D3A14A') {
  const id = 'bmtie' + (++_mk);                 // the tie is cut out of the brass, as in the master
  return `<svg viewBox="0 0 64 64" width="100%" height="100%" style="overflow:visible">
    <defs><mask id="${id}" maskUnits="userSpaceOnUse" x="0" y="0" width="64" height="64"><rect width="64" height="64" fill="#fff"/>
      <path d="M22.4 31.6 L29.6 36.4 L22.4 41.2 Z M41.6 31.6 L34.4 36.4 L41.6 41.2 Z" fill="#000" stroke="#000" stroke-width="2.6" stroke-linejoin="round"/>
      <rect x="29.2" y="33.4" width="5.6" height="6" rx="2" fill="#000"/></mask></defs>
    <g class="knob"><circle cx="32" cy="14.5" r="5.6" fill="${color}"/></g>
    <g class="body"><path d="M10.5 45.2 A21.5 21.5 0 0 1 53.5 45.2 Z" fill="${color}" mask="url(#${id})"/></g>
    <rect x="5" y="48.6" width="54" height="6.6" rx="3.3" fill="${color}"/>
    <g class="ring" fill="none" stroke="${color}" stroke-width="2.4" stroke-linecap="round">
      <path d="M12 24 Q8 30 9 36"/><path d="M52 24 Q56 30 55 36"/></g></svg>`;
}
function markAnim(svgHost, t, t0) {
  // one ring of the bell at t0: knob taps, the bell dips, arcs bloom and fade (pure function of t)
  const u = (t - t0) / 1.4;
  const ph = u >= 0 && u <= 1 ? u : -1;
  const tap = ph < 0 ? 0 : ph < .14 ? ph / .14 : ph < .4 ? 1 - (ph - .14) / .26 : 0;
  const knob = svgHost.querySelector('.knob'), body = svgHost.querySelector('.body'), ring = svgHost.querySelector('.ring');
  knob.setAttribute('transform', `translate(0 ${(3.4 * easeInOutSine(tap)).toFixed(3)})`);
  body.setAttribute('transform', `translate(0 ${(45.2 * (1 - (1 - .045 * easeInOutSine(tap)))).toFixed(3)}) scale(1 ${(1 - .045 * easeInOutSine(tap)).toFixed(4)})`);
  const ro = ph < .12 ? 0 : ph < .22 ? (ph - .12) / .1 : ph < .62 ? 1 - (ph - .22) / .4 : 0;
  const rs = ph < .12 ? .9 : lerp(.9, 1.14, clamp((ph - .12) / .5));
  ring.setAttribute('opacity', clamp(ro).toFixed(3));
  ring.setAttribute('transform', `translate(32 34) scale(${rs.toFixed(3)}) translate(-32 -34)`);
}

/** Keep on-screen text in a still hidden until it is said. lines: [[x0, y0, x1, y1], ...] in source px; each is
 * covered by a patch of the frame's own ground (a solid `color`, or the same image `dy` px lower, where it is blank),
 * whose left edge moves right as the line is spoken. The lines share the window [a, b] in proportion to `chars`
 * (default: their widths). Call build() once (into a shot's layer), render(t) every frame. */
function reveal(layer, key, lines, o) {
  const pad = o.pad == null ? 3 : o.pad;
  const [iw, ih] = sizeOf(key);
  const total = (o.chars || lines.map(l => l[2] - l[0])).reduce((s, c) => s + c, 0);
  let acc = 0;
  const parts = lines.map((l, i) => {
    const c = (o.chars || lines.map(q => q[2] - q[0]))[i];
    const p = { x0: l[0] - pad, y0: l[1] - pad, x1: l[2] + pad, y1: l[3] + pad, f0: acc / total, f1: (acc + c) / total };
    acc += c;
    p.el = el('div', {}, layer);
    css(p.el, { position: 'absolute', top: p.y0 + 'px', height: (p.y1 - p.y0) + 'px' });
    if (o.dy != null) css(p.el, { backgroundImage: `url("${path(key)}")`, backgroundSize: `${iw}px ${ih}px` });
    else if (o.grads) css(p.el, { backgroundImage: `linear-gradient(90deg, ${o.grads[i].join(', ')})`, backgroundSize: `${p.x1 - p.x0}px 100%`, backgroundRepeat: 'no-repeat' });
    else p.el.style.background = o.color;
    return p;
  });
  return {
    render(t) {
      const a = typeof o.a === 'function' ? o.a() : o.a, b = typeof o.b === 'function' ? o.b() : o.b;
      const u = clamp((t - a) / (b - a));
      for (const p of parts) {
        const k = clamp((u - p.f0) / (p.f1 - p.f0));
        const x = lerp(p.x0, p.x1, k), w = p.x1 - x;
        if (w <= .5) { p.el.style.display = 'none'; continue; }
        p.el.style.display = 'block';
        p.el.style.left = x.toFixed(1) + 'px'; p.el.style.width = w.toFixed(1) + 'px';
        if (o.dy != null) p.el.style.backgroundPosition = `${(-x).toFixed(1)}px ${-(p.y0 + o.dy)}px`;
        else if (o.grads) p.el.style.backgroundPosition = `${(p.x0 - x).toFixed(1)}px 0px`;
      }
    },
  };
}

/** A soft light band sweeping across the frame (the time-lapse; "light slides across the desk"). */
function sweep(parent, o = {}) {
  const e = el('div', { cls: 'ov' }, parent);
  css(e, { mixBlendMode: o.blend || 'screen', background: `linear-gradient(${o.angle || 100}deg, rgba(0,0,0,0) 0%, ${o.color || 'rgba(255,236,200,.55)'} 50%, rgba(0,0,0,0) 100%)`,
    width: '1400px', left: '0px', display: 'none' });
  return {
    render(t, a, b, peak = 1) {
      const k = (t - a) / (b - a);
      if (k <= 0 || k >= 1) { e.style.display = 'none'; return; }
      e.style.display = 'block';
      e.style.transform = `translateX(${lerp(-1400, 1920, k).toFixed(1)}px)`;
      e.style.opacity = (peak * Math.sin(Math.PI * k)).toFixed(3);
    },
  };
}

Object.assign(G, { SRC, SIZE, V, VE, M, still, seq, frameImg, label, fadeEl, markSVG, markAnim, sizeOf, imgPath: path, reveal, sweep });
})(window);
