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
  let run;
  const ct = () => M('close_tabs');
  const closeAt = i => ct() + .25 + i * .2;            // the i-th close (0..8), as the sound's tab_close cues
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
      cpu: +clamp(.09 + .18 * Math.exp(-6 * ((t - ct()) % .2)) * (n > 0 && t < closeAt(8) ? 1 : 0) + .04 * (1 - k), 0, .9).toFixed(4) };
    if (n === 0) Object.assign(st, { browser: false, tabs: [], cursor: { x: 700 + 30 * easeOutCubic(P(t, closeAt(8), .8)), y: 330 + 20 * easeOutCubic(P(t, closeAt(8), .8)) } });
    else Object.assign(st, { tabs: TABS.slice(0, n), active: TABS[n - 1], tabIn: +easeInOutSine(fold).toFixed(4),
      cursor: { x: +(690 + wiggle(t, 21, 2.2, 3)).toFixed(2), y: +(318 + wiggle(t, 22, 1.8, 2)).toFixed(2) } });
    return st;
  }
  Scene({
    id: '2', start: S, end: E, fadeIn: FI,
    build(root) {
      const sweepA = M('reading') + .1, sweepB = M('six_lit') - .9;
      const SIX = M('six_lit') + .2;
      run = seq(root, [
        { src: 'world/photo_2009.png', at: S - FI, cam: [[S - FI, 760, 560, 1.04], [M('calendar') + .5, 700, 540, 1.16]] },
        { src: 'world/x_board_night.png', at: M('calendar'), fi: .5, cam: [[M('calendar'), 380, 560, 1.45], [M('box') + .5, 430, 730, 1.9]] },
        { src: 'world/01_wide_night.png', at: M('box'), fi: .5, cam: [[M('box'), 1100, 650, 2.0], [ct() + .3, 1160, 700, 2.35]] },
        { src: 'live/shop', at: ct(), fi: .3, cam: [[ct(), 960, 540, 1.04], [M('desktop_night'), 900, 500, 1.0], [M('bell_arrive'), 900, 520, 1.02]], state: t => shopState(t) },
        { src: 'world/x_bell.png', at: M('bell_arrive') - .05, fi: .2, cam: [[M('bell_arrive'), 900, 620, 1.1], [M('reading'), 860, 660, 1.22]] },
        { src: 'comp/theo-handover-1-reading', at: M('reading') - .25, fi: .4, cam: [[M('reading'), 960, 540, 1.0], [M('six_lit'), 960, 520, 1.06]],
          state: t => ({ scan: +lerp(-.6, 20.6, easeInOutSine(clamp((t - sweepA) / (sweepB - sweepA)))).toFixed(3),
            heardK: +clamp((t - V(5)) / (VE(5) - V(5) - .1)).toFixed(3) }) },
        { src: 'comp/theo-handover-2-taken', at: M('six_lit'), fi: .35, cam: [[M('six_lit'), 960, 540, 1.0], [M('old_pc'), 920, 600, 1.06]],
          state: t => ({ lit: +clamp((t - SIX) / .26, 0, 6).toFixed(3), counts: +clamp((t - SIX - 1.6) / .4).toFixed(3),
            sayK: +clamp((t - V(6)) / (VE(6) - V(6) - .1)).toFixed(3) }) },
        { src: 'comp/theo-handover-pc', at: M('old_pc'), fi: .5, cam: [[M('old_pc'), 1150, 560, 1.0], [M('desk_detail'), 1480, 620, 1.3]],
          state: t => ({ lit: +clamp((t - M('old_pc') - .2) / .16, 0, 6).toFixed(3), sayK: +clamp((t - V(6)) / (VE(6) - V(6) - .1)).toFixed(3) }) },
        { src: 'world/02_medium_night.png', at: M('desk_detail'), fi: .4, cam: [[M('desk_detail'), 560, 830, 1.55], [M('key'), 1300, 820, 1.55]] },
        { src: 'world/03_keys_night.png', at: M('key'), fi: .4, keepGrade: true, cam: [[M('key'), 760, 700, 1.1], [E, 640, 840, 1.35]],
          grade: t => `brightness(${lerp(1, .16, easeOutCubic(P(t, M('lamp_off'), .15))).toFixed(3)})` },
      ], E);
    },
    render(t) { run.render(t); },
  });
})();
