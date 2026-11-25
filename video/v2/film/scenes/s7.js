/* 7 · Priya, day one. Tue 24 Nov, 08:34. The desk again with her things (05_medium_tuesday: the toolroll, the PRIYA
 * cup, the helmet on the chair) -> Priya's world LIVE (worlds2 priya-tuesday): her two job tags slide onto her bench,
 * Barnaby's answer typing as he says it -> "What else can this thing do?" -> her jobs, the parts they need, who's
 * collecting (the list comes up as he says it) and Theo's README slip, dropping in as he quotes it -> "Noted." */
(function () {
  const C = CUES.scenes[6], S = C.start, E = C.end, FI = .4;
  let run;
  Scene({
    id: '7', start: S, end: E, fadeIn: 0,
    build(root) {
      const tags = M('priya_world') + .15, col = V(42) + 2.3, slip = M('readme_note') + .15;
      const st = t => ({ cards: +clamp((t - tags) / .62, 0, 2).toFixed(3), say: +clamp((t - V(40)) / (VE(40) - V(40) - .1)).toFixed(3),
        rc: +clamp((t - col) / .6).toFixed(3), note: +clamp((t - slip) / .55).toFixed(3) });
      run = seq(root, [
        { src: 'world/05_medium_tuesday.png', at: S, cam: hold(960, 600, 1.12) },
        { src: 'comp/priya-tuesday', at: M('priya_world'), state: st, cam: move(M('readme_note') - .1, 1.3, [960, 540, 1], [1600, 560, 1.75], 0) },
        { src: 'world/05_medium_tuesday.png', at: V(43), cam: hold(1150, 600, 1.2) },
      ], E);
    },
    render(t) { run.render(t); },
  });
})();
