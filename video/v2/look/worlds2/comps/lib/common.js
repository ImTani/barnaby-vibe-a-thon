/* Shared by every worlds2 comp: SVG builders, Barnaby's bell (the real app's i-bell symbol, ui/index.html), the key,
   the warning and the tick, and the type stacks. Pure functions of their inputs. */
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs || {}) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function svg(container, w, h) { const s = el('svg', { width: w, height: h, viewBox: `0 0 ${w} ${h}` }); container.appendChild(s); return s; }
  function text(parent, x, y, str, attrs) { const t = el('text', Object.assign({ x, y }, attrs || {}), parent); t.textContent = str; return t; }
  /* multi-line text: lines array, line height */
  function lines(parent, x, y, arr, lh, attrs) { return arr.map((s, i) => text(parent, x, y + i * lh, s, attrs)); }
  /* greedy wrap by measured width (needs the text in the document) */
  function wrap(parent, x, y, str, maxW, lh, attrs) {
    const words = str.split(' '), out = []; let cur = '';
    const probe = text(parent, -9999, -9999, '', attrs);
    for (const w of words) { const t = cur ? cur + ' ' + w : w; probe.textContent = t; if (probe.getComputedTextLength() > maxW && cur) { out.push(cur); cur = w; } else cur = t; }
    if (cur) out.push(cur); probe.remove();
    lines(parent, x, y, out, lh, attrs); return out.length;
  }

  /* Barnaby's bell: the real app's symbol (24x24 box), filled. size = px, centred on (cx, cy). */
  function bell(parent, cx, cy, size, fill) {
    const k = size / 24, g = el('g', { transform: `translate(${cx - size / 2},${cy - size / 2}) scale(${k})`, fill }, parent);
    el('path', { d: 'M4.6 16.4a7.4 7.4 0 0 1 14.8 0z' }, g);
    el('rect', { x: 2.6, y: 17.3, width: 18.8, height: 2.8, rx: 1.3 }, g);
    el('path', { d: 'M12 9.1V6.9', stroke: fill, 'stroke-width': 2, 'stroke-linecap': 'round', fill: 'none' }, g);
    el('circle', { cx: 12, cy: 5.4, r: 1.7 }, g);
    return g;
  }
  /* a key (bow on the left, bit pointing down on the right), drawn in a 24x24 box */
  function key(parent, cx, cy, size, fill, rot = 0) {
    const k = size / 24, g = el('g', { transform: `translate(${cx},${cy}) rotate(${rot}) scale(${k}) translate(-12,-12)` }, parent);
    el('circle', { cx: 7, cy: 12, r: 5.2, fill: 'none', stroke: fill, 'stroke-width': 2.6 }, g);
    el('path', { d: 'M12 12H22.4M18.2 12v3.6M21.2 12v2.8', fill: 'none', stroke: fill, 'stroke-width': 2.6, 'stroke-linecap': 'round' }, g);
    return g;
  }
  function warn(parent, cx, cy, size, fill, mark = '#fff') {
    const k = size / 24, g = el('g', { transform: `translate(${cx - size / 2},${cy - size / 2}) scale(${k})` }, parent);
    el('path', { d: 'M12 2.6 23 21.4H1Z', fill, 'stroke-linejoin': 'round', stroke: fill, 'stroke-width': 1.6 }, g);
    el('path', { d: 'M12 9v5.6', stroke: mark, 'stroke-width': 2.6, 'stroke-linecap': 'round' }, g);
    el('circle', { cx: 12, cy: 18.1, r: 1.5, fill: mark }, g);
    return g;
  }
  function tick(parent, cx, cy, size, stroke, w = 2.6) {
    const k = size / 24, g = el('g', { transform: `translate(${cx - size / 2},${cy - size / 2}) scale(${k})` }, parent);
    el('path', { d: 'M4 12.6 9.4 18 20 6.4', fill: 'none', stroke, 'stroke-width': w, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, g);
    return g;
  }
  function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
  const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  /* Type. Gill Sans MT's "1" reads as a capital I in job numbers and times, so Martin's figures come from Segoe UI
     (the real app's own fix, DESIGN.md). Every face is installed; nothing is downloaded. */
  const css = document.createElement('style');
  css.textContent = `
    @font-face { font-family: "MFig"; src: local("Segoe UI"); unicode-range: U+0030-0039; font-weight: 400; }
    @font-face { font-family: "MFig"; src: local("Segoe UI Semibold"), local("SegoeUI-Semibold"); unicode-range: U+0030-0039; font-weight: 600 900; }`;
  document.head.appendChild(css);
  const FONT = {
    martin: '"MFig", "Gill Sans MT", "Gill Sans", "Segoe UI", sans-serif',
    theo: '"Segoe UI", system-ui, sans-serif', mono: '"Cascadia Code", "Cascadia Mono", Consolas, monospace',
    priya: 'Bahnschrift, "Segoe UI", sans-serif', tag: 'Rockwell, "Rockwell Nova", Georgia, serif',
    martinHand: '"Ink Free", "Segoe Print", cursive', theoHand: '"Segoe Print", cursive',
  };
  window.W2 = { el, svg, text, lines, wrap, bell, key, warn, tick, rng, esc, FONT, NS };
})();
