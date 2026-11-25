/* 1 · Nine tabs. INT. SHOP BACK OFFICE, THU 19 NOV 21:47 (CONTINUITY). Black, rain; light comes up on the wide; we
 * drift to the 2009 monitor (the Blender agent's s1_open when it is done); full screen, the shop PC LIVE (look/shop-pc,
 * preset `tabs`: the nine tabs open, Calendar up, as on the 3D monitor): Theo's cursor clicks through them, one per
 * mark (tab1..tab9); each click, the old PC loads the page (status bar), the CPU needle kicks and the MEMORY needle
 * climbs a notch into the red; the clock gadget's second hand ticks. "Tab four." -> the cursor goes to workload.xls
 * and clicks; "No — five." -> the Parts list (approved look-dev 03b); "It's the one with the spanner." -> the scene's
 * one move, a push to the spanner by PARTS LIST. The screen is otherwise full frame and locked; the hand moves at
 * human speed (shots.js hand()), each press on its click sound. */
(function () {
  const C = CUES.scenes[0], S = C.start, E = C.end;
  const TABS = ['shop', 'supplier', 'sms', 'xls', 'parts', 'invoices', 'email', 'bank', 'cal'];
  let run, live, vig = null, G = null;
  // the opening's grade: pixels much bluer than red (the void around the diorama, about rgb(6,12,24)) go to near-black;
  // the warm room, its greens, the window and the blue chair (B < 2.5 R) are untouched
  function voidFilter() {
    if (document.getElementById('s1void')) return;
    const d = document.createElement('div');
    d.innerHTML = '<svg width="0" height="0" style="position:absolute"><filter id="s1void" x="0" y="0" width="1" height="1" color-interpolation-filters="sRGB">' +
      '<feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -100 0 40 0 0" result="key"/>' +
      '<feFlood flood-color="#030304" result="ink"/><feComposite in="ink" in2="key" operator="in" result="dark"/>' +
      '<feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="dark"/></feMerge></filter></svg>';
    document.body.appendChild(d.firstChild);
  }
  const tabT = k => M('tab' + k);                   // the k-th tab opens (k = 1..9)
  const nOpen = t => { let n = 0; for (let k = 1; k <= 9; k++) if (t >= tabT(k)) n = k; return n; };
  // the needles: each tab adds its notch (eased, a little overshoot, like a real needle), the CPU kicks and settles
  const RAM0 = .38, RAM1 = .93, CPU0 = .14;
  function needles(t) {
    let ram = RAM0, cpu = CPU0 + .04 * Math.sin(t * 2.3) * .5;
    for (let k = 1; k <= 9; k++) {
      const a = tabT(k) + .05, u = P(t, a, .5);
      ram += (RAM1 - RAM0) / 9 * easeOutBack(u, 2.2);
      cpu += .055 * easeOutCubic(P(t, a, .3)) + .32 * Math.exp(-Math.max(0, t - a) * 5) * (t >= a ? 1 : 0);
    }
    // the switches to tab 4 and 5 make the old PC work too
    for (const a of [sfxT('tab', M('tab4_active')), sfxT('tab', M('tab5_active'))]) cpu += .22 * Math.exp(-Math.max(0, t - a) * 4) * (t >= a ? 1 : 0);
    return { ram: clamp(ram, 0, .97), cpu: clamp(cpu, 0, .99) };
  }
  Scene({
    id: '1', start: S, end: E, fadeIn: 0,
    build(root) {
      // the screen is full frame and locked; the one move: on "It's the one with the spanner." a push to the spanner
      const tabCam = move(M('spanner'), Math.min(2.2, E - M('spanner') - .1), [960, 540, 1.0], [720, 262, 2.1], 0);
      // v2.3: the whole opening is Blender's s1_open, one camera, continuous from black: black -> the light comes up on
      // `light_up` -> the drift to the desk (`medium`) -> into the monitor (`screen`). Frames 1-133 hold one framing
      // (only the light moves), so they are re-timed: black until light_up, the light up over 1.8 s (as the approved
      // grade), then the sequence's own events. The live desktop is on the glass the whole time (shots.js), so the
      // push into the screen hands over to the same picture. The surround: near-black, a soft vignette (no indigo void).
      const OPEN = shotDone('s1_open');
      voidFilter();
      const L = M('light_up'), openClock = t => {
        const k = [[S, 1], [L, 30], [L + 1.8, 85], [M('medium'), 133], [M('screen'), 368]];
        if (t >= k[k.length - 1][0]) return 368 + (t - M('screen')) * 24;
        for (let i = 1; i < k.length; i++) if (t <= k[i][0]) return lerp(k[i - 1][1], k[i][1], (t - k[i - 1][0]) / (k[i][0] - k[i - 1][0]));
        return 1;
      };
      const screenK = t => easeInOutSine(P(t, L + .3, 1.6));     // the monitor wakes with the room's light
      run = seq(root, (OPEN ? [
        { src: 'world/01_wide_night.png', at: S, blClock: openClock, keepGrade: true, grade: 'url(#s1void)', vignette: true,
          screen: { src: 'live/shop', state: t => state(t), k: screenK } },
      ] : [
        { src: 'world/01_wide_night.png', at: S, cam: hold(960, 540, 1.0),
          grade: t => `brightness(${easeInOutSine(P(t, M('light_up'), 1.8)).toFixed(3)})` },
        { src: 'world/02_medium_night.png', at: M('medium'), cam: move(M('medium') + .4, M('screen') - M('medium') - .5, [880, 640, 1.04], [842, 626, 1.6], 0),
          screen: { src: 'live/shop', state: t => state(t) } },
      ]).concat([
        // 1.2 into the screen: the room is scaled around the monitor's glass until the live desktop fills the frame
        { src: 'live/shop', at: M('screen'), pin: { d: .6 }, cam: tabCam, state: t => state(t) },
      ]), E, { scene: 1 });
      const room = run.list[0];
      if (room.vignette) {                           // the void: near-black at the edges, the diorama floating in it
        vig = el('div', {}, room.s.box);
        css(vig, { position: 'absolute', left: '0', top: '0', width: '1920px', height: '1080px', zIndex: 39, pointerEvents: 'none',
          background: 'radial-gradient(ellipse 62% 66% at 50% 47%, rgba(3,3,4,0) 62%, rgba(3,3,4,.55) 86%, rgba(3,3,4,.9) 100%)' });
      }
      live = run.list.find(it => it.src === 'live/shop').s;
    },
    ready() {
      // geometry, read once from the live page (logical px = rect / 1.5): each tab's centre with all nine open
      const w = live.win(), pc = w.pc, d = w.document, L = r => [(r.left + r.width / 2) / 1.5, (r.top + r.height / 2) / 1.5];
      pc.render(pc.preset('tabs', { cursor: null }));
      G = { tab: {} };
      for (const id of TABS) G.tab[id] = L(d.querySelector(`.tab[data-id="${id}"]`).getBoundingClientRect());
    },
    render(t) {
      run.render(t);
      if (vig) vig.style.opacity = (1 - easeInOutSine(P(t, M('medium') + .2, 2.4))).toFixed(3);   // gone by the desk
    },
  });

  // the clicks, on the sound of each (the cue sheet's `tab` events): the nine tabs in turn, then "four", then "five"
  const CLICK = () => { const c = []; for (let k = 1; k <= 9; k++) c.push(sfxT('tab', tabT(k))); c.push(sfxT('tab', M('tab4_active')), sfxT('tab', M('tab5_active'))); return c; };
  function cursorAt(t) {
    const c = CLICK(), at = id => G.tab[id], order = TABS.concat(['xls', 'parts']);
    const clicks = c.map((ct, i) => { const p = at(order[i]); return { t: ct, x: p[0] - 6, y: p[1] + 3 }; });
    const x5 = at('parts');
    return hand(t, [M('screen'), at('shop')[0] + 60, at('shop')[1] + 110], clicks, [c[10] + 1.4, x5[0] + 22, x5[1] + 30]);
  }

  function state(t) {
    // all nine already open, as on the 3D monitor (Calendar up); each click makes the old PC load that page
    const n = nOpen(t), nd = needles(t), cl = CLICK(), a4 = cl[9], a5 = cl[10];
    const st = { preset: 'tabs', tabs: TABS, tabIn: 1, ram: +nd.ram.toFixed(4), cpu: +nd.cpu.toFixed(4), secs: 12 + Math.floor(Math.max(0, t - M('screen'))) };
    st.active = t >= a5 ? 'parts' : t >= a4 ? 'xls' : n ? TABS[n - 1] : 'cal';
    const last = t >= a5 ? a5 : t >= a4 ? a4 : n ? tabT(n) : -9, since = t - last;
    st.loading = since < .28 ? +(.15 + .85 * since / .28).toFixed(3) : 0;      // the status bar: "Opening page..."
    if (G) { const c = cursorAt(t); st.cursor = { x: +c[0].toFixed(2), y: +c[1].toFixed(2) }; }
    return st;
  }
})();
