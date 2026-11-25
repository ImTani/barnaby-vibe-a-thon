/* 6 · A room Theo never built. Mon 23 Nov, 16:08-16:21. Late light on the desk -> the one sticky note on the bezel ->
 * the shop PC LIVE at 16:08: Theo's marquee crawling, the cursor drifting up to the tab "Reports (coming soon!!)" ->
 * Martin at the desk -> Theo's world LIVE (same-butler, his panel): the change written file by file, each count
 * climbing as its line types, then the checks running, one mark each, to "22 passed" -> Martin's glasses -> Martin's
 * world LIVE (martin-build): Barnaby's explanation card slides in (story.js build.card); "That one needs your click"
 * -> the cursor goes to "Add it"; "Fussy." -> the click -> Theo's system reloads (16:16): the status bar loads and
 * the tab "Reports (coming soon!!)" now says Reports -> on the plan the Workload room fills in where Reports was
 * planned, and its NEW sticker slaps on -> same butler, three worlds -> the after panel -> Dev -> Priya on Theo's
 * Jobs page (16:21): the two rows change, highlighted. */
(function () {
  const C = CUES.scenes[5], S = C.start, E = C.end, FI = .4;
  const LATE = 'sepia(.35) saturate(1.15) hue-rotate(-12deg) brightness(.93)';
  const SB = 'worlds/same-butler.png';
  let run, rv = {}, cardPlan, AddIt = null;
  Scene({
    id: '6', start: S, end: E, fadeIn: FI,
    build(root) {
      const n37 = VE(37) - V(37);
      const cardAt = M('glasses') + 3.2, cb = M('click_build');
      const filesA = M('code') + .35, filesB = M('checks') - .3, testsB = M('checks') + 1.5;
      run = seq(root, [
        { src: 'world/04_medium_monday.png', at: S - FI, grade: LATE, cam: [[S - FI, 960, 600, 1.08], [M('sticky'), 940, 720, 1.5]] },
        { src: 'world/04_medium_monday.png', at: M('sticky'), fi: .35, grade: LATE, cam: [[M('sticky'), 945, 760, 3.0], [M('soon_tab'), 955, 775, 3.4]] },
        { src: 'live/shop', at: M('soon_tab'), fi: .3, cam: [[M('soon_tab'), 960, 540, 1.0], [V(30), 820, 380, 1.7], [VE(30) + .2, 800, 400, 1.75]],
          state: t => {
            const a = M('soon_tab') + .4, c = path2(t, [[a, 700, 470], [V(30) - .2, 578, 258], [VE(30) + .3, 582, 261]]);
            return { preset: 'shop-reports-soon', marquee: +(((t - M('soon_tab')) * 60) % 2000).toFixed(1), secs: Math.floor(t - M('soon_tab')) + 14,
              cursor: { x: +(c[0] + wiggle(t, 31, 2, 1.2)).toFixed(2), y: +(c[1] + wiggle(t, 32, 1.7, 1)).toFixed(2) } };
          } },
        { src: 'world/04_medium_monday.png', at: VE(30) + .15, fi: .3, grade: LATE, cam: [[VE(30) + .15, 880, 640, 1.5], [M('code'), 845, 625, 1.95]] },
        { src: 'comp/same-butler', at: M('code'), fi: .4, cam: [[M('code'), 314, 680, 3.0], [M('checks'), 314, 700, 3.08], [M('glasses'), 300, 690, 3.16]],
          state: t => ({ files: +clamp(3 * (t - filesA) / (filesB - filesA), 0, 3).toFixed(3), tests: +(22 * clamp((t - M('checks')) / (testsB - M('checks')))).toFixed(2) - (t < M('checks') ? 1 : 0),
            added: 0, rediscover: 0 }) },
        { src: 'world/04_medium_monday.png', at: M('glasses'), fi: .35, grade: LATE, cam: [[M('glasses'), 600, 860, 2.0], [cardAt, 700, 880, 2.1]] },
        { src: 'comp/martin-build', at: cardAt, fi: .4,
          cam: [[cardAt, 1180, 560, 1.25], [cardAt + 1.2, 1500, 560, 1.5], [V(35), 1520, 600, 1.55], [cb, 1460, 700, 1.6]],
          state: t => ({ room: 0, side: 'card', time: '16:16', foot: '', card: +clamp((t - cardAt - .3) / .6).toFixed(3), marker: [11.0, 1.7], passage: 1,
            press: [+(clamp((t - cb + .02) / .06) * (1 - clamp((t - cb - .14) / .14))).toFixed(3), 0] }),
          build: l => { rv.cur = cursor(l, 1.5); },
          over: t => {
            if (!AddIt || t < V(35) + 1.2) { rv.cur.at(0, 0, false); return; }
            const c = path2(t, [[V(35) + 1.2, AddIt[0] - 260, AddIt[1] + 230], [cb - .08, AddIt[0], AddIt[1]], [cb + .3, AddIt[0] + 2, AddIt[1] + 3]]);
            rv.cur.at(c[0], c[1], true);
          } },
        { src: 'live/shop', at: M('reload'), cam: [[M('reload'), 720, 400, 2.0], [M('tab_change') + 1.2, 740, 440, 1.6]],
          state: t => t < M('tab_change')
            ? { preset: 'shop-reports-soon', time: '16:16', loading: +lerp(.08, .96, easeInOutSine(clamp((t - M('reload')) / (M('tab_change') - M('reload'))))).toFixed(3), secs: 2 }
            : { preset: 'shop-reports', loading: +(t < M('tab_change') + .15 ? 1 : 0), secs: 3 + Math.floor(t - M('tab_change')) } },
        { src: 'comp/martin-build', at: M('new_room'), fi: .3, cam: [[M('new_room'), 760, 400, 1.7], [M('same_butler'), 770, 410, 1.62]],
          state: t => ({ room: +easeInOutSine(clamp((t - M('new_room') - .1) / .6)).toFixed(3),
            sticker: +easeOutBack(clamp((t - M('new_room') - .75) / .35), 2.6).toFixed(3), side: 'build' }) },
        { src: 'comp/same-butler', at: M('same_butler'), fi: .4, cam: [[M('same_butler'), 960, 540, 1.0], [V(37) + 5.2, 960, 540, 1.035]],
          build: l => { rv.sb = reveal(l, SB, [[722, 986, 1170, 1015], [722, 1020, 801, 1046]], { color: '#F5F2EA', a: V(37), b: V(37) + n37 * 51 / 115 }); },
          over: t => rv.sb.render(t) },
        { src: 'worlds/martin-build.png', at: V(37) + 5.2, fi: .5, cam: [[V(37) + 5.2, 1180, 560, 1.15], [M('reassign'), 1240, 560, 1.22]],
          build: l => { rv.mb = reveal(l, 'worlds/martin-build.png', [[1428, 356, 1832, 384], [1426, 395, 1812, 423], [1426, 435, 1811, 463], [1426, 475, 1656, 496]], { color: '#F5F2EA', a: V(37), b: VE(37) - .1, chars: [31, 32, 30, 17] }); },
          over: t => rv.mb.render(t) },
        { src: 'live/shop', at: M('reassign') - .1, fi: .25, cam: [[M('reassign') - .1, 600, 830, 1.75], [E, 560, 830, 1.9]],
          state: t => ({ preset: 'shop-jobs-after', reassign: +clamp((t - M('reassign') - .25) / 1.3).toFixed(3), secs: 5 + Math.floor(t - M('reassign')) }) },
      ], E);
      cardPlan = run.list[6].s;
    },
    ready() {
      const w = cardPlan.win();
      w.COMP.render({ room: 0, side: 'card', card: 1 });
      const r = w.COMP.sideCard.querySelector('.yes').getBoundingClientRect();
      AddIt = [r.left + r.width * .45, r.top + r.height * .55];
    },
    render(t) { run.render(t); },
  });
})();
