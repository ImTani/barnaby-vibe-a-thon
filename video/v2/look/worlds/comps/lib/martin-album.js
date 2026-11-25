/* Martin · THE STICKER ALBUM (fused from the catalog's sticker-album spread). The building plan is printed across an
   album spread; each thing the system can do is a numbered slot in its room. Stuck in = Barnaby can use it (glossy,
   proud of the page); an empty slot prints the ghost of its sticker = needs Martin's key; one slot is printed
   "kept shut"; Reports is the slot printed since 2011 with no sticker ever made.
   ALBUM.draw(svg, {moment, orient, s, ox, oy, slots, slotW, slotH}) -> api */
window.ALBUM = (function () {
  const M = MPLAN, B = M.B, el = M.el;
  const C = { page: '#C8372D', pageDark: '#A92B22', wall: '#7E1E17', line: '#E9877E', ghost: '#EFA59C', ghostNum: '#F7CFC9', white: '#FFFFFF', ink: '#1A1A1A', yellow: '#FFC82E' };
  const TEAM = { counter: '#2753C4', till: '#E89A00', workshop: '#1E1E1E', stockroom: '#13805A', backdoor: '#6A3CA3', office: '#0D7F8C' };
  const FONT = "'Franklin Gothic Demi Cond', 'Franklin Gothic Medium', 'Arial Narrow', sans-serif";
  const SHORT = {
    search: 'Find a customer', customer_detail: 'Customer details', add_customer: 'Add a customer', book_job: 'Book a bike in',
    notify: 'Text a customer', recent_notifications: 'Recent texts', unpaid: 'Unpaid bills', create_invoice: 'Raise an invoice',
    takings: 'Money taken', open_jobs: 'Open jobs', jobs_due: 'Jobs due', job_detail: 'A job’s parts', update_status: 'Job status',
    assign: 'Move a job', mechanics: 'Who works here', cancel_job: 'Cancel a job', parts_low: 'Running low', parts: 'All the shelves',
    adjust: 'Stock levels', create_purchase_order: 'Order parts', purchase_orders: 'Past orders', receive: 'Book in a delivery',
    today_at_a_glance: 'Today at a glance', workload: 'Workload',
  };
  /* slot top-left in plan metres (landscape), placed in the room where it happens, clear of the gutter at x=10 */
  const SLOT = {
    search: [0.55, 0.78], customer_detail: [2.05, 0.78], add_customer: [0.55, 2.86], book_job: [2.05, 2.86], notify: [0.55, 4.94], recent_notifications: [2.05, 4.94],
    unpaid: [4.95, 0.78], create_invoice: [4.95, 2.86], takings: [4.95, 4.94],
    today_at_a_glance: [8.3, 1.18], workload: [10.75, 0.62],
    mechanics: [6.75, 3.82], open_jobs: [8.15, 3.82], job_detail: [10.45, 3.82], update_status: [11.85, 3.82], assign: [13.25, 3.82],
    jobs_due: [6.75, 7.2], cancel_job: [11.28, 7.2],
    parts_low: [15.35, 2.98], parts: [16.65, 2.98], adjust: [17.95, 2.98],
    receive: [15.3, 5.45], purchase_orders: [16.65, 5.45], create_purchase_order: [18.05, 5.45],
  };

  /* sticker pictures: simple drawn objects in a 40x40 box, stroke only */
  const PIC = {
    search: 'M17 17 m-8 0 a8 8 0 1 0 16 0 a8 8 0 1 0 -16 0 M23 23 L32 32',
    customer_detail: 'M20 14 m-6 0 a6 6 0 1 0 12 0 a6 6 0 1 0 -12 0 M8 34 C8 24 32 24 32 34',
    add_customer: 'M16 14 m-6 0 a6 6 0 1 0 12 0 a6 6 0 1 0 -12 0 M4 34 C4 24 28 24 28 34 M33 10 V22 M27 16 H39',
    book_job: 'M8 10 H26 L33 20 L26 30 H8 Z M13 20 m-2 0 a2 2 0 1 0 4 0 a2 2 0 1 0 -4 0',
    notify: 'M12 5 H28 V35 H12 Z M12 30 H28 M17 10 H23',
    recent_notifications: 'M6 11 H34 V29 H6 Z M6 11 L20 22 L34 11',
    unpaid: 'M10 5 H30 V35 L26 32 L22 35 L18 32 L14 35 L10 32 Z M15 13 H25 M15 19 H25 M15 25 H21',
    create_invoice: 'M10 5 H30 V35 H10 Z M15 14 H25 M15 20 H25 M24 28 L28 24',
    takings: 'M8 26 a12 5 0 1 0 24 0 a12 5 0 1 0 -24 0 M8 20 a12 5 0 1 0 24 0 a12 5 0 1 0 -24 0 M8 14 a12 5 0 1 0 24 0 a12 5 0 1 0 -24 0',
    open_jobs: 'M10 7 H30 V35 H10 Z M15 4 H25 V9 H15 Z M14 16 H26 M14 22 H26 M14 28 H22',
    jobs_due: 'M6 9 H34 V35 H6 Z M6 16 H34 M13 5 V12 M27 5 V12 M12 22 H17 M23 22 H28 M12 28 H17',
    job_detail: 'M9 31 L22 18 M22 18 a6 6 0 1 0 6 -11 L24 12 L28 16 L33 12 a6 6 0 0 1 -11 6',
    update_status: 'M8 10 H26 L33 20 L26 30 H8 Z M12 20 L16 24 L23 15',
    assign: 'M10 13 m-4 0 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0 M30 13 m-4 0 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0 M4 31 C4 23 16 23 16 31 M24 31 C24 23 36 23 36 31 M14 6 C18 2 22 2 26 6 L23 6 M26 6 L26 3',
    mechanics: 'M8 14 m-4 0 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0 M20 12 m-4 0 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0 M32 14 m-4 0 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0 M2 32 C2 22 14 22 14 32 M14 30 C14 20 26 20 26 30 M26 32 C26 22 38 22 38 32',
    cancel_job: 'M10 11 H30 M15 11 V7 H25 V11 M12 11 L14 35 H26 L28 11 M17 16 V30 M23 16 V30',
    parts_low: 'M7 15 L20 9 L33 15 V29 L20 35 L7 29 Z M7 15 L20 21 L33 15 M20 21 V35',
    parts: 'M5 6 V35 M35 6 V35 M5 15 H35 M5 25 H35 M9 15 V10 H15 V15 M21 25 V19 H29 V25',
    adjust: 'M7 15 L20 9 L33 15 V29 L20 35 L7 29 Z M14 22 H26 M20 16 V28',
    create_purchase_order: 'M3 13 H24 V29 H3 Z M24 18 H31 L37 24 V29 H24 M10 29 m-3 0 a3 3 0 1 0 6 0 a3 3 0 1 0 -6 0 M30 29 m-3 0 a3 3 0 1 0 6 0 a3 3 0 1 0 -6 0',
    purchase_orders: 'M12 5 H32 V29 H12 Z M8 9 V33 H28 M17 12 H27 M17 18 H27',
    receive: 'M7 15 L20 9 L33 15 V29 L20 35 L7 29 Z M14 23 L18 27 L26 18',
    today_at_a_glance: 'M4 20 C10 10 30 10 36 20 C30 30 10 30 4 20 Z M20 20 m-5 0 a5 5 0 1 0 10 0 a5 5 0 1 0 -10 0',
    workload: 'M6 34 H34 M10 34 V18 H16 V34 M18 34 V8 H24 V34 M26 34 V24 H32 V34',
  };

  function draw(svg, o) {
    const moment = o.moment, built = moment === 'build' || moment === 'priyaTuesday';
    const f = M.tf(o), s = o.s;
    const P = (x, y) => f(x, y), R = (x0, y0, x1, y1) => f.rect(x0, y0, x1, y1);
    const SW = o.slotW || 84, SH = o.slotH || 100, k = SW / 84;
    const defs = el('defs', {}, svg);
    const sh = el('filter', { id: 'al-shadow', x: '-30%', y: '-30%', width: '160%', height: '170%' }, defs);
    el('feDropShadow', { dx: 2, dy: 4, stdDeviation: 3.5, 'flood-color': '#3A0A06', 'flood-opacity': 0.55 }, sh);
    const sh2 = el('filter', { id: 'al-lift', x: '-40%', y: '-40%', width: '190%', height: '200%' }, defs);
    el('feDropShadow', { dx: 14, dy: 22, stdDeviation: 9, 'flood-color': '#3A0A06', 'flood-opacity': 0.5 }, sh2);
    const shutP = el('pattern', { id: 'al-shut', patternUnits: 'userSpaceOnUse', width: 10, height: 10, patternTransform: 'rotate(45)' }, defs);
    el('rect', { width: 10, height: 10, fill: C.pageDark }, shutP); el('line', { x1: 0, y1: 0, x2: 0, y2: 10, stroke: C.wall, 'stroke-width': 4 }, shutP);

    const gPlan = el('g', {}, svg), gRoute = el('g', {}, svg), gSlots = el('g', {}, svg), gTop = el('g', {}, svg);
    /* the printed plan */
    const out = R(0, 0, 20, 9);
    el('rect', { x: out.x, y: out.y, width: out.w, height: out.h, fill: '#D24A3F' }, gPlan);
    const pl = { stroke: C.line, 'stroke-width': 2, fill: 'none' };
    const box = (x0, y0, x1, y1) => { const r = R(x0, y0, x1, y1); el('rect', Object.assign({ x: r.x, y: r.y, width: r.w, height: r.h }, pl), gPlan); };
    const FR = id => { const q = M.fixture(id).rect; return [q[0], q[1], q[0] + q[2], q[1] + q[3]]; };
    ['counter', 'till', 'desk', 'bench', 'wheelbench', 'shelf-n', 'shelf-e', 'shelf-mid', 'cartons'].forEach(id => box(...FR(id)));
    for (const id of ['jobboard', 'rota', 'pegboard']) { const q = FR(id); const r = R(q[0], q[1], q[2] + 0.08, q[3]); el('rect', { x: r.x, y: r.y, width: Math.max(r.w, 5), height: Math.max(r.h, 5), fill: C.line }, gPlan); }
    const bike = (xc, yc) => { const ln = (u1, u2, v1 = 0, v2 = 0, w = 2) => { const a = P(xc + u1, yc + v1), b = P(xc + u2, yc + v2); el('line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: C.line, 'stroke-width': w, 'stroke-linecap': 'round' }, gPlan); };
      ln(-0.86, -0.18, 0, 0, 5); ln(0.16, 0.84, 0, 0, 5); ln(-0.5, 0.6, 0, 0, 2); ln(0.56, 0.56, -0.23, 0.23, 3); };
    B.fixtures.filter(q => q.stand).forEach(q => bike(...q.stand));
    M.fixture('forsale').bikes.forEach(([x, y]) => bike(x + 0.5, y));
    { const c = P(...M.fixture('bell').at); el('circle', { cx: c[0], cy: c[1], r: s * 0.11, fill: 'none', stroke: C.line, 'stroke-width': 2 }, gPlan); }
    for (const w of M.wallPieces({ built })) {
      const r = R(...w.r);
      if (w.kind === 'sill') { el('rect', { x: r.x, y: r.y, width: r.w, height: r.h, fill: '#D24A3F', stroke: C.wall, 'stroke-width': 1.5 }, gPlan); continue; }
      el('rect', { x: r.x, y: r.y, width: r.w, height: r.h, fill: C.wall }, gPlan);
    }
    if (!built) for (const sg of M.plannedLines()) { const a = P(sg[0], sg[1]), b = P(sg[2], sg[3]); el('line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: C.wall, 'stroke-width': 4, 'stroke-dasharray': '12 8' }, gPlan); }
    for (const dr of M.doors({ built })) {
      const h = P(...dr.hinge), lf = P(...dr.leaf);
      el('path', { d: M.arcPath(f, dr), fill: 'none', stroke: C.wall, 'stroke-width': 1.6, 'stroke-dasharray': dr.planned ? '7 6' : null }, gPlan);
      el('line', { x1: h[0], y1: h[1], x2: lf[0], y2: lf[1], stroke: C.wall, 'stroke-width': 3.5, 'stroke-dasharray': dr.planned ? '7 6' : null }, gPlan);
    }

    const api = { P, f, s, C, TEAM, FONT, SHORT, SLOT, PIC, gTop, gRoute, slotRect: {} };
    const pic = (g, tool, x, y, k, col, w) => el('path', { d: PIC[tool], transform: `translate(${x},${y}) scale(${k})`, fill: 'none', stroke: col, 'stroke-width': w / k, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, g);

    /* a sticker (glossy, proud of the page) */
    api.sticker = function (parent, a, x, y, opts = {}) {
      const w = opts.w || SW, h = opts.h || SH, q = w / 84;
      const g = el('g', { transform: opts.rot ? `rotate(${opts.rot} ${x + w / 2} ${y + h / 2})` : null, filter: opts.lift ? 'url(#al-lift)' : 'url(#al-shadow)' }, parent);
      const col = TEAM[a.group] || C.ink;
      el('rect', { x, y, width: w, height: h, rx: 5 * q, fill: C.white }, g);
      el('rect', { x: x + 5 * q, y: y + 5 * q, width: w - 10 * q, height: h - 30 * q, rx: 2 * q, fill: col }, g);
      pic(g, a.tool, x + w / 2 - 22 * q, y + 10 * q, 1.1 * q, C.white, 3.2 * Math.max(q, 0.6));
      if (q > 0.5) M.text(g, x + 8 * q, y + h - 9 * q, String(a.n), { 'font-family': FONT, 'font-size': 20 * q, fill: C.ink });
      el('path', { d: `M${x + w * 0.55},${y} L${x + w * 0.75},${y} L${x + w * 0.2},${y + h} L${x},${y + h} L${x},${y + h * 0.8} Z`, fill: '#FFFFFF', opacity: 0.16 }, g);
      if (opts.foil) for (let i = 0; i < 4; i++) el('path', { d: `M${x + 12 * q + i * 20 * q},${y + 5 * q} L${x + 22 * q + i * 20 * q},${y + 5 * q} L${x + 2 * q + i * 20 * q},${y + h - 25 * q} L${x - 8 * q + i * 20 * q},${y + h - 25 * q} Z`, fill: '#FFFFFF', opacity: 0.14 }, g);
      return g;
    };
    /* an empty slot printing its ghost */
    api.slot = function (parent, a, x, y, kind) {
      const g = el('g', {}, parent);
      if (kind === 'shut') {
        el('rect', { x, y, width: SW, height: SH, rx: 5, fill: 'url(#al-shut)', stroke: C.wall, 'stroke-width': 2 }, g);
        el('rect', { x: x + 4, y: y + SH / 2 - 14, width: SW - 8, height: 28, fill: C.ink }, g);
        M.text(g, x + SW / 2, y + SH / 2 + 6, 'KEPT SHUT', { 'text-anchor': 'middle', 'font-family': FONT, 'font-size': 16, fill: C.white });
        M.text(g, x + 8, y + 22, String(a.n), { 'font-family': FONT, 'font-size': 20, fill: C.ghostNum });
        return g;
      }
      el('rect', { x, y, width: SW, height: SH, rx: 5, fill: C.pageDark }, g);
      el('rect', { x: x + 3, y: y + 3, width: SW - 6, height: SH - 6, rx: 4, fill: 'none', stroke: C.ghost, 'stroke-width': 2, 'stroke-dasharray': '6 4' }, g);
      if (a.tool && PIC[a.tool]) pic(g, a.tool, x + SW / 2 - 22 * k, y + 10 * k, 1.1 * k, C.ghost, 2.4 * Math.max(k, 0.6));
      if (k > 0.6) M.text(g, x + SW / 2, y + SH - 12 * k, kind === 'planned' ? '24' : String(a.n), { 'text-anchor': 'middle', 'font-family': FONT, 'font-size': 26 * k, fill: C.ghostNum });
      return g;
    };
    api.caption = function (parent, a, x, y, extra = {}) {
      const words = (extra.text || SHORT[a.tool]).split(' ');
      const lines = []; let cur = '';
      for (const w of words) { const t = cur ? cur + ' ' + w : w; if (t.length > 11 && cur) { lines.push(cur); cur = w; } else cur = t; }
      lines.push(cur);
      lines.forEach((ln, i) => M.text(parent, x + SW / 2, y + SH + 21 + i * 19, ln, Object.assign({ 'text-anchor': 'middle', 'font-family': FONT, 'font-size': 18, fill: C.white }, extra.attrs || {})));
    };
    api.slotXY = tool => {
      if (o.slotsFromAnchors) { const a = B.abilities.find(q => q.tool === tool); const c = P(...a.anchor); return [c[0] - SW / 2, c[1] - SH / 2]; }
      const p = (o.slots && o.slots[tool]) || SLOT[tool]; return P(p[0], p[1]); };

    /* every ability: slot, sticker or ghost, and its caption */
    const st = M.numbered(moment);
    for (const a of st) {
      const [x, y] = api.slotXY(a.tool);
      api.slotRect[a.tool] = { x, y, w: SW, h: SH };
      const cap = !o.noCaptions;
      if (a.state === 'planned') { api.slot(gSlots, a, x, y, 'planned'); if (cap) api.caption(gSlots, a, x, y, { text: 'Reports: coming soon!!' }); continue; }
      if (a.state === 'shut') { if (k > 0.6) api.slot(gSlots, a, x, y, 'shut'); else { el('rect', { x, y, width: SW, height: SH, rx: 3, fill: 'url(#al-shut)', stroke: C.wall, 'stroke-width': 1.5 }, gSlots); } if (cap) api.caption(gSlots, a, x, y); continue; }
      if (a.state === 'new' && o.skipNew) continue;
      api.slot(gSlots, a, x, y, 'ghost');
      if (cap) api.caption(gSlots, a, x, y, a.state === 'lit' || a.state === 'new' ? { attrs: { 'font-weight': 700 } } : {});
      if (a.state === 'lit' || a.state === 'new') api.sticker(gSlots, a, x, y);
    }
    api.items = st;
    return api;
  }
  return { draw, C, TEAM, FONT };
})();
