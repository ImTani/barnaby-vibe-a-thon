/* 1 · Nine tabs. INT. SHOP BACK OFFICE, THU 19 NOV 21:47 (CONTINUITY). Black, rain; light comes up on the wide; we
 * drift to the 2009 monitor; full screen: the tabs open one after another, the memory needle climbing into the red
 * (look book shop-pc-03; states captured from the shop-pc page). Martin o.s.; Theo: "Tab four." (workload.xls)
 * "No, five." (the Parts list, shop-pc-03b) "It's the one with the spanner." (push to the spanners). */
(function () {
  const C = CUES.scenes[0], S = C.start, E = C.end;
  let run;
  Scene({
    id: '1', start: S, end: E, fadeIn: 0,
    build(root) {
      const tabCam = [[M('screen'), 960, 540, 1.0], [M('tab5_active'), 930, 480, 1.08]];
      const items = [
        { src: 'world/01_wide_night.png', at: S,
          cam: [[M('light_up'), 960, 540, 1.0], [M('medium') + .5, 880, 455, 1.3]],
          grade: t => `brightness(${easeInOutSine(P(t, M('light_up'), 1.8)).toFixed(3)})` },
        { src: 'world/02_medium_night.png', at: M('medium'), fi: .45,
          cam: [[M('medium'), 880, 640, 1.04], [M('screen') + .4, 842, 626, 1.6]] },
        { src: 'scr/s1_tabs_1.jpg', at: M('screen'), fi: .35, cam: tabCam },
      ];
      for (let k = 2; k <= 9; k++) items.push({ src: `scr/s1_tabs_${k}.jpg`, at: M('tab' + k), cam: tabCam });
      items.push({ src: 'scr/s1_tab4.jpg', at: M('tab4_active'), cam: tabCam });
      items.push({ src: 'look/shop-pc-03b-tabs-parts.png', at: M('tab5_active'),
        cam: [[M('tab5_active'), 930, 480, 1.08], [V(3) - .2, 900, 420, 1.14], [E, 800, 235, 1.8]] });
      run = seq(root, items, E);
    },
    render(t) { run.render(t); },
  });
})();
