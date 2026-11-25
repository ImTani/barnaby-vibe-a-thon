/* 6 · A room Theo never built. Mon 23 Nov, 16:08-16:21. Late light on the desk -> the one sticky note on the bezel ->
 * the tab "Reports (coming soon!!)" (shop-pc-06, 16:08) -> Martin at the desk -> the code, written line by line, and a
 * row of checks turning green (stand-in: Theo's panel of worlds2 same-butler, revealed line by line; the code on the
 * 3D monitor is not rendered yet) -> Martin's glasses by the keyboard -> his click (x_mouse_monday) -> Theo's system
 * reloads (16:16, captured) and the tab now says Reports (shop-pc-07) -> same butler, three worlds (worlds2
 * same-butler, 16:16) -> the new Workload room on Martin's plan (martin-build) -> Dev -> Priya (shop-pc-08, 16:21). */
(function () {
  const C = CUES.scenes[5], S = C.start, E = C.end, FI = .4;
  const LATE = 'sepia(.35) saturate(1.15) hue-rotate(-12deg) brightness(.93)';
  const SB = 'worlds/same-butler.png', MB = 'worlds/martin-build.png';
  let run, rv = {};
  Scene({
    id: '6', start: S, end: E, fadeIn: FI,
    build(root) {
      const navCam = [[M('reload'), 720, 400, 2.0], [M('tab_change') + 1.2, 740, 440, 1.6]];
      const jobsCam = [[M('reassign') - .1, 600, 830, 1.75], [E, 560, 830, 1.9]];
      const n37 = VE(37) - V(37);
      run = seq(root, [
        { src: 'world/04_medium_monday.png', at: S - FI, grade: LATE, cam: [[S - FI, 960, 600, 1.08], [M('sticky'), 940, 720, 1.5]] },
        { src: 'world/04_medium_monday.png', at: M('sticky'), fi: .35, grade: LATE, cam: [[M('sticky'), 945, 760, 3.0], [M('soon_tab'), 955, 775, 3.4]] },
        { src: 'look/shop-pc-06-shop-reports-soon.png', at: M('soon_tab'), fi: .3, cam: [[M('soon_tab'), 960, 540, 1.0], [V(30), 820, 380, 1.7], [VE(30) + .2, 800, 400, 1.75]] },
        { src: 'world/04_medium_monday.png', at: VE(30) + .15, fi: .3, grade: LATE, cam: [[VE(30) + .15, 880, 640, 1.5], [M('code'), 845, 625, 1.95]] },
        { src: SB, at: M('code'), fi: .4, cam: [[M('code'), 314, 672, 3.06], [M('glasses'), 314, 700, 3.12]],          // framed below "added 16:16 · Martin clicked" (not yet true)
          build: l => {
            rv.code = reveal(l, SB, [[36, 578, 610, 601], [36, 611, 610, 634], [36, 644, 610, 667], [36, 682, 512, 703]], { a: M('code') + .3, b: M('checks') - .25,
              grads: [['#16100B', '#0A0908 50%', '#0A0908'], ['#17110B', '#0A0908 50%', '#0A0908'], ['#19130C', '#0A0908 50%', '#0A0908'], ['#1B140C', '#0C0A08 50%', '#0A0908']] });
            rv.checks = reveal(l, SB, [[36, 742, 305, 792], [90, 795, 490, 815]], { a: M('checks'), b: M('checks') + .35,
              grads: [['#1F160E', '#120F0A 50%', '#0B0A08'], ['#1D150D', '#0C0A08 50%', '#0A0908']] });
          },
          over: t => { rv.code.render(t); rv.checks.render(t); } },
        { src: 'world/04_medium_monday.png', at: M('glasses'), fi: .35, grade: LATE, cam: [[M('glasses'), 600, 860, 2.0], [M('glasses') + 3.5, 700, 880, 2.1]] },
        { src: 'world/04_medium_monday.png', at: M('glasses') + 3.5, fi: .4, grade: LATE, cam: [[M('glasses') + 3.5, 900, 640, 1.25], [V(35) + 1.6, 860, 640, 1.5]] },
        { src: 'world/x_mouse_monday.png', at: V(35) + 1.6, fi: .3, grade: LATE, cam: [[V(35) + 1.6, 980, 560, 1.0], [M('reload'), 960, 580, 1.12]] },
        { src: 'scr/s6_reload.jpg', at: M('reload'), cam: navCam },
        { src: 'look/shop-pc-07-shop-reports.png', at: M('tab_change'), cam: navCam },
        { src: SB, at: M('new_room'), fi: .4, cam: [[M('new_room'), 960, 540, 1.0], [V(37) + 3.6, 960, 540, 1.03]],
          build: l => { rv.sb = reveal(l, SB, [[722, 986, 1170, 1015], [722, 1020, 801, 1046]], { color: '#F5F2EA', a: V(37), b: V(37) + n37 * 51 / 115 }); },
          over: t => rv.sb.render(t) },
        { src: MB, at: V(37) + 3.6, fi: .5, cam: [[V(37) + 3.6, 960, 540, 1.0], [M('reassign'), 980, 520, 1.05]],
          build: l => { rv.mb = reveal(l, MB, [[1428, 356, 1832, 384], [1426, 395, 1812, 423], [1426, 435, 1811, 463], [1426, 475, 1656, 496]], { color: '#F5F2EA', a: V(37), b: VE(37) - .1, chars: [31, 32, 30, 17] }); },
          over: t => rv.mb.render(t) },
        { src: 'scr/s6_reassign_0.jpg', at: M('reassign') - .1, fi: .25, cam: jobsCam },
        { src: 'scr/s6_reassign_4.jpg', at: M('reassign') + .35, cam: jobsCam },
        { src: 'look/shop-pc-08-shop-jobs-after.png', at: M('reassign') + .6, cam: jobsCam },
        { src: 'scr/s6_reassign_1.jpg', at: M('reassign') + 1.1, fi: .3, cam: jobsCam },
      ], E);
    },
    render(t) { run.render(t); },
  });
})();
