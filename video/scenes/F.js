/* Scene F: Build (82–120 s). The centrepiece.
 * Martin asks who's overloaded. The shop has no notion of workload ("Reports (coming soon!!)"), so Barnaby writes
 * the endpoint himself in a worktree: the real diff types in (services.py, then routes_reports.py), the real tests
 * run (22 passed), the build approval card shows the real diff, Martin approves, it merges, Synapse rediscovers
 * 24 endpoints, the new violet chip pops, Barnaby reads the new report and answers, and Dev's wheel builds move to
 * Priya in the 2009 window. Everything shown comes from DATA (data.js) or the storyboard.
 */
(function () {
  const START = 82, END = 120;
  const VO = { ask: 82.6, say1: 85.2, say2: 107.3, yes: 114.5 };                        // cues.json -> voice
  const ASK = 'Who’s overloaded this week?', ASK_DUR = 2.3;                              // audio/voice/manifest.json
  const SAY1 = 'The system has no notion of workload, sir. I can teach it.', SAY1_DUR = 4.97;
  const SAY2 = 'Dev has thirty-one hours booked against twenty. Shall I move the two wheel builds to Priya?', SAY2_DUR = 6.8;
  const YES = 'Yes, please.', YES_DUR = 1.58;
  const T = {
    row: 90.25, panel: 90.4, typeA: 90.8, typeB: 96.3, pytest: 96.8, passed: 98.3, card: 99.3, press: 102.8,
    merged: 103.3, restarted: 103.95, discover: 104.5, extracted: 105.3, chip: 105.8, read: 106.8,
    flipA: 116.3, flipB: 116.8,
  };
  const NEW_EP = DATA.build.endpoints[0];                       // GET /api/reports/workload/{day}
  const BRANCH = 'barnaby/api-reports-workload';
  const N_EP = DATA.endpoints.length + DATA.build.endpoints.length;   // 24
  const SPEC = (DATA.turns[2].calls.find(c => c.tool === 'build') || { input: { spec: '' } }).input.spec;
  const TESTED = /^(\d+) passed(.*)$/.exec(DATA.build.tested) || [DATA.build.tested, '0', ''];
  const LIT = [...DATA.starter, 'POST /api/purchase-orders'];   // exposed before this scene (B + D)
  const ASSIGN = 'POST /api/jobs/{job_id}/assign';

  // worktree panel geometry
  const PX = 80, PY = 120, PW = 880, PH = 760, TITLE_H = 46, TABS_H = 40, LH = 25, TERM_H = 176;
  const BASE = .035, SWITCH = .35;                              // per-line newline/indent beat, file-switch pause

  let root, shop, shopBody, navReports, wt, tabEls = [], codeBox, files = [], term, termBody, switchT = 0;
  let hd, stateEl, sayEl, buildRow, buildTag, specEl, tbox, map, newChip, assignChip, readRow, card, cursor, ripple;
  const S = {};

  const CSS = `
#scene-F .wt{position:absolute;background:#0B0E13;border:1px solid rgba(144,133,233,.5);border-radius:16px;overflow:hidden;
  box-shadow:0 40px 90px rgba(0,0,0,.6),0 0 60px rgba(144,133,233,.13)}
#scene-F .wt-title{display:flex;align-items:center;gap:10px;height:${TITLE_H}px;padding:0 18px;background:#131722;border-bottom:1px solid #262B35;
  font:16px "Cascadia Mono",Consolas,monospace;color:#F1ECE1}
#scene-F .wt-title .r{margin-left:auto;font:14px "Segoe UI",sans-serif;color:#8D8778;letter-spacing:.04em}
#scene-F .wt-tabs{display:flex;height:${TABS_H}px;background:#0F121A;border-bottom:1px solid #262B35}
#scene-F .wt-tab{display:flex;align-items:center;gap:9px;padding:0 18px;font:15px "Cascadia Mono",Consolas,monospace;color:#8D8778;border-right:1px solid #1C2029}
#scene-F .wt-tab.on{color:#F1ECE1;background:#0B0E13;box-shadow:inset 0 2px 0 #9085E9}
#scene-F .wt-tab .n{color:#9085E9;font-size:13px}
#scene-F .wt-code{position:absolute;left:0;right:0;top:${TITLE_H + TABS_H}px;overflow:hidden}
#scene-F .wt-file{position:absolute;left:0;right:0;top:0;padding-top:10px}
#scene-F .ln{display:flex;height:${LH}px;font:16px/${LH}px "Cascadia Mono",Consolas,monospace;white-space:pre}
#scene-F .ln .g{flex:none;width:58px;text-align:right;padding-right:12px;color:#4A505C;font-size:14px}
#scene-F .ln .m{flex:none;width:3px;margin-right:16px}
#scene-F .ln.add .m{background:rgba(144,133,233,.85)}
#scene-F .ln .c{flex:1;min-width:0;overflow:hidden;color:#D9D3C5}
#scene-F .ln.ctx .c{opacity:.45}
#scene-F .ln.fold .c{color:#6F6A5E;font-style:italic}
#scene-F .ln.cur{background:rgba(144,133,233,.09)}
#scene-F .ln.cur .g{color:#C2BBA9}
#scene-F .kw,#scene-F .dec{color:#ACA2F4}
#scene-F .fn{color:#F1ECE1;font-weight:700}
#scene-F .str{color:#D8C49B}
#scene-F .doc{color:#8D8778}
#scene-F .cm{color:#6F6A5E}
#scene-F .num{color:#F0CF8F}
#scene-F .p{color:#9C968A}
#scene-F .cu{color:#B6ADF7}
#scene-F .wt-fade{position:absolute;right:0;top:0;bottom:0;width:70px;background:linear-gradient(90deg,rgba(11,14,19,0),#0B0E13)}
#scene-F .wt-term{position:absolute;left:0;right:0;bottom:0;background:#08090D;border-top:1px solid #262B35;overflow:hidden;
  font:17px/1.6 "Cascadia Mono",Consolas,monospace;color:#C2BBA9}
#scene-F .wt-term .h{font:600 12px "Segoe UI",sans-serif;letter-spacing:.16em;color:#8D8778;padding:12px 20px 6px}
#scene-F .wt-term .b{padding:0 20px}
#scene-F .wt-term .pr{color:#D4A85A}
#scene-F .wt-term .ok{color:#22C55E;font-weight:700}
#scene-F .tr.fb{background:linear-gradient(90deg,rgba(144,133,233,.11),transparent 60%),#1B202A}
#scene-F .spec{background:#11141B;border:1px solid #262B35;border-left:3px solid rgba(144,133,233,.7);border-radius:10px;padding:10px 14px;
  margin-bottom:8px;font:15px/1.5 "Segoe UI",sans-serif;color:#A9A292;height:158px;overflow:hidden;
  -webkit-mask-image:linear-gradient(#000 62%,transparent)}
#scene-F .spec b{font:600 12px "Segoe UI",sans-serif;letter-spacing:.16em;color:#9085E9;margin-right:10px}
#scene-F .ftbox{font-size:17px;line-height:1.55;color:#C2BBA9;background:#0B0E13;border:1px solid #262B35;border-radius:12px;
  padding:10px 14px;margin-bottom:12px;height:128px}
#scene-F .fmap{margin-bottom:6px}
#scene-F .fmap .ep{font-size:12.5px;padding:4px 8px;margin:0 6px 6px 0}
#scene-F .apcard.fb{border-color:rgba(144,133,233,.7);background:linear-gradient(160deg,rgba(144,133,233,.13),transparent 60%),#161A22;
  box-shadow:0 20px 50px rgba(0,0,0,.45);margin-top:4px}
#scene-F .apcard.fb .diff{font-size:15px;line-height:1.45}
#scene-F .apcard.fb .t{text-wrap:balance}
#scene-F .apcard.fb .btn:not(.ghost){background:linear-gradient(#ABA2F3,#7E72DB);color:#120F24}
`;
  const BRANCH_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9085E9" stroke-width="2.2" stroke-linecap="round"><circle cx="6" cy="5" r="2.4"/><circle cx="6" cy="19" r="2.4"/><circle cx="18" cy="7" r="2.4"/><path d="M6 7.4v9.2M18 9.4c0 4.6-5 4.2-10.4 7.6"/></svg>';
  const CURSOR_SVG = '<svg width="30" height="30" viewBox="0 0 24 24"><path d="M3 2 L3 19.5 L7.6 15.2 L10.7 22 L13.6 20.8 L10.6 14.1 L16.8 14.1 Z" fill="#fff" stroke="#0E1117" stroke-width="1.4" stroke-linejoin="round"/></svg>';

  /* ---------- the real diff, parsed: rows per file with real line numbers ---------- */
  function parseDiff(diff) {
    const out = []; let f = null, next = 0;
    for (const line of diff.split('\n')) {
      if (line.startsWith('diff --git')) { f = { name: line.replace(/^diff --git a\/(\S+).*$/, '$1'), rows: [], added: 0 }; out.push(f); continue; }
      if (!f || /^(index |--- |\+\+\+ |new file mode)/.test(line)) continue;
      if (line.startsWith('@@')) { const m = /^@@ -\S+ \+(\d+)(?:,\d+)? @@ ?(.*)$/.exec(line); next = m ? +m[1] : 1; f.rows.push({ kind: 'fold', text: m ? m[2] : '' }); continue; }
      if (line.startsWith('+')) { f.rows.push({ kind: 'add', n: next++, text: line.slice(1) }); f.added++; continue; }
      if (line.startsWith('-') || line === '') continue;
      f.rows.push({ kind: 'ctx', n: next++, text: line.slice(1) });
    }
    return out;
  }

  /* ---------- a small Python tinter (keywords, strings, docstrings, numbers) ---------- */
  const KW = new Set('def return try except for in if else elif import from as lambda not and or is None True False with while class pass raise'.split(' '));
  function tint(rows) {
    let open = null, prev = '';
    for (const r of rows) {
      if (r.kind === 'fold') continue;
      const s = r.text, segs = []; let i = 0, lastWord = '';
      const push = (txt, c = '') => { if (!txt) return; const L = segs[segs.length - 1]; if (L && L[1] === c) L[0] += txt; else segs.push([txt, c]); };
      if (open) {
        const j = s.indexOf(open.q);
        if (j < 0) { push(s, open.c); i = s.length; } else { push(s.slice(0, j + 3), open.c); i = j + 3; open = null; }
      }
      while (i < s.length) {
        const ch = s[i], q3 = s.substr(i, 3);
        if (ch === '#') { push(s.slice(i), 'cm'); break; }
        if (q3 === '"""' || q3 === "'''") {
          const c = (!s.slice(0, i).trim() && /:\s*$/.test(prev)) ? 'doc' : 'str';
          const j = s.indexOf(q3, i + 3);
          if (j < 0) { push(s.slice(i), c); open = { q: q3, c }; i = s.length; } else { push(s.slice(i, j + 3), c); i = j + 3; }
          continue;
        }
        if (ch === '"' || ch === "'") { let j = i + 1; while (j < s.length && s[j] !== ch) j += s[j] === '\\' ? 2 : 1; push(s.slice(i, j + 1), 'str'); i = j + 1; continue; }
        if (ch === '@' && !s.slice(0, i).trim()) { const m = /^@[\w.]+/.exec(s.slice(i)); push(m[0], 'dec'); i += m[0].length; continue; }
        if (/[A-Za-z_]/.test(ch)) {
          const w = /^\w+/.exec(s.slice(i))[0];
          if (w === 'f' && (s[i + 1] === '"' || s[i + 1] === "'")) { push(w, 'str'); i += 1; continue; }
          push(w, KW.has(w) ? 'kw' : lastWord === 'def' ? 'fn' : ''); lastWord = w; i += w.length; continue;
        }
        if (/\d/.test(ch)) { const w = /^\d+(\.\d+)?/.exec(s.slice(i))[0]; push(w, 'num'); i += w.length; continue; }
        push(ch, /[()[\]{}:,.=<>+\-*/%]/.test(ch) ? 'p' : ''); i++;
      }
      r.segs = segs;
      if (s.trim()) prev = s;
    }
  }
  function segHTML(segs, n) {
    let out = '', left = n;
    for (const [s, c] of segs) {
      if (left <= 0) break;
      const part = s.slice(0, left); left -= part.length;
      out += c ? `<span class="${c}">${esc(part)}</span>` : esc(part);
    }
    return out;
  }

  /* ---------- small helpers ---------- */
  // an in-flow slot whose height is animated (so rows/cards slide open in the HUD instead of jumping)
  function slot(parent) { const s = el('div', { style: 'overflow:hidden;height:0px' }, parent); const inner = el('div', { style: 'display:flow-root' }, s); return { s, inner }; }
  function setSlot(o, k) {
    if (k >= 1) { o.s.style.height = ''; o.s.style.overflow = 'visible'; }
    else { o.s.style.overflow = 'hidden'; o.s.style.height = (k > 0 ? k * o.inner.offsetHeight : 0) + 'px'; }
  }
  function offsetIn(e, stop) { let x = 0, y = 0; while (e && e !== stop) { x += e.offsetLeft; y += e.offsetTop; e = e.offsetParent; } return { x, y }; }
  const ok = s => `<span style="color:${COL.good}">✓ ${esc(s)}</span>`;

  function stateAt(t) {
    if (t < VO.ask + ASK_DUR) return 'listening';
    if (t < VO.say1) return 'thinking';
    if (t < T.row) return 'speaking';
    if (t < T.pytest) return 'writing code';
    if (t < T.passed) return 'running tests';
    if (t < T.card) return 'tests passed';
    if (t < T.press) return 'awaiting approval';
    if (t < T.chip) return 'merging';
    if (t < VO.say2) return 'thinking';
    if (t < VO.yes - .2) return 'speaking';
    if (t < T.flipA - .3) return 'listening';
    return 'working';
  }

  Scene({
    id: 'F', start: START, end: END, drift: .02,
    captions: [[116.6, 119.8, 'Build: the report Theo never wrote. Tested, approved, live.']],

    build(r) {
      root = r;
      el('style', { text: CSS }, root);

      // the 2009 window, exactly where C–E left it
      shop = shop2009({ parent: root, x: 80, y: 150, w: 1100, page: 'Jobs' });
      shopBody = shop.el.querySelector('.xp-body');
      navReports = [...shop.el.querySelectorAll('.xp-nav a')].find(a => /^Reports/.test(a.textContent));

      // ---- Barnaby's worktree: editor + terminal ----
      const parsed = parseDiff(DATA.build.diff);
      const svc = parsed.find(f => f.name === 'services.py'), rts = parsed.find(f => f.name === 'routes_reports.py');
      const tst = parsed.find(f => /^tests\//.test(f.name));
      files = [svc, rts];
      wt = el('div', { cls: 'wt', style: `left:${PX}px;top:${PY}px;width:${PW}px;height:${PH}px` }, root);
      el('div', { cls: 'wt-title', html: `${BRANCH_SVG}<span>worktree · ${BRANCH}</span><span class="r">spokes-and-sprockets</span>` }, wt);
      const tabs = el('div', { cls: 'wt-tabs' }, wt);
      tabEls = [svc, rts, tst].filter(Boolean).map(f => el('div', { cls: 'wt-tab', html: `<span>${esc(f.name)}</span><span class="n">+${f.added}</span>` }, tabs));
      codeBox = el('div', { cls: 'wt-code' }, wt);
      for (const F of files) {
        tint(F.rows);
        F.el = el('div', { cls: 'wt-file' }, codeBox);
        for (const rw of F.rows) {
          rw.el = el('div', { cls: 'ln ' + rw.kind }, F.el);
          rw.g = el('span', { cls: 'g', text: rw.kind === 'fold' ? '⋮' : String(rw.n) }, rw.el);
          el('span', { cls: 'm' }, rw.el);
          rw.c = el('span', { cls: 'c' }, rw.el);
          if (rw.kind === 'fold') setText(rw.c, '⋯  ' + rw.text);
          else { rw.html = segHTML(rw.segs, Infinity); if (rw.kind === 'ctx') setHTML(rw.c, rw.html); }
        }
      }
      el('div', { cls: 'wt-fade' }, codeBox);
      // typing schedule: indentation appears at once (auto-indent), the rest streams at one steady rate
      let chars = 0, nAdd = 0;
      for (const F of files) for (const rw of F.rows) if (rw.kind === 'add') {
        rw.indent = /^ */.exec(rw.text)[0].length; rw.len = rw.text.length - rw.indent; chars += rw.len; nAdd++;
      }
      const cps = chars / (T.typeB - T.typeA - SWITCH - BASE * nAdd);
      let tt = T.typeA;
      files.forEach((F, fi) => {
        if (fi) tt += SWITCH;
        F.t0 = tt;
        for (const rw of F.rows) if (rw.kind === 'add') { rw.t0 = tt; rw.dur = BASE + rw.len / cps; tt += rw.dur; }
        F.t1 = tt;
      });
      switchT = svc.t1 + SWITCH * .3;
      term = el('div', { cls: 'wt-term' }, wt);
      el('div', { cls: 'h', text: 'TERMINAL' }, term);
      termBody = el('div', { cls: 'b' }, term);

      // ---- Barnaby's display ----
      hd = hud({ parent: root, x: 1000, y: 120, w: 840 });
      stateEl = hd.el.querySelector('.hud-state');
      sayEl = hd.el.querySelector('.hud-say');
      S.build = slot(hd.trace); S.spec = slot(hd.trace); S.term = slot(hd.trace); S.map = slot(hd.trace); S.read = slot(hd.trace);
      buildRow = traceRow(S.build.inner, { kind: 'build', name: 'barnaby · build', args: NEW_EP, tag: 'writing' });
      buildRow.el.classList.add('fb');
      buildTag = buildRow.el.querySelector('.tag');
      specEl = el('div', { cls: 'spec', html: `<b>SPEC</b>${esc(SPEC)}` }, S.spec.inner);
      tbox = el('div', { cls: 'mono ftbox' }, S.term.inner);
      map = endpointMap({ parent: S.map.inner, x: 0, y: 0, w: 792 });
      map.el.classList.add('fmap'); map.el.style.position = 'relative';
      newChip = map.add(NEW_EP);
      newChip.el.style.transformOrigin = '12% 50%';   // pop grows rightwards, so it never spills past the HUD's padding
      assignChip = map.chips.find(c => c.key === ASSIGN);
      readRow = traceRow(S.read.inner, { kind: 'read', name: 'shop · workload', args: '{day: today}', tag: 'read' });
      S.card = slot(hd.cards);
      card = approvalCard({ parent: S.card.inner, kind: 'build', title: 'Add GET /api/reports/workload/{day} to the shop’s back office',
        diff: DATA.build.diff, diffLines: 14, primary: 'Approve and merge' });
      card.el.classList.add('fb');
      Object.assign(card.el.style, { position: 'relative', left: '0px', top: '0px', width: 'auto' });
      el('span', { cls: 'muted', text: 'read the diff first', style: 'margin-left:auto;align-self:center;font-size:15px' }, card.btn.parentElement);

      // Martin's pointer, for the approval click
      cursor = el('div', { cls: 'abs', html: CURSOR_SVG, style: 'left:0;top:0;width:30px;height:30px;transform-origin:4px 2px;filter:drop-shadow(0 4px 8px rgba(0,0,0,.6))' }, root);
      ripple = el('div', { cls: 'abs', style: `left:-30px;top:-30px;width:60px;height:60px;border-radius:50%;border:2px solid ${COL.build};box-shadow:0 0 18px ${rgba(COL.build, .6)}` }, root);
    },

    render(t) {
      /* ---------------- the 2009 window ---------------- */
      const dim = E(t, T.panel, .6, easeInOutCubic) * (1 - E(t, T.merged + .12, .5, easeInOutCubic));
      shop.el.style.transform = ''; shop.el.style.opacity = 1 - dim;
      // "shop restarted": the page blinks as it reloads
      shopBody.style.opacity = keyframes(t, [[T.restarted, 1], [T.restarted + .07, .1], [T.restarted + .5, 1]]);
      // "no notion of workload": Theo's reports tab still says coming soon
      const navK = E(t, 86.4, .5, easeInOutCubic) * (1 - E(t, T.panel - .2, .5, easeInOutCubic));
      navReports.style.background = navK > .01 ? `linear-gradient(${mixColor('#ffffff', '#FFF4B0', navK)},${mixColor('#E3E0D8', '#FFDD55', navK)})` : '';
      navReports.style.boxShadow = navK > .01 ? `0 0 0 ${2 * navK}px rgba(255,204,0,${.9 * navK})` : '';
      // Martin says yes: Dev's two wheel builds go to Priya
      for (const [rowI, at] of [[0, T.flipA], [1, T.flipB]]) {
        const on = t >= at;
        shop.set(rowI, 1, on ? 'Priya' : 'Dev', on ? E(t, at, .25) * (.62 + .38 * pulse(t, at + .2, .35)) : 0);
        shop.cells[rowI][1].style.fontWeight = on ? 'bold' : '';
      }

      /* ---------------- the worktree panel ---------------- */
      show(wt, t, T.panel, .6, { dy: 28, scale: .97, out: T.merged - .05, outD: .38, outDy: -30 });
      // while Martin reads the card, the worktree steps back (darkened, not see-through)
      wt.style.filter = `brightness(${1 - .5 * E(t, T.card, .6, easeInOutCubic)})`;
      const active = t < switchT ? 0 : 1;
      tabEls.forEach((e, i) => { e.className = 'wt-tab' + (i === active ? ' on' : ''); });
      const termK = E(t, T.pytest - .35, .5, easeInOutCubic);
      const termH = TERM_H * termK, codeH = PH - TITLE_H - TABS_H - termH;
      codeBox.style.height = codeH + 'px';
      term.style.height = termH + 'px'; term.style.opacity = termK;
      const cursorOn = t < T.pytest - .2;
      files.forEach((F, fi) => {
        const vis = fi === 0 ? 1 - P(t, switchT - .1, .2) : P(t, switchT, .2);
        F.el.style.opacity = vis;
        let cur = -1, curK = 0;
        F.rows.forEach((rw, i) => {
          if (rw.kind !== 'add') { rw.el.className = 'ln ' + rw.kind; return; }
          const started = t >= rw.t0;
          rw.el.style.display = started ? '' : 'none';
          if (!started) { setHTML(rw.c, ''); rw.el.className = 'ln add'; return; }
          const k = rw.len ? clamp((t - rw.t0 - BASE) / (rw.dur - BASE)) : 1;
          cur = i; curK = k;
          rw.k = k;
        });
        F.rows.forEach((rw, i) => {
          if (rw.kind !== 'add' || t < rw.t0) return;
          const isCur = i === cur && fi === active && cursorOn;
          const n = rw.indent + Math.floor(rw.k * rw.len);
          const solid = t < F.t1 + .05 || fi !== files.length - 1;
          const caret = isCur && (solid || blink(t, 1.6)) ? '<span class="cu">▍</span>' : '';
          setHTML(rw.c, (rw.k >= 1 ? rw.html : segHTML(rw.segs, n)) + caret);
          rw.el.className = 'ln add' + (isCur ? ' cur' : '');
        });
        // scroll so the line being written stays in view (continuous, so the window glides)
        const visRows = (codeH - 10) / LH;
        const scroll = Math.max(0, (cur < 0 ? 0 : cur + curK) - (visRows - 3.2));
        F.el.style.transform = `translateY(${-scroll * LH}px)`;
      });
      // pytest, in the worktree
      const cmd = 'python -m pytest -q';
      const nCmd = Math.floor(clamp((t - T.pytest) * 40, 0, cmd.length));
      const nTests = +TESTED[1];
      const nd = Math.floor(nTests * P(t, T.pytest + .62, T.passed - .12 - (T.pytest + .62)));
      const tl = [];
      if (t >= T.pytest - .3) tl.push(`<div><span class="pr">$ ${esc(cmd.slice(0, nCmd))}</span>${t < T.passed && (nCmd < cmd.length || blink(t, 1.6)) && nd === 0 ? '<span class="cu">▍</span>' : ''}</div>`);
      if (nd > 0) tl.push(`<div><span style="color:${COL.good}">${'.'.repeat(nd)}</span>${nd >= nTests ? '<span class="muted">' + ' '.repeat(Math.max(2, 40 - nTests)) + '[100%]</span>' : ''}</div>`);
      if (t >= T.passed) {
        const g = pulse(t, T.passed + .15, .35);
        tl.push(`<div><span class="ok" style="text-shadow:0 0 ${16 * g}px rgba(34,197,94,${.8 * g})">${nTests} passed</span><span class="muted">${esc(TESTED[2])}</span></div>`);
      }
      setHTML(termBody, tl.join(''));

      /* ---------------- Barnaby's display ---------------- */
      hd.el.style.opacity = 1; hd.el.style.transform = '';
      hd.setState(stateAt(t));
      const building = t >= T.row && t < T.chip;
      stateEl.style.color = building ? '#C9C2F7' : '';
      stateEl.style.borderColor = building ? rgba(COL.build, .6) : '';
      // Martin
      const yesN = Math.floor(clamp((t - VO.yes) * YES.length / (YES_DUR * .92), 0, YES.length));
      const askN = Math.floor(clamp((t - VO.ask) * ASK.length / (ASK_DUR * .92), 0, ASK.length));
      hd.setYou('Martin', yesN > 0 ? YES.slice(0, yesN) : ASK.slice(0, askN));
      // Barnaby's lines: the first folds away as the build starts; the answer comes after the new report is read
      sayEl.style.overflow = 'hidden'; sayEl.style.height = '';
      if (t < VO.say2) {
        hd.say(SAY1, t, VO.say1, SAY1.length / (SAY1_DUR * .92));
        const kc = E(t, T.row - .05, .5, easeInOutCubic);
        sayEl.style.opacity = 1 - kc;
        if (kc > 0) sayEl.style.height = ((1 - kc) * sayEl.offsetHeight) + 'px';
      } else {
        hd.say(SAY2, t, VO.say2, SAY2.length / (SAY2_DUR * .92));
        sayEl.style.opacity = 1;
      }
      // the build row: one row whose status walks through the whole build
      setSlot(S.build, E(t, T.row, .45, easeInOutCubic));
      buildRow.render(t, T.row + .05);
      const passTag = `${nTests} passed`;
      const tag = t < T.pytest ? 'writing' : t < T.passed ? 'testing' : t < T.card ? passTag : t < T.press ? 'awaiting approval'
        : t < T.merged ? 'approved' : t < T.chip ? 'merged' : 'live';
      setText(buildTag, tag);
      buildTag.style.color = tag === passTag ? COL.good : COL.build;
      // the row's dot breathes while Barnaby is working on it
      const dot = buildRow.el.firstElementChild, busy = t >= T.row && t < T.passed;
      dot.style.boxShadow = busy ? `0 0 ${6 + 6 * (.5 + .5 * Math.sin(t * 6))}px ${rgba(COL.build, .9)}` : '';
      // the spec Barnaby handed his builder (real), folded away when the approval card arrives
      setSlot(S.spec, E(t, T.row + .15, .5, easeInOutCubic) * (1 - E(t, T.card - .4, .5, easeInOutCubic)));
      show(specEl, t, T.row + .3, .5, { dy: 8, out: T.card - .45, outD: .3 });
      // approval card (violet), Martin's click, then it folds away
      setSlot(S.card, E(t, T.card - .1, .5, easeInOutCubic) * (1 - E(t, T.press + .35, .4, easeInOutCubic)));
      show(card.el, t, T.card, .55, { dy: 18, out: T.press + .28, outD: .3 });
      const pk = pulse(t, T.press, .12), hov = E(t, T.press - .25, .2) * (1 - P(t, T.press + .3, .2));
      card.btn.style.transform = `scale(${1 - .07 * pk})`;
      card.btn.style.filter = `brightness(${1 + .12 * hov + .35 * pk})`;
      // status lines after the merge (the same little console Synapse used on arrival)
      setSlot(S.term, E(t, T.merged - .15, .45, easeInOutCubic));
      const dc = '$ synapse build --discover';
      const nDc = Math.floor(clamp((t - T.discover) * 40, 0, dc.length));
      const sl = [];
      if (t >= T.merged) sl.push(ok(`${BRANCH} merged into main`));
      if (t >= T.restarted) sl.push(ok('shop restarted'));
      if (t >= T.discover) sl.push(`<span style="color:${COL.brass}">${esc(dc.slice(0, nDc))}</span>`);
      if (t >= T.extracted) sl.push(ok(`Extracted ${N_EP} endpoint(s)`));
      setHTML(tbox, sl.join('<br>'));
      // the endpoint map: 23 as before, then the 24th, violet, with a pop
      setSlot(S.map, E(t, T.discover + .1, .55, easeInOutCubic));
      const lit = new Set(LIT); if (t >= T.flipA - .3) lit.add(ASSIGN);
      map.render(t, T.discover + .25, lit, t >= T.chip ? new Set([NEW_EP]) : new Set(), .012);
      pop(newChip.el, t, T.chip, .7, .5);
      for (const c of map.chips) c.el.style.boxShadow = '';
      const g = pulse(t, T.chip + .15, .45);
      newChip.el.style.boxShadow = t >= T.chip ? `0 0 0 4px rgba(144,133,233,.22),0 0 ${30 * g}px rgba(144,133,233,${.9 * g})` : '';
      if (assignChip) { const a = pulse(t, T.flipA - .1, .3); assignChip.el.style.boxShadow = a > .01 ? `0 0 ${16 * a}px ${rgba(COL.brass, .8 * a)}` : ''; }
      // Barnaby reads the new report
      setSlot(S.read, E(t, T.read - .1, .35, easeInOutCubic));
      readRow.render(t, T.read);

      /* ---------------- Martin's pointer ---------------- */
      const b = offsetIn(card.btn, root);
      const bx = b.x + card.btn.offsetWidth * .5, by = b.y + card.btn.offsetHeight * .55;
      const mk = E(t, T.press - .95, .8, easeInOutCubic);
      const cx = lerp(bx - 360, bx, mk) + Math.sin(Math.PI * mk) * 40, cy = lerp(by + 230, by, mk) - Math.sin(Math.PI * mk) * 30;
      const cs = 1 - .14 * pulse(t, T.press, .07);
      cursor.style.transform = `translate(${cx - 3.75}px,${cy - 2.5}px) scale(${cs})`;
      // gone by T.merged - .15, before the status console opens above the card and moves the button
      cursor.style.opacity = P(t, T.press - 1.05, .25) * (1 - P(t, T.press + .12, .2));
      const rk = P(t, T.press, .5);
      ripple.style.transform = `translate(${bx}px,${by}px) scale(${.25 + 1.3 * easeOutCubic(rk)})`;
      ripple.style.opacity = t >= T.press ? .85 * (1 - rk) : 0;
    },
  });
})();
