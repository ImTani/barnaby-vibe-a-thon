/* Shop PC: the Hartleys' 2009 Windows 7-era desktop, as components the film can animate.
 *
 *   const pc = PC.build(rootEl, { lw: 1280, lh: 720 });   // once (scene build). Logical px; scale the root yourself.
 *   pc.render(state);                                      // every frame. A pure function of `state`.
 *
 * `state` is merged over PC.DEFAULT, so every animatable property is written on every call and frames can be rendered
 * in any order (the film framework's rule). Named presets live in PC.STATES; see index.html for the URL params.
 * All artwork is original: no real logos, product names or system sounds. Depends on icons.js, wallpaper.js,
 * site.js (Theo's back office) and tabs.js (the other eight tabs). */
(function (G) {
  'use strict';
  const I = G.ICONS, ICO = I.ICO, FAV = I.FAV;

  function h(tag, cls, html, parent) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    if (parent) parent.appendChild(e);
    return e;
  }
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

  /* ------------------------------------------------------------------ the nine tabs ------------------------------ */
  // id, tab title, favicon, address, security zone. Order = the script's order.
  const TABS = [
    { id: 'shop', title: 'Back Office v2.3', fav: () => FAV.shop(16), url: ['http://localhost:8101', '/jobs'], zone: 'intranet' },
    { id: 'supplier', title: 'Supplier portal', fav: () => FAV.supplier(16), url: ['http://trade.northgatecycle.co.uk', '/account/order.aspx?cat=brakes'], zone: 'internet' },
    { id: 'sms', title: 'SMS box', fav: () => FAV.sms(16), url: ['http://www.smsbox-uk.net', '/send.php'], zone: 'internet' },
    { id: 'xls', title: 'workload.xls', fav: () => FAV.xls(16), url: ['file:///C:/Users/Shop/Desktop/', 'workload.xls'], zone: 'computer' },
    { id: 'invoices', title: 'Invoices', fav: () => FAV.invoices(16), url: ['https://www.ledgerbook-online.co.uk', '/sales/invoices?status=unpaid'], zone: 'internet' },
    { id: 'parts', title: 'Parts list', fav: () => FAV.parts(16), url: ['http://localhost', '/theo/partslist.htm'], zone: 'intranet' },
    { id: 'email', title: 'Email', fav: () => FAV.mail(16), url: ['http://webmail.spokesandsprockets.co.uk', '/inbox'], zone: 'internet' },
    { id: 'bank', title: 'Bank', fav: () => FAV.bank(16), url: ['https://business.harbourcounty.co.uk', '/online/timeout'], zone: 'internet', ev: 'Harbour & County Bank plc [GB]' },
    { id: 'cal', title: 'Calendar', fav: () => FAV.cal(16), url: ['http://webmail.spokesandsprockets.co.uk', '/calendar/week'], zone: 'internet' },
  ];
  const SITE_URL = { jobs: '/jobs', po: '/purchase-orders', reports: '/reports', parts: '/parts', mechanics: '/mechanics' };

  /* ------------------------------------------------------------------ defaults and presets ----------------------- */
  const DEFAULT = {
    // time (the taskbar clock, the clock and calendar gadgets)
    date: '2026-11-23', time: '08:52',
    secs: 0,                 // second hand of the clock gadget
    // gadgets: 0..1. The dial needles read these directly, so tween them for the "needle climbs" beat.
    ram: .31, cpu: .06,
    // desktop
    sel: null,               // id of a selected desktop icon
    start: 0,                // Start menu: 0 = closed, 1 = open (in between = the Win7 fade-and-rise)
    startHot: 'shop',        // highlighted Start menu row
    orbGlow: null,           // null = follows `start`; else 0..1 hover glow on the orb
    // the browser
    browser: false,          // window visible
    max: false,              // maximised (covers the gadgets)
    tabs: [],                // open tab ids, in order, e.g. ['shop', 'supplier', ...]
    tabIn: 1,                // 0..1 growth of the LAST tab in `tabs` (a tab opening)
    active: null,            // active tab id (defaults to the last one)
    notresp: false,          // "(Not Responding)" title + whitened page
    page: 'jobs',            // Theo's page in the Back Office tab: jobs | po | reports | parts | mechanics
    reports: 'soon',         // 'soon' = "Reports (coming soon!!)", 'built' = "Reports" (Barnaby's workload report)
    po: 0,                   // 0..1 the new purchase order row (#3) sliding in; 1 = in place
    poHl: 0,                 // 0..1 yellow "just appeared" highlight on that row
    reassign: 0,             // 0..1 Dev -> Priya on jobs 4471 and 4472 (0 = Dev, >= .5 = Priya, highlight peaks at .5)
    scroll: 0,               // page scroll (logical px) of the active tab
    marquee: 0,              // Theo's marquee offset (px); tween it for movement
    loading: 0,              // 0..1 status-bar progress (0 = "Done")
    // overlays
    balloon: false,          // "low on memory" tray balloon
    barnaby: 'off',          // Barnaby's slot: 'off' | 'slot' (dashed guide) | 'frame' (empty Aero window for his UI)
    barnabyTray: false,      // his bell's place in the tray / on the taskbar
    cursor: null,            // {x, y, busy: angle|false} in logical px
    dim: 0,                  // 0..1 screen dimming (the PC going to sleep at the end)
  };

  const MON = { date: '2026-11-23', time: '08:52' };
  const NIGHT = { date: '2026-11-19', time: '21:47' };          // Theo's last week, the night before his last day
  const ALL_TABS = TABS.map(t => t.id);
  const STATES = {
    'desktop': { ...MON },
    'start': { ...MON, start: 1, orbGlow: 1 },
    'tabs': { ...NIGHT, browser: true, tabs: ALL_TABS, active: 'cal', ram: .93, cpu: .71, cursor: { x: 612, y: 404 } },
    'tabs-parts': { ...NIGHT, browser: true, tabs: ALL_TABS, active: 'parts', ram: .94, cpu: .64, cursor: { x: 516, y: 84 } },
    'tabs-busy': { ...NIGHT, time: '21:49', browser: true, tabs: ALL_TABS, active: 'cal', ram: .98, cpu: 1, notresp: true, balloon: true, cursor: { x: 640, y: 360, busy: 40 } },
    'shop-jobs': { ...MON, browser: true, tabs: ['shop'], page: 'jobs', ram: .34, cpu: .09 },
    'shop-po': { ...MON, time: '09:04', browser: true, tabs: ['shop'], page: 'po', po: 1, poHl: 1, ram: .35, cpu: .12 },
    'shop-reports-soon': { ...MON, time: '11:18', browser: true, tabs: ['shop'], page: 'reports', reports: 'soon', ram: .34, cpu: .08 },
    'shop-reports': { ...MON, time: '11:26', browser: true, tabs: ['shop'], page: 'reports', reports: 'built', ram: .36, cpu: .1 },
    'shop-jobs-after': { ...MON, time: '11:31', browser: true, tabs: ['shop'], page: 'jobs', reports: 'built', reassign: .62, scroll: 34, ram: .35, cpu: .09 },
    'barnaby': { ...MON, browser: true, tabs: ['shop'], page: 'jobs', barnaby: 'slot', barnabyTray: true, ram: .36, cpu: .1 },
    'barnaby-frame': { ...MON, browser: true, tabs: ['shop'], page: 'jobs', barnaby: 'frame', barnabyTray: true, ram: .36, cpu: .1 },
  };

  /* ------------------------------------------------------------------ gadgets ------------------------------------ */
  // A 2009-style system meter: smoked-black capsule, chrome bezels, two needle dials (CPU small, MEMORY big, since
  // memory is the one that climbs), red zone, LCD-ish percentages, glossy highlight. Original design.
  function meterSVG() {
    const u = I.uid('mt');
    const dial = (cx, cy, r, big) => {
      const ticks = [];
      for (let i = 0; i <= (big ? 20 : 10); i++) {
        const v = i / (big ? 20 : 10), a = (-120 + 240 * v) * Math.PI / 180, major = big ? i % 2 === 0 : true;
        const r0 = r - (major ? (big ? 7 : 5.5) : 4), r1 = r - 1.8;
        ticks.push(`<line x1="${(cx + Math.sin(a) * r0).toFixed(2)}" y1="${(cy - Math.cos(a) * r0).toFixed(2)}" x2="${(cx + Math.sin(a) * r1).toFixed(2)}" y2="${(cy - Math.cos(a) * r1).toFixed(2)}" stroke="${v > .79 ? '#ff6a4a' : '#e9eef3'}" stroke-width="${major ? 1.3 : .7}"/>`);
        if (big && i % 4 === 0) {
          const rl = r - 14;
          ticks.push(`<text x="${(cx + Math.sin(a) * rl).toFixed(2)}" y="${(cy - Math.cos(a) * rl + 2.4).toFixed(2)}" text-anchor="middle" font-family="Segoe UI" font-size="6.6" font-weight="600" fill="${v > .79 ? '#ff8a6a' : '#cfd8e2'}">${Math.round(v * 100)}</text>`);
        }
      }
      // red zone arc 80..100
      const arc = (v0, v1, rr) => {
        const a0 = (-120 + 240 * v0) * Math.PI / 180, a1 = (-120 + 240 * v1) * Math.PI / 180;
        return `M${(cx + Math.sin(a0) * rr).toFixed(2)} ${(cy - Math.cos(a0) * rr).toFixed(2)} A${rr} ${rr} 0 0 1 ${(cx + Math.sin(a1) * rr).toFixed(2)} ${(cy - Math.cos(a1) * rr).toFixed(2)}`;
      };
      const rz = r - (big ? 4.6 : 3.6);
      return `
        <circle cx="${cx}" cy="${cy}" r="${r + (big ? 5.5 : 4.5)}" fill="url(#${u}chrome)" stroke="#1a1d21" stroke-width=".8"/>
        <circle cx="${cx}" cy="${cy}" r="${r + 1.2}" fill="#0b0d10" stroke="url(#${u}chromeIn)" stroke-width="1.4"/>
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="url(#${u}face)"/>
        <path d="${arc(.8, 1, rz)}" stroke="#d8261b" stroke-width="${big ? 4.2 : 3}" fill="none" opacity=".9"/>
        <path d="${arc(.6, .8, rz)}" stroke="#e8a21b" stroke-width="${big ? 2 : 1.6}" fill="none" opacity=".55"/>
        ${ticks.join('')}
        <text x="${cx}" y="${cy + r * .42}" text-anchor="middle" font-family="Segoe UI" font-size="${big ? 6.4 : 5.4}" font-weight="700" letter-spacing=".9" fill="#8c99a7">${big ? 'MEMORY' : 'CPU'}</text>
        <g class="needle-${big ? 'ram' : 'cpu'}" transform="rotate(0 ${cx} ${cy})">
          <path d="M${cx - (big ? 2.1 : 1.7)} ${cy + (big ? 7 : 5)} L${cx - .55} ${cy - r + (big ? 5 : 4)} L${cx + .55} ${cy - r + (big ? 5 : 4)} L${cx + (big ? 2.1 : 1.7)} ${cy + (big ? 7 : 5)}Z" fill="url(#${u}needle)" filter="url(#${u}glow)"/>
        </g>
        <circle cx="${cx}" cy="${cy}" r="${big ? 5 : 3.8}" fill="url(#${u}cap)" stroke="#20252b" stroke-width=".6"/>
        <ellipse cx="${cx}" cy="${cy - r * .42}" rx="${r * .78}" ry="${r * .5}" fill="url(#${u}gloss)"/>`;
    };
    return `<svg width="164" height="118" viewBox="0 0 164 118" class="meter-svg"><defs>
      <linearGradient id="${u}plate" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4b525a"/><stop offset=".48" stop-color="#1b1f24"/><stop offset=".52" stop-color="#0c0e11"/><stop offset="1" stop-color="#22272d"/></linearGradient>
      <linearGradient id="${u}chrome" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".35" stop-color="#b9c2cc"/><stop offset=".55" stop-color="#5d6771"/><stop offset=".8" stop-color="#d7dde3"/><stop offset="1" stop-color="#8a949e"/></linearGradient>
      <linearGradient id="${u}chromeIn" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#e9eef3"/><stop offset="1" stop-color="#4d5660"/></linearGradient>
      <radialGradient id="${u}face" cx=".5" cy=".62" r=".62"><stop offset="0" stop-color="#2a323b"/><stop offset=".75" stop-color="#11151a"/><stop offset="1" stop-color="#050608"/></radialGradient>
      <linearGradient id="${u}needle" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ffb070"/><stop offset=".4" stop-color="#ff6a1f"/><stop offset="1" stop-color="#ff3b12"/></linearGradient>
      <radialGradient id="${u}cap" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#9aa4ae"/><stop offset="1" stop-color="#3c444d"/></radialGradient>
      <linearGradient id="${u}gloss" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".34"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
      <linearGradient id="${u}lcd" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c1a10"/><stop offset="1" stop-color="#16301d"/></linearGradient>
      <filter id="${u}glow" x="-80%" y="-20%" width="260%" height="140%"><feGaussianBlur stdDeviation=".9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>
      <rect x="3" y="30" width="158" height="68" rx="34" fill="url(#${u}plate)" stroke="#05070a" stroke-width="1"/>
      <rect x="4.2" y="31.2" width="155.6" height="65.6" rx="32.8" fill="none" stroke="#c6ced6" stroke-opacity=".55" stroke-width=".8"/>
      <path d="M20 33 H140 a31 31 0 0 1 18 10 C120 40 60 40 6 48 a31 31 0 0 1 14 -15z" fill="#fff" opacity=".12"/>
      ${dial(38, 64, 24, false)}
      ${dial(110, 58, 42, true)}
      <g font-family="Consolas, 'Lucida Console', monospace" font-weight="700" text-anchor="middle">
        <rect x="22" y="94" width="32" height="12" rx="2.5" fill="url(#${u}lcd)" stroke="#5d6771" stroke-width=".7"/>
        <text class="pct-cpu" x="38" y="103.2" font-size="8.6" fill="#8dff9a">0%</text>
        <rect x="92" y="104" width="36" height="12" rx="2.5" fill="url(#${u}lcd)" stroke="#5d6771" stroke-width=".7"/>
        <text class="pct-ram" x="110" y="113.2" font-size="8.6" fill="#8dff9a">0%</text>
      </g></svg>`;
  }

  function clockSVG() {
    const u = I.uid('ck');
    let marks = '';
    for (let i = 0; i < 60; i++) {
      const a = i / 60 * Math.PI * 2, big = i % 5 === 0, r0 = big ? 38.5 : 41.2, r1 = 43;
      marks += `<line x1="${(60 + Math.sin(a) * r0).toFixed(2)}" y1="${(60 - Math.cos(a) * r0).toFixed(2)}" x2="${(60 + Math.sin(a) * r1).toFixed(2)}" y2="${(60 - Math.cos(a) * r1).toFixed(2)}" stroke="#2b333c" stroke-width="${big ? 2 : .7}"/>`;
    }
    const nums = [12, 3, 6, 9].map((n, i) => { const a = i * Math.PI / 2; return `<text x="${(60 + Math.sin(a) * 31).toFixed(1)}" y="${(60 - Math.cos(a) * 31 + 4.6).toFixed(1)}" text-anchor="middle" font-family="Segoe UI" font-size="13" fill="#2b333c">${n}</text>`; }).join('');
    return `<svg width="124" height="124" viewBox="0 0 120 120"><defs>
      <linearGradient id="${u}rim" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".3" stop-color="#c3cbd4"/><stop offset=".55" stop-color="#5f6973"/><stop offset=".8" stop-color="#dfe4ea"/><stop offset="1" stop-color="#7c8792"/></linearGradient>
      <radialGradient id="${u}face" cx=".5" cy=".45" r=".6"><stop offset="0" stop-color="#ffffff"/><stop offset=".8" stop-color="#eef2f6"/><stop offset="1" stop-color="#c9d2dc"/></radialGradient>
      <linearGradient id="${u}gl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".85"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
      <circle cx="60" cy="60" r="55" fill="url(#${u}rim)" stroke="#2a3038" stroke-width="1"/>
      <circle cx="60" cy="60" r="47.5" fill="url(#${u}face)" stroke="#4a545e" stroke-width="1"/>
      ${marks}${nums}
      <g font-family="Segoe UI" font-size="6" fill="#7d8996" text-anchor="middle" letter-spacing=".6"><text x="60" y="80">QUARTZ</text></g>
      <g class="hand-h" transform="rotate(0 60 60)"><path d="M57.6 66 L59.2 33 L60.8 33 L62.4 66Z" fill="#1f262e"/></g>
      <g class="hand-m" transform="rotate(0 60 60)"><path d="M58.3 67 L59.5 19 L60.5 19 L61.7 67Z" fill="#1f262e"/></g>
      <g class="hand-s" transform="rotate(0 60 60)"><path d="M59.6 72 L59.75 17 L60.25 17 L60.4 72Z" fill="#d22a1c"/><circle cx="60" cy="68" r="2.2" fill="#d22a1c"/></g>
      <circle cx="60" cy="60" r="3.2" fill="#d22a1c" stroke="#6a0e06" stroke-width=".6"/><circle cx="60" cy="60" r="1.1" fill="#f3d0cc"/>
      <path d="M22 50 A39 39 0 0 1 98 50 C84 40 36 40 22 50Z" fill="url(#${u}gl)" opacity=".75"/></svg>`;
  }

  /* ------------------------------------------------------------------ build -------------------------------------- */
  function build(root, opts = {}) {
    const LW = opts.lw || 1280, LH = opts.lh || 720, TB = 40;
    root.classList.add('pc');
    if (opts.blur === false) root.classList.add('noblur');   // bit-exact frames: no backdrop blur behind the glass
    root.style.width = LW + 'px'; root.style.height = LH + 'px';
    const parts = {};

    // wallpaper
    h('div', 'wallpaper', G.WALLPAPER(), root);

    // desktop icons (Theo's)
    const icons = h('div', 'desk-icons', null, root);
    const DESK = [
      ['bin', 'Recycle Bin', I.bin(48)],
      ['shop', 'Shop System', I.sprocket(48) + I.shortcutBadge(48)],
      ['inv', 'INVOICES 2009', I.folder(48, { papers: 2 })],
      ['theo', 'theo stuff DO NOT DELETE', I.folder(48, { papers: 1 })],
      ['xls', 'workload.xls', I.doc(48, 'sheet')],
      ['bak', 'backup to USB.bat', I.doc(48, 'bat')],
      ['wp', 'wallpaper FINAL2.png', I.photo(48)],
    ];
    parts.icons = DESK.map(([id, label, svg]) => {
      const d = h('div', 'dicon', `<div class="img">${svg}</div><div class="lbl">${label}</div>`, icons);
      d.dataset.id = id; return d;
    });

    // gadgets (right edge, top down, as Win7 lays them out)
    const gad = h('div', 'gadgets', null, root);
    const gMeter = h('div', 'gadget g-meter', meterSVG(), gad);
    const gClock = h('div', 'gadget g-clock', clockSVG(), gad);
    const gCal = h('div', 'gadget g-cal', `<div class="pg"><div class="hd"><span class="m"></span></div><div class="num"></div><div class="day"></div><div class="gloss"></div><div class="curl"></div></div><div class="rings"><i></i><i></i></div>`, gad);
    parts.gad = {
      ram: gMeter.querySelector('.needle-ram'), cpu: gMeter.querySelector('.needle-cpu'),
      ramT: gMeter.querySelector('.pct-ram'), cpuT: gMeter.querySelector('.pct-cpu'),
      hh: gClock.querySelector('.hand-h'), hm: gClock.querySelector('.hand-m'), hs: gClock.querySelector('.hand-s'),
      calM: gCal.querySelector('.m'), calN: gCal.querySelector('.num'), calD: gCal.querySelector('.day'),
    };

    // the browser window
    const bw = buildBrowser(root, LW, LH, TB);
    parts.browser = bw;

    // Barnaby's slot
    const slotG = barnabyGeom(LW, LH, TB);
    const slot = h('div', 'barnaby-slot', null, root);
    Object.assign(slot.style, { left: slotG.x + 'px', top: slotG.y + 'px', width: slotG.w + 'px', height: slotG.h + 'px' });
    slot.innerHTML = `<div class="frame glass glass-tint"></div>
      <div class="titlebar"><span class="ttext">Barnaby</span><div class="caps"><i class="mn"></i><i class="mx"></i><i class="x"></i></div></div>
      <div class="client" id="barnaby-client"></div>
      <div class="guide"><b>Barnaby's window</b><span>#barnaby-slot</span><code>logical ${slotG.x},${slotG.y} &middot; ${slotG.w}&times;${slotG.h}</code><code>at 1920&times;1080: ${slotG.x * 1.5},${slotG.y * 1.5} &middot; ${slotG.w * 1.5}&times;${slotG.h * 1.5}</code><code>client: #barnaby-client</code><span class="who">(his identity: video/v2/look/identity/)</span></div>`;
    parts.slot = slot;

    // Start menu
    parts.start = buildStart(root, TB);

    // taskbar
    parts.tb = buildTaskbar(root, TB);

    // tray balloon
    const bal = h('div', 'balloon', `<div class="bx">&#10005;</div><div class="bh">${ICO.warn(16)}<span>Your computer is low on memory</span></div><div class="bt">To restore enough memory for programs to work correctly, save your files and then close or restart all open programs.</div>`, root);
    Object.assign(bal.style, { right: '56px', bottom: (TB + 12) + 'px' });
    parts.balloon = bal;

    // cursor
    const cur = h('div', 'cursor', `<svg class="arrow" width="20" height="28" viewBox="0 0 20 28"><path d="M1.5 1.5 L1.5 21.5 L6.2 17 L9.4 24.8 L12.6 23.4 L9.5 15.9 L15.8 15.9Z" fill="#fff" stroke="#000" stroke-width="1.1" stroke-linejoin="round"/></svg><span class="busy"></span>`, root);
    parts.cursor = cur;

    // dimmer (sleep)
    parts.dim = h('div', 'dimmer', null, root);

    const api = {
      el: root, LW, LH, TABS, STATES, DEFAULT,
      /** Barnaby's slot in logical px (multiply by your scale; 1.5 at 1920x1080). */
      barnabySlot: slotG,
      barnabyClient: slot.querySelector('#barnaby-client'),
      render(s) { renderAll(parts, { ...DEFAULT, ...s }, LW, LH, TB); },
      preset(name, extra = {}) { return { ...DEFAULT, ...(STATES[name] || {}), ...extra }; },
    };
    return api;
  }

  /** Where Barnaby's window sits (logical px): to the right, over the gadgets, clear of Theo's nav bar. */
  function barnabyGeom(LW, LH, TB) {
    const w = 476, hgt = LH - TB - 64;
    return { x: LW - w - 14, y: 30, w, h: hgt };
  }

  function browserGeom(LW, LH, TB, max) {
    if (max) return { x: 0, y: 0, w: LW, h: LH - TB };
    return { x: 8, y: 8, w: LW - 188, h: LH - TB - 14 };     // leaves the gadget column clear
  }

  function buildBrowser(root, LW, LH, TB) {
    const win = h('div', 'win browser', null, root);
    win.innerHTML = `<div class="frame glass glass-tint"></div>
      <div class="titlebar"><span class="ticon">${I.globe(16)}</span><span class="ttext"></span><div class="caps"><i class="mn"></i><i class="mx"></i><i class="x"></i></div></div>
      <div class="navrow">
        <div class="navbtns"><span class="bk">${ICO.back(27)}</span><span class="fw">${ICO.fwd(23)}</span></div>
        <div class="addr"><span class="fav"></span><span class="ev"></span><span class="url"><span class="host"></span><span class="rest"></span></span><span class="ab compat">${compatIcon()}</span><span class="ab dd">${ICO.dropdown(7)}</span><span class="ab lock">${ICO.lock(14)}</span><span class="ab">${ICO.refresh(15)}</span><span class="ab">${ICO.stop(14)}</span></div>
        <div class="search"><span class="sfav">${ICO.mag(14)}</span><span>Web Search</span><span class="sb">${ICO.mag(14)}</span></div>
      </div>
      <div class="lightbar favbar">
        <span class="fb big">${ICO.star(16)}<span>Favourites</span></span>
        <span class="fb icon">${ICO.star(16, true)}</span>
        <span class="sep"></span>
        <span class="fb">${FAV.shop(16)}<span>Back Office</span></span>
        <span class="fb">${FAV.supplier(16)}<span>Northgate Trade</span></span>
        <span class="fb">${FAV.bank(16)}<span>Bank</span></span>
        <span class="fb">${ICO.page(16)}<span>5 day weather</span></span>
      </div>
      <div class="lightbar tabrow">
        <span class="qt"><span class="qtg">${quickTabsIcon()}</span><span class="qtd">${ICO.dropdown(7)}</span></span>
        <div class="tabs"></div>
        <div class="cmdbar">
          <span class="cmd">${ICO.home(16)}<span class="dd">${ICO.dropdown(7)}</span></span>
          <span class="cmd c-feed">${ICO.feed(16)}<span class="dd">${ICO.dropdown(7)}</span></span>
          <span class="cmd c-mail">${I.mail(16)}</span>
          <span class="cmd">${ICO.print(16)}<span class="dd">${ICO.dropdown(7)}</span></span>
          <span class="cmd c-lbl">${ICO.page(16)}<span class="lb">Page</span><span class="dd">${ICO.dropdown(7)}</span></span>
          <span class="cmd c-lbl c-safety">${ICO.shield(16)}<span class="lb">Safety</span><span class="dd">${ICO.dropdown(7)}</span></span>
          <span class="cmd c-lbl">${ICO.tools(16)}<span class="lb">Tools</span><span class="dd">${ICO.dropdown(7)}</span></span>
          <span class="cmd c-help">${ICO.help(16)}<span class="dd">${ICO.dropdown(7)}</span></span>
          <span class="cmd chev">&raquo;</span>
        </div>
      </div>
      <div class="client">
        <div class="viewport"><div class="page-host"></div><div class="vscroll"><span class="arr">${arrowGlyph(0)}</span><span class="track"><i class="thumb"></i></span><span class="arr">${arrowGlyph(180)}</span></div></div>
        <div class="statusbar"><div class="st-msg"><span class="st-ico">${ICO.page(14)}</span><span class="st-text">Done</span><span class="prog"><i></i></span></div><div class="st-zone"><span class="z-ico"></span><span class="z-text"></span></div><div class="st-zoom">${ICO.mag(12, '#3a4a5c')}<span>100%</span><span class="dd">${ICO.dropdown(7)}</span></div></div>
      </div>`;
    const tabsEl = win.querySelector('.tabs');
    const host = win.querySelector('.page-host');
    const tabs = {}, pages = {};
    TABS.forEach((t, i) => {
      const tab = h('div', 'tab', `<span class="tf">${t.fav()}</span><span class="tt">${t.title}</span><span class="tx">&#10005;</span>`, tabsEl);
      tab.dataset.id = t.id;
      tabs[t.id] = tab;
      const pg = h('div', 'page-wrap', null, host);
      pg.dataset.id = t.id;
      pg.innerHTML = t.id === 'shop' ? G.SITE.html() : G.TABPAGES[t.id]();
      pages[t.id] = pg;
    });
    const newtab = h('div', 'tab newtab', '', tabsEl);
    newtab.style.order = 99;
    return {
      win, tabs, pages, newtab,
      title: win.querySelector('.titlebar .ttext'),
      fav: win.querySelector('.addr .fav'), host: win.querySelector('.addr .host'), rest: win.querySelector('.addr .rest'),
      addr: win.querySelector('.addr'), ev: win.querySelector('.addr .ev'),
      zoneIco: win.querySelector('.z-ico'), zoneText: win.querySelector('.z-text'),
      stText: win.querySelector('.st-text'), prog: win.querySelector('.prog'), progI: win.querySelector('.prog i'),
      thumb: win.querySelector('.thumb'), cmdbar: win.querySelector('.cmdbar'), qt: win.querySelector('.qt'),
      site: G.SITE.bind(pages.shop),
    };
  }

  const compatIcon = () => `<svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h5.2l-.9 2.2 1.4 1.6-1.1 2.5 1.1 1.8-.9 2.9H2z" fill="#eef3f9" stroke="#5a6f8a" stroke-width=".8"/><path d="M9.2 3H14v11H9.6l.8-2.6-1-1.8 1.1-2.6-1.4-1.6z" fill="#eef3f9" stroke="#5a6f8a" stroke-width=".8"/><path d="M3.5 6h2M3.5 8.5h1.6M11 6h1.6M11.2 11h1.4" stroke="#7fa0c8" stroke-width=".9"/></svg>`;
  const quickTabsIcon = () => `<svg width="16" height="16" viewBox="0 0 16 16">${[[1.5, 1.5], [8.5, 1.5], [1.5, 8.5], [8.5, 8.5]].map(([x, y]) => `<rect x="${x}" y="${y}" width="6" height="6" rx=".8" fill="#fff" stroke="#5a6f8a" stroke-width=".8"/>`).join('')}<rect x="2.5" y="2.5" width="4" height="1.4" fill="#7fa0c8"/></svg>`;
  const arrowGlyph = rot => `<svg width="9" height="9" viewBox="0 0 9 9" style="transform:rotate(${rot}deg)"><path d="M1 6.2 L4.5 2.6 L8 6.2z" fill="#3a3a3a"/></svg>`;

  function buildStart(root, TB) {
    const m = h('div', 'startmenu', null, root);
    m.style.bottom = TB + 'px';
    const L = [
      ['web', I.globe(32), 'Internet', 'Web browser', true],
      ['mail', I.mail(32), 'E-mail', 'Webmail', false],
      'sep',
      ['shop', I.sprocket(32), 'Shop System', 'Back Office v2.3', true],
      ['sheet', I.sheetApp(32), 'Spreadsheet 2007', null, true],
      ['sol', I.cards(32), 'Solitaire', null, false],
      ['pic', I.palette(32), 'Picture Studio 7', null, true],
      ['calc', I.calc(32), 'Calculator', null, false],
      ['disc', I.disc(32), 'Disc Burner', null, true],
      ['bak', I.doc(32, 'bat'), 'backup to USB', null, false],
      ['media', I.media(32), 'Media Player', null, true],
    ];
    const left = L.map(r => {
      if (r === 'sep') return '<div class="sm-sep"></div>';
      const [id, ic, lb, , jl] = r;
      return `<div class="sm-item" data-id="${id}"><span class="ic">${ic}</span><span class="lb">${lb}</span>${jl ? `<span class="jl">${ICO.arrowR(8)}</span>` : ''}</div>`;
    }).join('');
    const R = ['Shop', 'Documents', 'Pictures', 'Music', 'gap', 'Games', 'Computer', 'gap', 'Control Panel', 'Devices and Printers', 'Default Programs', 'Help and Support'];
    let right = '', gap = false;
    for (const r of R) { if (r === 'gap') { gap = true; continue; } right += `<div class="sm-r${gap ? ' gap' : ''}${r === 'Shop' ? ' user' : ''}">${r}</div>`; gap = false; }
    m.innerHTML = `<div class="frame glass"></div>
      <div class="sm-left"><div class="sm-list">${left}</div>
        <div class="sm-all"><span class="arr">${ICO.arrowR(8)}</span><span>All Programs</span></div></div>
      <div class="sm-search"><span>Search programs and files</span>${ICO.mag(14, '#6d7a89')}</div>
      <div class="sm-right">${right}</div>
      <div class="sm-user">${I.bikeTile(48)}</div>
      <div class="sm-shut"><span class="b">Shut down</span><span class="a">${ICO.arrowR(8, '#fff')}</span></div>`;
    return { el: m, items: [...m.querySelectorAll('.sm-item')] };
  }

  function buildTaskbar(root, TB) {
    const tb = h('div', 'taskbar', null, root);
    tb.style.height = TB + 'px';
    tb.innerHTML = `<div class="orb"><div class="ball">${orbSprocket()}</div></div>
      <div class="tb-apps">
        <div class="tb-btn" data-id="web" style="--glow:rgba(90,170,255,.75)">${I.globe(30)}</div>
        <div class="tb-btn" data-id="files" style="--glow:rgba(250,210,110,.7)">${I.folder(32, { papers: 1 })}</div>
        <div class="tb-btn" data-id="media" style="--glow:rgba(255,160,60,.7)">${I.media(30)}</div>
        <div class="tb-btn" data-id="sheet" style="--glow:rgba(110,210,120,.7)">${I.sheetApp(30)}</div>
        <div class="tb-btn barnaby-tb" data-id="barnaby"><span class="slot-mark"></span></div>
      </div>
      <div class="tray">
        <span class="ti up">${ICO.upArrow(14)}</span>
        <span class="ti barnaby-tray"><span class="slot-mark"></span></span>
        <span class="ti">${I.sprocket(16, { teeth: 12 })}</span>
        <span class="ti">${ICO.shield(15)}</span>
        <span class="ti">${ICO.net(16)}</span>
        <span class="ti">${ICO.speaker(16)}</span>
        <div class="clock"><span class="t"></span><span class="d"></span></div>
        <div class="showdesk"></div>
      </div>`;
    return { el: tb, orb: tb.querySelector('.orb'), web: tb.querySelector('[data-id="web"]'), bTb: tb.querySelector('.barnaby-tb'),
      bTray: tb.querySelector('.barnaby-tray'), t: tb.querySelector('.clock .t'), d: tb.querySelector('.clock .d') };
  }

  /** The Start orb's glyph: a white sprocket, so the orb is the shop's own and not anyone's flag. */
  function orbSprocket() {
    // a chainring, not a settings cog: many fine teeth, a thin ring, five spider arms to a hub
    const ring = I.gearPath(12, 12, 22, 9.5, 11.2, .4, .56) + ' ' + I.circ(12, 12, 7.6);
    const arms = I.spider(12, 12, 5, 3.6, 7.6, 1.9);
    return `<svg width="24" height="24" viewBox="0 0 24 24"><path d="${ring}" fill="#fff" fill-rule="evenodd"/><path d="${arms}" fill="#fff"/>
      <circle cx="12" cy="12" r="3.1" fill="#fff"/><circle cx="12" cy="12" r="1.2" fill="#2a8fd8"/></svg>`;
  }

  /* ------------------------------------------------------------------ render ------------------------------------- */
  function renderAll(P, s, LW, LH, TB) {
    const d = new Date(s.date + 'T12:00:00');
    const [hh, mm] = s.time.split(':').map(Number);
    // taskbar clock (UK)
    P.tb.t.textContent = s.time;
    P.tb.d.textContent = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
    // clock gadget
    const mins = hh * 60 + mm + (s.secs || 0) / 60;
    P.gad.hh.setAttribute('transform', `rotate(${((mins / 60) % 12) * 30} 60 60)`);
    P.gad.hm.setAttribute('transform', `rotate(${(mins % 60) * 6} 60 60)`);
    P.gad.hs.setAttribute('transform', `rotate(${(s.secs || 0) * 6} 60 60)`);
    // calendar gadget
    P.gad.calM.textContent = MONTHS[d.getMonth()];
    P.gad.calN.textContent = d.getDate();
    P.gad.calD.textContent = DAYS[d.getDay()];
    // meter
    const ram = clamp(s.ram), cpu = clamp(s.cpu);
    P.gad.ram.setAttribute('transform', `rotate(${-120 + 240 * ram} 110 58)`);
    P.gad.cpu.setAttribute('transform', `rotate(${-120 + 240 * cpu} 38 64)`);
    P.gad.ramT.textContent = Math.round(ram * 100) + '%';
    P.gad.cpuT.textContent = Math.round(cpu * 100) + '%';
    P.gad.ramT.setAttribute('fill', ram > .795 ? '#ff7a5a' : '#8dff9a');
    P.gad.cpuT.setAttribute('fill', cpu > .795 ? '#ff7a5a' : '#8dff9a');

    // desktop icons
    P.icons.forEach(e => e.classList.toggle('sel', e.dataset.id === s.sel));

    // browser
    const B = P.browser, open = s.browser && s.tabs.length > 0;
    B.win.style.display = open ? '' : 'none';
    if (open) renderBrowser(B, s, LW, LH, TB);
    P.tb.web.classList.toggle('run', open);
    P.tb.web.classList.toggle('active', open && !(s.start > .5) && s.barnaby === 'off');
    P.tb.web.classList.toggle('stack', open && s.tabs.length > 1);

    // Barnaby
    const slot = P.slot;
    slot.style.display = s.barnaby === 'off' ? 'none' : '';
    slot.classList.toggle('as-slot', s.barnaby === 'slot');
    slot.classList.toggle('as-frame', s.barnaby === 'frame');
    B.win.classList.toggle('inactive', s.barnaby !== 'off' || s.start > .5);
    P.tb.bTb.style.display = s.barnabyTray && s.barnaby !== 'off' ? '' : 'none';
    P.tb.bTb.classList.toggle('run', s.barnaby !== 'off');
    P.tb.bTb.classList.toggle('active', s.barnaby !== 'off');
    P.tb.bTray.style.display = s.barnabyTray ? '' : 'none';

    // Start menu: Win7 fades it in while it rises a few px
    const st = clamp(s.start);
    P.start.el.style.display = st > 0 ? '' : 'none';
    P.start.el.style.opacity = st;
    P.start.el.style.transform = `translateY(${(1 - st) * 8}px)`;
    P.start.items.forEach(e => e.classList.toggle('hot', st > 0 && e.dataset.id === s.startHot));
    const glow = s.orbGlow == null ? st : s.orbGlow;
    P.tb.orb.style.setProperty('--glow', clamp(glow));

    // balloon, cursor, dim
    P.balloon.style.display = s.balloon ? '' : 'none';
    if (s.cursor) {
      P.cursor.style.display = '';
      P.cursor.style.left = s.cursor.x + 'px'; P.cursor.style.top = s.cursor.y + 'px';
      const busy = P.cursor.querySelector('.busy');
      busy.innerHTML = s.cursor.busy !== undefined && s.cursor.busy !== false ? I.busyRing(22, +s.cursor.busy || 0) : '';
    } else P.cursor.style.display = 'none';
    P.dim.style.opacity = clamp(s.dim);
    P.dim.style.display = s.dim > 0 ? '' : 'none';
  }

  function renderBrowser(B, s, LW, LH, TB) {
    const g = browserGeom(LW, LH, TB, s.max);
    Object.assign(B.win.style, { left: g.x + 'px', top: g.y + 'px', width: g.w + 'px', height: g.h + 'px' });
    B.win.classList.toggle('max', !!s.max);
    B.win.classList.toggle('notresp', !!s.notresp);
    const ids = s.tabs, act = s.active && ids.includes(s.active) ? s.active : ids[ids.length - 1];
    const tdef = TABS.find(t => t.id === act);
    const n = ids.length;
    // tabs: order by `tabs`; the last one may be growing in
    for (const t of TABS) {
      const el = B.tabs[t.id], i = ids.indexOf(t.id);
      el.style.display = i < 0 ? 'none' : '';
      el.style.order = i;
      el.classList.toggle('on', t.id === act);
      const grow = i === n - 1 ? clamp(s.tabIn) : 1;
      el.style.maxWidth = (n > 1 ? 196 : 230) * grow + 'px';
      el.style.opacity = Math.min(1, grow * 1.6);
      B.pages[t.id].style.display = t.id === act ? '' : 'none';
    }
    B.win.classList.toggle('many', n >= 5);
    B.win.classList.toggle('single', n === 1);
    B.qt.style.display = n > 1 ? '' : 'none';
    // title, address, zone
    let title = tdef.title, rest = tdef.url[1];
    if (act === 'shop') {
      title = 'Spokes & Sprockets - Back Office v2.3';
      rest = SITE_URL[s.page] || '/jobs';
    }
    B.title.textContent = title + (s.notresp ? ' (Not Responding)' : '');
    B.fav.innerHTML = tdef.fav();
    B.host.textContent = tdef.url[0];
    B.rest.textContent = rest;
    B.addr.classList.toggle('ev', !!tdef.ev);
    B.ev.textContent = tdef.ev || '';
    const Z = { intranet: [ICO.zone(14), 'Local intranet | Protected Mode: Off'], internet: [I.globe(14), 'Internet | Protected Mode: On'], computer: [ICO.zone(14), 'Computer | Protected Mode: Off'] }[tdef.zone];
    B.zoneIco.innerHTML = Z[0]; B.zoneText.textContent = Z[1];
    const ld = clamp(s.loading);
    B.stText.textContent = s.notresp ? 'Waiting for http://webmail.spokesandsprockets.co.uk/...' : ld > 0 ? `Opening page ${tdef.url[0]}${rest}...` : 'Done';
    B.prog.style.display = ld > 0 || s.notresp ? '' : 'none';
    B.progI.style.width = (s.notresp ? 38 : ld * 100) + '%';
    // the page
    if (act === 'shop') B.site.render(s);
    const pageEl = B.pages[act].firstElementChild;
    if (pageEl) pageEl.style.marginTop = `${-s.scroll}px`;   // layout offset, not a transform: no layer promotion, stable text AA
    // scrollbar thumb: rough proportion of page height to viewport
    const vh = B.pages[act].parentElement.clientHeight || 500, ph = Math.max(vh, B.pages[act].scrollHeight || vh);
    const frac = clamp(vh / ph, .12, 1), pos = clamp(s.scroll / Math.max(1, ph - vh));
    B.thumb.style.height = (frac * 100) + '%';
    B.thumb.style.top = (pos * (1 - frac) * 100) + '%';
  }

  G.PC = { build, DEFAULT, STATES, TABS, browserGeom, barnabyGeom };
})(window);
