/* Shop PC: original icon glyphs (SVG strings). Nothing here is traced from or modelled on a real product's artwork.
 * Every function returns an <svg> string; `s` is the rendered size in (logical) px.
 * Gradient ids are made unique per call so many icons can live in one document. */
(function (G) {
  let _n = 0;
  const uid = p => `${p}${++_n}`;

  /** A chainring/sprocket outline as a path: n teeth between radius r0 (root) and r1 (tip). */
  function gearPath(cx, cy, n, r0, r1, tip = .42, base = .62) {
    const pts = [];
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2 - Math.PI / 2, step = Math.PI * 2 / n;
      const b0 = a - step * base / 2, b1 = a + step * base / 2, t0 = a - step * tip / 2, t1 = a + step * tip / 2;
      pts.push([b0, r0], [t0, r1], [t1, r1], [b1, r0]);
    }
    return 'M' + pts.map(([a, r]) => `${(cx + r * Math.cos(a)).toFixed(2)},${(cy + r * Math.sin(a)).toFixed(2)}`).join('L') + 'Z';
  }
  const circ = (cx, cy, r) => `M${cx - r},${cy}a${r},${r} 0 1,0 ${2 * r},0a${r},${r} 0 1,0 ${-2 * r},0Z`;

  /** Spider arms of a chainring: k arms joining the hub (rh) to the inner ring (ri). */
  function spider(cx, cy, k, rh, ri, w) {
    let d = '';
    for (let i = 0; i < k; i++) {
      const a = (i / k) * Math.PI * 2 - Math.PI / 2, ca = Math.cos(a), sa = Math.sin(a), px = -sa * w / 2, py = ca * w / 2;
      const x0 = cx + ca * rh * .6, y0 = cy + sa * rh * .6, x1 = cx + ca * (ri + 1), y1 = cy + sa * (ri + 1);
      d += `M${(x0 + px).toFixed(2)},${(y0 + py).toFixed(2)}L${(x1 + px * 1.5).toFixed(2)},${(y1 + py * 1.5).toFixed(2)}L${(x1 - px * 1.5).toFixed(2)},${(y1 - py * 1.5).toFixed(2)}L${(x0 - px).toFixed(2)},${(y0 - py).toFixed(2)}Z`;
    }
    return d;
  }

  /** The shop's sprocket: brushed-steel chainring with five spider arms. Used for the shortcut, favicon, tray. */
  function sprocket(s = 48, o = {}) {
    const g = uid('sp'), h = uid('sph');
    const { teeth = 16, steel = ['#ffffff', '#c9d1d9', '#8b96a3', '#dfe5eb'], stroke = '#2d3a48' } = o;
    const C = 24, R1 = 22.5, R0 = 19.2, RI = 13.4;
    return `<svg width="${s}" height="${s}" viewBox="0 0 48 48"><defs>
      <linearGradient id="${g}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${steel[0]}"/><stop offset=".45" stop-color="${steel[1]}"/><stop offset=".7" stop-color="${steel[2]}"/><stop offset="1" stop-color="${steel[3]}"/></linearGradient>
      <radialGradient id="${h}" cx=".5" cy=".42" r=".6"><stop offset="0" stop-color="#4a6c93"/><stop offset="1" stop-color="#1b2c42"/></radialGradient></defs>
      <path d="${gearPath(C, C, teeth, R0, R1)} ${circ(C, C, RI)}" fill="url(#${g})" fill-rule="evenodd" stroke="${stroke}" stroke-width=".9" stroke-linejoin="round"/>
      <circle cx="${C}" cy="${C}" r="${RI}" fill="url(#${h})" opacity=".92"/>
      <path d="${spider(C, C, 5, 6, RI, 3.6)}" fill="url(#${g})" stroke="${stroke}" stroke-width=".7"/>
      <circle cx="${C}" cy="${C}" r="5.6" fill="url(#${g})" stroke="${stroke}" stroke-width=".8"/>
      <circle cx="${C}" cy="${C}" r="2.2" fill="#2d3a48"/>
      ${[0, 1, 2, 3, 4].map(i => { const a = i / 5 * Math.PI * 2 - Math.PI / 2; return `<circle cx="${(C + Math.cos(a) * (RI - 1.6)).toFixed(2)}" cy="${(C + Math.sin(a) * (RI - 1.6)).toFixed(2)}" r="1.1" fill="#3b4652"/>`; }).join('')}
      <path d="M8.5 17 A17 17 0 0 1 22 6.6" fill="none" stroke="#fff" stroke-opacity=".85" stroke-width="1.3" stroke-linecap="round"/></svg>`;
  }

  /** The little curved-arrow badge on a shortcut icon (bottom-left). */
  const shortcutBadge = (s = 48) => `<svg width="${s}" height="${s}" viewBox="0 0 48 48" style="position:absolute;left:0;top:0"><rect x="1.5" y="31.5" width="15" height="15" rx="1.5" fill="#fff" stroke="#6d7b8a"/><path d="M5.5 43 C5.5 37 8 35.2 13 35.2 L13 33 L15.6 36.6 L13 40.2 L13 38 C9.5 38 7.6 39.4 5.5 43Z" fill="#1d63c9" stroke="#0d3f86" stroke-width=".5"/></svg>`;

  /** A manila folder with papers peeking out. tint: 'manila' | 'plain' */
  function folder(s = 48, o = {}) {
    const a = uid('fa'), b = uid('fb'), { papers = 2, label = '' } = o;
    return `<svg width="${s}" height="${s}" viewBox="0 0 48 48"><defs>
      <linearGradient id="${a}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f3d98b"/><stop offset="1" stop-color="#d9b45a"/></linearGradient>
      <linearGradient id="${b}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fde9a6"/><stop offset=".5" stop-color="#f5d57a"/><stop offset="1" stop-color="#e2b955"/></linearGradient></defs>
      <path d="M3 10.5 h14 l3.5 3.5 h23 a1.5 1.5 0 0 1 1.5 1.5 v24 a1.5 1.5 0 0 1 -1.5 1.5 h-39 a1.5 1.5 0 0 1 -1.5 -1.5 v-27.5 a1.5 1.5 0 0 1 1.5 -1.5z" fill="url(#${a})" stroke="#a47e2a" stroke-width=".8"/>
      ${papers > 0 ? `<rect x="8" y="12" width="31" height="20" fill="#fff" stroke="#b9b9b9" stroke-width=".6" transform="rotate(-3 23 22)"/>` : ''}
      ${papers > 1 ? `<rect x="10" y="10.5" width="30" height="20" fill="#f7f7f7" stroke="#b9b9b9" stroke-width=".6" transform="rotate(4 25 20)"/><path d="M14 15h18M14 18h20M14 21h14" stroke="#9fb3cc" stroke-width="1" transform="rotate(4 25 20)"/>` : ''}
      <path d="M2.2 20.5 a1.5 1.5 0 0 1 1.5 -1.6 h40.6 a1.5 1.5 0 0 1 1.5 1.7 l-2.1 19.4 a1.5 1.5 0 0 1 -1.5 1.3 h-37 a1.5 1.5 0 0 1 -1.5 -1.3z" fill="url(#${b})" stroke="#a47e2a" stroke-width=".8"/>
      <path d="M4 20.6 h40" stroke="#fff6cf" stroke-width="1"/>
      ${label ? `<text x="24" y="35" text-anchor="middle" font-family="Segoe UI" font-size="7" font-weight="700" fill="#8a6418" opacity=".75">${label}</text>` : ''}</svg>`;
  }

  /** Recycle bin look-alike: frosted glass basket with crumpled paper inside (full). */
  function bin(s = 48) {
    const a = uid('ba'), b = uid('bb'), c = uid('bc');
    return `<svg width="${s}" height="${s}" viewBox="0 0 48 48"><defs>
      <linearGradient id="${a}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#bcd3e8" stop-opacity=".85"/><stop offset=".35" stop-color="#f4f9ff" stop-opacity=".9"/><stop offset=".7" stop-color="#a9c2da" stop-opacity=".8"/><stop offset="1" stop-color="#7f9cb9" stop-opacity=".9"/></linearGradient>
      <linearGradient id="${b}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8f1fa"/><stop offset="1" stop-color="#9db4cb"/></linearGradient>
      <pattern id="${c}" width="3" height="3" patternUnits="userSpaceOnUse"><path d="M0 0L3 3M3 0L0 3" stroke="#5d7894" stroke-width=".35" opacity=".55"/></pattern></defs>
      <path d="M13 10 l3 -4 l5 3 l4 -4 l4 4 l5 -2 l2 5z" fill="#fff" stroke="#9aa6b2" stroke-width=".6"/>
      <path d="M19 8 l5 -3 l3 3 l-4 2z" fill="#f4f0d8" stroke="#a9a48a" stroke-width=".5"/>
      <path d="M8 10 h32 l-4 33 a2 2 0 0 1 -2 1.8 h-20 a2 2 0 0 1 -2 -1.8z" fill="url(#${a})" stroke="#4d6782" stroke-width=".9"/>
      <path d="M8 10 h32 l-4 33 a2 2 0 0 1 -2 1.8 h-20 a2 2 0 0 1 -2 -1.8z" fill="url(#${c})"/>
      <ellipse cx="24" cy="10" rx="16" ry="2.6" fill="url(#${b})" stroke="#4d6782" stroke-width=".9"/>
      <ellipse cx="24" cy="10.2" rx="13.6" ry="1.6" fill="#4b6077" opacity=".55"/>
      <path d="M12 13 l3.2 28" stroke="#fff" stroke-width="1.6" stroke-opacity=".8" stroke-linecap="round"/>
      <path d="M11 42.5 h26" stroke="#3a536d" stroke-width="1" opacity=".5"/></svg>`;
  }

  /** A document: kind 'txt' (lined paper), 'sheet' (green grid), 'bat' (gears). */
  function doc(s = 48, kind = 'txt') {
    const a = uid('da');
    const body = {
      txt: `<path d="M14 15h18M14 19h20M14 23h16M14 27h19M14 31h12M14 35h17" stroke="#6f86a6" stroke-width="1.1"/>`,
      sheet: `<rect x="12" y="15" width="22" height="22" fill="#fff" stroke="#3f8f45" stroke-width=".8"/>
        <path d="M12 20.5h22M12 26h22M12 31.5h22M19.3 15v22M26.6 15v22" stroke="#7cb67f" stroke-width=".8"/>
        <rect x="12" y="15" width="22" height="5.5" fill="#4ea957" opacity=".85"/>
        <rect x="26.6" y="26" width="7.4" height="5.5" fill="#ffe36a"/>`,
      bat: `<rect x="12" y="14" width="23" height="17" rx="1" fill="#1e2b38"/><path d="M14.5 18l3 2.5-3 2.5M19 24h5" stroke="#d8e6f2" stroke-width="1.3" fill="none"/>
        <circle cx="29" cy="33" r="5.5" fill="#9aa5b1" stroke="#4f5b67" stroke-width=".8"/><circle cx="29" cy="33" r="2" fill="#4f5b67"/>`,
    }[kind];
    return `<svg width="${s}" height="${s}" viewBox="0 0 48 48"><defs><linearGradient id="${a}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#e4eaf1"/></linearGradient></defs>
      <path d="M9 4 h22 l8 8 v31 a1 1 0 0 1 -1 1 h-29 a1 1 0 0 1 -1 -1 v-38 a1 1 0 0 1 1 -1z" fill="url(#${a})" stroke="#8695a6" stroke-width=".9"/>
      <path d="M31 4 v7 a1 1 0 0 0 1 1 h7" fill="#dfe6ee" stroke="#8695a6" stroke-width=".9"/>${body}</svg>`;
  }

  /** The browser: a glossy blue globe with a silver compass needle (original). */
  function globe(s = 32) {
    const a = uid('ga'), b = uid('gb');
    return `<svg width="${s}" height="${s}" viewBox="0 0 32 32"><defs>
      <radialGradient id="${a}" cx=".38" cy=".32" r=".75"><stop offset="0" stop-color="#9fe0ff"/><stop offset=".45" stop-color="#2d8fe0"/><stop offset="1" stop-color="#0b3f8f"/></radialGradient>
      <linearGradient id="${b}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
      <circle cx="16" cy="16" r="13.5" fill="url(#${a})" stroke="#0a3470" stroke-width=".8"/>
      <path d="M8 11c3 1 4 4 7 3s2-4 5-3 2 3 4 2M6 18c3-1 5 2 7 4s1 5 4 5M20 20c2 0 3 2 5 1" fill="none" stroke="#7fe08a" stroke-width="1.6" stroke-linecap="round" opacity=".9"/>
      <ellipse cx="16" cy="16" rx="6" ry="13.5" fill="none" stroke="#cdeeff" stroke-width=".6" opacity=".7"/>
      <path d="M2.5 16h27M4.5 9.5h23M4.5 22.5h23" stroke="#cdeeff" stroke-width=".6" opacity=".6"/>
      <ellipse cx="14" cy="9" rx="9" ry="5.6" fill="url(#${b})"/>
      <path d="M22 4 l2.8 9.5 l-2.3 0.8z" fill="#e9eef3" stroke="#56636f" stroke-width=".5"/><path d="M22 4 l0.5 10.3 l-2.3 0.8z" fill="#e2483d" stroke="#7d1e18" stroke-width=".5"/></svg>`;
  }

  /** Mail: an envelope with a glossy flap. */
  function mail(s = 32) {
    const a = uid('ma');
    return `<svg width="${s}" height="${s}" viewBox="0 0 32 32"><defs><linearGradient id="${a}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#d5dde8"/></linearGradient></defs>
      <rect x="3" y="8" width="26" height="18" rx="1.6" fill="url(#${a})" stroke="#5a6f8a" stroke-width=".9"/>
      <path d="M3.6 9 L16 18.5 L28.4 9" fill="none" stroke="#5a6f8a" stroke-width=".9"/><path d="M3.6 25.4 L12.6 16.2M28.4 25.4 L19.4 16.2" stroke="#8ea0b6" stroke-width=".8"/>
      <circle cx="25" cy="9" r="4.6" fill="#f0a020" stroke="#9a5d00" stroke-width=".7"/><path d="M25 6.6v3M25 11.2v.4" stroke="#fff" stroke-width="1.4" stroke-linecap="round"/></svg>`;
  }

  /** Spreadsheet application (green). */
  function sheetApp(s = 32) {
    const a = uid('sa');
    return `<svg width="${s}" height="${s}" viewBox="0 0 32 32"><defs><linearGradient id="${a}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6ccf73"/><stop offset="1" stop-color="#23862d"/></linearGradient></defs>
      <rect x="4" y="4" width="24" height="24" rx="3" fill="url(#${a})" stroke="#145a1b" stroke-width=".8"/>
      <rect x="8" y="9" width="16" height="14" fill="#fff"/><path d="M8 13.7h16M8 18.3h16M13.3 9v14M18.6 9v14" stroke="#5fae64" stroke-width=".8"/>
      <path d="M4.5 13 C10 9 22 8 27.5 9 V7 a2.6 2.6 0 0 0 -2.6 -2.6 H7 A2.6 2.6 0 0 0 4.5 7z" fill="#fff" opacity=".28"/></svg>`;
  }

  /** Media player: an orange disc with a play triangle. */
  function media(s = 32) {
    const a = uid('me');
    return `<svg width="${s}" height="${s}" viewBox="0 0 32 32"><defs><radialGradient id="${a}" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#ffd27a"/><stop offset=".6" stop-color="#f08a12"/><stop offset="1" stop-color="#a14d00"/></radialGradient></defs>
      <circle cx="16" cy="16" r="13" fill="url(#${a})" stroke="#7a3a00" stroke-width=".8"/><path d="M13 10.5 L22 16 L13 21.5z" fill="#fff"/>
      <ellipse cx="15" cy="9.5" rx="8" ry="4.5" fill="#fff" opacity=".35"/></svg>`;
  }

  /** Card game: two fanned playing cards. */
  function cards(s = 32) {
    return `<svg width="${s}" height="${s}" viewBox="0 0 32 32"><rect x="5" y="6" width="15" height="21" rx="1.6" fill="#fff" stroke="#5b6571" stroke-width=".8" transform="rotate(-12 12 16)"/>
      <rect x="12" y="5" width="15" height="21" rx="1.6" fill="#fff" stroke="#5b6571" stroke-width=".8" transform="rotate(8 19 16)"/>
      <path d="M19.5 10.5c-2.5 2.6-4.6 4.2-4.6 6.1 0 1.5 1.9 2.3 3.6 1 -.3 1.3-.8 2-1.6 2.6h5.2c-.8-.6-1.3-1.3-1.6-2.6 1.7 1.3 3.6.5 3.6-1 0-1.9-2.1-3.5-4.6-6.1z" fill="#1b1b1b" transform="rotate(8 19 16)"/>
      <path d="M8.5 9.2l1.8 2.4-1.8 2.4-1.8-2.4z" fill="#d22" transform="rotate(-12 12 16)"/></svg>`;
  }

  /** Calculator. */
  function calc(s = 32) {
    const a = uid('ca');
    return `<svg width="${s}" height="${s}" viewBox="0 0 32 32"><defs><linearGradient id="${a}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8994a3"/><stop offset="1" stop-color="#3c4552"/></linearGradient></defs>
      <rect x="7" y="3" width="18" height="26" rx="2.5" fill="url(#${a})" stroke="#262d36" stroke-width=".8"/><rect x="9.5" y="6" width="13" height="5.5" rx="1" fill="#c9e7b8" stroke="#2f3a2a" stroke-width=".5"/>
      ${[0, 1, 2].map(r => [0, 1, 2].map(c => `<rect x="${9.5 + c * 4.5}" y="${14 + r * 4.6}" width="3.6" height="3.4" rx=".7" fill="${c === 2 && r === 2 ? '#f08a12' : '#eef1f5'}"/>`).join('')).join('')}</svg>`;
  }

  /** Picture editor (the one Theo made the wallpaper in): a painter's palette with a brush. */
  function palette(s = 32) {
    const a = uid('pl');
    return `<svg width="${s}" height="${s}" viewBox="0 0 32 32"><defs><linearGradient id="${a}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f7e3bf"/><stop offset="1" stop-color="#c99a5b"/></linearGradient></defs>
      <path d="M16 4C8.5 4 3 9 3 15.5 3 21 7 25 12 25c2 0 2.6-1.4 2.2-2.8-.5-1.6.4-2.8 2-2.8h3.4C25 19.4 29 16.4 29 12 29 7.4 23.6 4 16 4z" fill="url(#${a})" stroke="#7a5124" stroke-width=".9"/>
      <circle cx="9.5" cy="14" r="2.3" fill="#e2342a"/><circle cx="12.5" cy="8.8" r="2.3" fill="#f6c21b"/><circle cx="18.8" cy="8" r="2.3" fill="#3fae3a"/><circle cx="23.6" cy="11.6" r="2.3" fill="#2f7fd6"/>
      <path d="M30 20 L19.5 28.5" stroke="#6b4a22" stroke-width="2.4" stroke-linecap="round"/><path d="M20.6 27.6 L17.4 30.4 L16.6 29.6z" fill="#333"/></svg>`;
  }

  /** Disc burner: a CD-R with a rainbow sheen and a flame-orange burn arc. */
  function disc(s = 32) {
    const a = uid('cd');
    return `<svg width="${s}" height="${s}" viewBox="0 0 32 32"><defs><linearGradient id="${a}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e8f4ff"/><stop offset=".3" stop-color="#d6c8ff"/><stop offset=".48" stop-color="#bff3e0"/><stop offset=".62" stop-color="#fff2b8"/><stop offset=".8" stop-color="#c9dcf2"/><stop offset="1" stop-color="#9fb4cc"/></linearGradient></defs>
      <circle cx="16" cy="16" r="13.5" fill="url(#${a})" stroke="#6b7d92" stroke-width=".8"/><circle cx="16" cy="16" r="4.6" fill="#f4f7fa" stroke="#8a9bb0" stroke-width=".7"/><circle cx="16" cy="16" r="1.9" fill="#fff" stroke="#8a9bb0" stroke-width=".6"/>
      <path d="M6.2 12 A10.6 10.6 0 0 1 13 5.8" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" opacity=".9"/>
      <path d="M25.4 21.5 A10.8 10.8 0 0 1 18 26.7" fill="none" stroke="#f07a12" stroke-width="2.2" stroke-linecap="round"/></svg>`;
  }

  /** The spanner: favicon of the 'Parts list' tab ("it's the one with the spanner"). Drawn to read at 16px. */
  function spanner(s = 16) {
    const a = uid('spn');
    return `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><defs><linearGradient id="${a}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f4f7fa"/><stop offset=".5" stop-color="#aab4bf"/><stop offset="1" stop-color="#6c7784"/></linearGradient></defs>
      <path d="M11.6 1.2 A3.6 3.6 0 0 0 8.4 5.9 L1.9 12.4 A1.25 1.25 0 0 0 3.6 14.1 L10.1 7.6 A3.6 3.6 0 0 0 14.8 4.4 L12.6 5.2 L11.1 4.9 L10.8 3.4 L11.6 1.2Z" fill="url(#${a})" stroke="#2f3a46" stroke-width=".85" stroke-linejoin="round"/>
      <circle cx="2.75" cy="13.25" r=".7" fill="#2f3a46"/></svg>`;
  }

  /** An invoice: a receipt with a pound sign. */
  function invoice(s = 16) {
    return `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M3 1.5h10v13l-1.7-1.2-1.6 1.2-1.7-1.2-1.6 1.2-1.7-1.2L3 14.5z" fill="#fff" stroke="#5f6f84" stroke-width=".8" stroke-linejoin="round"/>
      <text x="8" y="10.6" text-anchor="middle" font-family="Georgia, serif" font-weight="700" font-size="8.5" fill="#2a7a3a">&#163;</text></svg>`;
  }

  /** Win7-era busy cursor look-alike: a spinning ring (original: gold-and-blue, not the real artwork). `a` = angle. */
  function busyRing(s = 22, a = 0) {
    const g = uid('br');
    return `<svg width="${s}" height="${s}" viewBox="0 0 22 22"><defs><linearGradient id="${g}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#bff1ff"/><stop offset=".5" stop-color="#2f9fe8"/><stop offset="1" stop-color="#0b4f9c"/></linearGradient></defs>
      <circle cx="11" cy="11" r="8" fill="none" stroke="#0a2a4a" stroke-width="5" opacity=".55"/>
      <g transform="rotate(${a} 11 11)"><circle cx="11" cy="11" r="8" fill="none" stroke="url(#${g})" stroke-width="3.4" stroke-dasharray="30 20.3" stroke-linecap="round"/></g></svg>`;
  }

  /** Photo viewer: a framed landscape. */
  function photo(s = 32) {
    const a = uid('ph');
    return `<svg width="${s}" height="${s}" viewBox="0 0 32 32"><defs><linearGradient id="${a}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6fc3ff"/><stop offset="1" stop-color="#d7f0ff"/></linearGradient></defs>
      <rect x="3" y="6" width="26" height="20" rx="1.5" fill="#fff" stroke="#6b7785" stroke-width=".8"/><rect x="5.5" y="8.5" width="21" height="15" fill="url(#${a})"/>
      <path d="M5.5 23.5 L12 15 L16 19.5 L20 14 L26.5 23.5z" fill="#3f9a3f"/><circle cx="22" cy="11.5" r="2" fill="#ffe36a"/></svg>`;
  }

  /** A friendly bicycle, used as the user tile picture. */
  function bikeTile(s = 48) {
    const a = uid('bt');
    return `<svg width="${s}" height="${s}" viewBox="0 0 48 48"><defs><linearGradient id="${a}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8fd3ff"/><stop offset=".62" stop-color="#d9f1ff"/><stop offset=".62" stop-color="#7cc46a"/><stop offset="1" stop-color="#4f9a42"/></linearGradient></defs>
      <rect width="48" height="48" fill="url(#${a})"/><circle cx="38" cy="10" r="4.5" fill="#ffe680"/>
      <g fill="none" stroke="#c0392b" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><path d="M14 33 L21 22 L33 22 L35 33 M21 22 L25 33 L33 22 M20 19 h4 M33 22 L31.5 17 h4"/></g>
      <g fill="none" stroke="#1f2a33" stroke-width="2"><circle cx="14" cy="33" r="7"/><circle cx="35" cy="33" r="7"/></g>
      <circle cx="25" cy="33" r="1.6" fill="#1f2a33"/></svg>`;
  }

  /** Small 16px-ish glyphs for chrome and tray. Drawn on a 16 grid. */
  const ICO = {
    back: (s = 26) => { const a = uid('bk'); return `<svg width="${s}" height="${s}" viewBox="0 0 26 26"><defs><radialGradient id="${a}" cx=".5" cy=".3" r=".8"><stop offset="0" stop-color="#9cd2ff"/><stop offset=".5" stop-color="#2f7fd6"/><stop offset="1" stop-color="#0d3f8a"/></radialGradient></defs><circle cx="13" cy="13" r="12" fill="url(#${a})" stroke="#0b2f63"/><ellipse cx="13" cy="7.5" rx="8.5" ry="5" fill="#fff" opacity=".35"/><path d="M15.5 7.5 L9.5 13 L15.5 18.5 M9.8 13 H19" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`; },
    fwd: (s = 22) => { const a = uid('fw'); return `<svg width="${s}" height="${s}" viewBox="0 0 26 26"><defs><radialGradient id="${a}" cx=".5" cy=".3" r=".8"><stop offset="0" stop-color="#eef3f8"/><stop offset="1" stop-color="#a9b6c4"/></radialGradient></defs><circle cx="13" cy="13" r="12" fill="url(#${a})" stroke="#7d8a98"/><path d="M10.5 7.5 L16.5 13 L10.5 18.5 M16.2 13 H7" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`; },
    refresh: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M12.5 6.2 A5 5 0 1 0 13 9.5" fill="none" stroke="#2f9a3a" stroke-width="2"/><path d="M10.2 5.6 L14 6.9 L13.6 2.8z" fill="#2f9a3a"/></svg>`,
    stop: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M4 4 L12 12 M12 4 L4 12" stroke="#d63a2c" stroke-width="2.4" stroke-linecap="round"/></svg>`,
    mag: (s = 16, c = '#3a5f8f') => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><circle cx="6.5" cy="6.5" r="4.3" fill="#e8f3ff" stroke="${c}" stroke-width="1.6"/><path d="M9.8 9.8 L14 14" stroke="${c}" stroke-width="2.4" stroke-linecap="round"/></svg>`,
    star: (s = 16, add) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M8 1.2 L10 5.8 L15 6.2 L11.2 9.4 L12.4 14.3 L8 11.7 L3.6 14.3 L4.8 9.4 L1 6.2 L6 5.8z" fill="#ffc928" stroke="#b27b00" stroke-width=".8" stroke-linejoin="round"/>${add ? '<circle cx="12.6" cy="12.6" r="3.2" fill="#3fae3a" stroke="#1d6a1a" stroke-width=".6"/><path d="M12.6 10.8v3.6M10.8 12.6h3.6" stroke="#fff" stroke-width="1.2"/>' : ''}</svg>`,
    home: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M2 8 L8 2.5 L14 8" fill="none" stroke="#9b3b1c" stroke-width="1.6" stroke-linejoin="round"/><path d="M4 7.5 V14 H12 V7.5 L8 4z" fill="#f2e3b8" stroke="#7a5a2a" stroke-width=".8"/><rect x="6.8" y="10" width="2.4" height="4" fill="#9b3b1c"/></svg>`,
    feed: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><rect x="1.5" y="1.5" width="13" height="13" rx="2.5" fill="#f08a12" stroke="#a5560a" stroke-width=".7"/><circle cx="5" cy="11" r="1.4" fill="#fff"/><path d="M4 7.2 A4.8 4.8 0 0 1 8.8 12 M4 4.2 A7.8 7.8 0 0 1 11.8 12" fill="none" stroke="#fff" stroke-width="1.5"/></svg>`,
    print: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><rect x="4" y="1.5" width="8" height="5" fill="#fff" stroke="#6b7785" stroke-width=".8"/><rect x="1.5" y="6" width="13" height="6" rx="1.2" fill="#8b97a5" stroke="#4a5562" stroke-width=".8"/><rect x="4" y="10" width="8" height="4.5" fill="#fff" stroke="#6b7785" stroke-width=".8"/><circle cx="12.3" cy="8" r=".8" fill="#5fe05a"/></svg>`,
    page: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M3 1.5h7l3 3v10H3z" fill="#fff" stroke="#6b7785" stroke-width=".8"/><path d="M5 6h6M5 8.5h6M5 11h4" stroke="#8aa0bc" stroke-width=".9"/></svg>`,
    shield: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M8 1.2 L14 3.4 V7.6 C14 11 11.4 13.6 8 14.9 C4.6 13.6 2 11 2 7.6 V3.4z" fill="#3c9a45" stroke="#1d5a24" stroke-width=".8"/><path d="M5 8 L7.2 10.2 L11.2 5.8" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    tools: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><circle cx="8" cy="8" r="4.6" fill="none" stroke="#5e6a78" stroke-width="2.6" stroke-dasharray="2.2 1.4"/><circle cx="8" cy="8" r="3" fill="#c9d1da" stroke="#5e6a78" stroke-width="1"/></svg>`,
    help: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.6" fill="#2f7fd6" stroke="#174a87" stroke-width=".8"/><text x="8" y="11.6" text-anchor="middle" font-family="Segoe UI" font-weight="700" font-size="10" fill="#fff">?</text></svg>`,
    speaker: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M2 6h3l4-3.5v11L5 10H2z" fill="#e8eef5" stroke="#2c3e52" stroke-width=".7"/><path d="M11 5.5 a3.6 3.6 0 0 1 0 5M12.8 3.6 a6 6 0 0 1 0 8.8" fill="none" stroke="#e8eef5" stroke-width="1.2" stroke-linecap="round"/></svg>`,
    net: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16">${[0, 1, 2, 3, 4].map(i => `<rect x="${1.5 + i * 2.8}" y="${12 - i * 2.2}" width="2" height="${2 + i * 2.2}" fill="#e8eef5" stroke="#2c3e52" stroke-width=".4"/>`).join('')}</svg>`,
    usb: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><rect x="5" y="1.5" width="6" height="6" fill="#c9d1da" stroke="#2c3e52" stroke-width=".6"/><rect x="3.5" y="7" width="9" height="7.5" rx="1" fill="#e8eef5" stroke="#2c3e52" stroke-width=".6"/><path d="M6.5 3.5h1M8.5 3.5h1" stroke="#2c3e52"/><circle cx="12" cy="12.4" r="3" fill="#3fae3a" stroke="#155d12" stroke-width=".5"/><path d="M10.6 12.4l1 1 1.8-2" fill="none" stroke="#fff" stroke-width=".9"/></svg>`,
    upArrow: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M4 10 L8 6 L12 10" fill="none" stroke="#e8eef5" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    warn: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M8 1.2 L15.2 14.2 H0.8z" fill="#ffcf2e" stroke="#9a6a00" stroke-width=".8" stroke-linejoin="round"/><path d="M8 5.5v4.5" stroke="#1b1b1b" stroke-width="1.7" stroke-linecap="round"/><circle cx="8" cy="12.2" r="1" fill="#1b1b1b"/></svg>`,
    dropdown: (s = 8, c = '#2c3e52') => `<svg width="${s}" height="${s}" viewBox="0 0 8 8"><path d="M1 2.5 L4 5.5 L7 2.5z" fill="${c}"/></svg>`,
    lock: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M5 7V5a3 3 0 0 1 6 0v2" fill="none" stroke="#8a6d1a" stroke-width="1.5"/><rect x="3.5" y="7" width="9" height="7" rx="1" fill="#f2c94c" stroke="#8a6d1a" stroke-width=".8"/></svg>`,
    zone: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><rect x="1.5" y="2.5" width="13" height="9" rx="1" fill="#bfe0ff" stroke="#3a5f8f" stroke-width=".8"/><path d="M5 14h6M8 11.5V14" stroke="#3a5f8f" stroke-width="1.2"/></svg>`,
    arrowR: (s = 8, c = '#2c3e52') => `<svg width="${s}" height="${s}" viewBox="0 0 8 8"><path d="M2.5 1 L5.5 4 L2.5 7z" fill="${c}"/></svg>`,
    power: (s = 14) => `<svg width="${s}" height="${s}" viewBox="0 0 14 14"><path d="M4.3 3.6 A4.6 4.6 0 1 0 9.7 3.6" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/><path d="M7 1.5v5" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/></svg>`,
  };

  /** Favicons for the nine tabs (16px). */
  const FAV = {
    shop: (s = 16) => sprocket(s, { teeth: 12 }),
    supplier: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M2 5 L8 2 L14 5 V12 L8 15 L2 12z" fill="#d98a2b" stroke="#7a4610" stroke-width=".8"/><path d="M2 5 L8 8 L14 5 M8 8 V15" fill="none" stroke="#7a4610" stroke-width=".8"/><path d="M5 3.5 L11 6.5" stroke="#f6d49a" stroke-width="1.2"/></svg>`,
    sms: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M2 2.5h12a1 1 0 0 1 1 1v7a1 1 0 0 1 -1 1H7l-3.5 3v-3H2a1 1 0 0 1 -1 -1v-7a1 1 0 0 1 1 -1z" fill="#3fb24a" stroke="#1c6a23" stroke-width=".8"/><path d="M4 6h8M4 8.5h5" stroke="#fff" stroke-width="1.1"/></svg>`,
    xls: (s = 16) => sheetApp(s),
    mail: (s = 16) => mail(s),
    bank: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M1.5 5.5 L8 1.5 L14.5 5.5z" fill="#1f5a8a" stroke="#0e2f4c" stroke-width=".6"/><path d="M3 6.5v6M6 6.5v6M10 6.5v6M13 6.5v6" stroke="#1f5a8a" stroke-width="1.6"/><rect x="1.5" y="12.5" width="13" height="2" fill="#1f5a8a"/></svg>`,
    cal: (s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 16 16"><rect x="1.5" y="2.5" width="13" height="12" rx="1" fill="#fff" stroke="#5a6f8a" stroke-width=".8"/><rect x="1.5" y="2.5" width="13" height="3.5" fill="#d94a3a"/><path d="M4 8.5h2M7 8.5h2M10 8.5h2M4 11h2M7 11h2M10 11h2" stroke="#5a6f8a" stroke-width="1.2"/></svg>`,
    parts: (s = 16) => spanner(s),
    invoices: (s = 16) => invoice(s),
    blank: (s = 16) => ICO.page(s),
  };

  G.ICONS = { uid, gearPath, circ, spider, sprocket, shortcutBadge, folder, bin, doc, globe, mail, sheetApp, media, cards, calc, palette, disc, spanner, invoice, busyRing, photo, bikeTile, ICO, FAV };
})(window);
