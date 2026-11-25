/* MARTIN: the shop as a floor plan, done with the sticker album's clarity. A handful of rooms, each its own colour;
   the room Barnaby is in is the only one in full colour, everything else a pale tint of its own hue; big room names;
   what he can do in each room as pips (filled: he can; ring: needs your key; struck: kept shut). Three marks only, each
   its own shape: the KEY he is asking for (a white disc, gold key), the PASSAGE he made (a road-marked band), the NEW
   ROOM (a sticker). Data: ../../worlds/data/building.js (the building, all 24 abilities), canon.js (dates, colours).
   MARTIN.plan(svg, opts) draws into an <svg>; pure function of opts. */
(function () {
  const { el, text, bell, key, warn, FONT } = window.W2;
  const W = window.WORLDS, B = W.building;
  const INK = '#1D1B17', PAPER = '#F5F2EA', GOLD = '#B8892B', GOLD_LT = '#E2B54E';

  // film: the first k (0..1) of a polyline, by length
  function cut(path, k) {
    if (k == null || k >= 1) return path;
    const seg = path.slice(1).map((p, i) => Math.hypot(p[0] - path[i][0], p[1] - path[i][1]));
    let d = Math.max(0, k) * seg.reduce((a, b) => a + b, 0); const out = [path[0]];
    for (let i = 0; i < seg.length; i++) {
      if (d >= seg[i]) { out.push(path[i + 1]); d -= seg[i]; continue; }
      const u = seg[i] ? d / seg[i] : 0; out.push([path[i][0] + (path[i + 1][0] - path[i][0]) * u, path[i][1] + (path[i + 1][1] - path[i][1]) * u]); break;
    }
    return out;
  }

  function mapper(o) {
    return o.rotate
      ? (x, y) => [o.x + y * o.s, o.y + (B.size.w - x) * o.s]          // portrait: back lane at the top, Market Place below
      : (x, y) => [o.x + x * o.s, o.y + y * o.s];
  }
  const pts = (T, poly) => poly.map(p => T(p[0], p[1]).map(n => n.toFixed(1)).join(',')).join(' ');

  function bikeGlyph(g, cx, cy, r, col, sw) {           // a bike side-on, wheels radius r
    el('circle', { cx: cx - r * 1.35, cy, r, fill: 'none', stroke: col, 'stroke-width': sw }, g);
    el('circle', { cx: cx + r * 1.35, cy, r, fill: 'none', stroke: col, 'stroke-width': sw }, g);
    el('path', { d: `M${cx - r * 1.35},${cy} L${cx - r * .25},${cy - r * 1.05} L${cx + r * .95},${cy - r * 1.05} L${cx + r * 1.35},${cy} M${cx - r * .25},${cy - r * 1.05} L${cx + .1 * r},${cy} L${cx + r * .95},${cy - r * 1.05} M${cx - r * .4},${cy - r * 1.35} L${cx - r * .05},${cy - r * 1.35} M${cx + r * .95},${cy - r * 1.05} L${cx + r * .8},${cy - r * 1.5} L${cx + r * 1.15},${cy - r * 1.5}`, fill: 'none', stroke: col, 'stroke-width': sw, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, g);
  }
  function pill(parent, x, y, str, o) {              // text in a rounded ink pill, left edge at x, centred on y
    const g = el('g', {}, parent), fs = o.fs || 19, pad = o.pad || 12;
    const t = text(g, x + pad, y + fs * .35, str, { 'font-family': FONT.martin, 'font-size': fs, 'font-weight': 700, fill: o.fill || '#fff' });
    const w = t.getComputedTextLength() + pad * 2, h = fs * 1.6;
    g.insertBefore(el('rect', { x, y: y - h / 2, width: w, height: h, rx: h / 2, fill: o.bg || INK }), t);
    return { g, w };
  }

  /* opts: { moment, x, y, s, rotate, focus: roomId, built: bool (reports drawn as Workload), labelAt: {room: [mx,my,dx,dy]},
     labelSize, pipR, route: [[x,y]...], stops: [[x,y,label,dx,dy]...], marker: [x,y], keyAsk: [x,y], passage: bool,
     newSticker: [mx,my,rot,w,h], pads: [mx,my,rot,w] }
     film state (each optional, default = the approved drawing): passageK (0..1 the band drawn so far, its label at 1),
     stickerK (0..1 the NEW sticker slapped on), keyK (0..1 the key disc popping in), keyRot (deg, the key turning),
     routeOpacity */
  function marker(g, T, o) {
    const p = T(o.marker[0], o.marker[1]), r = o.markerR || 30;
    el('circle', { cx: p[0] + 2, cy: p[1] + 5, r: r + 1, fill: 'rgba(0,0,0,.22)' }, g);
    el('circle', { cx: p[0], cy: p[1], r, fill: INK, stroke: '#fff', 'stroke-width': 4 }, g);
    bell(g, p[0], p[1] + 1, r * 1.2, GOLD_LT);
    if (o.markerLabel) text(g, p[0] + (o.markerLabel[1] || 0), p[1] + r + (o.markerLabel[2] || 26), o.markerLabel[0], { 'text-anchor': 'middle', 'font-family': FONT.martin, 'font-size': o.markerLabelSize || 20, 'font-weight': 700, fill: o.markerLabelFill || '#fff' });
  }

  function plan(svg, o) {
    if (o.onlyMarker) { const T = mapper(o), g = el('g', {}, svg); marker(g, T, o); return { T, g }; }   // film: the marker alone
    const T = mapper(o), s = o.s, g = el('g', {}, svg);
    const st = W.state(o.moment);
    const built = !!o.built;
    const LS = o.labelSize || 32, PR = o.pipR || 7;

    // the building's outline: the outside wall in ink, with the front door and the back door left open
    const ow = 0.16;
    el('polygon', { points: pts(T, [[-ow, -ow], [B.size.w + ow, -ow], [B.size.w + ow, B.size.h + ow], [-ow, B.size.h + ow]]), fill: PAPER, stroke: INK, 'stroke-width': o.wallW || 5, 'stroke-linejoin': 'round' }, g);

    // rooms: tiles of their own colour, separated by paper gutters
    for (const R of W.ROOMS) {
      const room = B.rooms[R.id], isFocus = o.focus === R.id;
      if (R.id === 'reports' && !built) {
        el('polygon', { points: pts(T, room.poly), fill: PAPER, stroke: '#A39C8E', 'stroke-width': 2.5, 'stroke-dasharray': '9 7' }, g);
        continue;
      }
      el('polygon', { points: pts(T, room.poly), fill: isFocus ? R.hue : R.tint, stroke: PAPER, 'stroke-width': o.gutter || 9, 'stroke-linejoin': 'round', 'paint-order': 'stroke' }, g);
    }

    // fixtures: faint, in a shade of the room's own colour (character, not information)
    const fx = el('g', {}, g);
    const fcol = rid => o.focus === rid ? 'rgba(255,255,255,.30)' : (W.ROOMS.find(r => r.id === rid).deep + '3A');
    const rectOf = r => { const a = T(r[0], r[1]), b = T(r[0] + r[2], r[1] + r[3]); return { x: Math.min(a[0], b[0]), y: Math.min(a[1], b[1]), w: Math.abs(b[0] - a[0]), h: Math.abs(b[1] - a[1]) }; };
    for (const f of B.fixtures) {
      if (f.outside || ['till', 'bell', 'jobboard', 'rota', 'pegboard', 'cabinet', 'pads'].includes(f.id)) continue;
      if (o.skipFixtures && o.skipFixtures.includes(f.id)) continue;
      const rid = f.room, col = fcol(rid);
      if (f.rect && !f.bikes) { const r = rectOf(f.rect); el('rect', { x: r.x, y: r.y, width: r.w, height: r.h, rx: 3, fill: col }, fx); }
      if (f.bikes && !o.rotate) f.bikes.forEach(b => { const p = T(b[0] + .55, b[1]); bikeGlyph(fx, p[0], p[1], s * .26, col, 2.2); });
      if (f.stand) {
        const p = T(f.stand[0], f.stand[1]);
        if (!o.rotate) bikeGlyph(fx, p[0], p[1], s * .3, col, 2.6);
        if (o.standNames) text(fx, p[0], p[1] + s * .8, f.who, { 'text-anchor': 'middle', 'font-family': FONT.martin, 'font-size': o.standNameSize || 19, 'font-weight': 700, fill: o.focus === 'workshop' ? 'rgba(255,255,255,.85)' : W.ROOMS[2].deep + 'B8' });
      }
    }

    // doors: the front door and the back door as clear gaps in the outside wall
    const door = (x1, y1, x2, y2) => { const a = T(x1, y1), b = T(x2, y2); el('line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: PAPER, 'stroke-width': (o.wallW || 5) + 4 }, g); };
    door(-ow, 6.7, -ow, 7.8); door(B.size.w + ow, 5.9, B.size.w + ow, 8.1);

    // labels and pips
    const byRoom = {};
    for (const a of st) { const R = W.roomOfAbility(a); (byRoom[R.id] = byRoom[R.id] || []).push(a); }
    const order = { lit: 0, new: 0, asking: 1, key: 2, shut: 3, planned: 4 };
    for (const R of W.ROOMS) {
      const isFocus = o.focus === R.id, at = (o.labelAt || {})[R.id];
      if (!at) continue;
      const p = T(at[0], at[1]);
      const lx = p[0] + (at[2] || 0), ly = p[1] + (at[3] || 0);
      if (R.id === 'reports' && !built) {
        text(g, lx, ly, 'Reports', { 'font-family': FONT.martin, 'font-size': LS * .8, 'font-weight': 700, fill: '#857E70' });
        text(g, lx, ly + LS * .8, 'planned 2011', { 'font-family': FONT.martin, 'font-size': LS * .6, fill: '#857E70' });
        continue;
      }
      const name = R.id === 'reports' ? 'Workload' : R.say;
      const lines = (o.labelLines || {})[R.id] || [name];
      const ls = (o.labelSizes || {})[R.id] || LS;
      lines.forEach((ln, i) => text(g, lx, ly + i * ls, ln, { 'font-family': FONT.martin, 'font-size': ls, 'font-weight': 700, fill: isFocus ? '#fff' : R.deep }));
      if (o.pips === false) continue;
      const items = (byRoom[R.id] || []).filter(a => a.state !== 'planned' && a.state !== 'asking').sort((a, b) => order[a.state] - order[b.state]);
      const py = ly + (lines.length - 1) * ls + ls * .55 + PR, perRow = (o.pipsPerRow || {})[R.id] || 12;
      items.forEach((a, i) => {
        const cx = lx + PR + (i % perRow) * PR * 3, cy = py + Math.floor(i / perRow) * PR * 3;
        const c = isFocus ? '#fff' : R.deep;
        if (a.state === 'lit' || a.state === 'new') el('circle', { cx, cy, r: PR, fill: c }, g);
        else {
          el('circle', { cx, cy, r: PR - 1.2, fill: 'none', stroke: c, 'stroke-width': 2.4 }, g);
          if (a.state === 'shut') el('line', { x1: cx - PR * .72, y1: cy + PR * .72, x2: cx + PR * .72, y2: cy - PR * .72, stroke: c, 'stroke-width': 2.4 }, g);
        }
      });
    }

    // the street and the lane
    if (o.streets !== false) {
      const sf = { 'font-family': FONT.martin, 'font-size': o.streetSize || 18, 'font-weight': 700, fill: '#7D766A', 'letter-spacing': '0.22em', 'text-anchor': 'middle' };
      if (!o.rotate) {
        const a = T(-0.62, B.size.h / 2), b = T(B.size.w + 0.62, B.size.h / 2);
        text(g, a[0], a[1], 'MARKET PLACE', Object.assign({ transform: `rotate(-90 ${a[0]} ${a[1]})` }, sf));
        text(g, b[0], b[1], 'BACK LANE', Object.assign({ transform: `rotate(90 ${b[0]} ${b[1]})` }, sf));
      } else {
        const a = T(-0.62, B.size.h / 2), b = T(B.size.w + 0.5, B.size.h / 2);
        text(g, a[0], a[1] + 6, 'MARKET PLACE', sf); text(g, b[0], b[1] + 2, 'BACK LANE', sf);
      }
    }

    // his walk (a dotted ink line) and its stops
    if (o.route && o.route.length > 1) {
      const rg = o.routeOpacity != null && o.routeOpacity < 1 ? el('g', { opacity: o.routeOpacity }, g) : g;
      const d = o.route.map((p, i) => (i ? 'L' : 'M') + T(p[0], p[1]).map(n => n.toFixed(1)).join(',')).join(' ');
      el('path', { d, fill: 'none', stroke: '#fff', 'stroke-width': 10, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', opacity: .85 }, rg);
      el('path', { d, fill: 'none', stroke: INK, 'stroke-width': 5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-dasharray': '0.1 11' }, rg);
      for (const sp of o.stops || []) {
        const p = T(sp[0], sp[1]);
        el('circle', { cx: p[0], cy: p[1], r: 8, fill: '#fff', stroke: INK, 'stroke-width': 3.5 }, rg);
        if (sp[2]) pill(rg, p[0] + (sp[3] || 16), p[1] + (sp[4] || 0), sp[2], { fs: 18 });
      }
    }

    // the passage he made: a road-marked band, its own shape
    if (o.passage && !(o.passageK <= 0)) {
      const path = cut(o.passagePath || B.passage.path.slice(0, 3), o.passageK);
      const d = path.map((p, i) => (i ? 'L' : 'M') + T(p[0], p[1]).map(n => n.toFixed(1)).join(',')).join(' ');
      const pw = o.passageW || 20, op = o.passageDim ? .62 : 1, pg = el('g', { opacity: op }, g);
      el('path', { d, fill: 'none', stroke: '#fff', 'stroke-width': pw + 8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, pg);
      el('path', { d, fill: 'none', stroke: INK, 'stroke-width': pw, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, pg);
      el('path', { d, fill: 'none', stroke: GOLD_LT, 'stroke-width': 3.2, 'stroke-dasharray': '14 12', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, pg);
      if (o.passageLabel && !(o.passageK < 1)) pill(pg, ...T(o.passageLabel[0], o.passageLabel[1]), 'Hand back a bike', { fs: o.passageLabelSize || 20 });
    }

    // the key he's asking for: a white disc with a gold key, ringed in ink
    if (o.keyAsk && !(o.keyK <= 0)) {
      const p = T(o.keyAsk[0], o.keyAsk[1]), r = o.keyR || 38;
      const kg = o.keyK != null && o.keyK < 1 ? el('g', { transform: `translate(${p[0]},${p[1]}) scale(${o.keyK}) translate(${-p[0]},${-p[1]})` }, g) : g;
      el('circle', { cx: p[0] + 2, cy: p[1] + 5, r: r + 1, fill: 'rgba(0,0,0,.2)' }, kg);
      el('circle', { cx: p[0], cy: p[1], r, fill: '#fff', stroke: INK, 'stroke-width': 4 }, kg);
      key(kg, p[0], p[1], r * 1.34, GOLD, o.keyRot || 0);
    }

    // Barnaby: an ink disc with his bell, where he is
    if (o.marker) marker(g, T, o);
  
    // the new room's sticker
    if (o.newSticker && !(o.stickerK <= 0)) {
      const q = o.newSticker, p = T(q[0], q[1]), R = W.ROOMS.find(r => r.id === 'reports'), sk = o.stickerK == null ? 1 : o.stickerK;
      const sg = el('g', { transform: `translate(${p[0]},${p[1]}) rotate(${q[2] || -8})` + (sk < 1 || sk > 1 ? ` scale(${sk})` : '') }, g);
      const w = q[3] || 104, h = q[4] || 46;
      el('rect', { x: -w / 2 + 3, y: -h / 2 + 5, width: w, height: h, rx: 9, fill: 'rgba(0,0,0,.22)' }, sg);
      el('rect', { x: -w / 2, y: -h / 2, width: w, height: h, rx: 9, fill: '#fff', stroke: R.deep, 'stroke-width': 3 }, sg);
      text(sg, 0, h * .21, 'NEW', { 'text-anchor': 'middle', 'font-family': FONT.martin, 'font-size': h * .62, 'font-weight': 700, fill: R.hue, 'letter-spacing': '0.08em' });
    }

    // the pads: a stuck-on warning where the shortfall is
    if (o.pads) {
      const p = T(o.pads[0], o.pads[1]), sg = el('g', { transform: `translate(${p[0]},${p[1]}) rotate(${o.pads[2] || -3})` }, g);
      const w = o.pads[3] || 240, h = 68;
      el('rect', { x: 3, y: 5, width: w, height: h, rx: 8, fill: 'rgba(0,0,0,.2)' }, sg);
      el('rect', { x: 0, y: 0, width: w, height: h, rx: 8, fill: '#fff', stroke: '#A3261B', 'stroke-width': 2.5 }, sg);
      warn(sg, 25, h / 2, 26, '#A3261B');
      text(sg, 48, 29, 'Pads: 1 pair left', { 'font-family': FONT.martin, 'font-size': 21, 'font-weight': 700, fill: '#A3261B' });
      text(sg, 48, 54, 'Anika’s brakes need 2', { 'font-family': FONT.martin, 'font-size': 19, fill: INK });
    }
    return { T, g };
  }

  /* the legend: shapes only, in ink */
  function legend(svg, x, y, items, o = {}) {
    const g = el('g', {}, svg), fs = o.fs || 20, gap = o.gap || 40; let cx = x;
    for (const it of items) {
      const cy = y - fs * .32;
      if (it === 'can') el('circle', { cx: cx + 8, cy, r: 8, fill: INK }, g);
      if (it === 'key') el('circle', { cx: cx + 8, cy, r: 6.8, fill: 'none', stroke: INK, 'stroke-width': 2.4 }, g);
      if (it === 'shut') { el('circle', { cx: cx + 8, cy, r: 6.8, fill: 'none', stroke: INK, 'stroke-width': 2.4 }, g); el('line', { x1: cx + 3, y1: cy + 5, x2: cx + 13, y2: cy - 5, stroke: INK, 'stroke-width': 2.4 }, g); }
      if (it === 'walk') el('line', { x1: cx + 2, y1: cy, x2: cx + 36, y2: cy, stroke: INK, 'stroke-width': 5, 'stroke-linecap': 'round', 'stroke-dasharray': '0.1 11' }, g);
      if (it === 'asking') { el('circle', { cx: cx + 15, cy, r: 15, fill: '#fff', stroke: INK, 'stroke-width': 2.5 }, g); key(g, cx + 15, cy, 21, GOLD); }
      if (it === 'passage') { el('line', { x1: cx + 6, y1: cy, x2: cx + 40, y2: cy, stroke: INK, 'stroke-width': 13, 'stroke-linecap': 'round' }, g); el('line', { x1: cx + 6, y1: cy, x2: cx + 40, y2: cy, stroke: GOLD_LT, 'stroke-width': 2.4, 'stroke-dasharray': '9 7' }, g); }
      if (it === 'new') { const sg = el('g', { transform: `translate(${cx + 26},${cy}) rotate(-6)` }, g); el('rect', { x: -26, y: -13, width: 52, height: 26, rx: 6, fill: '#fff', stroke: '#7A1A41', 'stroke-width': 2 }, sg); text(sg, 0, 6, 'NEW', { 'text-anchor': 'middle', 'font-family': FONT.martin, 'font-size': 16, 'font-weight': 700, fill: '#B0285F' }); }
      if (it === 'barnaby') { el('circle', { cx: cx + 15, cy, r: 15, fill: INK }, g); bell(g, cx + 15, cy + .5, 18, GOLD_LT); }
      const label = { can: 'He can do it', key: 'Needs your key', shut: 'Kept shut', walk: 'His walk this morning', asking: 'The key he’s asking for', passage: 'A shortcut he made', new: 'Built today', barnaby: 'Barnaby' }[it];
      const off = { can: 26, key: 26, shut: 26, walk: 48, asking: 40, passage: 52, new: 62, barnaby: 40 }[it];
      const t = text(g, cx + off, y, label, { 'font-family': FONT.martin, 'font-size': fs, fill: INK });
      cx += off + t.getComputedTextLength() + gap;
    }
    return g;
  }

  window.MARTIN = { plan, legend, pill, cut, INK, PAPER, GOLD, GOLD_LT };
})();
