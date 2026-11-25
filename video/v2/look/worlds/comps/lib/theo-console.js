/* THE ELBOW CONSOLE (Theo, challenger, fused from pop-culture-shelf-elbow-panel-console). Barnaby's form as a
   starship-style wall panel: thick elbows frame the screen (the frame is the layout grid), rooms are colour banks,
   every endpoint a flat pill carrying its method and path, gold only on what is running now. Flat colour on pure
   black: no gradients, no glow. Condensed caps in Bahnschrift (installed), paths keep their real case.
   CONSOLE.* builders take an svg and plain rects; the page composes them. */
(function () {
  const T = window.THEO, W = window.WORLDS;
  const { el, text } = T;
  const BANK = { counter: '#F0A37F', till: '#D97C80', workshop: '#8E9DEB', stockroom: '#BC9BD8', backdoor: '#D9B98C', office: '#A08BC9' };
  const GOLD = '#F7C548', BLACK = '#000', DIM = '#2A2A33';
  const F = "font-family:Bahnschrift;font-variation-settings:'wdth' 75";

  function t(parent, x, y, s, o) {
    return text(parent, x, y, s, Object.assign({ style: F + (o && o.w ? `,'wght' ${o.w}` : ",'wght' 600"), 'font-size': 20, fill: BLACK }, o || {}));
  }
  /* an elbow: a vertical bar of width vw joined to a horizontal arm of height ah. corner: 'tl' (arm on top) or 'bl'
     (arm at the bottom). R outer radius, r inner radius. */
  function elbow(g, { x, y, vw, vh, aw, ah, corner, R = 80, r = 34, fill }) {
    let d;
    if (corner === 'bl') {   // vertical from y down to y+vh; arm along the bottom
      const yb = y + vh;
      d = `M${x},${y} H${x + vw} V${yb - ah - r} A${r},${r} 0 0 0 ${x + vw + r},${yb - ah} H${x + vw + aw} V${yb} H${x + R} A${R},${R} 0 0 1 ${x},${yb - R} Z`;
    } else {                 // 'tl': arm along the top, vertical going down
      d = `M${x + R},${y} H${x + vw + aw} V${y + ah} H${x + vw + r} A${r},${r} 0 0 0 ${x + vw},${y + ah + r} V${y + vh} H${x} V${y + R} A${R},${R} 0 0 1 ${x + R},${y} Z`;
    }
    return el('path', { d, fill }, g);
  }
  /* black gaps cut across a bar make its segments */
  function cut(g, x, y, w, h) { el('rect', { x, y, width: w, height: h, fill: BLACK }, g); }

  /* a pill: solid (open), outline (key), outline struck (shut), dashed (planned), gold (running now). Text is measured,
     so call after document.fonts.ready. Returns the pill's width. */
  function pill(g, x, y, h, label, method, state, col) {
    if (state === 'planned') { label = 'reports page: coming soon (since 2011)'; method = ''; }   // no route exists before the Build
    const rr = h / 2, solid = state === 'lit' || state === 'new' || state === 'gold';
    const c = state === 'gold' ? GOLD : col, tc = solid ? BLACK : c, pg = el('g', {}, g);
    const m = t(pg, x + rr, y + h * .69, method, { 'font-size': h * .46, fill: tc, w: 700, 'letter-spacing': '0.06em' });
    const mw = method ? m.getComputedTextLength() + 12 : 0;
    const l = t(pg, x + rr + mw, y + h * .71, label, { 'font-size': h * .6, fill: tc, w: solid ? 600 : 400 });
    const w = rr + mw + l.getComputedTextLength() + rr;
    const r = el('rect', { x, y, width: w, height: h, rx: rr, fill: solid ? c : BLACK, stroke: solid ? 'none' : c, 'stroke-width': solid ? 0 : 2.2,
      'stroke-dasharray': state === 'planned' ? '7 5' : null });
    pg.insertBefore(r, pg.firstChild);
    if (state === 'shut') el('line', { x1: x + 10, y1: y + h / 2, x2: x + w - 10, y2: y + h / 2, stroke: c, 'stroke-width': 2.2 }, pg);
    return w;
  }

  /* the building as a flat deck plan: rooms as rounded blocks in their bank colour, endpoints as dots */
  function deck(g, x, y, s, moment) {
    const B = W.building, built = moment === 'build' || moment === 'priyaTuesday', st = W.state(moment);
    const roomBank = { shop: 'counter', office: 'office', reports: 'office', workshop: 'workshop', stockroom: 'stockroom', goodsin: 'backdoor' };
    const rects = { shop: [0, 0, 6.5, 9], office: [6.5, 0, 3.3, 3.6], reports: [9.8, 0, 2.6, 3.0], workshop: [6.5, 3.6, 8.5, 5.4], workshop2: [12.4, 0, 2.6, 3.6], stockroom: [15, 0, 5, 5], goodsin: [15, 5, 5, 4] };
    for (const [id, r] of Object.entries(rects)) {
      const bank = roomBank[id] || 'workshop', planned = id === 'reports' && !built, pad = 3;
      el('rect', { x: x + r[0] * s + pad, y: y + r[1] * s + pad, width: r[2] * s - pad * 2, height: r[3] * s - pad * 2, rx: 10,
        fill: planned ? BLACK : BANK[bank], 'fill-opacity': planned ? 1 : .9, stroke: planned ? BANK.office : 'none', 'stroke-width': 2, 'stroke-dasharray': planned ? '6 5' : null }, g);
    }
    // the workshop's two blocks read as one room: bridge the seam
    el('rect', { x: x + 12.4 * s - 3, y: y + 3.0 * s, width: 6, height: 0.6 * s + 3, fill: BANK.workshop, 'fill-opacity': .9 }, g);
    for (const a of st) {
      const cx = x + a.anchor[0] * s, cy = y + a.anchor[1] * s, rr = 5.2;
      if (a.state === 'lit' || a.state === 'new') el('circle', { cx, cy, r: rr, fill: BLACK }, g);
      else if (a.state === 'shut') { el('circle', { cx, cy, r: rr, fill: 'none', stroke: BLACK, 'stroke-width': 2 }, g); el('line', { x1: cx - rr, y1: cy - rr, x2: cx + rr, y2: cy + rr, stroke: BLACK, 'stroke-width': 2 }, g); }
      else if (a.state === 'planned') el('circle', { cx, cy, r: rr, fill: 'none', stroke: BANK.office, 'stroke-width': 2, 'stroke-dasharray': '3 2' }, g);
      else el('circle', { cx, cy, r: rr, fill: 'none', stroke: BLACK, 'stroke-width': 2 }, g);
    }
  }

  window.CONSOLE = { BANK, GOLD, BLACK, DIM, F, t, elbow, cut, pill, deck };
})();
