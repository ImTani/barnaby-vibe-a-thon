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
      const flip = M('clock') + .95;
      run = seq(root, [
        { src: 'world/02_medium_night.png', at: S, cam: [S, 960, 600, 1.12], grade: 'brightness(.16)' },
        { src: 'world/04_medium_monday.png', at: S + .35, fi: 1.5,
          cam: [[S + .35, 960, 600, 1.12], [S + 1.9, 960, 640, 1.06], [M('clock'), 1180, 830, 1.5]],
          grade: t => `brightness(${lerp(1.35, 1, easeInOutSine(P(t, S + .6, 1.6))).toFixed(3)})` },
        { src: 'live/shop', at: M('clock'), fi: .3,
          cam: [[M('clock'), 1790, 320, 2.6], [M('clock') + .25, 1790, 330, 2.6], [flip - .1, 1780, 905, 2.6], [flip + .45, 1780, 920, 2.66], [M('martin_world') + .1, 960, 540, 1.0]],
          state: t => ({ preset: 'shop-jobs', time: t < flip ? '08:51' : '08:52', secs: (58 + Math.floor(t - flip + 2)) % 60 }) },
        { src: 'comp/martin-key', at: M('martin_world'), fi: .5,
          cam: [[M('martin_world'), 530, 640, 1.8], [M('walk'), 520, 700, 1.95], [M('walk') + 1.4, 470, 520, 1.9], [M('pads_callout'), 610, 330, 1.9], [M('shelf'), 640, 310, 1.95]],
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
        { src: 'world/x_shelf_monday.png', at: M('shelf'), fi: .35, cam: [[M('shelf'), 700, 420, 1.15], [E, 560, 340, 1.35]] },
      ], E);
      mk = run.list[3].s;
      sw = sweep(root, { angle: 100, color: 'rgba(255,240,214,.6)' });
    },
    ready() {
      const a = mk.win().COMP.AT_DRAWER;
      if (Math.abs(a - AT_DRAWER) > 1e-3) window.__errors.push('[s3] martin-key AT_DRAWER is ' + a);
      // the walk's start: the comp's marker, before he sets off, sits where the route starts
    },
    render(t) { run.render(t); sw.render(t, S + .2, S + 2.6, .9); },
  });
})();
