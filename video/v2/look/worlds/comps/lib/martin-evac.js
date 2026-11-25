/* Martin · THE PLAN BY THE BACK DOOR. The building as the evacuation plan framed by every shop's back door: a true
   orthographic plan, solid walls, door swings, the safety-sign grammar everyone already reads (ISO 3864 colours):
   green square = safe = Barnaby can use it; blue circle with a key = mandatory = needs Martin's key, he asks first;
   red prohibition = kept shut; yellow triangle = warning = a real shortfall. Barnaby is the YOU ARE HERE marker,
   his route the green escape-route line.  EVAC.draw(svg, {moment, orient, s, ox, oy, detail}) -> api */
window.EVAC = (function () {
  const M = MPLAN, B = M.B, el = M.el;
  const C = { ink: '#141414', paper: '#FFFFFF', green: '#00843D', blue: '#0057A0', red: '#C8102E', yellow: '#FFC20E', line: '#141414' };
  const FONT = "'EvacNum', 'Gill Sans MT', 'Gill Sans', Calibri, sans-serif";

  function draw(svg, o) {
    const moment = o.moment, built = moment === 'build' || moment === 'priyaTuesday';
    const f = M.tf(o), s = o.s, low = o.detail === 'low';
    const P = (x, y) => f(x, y);
    const R = (x0, y0, x1, y1) => f.rect(x0, y0, x1, y1);
    const pstr = arr => arr.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ');
    const g0 = el('g', {}, svg), gW = el('g', {}, svg), gS = el('g', {}, svg);
    const thin = Math.max(1.2, s / 36);

    /* floor */
    const out = R(0, 0, 20, 9);
    el('rect', { x: out.x, y: out.y, width: out.w, height: out.h, fill: C.paper }, g0);

    /* fixtures, thin line */
    const box = (x0, y0, x1, y1, extra = {}) => { const r = R(x0, y0, x1, y1); return el('rect', Object.assign({ x: r.x, y: r.y, width: r.w, height: r.h, fill: C.paper, stroke: C.ink, 'stroke-width': thin }, extra), g0); };
    const fx = id => M.fixture(id), FR = id => { const q = fx(id).rect; return [q[0], q[1], q[0] + q[2], q[1] + q[3]]; };
    box(...FR('counter'));
    box(...FR('till'), { 'stroke-width': thin * 1.4 });
    box(...FR('desk')); box(7.6, 0.3, 8.6, 0.48, { fill: C.ink });   // the shop PC on the desk
    box(...FR('bench')); box(...FR('wheelbench'));
    { const c = P(13.8, 0.55); el('circle', { cx: c[0], cy: c[1], r: s * 0.22, fill: 'none', stroke: C.ink, 'stroke-width': thin }, g0); }   // truing stand
    for (const id of ['shelf-n', 'shelf-e', 'shelf-mid']) { const q = FR(id); box(...q); const a = P(q[0], q[1]), b = P(q[2], q[3]); el('line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: C.ink, 'stroke-width': thin * 0.7 }, g0); }
    for (const q of [[15.45, 7.7, 16.15, 8.6], [16.2, 7.95, 16.75, 8.6]]) { box(...q); const a = P(q[0], q[1]), b = P(q[2], q[3]), c2 = P(q[0], q[3]), d2 = P(q[2], q[1]); el('path', { d: `M${a[0]},${a[1]} L${b[0]},${b[1]} M${c2[0]},${c2[1]} L${d2[0]},${d2[1]}`, stroke: C.ink, 'stroke-width': thin * 0.7 }, g0); }
    for (const id of ['jobboard', 'rota', 'pegboard']) { const q = FR(id); const r = R(q[0], q[1], q[2] + 0.1, q[3]); el('rect', { x: r.x, y: r.y, width: Math.max(r.w, 5), height: Math.max(r.h, 5), fill: C.ink }, g0); }
    { const c = P(...fx('bell').at); el('circle', { cx: c[0], cy: c[1], r: s * 0.12, fill: C.paper, stroke: C.ink, 'stroke-width': thin * 1.3 }, g0); }
    /* bikes, from above */
    const bike = (xc, yc) => {
      const gg = el('g', { stroke: C.ink, 'stroke-linecap': 'round', fill: 'none' }, g0);
      const ln = (u1, v1, u2, v2, w) => { const a = P(xc + u1, yc + v1), b = P(xc + u2, yc + v2); el('line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1], 'stroke-width': w }, gg); };
      ln(-0.86, 0, -0.18, 0, s * 0.1); ln(0.16, 0, 0.84, 0, s * 0.1);    // tyres
      ln(-0.52, 0, 0.6, 0, s * 0.03);                                     // frame
      ln(0.56, -0.23, 0.56, 0.23, s * 0.05);                              // bars
      ln(-0.36, 0, -0.18, 0, s * 0.09);                                   // saddle
    };
    for (const st of B.fixtures.filter(q => q.stand)) {
      bike(st.stand[0], st.stand[1]);
      if (!low) { const c = P(st.stand[0] - 0.05, st.stand[1]); el('circle', { cx: c[0], cy: c[1], r: s * 0.09, fill: C.ink }, g0); }
    }
    for (const [bx, by] of fx('forsale').bikes) bike(bx + 0.5, by);
    /* the van in the lane */
    if (!low) { const vr = R(20.85, 5.5, o.vanTo || 22.4, 8.4); el('rect', { x: vr.x, y: vr.y, width: vr.w, height: vr.h, fill: C.paper, stroke: C.ink, 'stroke-width': thin, 'stroke-dasharray': `${s * 0.15} ${s * 0.08}` }, g0); }

    /* walls: solid poche; windows as glazing lines; door leaves and swings */
    for (const w of M.wallPieces({ built })) {
      const r = R(...w.r);
      if (w.kind === 'sill') {
        el('rect', { x: r.x, y: r.y, width: r.w, height: r.h, fill: C.paper, stroke: C.ink, 'stroke-width': thin }, gW);
        const v = r.w < r.h;
        el('line', v ? { x1: r.x + r.w / 2, y1: r.y, x2: r.x + r.w / 2, y2: r.y + r.h } : { x1: r.x, y1: r.y + r.h / 2, x2: r.x + r.w, y2: r.y + r.h / 2, }, gW).setAttribute('stroke', C.ink);
        continue;
      }
      el('rect', { x: r.x, y: r.y, width: r.w, height: r.h, fill: w.planned ? C.paper : C.ink, stroke: w.planned ? C.ink : 'none', 'stroke-width': thin }, gW);
      if (w.planned) el('rect', { x: r.x, y: r.y, width: r.w, height: r.h, fill: C.ink, opacity: 1, mask: null }, gW).setAttribute('fill', 'url(#ev-new)');
    }
    const defs = el('defs', {}, svg);
    { const p = el('pattern', { id: 'ev-new', patternUnits: 'userSpaceOnUse', width: 6, height: 6, patternTransform: 'rotate(45)' }, defs); el('line', { x1: 0, y1: 0, x2: 0, y2: 6, stroke: C.ink, 'stroke-width': 2.2 }, p); }
    if (!built) for (const sg of M.plannedLines()) { const a = P(sg[0], sg[1]), b = P(sg[2], sg[3]); el('line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: C.ink, 'stroke-width': thin * 1.6, 'stroke-dasharray': `${s * 0.2} ${s * 0.12}` }, gW); }
    for (const dr of M.doors({ built })) {
      const h = P(...dr.hinge), lf = P(...dr.leaf);
      el('path', { d: M.arcPath(f, dr), fill: 'none', stroke: C.ink, 'stroke-width': thin * 0.8, 'stroke-dasharray': dr.planned ? `${s * 0.12} ${s * 0.1}` : null }, gW);
      el('line', { x1: h[0], y1: h[1], x2: lf[0], y2: lf[1], stroke: C.ink, 'stroke-width': thin * 2, 'stroke-dasharray': dr.planned ? `${s * 0.12} ${s * 0.1}` : null }, gW);
    }

    /* signs */
    const api = { P, f, s, C, FONT, gS, svg };
    const num = (gg, x, y, n, size, col) => M.text(gg, x, y + size * 0.35, String(n), { 'text-anchor': 'middle', 'font-family': FONT, 'font-weight': 700, 'font-size': size, fill: col });
    function keyPict(gg, x, y, k, col) {   // white key pictogram, centred
      const kg = el('g', { transform: `translate(${x},${y}) rotate(-40)` }, gg);
      el('circle', { cx: -k * 0.62, cy: 0, r: k * 0.42, fill: 'none', stroke: col, 'stroke-width': k * 0.24 }, kg);
      el('path', { d: `M${-k * 0.2},0 H${k * 0.95} M${k * 0.55},0 V${k * 0.38} M${k * 0.88},0 V${k * 0.32}`, fill: 'none', stroke: col, 'stroke-width': k * 0.24 }, kg);
    }
    api.sign = function (state, x, y, size, n, parent) {
      const gg = el('g', {}, parent || gS);
      if (state === 'lit') {
        el('rect', { x: x - size / 2, y: y - size / 2, width: size, height: size, rx: size * 0.08, fill: C.green, stroke: C.paper, 'stroke-width': size * 0.07 }, gg);
        if (n != null) num(gg, x, y, n, size * 0.56, C.paper);
        else el('path', { d: `M${x - size * 0.25},${y + size * 0.02} L${x - size * 0.07},${y + size * 0.2} L${x + size * 0.27},${y - size * 0.2}`, fill: 'none', stroke: C.paper, 'stroke-width': size * 0.13, 'stroke-linecap': 'square' }, gg);
      } else if (state === 'key' || state === 'asking') {
        el('circle', { cx: x, cy: y, r: size / 2, fill: C.blue, stroke: C.paper, 'stroke-width': size * 0.07 }, gg);
        keyPict(gg, x, y - (n != null ? size * 0.12 : 0), size * 0.36, C.paper);
        if (n != null) num(gg, x, y + size * 0.2, n, size * 0.3, C.paper);
      } else if (state === 'new') {
        el('rect', { x: x - size / 2, y: y - size / 2, width: size, height: size, rx: size * 0.08, fill: C.green, stroke: C.ink, 'stroke-width': size * 0.06 }, gg);
        if (n != null) num(gg, x, y, n, size * 0.56, C.paper);
      } else if (state === 'shut') {
        el('circle', { cx: x, cy: y, r: size / 2 - size * 0.06, fill: C.paper, stroke: C.red, 'stroke-width': size * 0.12 }, gg);
        if (n != null) num(gg, x, y, n, size * 0.42, C.ink);
        else keyPict(gg, x, y, size * 0.3, C.ink);
        el('line', { x1: x - size * 0.31, y1: y - size * 0.31, x2: x + size * 0.31, y2: y + size * 0.31, stroke: C.red, 'stroke-width': size * 0.12 }, gg);
      }
      return gg;
    };
    api.warn = function (x, y, size, parent) {
      const gg = el('g', {}, parent || gS);
      const h = size * 0.87;
      el('path', { d: `M${x},${y - h / 2} L${x + size / 2},${y + h / 2} L${x - size / 2},${y + h / 2} Z`, fill: C.yellow, stroke: C.ink, 'stroke-width': size * 0.08, 'stroke-linejoin': 'round' }, gg);
      el('rect', { x: x - size * 0.045, y: y - h * 0.14, width: size * 0.09, height: h * 0.36, fill: C.ink }, gg);
      el('circle', { cx: x, cy: y + h * 0.33, r: size * 0.05, fill: C.ink }, gg);
      return gg;
    };
    api.here = function (x, y, r, parent) {
      const gg = el('g', {}, parent || gS);
      el('circle', { cx: x, cy: y, r: r * 1.55, fill: C.paper, stroke: C.red, 'stroke-width': r * 0.25 }, gg);
      el('circle', { cx: x, cy: y, r, fill: C.red }, gg);
      return gg;
    };
    api.keyPict = keyPict;

    /* route: the green line with white chevrons, Barnaby's way through the building */
    api.route = function (way, parent) {
      const gg = el('g', {}, parent || gS);
      const pts = way.map(p => P(...p));
      el('polyline', { points: pstr(pts), fill: 'none', stroke: C.paper, 'stroke-width': s * 0.36, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, gg);
      el('polyline', { points: pstr(pts), fill: 'none', stroke: C.green, 'stroke-width': s * 0.24, 'stroke-linejoin': 'round', 'stroke-linecap': 'butt' }, gg);
      // chevrons every ~1.1 m
      let acc = 0; const step = s * 1.1;
      for (let i = 0; i < pts.length - 1; i++) {
        const a = pts[i], b = pts[i + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]); if (L < 1) continue;
        const ux = (b[0] - a[0]) / L, uy = (b[1] - a[1]) / L;
        let t = step - acc;
        while (t < L - s * 0.25) {
          const cx = a[0] + ux * t, cy = a[1] + uy * t, k = s * 0.08;
          el('path', { d: `M${cx - ux * k - uy * k},${cy - uy * k + ux * k} L${cx + ux * k},${cy + uy * k} L${cx - ux * k + uy * k},${cy - uy * k - ux * k}`, fill: 'none', stroke: C.paper, 'stroke-width': s * 0.05, 'stroke-linejoin': 'miter' }, gg);
          t += step;
        }
        acc = (acc + L) % step;
      }
      // arrowhead
      const a = pts[pts.length - 2], b = pts[pts.length - 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]), ux = (b[0] - a[0]) / L, uy = (b[1] - a[1]) / L, k = s * 0.3;
      el('path', { d: `M${b[0] + ux * k * 0.9},${b[1] + uy * k * 0.9} L${b[0] - uy * k},${b[1] + ux * k} L${b[0] + uy * k},${b[1] - ux * k} Z`, fill: C.green, stroke: C.paper, 'stroke-width': s * 0.04 }, gg);
      return gg;
    };
    return api;
  }
  return { draw, C, FONT };
})();
