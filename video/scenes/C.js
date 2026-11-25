/* Scene C: Monday (30–47 s). Meet Martin.
 * Theo's 2009 window carries over from B and widens; Barnaby's display slides in over its right edge. Martin asks
 * which repairs are due tomorrow and whether they're short on parts; six read calls (the real ones, from
 * DATA.turns[0]) tick into the trace while the matching rows in the 2009 window flicker as they're read; Barnaby
 * answers, and from 41.0 Anika's brake job (row 4478) is marked in soft yellow.
 */
(function () {
  const START = 30, END = 47;
  const VO = { martin: 31.2, barnaby: 38.6 };                       // cues.json -> voice
  const ASK = 'Which repairs are due tomorrow, and are we short on parts?', ASK_DUR = 3.67;            // manifest
  const SAY = 'Five are due tomorrow. Only one is short: Anika’s brake job needs two pairs of pads, and we have one.';
  const SAY_DUR = 7.7;                                                // manifest
  const ROW_T = [35.2, 35.8, 36.4, 37.0, 37.6, 38.2];                 // trace rows (tick sfx on each)
  const HL_AT = 41.0, HL_ROW = 3;                                     // shop row 4478 (index 3)
  const SHOP_FROM = { x: 110, w: 1000, s: 1.02 };                     // where B leaves it (B's 2% drift included)
  const SHOP_TO = { x: 80, w: 1100, s: 1 }, SHOP_Y = 150;
  let shop, hd, chapter, rows = [], readRow = [], hlCall = -1;

  // readable args: jobs_due {day: tomorrow} (as in the storyboard), job_detail 4471, ...
  const fmtArgs = c => {
    if (c.tool === 'jobs_due') return '{day: tomorrow}';
    const ks = Object.keys(c.input || {});
    if (ks.length === 1 && /_id$/.test(ks[0])) return String(c.input[ks[0]]);
    return '{' + ks.map(k => `${k}: ${c.input[k]}`).join(', ') + '}';
  };

  Scene({
    id: 'C', start: START, end: END, drift: .02,

    build(root) {
      // reserve the request and answer lines so the panel doesn't jump when they start; an opaque panel so the 2009
      // window's right-hand columns don't show through where the HUD overlaps it
      el('style', { text: '#scene-C .hud{background:#0E1117}#scene-C .hud-you{min-height:25px}#scene-C .hud-say{min-height:70px}' }, root);
      shop = shop2009({ parent: root, x: SHOP_FROM.x, y: SHOP_Y, w: SHOP_FROM.w, page: 'Jobs' });
      chapter = chip('Monday &middot; 8:52am', COL.brass, root, 'position:absolute;left:80px;top:72px;font-size:24px;padding:7px 20px;letter-spacing:.02em');

      hd = hud({ parent: root, x: 1000, y: 120, w: 840 });
      // BELL() reuses one gradient id per size, and the first copy lives in B's HUD; once B is display:none Chrome
      // drops that gradient and this bell renders blank. Give ours a unique id.
      const lg = hd.el.querySelector('linearGradient');
      if (lg) {
        const old = lg.id; lg.id = 'bell-C-' + old;
        hd.el.querySelectorAll(`[fill="url(#${old})"]`).forEach(e => e.setAttribute('fill', `url(#${lg.id})`));
      }
      const calls = DATA.turns[0].calls.slice(0, ROW_T.length);
      rows = calls.map(c => traceRow(hd.trace, { kind: 'read', name: c.tool, args: fmtArgs(c), tag: 'read' }));
      // which row of the 2009 window each job_detail call reads (-1 for jobs_due)
      readRow = calls.map(c => c.input && c.input.job_id != null ? SHOP_ROWS.findIndex(r => r[0] === String(c.input.job_id)) : -1);
      hlCall = readRow.indexOf(HL_ROW);                                 // the job_detail 4478 call
    },

    render(t) {
      // the 2009 window: starts exactly where B left it, then widens to C's framing as the HUD arrives
      const k = E(t, 30.25, .9, easeInOutCubic);
      const x = lerp(SHOP_FROM.x, SHOP_TO.x, k), sc = lerp(SHOP_FROM.s, SHOP_TO.s, k);
      css(shop.el, {
        left: x.toFixed(2) + 'px', top: SHOP_Y + 'px', width: lerp(SHOP_FROM.w, SHOP_TO.w, k).toFixed(2) + 'px',
        transformOrigin: `${(960 - x).toFixed(2)}px ${540 - SHOP_Y}px`, transform: `scale(${sc.toFixed(4)})`, opacity: 1,
      });

      // rows flicker pale blue as Barnaby reads them; from 41.0 Anika's brake job (4478) holds a soft yellow
      const hl = .95 * E(t, HL_AT, .7, easeOutCubic);
      shop.cells.forEach((cells, r) => {
        let read = 0;
        readRow.forEach((rr, i) => { if (rr === r && t >= ROW_T[i]) read = Math.max(read, Math.exp(-Math.pow((t - ROW_T[i] - .15) / .32, 2))); });
        const base = r % 2 === 0 ? '#EEF3FB' : '#FFFFFF';
        const y = r === HL_ROW ? hl : 0;
        const bg = y > .005 ? mixColor(base, '#FFF6BF', y) : read > .01 ? mixColor(base, '#D3E3F8', read) : '';
        cells.forEach(td => { td.style.background = bg; });
      });

      // chapter chip
      show(chapter, t, 30.3, .5, { dy: 12, out: 31.6, outD: .4 });

      // Barnaby's display slides in over the window's right edge
      show(hd.el, t, 30.5, .6, { dx: 80, dy: 0 });
      hd.setState(t < 35.0 ? 'listening' : t < VO.barnaby ? 'thinking' : t < VO.barnaby + SAY_DUR + .2 ? 'speaking' : 'listening');

      // Martin's question, typed at his speaking rate
      const n = Math.floor(clamp((t - VO.martin) * ASK.length / (ASK_DUR * .92), 0, ASK.length));
      hd.setYou('Martin', ASK.slice(0, n));

      // six real read calls, 0.6 s apart
      rows.forEach((r, i) => r.render(t, ROW_T[i]));
      // the 4478 call gets a quiet brass mark when the answer reaches Anika
      if (hlCall >= 0) {
        const mk = .9 * E(t, HL_AT, .7, easeOutCubic), r = rows[hlCall].el;
        r.style.background = mk > .005 ? mixColor('#1B202A', '#2A2519', mk) : '';
        r.style.boxShadow = mk > .005 ? `0 0 0 1px ${rgba(COL.brass, .5 * mk)}, 0 0 18px ${rgba(COL.brass, .12 * mk)}` : '';
      }

      // his answer types out timed to the voice line
      hd.say(SAY, t, VO.barnaby, SAY.length / (SAY_DUR * .92));
    },
  });
})();
