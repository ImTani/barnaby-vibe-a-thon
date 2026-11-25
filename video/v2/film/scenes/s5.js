/* 5 · The same four steps. Mon afternoon. Light slides across the desk; the clunk of the repair stand (heard). Martin's
 * world LIVE (worlds2 martin-build, before the Workload room exists): "Sofia's bike's done." in the side panel,
 * Barnaby's answer typing as he says it, the two quick cards from the script sliding in ("Let Barnaby text
 * customers." "Let Barnaby mark bikes ready."); "Go on." -> the cursor clicks Allow on each -> on the plan, Barnaby
 * walks the four stops of a hand-back (the job, the customer, a text, the status) and back to the stand; the clunk
 * cuts (Kwame's, Jana's) and the same walk, quicker each time -> "the same four steps" (the stops pulse in turn) ->
 * "Give me a moment." -> the passage draws through them: Hand back a bike + the script's engine note -> Tom's
 * Brompton: one step along the passage. */
(function () {
  const C = CUES.scenes[4], S = C.start, E = C.end, FI = .4;
  const AFT = 'sepia(.22) saturate(1.12) hue-rotate(-6deg) brightness(1.02)';
  // a hand-back, in Theo's building (worlds/data/building.js anchors): from Ravi's stand, the job (job_detail), the
  // customer (search), a text (notify), the status (update_status), back to the stand
  const ROUTE = [[10.6, 6.9], [9.4, 6.9], [7.4, 5.6], [5.6, 4.5], [3.4, 3.3], [4.9, 3.0], [5.6, 4.5], [7.4, 5.6], [11.8, 6.9], [10.6, 6.9]];
  const STOPS = [[1, 'the job', -96, -30], [4, 'the customer', -150, -28], [5, 'a text', 14, -30], [8, 'the status', 14, -30]];
  const PASSAGE = [[10.55, 6.22], [6.95, 6.02], [5.05, 4.1]];
  const seg = ROUTE.slice(1).map((p, i) => Math.hypot(p[0] - ROUTE[i][0], p[1] - ROUTE[i][1])), LEN = seg.reduce((a, b) => a + b, 0);
  const frac = idx => seg.slice(0, idx).reduce((a, b) => a + b, 0) / LEN;
  const along = (path, u) => { const c = MCUT(path, u); return c[c.length - 1]; };
  function MCUT(path, k) {                                // the first k of a polyline (as martin.js cut)
    if (k >= 1) return path;
    const sg = path.slice(1).map((p, i) => Math.hypot(p[0] - path[i][0], p[1] - path[i][1]));
    let d = Math.max(0, k) * sg.reduce((a, b) => a + b, 0); const out = [path[0]];
    for (let i = 0; i < sg.length; i++) {
      if (d >= sg[i]) { out.push(path[i + 1]); d -= sg[i]; continue; }
      const u = sg[i] ? d / sg[i] : 0; out.push([path[i][0] + (path[i + 1][0] - path[i][0]) * u, path[i][1] + (path[i + 1][1] - path[i][1]) * u]); break;
    }
    return out;
  }
  let run, sw, note, plan, A = null;
  Scene({
    id: '5', start: S, end: E, fadeIn: FI,
    build(root) {
      const walks = [[M('walk1'), 1.55], [M('walk2'), .85], [M('walk3') + .05, .62]];       // quicker each time
      const four = V(23) + 2.0;                                                               // "...the same four steps"
      const pa = M('passage') + .05, pd = .85, w4 = M('walk4');
      const planCam = [[V(19) - .1, 1480, 470, 1.6], [M('cards2') + .9, 1500, 480, 1.62], [M('walk1') - .25, 1480, 490, 1.6],
        [M('walk1') + .25, 640, 560, 1.62], [M('clunk2'), 630, 560, 1.68]];
      const plan2 = [[M('walk2'), 640, 560, 1.66], [M('clunk3'), 630, 555, 1.7]];
      const plan3 = [[M('walk3'), 640, 560, 1.66], [four, 600, 540, 1.85], [M('passage'), 590, 520, 1.95], [w4, 600, 520, 2.0], [E, 620, 520, 1.92]];
      function planState(t) {
        let walk = -1;                                    // which loop is up, and how far along
        for (const [a, d] of walks) if (t >= a - .02) walk = clamp((t - a) / d);
        const w = walk < 0 ? 0 : easeInOutSine(walk);
        const after = t >= pa;
        const st = { room: 0, side: 'handback', time: '14:20', foot: '', martinSay: t >= V(20) ? 'Go on.' : undefined, passage: +easeInOutCubic(clamp((t - pa) / pd)).toFixed(4),
          say: +clamp((t - V(19)) / (VE(19) - V(19) - .1)).toFixed(3), cards: +clamp((t - M('cards2')) / .5, 0, 2).toFixed(3),
          press: [+(clamp((t - M('click_text') + .02) / .06) * (1 - clamp((t - M('click_text') - .14) / .14))).toFixed(3),
            +(clamp((t - M('click_ready') + .02) / .06) * (1 - clamp((t - M('click_ready') - .14) / .14))).toFixed(3)] };
        if (walk >= 0 && !after) {
          st.route = MCUT(ROUTE, w).map(p => [+p[0].toFixed(3), +p[1].toFixed(3)]);
          st.stops = STOPS.filter(s => w >= frac(s[0]) - 1e-6).map(s => [ROUTE[s[0]][0], ROUTE[s[0]][1], s[1], s[2], s[3]]);
          st.routeOpacity = +(walk >= 1 ? lerp(1, .55, clamp((t - walks[2][0] - walks[2][1]) / .6)) : 1).toFixed(3);
          const p = along(ROUTE, w); st.marker = [+p[0].toFixed(3), +p[1].toFixed(3)];
        } else if (after) {                               // the passage: his walk fades, the band draws, Tom's in one step
          const fade = 1 - clamp((t - pa) / .5);
          if (fade > 0) { st.route = ROUTE; st.stops = STOPS.map(s => [ROUTE[s[0]][0], ROUTE[s[0]][1], s[1], s[2], s[3]]); st.routeOpacity = +(.55 * fade).toFixed(3); }
          const k = easeInOutCubic(clamp((t - w4) / .7)), p = along([[10.6, 6.9]].concat(PASSAGE), k);
          st.marker = [+p[0].toFixed(3), +p[1].toFixed(3)];
        } else st.marker = [10.6, 6.9];
        return st;
      }
      const planItem = o => { let cur, pulses; return Object.assign({ src: 'comp/martin-build', state: planState,
        build: l => { cur = cursor(l, 1.5); pulses = STOPS.map(() => { const e = el('div', {}, l); css(e, { borderRadius: '50%', border: '4px solid #E2B54E', display: 'none' }); return e; }); },
        over: (t, l) => {
          // the four stops pulse in turn as he says "the same four steps"
          STOPS.forEach((s, i) => {
            const a = four + i * .32, k = P(t, a, .7), e = pulses[i];
            if (k <= 0 || k >= 1) { e.style.display = 'none'; return; }
            const p = [90 + ROUTE[s[0]][0] * 60, 286 + ROUTE[s[0]][1] * 60], r = lerp(10, 34, easeOutCubic(k));
            css(e, { display: 'block', left: (p[0] - r) + 'px', top: (p[1] - r) + 'px', width: 2 * r + 'px', height: 2 * r + 'px', opacity: (1 - k).toFixed(3) });
          });
          if (!A || t < M('click_text') - 1.0 || t > M('click_ready') + .6) { cur.at(0, 0, false); return; }
          const c = path2(t, [[M('click_text') - 1.0, A[0][0] + 220, A[0][1] + 260], [M('click_text') - .06, A[0][0], A[0][1]], [M('click_text') + .12, A[0][0] + 2, A[0][1] + 2],
            [M('click_ready') - .06, A[1][0], A[1][1]], [M('click_ready') + .6, A[1][0] - 120, A[1][1] + 150]]);
          cur.at(c[0], c[1], true);
        } }, o); };
      run = seq(root, [
        { src: 'world/04_medium_monday.png', at: S - FI, grade: AFT, cam: [[S - FI, 1000, 560, 1.08], [V(19) - .1, 900, 620, 1.25]] },
        planItem({ at: V(19) - .1, fi: .35, cam: planCam }),
        { src: 'world/x_pot_monday.png', at: M('clunk2'), grade: AFT, cam: [[M('clunk2'), 960, 560, 1.1], [M('walk2'), 990, 540, 1.16]] },
        planItem({ at: M('walk2') - .05, cam: plan2 }),
        { src: 'world/x_drawer_monday.png', at: M('clunk3'), grade: AFT, cam: [[M('clunk3'), 960, 560, 1.1], [M('walk3'), 930, 560, 1.16]] },
        planItem({ at: M('walk3') - .05, cam: plan3 }),
      ], E);
      plan = run.list[1].s;
      sw = sweep(root, { angle: 105, color: 'rgba(255,226,180,.5)' });
      note = label(root, 'synapse custom · composed from Theo’s own functions · 16 s',
        'left:0;top:996px;width:1920px;height:84px;padding:22px 64px 0;font:500 26px "Cascadia Code","Cascadia Mono",Consolas,monospace;color:#7D766A;letter-spacing:.02em;background:#F5F2EA;border-top:1px solid #E5DED0');
    },
    ready() {
      // the two quick cards' Allow buttons, where they land (comp px = source px)
      const w = plan.win();
      w.COMP.render({ room: 0, side: 'handback', cards: 2 });
      A = [...w.COMP.sideHB.querySelectorAll('.card .yes')].map(b => { const r = b.getBoundingClientRect(); return [r.left + r.width * .45, r.top + r.height * .55]; });
    },
    render(t) {
      run.render(t);
      if (!run.list[0].bl) sw.render(t, S - FI, S + 2.6, .75);                // unless a Blender shot bakes the light in
      fadeEl(note, t, M('engine_compose'), E + 1, .35, .2);
    },
  });
})();
