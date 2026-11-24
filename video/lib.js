/* =====================================================================
 * Barnaby film: lib.js. Adapted from Quorum's v3 motion framework (ImTani/quorum-edge-memory, video/lib.js).
 * Kept: timing/easing, deterministic randomness, colour, DOM + text helpers, captions, canvas glow, wordmark,
 * scene registry. Removed: the 3D cloud engine, laptop and network-graph components (Barnaby's own components
 * live in components.js).
 * RULE: every visual must be a PURE FUNCTION OF t. No Date.now(), no CSS transitions/animations, no rAF.
 * ===================================================================== */
(function (G) {
'use strict';
const W = 1920, H = 1080, FPS = 30;
const COL = {
  brass: '#D4A85A', brassDeep: '#B88A3E', brassLt: '#F0CF8F',
  ink: '#F1ECE1', sub: '#C2BBA9', muted: '#8D8778', bg: '#0E1117', card: '#161A22', card2: '#1B202A', hair: '#262B35',
  read: '#3987E5', write: '#D95926', grow: '#D4A85A', build: '#9085E9', good: '#22C55E', bad: '#E66767', warn: '#FAB219',
  xpBlue: '#0A4FC4', xpBanner: '#1D4A77', xpYellow: '#FFCC00', xpGrey: '#D4D0C8', xpBeige: '#ECE9D8',
  indigo: '#9085E9',
};
const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
const lerp = (a, b, k) => a + (b - a) * k;
const invLerp = (a, b, x) => clamp((x - a) / (b - a));
const remap = (x, a0, a1, b0, b1) => lerp(b0, b1, invLerp(a0, a1, x));
const lerp3 = (a, b, k) => [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
/** P(t,a,d): linear clamped progress 0..1 of the window [a, a+d]. */
const P = (t, a, d = 0.6) => (d <= 0 ? (t >= a ? 1 : 0) : clamp((t - a) / d));

/* -------------------------------------------------------------- easing */
const linear = x => x;
const easeOutExpo = x => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
const easeInExpo = x => (x <= 0 ? 0 : Math.pow(2, 10 * x - 10));
const easeInOutExpo = x => x <= 0 ? 0 : x >= 1 ? 1 : x < .5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2;
const easeOutCubic = x => 1 - Math.pow(1 - x, 3);
const easeInCubic = x => x * x * x;
const easeInOutCubic = x => (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const easeInOutSine = x => -(Math.cos(Math.PI * x) - 1) / 2;
const easeOutQuart = x => 1 - Math.pow(1 - x, 4);
const easeOutBack = (x, s = 1.70158) => { const c = s + 1; return 1 + c * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2); };
/** spring(x): damped spring 0 -> 1 with overshoot. x is progress 0..1. */
const spring = (x, damping = 6.5, freq = 2.1) => x <= 0 ? 0 : x >= 1 ? 1 :
  1 - Math.exp(-damping * x) * Math.cos(freq * 2 * Math.PI * x) * (1 - x * x * x);
/** E(t,a,d,ease): eased progress. Default ease = easeOutExpo. */
const E = (t, a, d = 0.6, ease = easeOutExpo) => ease(P(t, a, d));
/** pulse(t,t0,w): gaussian bump, 1 at t0, width w seconds. */
const pulse = (t, t0, w = 0.15) => Math.exp(-Math.pow((t - t0) / w, 2));
/** win(t,a,b,fi,fo): 0 -> 1 at a (over fi), 1 -> 0 ending at b (over fo). */
const win = (t, a, b, fi = .5, fo = .5) => Math.min(easeOutCubic(P(t, a, fi)), 1 - easeInCubic(P(t, b - fo, fo)));
/** blink(t, rate): square blink 0/1, deterministic. */
const blink = (t, rate = 2) => (Math.floor(t * rate * 2) % 2 === 0 ? 1 : 0);
/** keyframes(t, [[t0,v0],[t1,v1],...], ease): piecewise interpolation of numbers or arrays. */
function keyframes(t, keys, ease = easeInOutCubic) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    if (t <= keys[i][0]) {
      const [ta, va] = keys[i - 1], [tb, vb] = keys[i]; const k = ease((t - ta) / (tb - ta));
      return mixAny(va, vb, k);
    }
  }
  return keys[keys.length - 1][1];
}
function mixAny(a, b, k) {
  if (typeof a === 'number') return lerp(a, b, k);
  if (Array.isArray(a)) return a.map((v, i) => mixAny(v, b[i], k));
  if (a && typeof a === 'object') { const o = {}; for (const key in a) o[key] = key in b ? mixAny(a[key], b[key], k) : a[key]; for (const key in b) if (!(key in a)) o[key] = b[key]; return o; }
  return k < .5 ? a : b;
}

/* -------------------------------------------------------- deterministic rand */
/** rand(i, salt): hash -> [0,1). Same inputs, same output, always. */
function rand(i, salt = 0) {
  let h = (Math.imul(i | 0, 374761393) + Math.imul(salt | 0, 668265263) + 0x9E3779B9) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177); h ^= h >>> 16; h = Math.imul(h, 2246822519); h ^= h >>> 13;
  return (h >>> 0) / 4294967296;
}
/** randn(i, salt): gaussian (mean 0, sd 1). */
function randn(i, salt = 0) { const u = Math.max(1e-9, rand(i, salt)), v = rand(i, salt + 7919); return Math.sqrt(-2 * Math.log(u)) * Math.cos(6.283185307 * v); }
/** seeded(seed): returns a generator () => [0,1) (mulberry32). Create it in build(), not per frame. */
function seeded(seed) { let a = seed >>> 0; return function () { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
/** wiggle(t, seed, freq, amp): smooth deterministic noise in [-amp, amp]. */
function wiggle(t, seed = 0, freq = 1, amp = 1) {
  const a = rand(seed, 1) * 6.283, b = rand(seed, 2) * 6.283;
  return amp * (0.6 * Math.sin(t * freq * 1.0 + a) + 0.4 * Math.sin(t * freq * 2.31 + b));
}

/* ---------------------------------------------------------------- colour */
function hexToRgb(c) {
  if (Array.isArray(c)) return c;
  if (c[0] === '#') { let s = c.slice(1); if (s.length === 3) s = s.split('').map(x => x + x).join(''); const n = parseInt(s, 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  const m = c.match(/[\d.]+/g); return m ? [+m[0], +m[1], +m[2]] : [255, 255, 255];
}
const rgbToHex = ([r, g, b]) => '#' + [r, g, b].map(v => Math.round(clamp(v, 0, 255)).toString(16).padStart(2, '0')).join('');
/** mixColor(a, b, k): hex blend. */
const mixColor = (a, b, k) => { const A = hexToRgb(a), B = hexToRgb(b); return rgbToHex([lerp(A[0], B[0], k), lerp(A[1], B[1], k), lerp(A[2], B[2], k)]); };
/** rgba(hex, alpha) -> css string */
const rgba = (c, a) => { const [r, g, b] = hexToRgb(c); return `rgba(${r},${g},${b},${a})`; };

/* ------------------------------------------------------------------- DOM */
const $ = (sel, root = document) => (typeof sel === 'string' ? root.querySelector(sel) : sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
/** el(tag, {cls, style, html, text, attrs}, parent): create an element. style may be a string or object. */
function el(tag = 'div', props = {}, parent = null) {
  const e = document.createElement(tag);
  if (props.cls) e.className = props.cls;
  if (props.style) { if (typeof props.style === 'string') e.style.cssText = props.style; else Object.assign(e.style, props.style); }
  if (props.html != null) e.innerHTML = props.html;
  if (props.text != null) e.textContent = props.text;
  if (props.attrs) for (const k in props.attrs) e.setAttribute(k, props.attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
/** h(html, parent): build DOM from an HTML string, returns the first element. */
function h(html, parent = null) { const d = document.createElement('div'); d.innerHTML = html.trim(); const e = d.firstElementChild; if (parent) parent.appendChild(e); return e; }
const css = (e, obj) => (Object.assign(e.style, obj), e);
/** setHTML / setText: only touches the DOM when the value changes (fast, still deterministic). */
function setHTML(e, s) { if (e.__html !== s) { e.innerHTML = s; e.__html = s; e.__text = undefined; } }
function setText(e, s) { if (e.__text !== s) { e.textContent = s; e.__text = s; e.__html = undefined; } }
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
/** xf(el, {x, y, s, sx, sy, r, rx, ry, o, blur, persp}): set transform (+opacity) in one call. */
function xf(e, o = {}) {
  const p = [];
  if (o.persp) p.push(`perspective(${o.persp}px)`);
  if (o.x || o.y) p.push(`translate(${o.x || 0}px,${o.y || 0}px)`);
  if (o.rx) p.push(`rotateX(${o.rx}deg)`);
  if (o.ry) p.push(`rotateY(${o.ry}deg)`);
  if (o.r) p.push(`rotate(${o.r}deg)`);
  if (o.s != null && o.s !== 1) p.push(`scale(${o.s})`);
  if (o.sx != null || o.sy != null) p.push(`scale(${o.sx ?? 1},${o.sy ?? 1})`);
  e.style.transform = p.join(' ');
  if (o.o != null) e.style.opacity = clamp(o.o);
  if (o.blur != null) e.style.filter = o.blur > 0.05 ? `blur(${o.blur}px)` : 'none';
  return e;
}

/* ------------------------------------------------------------------ text */
/**
 * show(el, t, a, d=.6, {dy=24, dx=0, scale=1, ease=easeOutExpo, blur=0, out=null, outD=.4, outDy=0})
 * Entrance at time a over d seconds (opacity 0->1, slides from dy/dx, scales from `scale`).
 * Optional exit: `out` = time the exit starts. Returns the visible amount 0..1.
 */
function show(e, t, a, d = .6, o = {}) {
  const { dy = 24, dx = 0, scale = 1, ease = easeOutExpo, blur = 0, out = null, outD = .4, outDy = 0 } = o;
  const k = ease(P(t, a, d)); const kc = clamp(k);
  let ko = 0; if (out != null) ko = easeInOutCubic(P(t, out, outD));
  e.style.opacity = clamp(Math.min(kc * 1.15, 1) * (1 - ko));
  const s = lerp(scale, 1, k);
  e.style.transform = `translate(${(1 - k) * dx}px,${(1 - k) * dy - ko * outDy}px)` + (s !== 1 ? ` scale(${s})` : '');
  if (blur) e.style.filter = (1 - kc) * blur > .05 ? `blur(${(1 - kc) * blur}px)` : 'none';
  return kc * (1 - ko);
}
/** pop(el, t, a, d=.7): spring scale-in pop (0.6 -> 1 with overshoot). */
function pop(e, t, a, d = .7, from = .6) {
  const k = spring(P(t, a, d)); e.style.opacity = clamp(P(t, a, d * .3));
  e.style.transform = `scale(${lerp(from, 1, k)})`; return clamp(k);
}
/** hideAfter(el, t, a, d=.4): multiplies current opacity by an exit fade. Call AFTER show(). */
function hideAfter(e, t, a, d = .4) {
  const k = 1 - easeInOutCubic(P(t, a, d)); const cur = e.style.opacity === '' ? 1 : +e.style.opacity;
  e.style.opacity = cur * k; return k;
}
/**
 * typeText(el, str, t, start, cps=28, {cursor=true, cursorColor, hold=1.2, color})
 * Types str from `start` at cps chars/sec. Cursor blinks while typing and for `hold` s after.
 * Returns progress 0..1. Content is plain text (escaped).
 */
function typeText(e, str, t, start, cps = 28, o = {}) {
  const { cursor = true, cursorColor = COL.indigo, hold = 1.2 } = o;
  const n = Math.floor(clamp((t - start) * cps, 0, str.length));
  const end = start + str.length / cps;
  const cur = cursor && t >= start - .3 && t < end + hold && (t < end || blink(t, 1.6));
  setHTML(e, esc(str.slice(0, n)) + (cur ? `<span style="color:${cursorColor};font-weight:400;margin-left:1px">▍</span>` : ''));
  return str.length ? n / str.length : 1;
}
/** staggerIn(els, t, start, gap=.08, showOpts): show() each element with a stagger. Returns array of k. */
function staggerIn(els, t, start, gap = .08, o = {}) { return Array.from(els).map((e, i) => show(e, t, start + i * gap, o.d ?? .6, o)); }
/** splitWords(el): wraps each word of el's text into inline-block spans; returns the spans. (build() only) */
function splitWords(e) {
  const words = e.innerHTML.split(/(\s+)/); e.innerHTML = '';
  const out = [];
  for (const w of words) { if (/^\s+$/.test(w)) { e.appendChild(document.createTextNode(' ')); continue; } if (!w) continue; const s = el('span', { html: w, style: 'display:inline-block' }, e); out.push(s); }
  return out;
}
/** countUp(t, a, d, from, to, ease): number tween. */
const countUp = (t, a, d, from, to, ease = easeOutCubic) => lerp(from, to, ease(P(t, a, d)));
/** fmtTime(sec): "2:58:41" */
const fmtTime = s => { s = Math.floor(s); const hh = Math.floor(s / 3600), mm = Math.floor(s / 60) % 60, ss = s % 60; return `${hh}:${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`; };

/* ------------------------------------------------------------ components */
function chip(html, color = COL.indigo, parent = null, style = '') {
  return el('span', { cls: 'chip', html, style: `color:${color};background:${rgba(color, .12)};border-color:${rgba(color, .45)};${style}` }, parent);
}

/* --------------------------------------------------------------- captions */
const _cap = { list: [] };
/**
 * caption(text, t, start, end, {html=false}): shows a bottom caption (42px semibold, dark backing,
 * y≈958) with 0.45s fade-in and 0.4s fade-out. Call from a scene's render() every frame, or list
 * it in Scene({captions:[[start,end,text], ...]}). The strongest caption of the frame wins.
 */
function caption(text, t, start, end, o = {}) {
  if (t < start || t > end) return 0;
  const a = Math.min(easeOutCubic(P(t, start, .45)), 1 - easeInCubic(P(t, end - .4, .4)));
  if (a > 0) _cap.list.push({ text, a, o, rise: 1 - easeOutExpo(P(t, start, .6)) });
  return a;
}

/* ---------------------------------------------------------- glow sprites */
const _sprites = new Map();
function _q(c) { const [r, g, b] = hexToRgb(c); return [r & ~7, g & ~7, b & ~7]; }
/** glowSprite(color): cached 128px radial halo canvas (for drawImage with 'lighter'). */
function glowSprite(color) {
  const q = _q(color), key = 'g' + q.join(',');
  let s = _sprites.get(key); if (s) return s;
  s = document.createElement('canvas'); s.width = s.height = 128; const c = s.getContext('2d');
  const g = c.createRadialGradient(64, 64, 0, 64, 64, 64); const [r, gg, b] = q;
  g.addColorStop(0, `rgba(${r},${gg},${b},1)`); g.addColorStop(.12, `rgba(${r},${gg},${b},.62)`);
  g.addColorStop(.32, `rgba(${r},${gg},${b},.2)`); g.addColorStop(.62, `rgba(${r},${gg},${b},.05)`); g.addColorStop(1, `rgba(${r},${gg},${b},0)`);
  c.fillStyle = g; c.fillRect(0, 0, 128, 128); _sprites.set(key, s); return s;
}
/** coreSprite(color): cached 32px bright core (white-hot centre tinted by color). */
function coreSprite(color) {
  const q = _q(color), key = 'c' + q.join(',');
  let s = _sprites.get(key); if (s) return s;
  s = document.createElement('canvas'); s.width = s.height = 32; const c = s.getContext('2d');
  const hot = hexToRgb(mixColor(rgbToHex(q), '#ffffff', .75)); const [r, gg, b] = q;
  const g = c.createRadialGradient(16, 16, 0, 16, 16, 16);
  g.addColorStop(0, `rgba(${hot[0]},${hot[1]},${hot[2]},1)`); g.addColorStop(.35, `rgba(${r},${gg},${b},.95)`);
  g.addColorStop(.7, `rgba(${r},${gg},${b},.25)`); g.addColorStop(1, `rgba(${r},${gg},${b},0)`);
  c.fillStyle = g; c.fillRect(0, 0, 32, 32); _sprites.set(key, s); return s;
}
/** drawGlow(ctx, x, y, r, color, alpha, core=true): additive glowing dot, halo radius r (px). */
function drawGlow(ctx, x, y, r, color, alpha = 1, core = true) {
  if (alpha <= .003 || r <= 0) return;
  const prev = ctx.globalCompositeOperation; ctx.globalCompositeOperation = 'lighter';
  ctx.globalAlpha = clamp(alpha); const s = glowSprite(color); ctx.drawImage(s, x - r, y - r, 2 * r, 2 * r);
  if (core) { const cr = Math.max(1.2, r * .28); ctx.drawImage(coreSprite(color), x - cr, y - cr, 2 * cr, 2 * cr); }
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = prev;
}
/** glowLine(ctx, x1,y1,x2,y2, color, alpha, width): additive glowing beam. */
function glowLine(ctx, x1, y1, x2, y2, color, alpha = 1, width = 3) {
  if (alpha <= .003) return;
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
  for (const [wm, am] of [[6, .08], [3, .18], [1.6, .45], [.6, 1]]) {
    ctx.globalAlpha = clamp(alpha * am); ctx.strokeStyle = wm < 1 ? mixColor(color, '#ffffff', .6) : color; ctx.lineWidth = width * wm;
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  }
  ctx.restore();
}
function roundRect(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }

const FONT = '"Segoe UI Variable Display","Segoe UI",sans-serif';
function makeWordmark(o = {}) {
  const { text = 'BARNABY', size = 200, weight = 800, spacing = 40, cx = 960, baseY = 470 } = o;
  const font = `${weight} ${size}px ${FONT}`;
  const m = document.createElement('canvas').getContext('2d'); m.font = font;
  const widths = [...text].map(ch => m.measureText(ch).width);
  const total = widths.reduce((a, b) => a + b, 0) + spacing * (text.length - 1);
  const xs = []; let x = cx - total / 2; for (const w of widths) { xs.push(x); x += w + spacing; }
  const pad = 80, bx = Math.floor(cx - total / 2 - pad), by = Math.floor(baseY - size * 1.0 - pad), bw = Math.ceil(total + pad * 2), bh = Math.ceil(size * 1.3 + pad * 2);
  const mk = () => { const c = document.createElement('canvas'); c.width = bw; c.height = bh; return c; };
  const txt = mk(), tc = txt.getContext('2d'); tc.font = font; tc.fillStyle = '#fff';
  [...text].forEach((ch, i) => tc.fillText(ch, xs[i] - bx, baseY - by));
  const glow = mk(), gc = glow.getContext('2d'); gc.filter = 'blur(26px)'; gc.globalAlpha = .9; gc.drawImage(txt, 0, 0);
  const tinted = mk(), tic = tinted.getContext('2d'); tic.drawImage(glow, 0, 0); tic.globalCompositeOperation = 'source-in'; tic.fillStyle = COL.indigo; tic.fillRect(0, 0, bw, bh);
  const cool = mk(), cc = cool.getContext('2d'); cc.drawImage(txt, 0, 0); cc.globalCompositeOperation = 'source-in'; cc.fillStyle = '#AEB8EC'; cc.fillRect(0, 0, bw, bh);
  const sweep = mk(), sc = sweep.getContext('2d');
  return {
    bbox: { x: bx + pad, y: by + pad, w: total, h: size * 1.3 }, xs, widths, font,
    samples(step = 5) {
      const d = tc.getImageData(0, 0, bw, bh).data; const out = [];
      for (let yy = 0; yy < bh; yy += step) for (let xx = 0; xx < bw; xx += step) {
        const jx = ((yy / step) % 2) * step / 2; const X = Math.floor(xx + jx);
        if (X < bw && d[(yy * bw + X) * 4 + 3] > 140) out.push([X + bx, yy + by]);
      }
      return out;
    },
    draw(ctx, alpha = 1, sweepK = -1, glowAmt = 1) {
      if (alpha <= .003) return;
      const sweeping = sweepK > 0 && sweepK < 1;
      // env: letters cool down slightly while the specular band passes, so the white highlight reads
      const env = sweeping ? Math.min(1, sweepK / .15, (1 - sweepK) / .15) : 0;
      ctx.save();
      ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = clamp(alpha * .55 * glowAmt); ctx.drawImage(tinted, bx, by);
      ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = clamp(alpha); ctx.drawImage(txt, bx, by);
      if (sweeping) {
        ctx.globalAlpha = clamp(alpha * env * .85); ctx.drawImage(cool, bx, by);
        // diagonal specular band (~120px), leaning ~22deg, clipped to the letterforms (+ a soft edge bloom)
        const cx0 = lerp(pad - 170, bw - pad + 170, sweepK), cy0 = bh / 2, ang = -.38;
        const nx = Math.cos(ang), ny = Math.sin(ang);
        const band = (half, stops) => { const g = sc.createLinearGradient(cx0 - nx * half, cy0 - ny * half, cx0 + nx * half, cy0 + ny * half); for (const [o, c] of stops) g.addColorStop(o, c); return g; };
        sc.globalCompositeOperation = 'source-over'; sc.clearRect(0, 0, bw, bh); sc.drawImage(txt, 0, 0);
        sc.globalCompositeOperation = 'source-in';
        sc.fillStyle = band(60, [[0, 'rgba(190,200,255,0)'], [.3, 'rgba(210,218,255,.55)'], [.5, 'rgba(255,255,255,1)'], [.7, 'rgba(210,218,255,.55)'], [1, 'rgba(190,200,255,0)']]);
        sc.fillRect(0, 0, bw, bh);
        ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = clamp(alpha); ctx.drawImage(sweep, bx, by); ctx.drawImage(sweep, bx, by);
        // soft bloom of the same band on the blurred glow (spills just outside the letter edges)
        sc.globalCompositeOperation = 'source-over'; sc.clearRect(0, 0, bw, bh); sc.drawImage(glow, 0, 0);
        sc.globalCompositeOperation = 'source-in';
        sc.fillStyle = band(90, [[0, 'rgba(157,169,255,0)'], [.5, 'rgba(235,240,255,1)'], [1, 'rgba(157,169,255,0)']]);
        sc.fillRect(0, 0, bw, bh);
        ctx.globalAlpha = clamp(alpha * .8 * env); ctx.drawImage(sweep, bx, by);
      }
      ctx.restore();
    }
  };
}

/* ----------------------------------------------------------- scene registry */
const SCENES = [];
/**
 * Scene({id, start, end, fadeIn=.5, fadeOut=.5, drift=.03, z, captions:[[a,b,text]], build(root), render(t, lt, fade)})
 * build() runs once at load and creates DOM inside `root` (a 1920x1080 absolutely-positioned div).
 * render() runs every frame while the scene is visible: t in (start - fadeIn/2, end + fadeOut/2).
 * The framework owns root.style.opacity and root.style.transform (crossfade + slow 1.00 -> 1+drift zoom).
 */
function Scene(def) {
  const s = Object.assign({ fadeIn: .5, fadeOut: .5, drift: .03, captions: [], build: () => { }, render: () => { } }, def);
  s.z = s.z ?? SCENES.length;
  SCENES.push(s); return s;
}

/* ------------------------------------------------------------------ export */
Object.assign(G, {
  W, H, FPS, COL, FONT,
  clamp, lerp, invLerp, remap, lerp3, P, E, pulse, win, blink, keyframes, mixAny,
  linear, easeOutExpo, easeInExpo, easeInOutExpo, easeOutCubic, easeInCubic, easeInOutCubic, easeInOutSine, easeOutQuart, easeOutBack, spring,
  rand, randn, seeded, wiggle,
  hexToRgb, rgbToHex, mixColor, rgba,
  $, $$, el, h, css, setHTML, setText, esc, xf,
  show, pop, hideAfter, typeText, staggerIn, splitWords, countUp, fmtTime,
  chip, caption, _cap,
  glowSprite, coreSprite, drawGlow, glowLine, roundRect,
  makeWordmark, Scene, SCENES,
});
})(window);
