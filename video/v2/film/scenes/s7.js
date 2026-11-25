/* 7 · Priya, day one. Tue 24 Nov, 08:34. The desk again with her things (05_medium_tuesday: the toolroll, the PRIYA
 * cup, the helmet on the chair) -> Priya's world (worlds2 priya-tuesday: her bench, 4471/4472, 08:34) -> "What else can
 * this thing do?" -> her jobs, the parts they need, who's collecting, and Theo's README note -> "Noted." */
(function () {
  const C = CUES.scenes[6], S = C.start, E = C.end, FI = .4;
  const PR = 'worlds/priya-tuesday.png';
  let run, rv;
  Scene({
    id: '7', start: S, end: E, fadeIn: FI,
    build(root) {
      run = seq(root, [
        { src: 'world/05_medium_tuesday.png', at: S - FI, cam: [[S - FI, 520, 690, 1.75], [V(39) + 1.2, 1150, 620, 1.55], [M('priya_world'), 1400, 640, 1.75]] },
        { src: PR, at: M('priya_world'), fi: .35, cam: [[M('priya_world'), 700, 400, 1.35], [VE(40), 760, 420, 1.4]],
          build: l => { rv = reveal(l, PR, [[126, 192, 954, 238]], { color: '#ECE7DD', a: V(40), b: VE(40) - .1 }); },
          over: t => rv.render(t) },
        { src: 'world/05_medium_tuesday.png', at: VE(40) + .15, cam: [[VE(40) + .15, 980, 560, 1.2], [V(42), 900, 520, 1.35]] },
        { src: PR, at: V(42) - .1, fi: .3,
          cam: [[V(42) - .1, 650, 470, 1.5], [V(42) + 1.9, 700, 560, 1.6], [V(42) + 3.4, 1500, 440, 1.8], [M('readme_note') + .5, 1620, 680, 2.2], [VE(42) + .2, 1620, 690, 2.3]] },
        { src: 'world/05_medium_tuesday.png', at: VE(42) + .2, fi: .3, cam: [[VE(42) + .2, 1300, 600, 1.3], [E, 1280, 600, 1.35]] },
      ], E);
    },
    render(t) { run.render(t); },
  });
})();
