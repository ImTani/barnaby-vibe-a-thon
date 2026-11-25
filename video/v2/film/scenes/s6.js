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

  /* 6.5 · The change, drafted on a copy. Martin's plan (comp/martin-build, the room still "Reports, planned 2011") under
   * a sheet of tracing paper; on it, in pencil, the Workload room beside the back office: its walls and door (sheet 1,
   * routes_reports.py), its sums, three mechanics' hours (sheet 2, services.py), then its measurements and notes, each
   * row ticked (sheet 3, tests/test_workload.py). The title block counts each sheet's lines as he draws; a typed margin
   * slip carries real lines of the change (THEO_DIFF, quoted, never retyped). On 'checks' Theo's 22 checks land as
   * stamps, 19 kept and 3 new, then one approval: 22 PASSED. Brass marks only where he is working (the pencil's point,
   * the typing head). Everything is in the comp's source px (the shot's layer); everything is a pure function of t. */
  function drafting(layer, T) {
    const INK = '#1D1B17', LEAD = '#2E2B26', BRASS = '#D3A14A', BLUE = '#173C72', ROSE = '#B0285F', GREEN = '#2F6B25';
    const X0 = 46, Y0 = 124, SW = 1300, SH = 924;                      // the sheet, in layer px
    const A = T.code, PH = [[A + 1.05, .95], [A + 2.0, 1.25], [A + 3.25, 1.3]];   // sheets 1..3: start, duration
    const STAMP = .046, APPROVE = T.checks + 22 * STAMP + .2;
    // the working frame after the push is x 408..1920, y 175..1025: the title block sits in the sheet's bottom-right
    // corner, the approval just above it, the margin slip right of the sheet
    const TB = [600, 738, 716, 252], OK = [998, 646], STRIP = [1386, 226, 470];
    const INKMASK = 'url("data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="260" height="260">' +
      '<filter id="i" x="0" y="0"><feTurbulence type="fractalNoise" baseFrequency=".55" numOctaves="3" seed="23" stitchTiles="stitch"/>' +
      '<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -4 3.0"/></filter><rect width="260" height="260" filter="url(#i)"/></svg>') + '")';
    const NOISE = 'url("data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">' +
      '<filter id="n" x="0" y="0"><feTurbulence type="fractalNoise" baseFrequency=".75" numOctaves="3" seed="11" stitchTiles="stitch"/>' +
      '<feColorMatrix values="0 0 0 0 .42  0 0 0 0 .38  0 0 0 0 .30  0 0 0 1.1 -.42"/></filter>' +
      '<filter id="c" x="0" y="0"><feTurbulence type="fractalNoise" baseFrequency=".012" numOctaves="3" seed="4" stitchTiles="stitch"/>' +
      '<feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 .98  0 0 0 .9 -.25"/></filter>' +
      '<rect width="300" height="300" filter="url(#c)"/><rect width="300" height="300" filter="url(#n)"/></svg>') + '")';
    if (!document.getElementById('s6-drafting')) el('style', { attrs: { id: 's6-drafting' }, html: `
      .dr-sheet{left:${X0}px;top:${Y0}px;width:${SW}px;height:${SH}px;background:rgba(250,248,241,.78);
        backdrop-filter:blur(1.6px) saturate(.7);-webkit-backdrop-filter:blur(1.6px) saturate(.7);
        box-shadow:0 22px 48px rgba(52,40,20,.15),0 2px 6px rgba(52,40,20,.10);outline:1px solid rgba(140,128,104,.22);transform-origin:710px 252px}
      .dr-sheet>*{position:absolute}
      .dr-grain{left:0;top:0;width:100%;height:100%;background-image:${NOISE};background-size:300px 300px;mix-blend-mode:multiply;opacity:.55}
      .dr-tape{position:absolute;width:138px;height:38px;background:rgba(232,221,190,.84);box-shadow:0 1px 2px rgba(60,45,20,.14);
        clip-path:polygon(0 4%,8% 0,17% 6%,26% 1%,35% 5%,46% 0,57% 5%,68% 1%,79% 6%,90% 0,100% 5%,100% 95%,91% 100%,80% 94%,69% 99%,58% 95%,47% 100%,36% 95%,25% 99%,14% 94%,5% 100%,0 96%)}
      .dr-sheet svg{left:0;top:0;overflow:visible}
      .dr-tb{left:${TB[0] - X0}px;top:${TB[1] - Y0}px;width:${TB[2]}px;height:${TB[3]}px;border:2px solid ${INK};background:rgba(251,249,243,.9);
        display:flex;flex-direction:column;color:${INK};font-family:"Gill Sans MT","Gill Sans","Segoe UI",sans-serif}
      .dr-tb>div{padding:0 16px}
      .dr-tb .hd{display:flex;align-items:baseline;gap:12px;border-bottom:1.5px solid ${INK};height:37px;line-height:36px;flex:none}
      .dr-tb .hd b{font-size:22px;font-weight:700;letter-spacing:.01em}
      .dr-tb .hd span{font-size:17px;color:#5E584C}
      .dr-tb .hd i{margin-left:auto;font-style:normal;font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:${INK}}
      .dr-tb .lab{display:flex;justify-content:space-between;font-size:12.5px;letter-spacing:.16em;text-transform:uppercase;color:#6E675A;height:22px;align-items:center}
      .dr-tb .sh{padding-top:4px;padding-bottom:5px;border-bottom:1.5px solid ${INK};flex:none}
      .dr-tb .sh .lab span:nth-child(2){margin-right:auto;margin-left:34px}
      .dr-tb .row,.dr-tb .tot{display:flex;align-items:baseline;height:22px;font:700 15.5px/22px "Courier New",monospace;color:${LEAD}}
      .dr-tb .row span:first-child{width:34px;font:400 15px/22px "Gill Sans MT",sans-serif;color:#6E675A}
      .dr-tb .row .c,.dr-tb .tot .c{margin-left:auto}
      .dr-tb .tot{border-top:1px solid rgba(29,27,23,.3);margin-top:3px;padding-top:1px}
      .dr-tb .tot span:first-child{font:400 12.5px/23px "Gill Sans MT",sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#6E675A}
      .dr-tb .ck{padding-top:4px}
      .dr-tb .ck .n{font:700 15px/1 "Courier New",monospace;letter-spacing:0;color:${LEAD};text-transform:none}
      .dr-tb .grid{display:grid;grid-template-columns:repeat(11,1fr);grid-auto-rows:27px;gap:7px 7px;margin-top:4px}
      .dr-st{display:grid;place-items:center;border:2px solid currentColor;border-radius:4px;font:700 11px/1 "Gill Sans MT","Gill Sans",sans-serif;
        letter-spacing:.035em;mix-blend-mode:multiply;opacity:0;-webkit-mask-image:${INKMASK};-webkit-mask-size:220px 220px}
      .dr-ok{left:${OK[0] - X0}px;top:${OK[1] - Y0}px;width:304px;height:106px;color:${GREEN};white-space:nowrap;border:3.5px solid currentColor;border-radius:8px;
        outline:1.5px solid currentColor;outline-offset:-10px;display:flex;flex-direction:column;align-items:center;justify-content:center;
        font-family:"Gill Sans MT","Gill Sans",sans-serif;mix-blend-mode:multiply;opacity:0;-webkit-mask-image:${INKMASK};-webkit-mask-size:260px 260px}
      .dr-ok b{font-size:44px;font-weight:700;letter-spacing:.05em;line-height:1}
      .dr-ok span{font-size:13px;letter-spacing:.2em;text-transform:uppercase;margin-top:6px}
      .dr-strip{left:${STRIP[0]}px;top:${STRIP[1]}px;width:${STRIP[2]}px;padding:20px 22px 24px;background:#FBF9F3;color:#26231E;
        box-shadow:0 16px 36px rgba(52,40,20,.16),0 1px 4px rgba(52,40,20,.12);font:15px/22px "Courier New",monospace;transform-origin:235px 0}
      .dr-strip .f{font-weight:700;margin:14px 0 6px;padding-bottom:3px;border-bottom:1px solid rgba(29,27,23,.28);display:flex}
      .dr-strip .f:first-child{margin-top:0}
      .dr-strip .f i{margin-left:auto;font-style:normal;font-weight:400;color:#6E675A}
      .dr-strip .l{white-space:pre;height:22px;position:relative}
      .dr-strip .l.el{color:#9A9384}
      .dr-strip .cur{position:absolute;top:3px;width:2px;height:17px;background:${BRASS};box-shadow:0 0 6px rgba(211,161,74,.6)}
    ` }, document.head);

    // ---- the sheet: tracing paper, its grain, two pieces of tape, the pencil, the title block, the approval stamp
    const sheet = el('div', { cls: 'dr-sheet' }, layer);
    el('div', { cls: 'dr-grain' }, sheet);
    const tapeA = el('div', { cls: 'dr-tape' }, sheet), tapeB = el('div', { cls: 'dr-tape' }, sheet);
    css(tapeA, { left: '-34px', top: '-10px', transform: 'rotate(-38deg)' });
    css(tapeB, { left: (SW - 104) + 'px', top: '-8px', transform: 'rotate(34deg)' });
    const NS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', SW); svg.setAttribute('height', SH); svg.setAttribute('viewBox', `${X0} ${Y0} ${SW} ${SH}`);
    svg.innerHTML = `<defs><filter id="dr-lead" x="-2%" y="-2%" width="104%" height="104%">
        <feTurbulence type="fractalNoise" baseFrequency="1.1" numOctaves="2" seed="7" result="n"/>
        <feDisplacementMap in="SourceGraphic" in2="n" scale="1.5" xChannelSelector="R" yChannelSelector="G" result="d"/>
        <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1.5 0 0 0 .05" result="a"/>
        <feComposite in="d" in2="a" operator="in"/></filter>
      <pattern id="dr-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">
        <line x1="0" y1="0" x2="0" y2="6" stroke="${LEAD}" stroke-width="1.6"/></pattern></defs>
      <g id="dr-pencil" filter="url(#dr-lead)" fill="none" stroke="${LEAD}" stroke-linecap="round" stroke-linejoin="round"></g>
      <g id="dr-tip"><circle r="9" fill="${BRASS}" opacity=".22"/><circle r="3.6" fill="${BRASS}"/></g>`;
    sheet.appendChild(svg);
    const pencil = svg.querySelector('#dr-pencil'), tip = svg.querySelector('#dr-tip');
    const mk = (tag, attrs, parent = pencil) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); parent.appendChild(e); return e; };

    /* The drawing, sheet by sheet: [kind, spec, weight]. 'p' a pencil line (drawn along its length), 't' lettering
     * (written left to right), 'f' a shaded bar (its tone grows from the left). The room: x 678..835, y 286..466. */
    const L = 678, R = 835, TP = 286, B = 466, BAR = 736, HR = 2.9;   // bars: 2.9 px per hour from x 736
    const rows = [['Dev', 31, 20], ['Ravi', 10.5, 30], ['Priya', 0, 30]], RY = [352, 380, 408];
    const SHEETS = [
      [ ['p', 'M671 286 H842', 1], ['p', 'M835 279 V473', 1.1], ['p', 'M842 466 H750', .55], ['p', 'M708 466 H671', .25],
        ['p', 'M678 473 V279', 1.1], ['p', 'M708 466 V427', .25, 1.6], ['p', 'M708 427 A39 39 0 0 1 747 466', .4, 1.1] ],
      [ ['t', 'WORKLOAD', 692, 320, 16, .9, { 'letter-spacing': '.16em', 'font-weight': 700 }], ['p', 'M692 328 H791', .45, 1.3] ]
        .concat(...rows.map(([n, h, cap], i) => [
          ['t', n, 692, RY[i] + 4.5, 13.5, .35, {}],
          ['p', `M${BAR} ${RY[i] - 6} H${BAR + Math.max(h, 1.2) * HR} V${RY[i] + 6} H${BAR} Z`, h ? .45 : .1, 1.4],
          ['f', [BAR, RY[i] - 6, Math.min(h, cap) * HR, 12], h ? .3 : 0],
          ['p', `M${BAR + cap * HR} ${RY[i] - 11} V${RY[i] + 11}`, .15, 2.2],
        ].concat(h > cap ? [['h', [BAR + cap * HR, RY[i] - 6, (h - cap) * HR, 12], .3]] : []))),
      [ ['p', 'M678 279 V246', .25, 1.1], ['p', 'M835 279 V246', .25, 1.1], ['p', 'M678 256 H835', .6, 1.3],
        ['p', 'M672 262 L684 250', .1, 1.6], ['p', 'M829 262 L841 250', .1, 1.6],
        ['t', 'one week, Mon to Sat', 756.5, 243, 14, .7, { 'text-anchor': 'middle' }],
        ['p', 'M842 304 Q858 262 900 226 H1004', .7, 1.3],
        ['t', 'reads the job board', 1012, 222, 15.5, .6, {}], ['t', 'changes nothing', 1012, 243, 15.5, .5, {}] ]
        .concat(RY.map(y => ['p', `M847 ${y - 1} l5 6 l11 -13`, .2, 1.8])),
    ];
    // build the strokes, each with its slot of its sheet's time (by weight)
    const strokes = [];
    SHEETS.forEach((items, si) => {
      const tot = items.reduce((s, it) => s + (it[0] === 't' ? it[5] : it[2]), 0);
      let acc = 0;
      for (const it of items) {
        const w = it[0] === 't' ? it[5] : it[2], s = { kind: it[0], sheet: si, a: PH[si][0] + PH[si][1] * acc / tot, d: Math.max(.001, PH[si][1] * w / tot) };
        acc += w;
        if (it[0] === 'p') { s.e = mk('path', { d: it[1], 'stroke-width': it[3] || 2.3, pathLength: 1, 'stroke-dasharray': '1 1', 'stroke-dashoffset': 1 }); }
        else if (it[0] === 't') {
          const id = 'dr-clip' + strokes.length, cp = mk('clipPath', { id }, svg.querySelector('defs'));
          s.clip = mk('rect', { x: 0, y: it[3] - it[4] * 1.1, width: 0, height: it[4] * 1.6 }, cp);
          s.e = mk('text', Object.assign({ x: it[2], y: it[3], 'font-size': it[4], 'font-family': '"Gill Sans MT","Gill Sans","Segoe UI",sans-serif', fill: LEAD, stroke: 'none', 'clip-path': `url(#${id})` }, it[6]));
          s.e.textContent = it[1]; s.anchor = it[6]['text-anchor'] || 'start'; s.x = it[2]; s.y = it[3]; s.size = it[4];
        } else {                                                     // 'f' tone / 'h' hatch: a rect that grows from its left
          const [x, y, w2, h2] = it[1];
          s.e = mk('rect', { x, y, width: 0, height: h2, fill: it[0] === 'h' ? 'url(#dr-hatch)' : LEAD, opacity: it[0] === 'h' ? .9 : .32, stroke: 'none' });
          s.x = x; s.y = y + h2 / 2; s.w = w2;
          if (!w2) s.d = .001;
        }
        strokes.push(s);
      }
    });

    // the title block: the room, "on a copy", Theo's checks (stamped later), and the sheets with their line counts
    const FILES = [['routes_reports.py', 11], ['services.py', 34], ['tests/test_workload.py', 69]];
    const tb = el('div', { cls: 'dr-tb', html: `
      <div class="hd"><b>Workload</b><span>a new room, beside the back office</span><i>On a copy</i></div>
      <div class="sh"><div class="lab"><span>Sheet</span><span>File</span><span>Lines</span></div>
        ${FILES.map((f, i) => `<div class="row"><span>${i + 1}</span><span>${f[0]}</span><span class="c"></span></div>`).join('')}
        <div class="tot"><span>Total</span><span class="c"></span></div></div>
      <div class="ck"><div class="lab"><span>Theo&rsquo;s checks &middot; 19 kept, 3 new</span><span class="n"></span></div><div class="grid"></div></div>` }, sheet);
    const counts = [...tb.querySelectorAll('.row .c')], total = tb.querySelector('.tot .c'), ckN = tb.querySelector('.ck .n');
    const fileRows = [...tb.querySelectorAll('.row')];
    const hash = i => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
    const stamps = Array.from({ length: 22 }, (_, i) => {
      const s = el('div', { cls: 'dr-st', text: i < 19 ? 'THEO’S' : 'NEW' }, tb.querySelector('.grid'));
      s.style.color = i < 19 ? BLUE : ROSE;
      return { e: s, at: T.checks + i * STAMP, r: (hash(i) - .5) * 5, o: .8 + .14 * hash(i + 40) };
    });
    const ok = el('div', { cls: 'dr-ok', html: '<b>22 PASSED</b><span>23 Nov &middot; 16:15</span>' }, sheet);

    // ---- the margin slip: real lines of the change, typed as he draws each sheet
    const CODE = [
      ['routes_reports.py', ['@router.get("/api/reports/workload/{day}")', 'def workload(day: str):', '    if day == "today":', '        day = today()', '    return services.mechanic_workload(day)']],
      ['services.py', ['def mechanic_workload(day):', '    week_start, week_end = week_bounds(day)', '    con = connect()', '    rows = con.execute(', '    · · ·', '    rows.sort(key=lambda r: r["spare_hours"])']],
      ['tests/test_workload.py', ['def test_workload_week_and_exclusions(client):', '    _set_jobs(client, JOBS)', '    assert r["ok"] is True', '    assert by_name["Priya"]["spare_hours"] == 30', '    · · ·', 'def test_workload_bad_date(client):']],
    ];
    const strip = el('div', { cls: 'dr-strip' }, layer);
    const tapeC = el('div', { cls: 'dr-tape' }, strip);
    css(tapeC, { left: '166px', top: '-20px', width: '128px', height: '34px', transform: 'rotate(-2deg)' });
    const typed = CODE.map(([f, lines], fi) => {
      const head = el('div', { cls: 'f', html: `<span>${f}</span>` }, strip);
      const ls = lines.map(s => { const d = el('div', { cls: 'l' + (s.trim().startsWith('·') ? ' el' : '') }, strip); return { d, s }; });
      return { head, ls, n: ls.reduce((a, l) => a + l.s.length, 0) };
    });
    const cur = el('div', { cls: 'cur' }, strip);

    return {
      render(t) {
        // the sheet slides over the plan from the right and settles a hair off square; the slip follows it
        const ks = easeInOutCubic(P(t, A, 1.0)), kp = easeInOutCubic(P(t, A + .45, .85));
        sheet.style.transform = `translate(${((1 - ks) * 1480).toFixed(1)}px,${((1 - ks) * 26).toFixed(1)}px) rotate(${lerp(-2.2, -.3, ks).toFixed(3)}deg)`;
        strip.style.transform = `translate(${((1 - kp) * 640).toFixed(1)}px,${((1 - kp) * 18).toFixed(1)}px) rotate(${lerp(3, .7, kp).toFixed(3)}deg)`;
        // the pencil: every stroke at its own moment, eased in and out like a hand; brass at the point while it moves
        let tipAt = null;
        for (const s of strokes) {
          const k = s.d <= .001 ? (t >= s.a ? 1 : 0) : easeInOutSine(P(t, s.a, s.d));
          if (s.kind === 'p') {
            s.e.setAttribute('stroke-dashoffset', (1 - k).toFixed(4));
            if (k > 0 && k < 1) { const len = s.e.getTotalLength(), p = s.e.getPointAtLength(len * k); tipAt = [p.x, p.y]; }
          } else if (s.kind === 't') {
            if (s.w == null || !s.w) s.w = s.e.getComputedTextLength() * 1.02;
            const x0 = s.anchor === 'middle' ? s.x - s.w / 2 : s.x;
            s.clip.setAttribute('x', (x0 - 2).toFixed(1)); s.clip.setAttribute('width', (k * (s.w + 4)).toFixed(1));
            if (k > 0 && k < 1) tipAt = [x0 + k * s.w, s.y - s.size * .3];
          } else {
            s.e.setAttribute('width', (k * s.w).toFixed(2));
            if (k > 0 && k < 1) tipAt = [s.x + k * s.w, s.y];
          }
        }
        tip.style.display = tipAt ? '' : 'none';
        if (tipAt) tip.setAttribute('transform', `translate(${tipAt[0].toFixed(1)} ${tipAt[1].toFixed(1)})`);
        // the title block: each sheet's row comes up as he starts it, its count running with the drawing
        let sum = 0;
        FILES.forEach(([, n], i) => {
          const k = P(t, PH[i][0], PH[i][1]), c = Math.round(n * easeInOutSine(k));
          sum += c;
          setText(counts[i], t < PH[i][0] ? '' : '+' + c);
          fileRows[i].style.opacity = (.18 + .82 * easeOutCubic(P(t, PH[i][0] - .15, .3))).toFixed(3);
        });
        setText(total, t < PH[0][0] ? '' : `+${sum} −0`);
        // the margin slip: the lines of the sheet being drawn, typed at an even rate, the brass head where he types
        let curAt = null;
        typed.forEach((f, i) => {
          const k = P(t, PH[i][0], PH[i][1]);
          let left = Math.floor(f.n * k + 1e-6);
          f.head.style.opacity = t >= PH[i][0] - .1 ? '1' : '0';
          for (const l of f.ls) {
            const c = Math.max(0, Math.min(l.s.length, left));
            setText(l.d, l.s.slice(0, c));
            if (k > 0 && k < 1 && !curAt && left >= 0 && left <= l.s.length) curAt = [l.d, c];
            left -= l.s.length;
          }
        });
        cur.style.display = curAt ? '' : 'none';
        if (curAt) css(cur, { left: (22 + curAt[1] * 9.0 + 1).toFixed(1) + 'px', top: (curAt[0].offsetTop + 3) + 'px' });
        // Theo's checks: one stamp each, pressed and lifted (no bounce), then the approval across the sheet
        let n = 0;
        for (const s of stamps) {
          const k = easeOutCubic(P(t, s.at, .09));
          if (t >= s.at) n++;
          s.e.style.opacity = (s.o * k).toFixed(3);
          s.e.style.transform = `rotate(${s.r.toFixed(2)}deg) scale(${(1 + .35 * (1 - k)).toFixed(3)})`;
        }
        setText(ckN, t < T.checks ? '' : `${n} of 22`);
        const ko = easeOutCubic(P(t, APPROVE, .16));
        ok.style.opacity = (.88 * ko).toFixed(3);
        ok.style.transform = `rotate(-6deg) scale(${(1 + .28 * (1 - ko)).toFixed(3)})`;
      },
    };
  }

  Scene({
    id: '6', start: S, end: E, fadeIn: 0,
    build(root) {
      const n37 = VE(37) - V(37);
      const cb = sfxT('mouse_click', M('click_build')), cardAt = V(33), CHAIR = pick('world/x_chair_dusk.png', '');
      const LAMP = shotDone('s6_lamp_on');
      const MON = 'world/04_medium_monday.png', DUSK = pick('world/06_medium_dusk.png', MON), STICKY = pick('world/x_sticky_dusk.png', MON), GLASSES = pick('world/x_glasses_dusk.png', MON);
      const cardItem = (at, close) => ({ src: 'comp/martin-build', at, cam: [960, 540, 1], close,
          state: t => ({ room: 0, side: 'card', time: '16:16', foot: '', martinSay: t >= V(36) ? 'Fussy.' : t >= V(34) ? 'Add it.' : 'You can do that?', card: +clamp((t - cardAt - .3) / .6).toFixed(3), marker: [11.62, 2.45], passage: 1,
            press: [+pressAt(t, cb).toFixed(3), 0] }),
          build: l => { const cur = cursor(l, 1.5); (rv.curs = rv.curs || []).push(cur); },
          over: (t, l) => {
            const cur = rv.curs[at === cardAt ? 0 : 1], from = Math.min(V(35) + 1.2, cb - 1.3);
            if (!AddIt || t < from) { cur.at(0, 0, false); return; }
            const c = hand(t, [from, AddIt[0] - 260, AddIt[1] + 230], [{ t: cb, x: AddIt[0], y: AddIt[1] }]);
            cur.at(c[0], c[1], true);
          } });
      // Theo's system at 16:08, Reports (coming soon!!): one state for the full screen (6.3) and the monitor's glass in
      // the dusk desk shots around it (6.1, 6.4), so the room's screen is the page we cut to; the marquee and the clock
      // run on one clock, Martin's hand goes to the tab in 6.3 and rests there
      const soonState = t => {
        const b = Math.max(M('soon_tab') + 1.4, V(29) + 4), c = path2(t, [[b - .9, 700, 470], [b - .1, 578, 258], [b + 3, 582, 261]]);   // Martin's hand to the tab
        return { preset: 'shop-reports-soon', marquee: +(((t - S + 2) * 60) % 2000).toFixed(1), secs: Math.floor(t - S + 6) % 60,
          cursor: { x: +(c[0] + wiggle(t, 31, 2, 1.2)).toFixed(2), y: +(c[1] + wiggle(t, 32, 1.7, 1)).toFixed(2) } };
      };
      run = seq(root, [
        // 6.1 dusk: the room deep blue, then the lamp comes on: Blender's s6_lamp_on (it replaces the Monday still, locked
        // off on its framing, so its glass is the still's: glassFromStill), Theo's system live on the monitor. Until the
        // sequence lands, the Monday desk in the late grade, its light stepping up on the lamp's click.
        LAMP ? { src: MON, at: S, cam: hold(960, 610, 1.08), glassFromStill: true, screen: { src: 'live/shop', state: soonState } }
          : { src: DUSK, at: S, cam: hold(960, 610, 1.08), keepGrade: true, screen: { src: 'live/shop', state: soonState },
            grade: t => DUSK === MON ? `${LATE} brightness(${lerp(.62, 1, easeOutCubic(P(t, M('lamp_on'), .12))).toFixed(3)})` : '' },
        // 6.2 the sticky note, in Theo's hand; 6.3 Reports (coming soon!!), locked and held for the joke
        { src: STICKY, at: M('sticky'), grade: STICKY === MON ? LATE : '', cam: STICKY === MON ? hold(948, 766, 3.1, .006) : hold(960, 540, 1.0) },
        { src: 'live/shop', at: M('soon_tab'), cam: [960, 540, 1], state: soonState },
        // 6.4 back to the dusk desk: "I could write it" / "You can do that?" / "With your say-so"
        { src: DUSK, at: V(30), grade: DUSK === MON ? LATE : '', cam: pan(V(30) + .3, M('code') - V(30) - .8, 880, 610, 1040, 600, 1.1),
          screen: { src: 'live/shop', state: soonState, grade: DUSK === MON ? LATE : '' } },
        // 6.5 "I'll work on a copy", literally: tracing paper over Martin's plan; Barnaby drafts the Workload room in
        // pencil, the code typed in the margin; then Theo's checks land as stamps (drafting(), below). Wide while the sheet
        // goes down, then one push to his working frame (the room, the margin, the title block). The side panel is
        // cleared (side 'none'); the header clock runs on while he works (16:09 -> 16:15; the card says 16:16).
        { src: 'comp/martin-build', at: M('code'), cam: move(M('code') + .95, 1.5, [960, 540, 1.0], [1164, 600, 1.27], 0),
          state: t => ({ room: 0, side: 'none', marker: [11.62, 2.45], foot: '',
            time: '16:' + String(9 + Math.min(6, Math.floor(7 * clamp((t - M('code')) / (V(33) - M('code')))))).padStart(2, '0') }),
          build: l => { rv.dr = drafting(l, { code: M('code'), checks: M('checks'), done: V(33) }); },
          over: t => rv.dr.render(t) },
        // 6.6 Martin's plan with the explanation card; mid-line, his reading glasses on the dusk desk; back to the card
        cardItem(V(33)),
        { src: GLASSES, at: M('glasses'), grade: GLASSES === MON ? LATE : '', cam: GLASSES === MON ? hold(640, 865, 2.05) : hold(960, 540, 1.0) },
        cardItem(M('glasses') + 2.4, { x: 1542, y: 520, d: .6 }),      // closes back into the shop PC on the reload
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
        { src: 'comp/martin-build', at: M('same_butler'), cam: [960, 540, 1], state: () => ({ side: 'build' }), close: { x: 1542, y: 520, d: .6 },
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
