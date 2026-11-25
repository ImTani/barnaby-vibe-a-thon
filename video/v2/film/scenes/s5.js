/* 5 · The same four steps. Mon afternoon. Light slides across the desk; a clunk from the repair stand through the
 * doorway (heard: no stand shot exists). Sofia -> Barnaby asks to text her and mark it ready (stand-in: Theo's job
 * list; Martin's two quick cards are not designed yet) -> "Go on." (two clicks) -> the montage cut to each clunk:
 * Kwame's, Jana's (Monday desk details) -> the offer -> "Give me a moment." -> on the plan a passage opens through the
 * rooms: "Hand back a bike" (worlds2 martin-build, framed tight on the shop floor so the 16:16 Workload room and clock
 * stay out of shot) + the script's engine note -> Tom's Brompton: one step. */
(function () {
  const C = CUES.scenes[4], S = C.start, E = C.end, FI = .4;
  const AFT = 'sepia(.22) saturate(1.12) hue-rotate(-6deg) brightness(1.02)';
  const PATH = [[393, 532], [507, 647], [723, 659]];          // martin.js passagePath in plan units -> px (x 90, y 286, s 60)
  let run, sw, note, glow, dot;
  const seglen = PATH.slice(1).map((p, i) => Math.hypot(p[0] - PATH[i][0], p[1] - PATH[i][1]));
  const total = seglen.reduce((a, b) => a + b, 0);
  const along = u => {                                         // point at fraction u of the passage
    let d = u * total;
    for (let i = 0; i < seglen.length; i++) {
      if (d <= seglen[i] || i === seglen.length - 1) { const k = clamp(d / seglen[i]); return [lerp(PATH[i][0], PATH[i + 1][0], k), lerp(PATH[i][1], PATH[i + 1][1], k)]; }
      d -= seglen[i];
    }
  };
  Scene({
    id: '5', start: S, end: E, fadeIn: FI,
    build(root) {
      run = seq(root, [
        { src: 'world/04_medium_monday.png', at: S - FI, grade: AFT, cam: [[S - FI, 1000, 560, 1.08], [V(19) - .1, 900, 620, 1.25]] },
        { src: 'look/shop-pc-04-shop-jobs.png', at: V(19) - .1, fi: .3, cam: [[V(19) - .1, 560, 650, 1.7], [M('click_text') - .2, 900, 700, 1.7]] },
        { src: 'world/x_mouse_monday.png', at: M('click_text') - .2, fi: .15, grade: AFT, cam: [[M('click_text'), 960, 560, 1.05], [M('walk1'), 960, 575, 1.1]] },
        { src: 'world/04_medium_monday.png', at: M('walk1'), fi: .25, grade: AFT, cam: [[M('walk1'), 900, 660, 1.4], [M('clunk2'), 860, 640, 1.65]] },
        { src: 'world/x_pot_monday.png', at: M('clunk2'), grade: AFT, cam: [[M('clunk2'), 960, 560, 1.1], [M('clunk3'), 990, 540, 1.18]] },
        { src: 'world/x_drawer_monday.png', at: M('clunk3'), grade: AFT, cam: [[M('clunk3'), 960, 560, 1.1], [M('walk3') + .3, 930, 560, 1.18]] },
        { src: 'world/04_medium_monday.png', at: M('walk3') + .3, fi: .3, grade: AFT, cam: [[M('walk3') + .3, 1000, 600, 1.15], [M('passage'), 870, 640, 1.5]] },
        { src: 'worlds/martin-build.png', at: M('passage'), fi: .3, cam: [[M('passage'), 572, 682, 2.56], [E, 572, 682, 2.62]],
          build: l => {
            glow = el('div', { html: `<svg width="1920" height="1080" style="overflow:visible"><polyline points="${PATH.map(p => p.join(',')).join(' ')}" fill="none" stroke="#F0CF8F" stroke-width="30" stroke-linecap="round" stroke-linejoin="round" style="filter:blur(6px)"/></svg>` }, l);
            css(glow, { left: '0px', top: '0px', mixBlendMode: 'screen' });
            dot = el('div', {}, l);
            css(dot, { width: '30px', height: '30px', borderRadius: '50%', background: '#D3A14A', boxShadow: '0 0 0 5px #1D1B17, 0 0 18px 6px rgba(240,207,143,.9)' });
          },
          over: t => {
            glow.style.opacity = (.85 * Math.min(easeOutCubic(P(t, M('passage') + .1, .5)), 1 - P(t, M('passage') + 1.0, .9))).toFixed(3);
            const w = M('walk4'), k = P(t, w - .1, .9);       // the fourth hand-back: one step along the passage
            if (k > 0 && k < 1) { const p = along(easeInOutCubic(k)); css(dot, { display: 'block', left: (p[0] - 15).toFixed(1) + 'px', top: (p[1] - 15).toFixed(1) + 'px', opacity: Math.min(1, 6 * k, 6 * (1 - k)).toFixed(3) }); }
            else dot.style.display = 'none';
          } },
      ], E);
      sw = sweep(root, { angle: 105, color: 'rgba(255,226,180,.5)' });
      note = label(root, 'synapse custom · composed from Theo’s own functions · 16 s',
        'left:0;top:996px;width:1920px;height:84px;padding:22px 64px 0;font:500 26px "Cascadia Code","Cascadia Mono",Consolas,monospace;color:#7D766A;letter-spacing:.02em;background:#F5F2EA;border-top:1px solid #E5DED0');
    },
    render(t) {
      run.render(t);
      sw.render(t, S - FI, S + 2.6, .75);
      fadeEl(note, t, M('engine_compose'), E + 1, .35, .2);
    },
  });
})();
