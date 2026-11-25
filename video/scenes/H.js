/* Scene H: Any repo (131–146 s). The music's fullest moment.
 * Two more real repos, scanned by Synapse (Quorum: 13 endpoints, ComfyUI: 28), each with a question you could ask
 * Barnaby, then a wide "Your company" card: 40 small old-system tiles light brass one by one (134–143) as Barnaby
 * takes them on. Everything drifts gently forward.
 */
(function () {
  const START = 131, END = 146;
  const REPOS = [                                                        // storyboard H (real endpoint counts)
    { name: 'Quorum', tag: 'offline team memory', ask: 'Any disputed deadlines?', n: 13, at: 131.5, x: 160 },
    { name: 'ComfyUI', tag: '', ask: 'What GPU is it using, and is anything queued?', n: 28, at: 131.85, x: 976 },
  ];
  const CO_AT = 132.2;                                                   // the third card, 0.35 s after the second
  const N = 40, COLS = 10, LIGHT0 = 134.0, LIGHT1 = 143.0, FINAL = 143.35;
  const REPO_SVG = `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="${COL.sub}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H20v16H7.5A2.5 2.5 0 0 0 5 20.5z"/><path d="M5 20.5A2.5 2.5 0 0 0 7.5 23H20v-5"/><path d="M9 6.5h7"/></svg>`;
  const BARS = ['#3B5378', '#565B66', '#3F5F5B', '#62503F', '#4A4F69'];  // dusty old-system title bars (no tier colours)
  let wrap, repos = [], co, coCount, tiles = [];

  Scene({
    id: 'H', start: START, end: END, drift: .02,
    captions: [[131.5, 137.5, 'Point Barnaby at any repo.'],
               [138.0, 145.5, 'Synapse makes it agent-ready. Barnaby makes it grow.']],

    build(root) {
      el('style', { text: `
#scene-H .hc{padding:22px 28px 20px}
#scene-H .top{display:flex;align-items:center;gap:12px}
#scene-H .nm{font-size:34px;color:${COL.ink};line-height:1.1}
#scene-H .tg{font-size:21px;color:${COL.sub}}
#scene-H .st{margin-left:auto;font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:${COL.sub};padding:5px 12px;border:1px solid rgba(212,168,90,.35);border-radius:999px}
#scene-H .mid{display:flex;align-items:flex-end;margin-top:14px}
#scene-H .mid .l{flex:1}
#scene-H .cmd{font-size:17px;line-height:1.55;height:53px;color:${COL.sub}}
#scene-H .pills{margin-top:12px;height:38px;width:340px}
#scene-H .pills i{display:inline-block;width:18px;height:12px;border-radius:4px;margin:0 6px 7px 0;background:#1B202A;border:1px solid #474D59}
#scene-H .num{width:190px;text-align:right}
#scene-H .num b{display:block;font-size:88px;line-height:.9;font-weight:400;color:${COL.brass}}
#scene-H .num span{font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:${COL.sub}}
#scene-H .ask{margin-top:16px;padding-top:14px;border-top:1px solid ${COL.hair};font-size:23px;color:${COL.ink};white-space:nowrap;height:48px}
#scene-H .ask b{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:${COL.muted};margin-right:12px;font-weight:600}
#scene-H .cnt{margin-left:auto;display:flex;align-items:baseline;gap:12px}
#scene-H .cnt b{font-size:56px;line-height:1;font-weight:400;color:${COL.brass};min-width:70px;text-align:right}
#scene-H .cnt span{font-size:15px;letter-spacing:.14em;text-transform:uppercase;color:${COL.sub}}
#scene-H .grid{position:relative;display:grid;grid-template-columns:repeat(${COLS},1fr);gap:16px;margin-top:18px}
#scene-H .tl{position:relative;height:72px;border:1px solid #2B313C;border-radius:9px;padding:3px}
#scene-H .tl .gl{position:absolute;inset:-1px;border-radius:9px;box-shadow:0 0 26px 2px rgba(212,168,90,.75);opacity:0}
#scene-H .tl .tb{height:9px;background:var(--tb)}
#scene-H .tl .bd{padding:6px 6px 0;display:flex;gap:7px}
#scene-H .tl .bd i{display:block;height:6px;background:var(--bar);margin-bottom:6px}
#scene-H .tl .sb{width:20px;height:40px;background:var(--bar);opacity:.6}
#scene-H .tl .tbl{display:grid;grid-template-columns:repeat(3,1fr);gap:3px;flex:1}
#scene-H .tl .tbl i{height:8px;margin:0}
#scene-H .tl .big{width:34px;height:24px;background:var(--bar)}
#scene-H .tl .bl{position:absolute;right:6px;bottom:4px;line-height:0}
` }, root);

      wrap = el('div', { cls: 'abs', style: 'left:0;top:0;width:1920px;height:1080px' }, root);

      // the two repo cards
      for (const r of REPOS) {
        const c = el('div', { cls: 'card hc', style: `left:${r.x}px;top:96px;width:784px` }, wrap);
        c.innerHTML = `<div class="top">${REPO_SVG}<span class="serif nm">${esc(r.name)}</span>` +
          (r.tag ? `<span class="tg">· ${esc(r.tag)}</span>` : '') + `<span class="st"></span></div>
          <div class="mid"><div class="l"><div class="mono cmd"></div><div class="pills"></div></div>
          <div class="num"><b class="serif">0</b><span>endpoints</span></div></div>
          <div class="ask"><b>Ask Barnaby</b><span class="q"></span></div>`;
        const pills = c.querySelector('.pills');
        repos.push({
          ...r, el: c, st: c.querySelector('.st'), cmd: c.querySelector('.cmd'), num: c.querySelector('.num b'),
          askEl: c.querySelector('.ask'), q: c.querySelector('.q'),
          pills: [...Array(r.n)].map(() => el('i', {}, pills)),
        });
      }

      // "Your company": 40 small old-system tiles
      co = el('div', { cls: 'card hc', style: 'left:160px;top:398px;width:1600px' }, wrap);
      co.innerHTML = `<div class="top"><span class="serif nm">Your company</span><span class="tg">· the systems nobody has time to rewrite</span>
        <span class="cnt"><b class="serif">0</b><span>of ${N} looked after</span></span></div><div class="grid"></div>`;
      coCount = co.querySelector('.cnt b');
      const grid = co.querySelector('.grid');
      for (let i = 0; i < N; i++) {
        const kind = Math.floor(rand(i, 11) * 4), w = k => Math.round(35 + rand(i, 20 + k) * 55) + '%';
        let body;
        if (kind === 0) body = `<div style="flex:1"><i style="width:${w(0)}"></i><i style="width:${w(1)}"></i><i style="width:${w(2)}"></i></div>`;
        else if (kind === 1) body = `<div class="tbl">${'<i></i>'.repeat(9)}</div>`;
        else if (kind === 2) body = `<div class="sb"></div><div style="flex:1"><i style="width:${w(0)}"></i><i style="width:${w(1)}"></i><i style="width:${w(2)}"></i></div>`;
        else body = `<div class="big"></div><div style="flex:1"><i style="width:${w(0)}"></i><i style="width:${w(1)}"></i></div>`;
        const tl = el('div', { cls: 'tl', html: `<div class="gl"></div><div class="tb"></div><div class="bd">${body}</div><span class="bl">${BELL(18)}</span>` }, grid);
        tiles.push({ el: tl, gl: tl.querySelector('.gl'), bl: tl.querySelector('.bl'), bar: BARS[Math.floor(rand(i, 3) * BARS.length)], col: i % COLS, row: Math.floor(i / COLS), at: 0 });
      }
      // light order: a left-to-right wave with an organic jitter, one tile at a time, evenly over 134–143
      tiles.map((tl, i) => ({ tl, s: tl.col + rand(i, 31) * 1.8 + tl.row * .15 }))
        .sort((a, b) => a.s - b.s)
        .forEach((o, rank) => { o.tl.at = LIGHT0 + rank * (LIGHT1 - LIGHT0) / (N - 1); });
    },

    render(t) {
      // a slow, steady forward drift of the whole composition
      xf(wrap, { x: lerp(24, -24, P(t, START, END - START)) });

      // repo cards: in from the right, Synapse scans, count fills, the question types
      for (const r of repos) {
        show(r.el, t, r.at, .6, { dx: 70, dy: 0 });
        const scanned = r.at + .95;
        setText(r.st, t < scanned ? 'connecting' : 'connected');
        const kc = pulse(t, scanned + .1, .3);
        r.st.style.borderColor = rgba(COL.brass, .35 + .5 * kc);
        r.st.style.boxShadow = kc > .01 ? `0 0 ${16 * kc}px ${rgba(COL.brass, .6 * kc)}` : 'none';
        const cmd = '$ synapse build --auto', nc = Math.floor(clamp((t - (r.at + .3)) * 45, 0, cmd.length));
        setHTML(r.cmd, `<span style="color:${COL.brass}">${esc(cmd.slice(0, nc))}</span>` +
          (t >= scanned ? `<br><span style="color:${COL.good}">✓ Extracted ${r.n} endpoint(s)</span>` : ''));
        const g = 1.0 / r.n; let seen = 0;
        r.pills.forEach((p, i) => { if (show(p, t, scanned + .05 + i * g, .3, { dy: 6 }) > 0) seen++; });
        setText(r.num, String(seen));
        show(r.askEl, t, r.at + 1.6, .5, { dy: 10 });
        const nq = Math.floor(clamp((t - (r.at + 1.7)) * 34, 0, r.ask.length));
        setText(r.q, nq ? '“' + r.ask.slice(0, nq) + (nq >= r.ask.length ? '”' : '') : '');
        // the final flourish reaches the top cards too
        const fin = pulse(t, FINAL + .15, .45);
        r.el.style.borderColor = rgba(COL.brass, .28 + .4 * fin);
      }

      // Your company
      show(co, t, CO_AT, .6, { dy: 40 });
      let lit = 0;
      for (const tl of tiles) {
        show(tl.el, t, CO_AT + .3 + tl.col * .045 + tl.row * .035, .45, { dy: 10 });
        const k = E(t, tl.at, .55, easeOutCubic);
        if (t >= tl.at) lit++;
        const fl = pulse(t, tl.at + .08, .22) + .7 * pulse(t, FINAL + tl.col * .03, .32);
        tl.el.style.borderColor = mixColor('#2B313C', COL.brass, k);
        tl.el.style.background = mixColor('#151920', '#221D15', k);
        tl.gl.style.opacity = clamp(.16 * k + .7 * fl);                        // fixed glow, only its opacity moves
        tl.el.style.setProperty('--tb', mixColor(tl.bar, COL.brassDeep, k * .9));
        tl.el.style.setProperty('--bar', mixColor('#2F3541', '#5F5038', k));
        tl.bl.style.opacity = k;
      }
      setText(coCount, String(lit));
      const kn = pulse(t, FINAL, .4);
      coCount.style.textShadow = kn > .01 ? `0 0 ${28 * kn}px ${rgba(COL.brass, .8 * kn)}` : 'none';
      co.style.borderColor = rgba(COL.brass, .28 + .3 * E(t, LIGHT1, 1.2, easeInOutCubic) + .3 * kn);
    },
  });
})();
