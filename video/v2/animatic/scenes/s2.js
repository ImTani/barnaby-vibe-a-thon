/* 2 · The handover. Thu 19 Nov, night. Props that say who Theo is (the 2009 photo, the calendar with Friday circled,
 * the moving box) -> "Seventeen years." -> he closes the tabs one by one -> the brass bell: Barnaby arrives ->
 * Theo's view (worlds2 theo-handover-1: Synapse reading his code) -> six light up (theo-handover-2) -> the whole
 * 2009 desktop with Barnaby's window, modest on old hardware (theo-handover-pc) -> desk details -> the key on the
 * keyboard, the lamp clicks off. On-screen transcripts in Barnaby's UI are revealed as the lines are spoken. */
(function () {
  const C = CUES.scenes[1], S = C.start, E = C.end, FI = .35;
  let run, rv = {};
  const R1 = 'worlds/theo-handover-1-reading.png', R2 = 'worlds/theo-handover-2-taken.png', PC = 'worlds/theo-handover-pc.png';
  Scene({
    id: '2', start: S, end: E, fadeIn: FI,
    build(root) {
      const ct = M('close_tabs');
      const items = [
        { src: 'world/photo_2009.png', at: S - FI, cam: [[S - FI, 760, 560, 1.04], [M('calendar') + .5, 700, 540, 1.16]] },
        { src: 'world/x_board_night.png', at: M('calendar'), fi: .5, cam: [[M('calendar'), 380, 560, 1.45], [M('box') + .5, 430, 730, 1.9]] },
        { src: 'world/01_wide_night.png', at: M('box'), fi: .5, cam: [[M('box'), 1100, 650, 2.0], [ct + .3, 1160, 700, 2.35]] },
        { src: 'look/shop-pc-03b-tabs-parts.png', at: ct, fi: .3 },
      ];
      for (let i = 0; i < 8; i++) items.push({ src: `scr/s2_close_${8 - i}.jpg`, at: ct + .25 + i * .2 });
      items.push({ src: 'scr/s2_desktop_night.jpg', at: ct + .25 + 8 * .2 });
      items.push({ src: 'world/x_bell.png', at: M('bell_arrive') - .05, fi: .2, cam: [[M('bell_arrive'), 900, 620, 1.1], [M('reading'), 860, 660, 1.22]] });
      items.push({ src: R1, at: M('reading') - .25, fi: .4, cam: [[M('reading'), 960, 540, 1.0], [M('six_lit'), 960, 520, 1.05]],
        build: l => { rv.r1 = reveal(l, R1, [[218, 880, 945, 905], [216, 916, 747, 938]], { dy: 95, a: V(5), b: VE(5) - .15, chars: [64, 45] }); },
        over: t => rv.r1.render(t) });
      items.push({ src: R2, at: M('six_lit'), fi: .35, cam: [[M('six_lit'), 960, 540, 1.0], [M('old_pc'), 920, 600, 1.06]],
        build: l => { rv.r2 = reveal(l, R2, [[165, 858, 1016, 902], [166, 918, 1071, 962]], { dy: 115, a: V(6), b: VE(6) - .1, chars: [47, 47] }); },
        over: t => rv.r2.render(t) });
      items.push({ src: PC, at: M('old_pc'), fi: .5, cam: [[M('old_pc'), 1150, 560, 1.0], [M('desk_detail'), 1480, 620, 1.3]],
        build: l => { rv.pc = reveal(l, PC, [[1246, 815, 1569, 843], [1248, 853, 1619, 881], [1248, 890, 1628, 918]], { color: '#0A0908', a: V(6), b: VE(6) - .1, chars: [28, 34, 31] }); },
        over: t => rv.pc.render(t) });
      items.push({ src: 'world/02_medium_night.png', at: M('desk_detail'), fi: .4, cam: [[M('desk_detail'), 560, 830, 1.55], [M('key'), 1300, 820, 1.55]] });
      items.push({ src: 'world/03_keys_night.png', at: M('key'), fi: .4, cam: [[M('key'), 760, 700, 1.1], [E, 640, 840, 1.35]],
        grade: t => `brightness(${lerp(1, .16, easeOutCubic(P(t, M('lamp_off'), .15))).toFixed(3)})` });
      run = seq(root, items, E);
    },
    render(t) { run.render(t); },
  });
})();
