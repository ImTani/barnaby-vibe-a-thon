/* Film helpers (from the animatic's shots.js): shots laid out on the cue sheet's clock (cues.js, from layout.py).
 * Everything is a pure function of t, as in v1's FRAMEWORK.md: DOM is created once in build(); render() sets every
 * animated property every frame. Coordinates: 1920x1080 stage; cameras are given in SOURCE pixels.
 *
 * A shot's `src` is one of
 *   'world/x.png' 'look/..' 'worlds/..' 'realapp/..' 'rapp/..'   a still (as the animatic). A world still is swapped for
 *        the Blender agent's sequence when ../world/anim/shots.json has a "done" shot that `replaces` it (a key or a
 *        list of keys) over this shot's time (frame = floor((t - start) * 24) + 1, clamped); the camera move and the
 *        grade are then dropped (the light is baked in), unless the item says keepGrade.
 *   'live/shop'  'live/lis-main'  'live/lis-studio'   an approved look-dev page in an <iframe>, driven every frame
 *        through its documented film API (PC / LX) with `state(t, lt)` -> {preset, ...keys}
 *   'comp/<name>'   a worlds2 comp in an <iframe>, driven through window.COMP.render(state) (defaults = approved frame)
 *
 *   V(n) / VE(n)       speech onset / end of voice line n (1-based, cues.json -> voice[n-1].speech)
 *   M('mark')          a picture mark from cues.json -> marks
 *   seq(root, items, end)   a run of shots, each {src, at, fi, fo, cam, grade, blur, fit, z, state, over, build}
 *     at   start time; fi = crossfade-in seconds (0 = cut). A shot stays fully up until the next one has faded in.
 *     cam  [x, y, s] (static) or [[t, x, y, s], ...] keyframes (eased): (x, y) is the source point at frame centre,
 *          s the zoom over "cover" (1 = the image just fills 1920x1080). The view is clamped to the image.
 *     over (t, layer, shotLocalT, shot) per-frame hook for a shot's own overlays (children of layer, in source px).
 */
