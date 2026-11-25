/* 1 · Nine tabs. INT. SHOP BACK OFFICE, THU 19 NOV 21:47 (CONTINUITY). Black, rain; light comes up on the wide; we
 * drift to the 2009 monitor; full screen, the shop PC LIVE (look/shop-pc, preset `tabs`): Theo's cursor opens the
 * browser from the taskbar, then clicks the new-tab button eight times, one tab per mark (tab1..tab9); each tab grows
 * in, the status bar loads, the CPU needle kicks and the MEMORY needle climbs a notch into the red; the clock
 * gadget's second hand ticks. "Tab four." -> the cursor goes to workload.xls and clicks; "No — five." -> the Parts
 * list (approved look-dev 03b); "It's the one with the spanner." -> push in to the spanner by PARTS LIST. */
(function () {
  const C = CUES.scenes[0], S = C.start, E = C.end;
  const TABS = ['shop', 'supplier', 'sms', 'xls', 'parts', 'invoices', 'email', 'bank', 'cal'];
  let run, live, G = null;
  const tabT = k => M('tab' + k);                   // the k-th tab opens (k = 1..9)
  const nOpen = t => { let n = 0; for (let k = 1; k <= 9; k++) if (t >= tabT(k)) n = k; return n; };
  const GROW = .2;                                  // a tab grows in over 0.2 s
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
    for (const a of [M('tab4_active'), M('tab5_active')]) cpu += .22 * Math.exp(-Math.max(0, t - a) * 4) * (t >= a ? 1 : 0);
    return { ram: clamp(ram, 0, .97), cpu: clamp(cpu, 0, .99) };
  }
  Scene({
    id: '1', start: S, end: E, fadeIn: 0,
    build(root) {
      const tabCam = [[M('screen'), 960, 540, 1.0], [M('tab9') + .2, 990, 470, 1.06], [M('tab5_active'), 900, 430, 1.1],
        [M('spanner') - .1, 860, 380, 1.16], [E, 640, 262, 2.5]];
      run = seq(root, [
        { src: 'world/01_wide_night.png', at: S,
          cam: [[M('light_up'), 960, 540, 1.0], [M('medium') + .5, 880, 455, 1.3]],
          grade: t => `brightness(${easeInOutSine(P(t, M('light_up'), 1.8)).toFixed(3)})` },
        { src: 'world/02_medium_night.png', at: M('medium'), fi: .45,
          cam: [[M('medium'), 880, 640, 1.04], [M('screen') + .4, 842, 626, 1.6]] },
        { src: 'live/shop', at: M('screen'), fi: .35, cam: tabCam, state: t => state(t) },
      ], E);
      live = run.list[2].s;
    },
    ready() {
      // geometry, read once from the live page (logical px = rect / 1.5): the new-tab button with k tabs open, each
      // tab's centre with all nine open, the taskbar's browser button
      const w = live.win(), pc = w.pc, d = w.document, L = r => [(r.left + r.width / 2) / 1.5, (r.top + r.height / 2) / 1.5];
      G = { nt: [], tab: {} };
      for (let k = 1; k <= 9; k++) {
        pc.render(pc.preset('tabs', { tabs: TABS.slice(0, k), active: TABS[k - 1], cursor: null }));
        G.nt[k] = L(d.querySelector('.tab.newtab').getBoundingClientRect());
      }
      for (const id of TABS) G.tab[id] = L(d.querySelector(`.tab[data-id="${id}"]`).getBoundingClientRect());
      G.web = L(d.querySelector('.tb-btn[data-id="web"]').getBoundingClientRect());
    },
    render(t) { run.render(t); },
  });

  function cursorAt(t) {
    // 1) the taskbar browser button (tab 1 opens the browser on the Back Office), 2) the new-tab button, which slides
    // right as each tab grows in, 3) workload.xls, 4) the Parts list, then the hand rests
    const t1 = tabT(1), t9 = tabT(9), a4 = M('tab4_active'), a5 = M('tab5_active');
    const ntAt = u => {                                     // where the new-tab button is at time u
      const n = nOpen(u); if (n < 1) return G.nt[1];
      const grow = clamp((u - tabT(n)) / GROW);
      const a = G.nt[Math.max(1, n - 1)], b = G.nt[n];
      return n === 1 ? G.nt[1] : [lerp(a[0], b[0], easeOutCubic(grow)), b[1]];
    };
    if (t < t1) return path2(t, [[M('screen'), 300, 560], [t1 - .06, G.web[0] + 4, G.web[1] + 2]]);
    if (t < t1 + .2) return path2(t, [[t1, G.web[0] + 4, G.web[1] + 2], [t1 + .2, G.web[0] + 6, G.web[1] - 6]]);
    if (t < tabT(2) - .1) { const nt = G.nt[1]; return path2(t, [[t1 + .2, G.web[0] + 6, G.web[1] - 6], [tabT(2) - .1, nt[0] + 2, nt[1] + 3]]); }
    if (t < t9 + .25) {                                     // ride the button: follow it, clicking at each mark
      const p = ntAt(t); return [p[0] + 2 + wiggle(t, 3, 4, .8), p[1] + 3 + wiggle(t, 4, 3.3, .6)];
    }
    const nt9 = G.nt[9], x4 = G.tab.xls, x5 = G.tab.parts;
    if (t < a5 - .45) return path2(t, [[t9 + .25, nt9[0] + 2, nt9[1] + 3], [t9 + .5, nt9[0] - 40, nt9[1] + 70], [a4 - .05, x4[0] + 10, x4[1] + 2], [a5 - .45, x4[0] + 16, x4[1] + 6]]);
    return path2(t, [[a5 - .45, x4[0] + 16, x4[1] + 6], [a5 - .05, x5[0] - 8, x5[1] + 2], [M('spanner'), x5[0] - 2, x5[1] + 4], [E, x5[0] + 16, x5[1] + 13]]);
  }

  function state(t) {
    const n = nOpen(t), nd = needles(t);
    const st = { preset: 'tabs', ram: +nd.ram.toFixed(4), cpu: +nd.cpu.toFixed(4), secs: 12 + Math.floor(Math.max(0, t - M('screen'))) };
    if (n === 0) Object.assign(st, { browser: false, tabs: [] });
    else {
      const a4 = M('tab4_active'), a5 = M('tab5_active');
      st.tabs = TABS.slice(0, n);
      st.tabIn = +easeOutCubic(clamp((t - tabT(n)) / GROW)).toFixed(4);
      st.active = t >= a5 ? 'parts' : t >= a4 ? 'xls' : TABS[n - 1];
      const since = Math.min(t - tabT(n), t >= a4 ? t - (t >= a5 ? a5 : a4) : 9);
      st.loading = since < .28 ? +(.15 + .85 * since / .28).toFixed(3) : 0;      // the status bar: "Opening page..."
    }
    if (G) { const c = cursorAt(t); st.cursor = { x: +c[0].toFixed(2), y: +c[1].toFixed(2) }; }
    return st;
  }
})();
