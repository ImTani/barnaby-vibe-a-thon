/* PRIYA · THE LACING CHART (pick). The system as a wheel she would build: Barnaby at the hub, 24 spokes for the 24
   things it can do, the rim divided into the shop's rooms (data/building.js groups, same order and colours as her
   toolroll). Tensioned spoke = he can use it; slack (bowed) = waits for a key; left out = kept shut; brass nipple = new.
   PRIYA_LACING.render(container, {moment, w, h})  'priyaTuesday' -> 1920x1080 hero; 'build' -> 640x1080 panel. */
(function () {
  const W = window.WORLDS;
  const C = { ground: '#141518', rim: '#c9ced4', rimDk: '#7d858e', steel: '#dfe3e8', slack: '#8d96a0', brass: '#b8893a', brassHi: '#e2bd6c',
    bone: '#f2ede3', boneDim: '#a7a39b', ink: '#141518', red: '#ff4a3b' };
  const ROOM = { counter: '#ffd23f', till: '#ff9ac1', workshop: '#6ee0b0', stockroom: '#ffa24c', backdoor: '#7fcbff', office: '#c6a8ff' };
  const FONT = "'Tw Cen MT Condensed','Tw Cen MT',sans-serif", FONT_W = "'Tw Cen MT','Tw Cen MT Condensed',sans-serif", HAND = "'Ink Free',cursive";
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const rad = d => d * Math.PI / 180, P = (cx, cy, r, a) => [cx + r * Math.cos(rad(a)), cy + r * Math.sin(rad(a))];
  const SAY = { cancel_job: 'Cancel a job: left out, no undo', book_job: 'Book a bike in' };
  const icon = {
    key: (x, y, s = 1, col = C.bone) => `<g transform="translate(${x} ${y}) scale(${s})" fill="none" stroke="${col}" stroke-width="2.6" stroke-linecap="round"><circle cx="-6" cy="0" r="5.5"/><path d="M-0.5 0 H12 M8 0 v5 M12 0 v4"/></g>`,
    shut: (x, y, s = 1, col = C.bone) => `<g transform="translate(${x} ${y}) scale(${s})" fill="none" stroke="${col}" stroke-width="2.8" stroke-linecap="round"><path d="M-6 -6 L6 6 M6 -6 L-6 6"/></g>`,
    tick: (x, y, s = 1, col = C.bone) => `<path transform="translate(${x} ${y}) scale(${s})" d="M-7 0 L-2 5 L8 -6" fill="none" stroke="${col}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`,
    warn: (x, y, s = 1, col = C.red) => `<g transform="translate(${x} ${y}) scale(${s})"><path d="M0 -10 L10 8 L-10 8 Z" fill="${col}"/><path d="M0 -3 v5" stroke="${C.ink}" stroke-width="2.4" stroke-linecap="round"/><circle cy="5" r="1.3" fill="${C.ink}"/></g>`,
    bell: (x, y, s = 1, col = C.bone) => `<g transform="translate(${x} ${y}) scale(${s})" fill="${col}"><path d="M-9 4 Q-9 -9 0 -10 Q9 -9 9 4 Z"/><rect x="-12" y="4" width="24" height="3" rx="1.5"/><circle cy="-12" r="2"/></g>`,
    star: (x, y, s = 1, col = C.brassHi) => `<path transform="translate(${x} ${y}) scale(${s})" d="M0 -9 L2.6 -2.8 L9 -2.8 L3.9 1.2 L5.8 7.6 L0 3.8 L-5.8 7.6 L-3.9 1.2 L-9 -2.8 L-2.6 -2.8 Z" fill="${col}"/>`,
  };
  function defs() {
    return `<defs>
      <filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="5" result="n"/>
        <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .06 0"/><feComposite in2="SourceGraphic" operator="in"/></filter>
      <filter id="lift" x="-10%" y="-10%" width="120%" height="120%"><feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#000" flood-opacity=".55"/></filter>
      <linearGradient id="rimface" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e3e7eb"/><stop offset=".5" stop-color="#b9bfc6"/><stop offset="1" stop-color="#d7dce1"/></linearGradient>
      <radialGradient id="brass" cx=".4" cy=".35" r=".75"><stop offset="0" stop-color="#e9c97c"/><stop offset=".6" stop-color="#b8893a"/><stop offset="1" stop-color="#7f5c22"/></radialGradient>
    </defs>`;
  }

  /* the wheel itself. cx, cy centre; R = rim inner radius. labels: draw the words along each spoke. */
  function wheel(cx, cy, R, momentId, opts = {}) {
    const st = W.state(momentId), B = W.building, o = [], lab = opts.labels !== false;
    const order = B.groups.map(g => g.id), seq = [];
    order.forEach(g => st.filter(a => a.group === g).forEach(a => seq.push(a)));
    const ang = i => -90 + 7.5 + 15 * i, HUB = R * 0.135, HOLE = HUB * 0.8, RO = R + R * 0.075;
    // rim: silver double wall, room bands on the inner edge, room names on the rim face
    o.push(`<g filter="url(#lift)"><circle cx="${cx}" cy="${cy}" r="${(R + RO) / 2}" fill="none" stroke="url(#rimface)" stroke-width="${RO - R}"/></g>`);
    o.push(`<circle cx="${cx}" cy="${cy}" r="${RO}" fill="none" stroke="${C.rimDk}" stroke-width="1.6"/><circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="${C.rimDk}" stroke-width="1.6"/>`);
    let i0 = 0;
    order.forEach((g, gi) => {
      const n = seq.filter(a => a.group === g).length, a0 = ang(i0) - 7.5, a1 = ang(i0 + n - 1) + 7.5, col = ROOM[g];
      const [x0, y0] = P(cx, cy, R - 7, a0 + 1.2), [x1, y1] = P(cx, cy, R - 7, a1 - 1.2), big = a1 - a0 > 180 ? 1 : 0;
      o.push(`<path d="M${x0} ${y0} A${R - 7} ${R - 7} 0 ${big} 1 ${x1} ${y1}" fill="none" stroke="${col}" stroke-width="9" stroke-linecap="round"/>`);
      if (lab) {
        const rr = (R + RO) / 2, mid = (a0 + a1) / 2, bottom = mid > 0 && mid < 180, id = `rimtext-${g}-${Math.round(R)}`;
        // text on the rim face: clockwise on the top half, anticlockwise on the bottom so it never reads upside down
        const [s0x, s0y] = P(cx, cy, rr, bottom ? a1 : a0), [s1x, s1y] = P(cx, cy, rr, bottom ? a0 : a1);
        o.push(`<path id="${id}" d="M${s0x} ${s0y} A${rr} ${rr} 0 0 ${bottom ? 0 : 1} ${s1x} ${s1y}" fill="none"/>`);
        const name = B.groups.find(q => q.id === g).name;
        o.push(`<text font-family="${FONT}" font-weight="700" font-size="${opts.rimSize || 20}" fill="${C.ink}" dy="7" letter-spacing="1.2"><textPath href="#${id}" startOffset="50%" text-anchor="middle">${esc(name.replace(/^The /, '').toUpperCase())}</textPath></text>`);
      }
      const [sx, sy] = P(cx, cy, R - 2, a0), [ex, ey] = P(cx, cy, RO + 2, a0);
      o.push(`<path d="M${sx} ${sy} L${ex} ${ey}" stroke="${C.ink}" stroke-width="2.6"/>`);
      i0 += n;
    });
    // valve hole at the top, between the back office and the counter
    const [vx, vy] = P(cx, cy, (R + RO) / 2, -90);
    o.push(`<circle cx="${vx}" cy="${vy}" r="${(RO - R) * .26}" fill="${C.ground}" stroke="${C.rimDk}" stroke-width="1.4"/>`);
    // spokes
    const pos = {};
    seq.forEach((a, i) => {
      const t = ang(i), col = ROOM[a.group], [hx, hy] = P(cx, cy, HOLE, t), [rx, ry] = P(cx, cy, R - 2, t);
      pos[a.tool] = { t, i };
      if (a.state === 'shut') {
        const [qx, qy] = P(cx, cy, R + (RO - R) * .45, t);
        o.push(`<circle cx="${qx}" cy="${qy}" r="${Math.max(3, R * .009)}" fill="${C.ground}"/>`);
        const [kx, ky] = P(cx, cy, R - R * .05, t); o.push(icon.shut(kx, ky, R / 420, C.bone));
      } else if (a.state === 'key') {
        const [mx, my] = P(cx, cy, (HOLE + R) / 2, t), bow = R * .075 * (t > 90 && t < 270 ? 1 : -1), nx = -Math.sin(rad(t)), ny = Math.cos(rad(t));
        o.push(`<path d="M${hx} ${hy} Q${mx + nx * bow} ${my + ny * bow} ${rx} ${ry}" fill="none" stroke="${C.slack}" stroke-width="${Math.max(1.6, R * .006)}" stroke-dasharray="${R * .02} ${R * .012}"/>`);
        const [kx, ky] = P(cx, cy, R - R * .055, t); o.push(icon.key(kx, ky, R / 470, col));
      } else if (a.state === 'new') {
        const [mx, my] = P(cx, cy, HOLE + (R - HOLE) * .45, t);
        o.push(`<path d="M${mx} ${my} L${rx} ${ry}" stroke="${C.brassHi}" stroke-width="${Math.max(2.4, R * .009)}" stroke-linecap="round"/><path d="M${hx} ${hy} L${mx} ${my}" stroke="${C.brassHi}" stroke-width="${Math.max(2, R * .007)}" stroke-dasharray="4 5"/>`);
      } else {
        o.push(`<path d="M${hx} ${hy} L${rx} ${ry}" stroke="${C.steel}" stroke-width="${Math.max(2, R * .0075)}" stroke-linecap="round"/>`);
      }
      if (a.state !== 'shut') { // nipple: anodised in the room colour, brass when new
        const isNew = a.state === 'new' || a.tool === 'workload', [n0x, n0y] = P(cx, cy, R - R * .02, t), [n1x, n1y] = P(cx, cy, R + (RO - R) * .5, t);
        o.push(`<path d="M${n0x} ${n0y} L${n1x} ${n1y}" stroke="${isNew ? C.brassHi : col}" stroke-width="${Math.max(5, R * .02)}" stroke-linecap="round" opacity="${a.state === 'key' ? .55 : 1}"/>`);
      }
      if (lab) {
        const left = t > 90 && t < 270, r0 = R * .3, lit = a.state === 'lit' || a.state === 'new', words = SAY[a.tool] || a.say;
        const off = left ? -R * .022 : R * .022, [tx, ty] = P(cx, cy, r0, t), nx = -Math.sin(rad(t)) * off, ny = Math.cos(rad(t)) * off;
        const rot = left ? t + 180 : t, anchor = left ? 'end' : 'start';
        o.push(`<text transform="translate(${tx + nx} ${ty + ny}) rotate(${rot})" text-anchor="${anchor}" dy="${left ? 6 : 6}" font-family="${FONT}" font-weight="${lit ? 700 : 400}" font-size="${opts.labelSize || 19}" fill="${a.state === 'shut' ? C.boneDim : lit ? C.bone : C.boneDim}">${esc(words)}</text>`);
      }
    });
    // the hand-back passage: one cord laced round the hub through three spokes
    if (opts.passage !== false && W.moments[momentId].passage) {
      const r = HUB + R * .035, ts = ['notify', 'job_detail', 'update_status'].map(k => pos[k].t).sort((a, b) => a - b);
      const [a0, a1] = [ts[0], ts[2]], [x0, y0] = P(cx, cy, r, a0), [x1, y1] = P(cx, cy, r, a1);
      o.push(`<path d="M${x0} ${y0} A${r} ${r} 0 0 1 ${x1} ${y1}" fill="none" stroke="${C.bone}" stroke-width="${R * .011}" stroke-linecap="round"/><path d="M${x0} ${y0} A${r} ${r} 0 0 1 ${x1} ${y1}" fill="none" stroke="${C.ink}" stroke-width="${R * .011}" stroke-dasharray="${R * .005} ${R * .014}"/>`);
      ts.forEach(t => { const [x, y] = P(cx, cy, r, t); o.push(`<circle cx="${x}" cy="${y}" r="${R * .014}" fill="${C.bone}" stroke="${C.ink}" stroke-width="1.5"/>`); });
    }
    // hub: Barnaby, brass, with the bell
    o.push(`<g filter="url(#lift)"><circle cx="${cx}" cy="${cy}" r="${HUB}" fill="url(#brass)"/></g>`);
    for (let k = 0; k < 24; k++) { const [x, y] = P(cx, cy, HOLE, ang(k)); o.push(`<circle cx="${x}" cy="${y}" r="${HUB * .055}" fill="#5c4214"/>`); }
    o.push(`<circle cx="${cx}" cy="${cy}" r="${HUB * .58}" fill="none" stroke="#7f5c22" stroke-width="1.5"/>`);
    o.push(icon.bell(cx, cy + HUB * .08, HUB / 26, '#4a350f'));
    return { svg: o.join(''), pos };
  }

  function hero(w, h) {
    const S = W.story.priyaTuesday, n = W.counts('priyaTuesday'), o = [];
    o.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${defs()}`);
    o.push(`<rect width="${w}" height="${h}" fill="${C.ground}"/><rect width="${w}" height="${h}" fill="#000" filter="url(#grain)"/>`);
    const cx = 960, cy = 540, R = 398;
    o.push(wheel(cx, cy, R, 'priyaTuesday').svg);
    const D = `font-family="${FONT_W}"`, LX = 56, RXc = 1446, RW = w - RXc - 50;
    // left: her questions, his first answer
    const wrapHand = (x, y, lines, sz = 31) => lines.map((l, i) => `<text x="${x}" y="${y + i * sz * 1.22}" font-family="${HAND}" font-size="${sz}" fill="#ffffff">${esc(l)}</text>`).join('');
    o.push(wrapHand(LX, 92, ['So you’re why I’ve got', 'two wheel builds on my first day?']));
    o.push(`${icon.bell(LX + 12, 182, 1.05)}<text x="${LX + 34}" y="${192}" ${D} font-size="28" fill="${C.bone}">Guilty. Dev had thirty-one hours</text><text x="${LX + 34}" y="${226}" ${D} font-size="28" fill="${C.bone}">booked. You had none.</text>`);
    o.push(wrapHand(LX, 292, ['Fair. What else can', 'this thing do?']));
    // legend, bottom left
    const GY = 640, rows = [
      [`<path d="M${LX} ${GY} h46" stroke="${C.steel}" stroke-width="3"/><path d="M${LX + 46} ${GY} h9" stroke="${ROOM.workshop}" stroke-width="7" stroke-linecap="round"/>`, `Tight spoke: I can do it (${n.lit})`],
      [`<path d="M${LX} ${GY} Q${LX + 26} ${GY + 10} ${LX + 50} ${GY}" fill="none" stroke="${C.slack}" stroke-width="2.4" stroke-dasharray="8 5"/>${icon.key(LX + 30, GY - 12, .9, C.bone)}`, `Slack, with a key: ask Martin first (${n.key})`],
      [`${icon.shut(LX + 26, GY, 1)}`, `Left out: never (${n.shut})`],
      [`<path d="M${LX} ${GY} h46" stroke="${C.steel}" stroke-width="3"/><path d="M${LX + 46} ${GY} h9" stroke="${C.brassHi}" stroke-width="7" stroke-linecap="round"/>`, `Brass nipple: added yesterday`],
      [`<path d="M${LX} ${GY + 4} q26 -16 52 0" fill="none" stroke="${C.bone}" stroke-width="4"/><circle cx="${LX}" cy="${GY + 4}" r="4" fill="${C.bone}"/><circle cx="${LX + 52}" cy="${GY + 4}" r="4" fill="${C.bone}"/>`, `Cord at the hub: “Hand it back”, one go`],
      [`<circle cx="${LX + 26}" cy="${GY}" r="15" fill="url(#brass)"/>${icon.bell(LX + 26, GY + 1, .7, '#4a350f')}`, `The hub: me`],
    ];
    rows.forEach(([ic, t], i) => o.push(`<g transform="translate(0 ${i * 52})">${ic}<text x="${LX + 76}" y="${GY + 7}" ${D} font-size="21" fill="${C.bone}">${esc(t)}</text></g>`));
    o.push(`<text x="${LX}" y="${GY - 56}" font-family="${FONT}" font-weight="700" font-size="27" fill="${C.bone}">24 spokes, one for each thing</text><text x="${LX}" y="${GY - 26}" font-family="${FONT}" font-weight="700" font-size="27" fill="${C.bone}">the shop’s system can do</text>`);
    // right: his answer, her stand, who's collecting, Theo's note
    o.push(`${icon.bell(RXc + 14, 74, 1.4)}<text x="${RXc + 42}" y="${86}" ${D} font-size="40" font-weight="700" fill="${C.bone}">Your jobs, the parts</text><text x="${RXc + 42}" y="${132}" ${D} font-size="40" font-weight="700" fill="${C.bone}">they need, who’s</text><text x="${RXc + 42}" y="${178}" ${D} font-size="40" font-weight="700" fill="${C.bone}">collecting what.</text>`);
    let y = 248;
    S.bench.forEach((j, i) => {
      const side = j.job === 4471 ? 'front' : 'rear', hrs = j.job === 4471 ? '6' : '5½';
      o.push(`<text x="${RXc}" y="${y}" font-family="${FONT}" font-weight="700" font-size="27" fill="${C.bone}">${j.job} ${esc(j.who)}</text>`);
      o.push(`<text x="${RXc}" y="${y + 30}" ${D} font-size="21" fill="${C.bone}">${esc(j.bike)}, ${side}, 32 hole</text><text x="${RXc}" y="${y + 58}" ${D} font-size="21" fill="${C.boneDim}">${hrs} h · due <tspan fill="${C.bone}" font-weight="700">${j.job === 4471 ? 'today' : 'Wednesday'}</tspan></text>`);
      if (i === 0) o.push(`${icon.tick(RXc + 9, y + 81, 1)}<text x="${RXc + 26}" y="${y + 88}" ${D} font-size="21" fill="${C.bone}">Spokes and rim on the shelf</text>`);
      else o.push(`${icon.warn(RXc + 11, y + 81, 1.1)}<text x="${RXc + 28}" y="${y + 88}" ${D} font-size="21" font-weight="700" fill="${C.red}">Spokes short: 40 on the shelf,</text><text x="${RXc + 28}" y="${y + 114}" ${D} font-size="21" font-weight="700" fill="${C.red}">64 for both wheels</text>`);
      y += i === 0 ? 128 : 160;
    });
    const ready = window.SHOP ? window.SHOP.jobs.filter(j => j.status === 'ready') : [];
    o.push(`<text x="${RXc}" y="${y}" font-family="${FONT}" font-weight="700" font-size="27" fill="${ROOM.counter}">Ready to collect</text>`);
    ready.forEach((j, i) => o.push(`<text x="${RXc}" y="${y + 36 + i * 31}" ${D} font-size="21" fill="${C.bone}"><tspan font-weight="700">${esc(j.customer)}</tspan><tspan fill="${C.boneDim}">  ${esc(j.bike)}</tspan></text>`));
    y += 36 + 4 * 31 + 30;
    o.push(`<text x="${RXc}" y="${y}" ${D} font-size="22" fill="${C.bone}">And Theo left you a note:</text>`);
    o.push(`<path d="M${RXc} ${y + 16} v86" stroke="${C.bone}" stroke-width="3"/><text x="${RXc + 18}" y="${y + 50}" font-family="${FONT}" font-weight="700" font-size="31" fill="${C.bone}">Never trust the stock count</text><text x="${RXc + 18}" y="${y + 84}" font-family="${FONT}" font-weight="700" font-size="31" fill="${C.bone}">on a Friday.</text><text x="${RXc + 18}" y="${y + 112}" ${D} font-size="19" fill="${C.boneDim}">from his README</text>`);
    o.push('</svg>');
    return o.join('');
  }

  /* PANEL (Mon 23 Nov 2026, 15:05-15:08): the new spoke laces in; two rims arrive on her truing stand */
  function panel(w, h) {
    const P2 = W.story.priyaTuesday, S = W.story.build, o = [];
    o.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${defs()}`);
    o.push(`<rect width="${w}" height="${h}" fill="${C.ground}"/><rect width="${w}" height="${h}" fill="#000" filter="url(#grain)"/>`);
    const D = `font-family="${FONT_W}"`;
    const cx = w / 2, cy = 318, R = 182, wh = wheel(cx, cy, R, 'build', { labels: false, rimSize: 14 });
    o.push(wh.svg);
    // call out the new spoke
    const t = wh.pos.workload.t, [nx, ny] = P(cx, cy, R * .62, t);
    o.push(`<circle cx="${nx}" cy="${ny}" r="22" fill="none" stroke="${C.brassHi}" stroke-width="3"/>`);
    o.push(`<path d="M${nx - 16} ${ny - 16} L${nx - 60} ${84}" stroke="${C.brassHi}" stroke-width="2"/>`);
    o.push(`<text x="28" y="40" font-family="${FONT}" font-weight="700" font-size="25" fill="${C.brassHi}">A new spoke, laced in at ${S.time}:</text><text x="28" y="68" ${D} font-size="20" fill="${C.bone}">each mechanic’s hours this week</text>`);
    // her truing stand with the two rims that just arrived
    let y = 572;
    o.push(`<text x="28" y="${y}" font-family="${FONT}" font-weight="700" font-size="27" fill="${C.bone}">Two rims on your hooks, from Dev at 15:08</text>`);
    const rimAt = (x, yy, r, label) => {
      const s = [`<g filter="url(#lift)"><circle cx="${x}" cy="${yy}" r="${r}" fill="none" stroke="url(#rimface)" stroke-width="${r * .12}"/></g>`];
      for (let k = 0; k < 32; k++) { const [hx, hy] = P(x, yy, r - r * .03, k * 11.25); s.push(`<circle cx="${hx}" cy="${hy}" r="${r * .016}" fill="${C.ground}"/>`); }

      return s.join('');
    };
    const r = 104, rail = y + 30, c1 = 160, c2 = w - 160, cyR = rail + 12 + r;
    o.push(`<path d="M28 ${rail} H${w - 28}" stroke="#4b525a" stroke-width="9" stroke-linecap="round"/>`);
    [c1, c2].forEach(cxh => o.push(`<path d="M${cxh} ${rail} v10 q0 10 -8 12" fill="none" stroke="#8d96a0" stroke-width="5" stroke-linecap="round"/>`));
    o.push(rimAt(c1, cyR, r));
    o.push(rimAt(c2, cyR, r));
    o.push(`<text x="${c1}" y="${cyR + 8}" text-anchor="middle" font-family="${FONT}" font-weight="700" font-size="22" fill="${C.bone}">front, 32 hole</text><text x="${c2}" y="${cyR + 8}" text-anchor="middle" font-family="${FONT}" font-weight="700" font-size="22" fill="${C.bone}">rear, 32 hole</text>`);
    y = cyR + r + 2;
    const job = (x, yy, j, hrs, warn) => `<text x="${x}" y="${yy}" font-family="${FONT}" font-weight="700" font-size="25" fill="${C.bone}">${j.job} ${esc(j.who.split(' ')[0])}</text>
      <text x="${x}" y="${yy + 28}" ${D} font-size="20" fill="${C.bone}">${esc(j.bike)}</text>
      <text x="${x}" y="${yy + 54}" ${D} font-size="20" fill="${C.boneDim}">${hrs} h · due ${esc(j.dueDate)}</text>
      ${warn ? `${icon.warn(x + 11, yy + 79, 1)}<text x="${x + 26}" y="${yy + 86}" ${D} font-size="19" font-weight="700" fill="${C.red}">Spokes short</text>` : `${icon.tick(x + 9, yy + 79, .9)}<text x="${x + 24}" y="${yy + 86}" ${D} font-size="19" fill="${C.bone}">Parts on the shelf</text>`}`;
    o.push(job(40, y + 52, P2.bench[0], '6'));
    o.push(job(w / 2 + 24, y + 52, P2.bench[1], '5½', true));
    o.push(`<text x="28" y="${h - 62}" ${D} font-size="20" fill="${C.bone}">Dev: 31 → 19½ of his 20 hours.</text><text x="28" y="${h - 34}" ${D} font-size="20" fill="${C.bone}">Moved with Martin’s say-so.</text>`);
    o.push('</svg>');
    return o.join('');
  }

  window.PRIYA_LACING = { render(el, { moment = 'priyaTuesday', w = 1920, h = 1080 } = {}) { el.innerHTML = moment === 'build' ? panel(w, h) : hero(w, h); }, wheel, ROOM };
})();
