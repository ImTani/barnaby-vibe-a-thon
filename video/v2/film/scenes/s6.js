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
      const cardAt = M('glasses') + 3.2, cb = sfxT('mouse_click', M('click_build'));
      const filesA = M('code') + .35, filesB = M('checks') - .3, testsB = M('checks') + 1.5;
      run = seq(root, [
        { src: 'world/04_medium_monday.png', at: S - FI, grade: LATE, cam: hold(960, 610, 1.1) },
        { src: 'world/04_medium_monday.png', at: M('sticky'), fi: .35, grade: LATE, cam: hold(948, 766, 3.1, .006) },   // a cut to the note
        { src: 'live/shop', at: M('soon_tab'), fi: .3, cam: [960, 540, 1],
          state: t => {
            const b = Math.max(M('soon_tab') + 1.4, V(30)), c = path2(t, [[b - .9, 700, 470], [b - .1, 578, 258], [VE(30) + .3, 582, 261]]);   // Martin's hand to the tab
            return { preset: 'shop-reports-soon', marquee: +(((t - M('soon_tab')) * 60) % 2000).toFixed(1), secs: Math.floor(t - M('soon_tab')) + 14,
              cursor: { x: +(c[0] + wiggle(t, 31, 2, 1.2)).toFixed(2), y: +(c[1] + wiggle(t, 32, 1.7, 1)).toFixed(2) } };
          } },
        { src: 'world/04_medium_monday.png', at: V(31), fi: .3, grade: LATE, cam: hold(880, 640, 1.45) },
        { src: 'comp/same-butler', at: M('code'), fi: .4, cam: [314, 690, 3.0],
          state: t => ({ files: +clamp(3 * (t - filesA) / (filesB - filesA), 0, 3).toFixed(3), tests: +(22 * clamp((t - M('checks')) / (testsB - M('checks')))).toFixed(2) - (t < M('checks') ? 1 : 0),
            added: 0, rediscover: 0 }) },
        { src: 'world/04_medium_monday.png', at: M('glasses'), fi: .35, grade: LATE, cam: hold(640, 865, 2.05) },
        { src: 'comp/martin-build', at: cardAt, fi: .4, cam: [960, 540, 1],
          state: t => ({ room: 0, side: 'card', time: '16:16', foot: '', martinSay: t >= V(36) ? 'Fussy.' : t >= V(34) ? 'Add it.' : 'You can do that?', card: +clamp((t - cardAt - .3) / .6).toFixed(3), marker: [11.62, 2.45], passage: 1,
            press: [+pressAt(t, cb).toFixed(3), 0] }),
          build: l => { rv.cur = cursor(l, 1.5); },
          over: t => {
            const from = Math.min(V(35) + 1.2, cb - 1.3);
            if (!AddIt || t < from) { rv.cur.at(0, 0, false); return; }
            const c = hand(t, [from, AddIt[0] - 260, AddIt[1] + 230], [{ t: cb, x: AddIt[0], y: AddIt[1] }]);
            rv.cur.at(c[0], c[1], true);
          } },
        { src: 'live/shop', at: M('reload'), cam: [960, 540, 1],
          state: t => t < M('tab_change')
            ? { preset: 'shop-reports-soon', time: '16:16', loading: +lerp(.08, .96, easeInOutSine(clamp((t - M('reload')) / (M('tab_change') - M('reload'))))).toFixed(3), secs: 2 }
            : { preset: 'shop-reports', loading: +(t < M('tab_change') + .15 ? 1 : 0), secs: 3 + Math.floor(t - M('tab_change')) } },
        // the scene's one move: the Workload room fills in and its NEW sticker lands as we close in on it
        { src: 'comp/martin-build', at: M('new_room'), fi: .3, cam: move(M('new_room') + .05, 1.15, [700, 560, 1.32], [760, 420, 1.62], 0),
          state: t => ({ room: +easeInOutSine(clamp((t - M('new_room') - .1) / .6)).toFixed(3),
            sticker: +easeOutBack(clamp((t - M('new_room') - .75) / .35), 2.6).toFixed(3), side: 'build' }) },
        { src: 'comp/same-butler', at: M('same_butler'), fi: .4, cam: [960, 540, 1],
          build: l => { rv.sb = reveal(l, SB, [[722, 986, 1170, 1015], [722, 1020, 801, 1046]], { color: '#F5F2EA', a: V(37), b: V(37) + n37 * 51 / 115 }); },
          over: t => rv.sb.render(t) },
        { src: 'worlds/martin-build.png', at: V(37) + 5.2, fi: .5, cam: [960, 540, 1],
          build: l => { rv.mb = reveal(l, 'worlds/martin-build.png', [[1428, 356, 1832, 384], [1426, 395, 1812, 423], [1426, 435, 1811, 463], [1426, 475, 1656, 496]], { color: '#F5F2EA', a: V(37), b: VE(37) - .1, chars: [31, 32, 30, 17] }); },
          over: t => rv.mb.render(t) },
        { src: 'live/shop', at: M('reassign') - .1, fi: .25, cam: [960, 540, 1],
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
