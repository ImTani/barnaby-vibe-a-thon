/* Theo's frames, built from HOLO2 (theo.js). Each scene is a pure function of its inputs.
   handoverWide(svg, beat)  1920x1080 cut-in, Thu 19 Nov 21:47, modest. beat 'reading' | 'taken'
   handoverTall(svg, w, h)  the same 'taken' beat laid out for Barnaby's window on the 2009 PC (portrait), modest
   buildTall(svg, w, h)     the Build moment, Mon 23 Nov 16:16, in Theo's world (portrait panel), full */
(function () {
  const { el, text, FONT } = window.W2;
  const H = window.HOLO2, C = H.C, T0 = window.THEO, W = window.WORLDS, S = W.story;

  const PATHS = {};
  W.building.abilities.forEach(a => { const i = a.key.indexOf(' '); PATHS[a.tool] = [a.key.slice(0, i), a.key.slice(i + 1)]; });

  function ground(svg, w, h, d, o = {}) {
    el('rect', { x: 0, y: 0, width: w, height: h, fill: C.ground }, svg);
    if (o.lamp !== false) el('rect', { x: 0, y: 0, width: w * .6, height: h, fill: d.lamp }, svg);
  }

  function handoverWide(svg, beat) {
    const w = 1920, h = 1080, d = H.defs(svg), Sh = S.handover, sy = Sh.synapse;
    ground(svg, w, h, d);
    const px = 56, P = T0.projection({ cx: 930, cy: 452, s: px, yaw: -0.36, pitch: 0.6 });
    const reading = beat === 'reading', scanX = 12.7;

    // what Synapse is doing, top left; the clock, top right (small: context, not focus)
    const top = el('g', { 'font-family': FONT.mono }, svg);
    text(top, 64, 78, `$ ${sy.cmd}`, { fill: C.white, 'font-size': 19, 'font-weight': 600 });
    if (reading) text(top, 64, 108, `reading ${sy.repo} …  17 endpoints so far`, { fill: C.amberLine, 'font-size': 16 });
    else text(top, 64, 108, `Extracted ${sy.found} endpoint(s) · ${sy.exposed} read-only taken · ${sy.denied} denied · ${sy.seconds.toFixed(2)} s`, { fill: C.amber, 'font-size': 16 });
    text(svg, w - 64, 78, 'Thu 19 Nov 2026  21:47', { fill: C.mute, 'font-family': FONT.mono, 'font-size': 16, 'text-anchor': 'end' });

    if (reading) {
      // the system being read: everything found so far is the same quiet outline; the plane is the one event
      H.model(svg, { P, px, moment: 'handover', allFound: true, scanX, fidelity: 'modest', built: false, defs: d, keyOpacity: .7 });
      const tp = H.scan(svg, P, scanX);
      const lg = el('g', {}, svg);
      text(lg, tp[0] + 14, tp[1] + 6, 'reading the workshop', { fill: C.accent, 'font-family': FONT.mono, 'font-size': 18, 'font-weight': 600 });
      H.heard(svg, 120, 900, 'THEO', ['Right. Barnaby, this is the shop’s system. I wrote it when I was', 'fourteen, so be kind. Look after them for me.'], { fs: 27, indent: 96 });
      return;
    }

    // what matters: the six he took, each named once, where it lives
    const m = H.model(svg, { P, px, moment: 'handover', fidelity: 'modest', built: false, defs: d, keyOpacity: .5 });
    const pos = m.pos;
    const place = {   // label positions: outside the model's silhouette, every leader short, none crossing
      search:     [528, 334, 'right'],
      mechanics:  [760, 262, 'right'],
      parts_low:  [1400, 196, 'left'],
      open_jobs:  [806, 712, 'right'],
      jobs_due:   [884, 712, 'left'],
      job_detail: [1236, 606, 'left'],
    };
    for (const tool in place) {
      const [x, y, al] = place[tool], [mth, path] = PATHS[tool];
      H.callout(svg, pos[tool], [x, y], mth, path, { fs: 19, align: al });
    }
    H.counts(svg, 1236, 660, [['lit', '6 taken · read-only'], ['key', '16 need a key'], ['shut', '1 denied']], { fs: 17, gap: 28 });
    H.says(svg, 120, 892, ['Twenty-three endpoints, sir. I’ve taken the six', 'that only read; nobody’s given me any keys yet.'], { fs: 46, lh: 60 });
  }

  /* portrait: the window on the shop PC (logical px; the page scales it 1.5x) */
  function handoverTall(svg, w, h) {
    const d = H.defs(svg), sy = S.handover.synapse;
    ground(svg, w, h, d, { lamp: false });
    const px = 19.5, P = T0.projection({ cx: w / 2 + 6, cy: 142, s: px, yaw: -0.36, pitch: 0.6 });
    const top = el('g', { 'font-family': FONT.mono }, svg);
    text(top, 16, 26, `$ ${sy.cmd}`, { fill: C.white, 'font-size': 11.5, 'font-weight': 600 });
    text(top, 16, 44, `${sy.found} found · ${sy.exposed} taken · ${sy.denied} denied · ${sy.seconds.toFixed(2)} s`, { fill: C.amber, 'font-size': 10.5 });
    H.model(svg, { P, px, moment: 'handover', fidelity: 'modest', built: false, defs: d, keyOpacity: .5 });
    // the six, listed once, by room (the model shows where; the list says what)
    const lit = W.state('handover').filter(a => a.state === 'lit');
    const rooms = [['counter', 'COUNTER'], ['workshop', 'WORKSHOP'], ['stockroom', 'STOCKROOM']];
    let y = 240;
    text(svg, 16, y, 'The six I’ve taken (read-only)', { 'font-family': FONT.theo, 'font-size': 14, 'font-weight': 700, fill: C.white });
    y += 26;
    for (const [gid, name] of rooms) {
      text(svg, 16, y, name, { 'font-family': FONT.theo, 'font-size': 10, 'font-weight': 700, fill: C.amber, 'letter-spacing': '0.16em' });
      y += 17;
      for (const a of lit.filter(x => x.group === gid)) {
        const [mth, path] = PATHS[a.tool];
        el('rect', { x: 18, y: y - 8.5, width: 8.5, height: 8.5, fill: C.white }, svg);
        text(svg, 36, y, mth, { 'font-family': FONT.mono, 'font-size': 10, fill: C.mute });
        text(svg, 64, y, path, { 'font-family': FONT.mono, 'font-size': 12, 'font-weight': 600, fill: C.white });
        y += 16;
      }
      y += 7;
    }
    H.counts(svg, 16, y + 6, [['key', '16 need a key'], ['shut', '1 denied']], { fs: 11, gap: 16 });
    H.says(svg, 14, h - 80, ['Twenty-three endpoints, sir.', 'I’ve taken the six that only read;', 'nobody’s given me any keys yet.'], { fs: 19, lh: 25 });
  }

  /* the Build moment in Theo's world: the room built where Reports was planned, one new endpoint, the checks */
  function buildTall(svg, w, h) {
    const d = H.defs(svg), b = S.build.technical;
    ground(svg, w, h, d);
    // his desk's bar: Lisbon, his first day, the same minute
    const bar = el('g', { 'font-family': FONT.mono }, svg);
    el('rect', { x: 14, y: 14, width: w - 28, height: 34, rx: 7, fill: 'rgba(21,18,15,.95)', stroke: '#3a3128' }, bar);
    el('rect', { x: 22, y: 21, width: 28, height: 20, rx: 4, fill: '#f2c14e' }, bar);
    text(bar, 36, 36, '1', { 'text-anchor': 'middle', 'font-size': 13, 'font-weight': 700, fill: '#1b1713' });
    text(bar, 62, 36, 'barnaby · spokes-and-sprockets', { 'font-size': 13, fill: '#b9ab96' });
    text(bar, w - 26, 36, 'Mon 23 Nov  16:16', { 'font-size': 13, fill: '#f2c14e', 'text-anchor': 'end', 'font-weight': 700 });

    const px = 24.5, P = T0.projection({ cx: w / 2 + 4, cy: 236, s: px, yaw: -0.36, pitch: 0.6 });
    const m = H.model(svg, { P, px, moment: 'build', fidelity: 'full', built: true, defs: d, keyOpacity: .45 });
    const p = m.pos.workload;
    H.callout(svg, p, [40, 452], 'GET', '/api/reports/workload/{day}', { fs: 17, accent: C.accent, note: 'written today · added 16:16 · Martin clicked', noteFill: C.white });

    // the change, as numbers he trusts
    let y = 560;
    text(svg, 40, y, 'the change', { 'font-family': FONT.theo, 'font-size': 15, 'font-weight': 700, fill: C.amber, 'letter-spacing': '0.14em' });
    y += 36;
    for (const [f, n] of b.files) {
      text(svg, 40, y, f, { 'font-family': FONT.mono, 'font-size': 20, fill: C.white });
      text(svg, w - 40, y, n, { 'font-family': FONT.mono, 'font-size': 20, fill: '#9BD08A', 'text-anchor': 'end' });
      y += 33;
    }
    text(svg, 40, y + 2, `+${b.added} −${b.removed} · on a git worktree · fast-forward after approval`, { 'font-family': FONT.mono, 'font-size': 14, fill: C.mute });
    y += 84;
    // the checks: the moment's single result
    W2.tick(svg, 60, y - 13, 42, '#9BD08A', 3);
    text(svg, 96, y, '22 passed', { 'font-family': FONT.mono, 'font-size': 38, 'font-weight': 700, fill: C.white });
    text(svg, 96, y + 30, '1 warning · 1.55 s · your 19, and 3 new ones', { 'font-family': FONT.mono, 'font-size': 15, fill: C.whiteDim });
    y += 94;
    text(svg, 40, y, `$ ${b.rediscover.split(' · ')[0]}`, { 'font-family': FONT.mono, 'font-size': 15, fill: C.white });
    text(svg, 40, y + 24, `Extracted 24 endpoint(s) · ${b.rediscover.split(' · ')[2]}`, { 'font-family': FONT.mono, 'font-size': 15, fill: C.amber });
    H.counts(svg, 40, h - 44, [['lit', '9 his'], ['new', '1 new'], ['key', '13 need a key'], ['shut', '1 denied']], { fs: 15, gap: 20 });
  }


  /* Lisbon, Tue 24 Nov 09:41 (scene 8, staged): Quorum read at 09:39:58; what matters now is the two disputes.
     The form is Quorum's own: 13 endpoints on one plate (it has no rooms), the six he took lit. Full fidelity. */
  function quorumTall(svg, w, h, E, Q, say) {
    const d = H.defs(svg);
    el('rect', { x: 0, y: 0, width: w, height: h, fill: '#14110E' }, svg);
    // head: his name and what he's doing, as the desk's own slot does
    text(svg, 18, 30, 'Barnaby', { 'font-family': FONT.theo, 'font-size': 15, 'font-weight': 700, fill: '#ece3d4' });
    const pill = el('g', {}, svg);
    el('rect', { x: w - 86, y: 15, width: 70, height: 21, rx: 10.5, fill: 'none', stroke: '#f2c14e', 'stroke-width': 1.2 }, pill);
    text(pill, w - 51, 30, 'speaking', { 'text-anchor': 'middle', 'font-family': FONT.mono, 'font-size': 11, fill: '#f2c14e' });

    // the form: one plate, five by three, reads in front
    const order = [['resolve', 'draft', 'receive'], ['stage', 'get_index', 'ingest_route', 'ask', 'net'], ['state', 'events', 'inbox', 'look', 'phone']];
    const exposed = new Set(['state', 'events', 'inbox', 'look', 'phone', 'stage']);
    const px = 30, P = T0.projection({ cx: w / 2 + 4, cy: 132, s: px, yaw: -0.36, pitch: 0.6, ox: 3.6, oy: 2.1 });
    const pg = el('g', {}, svg);
    const plate = [[0, 0], [7.2, 0], [7.2, 4.2], [0, 4.2]];
    el('ellipse', { cx: P(3.6, 2.1)[0], cy: P(3.6, 2.1)[1] + 14, rx: 170, ry: 48, fill: d.pool }, pg);
    el('polygon', { points: P.pts(plate), fill: 'rgba(240,164,88,.07)', stroke: C.amberLine, 'stroke-width': 1.3 }, pg);
    el('polygon', { points: P.pts(plate.map(q => [q[0], q[1], -0.25])), fill: 'none', stroke: C.amberDim, 'stroke-width': 1 }, pg);
    const items = [];
    order.forEach((row, j) => row.forEach((tool, i) => items.push({ tool, anchor: [0.85 + i * 1.38 + (row.length === 3 ? 1.38 : 0), 0.75 + j * 1.35], state: exposed.has(tool) ? 'lit' : 'key' })));
    items.sort((a, b) => P.depth(a.anchor[0], a.anchor[1]) - P.depth(b.anchor[0], b.anchor[1]));
    const pos = {};
    for (const a of items) pos[a.tool] = H.brick(svg, P, a, { px, bloom: d.bloom, size: .62, keyOpacity: .6 }).top;
    const e = E.endpoints.find(x => x.tool === 'state');
    H.callout(svg, pos.state, [18, 254], e.m, e.p, { fs: 12.5, note: 'read at 09:41:04' , noteFill: C.amber });
    text(svg, w - 18, 254, `${E.count} endpoints · 6 taken`, { 'font-family': FONT.mono, 'font-size': 11, fill: C.mute, 'text-anchor': 'end' });

    // what matters: the two disputes, the moment's one accent
    let y = 312;
    el('circle', { cx: 24, cy: y - 5, r: 5, fill: C.accent }, svg);
    text(svg, 36, y, '2 deadlines in dispute', { 'font-family': FONT.theo, 'font-size': 16, 'font-weight': 700, fill: C.white });
    y += 14;
    for (const c of Q.conflicts) {
      const ch = 82, cg = el('g', {}, svg);
      el('rect', { x: 14, y, width: w - 28, height: ch, rx: 8, fill: 'rgba(255,90,60,.07)', stroke: 'rgba(255,90,60,.55)', 'stroke-width': 1.2 }, cg);
      text(cg, 26, y + 21, c.what, { 'font-family': FONT.theo, 'font-size': 12.5, 'font-weight': 600, fill: '#ece3d4' });
      const colW = (w - 28 - 24 - 26) / 2;
      [[c.a, 26], [c.b, 26 + colW + 26]].forEach(([[src, date], x]) => {
        text(cg, x, y + 48, date, { 'font-family': FONT.theo, 'font-size': 17, 'font-weight': 700, fill: C.white });
        text(cg, x, y + 68, src, { 'font-family': FONT.theo, 'font-size': 11, fill: '#b9ab96' });
      });
      text(cg, 26 + colW + 6, y + 49, '≠', { 'font-family': FONT.theo, 'font-size': 18, 'font-weight': 700, fill: C.accent });
      y += ch + 10;
    }
    // his line
    const words = el('g', {}, svg);
    W2.bell(words, 28, h - 112, 17, '#f2c14e');
    W2.wrap(words, 44, h - 104, '“' + say + '”', w - 62, 25, { 'font-family': FONT.theo, 'font-size': 19.5, 'font-weight': 300, fill: C.white });
  }

  window.THEO_SCENES = { handoverWide, handoverTall, buildTall, quorumTall, PATHS };
})();
