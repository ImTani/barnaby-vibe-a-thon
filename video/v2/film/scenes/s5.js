/* 5 · The same four steps. Mon afternoon. Light slides across the desk; the clunk of the repair stand (heard). Martin's
 * world LIVE (worlds2 martin-build, before the Workload room exists): "Sofia's bike's done." in the side panel,
 * Barnaby's answer typing as he says it, the two quick cards from the script sliding in ("Let Barnaby text
 * customers." "Let Barnaby mark bikes ready."); "Go on." -> the cursor clicks Allow on each -> on the plan, Barnaby
 * walks the four stops of a hand-back (the job, the customer, a text, the status) and back to the stand; at each clunk
 * (Kwame's, Jana's) a ring at Ravi's stand and the same walk, quicker each time, all on the plan -> "the same four
 * steps" (the stops pulse in turn) ->
 * "Give me a moment." -> the passage draws through them: Hand back a bike + the script's engine note -> Tom's
 * Brompton (Dev's job 4481: the ring at Dev's stand, Barnaby goes over): one step along the passage. */
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
    id: '5', start: S, end: E, fadeIn: 0,
    build(root) {
      // the walks, quicker each time, timed by their footsteps on the cue sheet (the third has none: quicker still)
      const stepsEnd = (a, b) => { const st = sfxAll('step', a - .05, b); return st.length ? st[st.length - 1] + .25 : a + 1; };
      const w1 = Math.min(stepsEnd(M('walk1'), M('clunk2')), M('clunk2') - .05) - M('walk1');
      const w2 = Math.min(stepsEnd(M('walk2'), M('clunk3')), M('clunk3') - .05) - M('walk2');
      const walks = [[M('walk1'), w1], [M('walk2'), w2], [M('walk3') + .05, Math.max(.5, .72 * w2)]];
      const four = V(23) + 2.0;                                                               // "...the same four steps"
      const pa = M('passage') + .05, pd = .85, w4 = M('walk4');
      // Martin's world, locked: the whole of it for Sofia's cards; then, as Barnaby sets off, a cut to the shop floor
      // (counter to workshop), framed once: the walks, the passage and Tom's step all happen inside that frame
      // a bike comes off a stand: Kwame's 4490 and Jana's 4488 are Ravi's, Tom's 4481 is Dev's (shop-data.js)
      const RAVI = [10.6, 6.9], DEV = [8.2, 6.9];
      const CLUNKS = [[M('clunk2'), RAVI], [M('clunk3'), RAVI], [M('clunk4'), DEV]];
      const TOM = [DEV, [8.2, 6.09]].concat(PASSAGE.slice(1));                               // from Dev's stand onto the passage
      function planState(t) {
        let walk = -1;                                    // which loop is up, and how far along
        for (const [a, d] of walks) if (t >= a - .02) walk = clamp((t - a) / d);
        const w = walk < 0 ? 0 : easeInOutSine(walk);
        const after = t >= pa;
        const st = { room: 0, side: 'handback', time: '14:20', foot: '', martinSay: t >= V(20) ? 'Go on.' : undefined, passage: +easeInOutCubic(clamp((t - pa) / pd)).toFixed(4),
          say: +clamp((t - V(19)) / (VE(19) - V(19) - .1)).toFixed(3), cards: +clamp((t - M('cards2')) / .5, 0, 2).toFixed(3),
          press: [+pressAt(t, sfxT('mouse_click', M('click_text'))).toFixed(3), +pressAt(t, sfxT('mouse_click', M('click_ready'))).toFixed(3)] };
        if (walk >= 0 && !after) {
          st.route = MCUT(ROUTE, w).map(p => [+p[0].toFixed(3), +p[1].toFixed(3)]);
          st.stops = STOPS.filter(s => w >= frac(s[0]) - 1e-6).map(s => [ROUTE[s[0]][0], ROUTE[s[0]][1], s[1], s[2], s[3]]);
          st.routeOpacity = +(walk >= 1 ? lerp(1, .55, clamp((t - walks[2][0] - walks[2][1]) / .6)) : 1).toFixed(3);
          const p = along(ROUTE, w); st.marker = [+p[0].toFixed(3), +p[1].toFixed(3)];
        } else if (after) {                               // the passage: his walk fades, the band draws, Tom's in one step
          const fade = 1 - clamp((t - pa) / .5);
          if (fade > 0) { st.route = ROUTE; st.stops = STOPS.map(s => [ROUTE[s[0]][0], ROUTE[s[0]][1], s[1], s[2], s[3]]); st.routeOpacity = +(.55 * fade).toFixed(3); }
          // to Dev's stand on Tom's clunk, then the one step: from there along the passage to the counter
          const g = easeInOutSine(clamp((t - M('clunk4') - .05) / .5)), k = easeInOutCubic(clamp((t - w4) / .7));
          const p = k > 0 ? along(TOM, k) : [lerp(RAVI[0], DEV[0], g), lerp(RAVI[1], DEV[1], g)];
          st.marker = [+p[0].toFixed(3), +p[1].toFixed(3)];
        } else st.marker = [10.6, 6.9];
        return st;
      }
      const planItem = o => { let cur, pulses, stand; return Object.assign({ src: 'comp/martin-build', state: planState,
        build: l => { cur = cursor(l, 1.5); pulses = STOPS.map(() => { const e = el('div', {}, l); css(e, { borderRadius: '50%', border: '4px solid #E2B54E', display: 'none' }); return e; });
          stand = el('div', {}, l); css(stand, { borderRadius: '50%', border: '4px solid #83400F', display: 'none' }); },
        over: (t, l) => {
          // the clunk: the next bike off Ravi's stand (the workshop's own ink), as Martin calls it
          const cl = CLUNKS.find(c => P(t, c[0], .6) > 0 && P(t, c[0], .6) < 1), ck = cl ? P(t, cl[0], .6) : null;
          if (ck == null) stand.style.display = 'none';
          else { const r = lerp(18, 64, easeOutCubic(ck)), p = [90 + cl[1][0] * 60, 286 + cl[1][1] * 60];
            css(stand, { display: 'block', left: (p[0] - r) + 'px', top: (p[1] - r) + 'px', width: 2 * r + 'px', height: 2 * r + 'px', opacity: (.9 * (1 - ck)).toFixed(3) }); }
          // the four stops pulse in turn as he says "the same four steps"
          STOPS.forEach((s, i) => {
            const a = four + i * .32, k = P(t, a, .7), e = pulses[i];
            if (k <= 0 || k >= 1) { e.style.display = 'none'; return; }
            const p = [90 + ROUTE[s[0]][0] * 60, 286 + ROUTE[s[0]][1] * 60], r = lerp(10, 34, easeOutCubic(k));
            css(e, { display: 'block', left: (p[0] - r) + 'px', top: (p[1] - r) + 'px', width: 2 * r + 'px', height: 2 * r + 'px', opacity: (1 - k).toFixed(3) });
          });
          const c1 = sfxT('mouse_click', M('click_text')), c2 = sfxT('mouse_click', M('click_ready')), from = Math.min(V(20), c1 - 1.3);
          if (!A || t < from || t > c2 + .9) { cur.at(0, 0, false); return; }
          const c = hand(t, [from, A[0][0] + 220, A[0][1] + 260], [{ t: c1, x: A[0][0], y: A[0][1] }, { t: c2, x: A[1][0], y: A[1][1] }], [c2 + .9, A[1][0] - 60, A[1][1] + 110]);
          cur.at(c[0], c[1], true);
        } }, o); };
      run = seq(root, [
        { src: 'world/04_medium_monday.png', at: S, grade: AFT, keepGrade: true, cam: hold(960, 600, 1.1) },
        planItem({ at: V(19) - .1, fi: .35, cam: [960, 540, 1] }),
        planItem({ at: M('walk1'), cam: move(M('passage') + .05, 2.2, [620, 540, 1.62], [600, 525, 1.8], 0) }),   // 5.4 the slow push as it forms
      ], E, { scene: 5 });
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
