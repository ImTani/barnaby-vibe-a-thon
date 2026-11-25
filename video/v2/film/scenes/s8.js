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
  // From the `typing` mark Theo types "quorum" at about 8 characters a second, unevenly, Tab, pastes the repo path
  // (Ctrl+V), Tab, types the URL, in time for the hand to reach Connect at human speed and press on the click sound.
  // With less room than that it types faster (window.__typingFit < 1).
  const PRESS = () => sfxT('mouse_click', M('connect'));
  let FIT = 1;                                                   // how much the typing had to be squeezed (1 = not)
  const STEPS = () => {
    const kind = [];                                             // per step 1..52: 'click' | 'tab' | 'key'
    kind.push('click'); for (let i = 0; i < 6; i++) kind.push('key');
    kind.push('tab'); for (let i = 0; i < 22; i++) kind.push('key');
    kind.push('tab'); for (let i = 0; i < 21; i++) kind.push('key');
    const repo = i => i >= 8 && i <= 29;                         // the repo path's 22 keys arrive at once: pasted
    const gap = (k, i) => k === 'click' ? 0 : k === 'tab' ? .34 + .1 * rand(i, 91) : repo(i) ? (i === 8 ? .42 : 0) : (1 / 8) * (.65 + .7 * rand(i, 92)) + (rand(i, 93) < .08 ? .16 : 0);
    const t0 = CUES.marks.typing != null ? M('typing') : Math.max(M('realapp_full') + .45, sfxT('keys_modern', M('realapp_full')) - .05), t1 = PRESS() - 1.25;
    const raw = kind.map((k, i) => gap(k, i)), need = raw.reduce((a, b) => a + b, 0);
    FIT = need > 0 && t1 - t0 < need ? Math.max(.05, (t1 - t0) / need) : 1;
    const at = []; let t = t0;
    raw.forEach(g => { t += g * FIT; at.push(t); });
    at.push(PRESS() - .3);                                       // 53 the pointer over Connect (hover)
    at.push(PRESS() - .01);                                      // 54 pressed
    return at;                                                   // at[k] = time step k+1 is reached
  };
  let run, rv, chip, disc, forms = [], fcur, stepAt;
  const stepOf = t => {
    if (t >= PRESS() + .12) return 53;                           // released: the pointer still over Connect
    let k = 0; for (let i = 0; i < stepAt.length; i++) if (t >= stepAt[i]) k = i + 1; return k;
  };
  Scene({
    id: '8', start: S, end: E, fadeIn: 0,
    build(root) {
      stepAt = STEPS(); window.__typingFit = FIT;                  // < 1: Theo had to type faster than 7/s to fit
      const qOpen = M('queue') - .3;
      const MATCH = pick('world/lisbon_match_day.png', ''), LW4K = pick('world/lisbon_01_wide_day_4k.png', '');
      run = seq(root, [
        ...(MATCH ? [{ src: MATCH, at: S, cam: hold(960, 600, 1.12) }] : []),
        LW4K ? { src: LW4K, at: MATCH ? S + 1.6 : S, cam: pan((MATCH ? S + 1.6 : S) + .2, M('nata') - (MATCH ? S + 1.6 : S) - .5, 760, 520, 1160, 560, 1.2) }
          : { src: 'world/lisbon_01_wide_day.png', at: MATCH ? S + 1.6 : S, cam: move((MATCH ? S + 1.6 : S) + .4, M('nata') - (MATCH ? S + 1.6 : S) - .6, [970, 540, 1.0], [1000, 560, 1.12], 0) },
        { src: 'world/x_lisbon_detail_day.png', at: M('nata'), cam: hold(880, 580, 1.06) },
        { src: 'live/lis-main-empty', at: M('realapp'), fi: .12, pin: { shot: 's8_lisbon_day', d: .6 }, cam: [960, 540, 1],
          state: t => ({ preset: 'realapp', app: +easeOutCubic(clamp((t - M('realapp') - .05) / .6)).toFixed(4), secs: 40 + Math.floor(t - M('realapp')) }) },
        { src: 'rapp/base.jpg', at: M('realapp_full'), cam: [712, 560, 1],
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
            // Theo's pointer: off the form while he types, then to Connect at human speed, the press on its click
            const from = Math.max(stepAt[51] + .05, PRESS() - 1.15);
            if (t < from) { fcur.at(0, 0, false); return; }
            const c = hand(t, [from, BTN[0] + 330, BTN[1] + 150], [{ t: PRESS(), x: BTN[0] + 6, y: BTN[1] + 4 }]);
            fcur.at(c[0], c[1], true);
          } },
        { src: 'live/lis-main', at: M('synapse_log') - .1, cam: [600, 700, 1.6],               // Barnaby's log pane, held
          state: t => ({ preset: 'quorum', time: '09:40', secs: 2 + Math.floor((t - M('synapse_log')) * 2), out: Math.floor(lerp(0, 10.99, clamp((t - M('synapse_log')) / 1.6))),
            say: '', sayK: 0, plan: '', mode: 'thinking', level: 0, notify: 0 }) },
        { src: TL, at: M('theo_world'), cam: [960, 540, 1], open: { x: 1650, y: 540, d: .6 },
          build: l => { rv = reveal(l, TL, [[1466, 884, 1840, 912], [1467, 922, 1846, 950], [1467, 959, 1604, 987]], { color: '#14110E', a: V(45), b: VE(45) - .1, chars: [30, 33, 11] }); },
          over: t => rv.render(t) },
        { src: 'live/lis-studio', at: V(48), cam: [960, 540, 1],
          state: t => ({ preset: 'comfy', queueOpen: +easeInOutCubic(clamp((t - qOpen + .45) / .55)).toFixed(4), queueHl: +clamp((t - qOpen - .2) / .4).toFixed(3),
            step: Math.min(28, 9 + Math.floor((t - V(48)) * 2)), frame: 123 + 2 * Math.floor((t - V(48)) * 6), secs: 3 + Math.floor(t - V(48)) }) },
        { src: 'world/lisbon_02_medium_day.png', at: V(50), cam: hold(970, 560, 1.12) },
      ], E, { scene: 8 });
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