(function (G) {
'use strict';
const SRC = {
  world: '../world/out/', look: '../look/frames/', worlds: '../look/worlds2/frames/', app3: '../look/app3/frames/',
  scr: '../animatic/assets/screens/', realapp: '../look/lisbon-pc/realapp/', rapp: 'assets/realapp/',
};
const SIZE = {
  'world/photo_2009.png': [1500, 1000], 'world/x_close_half_shop.png': [960, 1080], 'world/x_close_half_lisbon.png': [960, 1080],
  'look/shop-pc-12-desktop-16x10.png': [1920, 1200], 'realapp/barnaby-connect.png': [1424, 1277], 'realapp/barnaby-connect-empty.png': [1424, 1277],
  'look/lisbon-02-realapp-main.png': [2560, 1440], 'look/lisbon-03-quorum-main.png': [2560, 1440],
  'look/lisbon-04-comfy-studio.png': [2560, 1440], 'look/lisbon-04-comfy-main.png': [2560, 1440],
  'look/lisbon-03b-quorum-theo-main.png': [2560, 1440], 'look/lisbon-05-night-main.png': [2560, 1440],
};
const LIVE = {
  shop: { url: '../look/shop-pc/index.html?state=desktop&blur=0', apply: (w, s) => w.pc.render(w.pc.preset(s.preset || 'desktop', s)) },
  'lis-main': { url: '../look/lisbon-pc/index.html?monitor=main', apply: (w, s) => w.desk.render(w.LX.preset(s.preset || 'rest', s)) },
  'lis-main-empty': { url: '../look/lisbon-pc/index.html?monitor=main&realimg=empty', apply: (w, s) => w.desk.render(w.LX.preset(s.preset || 'rest', s)) },
  'lis-studio': { url: '../look/lisbon-pc/index.html?monitor=studio', apply: (w, s) => w.desk.render(w.LX.preset(s.preset || 'rest', s)) },
};
const path = key => {
  if (key.startsWith('rapp/')) return SRC.rapp + key.slice(5);
  const i = key.indexOf('/'); return SRC[key.slice(0, i)] + key.slice(i + 1);
};
const sizeOf = key => {
  if (key.startsWith('rapp/')) return SIZE['realapp/barnaby-connect.png'];
  const wf = G.WORLD_FILES && key.startsWith('world/') && G.WORLD_FILES[key.slice(6)];
  return wf || SIZE[key] || [1920, 1080];
};
/** The first world still of `keys` that exists on disk (render.js lists ../world/out as window.WORLD_FILES): the
 * Blender agent's new stills swap in when they land, the approved ones stand in until then. */
const pick = (...keys) => { const wf = G.WORLD_FILES; if (!wf) return keys[keys.length - 1]; return keys.find(k => !k.startsWith('world/') || wf[k.slice(6)]) || keys[keys.length - 1]; };
const isRoom = key => key.startsWith('world/');
const isLive = key => key.startsWith('live/') || key.startsWith('comp/');

const V = n => CUES.voice[n - 1].speech[0];
const VE = n => CUES.voice[n - 1].speech[1];
const M = k => { const v = CUES.marks[k]; if (v == null) throw new Error('no mark ' + k); return v; };

/* ---- the Blender agent's sequences (../world/anim/shots.json; render.js injects it as window.BLENDER at load) ---- */
const FILM_FPS = 24;
function blenderManifest() {
  if (G.BLENDER !== undefined) return G.BLENDER;
  try { const x = new XMLHttpRequest(); x.open('GET', '../world/anim/shots.json', false); x.send(); G.BLENDER = x.status === 0 || x.status === 200 ? JSON.parse(x.responseText) : null; }
  catch (e) { G.BLENDER = null; }
  return G.BLENDER;
}
function blenderFor(key, a, b) {
  const m = blenderManifest();
  if (!m || !m.shots || !key.startsWith('world/')) return null;
  let best = null, bestOv = 0;
  for (const s of m.shots) {
    const rep = Array.isArray(s.replaces) ? s.replaces : [s.replaces];    // one shot may cover several stills in a row
    if (s.status !== 'done' || !rep.includes(key) || !(s.frames > 0)) continue;
    const s0 = s.start, s1 = s.start + s.frames / (m.fps || FILM_FPS);
    const ov = Math.min(b, s1) - Math.max(a, s0);
    if (ov > bestOv && ov >= .5 * Math.min(b - a, s1 - s0)) { best = s; bestOv = ov; }
  }
  return best;
}
G.__pending = [];
G.settle = () => { const p = G.__pending; G.__pending = []; return Promise.all(p); };

/** Camera keys [[t, x, y, s], ...]: two keys ease in and out (as the animatic); more keys run through a monotone
 * cubic (Fritsch-Butland tangents, zero at the ends), so the camera eases in, carries its speed through the middle
 * keys instead of stopping at each, never overshoots a key, and eases out. Holds (equal neighbours) stay holds. */
function camAt(cam, t) {
  if (!cam) return null;
  if (typeof cam[0] === 'number') return cam;
  if (cam.length <= 2) return keyframes(t, cam.map(k => [k[0], k.slice(1)]), easeInOutSine);
  const n = cam.length;
  if (t <= cam[0][0]) return cam[0].slice(1);
  if (t >= cam[n - 1][0]) return cam[n - 1].slice(1);
  let i = 0; while (i < n - 2 && t > cam[i + 1][0]) i++;
  const h = cam[i + 1][0] - cam[i][0];
  if (h <= 1e-6) return cam[i + 1].slice(1);
  const u = (t - cam[i][0]) / h, u2 = u * u, u3 = u2 * u;
  const tan = (k, c) => {                                   // tangent of component c at key k (value per second)
    if (k === 0 || k === n - 1) return 0;
    const h0 = cam[k][0] - cam[k - 1][0], h1 = cam[k + 1][0] - cam[k][0];
    if (h0 <= 1e-6 || h1 <= 1e-6) return 0;
    const d0 = (cam[k][c] - cam[k - 1][c]) / h0, d1 = (cam[k + 1][c] - cam[k][c]) / h1;
    if (d0 * d1 <= 0) return 0;
    const w0 = 2 * h1 + h0, w1 = h1 + 2 * h0;
    return (w0 + w1) / (w0 / d0 + w1 / d1);
  };
  const out = [];
  for (let c = 1; c <= 3; c++) {
    const p0 = cam[i][c], p1 = cam[i + 1][c], m0 = tan(i, c) * h, m1 = tan(i + 1, c) * h;
    out.push((2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * m1);
  }
  return out;
}

/** Place an element of natural size (w, h) so source point (x, y) is at the frame centre, zoom s over cover. */
function frameImg(img, w, h, x, y, s, fit) {
  const k0 = fit === 'contain' ? Math.min(W / w, H / h) : Math.max(W / w, H / h);
  const k = k0 * s, vw = w * k, vh = h * k;
  let L = W / 2 - x * k, T = H / 2 - y * k;
  if (vw >= W) L = clamp(L, W - vw, 0); else L = (W - vw) / 2;
  if (vh >= H) T = clamp(T, H - vh, 0); else T = (H - vh) / 2;
  img.style.transform = `translate(${L.toFixed(2)}px,${T.toFixed(2)}px) scale(${k.toFixed(5)})`;
  return { L, T, k };
}

/** One shot: a 1920x1080 box with the picture (img or live iframe) and an overlay layer that moves with it (source px). */
const frames = [];          // every live iframe, for main.js to wait on
function still(parent, key, o = {}) {
  const [w, h] = sizeOf(key);
  const box = el('div', { cls: 'shot' + (o.fit === 'contain' ? ' contain' : '') }, parent);
  let img, live = null;
  if (isLive(key)) {
    const name = key.slice(5);
    live = key.startsWith('comp/') ? { url: `../look/worlds2/comps/${name}.html`, apply: (w, s) => w.COMP.render(s) } : LIVE[name];
    if (!live) throw new Error('no live page ' + key);
    img = el('iframe', { cls: 'live', attrs: { src: live.url, scrolling: 'no', tabindex: '-1' } }, box);
    css(img, { width: w + 'px', height: h + 'px', border: '0', position: 'absolute', left: '0', top: '0', transformOrigin: '0 0', background: '#000' });
    frames.push(img);
  } else {
    img = el('img', { attrs: { src: path(key), width: w, height: h, decoding: 'sync' } }, box);
    css(img, { width: w + 'px', height: h + 'px' });
  }
  const layer = el('div', { cls: 'layer' }, box);
  css(layer, { width: w + 'px', height: h + 'px' });
  let last = null;
  return {
    box, img, layer, key, w, h, live,
    win() { return img.contentWindow; },
    apply(state) {                    // drive a live page; skipped when the state is unchanged (output = f(state))
      const j = JSON.stringify(state);
      if (j === last) return;
      live.apply(img.contentWindow, state); last = j;
    },
    place(t, cam, fit) {
      const c = camAt(cam, t) || [w / 2, h / 2, 1];
      const r = frameImg(img, w, h, c[0], c[1], c[2], fit);
      layer.style.transform = img.style.transform;
      return r;
    },
  };
}

/** A run of shots on one clock. Each shot is fully opaque until the next shot has finished fading in.
 * The finish (SHOTLIST section 3): hard cuts; a shot's fi is honoured only where dissolves belong (o.dissolves: scene
 * 9 and the titles), for the short crossfade of a push into the screen (pin), or an item's own keepFi. Room shots
 * (world stills and Blender sequences) get the fine grain and the soft vignette; screens and worlds stay clean. */
function seq(root, items, end, o = {}) {
  const list = items.map(it => ({ ...it, s: still(root, it.src, it) }));
  list.forEach(it => {
    if (!o.dissolves && !it.keepFi && !it.pin) it.fi = 0;
    if (it.pin) { it.quad = quadOf(it.pin.shot); if (!it.quad) it.fi = 0; }
  });
  list.forEach((it, i) => {
    const nx = list[i + 1];
    it.end = it.until != null ? it.until : nx ? nx.at + Math.max(nx.fi || 0, nx.quad ? nx.pin.d || .6 : 0, nx.open ? nx.open.d || .55 : 0) : end;
    it.bl = blenderFor(it.src, it.at, it.end);
    if (it.bl) { it.blDir = `../world/out/anim/${it.bl.id}/`; it.blN = -1; }
    if (isRoom(it.src) && !it.clean) it.finish = finish(it.s.box);
    if (it.open) {                                     // his mark, at the heart of the opening
      it.openMark = el('div', { html: markSVG('#D3A14A') }, it.s.box);
      css(it.openMark, { position: 'absolute', width: '132px', height: '132px', left: (it.open.x - 66) + 'px', top: (it.open.y - 74) + 'px', zIndex: 60, pointerEvents: 'none',
        filter: 'drop-shadow(0 0 18px rgba(211,161,74,.55))' });
    }
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
        let g = typeof it.grade === 'function' ? it.grade(t) : (it.grade || '');
        if (it.bl) {                                     // the Blender sequence: its own camera and light
          const n = clamp(Math.floor((t - it.bl.start) * FILM_FPS) + 1, 1, it.bl.frames);
          if (n !== it.blN) {
            it.blN = n; it.s.img.src = it.blDir + String(n).padStart(4, '0') + '.jpg';
            G.__pending.push(it.s.img.decode().catch(() => { G.__errors && G.__errors.push('[blender] missing ' + it.s.img.src); }));
          }
          it.s.place(t, null, it.fit);
          if (!it.keepGrade) g = '';
        } else if (it.quad && t < it.at + (it.pin.d || .6)) {          // the push into the screen: pinned, growing
          const u = easeInOutCubic(clamp((t - it.at) / (it.pin.d || .6))), F = [[0, 0], [W, 0], [W, H], [0, H]];
          const q = it.quad.map((p, k) => [lerp(p[0], F[k][0], u), lerp(p[1], F[k][1], u)]);
          it.s.img.style.transform = it.s.layer.style.transform = pinMatrix(q, it.s.w, it.s.h);
        } else it.s.place(t, typeof it.cam === 'function' ? it.cam(t, it) : it.cam, it.fit);
        if (it.finish) it.finish(t);
        if (it.open) {                                   // Barnaby's window opening out of the screen
          const d = it.open.d || .55, u = clamp((t - it.at) / d);
          if (u < 1) {
            const R = 2300 * easeInOutCubic(u) + 40 * (1 - u);
            it.s.box.style.clipPath = `circle(${R.toFixed(1)}px at ${it.open.x}px ${it.open.y}px)`;
          } else if (it.s.box.style.clipPath) it.s.box.style.clipPath = '';
          const mk = clamp(1 - (t - it.at) / (d * .9));
          it.openMark.style.display = mk > .01 ? 'block' : 'none';
          it.openMark.style.opacity = mk.toFixed(3);
          it.openMark.style.transform = `scale(${(1 + .35 * (1 - mk)).toFixed(3)})`;
        }
        const b = typeof it.blur === 'function' ? it.blur(t) : (it.blur || 0);
        const f = (g + (b > .05 ? ` blur(${b.toFixed(2)}px)` : '')).trim();
        it.s.img.style.filter = f || 'none';
        if (it.state && it.s.live) it.s.apply(it.state(t, t - it.at));
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

/** The 2009 arrow cursor (the shop PC's own, os.js), as an overlay in a shot's layer; `scale` = source px per logical
 * px (1.5 on the 1920x1080 look-dev frames). cursorAt(t, keys) -> [x, y] from [[t, x, y], ...] keyframes. */
function cursor(layer, scale = 1.5) {
  const c = el('div', { html: '<svg width="20" height="28" viewBox="0 0 20 28" style="display:block;overflow:visible"><path d="M1.5 1.5 L1.5 21.5 L6.2 17 L9.4 24.8 L12.6 23.4 L9.5 15.9 L15.8 15.9Z" fill="#fff" stroke="#000" stroke-width="1.1" stroke-linejoin="round"/></svg>' }, layer);
  css(c, { position: 'absolute', left: '0', top: '0', width: '20px', height: '28px', transformOrigin: '0 0', zIndex: 50, filter: 'drop-shadow(1px 2px 1.5px rgba(0,0,0,.35))' });
  return {
    el: c,
    at(x, y, show = true) {
      c.style.display = show ? 'block' : 'none';
      c.style.transform = `translate(${(x - 1.5 * scale).toFixed(1)}px,${(y - 1.5 * scale).toFixed(1)}px) scale(${scale})`;
    },
  };
}
/** Cursor path: keys [[t, x, y], ...], eased between keys (a hand moving a mouse: ease in-out). */
function path2(t, keys) { return keyframes(t, keys.map(k => [k[0], [k[1], k[2]]]), easeInOutCubic); }
/** A click flash: 1 at a click, decaying over d. */
const clickK = (t, at, d = .14) => (t >= at && t < at + d ? 1 - (t - at) / d : 0);

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

/** Keep on-screen text in a still hidden until it is said (the animatic's reveal; used where a still remains). */
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

/* ---- the push into the screen: a corner pin onto the monitor's glass (shots.json screen_quad) ---------------- */
function quadOf(id) {
  const m = blenderManifest(); if (!m || !m.shots) return null;
  const sh = m.shots.find(x => x.id === id);
  if (!sh || sh.status !== 'done') return null;
  let q = sh.screen_quad || (sh.screen && sh.screen.quad);
  if (!q) return null;
  if (!Array.isArray(q)) q = [q.tl, q.tr, q.br, q.bl];
  if (q.length !== 4 || q.some(p => !Array.isArray(p) || p.length < 2)) return null;
  const norm = q.every(p => Math.abs(p[0]) <= 1.5 && Math.abs(p[1]) <= 1.5);
  return q.map(p => norm ? [p[0] * W, p[1] * H] : [+p[0], +p[1]]);
}
/** CSS matrix3d taking a w x h box onto the quad [TL, TR, BR, BL] (a projective map, Heckbert's square-to-quad). */
function pinMatrix(q, w, h) {
  const [[x0, y0], [x1, y1], [x2, y2], [x3, y3]] = q;
  const dx1 = x1 - x2, dx2 = x3 - x2, dx3 = x0 - x1 + x2 - x3, dy1 = y1 - y2, dy2 = y3 - y2, dy3 = y0 - y1 + y2 - y3;
  const den = dx1 * dy2 - dx2 * dy1 || 1e-9;
  const g = (dx3 * dy2 - dx2 * dy3) / den, hh = (dx1 * dy3 - dx3 * dy1) / den;
  const a = x1 - x0 + g * x1, b = x3 - x0 + hh * x3, c = x0, d = y1 - y0 + g * y1, e = y3 - y0 + hh * y3, f = y0;
  const m = [a / w, d / w, 0, g / w, b / h, e / h, 0, hh / h, 0, 0, 1, 0, c, f, 0, 1];
  return `matrix3d(${m.map(v => +v.toFixed(8)).join(',')})`;
}

/* ---- the room finish: fine deterministic grain (about 2/255, a new pattern each frame) and a soft vignette --- */
const GRAIN = [];
function grainTiles() {
  if (GRAIN.length) return GRAIN;
  for (let k = 0; k < 6; k++) {
    const c = document.createElement('canvas'); c.width = c.height = 256;
    const x = c.getContext('2d'), im = x.createImageData(256, 256), r = seeded(9001 + k);
    for (let i = 0; i < im.data.length; i += 4) { const v = r() < .5 ? 0 : 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = Math.round(r() * 5); }
    x.putImageData(im, 0, 0); GRAIN.push(c.toDataURL('image/png'));
  }
  return GRAIN;
}
function finish(box) {
  const tiles = grainTiles();
  const vig = el('div', {}, box), gr = el('div', {}, box);
  css(vig, { position: 'absolute', left: '0', top: '0', width: W + 'px', height: H + 'px', zIndex: 40, pointerEvents: 'none',
    background: 'radial-gradient(ellipse 75% 75% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,.12) 100%)' });
  css(gr, { position: 'absolute', left: '0', top: '0', width: W + 'px', height: H + 'px', zIndex: 41, pointerEvents: 'none' });
  let last = null;
  return t => {
    const f = Math.floor(t * FILM_FPS + 1e-6);
    if (f === last) return; last = f;
    gr.style.backgroundImage = `url(${tiles[((f % tiles.length) + tiles.length) % tiles.length]})`;
    gr.style.backgroundPosition = `${Math.floor(rand(f, 31) * 256)}px ${Math.floor(rand(f, 32) * 256)}px`;
  };
}

/* ---- the director's camera rules (gate 4 notes): hold by default, motivated moves only, human-speed hands ---- */
/** A held shot: (x, y, s) with at most an imperceptible drift over the whole shot (scale +k, default 1.2%). */
const hold = (x, y, s = 1, k = .012) => (t, it) => { const u = easeInOutSine(clamp((t - it.at) / Math.max(.1, it.end - it.at))); return [x, y, s * (1 + k * u)]; };
/** One motivated move: holds `from` (with the drift) until a, eases to `to` over d, then holds `to`. */
const move = (a, d, from, to, k = .006) => (t, it) => {
  if (t < a) { const u = easeInOutSine(clamp((t - it.at) / Math.max(.1, a - it.at))); return [from[0], from[1], from[2] * (1 + k * u)]; }
  const u = easeInOutCubic(clamp((t - a) / d)), f = [from[0], from[1], from[2] * (1 + k)];
  return [lerp(f[0], to[0], u), lerp(f[1], to[1], u), lerp(f[2], to[2], u)];
};
/** The cue sheet's sound events: the time of the `type` event nearest to `near` (e.g. a mouse_click by its mark). */
function sfxT(type, near) {
  let best = null;
  for (const e of CUES.sfx || []) if (e.type === type && (best == null || Math.abs(e.t - near) < Math.abs(best.t - near))) best = e;
  return best ? best.t : near;
}
const sfxAll = (type, a = -1e9, b = 1e9) => (CUES.sfx || []).filter(e => e.type === type && e.t >= a && e.t < b).map(e => e.t);
/** A hand on a mouse: from rest [t, x, y], to each click {t, x, y} (the press is at t): it travels 0.6-1.0 s
 * (longer for longer trips), arrives and settles 150 ms before the press, holds 120 ms down, and leaves no sooner
 * than 120 ms after; with less room than that the trip is shortened. Ends at `after` [t, x, y] if given. */
function hand(t, rest, clicks, after) {
  const keys = [[rest[0], rest[1], rest[2]]];
  let px = rest[1], py = rest[2], free = rest[0];
  for (const c of clicks) {
    const dist = Math.hypot(c.x - px, c.y - py), travel = clamp(.6 + dist / 1800, .6, 1.0);
    const arrive = c.t - .15, leave = Math.max(free, arrive - travel);
    if (leave > keys[keys.length - 1][0] + 1e-3) keys.push([leave, px, py]);
    keys.push([Math.max(arrive, leave + .08), c.x, c.y], [c.t + .12, c.x, c.y]);
    px = c.x; py = c.y; free = c.t + .24;
  }
  if (after) { keys.push([Math.max(free, after[0] - 1.0), px, py], [Math.max(free + .6, after[0]), after[1], after[2]]); }
  keys.sort((a, b) => a[0] - b[0]);
  return keyframes(t, keys.map(k => [k[0], [k[1], k[2]]]), easeInOutCubic);
}
/** The button under a click: down for 120 ms from the press. */
const pressAt = (t, at) => (t >= at && t < at + .12 ? 1 : t >= at - .02 && t < at ? (t - at + .02) / .02 : 0);

/** Typed text: the first n characters of s at time t, typing from a to b (deterministic, slightly uneven rhythm). */
function typed(s, t, a, b) {
  const u = clamp((t - a) / (b - a)); if (u <= 0) return ''; if (u >= 1) return s;
  let acc = 0; const w = [...s].map((c, i) => (acc += .6 + .8 * rand(i, 77)));
  const n = w.findIndex(x => x / acc > u); return s.slice(0, n < 0 ? s.length : n);
}

Object.assign(G, { SRC, SIZE, V, VE, M, still, seq, frameImg, label, fadeEl, markSVG, markAnim, sizeOf, imgPath: path, reveal, sweep,
  cursor, path2, clickK, typed, LIVE_FRAMES: frames, FILM_FPS, hold, move, sfxT, sfxAll, hand, pressAt, pick, quadOf });
})(window);
