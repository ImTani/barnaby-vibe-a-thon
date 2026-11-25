/* 8 · Any house. Lisbon, Tue 24 Nov, 09:39-09:43. The second diorama (lisbon_01 wide, the nata and bica) -> the main
 * monitor LIVE (look/lisbon-pc, preset realapp): the browser tile with the real Barnaby app slides in, its Connect form
 * still empty -> the REAL app full screen (captured by capture.js from `python -m barnaby serve`, key by key): Theo
 * clicks into each field and types quorum · /home/theo/crew/quorum · http://localhost:8001, the pointer goes to
 * Connect and presses it -> the main monitor LIVE (preset quorum): Barnaby's log streams into the tmux pane as
 * Synapse reads Quorum -> Barnaby in Theo's world (worlds2 theo-lisbon, the approved still; his line printed as he
 * says it) -> "Still Theo." -> "Theo." typed in his slot (LIVE, quorum-theo) -> the render box -> the studio monitor
 * LIVE (preset comfy): the queue slides open, the sampler's steps tick on, the pencil test plays -> "Show-off."
 * The small disclosure from the script stays up from the Connect to the end of the scene. */
(function () {
  const C = CUES.scenes[7], S = C.start, E = C.end, FI = .5;
  const TL = 'worlds/theo-lisbon.png', FORM = { x: 700, y: 400, w: 724, h: 440 }, BTN = [813, 779];
  // the form, step by step (capture.js manifest): 0 empty, 1 click Name, 2-7 "quorum", 8 click Repo path,
  // 9-30 "/home/theo/crew/quorum", 31 click API base URL, 32-52 "http://localhost:8001", 53 hover Connect, 54 pressed
  const T0 = () => M('realapp_full') + .05;
  const STEPS = () => {
    const at = [], push = (t) => at.push(t);
    let t = T0(); push(t);                                       // 1 click name
    for (let i = 0; i < 6; i++) push(t += i ? .03 : .05);        // 2-7
    push(t += .05);                                              // 8 click repo
    for (let i = 0; i < 22; i++) push(t += i ? .019 : .04);      // 9-30
    push(t += .05);                                              // 31 click url
    for (let i = 0; i < 21; i++) push(t += i ? .018 : .04);      // 32-52
    push(M('connect') - .12);                                    // 53 hover
    push(M('connect') - .01);                                    // 54 pressed
    return at;                                                   // at[k] = time step k+1 is reached
  };
  let run, rv, chip, disc, forms = [], fcur, stepAt;
  const stepOf = t => {
    if (t >= M('connect') + .14) return 53;                      // released: the pointer still over Connect
    let k = 0; for (let i = 0; i < stepAt.length; i++) if (t >= stepAt[i]) k = i + 1; return k;
  };
  Scene({
    id: '8', start: S, end: E, fadeIn: FI,
    build(root) {
      stepAt = STEPS();
      const mainCam = [[M('realapp'), 960, 540, 1.0], [M('realapp_full') + .1, 1240, 520, 1.25]];
      const logCam = [[M('synapse_log') - .1, 420, 700, 2.0], [M('theo_world'), 420, 740, 2.05]];
      const qOpen = V(49) + 2.9;
      run = seq(root, [
        { src: 'world/lisbon_01_wide_day.png', at: S - FI, cam: [[S - FI, 980, 560, 1.0], [M('nata') + .4, 1000, 520, 1.15]] },
        { src: 'world/x_lisbon_detail_day.png', at: M('nata'), fi: .4, cam: [[M('nata'), 900, 560, 1.05], [M('realapp') + .3, 860, 600, 1.15]] },
        { src: 'live/lis-main-empty', at: M('realapp'), fi: .3, cam: mainCam,
          state: t => ({ preset: 'realapp', app: +easeOutCubic(clamp((t - M('realapp') - .05) / .6)).toFixed(4), secs: 40 + Math.floor(t - M('realapp')) }) },
        { src: 'rapp/base.jpg', at: M('realapp_full'), fi: .25, cam: [[M('realapp_full'), 1040, 600, 1.12], [M('connect'), 1010, 640, 1.2], [M('synapse_log'), 1000, 650, 1.22]],
          build: l => {
            forms = [];
            for (let i = 0; i <= 54; i++) {
              const im = el('img', { attrs: { src: `assets/realapp/f_${String(i).padStart(3, '0')}.jpg`, decoding: 'sync' } }, l);
              css(im, { position: 'absolute', left: FORM.x + 'px', top: FORM.y + 'px', width: FORM.w + 'px', height: FORM.h + 'px', display: 'none' });
              forms.push(im);
            }
            fcur = cursor(l, 1.6);
          },
          over: t => {
            const k = stepOf(t);
            forms.forEach((im, i) => { const on = i === k; if ((im.style.display !== 'none') !== on) im.style.display = on ? 'block' : 'none'; });
            // Theo's pointer: off the form while he types, then to Connect, the press
            if (t < stepAt[51] - .05) { fcur.at(0, 0, false); return; }
            const c = path2(t, [[stepAt[51] - .05, BTN[0] + 330, BTN[1] + 150], [stepAt[52], BTN[0] + 6, BTN[1] + 4], [M('synapse_log'), BTN[0] + 10, BTN[1] + 8]]);
            fcur.at(c[0], c[1], true);
          } },
        { src: 'live/lis-main', at: M('synapse_log') - .1, cam: logCam,
          state: t => ({ preset: 'quorum', time: '09:40', secs: 2 + Math.floor((t - M('synapse_log')) * 2), out: Math.floor(lerp(0, 10.99, clamp((t - M('synapse_log')) / 1.6))),
            say: '', sayK: 0, plan: '', mode: 'thinking', level: 0, notify: 0 }) },
        { src: TL, at: M('theo_world'), fi: .35, cam: [[M('theo_world'), 960, 540, 1.0], [M('still_theo'), 1100, 560, 1.12]],
          build: l => { rv = reveal(l, TL, [[1466, 884, 1840, 912], [1467, 922, 1846, 950], [1467, 959, 1604, 987]], { color: '#14110E', a: V(45), b: VE(45) - .1, chars: [30, 33, 11] }); },
          over: t => rv.render(t) },
        { src: 'world/lisbon_02_medium_day.png', at: M('still_theo'), cam: [[M('still_theo'), 1040, 540, 1.6], [V(47) - .1, 1050, 540, 1.7]] },
        { src: 'live/lis-main', at: V(47) - .1, cam: [[V(47) - .1, 1612, 645, 1.6], [M('render_box'), 1612, 660, 1.65]],
          state: t => ({ preset: 'quorum-theo', sayK: +clamp((t - V(47)) / (VE(47) - V(47))).toFixed(3), level: +(.4 * (t < VE(47) ? 1 : 0)).toFixed(2) }) },
        { src: 'world/lisbon_02_medium_day.png', at: M('render_box'), cam: [[M('render_box'), 1250, 600, 1.3], [V(49), 1450, 610, 1.55]] },
        { src: 'live/lis-studio', at: V(49), fi: .25, cam: [[V(49), 960, 540, 1.0], [qOpen, 760, 500, 1.12], [VE(49) + .2, 640, 560, 1.45]],
          state: t => ({ preset: 'comfy', queueOpen: +easeInOutCubic(clamp((t - qOpen + .45) / .55)).toFixed(4), queueHl: +clamp((t - qOpen - .2) / .4).toFixed(3),
            step: Math.min(28, 9 + Math.floor((t - V(49)) * 2.4)), frame: 123 + 2 * Math.floor((t - V(49)) * 6), secs: 3 + Math.floor(t - V(49)) }) },
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
