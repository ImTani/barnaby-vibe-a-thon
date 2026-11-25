/* PRIYA · THE TOOLROLL (assigned, raised). Her new toolroll unrolled on the bench: every thing the system can do is a
   tool in a pocket, stitched into sections by room (data/building.js groups, front door to back door).
   PRIYA_ROLL.render(container, {moment, w, h})  moment 'priyaTuesday' -> 1920x1080 hero; 'build' -> 640x1080 panel.
   Raises carried (data/hands.js): thread colour = room; handling marks fade with time; each pocket carries the words to
   ask for it; one ruled scale (her hours of 30); the object is the label; red only for what needs her. */
(function () {
  const W = window.WORLDS;
  const C = {
    bench: '#1d1e21', canvas: '#23449b', canvasHi: '#2c52b0', pocket: '#1d3b8a', pocketHem: '#16306f',
    leather: '#95582b', leatherDk: '#6a3a17', bone: '#f2ede3', boneDim: 'rgba(242,237,227,.62)', ink: '#121316',
    steel: '#d3d8de', steelDk: '#646d77', red: '#ff4a3b', webbing: '#151619',
  };
  /* thread colour per room, same order as the plan: counter, till, workshop floor, stockroom, back door, back office */
  const THREAD = { counter: '#ffd23f', till: '#ff9ac1', workshop: '#6ee0b0', stockroom: '#ffa24c', backdoor: '#7fcbff', office: '#c6a8ff' };
  const FONT = "'Tw Cen MT Condensed','Tw Cen MT',sans-serif", FONT_W = "'Tw Cen MT','Tw Cen MT Condensed',sans-serif", HAND = "'Ink Free',cursive";

  /* the exact words to ask for each one (raise: ANSI board), and the object that says it (raise: Fletcher) */
  const ASK = {
    search: ['Find Rachel Okafor', 'loupe'], customer_detail: ['What’s Magnus riding?', 'glasses'],
    add_customer: ['Add a new customer', 'pen'], book_job: ['Book this bike in', 'stamp'],
    notify: ['Text Rachel', 'phone'], recent_notifications: ['What did we text her?', 'envelope'],
    unpaid: ['Who still owes us?', 'spike'], create_invoice: ['Invoice this job', 'pad'], takings: ['What did we take today?', 'coins'],
    open_jobs: ['What’s on my bench?', 'clipboard'], jobs_due: ['What’s due today?', 'stopwatch'],
    job_detail: ['Parts for Rachel’s wheel?', 'spokekey'], update_status: ['Mark it ready', 'bell'],
    assign: ['Give this one to Ravi', 'levers'], mechanics: ['Who works here?', 'lanyard'], cancel_job: ['Cancel a job', 'cutters'],
    parts_low: ['Is anything running low?', 'gauge'], parts: ['What’s on the shelves?', 'bolt'], adjust: ['Change a stock count', 'tally'],
    create_purchase_order: ['Order more spokes', 'parcel'], purchase_orders: ['What have we ordered?', 'docket'],
    receive: ['Book in the delivery', 'cutter'], today_at_a_glance: ['How’s today looking?', 'mirror'],
    workload: ['Who’s got too much on?', 'torque'],
  };
  /* raise: history as a fading wake. What he used this morning (and yesterday, fainter). */
  const WAKE = { open_jobs: ['08:39', 0.85], job_detail: ['08:39', 0.8], workload: ['08:40', 0.75],
    create_purchase_order: ['Mon', 0.32], assign: ['Mon', 0.32] };

  /* ---- tools: drawn upright, x centred on 0, y = 0 is the pocket mouth (negative is above it) ---- */
  function tool(kind, ghost) {
    const S = ghost ? `fill="none" stroke="${C.bone}" stroke-width="2.2" stroke-dasharray="5 4" stroke-linejoin="round"` : '';
    const f = (fill, extra = '') => ghost ? S : `fill="${fill}" stroke="${C.ink}" stroke-width="1.6" stroke-linejoin="round" ${extra}`;
    const st = f(C.steel), bn = f(C.bone), dk = f('#2a2c31');
    const L = (d, w = 2) => ghost ? `<path d="${d}" ${S}/>` : `<path d="${d}" fill="none" stroke="${C.ink}" stroke-width="${w}" stroke-linecap="round"/>`;
    switch (kind) {
      case 'loupe': return `<rect x="-6" y="-96" width="12" height="190" rx="5" ${f('#2a2c31')}/><circle cy="-120" r="22" ${st}/><circle cy="-120" r="14" ${f('#9fc0dc', 'opacity=".95"')}/>${ghost ? '' : '<path d="M-7 -127 q5 -6 12 -4" stroke="#fff" stroke-width="2" fill="none"/>'}`;
      case 'glasses': return `<path d="M-15 -128 L-17 90 M15 -128 L17 90" ${ghost ? S : `stroke="#2a2c31" stroke-width="3.5" fill="none"`}/><circle cx="-13" cy="-138" r="12" ${f('#9fc0dc')}/><circle cx="13" cy="-138" r="12" ${f('#9fc0dc')}/>${L('M-2 -140 q2 -4 4 0', 2.4)}`;
      case 'pen': return `<rect x="-10" y="-112" width="20" height="210" rx="4" ${dk}/><rect x="-11" y="-158" width="22" height="50" rx="6" ${bn}/><rect x="-11" y="-118" width="22" height="7" ${f(THREAD.counter)}/>${ghost ? '' : `<rect x="7" y="-154" width="4" height="34" rx="2" fill="${C.steelDk}"/>`}`;
      case 'stamp': return `<ellipse cy="-146" rx="14" ry="17" ${f('#7a4e2d')}/><rect x="-5" y="-130" width="10" height="44" ${st}/><rect x="-24" y="-88" width="48" height="12" rx="2" ${st}/><rect x="-21" y="-76" width="42" height="24" rx="2" ${f('#2a2c31')}/>${ghost ? L('M-14 -68 h28 M-14 -60 h18', 1.6) : `<path d="M-14 -68 h28 M-14 -60 h18" stroke="${C.boneDim}" stroke-width="2.5"/>`}<rect x="-3" y="-52" width="6" height="140" ${ghost ? 'fill="none" stroke="none"' : `fill="#2a2c31"`}/>`;
      case 'phone': return `<rect x="-21" y="-156" width="42" height="200" rx="8" ${dk}/>${ghost ? `<rect x="-15" y="-144" width="30" height="120" rx="3" ${S}/><path d="M-6 -150 h12" ${S}/>` : `<rect x="-16" y="-148" width="32" height="150" rx="3" fill="#3a5a96"/><path d="M-10 -136 h20 M-10 -128 h14" stroke="${C.bone}" stroke-width="3" stroke-linecap="round"/><rect x="-12" y="-114" width="18" height="10" rx="4" fill="${C.bone}"/>`}`;
      case 'envelope': return `<rect x="-22" y="-142" width="44" height="120" rx="2" ${bn}/>${L('M-22 -142 L0 -112 L22 -142', 1.6)}`;
      case 'spike': return `<path d="M0 -168 L2 -150 L2 90 L-2 90 L-2 -150 Z" ${st}/><rect x="-17" y="-118" width="34" height="22" transform="rotate(-8 0 -107)" ${bn}/><rect x="-16" y="-96" width="32" height="20" transform="rotate(6 0 -86)" ${bn}/><rect x="-18" y="-74" width="36" height="22" transform="rotate(-4 0 -63)" ${bn}/>`;
      case 'pad': return `<rect x="-21" y="-140" width="42" height="200" rx="2" ${bn}/>${ghost ? '' : [-128, -112, -96, -80, -64, -48].map(y => `<path d="M-14 ${y} h${y === -128 ? 18 : 28}" stroke="#7c8796" stroke-width="2"/>`).join('')}${[-14, -5, 4, 13].map(x => `<circle cx="${x}" cy="-142" r="3.2" ${ghost ? S : `fill="none" stroke="${C.ink}" stroke-width="1.8"`}/>`).join('')}`;
      case 'coins': return [0, 1, 2, 3, 4, 5].map(i => `<rect x="-19" y="${-128 + i * 13}" width="38" height="11" rx="4" ${f('#cba650')}/>`).join('') + (ghost ? '' : `<path d="M-14 -123 h28" stroke="#f3dc95" stroke-width="2"/>`);
      case 'clipboard': return `<rect x="-24" y="-150" width="48" height="230" rx="4" ${f('#8c5a33')}/><rect x="-18" y="-138" width="36" height="200" ${bn}/><rect x="-11" y="-160" width="22" height="15" rx="3" ${st}/>${ghost ? '' : [-122, -110, -98, -86, -74].map(y => `<path d="M-12 ${y} h24" stroke="#7c8796" stroke-width="2"/>`).join('')}`;
      case 'stopwatch': return `<rect x="-5" y="-150" width="10" height="12" ${st}/><rect x="-9" y="-158" width="18" height="8" rx="2" ${st}/><circle cy="-114" r="24" ${st}/><circle cy="-114" r="18" ${bn}/>${L('M0 -114 L0 -128', 2.4)}${L('M0 -114 L9 -109', 2.4)}<path d="M-4 -90 L-6 80 M4 -90 L6 80" ${ghost ? S : `stroke="#2a2c31" stroke-width="4"`}/>`;
      case 'spokekey': return `<path d="M0 -96 v180" ${ghost ? S : `stroke="#2a2c31" stroke-width="3"`}/><circle cy="-120" r="23" ${f('#3b4149')}/>${ghost ? '' : `<circle cy="-120" r="23" fill="none" stroke="${C.steel}" stroke-width="2" opacity=".7"/>${[0, 120, 240].map(r => `<rect x="-3.5" y="-146" width="7" height="12" rx="1" fill="${C.canvas}" transform="rotate(${r} 0 -120)"/>`).join('')}`}<circle cy="-120" r="5" ${ghost ? S : `fill="${C.canvas}"`}/>`;
      case 'bell': return `<path d="M0 -84 v170" ${ghost ? S : `stroke="#2a2c31" stroke-width="4"`}/><ellipse cy="-86" rx="22" ry="7" ${st}/><path d="M-20 -88 Q-20 -136 0 -138 Q20 -136 20 -88 Z" ${st}/><path d="M14 -100 L36 -116" ${ghost ? S : `stroke="${C.ink}" stroke-width="4" stroke-linecap="round"`}/>${ghost ? '' : '<path d="M-10 -126 Q-12 -110 -8 -96" stroke="#fff" stroke-width="2.4" fill="none"/>'}`;
      case 'levers': return `<path d="M-20 90 L-20 -146 Q-20 -156 -12 -158 L-6 -150 L-6 90 Z" ${f('#7fcbff')}/><path d="M6 90 L6 -138 Q6 -148 14 -150 L20 -142 L20 90 Z" ${f(C.bone)}/>`;
      case 'lanyard': return `<path d="M-14 -40 L-8 -166 Q0 -176 8 -166 L14 -40" ${ghost ? S : `fill="none" stroke="${THREAD.workshop}" stroke-width="5"`}/><rect x="-21" y="-104" width="42" height="58" rx="4" ${bn}/>${ghost ? '' : `<rect x="-21" y="-104" width="42" height="15" rx="4" fill="#2a2c31"/><rect x="-21" y="-94" width="42" height="5" fill="#2a2c31"/><path d="M-13 -76 h26 M-13 -66 h18" stroke="#2a2c31" stroke-width="2.5"/>`}`;
      case 'cutters': return `<path d="M-4 -160 Q-16 -138 -7 -112 L-2 -112 Q-8 -138 0 -154 Z M4 -160 Q16 -138 7 -112 L2 -112 Q8 -138 0 -154 Z" ${st}/><circle cy="-108" r="6" ${st}/><path d="M-5 -102 L-22 90 L-10 90 L-1 -100 M5 -102 L22 90 L10 90 L1 -100" ${f('#2a2c31')}/>`;
      case 'gauge': return `<rect x="-5" y="-92" width="10" height="180" ${st}/><circle cy="-118" r="25" ${st}/><circle cy="-118" r="19" ${bn}/>${ghost ? '' : `<path d="M-13 -106 A17 17 0 1 1 13 -106" fill="none" stroke="#7c8796" stroke-width="2"/>`}${L('M0 -118 L-12 -108', 3)}`;
      case 'bolt': return `<path d="M-16 -150 L-8 -160 L8 -160 L16 -150 L16 -136 L-16 -136 Z" ${st}/><rect x="-8" y="-136" width="16" height="220" ${st}/>${ghost ? '' : [-128, -120, -112, -104, -96, -88, -80].map(y => `<path d="M-8 ${y} L8 ${y - 4}" stroke="${C.steelDk}" stroke-width="1.6"/>`).join('')}`;
      case 'tally': return `<rect x="-4" y="-158" width="8" height="14" ${st}/><rect x="-22" y="-146" width="44" height="50" rx="14" ${st}/><circle cy="-70" r="16" ${ghost ? S : `fill="none" stroke="${C.steel}" stroke-width="6"`}/>${ghost ? '' : `<rect x="-14" y="-132" width="28" height="14" rx="2" fill="#2a2c31"/>${[-9, -3, 3, 9].map(x => `<rect x="${x - 2}" y="-129" width="4" height="8" fill="${C.bone}"/>`).join('')}`}`;
      case 'parcel': return `<rect x="-24" y="-128" width="48" height="190" rx="2" ${f('#b07a45')}/>${ghost ? '' : `<path d="M0 -128 V62 M-24 -96 H24" stroke="#f2ede3" stroke-width="3"/><path d="M0 -96 q-12 -16 -16 -4 q4 8 16 4 q12 -16 16 -4 q-4 8 -16 4" fill="none" stroke="#f2ede3" stroke-width="2.6"/><rect x="-19" y="-80" width="16" height="12" fill="#f2ede3"/>`}`;
      case 'docket': return `<path d="M-20 -146 L10 -146 L20 -136 L20 80 L-20 80 Z" ${bn}/>${L('M10 -146 L10 -136 L20 -136', 1.5)}${ghost ? '' : [-126, -116, -106, -96].map(y => `<path d="M-13 ${y} h${y === -126 ? 16 : 26}" stroke="#7c8796" stroke-width="2"/>`).join('')}`;
      case 'cutter': return `<path d="M-2 -164 L10 -150 L10 -138 L-2 -138 Z" ${st}/><path d="M-13 -140 L13 -140 L16 90 L-16 90 Z" ${f(C.bone)}/>${ghost ? '' : `<rect x="-9" y="-112" width="18" height="70" rx="4" fill="#2a2c31"/>`}`;
      case 'mirror': return `<ellipse cy="-142" rx="17" ry="14" ${st}/><ellipse cy="-142" rx="12" ry="9.5" ${f('#b9d3ea')}/><path d="M0 -128 L0 -110" ${ghost ? S : `stroke="${C.steel}" stroke-width="4"`}/><rect x="-4" y="-110" width="8" height="60" ${st}/><rect x="-6" y="-50" width="12" height="140" rx="3" ${f('#2a2c31')}/>`;
      case 'torque': return `<circle cy="-150" r="15" ${st}/><circle cy="-150" r="6" ${f('#2a2c31')}/><rect x="-8" y="-136" width="16" height="230" rx="3" ${st}/><rect x="-6" y="-112" width="12" height="44" ${bn}/>${ghost ? '' : [-108, -100, -92, -84, -76].map(y => `<path d="M-6 ${y} h${y % 16 === 0 ? 8 : 5}" stroke="${C.ink}" stroke-width="1.6"/>`).join('')}`;
    }
    return '';
  }
  /* small drawn icons (never glyphs) */
  const icon = {
    key: (x, y, s = 1, col = C.bone) => `<g transform="translate(${x} ${y}) scale(${s})" fill="none" stroke="${col}" stroke-width="2.6" stroke-linecap="round"><circle cx="-6" cy="0" r="5.5"/><path d="M-0.5 0 H12 M8 0 v5 M12 0 v4"/></g>`,
    shut: (x, y, s = 1, col = C.bone) => `<g transform="translate(${x} ${y}) scale(${s})" fill="none" stroke="${col}" stroke-width="2.8" stroke-linecap="round"><path d="M-7 -7 L7 7 M7 -7 L-7 7"/></g>`,
    tick: (x, y, s = 1, col = C.bone) => `<path transform="translate(${x} ${y}) scale(${s})" d="M-7 0 L-2 5 L8 -6" fill="none" stroke="${col}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`,
    warn: (x, y, s = 1, col = C.red) => `<g transform="translate(${x} ${y}) scale(${s})"><path d="M0 -10 L10 8 L-10 8 Z" fill="${col}"/><path d="M0 -3 v5" stroke="${C.ink}" stroke-width="2.4" stroke-linecap="round"/><circle cy="5" r="1.3" fill="${C.ink}"/></g>`,
    bell: (x, y, s = 1, col = C.bone) => `<g transform="translate(${x} ${y}) scale(${s})" fill="${col}"><path d="M-9 4 Q-9 -9 0 -10 Q9 -9 9 4 Z"/><rect x="-12" y="4" width="24" height="3" rx="1.5"/><circle cy="-12" r="2"/></g>`,
    star: (x, y, s = 1, col = C.bone) => `<path transform="translate(${x} ${y}) scale(${s})" d="M0 -9 L2.6 -2.8 L9 -2.8 L3.9 1.2 L5.8 7.6 L0 3.8 L-5.8 7.6 L-3.9 1.2 L-9 -2.8 L-2.6 -2.8 Z" fill="${col}"/>`,
  };
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  /* running stitch along a rect */
  const stitchRect = (x, y, w, h, col, dash = '9 6', sw = 2.4, r = 6) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="none" stroke="${col}" stroke-width="${sw}" stroke-dasharray="${dash}" stroke-linecap="round"/>`;

  function defs() {
    return `<defs>
      <filter id="weave" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="1.1 0.9" numOctaves="2" seed="4" result="n"/>
        <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .55 -.18" result="a"/><feComposite in="a" in2="SourceGraphic" operator="in"/></filter>
      <filter id="wax" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".006 .011" numOctaves="3" seed="11" result="n"/>
        <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .9 -.42"/><feComposite in2="SourceGraphic" operator="in"/></filter>
      <filter id="matgrain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="2" result="n"/>
        <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .07 0"/><feComposite in2="SourceGraphic" operator="in"/></filter>
      <filter id="smudge" x="-50%" y="-50%" width="200%" height="200%"><feTurbulence type="fractalNoise" baseFrequency=".09" numOctaves="2" seed="7" result="n"/>
        <feDisplacementMap in="SourceGraphic" in2="n" scale="16"/><feGaussianBlur stdDeviation="2.2"/></filter>
      <filter id="soft" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="6" stdDeviation="7" flood-color="#000" flood-opacity=".45"/></filter>
      <filter id="softsm" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="2.5" stdDeviation="2.5" flood-color="#000" flood-opacity=".4"/></filter>
      <pattern id="hatch" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="9" height="9" fill="none"/><path d="M0 0 V9" stroke="${C.bone}" stroke-width="2.4"/></pattern>
    </defs>`;
  }
  function canvasRect(x, y, w, h, fill, r = 10) {
    return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}"/>
      <rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" filter="url(#wax)" opacity=".24"/>
      <rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" filter="url(#weave)" opacity=".5"/>`;
  }
  function bench(w, h) {
    return `<rect width="${w}" height="${h}" fill="${C.bench}"/><rect width="${w}" height="${h}" fill="#000" filter="url(#matgrain)"/>
      <ellipse cx="${w * 0.04}" cy="${h * 0.12}" rx="60" ry="22" fill="#000" opacity=".25" filter="url(#smudge)"/>`;
  }

  /* one pocket. x = left, y0 = top of tool area, mouth = pocket mouth y, bottom = pocket bottom */
  function pocket(a, x, pw, mouth, bottom, thread) {
    const [ask, kind] = ASK[a.tool], cx = x + pw / 2, out = [];
    const isShut = a.state === 'shut', isKey = a.state === 'key', isNew = a.tool === 'workload';
    // ghost outline printed on the canvas above the mouth (key and shut)
    if (isKey || isShut) out.push(`<g transform="translate(${cx} ${mouth})" opacity="${isShut ? .55 : .9}">${tool(kind, true)}</g>`);
    else out.push(`<g transform="translate(${cx} ${mouth})" filter="url(#softsm)">${tool(kind, false)}</g>`);
    // handling marks (raise: fading wake)
    const wk = WAKE[a.tool];
    // the pocket itself
    const pf = isNew ? '#2552b8' : C.pocket;
    out.push(canvasRect(x + 2, mouth, pw - 4, bottom - mouth, pf, 4));
    out.push(`<rect x="${x + 2}" y="${mouth}" width="${pw - 4}" height="9" fill="${isNew ? '#2b5cc7' : C.pocketHem}"/>`);
    out.push(`<path d="M${x + 6} ${mouth + 13} H${x + pw - 6}" stroke="${thread}" stroke-width="${isNew ? 2.8 : 2}" stroke-dasharray="7 5" opacity="${isNew ? 1 : .8}"/>`);
    out.push(`<path d="M${x + 5} ${mouth + 4} V${bottom - 6} M${x + pw - 5} ${mouth + 4} V${bottom - 6}" stroke="${thread}" stroke-width="${isNew ? 2.8 : 2}" stroke-dasharray="7 5" opacity="${isNew ? 1 : .75}"/>`);
    if (wk && !isKey) out.push(`<g opacity="${wk[1]}"><ellipse cx="${cx + 9}" cy="${mouth + 30}" rx="19" ry="13" fill="#04060b" opacity=".7" filter="url(#smudge)"/><ellipse cx="${cx - 12}" cy="${mouth + 56}" rx="12" ry="9" fill="#04060b" opacity=".55" filter="url(#smudge)"/><ellipse cx="${cx + 4}" cy="${mouth - 6}" rx="16" ry="6" fill="#04060b" opacity=".5" filter="url(#smudge)"/></g>`);
    if (isShut) { // sewn shut: zig-zag across the mouth
      let z = `M${x + 8} ${mouth - 2}`; for (let i = 0; i < 6; i++) z += ` L${x + 8 + (i + .5) * (pw - 16) / 6} ${mouth + (i % 2 ? -10 : 12)}`; z += ` L${x + pw - 8} ${mouth - 2}`;
      out.push(`<path d="${z}" fill="none" stroke="${C.bone}" stroke-width="3" stroke-linecap="round"/>`);
    }
    // the words to ask for it, up the pocket (reads bottom to top)
    const ty = bottom - 18, tx = cx + 7;
    out.push(`<text transform="translate(${tx} ${ty}) rotate(-90)" font-family="${FONT}" font-size="20" font-weight="700" fill="${isShut ? C.boneDim : C.bone}" letter-spacing=".2">${esc(isShut ? 'Cancel a job: no undo' : '“' + ask + '”')}</text>`);
    // state mark at the foot of the pocket
    const sy = bottom - 2;
    if (isKey) out.push(icon.key(cx + 2, mouth + 50, 1.15));
    if (isShut) out.push(icon.shut(cx, mouth + 50, 1.1));
    if (isNew) out.push(icon.star(cx, mouth + 50, 1.2, thread));
    return out.join('');
  }

  /* ================= HERO: Tuesday morning ================= */
  function hero(w, h) {
    const S = W.story.priyaTuesday, B = W.building, st = W.state('priyaTuesday'), n = W.counts('priyaTuesday');
    const o = [];
    o.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${defs()}`);
    o.push(bench(w, h));
    const RX = 118, RY = 30, RW = w - RX - 26, RH = h - RY - 26, FOLD = 316, MOUTH = 560, PB = 862;
    // strap and buckle on the bench, out of the roll's left end
    o.push(`<g filter="url(#soft)"><path d="M${RX + 12} 610 C 60 640, 40 760, 92 900 L 116 1060 L 80 1060 L 58 905 C 8 760, 30 610, ${RX + 12} 572 Z" fill="${C.leather}"/>
      <path d="M${RX + 6} 600 C 56 626, 44 750, 86 890" fill="none" stroke="${C.leatherDk}" stroke-width="2" stroke-dasharray="6 5"/>
      <rect x="56" y="922" width="54" height="40" rx="6" fill="none" stroke="#c9ccd1" stroke-width="7" transform="rotate(-12 83 942)"/><path d="M84 920 L80 966" stroke="#c9ccd1" stroke-width="5" transform="rotate(-12 83 942)"/>
      ${[980, 1010, 1040].map(yy => `<circle cx="${96 - (yy - 960) * .12}" cy="${yy}" r="4" fill="${C.leatherDk}"/>`).join('')}</g>`);
    // the roll: leather-bound waxed canvas
    o.push(`<g filter="url(#soft)"><rect x="${RX - 8}" y="${RY - 8}" width="${RW + 16}" height="${RH + 16}" rx="16" fill="${C.leather}"/></g>`);
    o.push(`<rect x="${RX - 8}" y="${RY - 8}" width="${RW + 16}" height="${RH + 16}" rx="16" fill="none" stroke="${C.leatherDk}" stroke-width="2" stroke-dasharray="7 6" transform="translate(0 0)" opacity=".9"/>`);
    o.push(canvasRect(RX, RY, RW, RH, C.canvas, 10));
    // flap crease
    o.push(`<rect x="${RX}" y="${FOLD - 6}" width="${RW}" height="12" fill="#163276" opacity=".55"/><path d="M${RX + 10} ${FOLD + 12} H${RX + RW - 10}" stroke="${C.bone}" stroke-width="1.8" stroke-dasharray="8 6" opacity=".55"/>`);

    /* ---- flap: the conversation, Theo's note, who's collecting ---- */
    const D = 'font-family="' + FONT_W + '"';
    const pl = (y, txt, sz = 30) => `<text x="${RX + 46}" y="${y}" font-family="${HAND}" font-size="${sz}" fill="#ffffff">${esc(txt)}</text>`;
    const bl = (y, txt, sz = 29, fill = C.bone) => `${icon.bell(RX + 58, y - sz * .32, 1.05, C.bone)}<text x="${RX + 82}" y="${y}" ${D} font-size="${sz}" fill="${fill}">${esc(txt)}</text>`;
    o.push(pl(RY + 54, S.priya));
    o.push(bl(RY + 98, S.barnaby));
    o.push(pl(RY + 146, S.priya2));
    o.push(`${icon.bell(RX + 58, RY + 210, 1.5, C.bone)}<text x="${RX + 84}" y="${RY + 224}" ${D} font-size="46" font-weight="700" fill="${C.bone}" letter-spacing="-.3">Your jobs, the parts they need,</text>
      <text x="${RX + 84}" y="${RY + 272}" ${D} font-size="46" font-weight="700" fill="${C.bone}" letter-spacing="-.3">who’s collecting what.</text>`);
    // Theo's note: a woven maker's label sewn on the flap (quoted from his README)
    const LX = 1010, LY = RY + 70;
    o.push(`<text x="${LX}" y="${LY - 16}" ${D} font-size="24" fill="${C.bone}">And Theo left you a note:</text>`);
    o.push(`<g filter="url(#softsm)"><rect x="${LX}" y="${LY}" width="420" height="150" rx="3" fill="#f6f3ec"/></g><rect x="${LX}" y="${LY}" width="420" height="150" rx="3" fill="#f6f3ec" filter="url(#weave)" opacity=".35"/>
      <path d="M${LX + 4} ${LY + 4} h412 M${LX + 4} ${LY + 146} h412" stroke="#c9c2b4" stroke-width="1.2"/>
      ${stitchRect(LX + 8, LY + 8, 404, 134, C.canvas, '5 4', 1.6, 2)}
      <text x="${LX + 28}" y="${LY + 58}" font-family="${FONT}" font-weight="700" font-size="34" fill="${C.ink}">Never trust the stock count</text>
      <text x="${LX + 28}" y="${LY + 96}" font-family="${FONT}" font-weight="700" font-size="34" fill="${C.ink}">on a Friday.</text>
      <text x="${LX + 28}" y="${LY + 128}" font-family="${FONT}" font-size="20" fill="#4a4d55">Theo, in his README for whoever looks after it next</text>`);
    // who's collecting what (counter thread: collection happens at the counter)
    const ready = (window.SHOP ? window.SHOP.jobs.filter(j => j.status === 'ready') : []);
    const CX = 1474, CY = RY + 30, CW = RX + RW - CX - 24;
    o.push(stitchRect(CX, CY, CW, 252, THREAD.counter, '9 6', 2.4, 8));
    o.push(`<text x="${CX + 22}" y="${CY + 40}" font-family="${FONT}" font-weight="700" font-size="28" fill="${THREAD.counter}">Ready to collect</text>`);
    ready.forEach((j, i) => o.push(`<text x="${CX + 22}" y="${CY + 82 + i * 42}" ${D} font-size="21" fill="${C.bone}"><tspan font-weight="700">${esc(j.customer)}</tspan><tspan fill="${C.boneDim}">  ${esc(j.bike)}</tspan></text>`));

    /* ---- pockets, by room ---- */
    const order = B.groups.map(g => g.id), byG = {};
    st.forEach(a => (byG[a.group] = byG[a.group] || []).push(a));
    const IX = RX + 26, IW = RW - 52, GAP = 22, PW = (IW - GAP * (order.length - 1)) / 24;
    let x = IX; const pos = {};
    order.forEach(g => {
      const list = byG[g], gw = PW * list.length, col = THREAD[g], name = B.groups.find(q => q.id === g).name;
      o.push(stitchRect(x - 6, FOLD + 22, gw + 12, PB - FOLD - 16, col, '10 7', 2.6, 8));
      o.push(`<text x="${x + 6}" y="${FOLD + 58}" font-family="${FONT}" font-weight="700" font-size="${gw < 150 ? 23 : 26}" fill="${col}">${esc(gw < 150 ? name.replace('The back ', 'Back ') : name)}</text>`);
      list.forEach(a => { o.push(pocket(a, x, PW, MOUTH, PB - 14, col)); pos[a.tool] = x + PW / 2; x += PW; });
      x += GAP;
    });
    // the hand-back passage: a drawstring along the hems, dipping into the three pockets it ties together
    const hy = MOUTH + 4, tied = ['notify', 'job_detail', 'update_status'].map(t => pos[t]);
    const xa = Math.min(...tied) - 14, xb = Math.max(...tied) + 22;
    let d = `M${xa} ${hy}`; [...tied].sort((a, b) => a - b).forEach(t => { d += ` L${t - 12} ${hy} C ${t - 10} ${hy + 30}, ${t + 10} ${hy + 30}, ${t + 12} ${hy}`; }); d += ` L${xb} ${hy}`;
    o.push(`<path d="${d}" fill="none" stroke="#06080d" stroke-width="8" opacity=".4" transform="translate(0 3)"/><path d="${d}" fill="none" stroke="${C.bone}" stroke-width="5.5" stroke-linecap="round"/><path d="${d}" fill="none" stroke="#2a2c31" stroke-width="5.5" stroke-dasharray="2.5 7"/>`);
    o.push(`<g filter="url(#softsm)"><rect x="${xb - 2}" y="${hy - 11}" width="16" height="22" rx="5" fill="#2a2c31"/><circle cx="${xb + 6}" cy="${hy}" r="3" fill="${C.bone}"/><path d="M${xb + 14} ${hy} q14 4 10 22" fill="none" stroke="${C.bone}" stroke-width="5" stroke-linecap="round"/></g>`);

    /* ---- one ruled scale along the bottom: her week, 30 hours (raise: oscilloscope) ---- */
    const TX = RX + 26, TY = PB + 8, TW = 1250, TH = RY + RH - TY - 14, hx = hh => TX + 40 + hh * ((TW - 80) / 30);
    o.push(`<g filter="url(#softsm)"><rect x="${TX}" y="${TY}" width="${TW}" height="${TH}" rx="6" fill="${C.webbing}"/></g><rect x="${TX}" y="${TY}" width="${TW}" height="${TH}" rx="6" fill="#fff" filter="url(#weave)" opacity=".06"/>`);
    const rulerY = TY + TH - 34;
    for (let i = 0; i <= 60; i++) { const hh = i / 2, X = hx(hh), big = hh % 5 === 0, mid = Number.isInteger(hh);
      o.push(`<path d="M${X} ${rulerY} v${big ? -16 : mid ? -10 : -6}" stroke="${C.bone}" stroke-width="${big ? 2.2 : 1.4}"/>`);
      if (big) o.push(`<text x="${X}" y="${rulerY + 22}" text-anchor="middle" font-family="${FONT}" font-size="19" fill="${C.bone}">${hh}${hh === 30 ? ' h' : ''}</text>`); }
    // her two jobs as segments on the scale
    const segs = [[0, 6, S.bench[0]], [6, 11.5, S.bench[1]]];
    segs.forEach(([a, b, j], i) => {
      o.push(`<rect x="${hx(a) + 1}" y="${rulerY - 34}" width="${hx(b) - hx(a) - 2}" height="14" rx="3" fill="${i ? THREAD.workshop : C.bone}"/>`);
    });
    o.push(`<text x="${hx(11.5) + 12}" y="${rulerY - 21}" font-family="${FONT}" font-size="19" fill="${C.bone}">11½ of your 30 hours booked</text>`);
    const j1 = S.bench[0], j2 = S.bench[1], r1 = TY + 32, r2 = TY + 68, X0 = hx(0);
    o.push(`<rect x="${X0}" y="${r1 - 17}" width="14" height="14" rx="3" fill="${C.bone}"/><text id="r1a" x="${X0 + 24}" y="${r1}" ${D} font-size="21" fill="${C.bone}"><tspan font-weight="700">${j1.job} ${esc(j1.who)}</tspan>  ${esc(j1.bike)}, front, 32 hole  \u00b7  6 h  \u00b7  <tspan font-weight="700">due today</tspan></text>`);
    o.push(`<g data-ref="r1a" data-dx="26" data-y="${r1}">${icon.tick(8, -7, 1.0)}<text x="22" y="0" ${D} font-size="21" fill="${C.bone}">spokes and rim on the shelf</text></g>`);
    o.push(`<rect x="${X0}" y="${r2 - 17}" width="14" height="14" rx="3" fill="${THREAD.workshop}"/><text id="r2a" x="${X0 + 24}" y="${r2}" ${D} font-size="21" fill="${C.bone}"><tspan font-weight="700">${j2.job} ${esc(j2.who)}</tspan>  ${esc(j2.bike)}, rear, 32 hole  \u00b7  5\u00bd h  \u00b7  <tspan font-weight="700">due Wednesday</tspan></text>`);
    o.push(`<g data-ref="r2a" data-dx="26" data-y="${r2}">${icon.warn(10, -7, 1.15)}<text x="26" y="0" ${D} font-size="21" font-weight="700" fill="${C.red}">Spokes short: 40 on the shelf, 64 for both</text></g>`);
    // legend: state by shape, never colour alone
    const GX = TX + TW + 24, GY = TY - 2, LH = 29.5;
    const smudgeIc = `<ellipse cx="${GX + 16}" cy="${GY + 22}" rx="13" ry="8" fill="#04060b" opacity=".8" filter="url(#smudge)"/>`;
    const cordIc = `<path d="M${GX + 2} ${GY + 22} h8 c2 9 10 9 12 0 h8" fill="none" stroke="${C.bone}" stroke-width="4" stroke-linecap="round"/>`;
    const leg = [
      [`<g transform="translate(${GX + 16} ${GY + 42}) scale(.2)">${tool('torque', false)}</g>`, `In its pocket: I can do it (${n.lit})`],
      [`${icon.key(GX + 16, GY + 22, 1)}`, `Outline and a key: ask Martin first (${n.key})`],
      [`${icon.shut(GX + 16, GY + 22, 1)}`, `Sewn shut: never (${n.shut})`],
      [`${icon.star(GX + 16, GY + 22, 1, THREAD.office)}`, `Bright thread: added yesterday`],
      [cordIc, `Drawstring: \u201cHand it back\u201d, three in one pull`],
      [smudgeIc, `Grease marks: what I used this morning`],
    ];
    leg.forEach(([ic, t], i) => o.push(`<g transform="translate(0 ${i * LH})">${ic}<text x="${GX + 40}" y="${GY + 29}" ${D} font-size="19" fill="${C.bone}">${esc(t)}</text></g>`));
    o.push('</svg>');
    return o.join('');
  }

  /* ================= PANEL: the Build lands, two jobs arrive (Mon 23 Nov 2026, 15:05-15:08) ================= */
  function panel(w, h) {
    const S = W.story.build, P = W.story.priyaTuesday, o = [];
    o.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${defs()}`);
    o.push(bench(w, h));
    const RX = 26, RY = 26, RW = w - 52, RH = h - 52;
    o.push(`<g filter="url(#soft)"><rect x="${RX - 7}" y="${RY - 7}" width="${RW + 14}" height="${RH + 14}" rx="14" fill="${C.leather}"/></g>`);
    o.push(canvasRect(RX, RY, RW, RH, C.canvas, 10));
    const D = 'font-family="' + FONT_W + '"';
    // the back office section of her roll: the new pocket being stitched in right now
    const col = THREAD.office, SX = RX + 24, SY = RY + 24, SW = RW - 48, SH = 330;
    o.push(stitchRect(SX, SY, SW, SH, col, '10 7', 2.6, 8));
    o.push(`<text x="${SX + 18}" y="${SY + 40}" font-family="${FONT}" font-weight="700" font-size="28" fill="${col}">The back office</text>`);
    const mouth = SY + 228, pw = 86, px = SX + 30, pb = SY + SH - 18;
    o.push(`<clipPath id="pk"><rect x="${SX}" y="${SY}" width="${SW}" height="${pb - SY - 2}"/></clipPath>`);
    o.push(`<g clip-path="url(#pk)"><g transform="translate(${px + pw / 2} ${mouth})" opacity=".9">${tool('mirror', true)}</g></g>`);
    o.push(canvasRect(px + 2, mouth, pw - 4, pb - mouth, C.pocket, 4) + `<rect x="${px + 2}" y="${mouth}" width="${pw - 4}" height="9" fill="${C.pocketHem}"/>` + icon.key(px + pw / 2 + 2, mouth + 46, 1.2));
    const nx = px + pw + 22;
    o.push(`<g clip-path="url(#pk)"><g transform="translate(${nx + pw / 2} ${mouth - 8})" filter="url(#softsm)">${tool('torque', false)}</g></g>`);
    o.push(canvasRect(nx + 2, mouth, pw - 4, pb - mouth, '#2552b8', 4) + `<rect x="${nx + 2}" y="${mouth}" width="${pw - 4}" height="9" fill="#2b5cc7"/>`);
    // stitching in progress: the left side and half the hem done, the needle still in the canvas
    o.push(`<path d="M${nx + 6} ${pb - 4} V${mouth + 13} H${nx + pw - 34}" fill="none" stroke="${col}" stroke-width="3" stroke-dasharray="7 5"/>`);
    o.push(`<path d="M${nx + pw - 34} ${mouth + 13} C ${nx + pw + 2} ${mouth - 30}, ${nx + pw + 10} ${mouth - 120}, ${nx + pw + 52} ${mouth - 150}" fill="none" stroke="${col}" stroke-width="2.4"/>`);
    o.push(`<g filter="url(#softsm)"><path d="M${nx + pw + 42} ${mouth - 140} L${nx + pw + 108} ${mouth - 186}" stroke="${C.steel}" stroke-width="4.5" stroke-linecap="round"/><path d="M${nx + pw + 98} ${mouth - 182} l7 -4" stroke="${C.canvas}" stroke-width="2.2" stroke-linecap="round"/></g>`);
    o.push(icon.star(nx + pw / 2, mouth + 46, 1.3, col));
    const TXr = nx + pw + 36;
    o.push(`<text x="${TXr}" y="${mouth - 72}" font-family="${FONT}" font-weight="700" font-size="26" fill="${C.bone}">“Who’s got too much on?”</text>
      <text x="${TXr}" y="${mouth - 38}" ${D} font-size="21" fill="${C.bone}">A new pocket, stitched in</text>
      <text x="${TXr}" y="${mouth - 10}" ${D} font-size="21" fill="${C.bone}">at ${S.time}: each mechanic’s</text>
      <text x="${TXr}" y="${mouth + 18}" ${D} font-size="21" fill="${C.bone}">hours this week.</text>
      <text x="${TXr}" y="${mouth + 56}" ${D} font-size="20" fill="${col}">All 22 checks pass, 3 of them new.</text>`);
    // one ruled scale per mechanic: what the new pocket says
    const TX = RX + 24, TW = RW - 48, NAMEW = 180, scaleX = hh => TX + NAMEW + hh * ((TW - NAMEW - 24) / 32);
    const tape = (y, name, sub, booked, cap, after) => {
      const t = [];
      t.push(`<g filter="url(#softsm)"><rect x="${TX}" y="${y}" width="${TW}" height="78" rx="6" fill="${C.webbing}"/></g>`);
      t.push(`<text x="${TX + 16}" y="${y + 33}" font-family="${FONT}" font-weight="700" font-size="26" fill="${C.bone}">${name}</text><text x="${TX + 16}" y="${y + 60}" ${D} font-size="19" fill="${C.bone}">${sub}</text>`);
      for (let hh = 0; hh <= 32; hh++) { const X = scaleX(hh), big = hh % 10 === 0; t.push(`<path d="M${X} ${y + 68} v${big ? -12 : hh % 5 === 0 ? -8 : -5}" stroke="${C.bone}" stroke-width="${big ? 2 : 1.2}" opacity=".85"/>`); }
      t.push(`<path d="M${scaleX(cap)} ${y + 8} v62" stroke="${C.bone}" stroke-width="3"/>`);
      const fade = after != null ? .28 : 1;
      if (booked > 0) {
        t.push(`<rect x="${scaleX(0)}" y="${y + 22}" width="${scaleX(Math.min(booked, cap)) - scaleX(0)}" height="22" rx="3" fill="${C.bone}" opacity="${fade}"/>`);
        if (booked > cap) t.push(`<g opacity="${after != null ? .5 : 1}"><rect x="${scaleX(cap)}" y="${y + 22}" width="${scaleX(booked) - scaleX(cap)}" height="22" fill="url(#hatch)"/><rect x="${scaleX(cap)}" y="${y + 22}" width="${scaleX(booked) - scaleX(cap)}" height="22" fill="none" stroke="${C.bone}" stroke-width="2"/></g>`);
      }
      if (after != null) t.push(`<rect x="${scaleX(0)}" y="${y + 22}" width="${scaleX(after) - scaleX(0)}" height="22" rx="3" fill="${C.bone}"/>`);
      return t.join('');
    };
    let y = SY + SH + 44;
    o.push(`<text x="${TX}" y="${y}" ${D} font-size="22" fill="${C.bone}">This week, Monday to Saturday</text>`);
    y += 18;
    const yDev = y;
    o.push(tape(y, 'Dev', '31 → 19½ of 20 h', 31, 20, 19.5));
    y += 90; o.push(tape(y, 'Ravi', '22 of 30 h', 22, 30));
    y += 90; const yPri = y;
    o.push(tape(y, 'Priya', '0 → 11½ of 30 h', 0, 30));
    o.push(`<rect x="${scaleX(0)}" y="${y + 22}" width="${scaleX(6) - scaleX(0) - 1}" height="22" rx="3" fill="${C.bone}"/><rect x="${scaleX(6) + 1}" y="${y + 22}" width="${scaleX(11.5) - scaleX(6) - 1}" height="22" rx="3" fill="${THREAD.workshop}"/>`);
    // the two wheel builds travel from Dev's overflow to Priya's tape
    const fx = scaleX(25), tx = scaleX(8.5);
    o.push(`<path d="M${fx} ${yDev + 50} C ${scaleX(33)} ${yDev + 140}, ${scaleX(20)} ${yPri - 26}, ${tx} ${yPri + 16}" fill="none" stroke="${C.bone}" stroke-width="3" stroke-dasharray="2 7" stroke-linecap="round"/>
      <path d="M${tx} ${yPri + 16} l1 -17 M${tx} ${yPri + 16} l15 -8" stroke="${C.bone}" stroke-width="3" stroke-linecap="round"/>`);
    y += 126;
    const job = (yy, j, swatch, side, hrs, warn) => `<rect x="${TX}" y="${yy - 18}" width="17" height="17" rx="3" fill="${swatch}"/>
      <text x="${TX + 30}" y="${yy}" font-family="${FONT}" font-weight="700" font-size="27" fill="${C.bone}">${j.job} ${esc(j.who)}</text>
      <text x="${TX + 30}" y="${yy + 31}" ${D} font-size="21" fill="${C.bone}">${esc(j.bike)}, ${side} wheel, 32 hole</text>
      <text x="${TX + 30}" y="${yy + 60}" ${D} font-size="21" fill="${C.bone}">${hrs} h · due ${esc(j.dueDate)}</text>
      ${warn ? `${icon.warn(TX + 41, yy + 89, 1.1)}<text x="${TX + 58}" y="${yy + 96}" ${D} font-size="21" font-weight="700" fill="${C.red}">Spokes short: 40 on the shelf, 64 for both</text>`
             : `${icon.tick(TX + 40, yy + 89, 1.0)}<text x="${TX + 56}" y="${yy + 96}" ${D} font-size="21" fill="${C.bone}">Spokes and rim on the shelf</text>`}`;
    o.push(job(y, P.bench[0], C.bone, 'front', '6'));
    o.push(job(y + 136, P.bench[1], THREAD.workshop, 'rear', '5½', true));
    o.push(`<text x="${TX}" y="${RY + RH - 26}" ${D} font-size="20" fill="${C.bone}">Moved to you from Dev at 15:08, with Martin’s say-so.</text>`);
    o.push('</svg>');
    return o.join('');
  }

  window.PRIYA_ROLL = {
    render(el, { moment = 'priyaTuesday', w = 1920, h = 1080 } = {}) {
      el.innerHTML = moment === 'build' ? panel(w, h) : hero(w, h);
      const place = () => el.querySelectorAll('[data-ref]').forEach(g => { const r = el.querySelector('#' + g.dataset.ref).getBBox();
        g.setAttribute('transform', `translate(${r.x + r.width + +g.dataset.dx} ${+g.dataset.y})`); });
      place(); if (document.fonts) document.fonts.ready.then(place);
    },
    tool, icon, THREAD, C,
  };
})();
