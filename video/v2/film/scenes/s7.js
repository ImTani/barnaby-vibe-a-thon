/* 7 · Priya, day one. Tue 24 Nov, 08:34. The desk again with her things (05_medium_tuesday: the toolroll, the PRIYA
 * cup, the helmet on the chair) -> Priya's world LIVE (worlds2 priya-tuesday): her two job tags slide onto her bench,
 * Barnaby's answer typing as he says it -> "What else can this thing do?" -> her jobs, the parts they need, who's
 * collecting (the list comes up as he says it) and Theo's README slip, dropping in as he quotes it -> "Noted." */
(function () {
  const C = CUES.scenes[6], S = C.start, E = C.end, FI = .4;
  let run;
  Scene({
    id: '7', start: S, end: E, fadeIn: FI,
    build(root) {
      const tags = M('priya_world') + .15, col = V(42) + 2.3, slip = M('readme_note') - .1;
      const st = t => ({ cards: +clamp((t - tags) / .62, 0, 2).toFixed(3), say: +clamp((t - V(40)) / (VE(40) - V(40) - .1)).toFixed(3),
        rc: +clamp((t - col) / .6).toFixed(3), note: +clamp((t - slip) / .55).toFixed(3) });
      run = seq(root, [
        { src: 'world/05_medium_tuesday.png', at: S - FI, cam: [[S - FI, 520, 690, 1.75], [V(39) + 1.2, 1150, 620, 1.55], [M('priya_world'), 1400, 640, 1.75]] },
        { src: 'comp/priya-tuesday', at: M('priya_world'), fi: .35, cam: [[M('priya_world'), 700, 420, 1.3], [VE(40), 760, 430, 1.38]], state: st },
        { src: 'world/05_medium_tuesday.png', at: VE(40) + .15, cam: [[VE(40) + .15, 980, 560, 1.2], [V(42), 900, 520, 1.35]] },
        { src: 'comp/priya-tuesday', at: V(42) - .1, fi: .3, state: st,
          cam: [[V(42) - .1, 650, 470, 1.5], [V(42) + 1.9, 700, 560, 1.6], [col + .2, 1500, 440, 1.8], [M('readme_note') + .5, 1620, 660, 2.15], [VE(42) + .2, 1620, 680, 2.25]] },
        { src: 'world/05_medium_tuesday.png', at: VE(42) + .2, fi: .3, cam: [[VE(42) + .2, 1300, 600, 1.3], [E, 1280, 600, 1.35]] },
      ], E);
    },
    render(t) { run.render(t); },
  });
})();
