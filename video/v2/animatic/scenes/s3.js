/* 3 · Monday. Mon 23 Nov, 08:52. Time-lapse: from the dark desk, daylight sweeps in and the props swap (Theo's things
 * gone; tea in the OKAYEST NEPHEW mug, Martin's glasses, rag, job card) -> the screen clock, 08:52 (shop-pc-04, pulling
 * out to Theo's Back Office) -> Martin's world (worlds2 martin-key, the plan only: his walk from the job board, 08:53,
 * to drawer 1, 08:54, and the pads shortfall; the 08:55 key and card stay out of frame until scene 4) -> the shelf:
 * drawer 1 pulled out, one pair of pads. */
(function () {
  const C = CUES.scenes[2], S = C.start, E = C.end;
  let run, sw;
  Scene({
    id: '3', start: S, end: E, fadeIn: 0,
    build(root) {
      run = seq(root, [
        { src: 'world/02_medium_night.png', at: S, cam: [S, 960, 600, 1.12], grade: 'brightness(.16)' },
        { src: 'world/04_medium_monday.png', at: S + .35, fi: 1.5,
          cam: [[S + .35, 960, 600, 1.12], [S + 1.9, 960, 640, 1.06], [M('clock'), 1180, 830, 1.5]],
          grade: t => `brightness(${lerp(1.35, 1, easeInOutSine(P(t, S + .6, 1.6))).toFixed(3)})` },
        { src: 'look/shop-pc-04-shop-jobs.png', at: M('clock'), fi: .3,
          cam: [[M('clock'), 1640, 920, 3.0], [V(9) + .3, 1640, 920, 3.0], [M('martin_world') + .1, 960, 540, 1.0]] },
        { src: 'worlds/martin-key.png', at: M('martin_world'), fi: .5,
          cam: [[M('martin_world'), 530, 610, 1.8], [M('walk'), 520, 700, 1.95], [M('pads_callout'), 610, 330, 1.9], [M('shelf'), 640, 310, 1.95]] },
        { src: 'world/x_shelf_monday.png', at: M('shelf'), fi: .35, cam: [[M('shelf'), 700, 420, 1.15], [E, 560, 340, 1.35]] },
      ], E);
      sw = sweep(root, { angle: 100, color: 'rgba(255,240,214,.6)' });
    },
    render(t) { run.render(t); sw.render(t, S + .2, S + 2.6, .9); },
  });
})();
