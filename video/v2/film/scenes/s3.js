/* 3 · Monday. Mon 23 Nov, 08:52. Time-lapse: from the dark desk, daylight sweeps in and the props swap -> the shop PC
 * LIVE (preset shop-jobs): on the gadget clock the second hand sweeps up and the taskbar clock turns 08:51 -> 08:52,
 * then we pull out to Theo's Back Office -> Martin's world LIVE (worlds2 martin-key): Barnaby's mark waits at the job
 * board while Martin asks, then walks his dotted path (the 08:53 stamp as he sets off) through the arch, behind the
 * counter, up to drawer 1 in the back office; the pads note drops on as he says it (08:54) -> the shelf: drawer 1, one
 * pair of pads. The 08:55 key and card stay out of frame until scene 4. */
(function () {
  const C = CUES.scenes[2], S = C.start, E = C.end;
  let run, sw, ring, mk;
  const AT_DRAWER = .3936;                       // martin-key COMP.AT_DRAWER (checked in ready())
  const walkAt = t => AT_DRAWER * easeInOutSine(clamp((t - M('walk')) / (M('pads_callout') - .15 - M('walk'))));
  Scene({
    id: '3', start: S, end: E, fadeIn: 0,
    build(root) {
      const flip = M('clock') + .95, full = Math.max(V(9), M('clock') + 1.6);
      run = seq(root, [
        { src: 'world/02_medium_night.png', at: S, cam: [S, 960, 600, 1.12], grade: 'brightness(.16)' },
        { src: 'world/04_medium_monday.png', at: S + .35, fi: 1.5, cam: hold(960, 600, 1.12, -.01),
          grade: t => `brightness(${lerp(1.35, 1, easeInOutSine(P(t, S + .6, 1.6))).toFixed(3)})` },
        // the screen clock: a cut to the corner of the screen (the calendar gadget and the taskbar clock), held while
        // 08:51 turns 08:52; then, on Martin's line, Theo's Back Office full frame, locked
        { src: 'live/shop', at: M('clock'), fi: .3, cam: [1700, 800, 1.9],
          state: t => ({ preset: 'shop-jobs', time: t < flip ? '08:51' : '08:52', secs: (58 + Math.floor(t - flip + 2)) % 60 }) },
        { src: 'live/shop', at: full, cam: [960, 540, 1],
          state: t => ({ preset: 'shop-jobs', time: '08:52', secs: (58 + Math.floor(t - flip + 2)) % 60 }) },
        // Martin's plan, the west wing framed once (job board to back office); Barnaby walks inside the frame. The
        // scene's one move: as he reaches drawer 1 and the pads note drops on, a push to end on the callout
        { src: 'comp/martin-key', at: M('martin_world'), fi: .5,
          cam: move(M('pads_callout') - .15, 1.4, [600, 540, 1.5], [620, 310, 2.0], 0),
          state: t => ({ walk: +walkAt(t).toFixed(4), pads: +clamp((t - M('pads_callout')) / .55).toFixed(3), ask: 0, card: 0, say: 0, martin: 0, time: '08:54' }),
          build: l => {
            // Barnaby listening at the job board while Martin asks: his ring breathes (a brass ring, his colour)
            ring = el('div', {}, l); css(ring, { width: '0px', height: '0px', borderRadius: '50%', border: '3px solid #E2B54E', display: 'none' });
          },
          over: t => {
            const p = [90 + 7.3 * 60, 286 + 8.05 * 60];
            const u = ((t - M('martin_world') - .6) / 1.4) % 1, on = t > M('martin_world') + .6 && t < M('walk');
            if (!on || u < 0) { ring.style.display = 'none'; return; }
            const r = lerp(32, 60, easeOutCubic(u));
            css(ring, { display: 'block', left: (p[0] - r).toFixed(1) + 'px', top: (p[1] - r).toFixed(1) + 'px', width: 2 * r + 'px', height: 2 * r + 'px', opacity: (.8 * (1 - u)).toFixed(3) });
          } },
        { src: 'world/x_shelf_monday.png', at: M('shelf'), fi: .35, cam: hold(680, 400, 1.18) },
      ], E);
      mk = run.list[4].s;
      sw = sweep(root, { angle: 100, color: 'rgba(255,240,214,.6)' });
    },
    ready() {
      const a = mk.win().COMP.AT_DRAWER;
      if (Math.abs(a - AT_DRAWER) > 1e-3) window.__errors.push('[s3] martin-key AT_DRAWER is ' + a);
      // the walk's start: the comp's marker, before he sets off, sits where the route starts
    },
    render(t) { run.render(t); if (!run.list[1].bl) sw.render(t, S + .2, S + 2.6, .9); },     // Blender's time-lapse bakes its own light
  });
})();
