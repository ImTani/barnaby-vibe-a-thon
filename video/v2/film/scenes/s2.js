/* 2 · The handover. Thu 19 Nov, night. Props that say who Theo is (the 2009 photo, the calendar with Friday circled,
 * the moving box) -> "Seventeen years." -> the shop PC LIVE: he closes the nine tabs one by one (each tab folds away,
 * the memory needle sinks), the browser goes, the desktop at 21:47 -> the brass bell: Barnaby arrives -> Theo's view
 * LIVE (worlds2 theo-handover-1-reading): Synapse's scan plane sweeps the workshop, the endpoints appearing behind it,
 * the count climbing, Theo's line printed as he says it -> six light up, one by one, each named (theo-handover-2),
 * Barnaby's line typed as he speaks -> the same beat, modest, in his window on the 2009 desktop (theo-handover-pc) ->
 * desk details -> the key on the keyboard, the lamp clicks off. */
(function () {
  const C = CUES.scenes[1], S = C.start, E = C.end, FI = .35;
  const TABS = ['shop', 'supplier', 'sms', 'xls', 'parts', 'invoices', 'email', 'bank', 'cal'];
  let run, shop, X = null, BW = null, bellWin, bellMark;
  const ct = () => M('close_tabs');
  // the i-th close (0..8), on the cue sheet's own tab_close sounds (the layout's .25 + i * .2 if there are none)
  const CLOSES = () => { const c = sfxAll('tab_close', ct() - .5, ct() + 20); return c.length === 9 ? c : [...Array(9)].map((_, i) => ct() + .25 + i * .2); };
  const closeAt = i => CLOSES()[i];
  const FOLD = .15;
  function shopState(t) {
    let n = 9, fold = 1;
    for (let i = 0; i < 9; i++) {
      const c = closeAt(i);
      if (t >= c) n = 8 - i;
      else if (t >= c - FOLD) { fold = 1 - (t - (c - FOLD)) / FOLD; break; }
      else break;
    }
    const k = 1 - n / 9;                                  // how much has closed
    const st = { preset: 'tabs', secs: 31 + Math.floor(Math.max(0, t - ct())),
      ram: +lerp(.93, .36, easeInOutSine(clamp((t - closeAt(0)) / (closeAt(8) + .25 - closeAt(0))))).toFixed(4),
      cpu: +clamp(.09 + CLOSES().reduce((a, c) => a + .18 * (t >= c ? Math.exp(-6 * (t - c)) : 0), 0) + .04 * (1 - k), 0, .9).toFixed(4) };
    // with five or more tabs the old browser hides the close box: those go with Ctrl+W, the hand still on the mouse;
    // once a close box shows, his cursor clicks it (at human pace: a close he hasn't time to reach goes by keyboard)
    const rest = [690, 318], clicks = [];
    if (X) for (let i = 5; i <= 8; i++) {
      const gap = closeAt(i) - (clicks.length ? clicks[clicks.length - 1].t : closeAt(4));
      if (gap >= .55) { const x = X[9 - i]; clicks.push({ t: closeAt(i) - FOLD, x: x[0], y: x[1] }); }
    }
    const c = clicks.length ? hand(t, [ct(), rest[0], rest[1]], clicks, [closeAt(8) + 1.2, rest[0] + 40, rest[1] + 120]) : rest;
    st.cursor = { x: +c[0].toFixed(2), y: +c[1].toFixed(2) };
    if (n === 0) Object.assign(st, { browser: false, tabs: [], barnaby: t >= M('bell_arrive') - .05 ? 'frame' : 'off' });
    else Object.assign(st, { tabs: TABS.slice(0, n), active: TABS[n - 1], tabIn: +easeInOutSine(fold).toFixed(4) });
    return st;
  }
  Scene({
    id: '2', start: S, end: E, fadeIn: 0,
    build(root) {
      const sweepA = M('reading') + .1, sweepB = M('six_lit') - .9;
      const SIX = M('six_lit') + .2;
      run = seq(root, [
        // 2.1 the photo: a very slow push (memory); 2.2 the calendar, held; 2.3 the desk at night for "Seventeen years."
        { src: 'world/photo_2009.png', at: S, cam: move(S + .3, M('calendar') - S - .5, [750, 550, 1.04], [730, 540, 1.12], 0) },
        { src: 'world/x_board_night.png', at: M('calendar'), cam: hold(400, 620, 1.55) },
        { src: 'world/02_medium_night.png', at: M('box'), cam: hold(960, 610, 1.08) },
        // 2.4 the tabs close (locked); 2.5 on the bell, Barnaby's window opens on the desktop, his mark ringing
        { src: 'live/shop', at: ct(), cam: [960, 540, 1], state: t => shopState(t),
          build: l => { bellWin = el('div', {}, l); css(bellWin, { position: 'absolute', display: 'none', background: '#14110E' });
            bellMark = el('div', { html: markSVG('#D3A14A') }, bellWin); css(bellMark, { position: 'absolute', width: '150px', height: '150px' }); },
          over: t => {
            if (!BW || t < M('bell_arrive') - .05) { bellWin.style.display = 'none'; return; }
            const k = easeOutCubic(clamp((t - M('bell_arrive') + .05) / .35));
            css(bellWin, { display: 'block', left: BW[0] + 'px', top: BW[1] + 'px', width: BW[2] + 'px', height: BW[3] + 'px', opacity: k.toFixed(3) });
            css(bellMark, { left: (BW[2] / 2 - 75) + 'px', top: (BW[3] / 2 - 95) + 'px' });
            markAnim(bellMark, t, sfxT('bell', M('bell_arrive')));
          } },
        // 2.6 Theo's hologram (held): the scan, the six; 2.7 the same, modest, on the 2009 PC (locked)
        { src: 'comp/theo-handover-1-reading', at: M('reading'), cam: [960, 540, 1],
          state: t => ({ scan: +lerp(-.6, 20.6, easeInOutSine(clamp((t - sweepA) / (sweepB - sweepA)))).toFixed(3),
            heardK: +clamp((t - V(5)) / (VE(5) - V(5) - .1)).toFixed(3) }) },
        { src: 'comp/theo-handover-2-taken', at: M('six_lit'), cam: [960, 540, 1],
          state: t => ({ lit: +clamp((t - SIX) / .26, 0, 6).toFixed(3), counts: +clamp((t - SIX - 1.6) / .4).toFixed(3),
            sayK: +clamp((t - V(6)) / (VE(6) - V(6) - .1)).toFixed(3) }) },
        { src: 'comp/theo-handover-pc', at: M('old_pc'), cam: [960, 540, 1],
          state: t => ({ lit: +clamp((t - M('old_pc') - .2) / .16, 0, 6).toFixed(3), sayK: +clamp((t - V(6)) / (VE(6) - V(6) - .1)).toFixed(3) }) },
        // 2.8 back to the room: the desk at night for "It's Theo..." / "Noted."; 2.9 the key (Blender's s2_key_lamp)
        { src: 'world/02_medium_night.png', at: M('desk_detail'), cam: hold(960, 620, 1.1) },
        { src: 'world/03_keys_night.png', at: M('key'), cam: move(M('key') + .2, 1.6, [760, 700, 1.1], [700, 800, 1.3], 0),
          grade: t => `brightness(${lerp(1, .16, easeOutCubic(P(t, M('lamp_off'), .15))).toFixed(3)})` },
      ], E);
      shop = run.list[3].s;
    },
    ready() {
      // the close box on the active (last) tab with n = 1..4 tabs open (logical px)
      const w = shop.win(), pc = w.pc, d = w.document;
      X = [];
      for (let n = 1; n <= 4; n++) {
        pc.render(pc.preset('tabs', { tabs: TABS.slice(0, n), active: TABS[n - 1], cursor: null }));
        const r = d.querySelector('.tab.on .tx').getBoundingClientRect();
        X[n] = [(r.left + r.width * .45) / 1.5, (r.top + r.height * .5) / 1.5];
      }
      // Barnaby's window on the night desktop: its client area (1920x1080 px), where his bell rings
      pc.render(pc.preset('desktop', { date: '2026-11-19', time: '21:47', barnaby: 'frame', cursor: null }));
      const c = d.querySelector('#barnaby-client').getBoundingClientRect();
      BW = [c.left, c.top, c.width, c.height];
    },
    render(t) { run.render(t); },
  });
})();
