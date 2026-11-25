/* Scene A: Nine tabs (0–11 s). Cold open.
 * Black, the bell, then a desk monitor. Nine browser windows (one per system a small business juggles) cascade in
 * 0.6 s apart, the pile compressing and shrinking until the titles are unreadable, while a RAM gadget in the screen's
 * top-right corner climbs 38% -> 94% (grey, brass, then red). The one scene that should feel overwhelming.
 * 10.2–11: the tabs are swept away (whoosh at 10.4).
 */
(function () {
  const START = 0, END = 11;
  const TABS = ['Back Office v2.3', 'Supplier portal', 'SMS box', 'workload.xls', 'Invoices', 'Parts list', 'Email', 'Bank', 'Calendar'];
  const FAV = [['#1D4A77', 'S'], ['#2F6B6F', 'P'], ['#5B6B8C', 'M'], ['#217346', 'X'], ['#6B4E7A', 'I'], ['#4A5568', 'P'], ['#A8473B', '@'], ['#1F3354', 'B'], ['#3C6E9A', 'C']];
  const T0 = 1.0, GAP = .6;           // tab i lands at T0 + i*GAP (cues.json -> sfx "tab")
  const RAM0 = 38, RAM1 = 94, RAM_END = 9.5;   // storyboard: 1.0–9.5, 38% -> 94%
  const OUT = 10.2;                   // tabs leave 10.2–11 (whoosh at 10.4)
  const SW = 1344, SH = 744, TB = 40; // screen size, taskbar height
  const WW = 860, WH = 530;           // a browser window at scale 1
  const tAt = i => T0 + i * GAP;

  let mon, scr, wall, pile, red, wins = [], btns = [], ram, ramV, ramBar, busy, ring;

  /* ---------------------------------------------------------- page look-alikes (static, built once) */
  const bar = (w, c = '#D7DBE2', h = 8, st = '') => `<i style="display:block;width:${w | 0}px;height:${h}px;border-radius:${h / 2}px;background:${c};${st}"></i>`;
  const ibar = (w, c = '#D7DBE2', h = 8, st = '') => `<i style="display:inline-block;vertical-align:middle;width:${w | 0}px;height:${h}px;border-radius:${h / 2}px;background:${c};${st}"></i>`;
  const R = (i, s) => rand(i, s);

  const PAGES = [
    // 0 · Back Office v2.3 (Theo's 2009 system, real rows)
    () => `<div style="background:linear-gradient(#3A6EA5,#1D4A77);color:#fff;padding:8px 14px 6px;border-bottom:4px solid #FFCC00"><b style="display:block;font:italic bold 26px 'Trebuchet MS',Verdana,sans-serif;text-shadow:2px 2px 0 #0B2A4A">Spokes &amp; Sprockets</b><span style="font:12px Verdana;color:#FFE680">A Hartley family workshop &middot; est. 1987</span></div>
      <div style="background:#D4D0C8;padding:4px 8px;border-bottom:1px solid #808080;font:12px Verdana;white-space:nowrap">${['Jobs', 'Customers', 'Parts', 'Purchase Orders', 'Mechanics', 'Invoices'].map((p, i) => `<span style="display:inline-block;padding:1px 7px;margin-right:3px;border:2px ${i ? 'outset' : 'inset'} #F4F4F4;background:${i ? 'linear-gradient(#fff,#E3E0D8)' : '#ECE9D8'};color:${i ? '#00E' : '#551A8B'};text-decoration:underline;${i ? '' : 'font-weight:bold'}">${p}</span>`).join('')}</div>
      <div style="padding:8px 10px"><div style="font:bold 14px Verdana;color:#1D4A77;margin-bottom:6px">Open repair jobs &ndash; this week</div>
      <table style="border-collapse:collapse;width:100%;font:12px Verdana;color:#000"><tr>${['Job #', 'Mechanic', 'Work', 'Customer', 'Hrs', 'Due'].map(h => `<th style="background:#D4D0C8;border:1px solid #808080;text-align:left;padding:3px 6px">${h}</th>`).join('')}</tr>
      ${SHOP_ROWS.slice(0, 8).map((r, i) => `<tr style="background:${i % 2 ? '#fff' : '#EEF3FB'}">${r.map(c => `<td style="border:1px solid #C6C6C6;padding:3px 6px;white-space:nowrap">${esc(c)}</td>`).join('')}</tr>`).join('')}</table></div>`,

    // 1 · Supplier portal
    () => `<div style="height:46px;background:#2F6B6F;display:flex;align-items:center;gap:14px;padding:0 18px">${ibar(30, '#E8F1F1', 30, 'border-radius:8px')}${ibar(130, 'rgba(255,255,255,.75)', 10)}<span style="flex:1"></span>${ibar(70, 'rgba(255,255,255,.4)', 8)}${ibar(70, 'rgba(255,255,255,.4)', 8)}</div>
      <div style="padding:14px 18px"><div style="height:34px;border:1px solid #CFD6DA;border-radius:17px;margin-bottom:14px;display:flex;align-items:center;padding:0 16px">${ibar(220, '#DCE1E5')}</div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">${[...Array(8)].map((_, i) => `<div style="border:1px solid #E1E4E8;border-radius:8px;padding:9px"><div style="height:62px;border-radius:6px;background:linear-gradient(135deg,#EDF0F3,#D8DEE4);margin-bottom:8px"></div>${bar(70 + R(i, 21) * 80, '#C5CBD3')}<div style="height:7px"></div><div style="display:flex;justify-content:space-between;align-items:center">${ibar(46, '#9DB8B9')}${ibar(38, '#2F6B6F', 18, 'border-radius:5px')}</div></div>`).join('')}</div></div>`,

    // 2 · SMS box
    () => `<div style="display:flex;height:100%"><div style="width:250px;border-right:1px solid #E3E6EA;background:#F7F8FA">${[...Array(7)].map((_, i) => `<div style="display:flex;gap:10px;align-items:center;padding:11px 14px;border-bottom:1px solid #ECEEF1;${i === 1 ? 'background:#E8ECF3' : ''}"><i style="width:34px;height:34px;border-radius:50%;flex:none;background:${['#B7C3D6', '#C9B7A8', '#A9C4B5', '#C4B1CC', '#B5BFC9', '#CDBFA4', '#ABBBD0'][i]}"></i><div style="flex:1">${bar(80 + R(i, 31) * 70, '#BCC3CD')}<div style="height:7px"></div>${bar(120 + R(i, 32) * 60, '#DADFE5', 6)}</div></div>`).join('')}</div>
      <div style="flex:1;padding:16px 18px;display:flex;flex-direction:column;gap:12px">${[0, 1, 0, 0, 1, 0, 1].map((me, i) => `<div style="align-self:${me ? 'flex-end' : 'flex-start'};max-width:62%;padding:10px 14px;border-radius:14px;background:${me ? '#5B6B8C' : '#E9ECF0'}">${bar(110 + R(i, 33) * 170, me ? 'rgba(255,255,255,.7)' : '#BEC5CE')}${R(i, 34) > .5 ? `<div style="height:7px"></div>${bar(60 + R(i, 35) * 90, me ? 'rgba(255,255,255,.45)' : '#D2D7DE')}` : ''}</div>`).join('')}</div></div>`,

    // 3 · workload.xls
    () => {
      const cols = 'ABCDEFGHI'.split('');
      let g = `<div style="height:30px;background:#217346;display:flex;align-items:center;gap:16px;padding:0 12px">${[40, 50, 44, 52, 38].map(w => ibar(w, 'rgba(255,255,255,.55)', 7)).join('')}</div>
        <div style="height:30px;display:flex;align-items:center;gap:8px;padding:0 8px;border-bottom:1px solid #D4D4D4;font:italic 14px Cambria,Georgia,serif;color:#666"><span style="width:60px;border:1px solid #D4D4D4;height:20px"></span>fx<span style="flex:1;border:1px solid #D4D4D4;height:20px"></span></div>
        <table style="border-collapse:collapse;font:12px Calibri,'Segoe UI',sans-serif;color:#555;table-layout:fixed;width:100%"><tr><td style="width:34px;background:#E9E9E9;border:1px solid #D4D4D4"></td>${cols.map(c => `<td style="background:#E9E9E9;border:1px solid #D4D4D4;text-align:center;height:22px">${c}</td>`).join('')}</tr>`;
      for (let r = 1; r <= 16; r++) {
        g += `<tr><td style="background:#E9E9E9;border:1px solid #D4D4D4;text-align:center;height:23px">${r}</td>`;
        cols.forEach((c, k) => {
          const v = R(r * 17 + k, 41), fill = r === 1 ? '#DDEBDD' : (R(r * 13 + k, 42) > .9 ? '#FFF2A8' : '#fff');
          g += `<td style="border:1px solid #DADADA;background:${fill};padding:0 5px">${v > .3 ? ibar(18 + v * 42, r === 1 ? '#8FB59A' : '#C9CDD3', 6) : ''}</td>`;
        });
        g += '</tr>';
      }
      return g + '</table>';
    },

    // 4 · Invoices
    () => `<div style="height:48px;background:#6B4E7A;display:flex;align-items:center;padding:0 18px;gap:14px">${ibar(120, 'rgba(255,255,255,.8)', 10)}<span style="flex:1"></span>${ibar(90, 'rgba(255,255,255,.35)', 26, 'border-radius:6px')}</div>
      <div style="padding:10px 18px">${[...Array(9)].map((_, i) => `<div style="display:flex;align-items:center;gap:18px;padding:10px 4px;border-bottom:1px solid #ECEEF1">${ibar(64, '#B9B0C2')}${ibar(150 + R(i, 51) * 140, '#D3D7DE')}<span style="flex:1"></span>${ibar(70, '#C3C8D0')}${ibar(64, ['#F0D9D9', '#DCE9DC', '#EFE6CC'][Math.floor(R(i, 52) * 3)], 20, 'border-radius:10px')}</div>`).join('')}</div>`,

    // 5 · Parts list
    () => `<div style="height:44px;background:#4A5568;display:flex;align-items:center;padding:0 18px;gap:12px">${ibar(110, 'rgba(255,255,255,.75)', 10)}</div>
      <div style="padding:10px 16px"><div style="display:flex;gap:10px;margin-bottom:10px">${ibar(180, '#E3E6EA', 28, 'border-radius:6px')}${ibar(90, '#E3E6EA', 28, 'border-radius:6px')}</div>
      <div style="display:flex;gap:16px;padding:7px 8px;background:#EEF0F3;border-radius:4px">${[60, 220, 90, 70].map(w => ibar(w, '#A9B0BA', 7)).join('')}</div>
      ${[...Array(9)].map((_, i) => `<div style="display:flex;gap:16px;align-items:center;padding:9px 8px;border-bottom:1px solid #EEF0F3">${ibar(60, '#C2C7CF', 7)}${ibar(120 + R(i, 61) * 100, '#D5D9DF', 7, 'margin-right:' + (100 - R(i, 61) * 100 | 0) + 'px')}${ibar(50 + R(i, 62) * 40, '#D5D9DF', 7, 'margin-right:' + (40 - R(i, 62) * 40 | 0) + 'px')}${ibar(26, R(i, 63) > .75 ? '#E4B9A8' : '#CCD8CF', 14, 'border-radius:7px')}</div>`).join('')}</div>`,

    // 6 · Email
    () => `<div style="display:flex;height:100%"><div style="width:190px;background:#F1F3F4;padding:14px 12px">${ibar(120, '#A8473B', 34, 'border-radius:17px;margin-bottom:16px')}${[...Array(7)].map((_, i) => `<div style="padding:8px 6px">${bar(70 + R(i, 71) * 60, i === 0 ? '#9AA1AB' : '#C9CED5')}</div>`).join('')}</div>
      <div style="flex:1"><div style="padding:12px 16px;border-bottom:1px solid #E6E8EB">${bar(320, '#E6E8EB', 28, 'border-radius:14px')}</div>${[...Array(10)].map((_, i) => `<div style="display:flex;gap:14px;align-items:center;padding:10px 16px;border-bottom:1px solid #F0F1F3"><i style="width:8px;height:8px;border-radius:50%;flex:none;background:${R(i, 72) > .45 ? '#5B7DB1' : 'transparent'}"></i>${ibar(90 + R(i, 73) * 30, R(i, 72) > .45 ? '#8E96A2' : '#C3C8CF')}${ibar(200 + R(i, 74) * 120, '#DDE1E6')}<span style="flex:1"></span>${ibar(34, '#D0D4DA', 6)}</div>`).join('')}</div></div>`,

    // 7 · Bank
    () => `<div style="height:50px;background:#1F3354;display:flex;align-items:center;gap:12px;padding:0 18px"><i style="width:26px;height:26px;border-radius:50%;background:#C9D3E3"></i>${ibar(110, 'rgba(255,255,255,.75)', 10)}<span style="flex:1"></span>${ibar(80, 'rgba(255,255,255,.3)', 26, 'border-radius:6px')}</div>
      <div style="display:flex;gap:16px;padding:16px 18px"><div style="flex:1;border:1px solid #E1E5EB;border-radius:10px;padding:14px 16px">${bar(90, '#B8C1CE')}<div style="font:600 30px 'Segoe UI';color:#1F3354;letter-spacing:.12em;margin:10px 0 8px">&bull;&bull;&bull;&bull; &bull;&bull;&bull;&bull;</div>${bar(150, '#DCE1E8')}</div>
      <div style="flex:1;border:1px solid #E1E5EB;border-radius:10px;padding:14px 16px;display:flex;align-items:flex-end;gap:9px;height:112px">${[...Array(12)].map((_, i) => `<i style="flex:1;height:${20 + R(i, 81) * 70 | 0}px;border-radius:3px;background:${i === 11 ? '#1F3354' : '#C3CCDA'}"></i>`).join('')}</div></div>
      <div style="padding:0 18px">${[...Array(6)].map((_, i) => `<div style="display:flex;gap:16px;align-items:center;padding:10px 4px;border-bottom:1px solid #EEF0F3">${ibar(44, '#D0D6DF')}${ibar(180 + R(i, 82) * 120, '#DADFE6')}<span style="flex:1"></span>${ibar(70, '#BCC4D0')}</div>`).join('')}</div>`,

    // 8 · Calendar
    () => {
      const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], ev = ['#A7B8D9', '#D9B8A7', '#B9D3C2', '#D1C3E6', '#E3D4A8'];
      let s = `<div style="display:flex;padding:10px 0 8px 54px;border-bottom:1px solid #E3E6EA;font:600 14px 'Segoe UI';color:#5F6368">${days.map(d => `<div style="flex:1;padding-left:8px">${d}</div>`).join('')}</div>
        <div style="position:relative;height:420px;margin-left:54px;background:repeating-linear-gradient(#fff 0 39px,#ECEEF1 39px 40px)">`;
      for (let d = 1; d < 5; d++) s += `<i style="position:absolute;top:0;bottom:0;left:${d * 20}%;width:1px;background:#ECEEF1"></i>`;
      for (let k = 0; k < 13; k++) {
        const d = k % 5, top = 6 + R(k, 91) * 320 | 0, h = 34 + R(k, 92) * 44 | 0;
        s += `<div style="position:absolute;left:calc(${d * 20}% + 4px);width:calc(20% - 8px);top:${top}px;height:${h}px;border-radius:6px;background:${ev[k % 5]};border-left:4px solid ${mixColor(ev[k % 5], '#000', .25)};padding:6px 8px">${bar(50 + R(k, 93) * 50, 'rgba(0,0,0,.18)', 6)}</div>`;
      }
      return s + '</div>';
    },
  ];

  Scene({
    id: 'A', start: START, end: END, drift: .02,
    captions: [[4.5, 10.5, 'Every small business runs on systems nobody has time to rewrite.']],

    build(root) {
      el('style', { text: `
#scene-A .mon{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:960px 720px}
#scene-A .bez{position:absolute;left:270px;top:44px;width:1380px;height:806px;border-radius:24px;background:linear-gradient(180deg,#23272F,#15181E 42%,#0F1116);border:1px solid #2C313B;box-shadow:0 60px 140px rgba(0,0,0,.7),0 0 140px rgba(110,140,190,.08),inset 0 1px 0 rgba(255,255,255,.07)}
#scene-A .led{position:absolute;left:50%;bottom:17px;width:6px;height:6px;margin-left:-3px;border-radius:50%;background:#6E7686;box-shadow:0 0 8px rgba(160,175,200,.5)}
#scene-A .neck{position:absolute;left:895px;top:849px;width:130px;height:46px;background:linear-gradient(90deg,#121419,#262A33 50%,#121419);clip-path:polygon(16% 0,84% 0,100% 100%,0 100%)}
#scene-A .foot{position:absolute;left:735px;top:893px;width:450px;height:14px;border-radius:7px;background:linear-gradient(#2A2E37,#14171C);box-shadow:0 16px 34px rgba(0,0,0,.6)}
#scene-A .scr{position:absolute;left:18px;top:18px;width:${SW}px;height:${SH}px;border-radius:6px;overflow:hidden;background:#07090D;box-shadow:inset 0 0 0 1px #000}
#scene-A .wall{position:absolute;inset:0;background:radial-gradient(ellipse 85% 75% at 30% 25%,#273349,#161C28 58%,#0D1118)}
#scene-A .wall:after{content:'';position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);background-size:48px 48px}
#scene-A .pile{position:absolute;left:0;top:0;width:${SW}px;height:${SH - TB}px}
#scene-A .aw{position:absolute;left:0;top:0;width:${WW}px;height:${WH}px;transform-origin:0 0;background:#F3F4F6;border-radius:10px 10px 6px 6px;overflow:hidden;box-shadow:0 26px 60px rgba(0,0,0,.55),0 0 0 1px rgba(0,0,0,.4);font-family:"Segoe UI",sans-serif;color:#222}
#scene-A .aw-tabs{position:relative;height:44px;background:#D9DCE2;display:flex;align-items:flex-end;padding-left:10px}
#scene-A .aw-tab{height:36px;width:310px;background:#F3F4F6;border-radius:10px 10px 0 0;display:flex;align-items:center;gap:10px;padding:0 14px;font-size:19px;font-weight:600;color:#202124;white-space:nowrap}
#scene-A .fav{width:20px;height:20px;border-radius:5px;flex:none;color:#fff;font:700 13px/20px "Segoe UI",sans-serif;text-align:center}
#scene-A .aw-tab .x{margin-left:auto;color:#6B7079;font-size:15px;font-weight:400}
#scene-A .aw-plus{color:#5F6368;font-size:22px;padding:0 0 6px 14px}
#scene-A .aw-ctl{position:absolute;right:14px;top:9px;display:flex;gap:20px;color:#5F6368;font-size:16px}
#scene-A .aw-bar{height:40px;display:flex;align-items:center;gap:14px;padding:0 14px;border-bottom:1px solid #D2D5DA;color:#7A7F87;font-size:16px}
#scene-A .aw-url{flex:1;height:26px;border-radius:13px;background:#E4E6EA;display:flex;align-items:center;padding-left:16px}
#scene-A .aw-body{position:absolute;left:0;right:0;top:84px;bottom:0;background:#fff;overflow:hidden}
#scene-A .aw-fog{position:absolute;inset:0;background:#5F6775;opacity:0}
#scene-A .red{position:absolute;inset:0;pointer-events:none}
#scene-A .tb{position:absolute;left:0;right:0;bottom:0;height:${TB}px;background:rgba(10,13,19,.94);border-top:1px solid rgba(255,255,255,.08)}
#scene-A .tb-start{position:absolute;left:14px;top:7px;width:26px;height:26px;border-radius:50%;background:radial-gradient(circle at 40% 35%,#6A86B5,#22355A);box-shadow:0 0 0 1px rgba(255,255,255,.15)}
#scene-A .tb-tray{position:absolute;right:16px;top:13px;display:flex;gap:12px}
#scene-A .tb-tray i{width:14px;height:14px;border-radius:3px;background:rgba(255,255,255,.22)}
#scene-A .tbb{position:absolute;top:5px;height:30px;border-radius:5px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.1);display:flex;align-items:center;gap:7px;padding:0 9px;color:#D9DCE2;font-size:14px;white-space:nowrap;overflow:hidden}
#scene-A .tbb .fav{width:16px;height:16px;font-size:10px;line-height:16px;border-radius:4px}
#scene-A .tbb span{overflow:hidden;text-overflow:ellipsis}
#scene-A .ram{position:absolute;right:18px;top:16px;width:258px;padding:12px 16px 14px;border-radius:12px;background:rgba(9,11,16,.9);border:1px solid rgba(255,255,255,.13);font-family:"Segoe UI",sans-serif}
#scene-A .ram-h{display:flex;align-items:baseline;justify-content:space-between}
#scene-A .ram-l{font:600 14px "Segoe UI",sans-serif;letter-spacing:.18em;color:#8D8778}
#scene-A .ram-v{font:600 36px "Cascadia Mono",Consolas,monospace;line-height:1}
#scene-A .ram-bar{height:8px;border-radius:4px;background:rgba(255,255,255,.1);margin-top:10px;overflow:hidden}
#scene-A .ram-bar i{display:block;height:100%;border-radius:4px}
#scene-A .busy{position:absolute;left:0;top:0;width:60px;height:60px}
` }, root);

      mon = el('div', { cls: 'mon' }, root);
      el('div', { cls: 'neck' }, mon);
      el('div', { cls: 'foot' }, mon);
      const bez = el('div', { cls: 'bez' }, mon);
      el('div', { cls: 'led' }, bez);
      scr = el('div', { cls: 'scr' }, bez);
      wall = el('div', { cls: 'wall' }, scr);
      pile = el('div', { cls: 'pile' }, scr);

      TABS.forEach((title, i) => {
        const [c, ch] = FAV[i];
        const w = el('div', { cls: 'aw' }, pile);
        w.innerHTML = `<div class="aw-tabs"><div class="aw-tab"><span class="fav" style="background:${c}">${ch}</span><span>${esc(title)}</span><span class="x">&#x2715;</span></div><span class="aw-plus">+</span>
          <span class="aw-ctl"><span>&#x2013;</span><span>&#x25A1;</span><span>&#x2715;</span></span></div>
          <div class="aw-bar"><span>&#x2190;</span><span>&#x2192;</span><span>&#x21BB;</span><span class="aw-url">${ibar(150 + rand(i, 3) * 120, '#B7BCC5', 7)}</span></div>
          <div class="aw-body">${PAGES[i]()}</div><div class="aw-fog"></div>`;
        // entrance direction: each one lands from a slightly different side, so the pile feels unruly
        const a = rand(i, 5) * Math.PI * 2;
        wins.push({ el: w, fog: w.querySelector('.aw-fog'), jx: (rand(i, 7) - .5) * 2 * 44, jy: (rand(i, 8) - .5) * 2 * 22, ix: Math.cos(a) * 70, iy: Math.sin(a) * 50 - 20 });
      });

      red = el('div', { cls: 'red' }, scr);

      const tb = el('div', { cls: 'tb' }, scr);
      el('div', { cls: 'tb-start' }, tb);
      el('div', { cls: 'tb-tray', html: '<i></i><i></i><i></i>' }, tb);
      TABS.forEach((title, i) => {
        const [c, ch] = FAV[i];
        btns.push(el('div', { cls: 'tbb', html: `<span class="fav" style="background:${c}">${ch}</span><span>${esc(title)}</span>` }, tb));
      });

      // RAM gadget, pinned to the screen's top-right corner (always on top)
      ram = el('div', { cls: 'ram', html: '<div class="ram-h"><span class="ram-l">RAM</span><b class="ram-v">38%</b></div><div class="ram-bar"><i></i></div>' }, scr);
      ramV = ram.querySelector('.ram-v'); ramBar = ram.querySelector('.ram-bar i');

      // the busy cursor: an arrow with a spinning ring
      busy = el('div', { cls: 'busy', html: `<svg width="60" height="60" viewBox="0 0 60 60" style="position:absolute;left:0;top:0;overflow:visible">
        <path d="M2 2 L2 30 L9 23 L14 34 L19 32 L14 21 L24 21 Z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/>
        <g class="ring" style="transform-origin:36px 40px"><circle cx="36" cy="40" r="11" fill="none" stroke="rgba(20,26,38,.22)" stroke-width="4"/>
        <path d="M36 29 A11 11 0 0 1 47 40" fill="none" stroke="#24314A" stroke-width="4" stroke-linecap="round"/></g></svg>` }, scr);
      ring = busy.querySelector('.ring');
    },

    render(t) {
      // 0–0.6 black; the bell rings at 0.6 and the room comes up
      Q.setBlack(1 - easeOutCubic(P(t, .6, .6)));
      // the monitor fades up, then the camera leans in slowly as the pile grows (anchored low, so the stand stays
      // clear of the caption's 160 px)
      const mk = easeOutCubic(P(t, .7, .9));
      mon.style.opacity = mk;
      mon.style.transform = `scale(${(lerp(.975, 1, mk) * (1 + .02 * easeInOutSine(P(t, 1.0, 9.2)))).toFixed(4)})`;
      wall.style.opacity = easeOutCubic(P(t, .85, .5));

      // n: how many tabs have landed (continuous, so the pile re-lays itself out smoothly)
      let n = 0; for (let i = 0; i < 9; i++) n += easeOutCubic(P(t, tAt(i), .45));
      const nn = Math.max(n, 1), m = clamp((n - 1) / 8);
      const s = lerp(1, .72, m), DX = lerp(120, 44, m), DY = lerp(62, 19, m);
      const X0 = (SW - (WW * s + (nn - 1) * DX)) / 2, Y0 = (SH - TB - (WH * s + (nn - 1) * DY)) / 2;

      // every landing jolts the pile a little
      let sx = 0, sy = 0;
      for (let j = 0; j < 9; j++) {
        const d = t - tAt(j) - .12; if (d <= 0) continue;
        const a = Math.exp(-d * 7) * (2.5 + j * .7);
        sx += a * Math.sin(d * 46 + j); sy += a * .7 * Math.cos(d * 39 + j * 2);
      }
      pile.style.transform = `translate(${sx.toFixed(2)}px,${sy.toFixed(2)}px)`;

      let topX = 0, topY = 0;
      wins.forEach((w, i) => {
        const ti = tAt(i), a = P(t, ti, .34), e = easeOutBack(a, 1.5);
        const ko = easeInOutCubic(P(t, OUT + (8 - i) * .03, .5));        // swept away, newest first
        const depth = clamp(n - 1 - i, 0, 8);
        let x = X0 + i * DX + w.jx * m + (1 - e) * w.ix;
        let y = Y0 + i * DY + w.jy * m + (1 - e) * w.iy - ko * 46;
        const sc = s * lerp(1.1, 1, e) * (1 - .07 * ko);
        if (i === 8) { topX = X0 + i * DX + w.jx * m + WW * s * .55; topY = Y0 + i * DY + w.jy * m + WH * s * .5; }
        w.el.style.transform = `translate(${x.toFixed(2)}px,${y.toFixed(2)}px) scale(${sc.toFixed(4)})`;
        w.el.style.opacity = clamp(a * 4) * (1 - ko);
        // buried windows sink out of focus and into a grey haze until their titles can't be read
        w.fog.style.opacity = clamp(depth * .09, 0, .5).toFixed(3);
        const blur = clamp((depth - .6) * .9, 0, 3.2) + ko * 8;
        w.el.style.filter = blur > .05 ? `blur(${blur.toFixed(2)}px)` : 'none';
      });

      // taskbar buttons pile up and shrink too
      const bw = Math.min(176, 800 / nn) - 6;
      btns.forEach((b, i) => {
        const a = easeOutCubic(P(t, tAt(i), .3)), ko = easeInOutCubic(P(t, OUT + (8 - i) * .03, .5));
        b.style.left = (56 + i * (bw + 6)).toFixed(1) + 'px';
        b.style.width = bw.toFixed(1) + 'px';
        b.style.opacity = a * (1 - ko);
        b.style.transform = `translateY(${(1 - a) * 12}px)`;
      });

      // RAM: each tab bites a chunk, the rest creeps; 38% at 1.0 -> 94% at 9.5
      let bites = 0; for (let i = 0; i < 9; i++) bites += easeOutCubic(P(t, tAt(i) + .05, .5));
      const v = Math.round(lerp(RAM0, RAM1, .6 * bites / 9 + .4 * P(t, T0, RAM_END - T0)));
      const c = mixColor(mixColor('#C2BBA9', COL.brass, invLerp(48, 62, v)), COL.bad, invLerp(78, 89, v));
      setText(ramV, v + '%');
      ramV.style.color = c;
      ramBar.style.width = v + '%';
      ramBar.style.background = c;
      const alarm = invLerp(86, 94, v) * (.6 + .4 * Math.sin(t * Math.PI * 2 * 1.4));
      ram.style.borderColor = alarm > .01 ? rgba(COL.bad, .25 + .5 * alarm) : 'rgba(255,255,255,.13)';
      ram.style.boxShadow = `0 12px 30px rgba(0,0,0,.5), 0 0 ${(34 * alarm).toFixed(1)}px ${rgba(COL.bad, .55 * alarm)}`;
      ram.style.opacity = easeOutCubic(P(t, .9, .5));
      // the screen's edges warm to red as memory runs out
      red.style.boxShadow = `inset 0 0 160px ${rgba(COL.bad, .28 * invLerp(80, 94, v) * (.75 + .25 * Math.sin(t * Math.PI * 2 * 1.4)))}`;

      // busy cursor, jiggled by an impatient hand
      const bk = win(t, 6.9, OUT + .15, .25, .3);
      xf(busy, { x: topX + wiggle(t, 5, 3.1, 26), y: topY + wiggle(t, 9, 2.7, 16), o: bk });
      ring.style.transform = `rotate(${(t * 420) % 360}deg)`;
    },
  });
})();
