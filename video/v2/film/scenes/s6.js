/* 6 · A room Theo never built. Mon 23 Nov, 16:08-16:21. Late light on the desk -> the one sticky note on the bezel ->
 * the shop PC LIVE at 16:08: Theo's marquee crawling, the cursor drifting up to the tab "Reports (coming soon!!)" ->
 * Martin at the desk -> Theo's world LIVE (same-butler, his panel): the change written file by file, each count
 * climbing as its line types, then the checks running, one mark each, to "22 passed" -> Martin's glasses -> Martin's
 * world LIVE (martin-build): Barnaby's explanation card slides in (story.js build.card); "That one needs your click"
 * -> the cursor goes to "Add it"; "Fussy." -> the click -> Theo's system reloads (16:16): the status bar loads and
 * the tab "Reports (coming soon!!)" now says Reports -> on the plan the Workload room fills in where Reports was
 * planned, and its NEW sticker slaps on -> the plan with the room's hours as Barnaby speaks -> Dev -> Priya on Theo's
 * Jobs page (16:21): the two rows change, highlighted. */
(function () {
  const C = CUES.scenes[5], S = C.start, E = C.end, FI = .4;
  const LATE = 'sepia(.35) saturate(1.15) hue-rotate(-12deg) brightness(.93)';
  const SB = 'worlds/same-butler.png';
  let run, rv = {}, cardPlan, AddIt = null;
  Scene({
    id: '6', start: S, end: E, fadeIn: 0,
    build(root) {
      const n37 = VE(37) - V(37);
      const cb = sfxT('mouse_click', M('click_build')), cardAt = V(33), CHAIR = pick('world/x_chair_dusk.png', '');
      const MON = 'world/04_medium_monday.png', DUSK = pick('world/06_medium_dusk.png', MON), STICKY = pick('world/x_sticky_dusk.png', MON), GLASSES = pick('world/x_glasses_dusk.png', MON);
      const cardItem = at => ({ src: 'comp/martin-build', at, cam: [960, 540, 1],
          state: t => ({ room: 0, side: 'card', time: '16:16', foot: '', martinSay: t >= V(36) ? 'Fussy.' : t >= V(34) ? 'Add it.' : 'You can do that?', card: +clamp((t - cardAt - .3) / .6).toFixed(3), marker: [11.62, 2.45], passage: 1,
            press: [+pressAt(t, cb).toFixed(3), 0] }),
          build: l => { const cur = cursor(l, 1.5); (rv.curs = rv.curs || []).push(cur); },
          over: (t, l) => {
            const cur = rv.curs[at === cardAt ? 0 : 1], from = Math.min(V(35) + 1.2, cb - 1.3);
            if (!AddIt || t < from) { cur.at(0, 0, false); return; }
            const c = hand(t, [from, AddIt[0] - 260, AddIt[1] + 230], [{ t: cb, x: AddIt[0], y: AddIt[1] }]);
            cur.at(c[0], c[1], true);
          } });
      const filesA = M('code') + .35, filesB = M('checks') - .3, testsB = M('checks') + 1.5;
      run = seq(root, [
        // 6.1 dusk: the room deep blue, then the lamp comes on (Blender's s6_lamp_on / 06_medium_dusk when they land;
        // until then the Monday desk in the late grade, its light stepping up on the lamp's click)
        { src: DUSK, at: S, cam: hold(960, 610, 1.08), keepGrade: true,
          grade: t => DUSK === MON ? `${LATE} brightness(${lerp(.62, 1, easeOutCubic(P(t, M('lamp_on'), .12))).toFixed(3)})` : '' },
        // 6.2 the sticky note, in Theo's hand; 6.3 Reports (coming soon!!), locked and held for the joke
        { src: STICKY, at: M('sticky'), grade: STICKY === MON ? LATE : '', cam: STICKY === MON ? hold(948, 766, 3.1, .006) : hold(960, 540, 1.0) },
        { src: 'live/shop', at: M('soon_tab'), cam: [960, 540, 1],
          state: t => {
            const b = Math.max(M('soon_tab') + 1.4, V(29) + 4), c = path2(t, [[b - .9, 700, 470], [b - .1, 578, 258], [b + 3, 582, 261]]);   // Martin's hand to the tab
            return { preset: 'shop-reports-soon', marquee: +(((t - M('soon_tab')) * 60) % 2000).toFixed(1), secs: Math.floor(t - M('soon_tab')) + 14,
              cursor: { x: +(c[0] + wiggle(t, 31, 2, 1.2)).toFixed(2), y: +(c[1] + wiggle(t, 32, 1.7, 1)).toFixed(2) } };
          } },
        // 6.4 back to the dusk desk: "I could write it" / "You can do that?" / "With your say-so"
        { src: DUSK, at: V(30), grade: DUSK === MON ? LATE : '', cam: pan(V(30) + .3, M('code') - V(30) - .8, 880, 610, 1040, 600, 1.1) },
        // 6.5 the change, written and checked (locked)
        { src: 'comp/same-butler', at: M('code'), cam: [314, 690, 3.0],
          state: t => ({ files: +clamp(3 * (t - filesA) / (filesB - filesA), 0, 3).toFixed(3), tests: +(22 * clamp((t - M('checks')) / (testsB - M('checks')))).toFixed(2) - (t < M('checks') ? 1 : 0),
            added: 0, rediscover: 0 }) },
        // 6.6 Martin's plan with the explanation card; mid-line, his reading glasses on the dusk desk; back to the card
        cardItem(V(33)),
        { src: GLASSES, at: M('glasses'), grade: GLASSES === MON ? LATE : '', cam: GLASSES === MON ? hold(640, 865, 2.05) : hold(960, 540, 1.0) },
        cardItem(M('glasses') + 2.4),
        // 6.8 the reload, the tab turns Reports (locked); 6.9 the scene's one move: the Workload room appears
        { src: 'live/shop', at: M('reload'), cam: [960, 540, 1],
          state: t => t < M('tab_change')
            ? { preset: 'shop-reports-soon', time: '16:16', loading: +lerp(.08, .96, easeInOutSine(clamp((t - M('reload')) / (M('tab_change') - M('reload'))))).toFixed(3), secs: 2 }
            : { preset: 'shop-reports', loading: +(t < M('tab_change') + .15 ? 1 : 0), secs: 3 + Math.floor(t - M('tab_change')) } },
        { src: 'comp/martin-build', at: M('new_room'), open: { x: 1542, y: 520, d: .55 }, cam: move(M('new_room') + .05, 1.15, [700, 560, 1.32], [760, 420, 1.62], 0),
          state: t => ({ room: +easeInOutSine(clamp((t - M('new_room') - .1) / .6)).toFixed(3),
            sticker: +easeOutBack(clamp((t - M('new_room') - .75) / .35), 2.6).toFixed(3), side: 'build' }) },
        // 6.10 (v2.3: the triptych is cut) Martin's plan with the new Workload room and its hours, Dev 31 of 20; his line
        // prints in the side panel as he says it, held through "Good idea."
        { src: 'comp/martin-build', at: M('same_butler'), cam: [960, 540, 1], state: () => ({ side: 'build' }),
          build: l => { rv.mb = reveal(l, 'worlds/martin-build.png', [[1428, 356, 1832, 384], [1426, 395, 1812, 423], [1426, 435, 1811, 463], [1426, 475, 1656, 496]], { color: '#F5F2EA', a: V(37), b: VE(37) - .1, chars: [31, 32, 30, 17] }); },
          over: t => rv.mb.render(t) },
        // 6.11 the jobs page: Dev -> Priya (locked, held)
        { src: 'live/shop', at: M('reassign') - .1, cam: [960, 540, 1],
          state: t => ({ preset: 'shop-jobs-after', reassign: +clamp((t - M('reassign') - .25) / 1.3).toFixed(3), secs: 5 + Math.floor(t - M('reassign')) }) },
      ].concat(CHAIR ? [{ src: CHAIR, at: CUES.marks.s6_chair != null ? M('s6_chair') : Math.max(M('reassign') + 3.0, E - 1.6), cam: hold(960, 540, 1.0) }] : []), E, { scene: 6 });
      cardPlan = run.list[7].s;
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
