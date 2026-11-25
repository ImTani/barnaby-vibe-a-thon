/* 8 · Any house. Lisbon, Tue 24 Nov, 09:39-09:43. The second diorama (lisbon_01 wide, the nata and bica) -> the main
 * monitor: the browser tile with the REAL Barnaby app slides in (lisbon-pc realapp, app 0 -> .5 -> 1, re-captured in
 * the round 3 look) -> the real app full screen, labelled as the real app, Connect -> Barnaby's log: Synapse reads
 * Quorum (Extracted 13 endpoint(s)) -> Barnaby fully himself in Theo's world (worlds2 theo-lisbon) -> "Still Theo." ->
 * "Theo." (lisbon-pc quorum-theo) -> the render box (lisbon_02 -> the studio monitor, the queue opening) -> "Show-off."
 * The small disclosure from the script stays up from the Connect to the end of the scene. */
(function () {
  const C = CUES.scenes[7], S = C.start, E = C.end, FI = .5;
  const RA = 'realapp/barnaby-connect.png', TL = 'worlds/theo-lisbon.png';
  let run, rv, press, chip, disc;
  Scene({
    id: '8', start: S, end: E, fadeIn: FI,
    build(root) {
      const mainCam = [[M('realapp'), 960, 540, 1.0], [M('realapp_full') + .1, 1240, 520, 1.25]];
      const mainCam2560 = mainCam.map(k => [k[0], k[1] * 4 / 3, k[2] * 4 / 3, k[3]]);
      const logCam = [[M('synapse_log') - .1, 420, 700, 2.0], [M('theo_world'), 420, 740, 2.05]];
      const qOpen = V(49) + 2.9;
      run = seq(root, [
        { src: 'world/lisbon_01_wide_day.png', at: S - FI, cam: [[S - FI, 980, 560, 1.0], [M('nata') + .4, 1000, 520, 1.15]] },
        { src: 'world/x_lisbon_detail_day.png', at: M('nata'), fi: .4, cam: [[M('nata'), 900, 560, 1.05], [M('realapp') + .3, 860, 600, 1.15]] },
        { src: 'scr/s8_app_0.jpg', at: M('realapp'), fi: .3, cam: mainCam },
        { src: 'scr/s8_app_5.jpg', at: M('realapp') + .3, cam: mainCam },
        { src: 'look/lisbon-02-realapp-main.png', at: M('realapp') + .55, cam: mainCam2560 },
        { src: RA, at: M('realapp_full'), fi: .3, cam: [[M('realapp_full'), 1000, 560, 1.0], [M('connect') + .3, 900, 690, 1.1]],
          build: l => { press = el('div', {}, l); css(press, { left: '746px', top: '751px', width: '134px', height: '57px', borderRadius: '29px', background: '#000' }); },
          over: t => { press.style.opacity = (.28 * pulse(t, M('connect') + .05, .12)).toFixed(3); } },
        { src: 'scr/s8_log_4.jpg', at: M('synapse_log') - .1, cam: logCam },
        { src: 'scr/s8_log_10.jpg', at: M('synapse_log') + .8, cam: logCam },
        { src: TL, at: M('theo_world'), fi: .35, cam: [[M('theo_world'), 960, 540, 1.0], [M('still_theo'), 1100, 560, 1.12]],
          build: l => { rv = reveal(l, TL, [[1466, 884, 1840, 912], [1467, 922, 1846, 950], [1467, 959, 1604, 987]], { color: '#14110E', a: V(45), b: VE(45) - .1, chars: [30, 33, 11] }); },
          over: t => rv.render(t) },
        { src: 'world/lisbon_02_medium_day.png', at: M('still_theo'), cam: [[M('still_theo'), 1040, 540, 1.6], [V(47) - .1, 1050, 540, 1.7]] },
        { src: 'look/lisbon-03b-quorum-theo-main.png', at: V(47) - .1, cam: [[V(47) - .1, 2150, 860, 1.6], [M('render_box'), 2150, 880, 1.65]] },
        { src: 'world/lisbon_02_medium_day.png', at: M('render_box'), cam: [[M('render_box'), 1250, 600, 1.3], [V(49), 1450, 610, 1.55]] },
        { src: 'scr/s8_studio_q0.jpg', at: V(49), fi: .25, cam: [[V(49), 960, 540, 1.0], [qOpen, 700, 480, 1.15]] },
        { src: 'look/lisbon-04-comfy-studio.png', at: qOpen, fi: .3, cam: [[qOpen, 933, 640, 1.15], [VE(49) + .2, 600, 560, 1.5]] },
        { src: 'world/lisbon_02_medium_day.png', at: VE(49) + .2, fi: .3, cam: [[VE(49) + .2, 980, 560, 1.12], [E, 960, 560, 1.18]] },
      ], E);
      chip = label(root, 'The real Barnaby app', 'left:48px;top:40px;font:600 28px "Segoe UI",sans-serif;color:#24211C;background:rgba(241,229,201,.95);border:1px solid #A8772A;padding:6px 16px;border-radius:20px');
      disc = label(root, 'Quorum and ComfyUI scenes staged · endpoint counts from real Synapse scans',
        'right:40px;top:1020px;font:500 22px "Segoe UI",sans-serif;color:rgba(255,255,255,.82);background:rgba(0,0,0,.55);padding:4px 12px;border-radius:4px');
    },
    render(t) {
      run.render(t);
      fadeEl(chip, t, M('realapp_full') + .15, M('synapse_log') - .1, .3, .2);
      fadeEl(disc, t, M('synapse_log'), E, .4, .3);
    },
  });
})();
