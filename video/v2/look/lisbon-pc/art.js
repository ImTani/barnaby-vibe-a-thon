/* Lisbon desk: small original artworks and icons, all SVG strings, all deterministic (seeded).
 *   LXArt.bike(w)            Theo's line-drawn bike (his fetch "logo": no distro logo anywhere)
 *   LXArt.layout(w, h)       a blue-pencil background layout (the render job's input)
 *   LXArt.gouache(w, h, s)   a flat gouache background painting (the render box's output), seed s
 *   LXArt.pigeon(w, h, f)    "Pombo" pencil test, frame f (the head bobs with f)
 *   LXArt.icon(name, size)   bar and app icons, line style */
(function (G) {
  'use strict';
  function rng(seed) {
    return function () {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  const f1 = v => v.toFixed(1);

  function bike(w) {
    const h = w * .62;
    return `<svg width="${w}" height="${f1(h)}" viewBox="-36 -74 160 100" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <g stroke="#f2c14e" stroke-width="3.2">
        <circle cx="0" cy="0" r="25"/><circle cx="90" cy="0" r="25"/>
        <path d="M0 0 L36 0 L26 -42 L0 0 M36 0 L76 -42 L90 0 M26 -42 L72 -42"/>
        <path d="M18 -52 L34 -52 M76 -42 L72 -58 L84 -62"/>
      </g>
      <g stroke="#d9822b" stroke-width="2.4"><circle cx="36" cy="0" r="7"/><path d="M0 0 L36 -4"/></g>
      <g stroke="#7fb0e6" stroke-width="1.6" opacity=".7"><circle cx="0" cy="0" r="17"/><circle cx="90" cy="0" r="17"/></g>
      <path d="M62 -60 C72 -58 84 -56 90 -48" stroke="#e0675a" stroke-width="3.6"/>
      <circle cx="0" cy="0" r="3" fill="#f2c14e"/><circle cx="90" cy="0" r="3" fill="#f2c14e"/>
    </svg>`;
  }

  /** A sketchy line: two passes with a little seeded wobble (blue pencil). */
  function sk(r, x1, y1, x2, y2, col, wdt, op) {
    const j = () => (r() - .5) * 1.6;
    return `<path d="M${f1(x1 + j())} ${f1(y1 + j())} L${f1(x2 + j())} ${f1(y2 + j())}" stroke="${col}" stroke-width="${wdt}" opacity="${op}"/>` +
      `<path d="M${f1(x1 + j())} ${f1(y1 + j())} L${f1(x2 + j())} ${f1(y2 + j())}" stroke="${col}" stroke-width="${wdt * .7}" opacity="${op * .6}"/>`;
  }

  function layout(w, h) {
    const r = rng(1401), o = [], B = '#4a7bd0', D = '#4d4a55';
    o.push(`<rect width="${w}" height="${h}" fill="#f7f5ef"/>`);
    const hz = h * .46;
    o.push(sk(r, 0, hz, w, hz - 4, B, .9, .5));
    for (let i = 0; i < 7; i++) o.push(sk(r, w * .82, hz - 3, i * w / 6 - 20, h, B, .6, .28));      // perspective lines to a VP
    let x = 4;
    while (x < w - 8) {                                                                               // rooftops
      const bw = 14 + r() * 20, bh = 14 + r() * 26, base = hz + 18 + (x / w) * 16;
      o.push(sk(r, x, base, x, base - bh, D, .9, .75), sk(r, x + bw, base, x + bw, base - bh, D, .9, .75));
      o.push(sk(r, x - 2, base - bh, x + bw / 2, base - bh - 8, D, .9, .75), sk(r, x + bw / 2, base - bh - 8, x + bw + 2, base - bh, D, .9, .75));
      for (let k = 0; k < 2; k++) o.push(sk(r, x + 4 + k * 7, base - bh + 6, x + 4 + k * 7, base - bh + 11, D, .8, .6));
      x += bw + 2;
    }
    o.push(`<circle cx="${f1(w * .78)}" cy="${f1(hz - 16)}" r="${f1(h * .09)}" stroke="${B}" stroke-width=".9" fill="none" opacity=".55"/>`);
    o.push(`<text x="5" y="${h - 5}" font-family="Segoe Print, cursive" font-size="7.5" fill="${B}" opacity=".8">sc014 · BG · layout A</text>`);
    return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" fill="none" stroke-linecap="round">${o.join('')}</svg>`;
  }

  const SKIES = [
    ['#2c4a7c', '#7f97bd', '#f0c98c'], ['#3b3a6e', '#c98aa0', '#f4c79a'], ['#4f86c6', '#9cc3ef', '#f1e4cc'],
    ['#24304f', '#5a5f8f', '#d58b6a'], ['#5d8fc4', '#b7d2ee', '#f6e7c8'], ['#2f5066', '#6f9a9a', '#e9cf7e'],
  ];
  const FAC = ['#f1e4cc', '#f3c9a8', '#e9cf7e', '#a9c6e8', '#e7a07a', '#f6f0e4', '#d7e3c4', '#f0b9b0'];
  function gouache(w, h, seed, partial) {
    const r = rng(seed * 7919 + 3), o = [], s = SKIES[seed % SKIES.length], id = 'g' + seed + '_' + w;
    o.push(`<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${s[0]}"/><stop offset=".55" stop-color="${s[1]}"/><stop offset="1" stop-color="${s[2]}"/></linearGradient></defs>`);
    o.push(`<rect width="${w}" height="${h}" fill="url(#${id})"/>`);
    o.push(`<circle cx="${f1(w * (.6 + r() * .3))}" cy="${f1(h * (.35 + r() * .15))}" r="${f1(h * .09)}" fill="#fbe7b4" opacity=".85"/>`);
    o.push(`<rect y="${f1(h * .62)}" width="${w}" height="${f1(h * .1)}" fill="${s[1]}" opacity=".7"/>`);
    for (let band = 0; band < 2; band++) {
      let x = -4;
      const base0 = h * (band ? .98 : .72), k = band ? 0 : .35;
      while (x < w) {
        const bw = w * (.05 + r() * .06), bh = h * (.12 + r() * .2) * (band ? 1.4 : 1);
        const top = base0 - bh - Math.sin((x / w) * 3 + seed) * h * .05;
        const c = FAC[Math.floor(r() * FAC.length)];
        o.push(`<rect x="${f1(x)}" y="${f1(top)}" width="${f1(bw + .5)}" height="${f1(h - top)}" fill="${c}" opacity="${1 - k * .5}"/>`);
        o.push(`<path d="M${f1(x - 1)} ${f1(top)} L${f1(x + bw / 2)} ${f1(top - bh * .25)} L${f1(x + bw + 1)} ${f1(top)}Z" fill="#c35d38" opacity="${1 - k * .5}"/>`);
        if (band) for (let wy = top + bh * .2; wy < h - 3; wy += bh * .3) o.push(`<rect x="${f1(x + bw * .3)}" y="${f1(wy)}" width="${f1(bw * .16)}" height="${f1(bh * .14)}" fill="#3b3550" opacity=".8"/>`);
        x += bw;
      }
    }
    if (partial != null) {        // a render in progress: the bottom part is still noise
      const ny = h * partial;
      o.push(`<rect y="${f1(ny)}" width="${w}" height="${f1(h - ny)}" fill="#3a3a3a"/>`);
      for (let i = 0; i < 70; i++) o.push(`<rect x="${f1(r() * w)}" y="${f1(ny + r() * (h - ny))}" width="2" height="2" fill="${FAC[i % FAC.length]}" opacity=".35"/>`);
    }
    return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" preserveAspectRatio="xMidYMid slice">${o.join('')}</svg>`;
  }

  /** Pombo, the studio's pigeon: a pencil test frame. The head bobs over a 12-frame cycle (hold, push, hold). */
  function pigeon(w, h, frame) {
    const r = rng(77), o = [], B = '#5b86d6', D = '#3f3c46';
    const ph = ((frame % 12) + 12) % 12;
    const push = ph < 4 ? 0 : ph < 6 ? (ph - 3) / 3 : ph < 10 ? 1 : 1 - (ph - 9) / 3;   // head forward and back
    const hx = 182 + 22 * push, hy = 92 + 3 * push;
    o.push(`<rect width="400" height="260" fill="#f8f6ef"/>`);
    // three peg holes along the top (round, slot, round)
    o.push(`<g fill="#2a2a30"><circle cx="152" cy="14" r="5"/><rect x="186" y="9" width="28" height="10" rx="5"/><circle cx="248" cy="14" r="5"/></g>`);
    // blue construction: body, head, line of action
    o.push(`<g stroke="${B}" fill="none" stroke-width="1.1" opacity=".55"><ellipse cx="150" cy="150" rx="70" ry="48"/><circle cx="${hx}" cy="${hy}" r="24"/>
      <path d="M70 200 C130 130 170 110 ${hx + 30} ${hy - 20}"/><path d="M120 196 L116 232 M160 196 L166 232"/><path d="M60 240 H330" opacity=".6"/></g>`);
    // graphite clean-up line
    const j = () => (r() - .5) * 1.2;
    const body = `M${88 + j()} 160 C 96 118 130 104 ${hx - 22} ${hy + 20} C ${hx - 26} ${hy - 6} ${hx - 6} ${hy - 26} ${hx + 12} ${hy - 20} C ${hx + 26} ${hy - 14} ${hx + 26} ${hy + 4} ${hx + 18} ${hy + 14}
      L ${hx + 36} ${hy + 18} L ${hx + 16} ${hy + 22} C ${hx + 10} ${hy + 40} 214 168 196 188 C 170 204 120 204 96 190 L 52 206 L 78 176 C 70 172 84 166 ${88 + j()} 160Z`;
    o.push(`<path d="${body}" fill="none" stroke="${D}" stroke-width="2" stroke-linejoin="round"/>`);
    o.push(`<path d="${body}" fill="none" stroke="${D}" stroke-width="1" opacity=".45" transform="translate(1.2 .8)"/>`);
    o.push(`<path d="M110 150 C130 136 158 138 176 160 M118 166 C136 156 156 160 168 176" fill="none" stroke="${D}" stroke-width="1.4" opacity=".7"/>`);
    o.push(`<circle cx="${hx + 8}" cy="${hy - 6}" r="3" fill="${D}"/>`);
    o.push(`<path d="M128 196 L124 232 L114 236 M124 232 L132 236 M162 196 L168 232 L158 236 M168 232 L178 236" fill="none" stroke="${D}" stroke-width="1.8" stroke-linecap="round"/>`);
    // the frame number, circled, the way it's written on the sheet
    o.push(`<g font-family="Segoe Print, cursive" fill="${D}"><text x="352" y="240" font-size="17" text-anchor="middle">${String(frame).padStart(3, '0')}</text></g>`);
    o.push(`<ellipse cx="352" cy="234" rx="26" ry="15" fill="none" stroke="${D}" stroke-width="1.2" opacity=".8"/>`);
    o.push(`<text x="18" y="244" font-family="Segoe Print, cursive" font-size="10" fill="${B}" opacity=".85">pombo · sc014 · A</text>`);
    return `<svg width="${w}" height="${h}" viewBox="0 0 400 260" preserveAspectRatio="xMidYMid meet">${o.join('')}</svg>`;
  }

  const ICONS = {
    cpu: '<rect x="3.5" y="3.5" width="9" height="9" rx="1.5"/><rect x="6" y="6" width="4" height="4" fill="currentColor" stroke="none"/><path d="M6 1.5v2M10 1.5v2M6 12.5v2M10 12.5v2M1.5 6h2M1.5 10h2M12.5 6h2M12.5 10h2"/>',
    mem: '<rect x="1.5" y="4.5" width="13" height="7" rx="1"/><path d="M4 7v2M7 7v2M10 7v2M13 7v2M3 11.5v2M13 11.5v2"/>',
    net: '<path d="M4 2.5v8M1.8 8.2 4 10.6l2.2-2.4M12 13.5v-8M9.8 7.8 12 5.4l2.2 2.4"/>',
    eth: '<rect x="2.5" y="5" width="11" height="8" rx="1"/><path d="M5 5V3h6v2M5.5 9.5v1.5M8 9.5v1.5M10.5 9.5v1.5"/>',
    vol: '<path d="M2 6h3l4-3v10l-4-3H2z"/><path d="M11 5.5c1 1.4 1 3.6 0 5M12.8 3.8c2 2.4 2 6 0 8.4"/>',
    cloud: '<path d="M4.5 12.5h7.2a2.8 2.8 0 0 0 .3-5.6A4 4 0 0 0 4.3 7.6a2.5 2.5 0 0 0 .2 4.9z"/>',
    bt: '<path d="M5 5l6 6-3 3V2l3 3-6 6"/>',
    moon: '<path d="M12.5 10.2A5.6 5.6 0 0 1 5.8 3.5a5.6 5.6 0 1 0 6.7 6.7z"/>',
    sun: '<circle cx="8" cy="8" r="3"/><path d="M8 1v1.8M8 13.2V15M1 8h1.8M13.2 8H15M3 3l1.3 1.3M11.7 11.7 13 13M3 13l1.3-1.3M11.7 4.3 13 3"/>',
    bat: '<rect x="1.5" y="4.5" width="12" height="7" rx="1.5"/><path d="M14.5 7v2"/><path d="M6.5 6 5 8.3h2.5L6 10.5" stroke-width="1.2"/>',
    clock: '<circle cx="8" cy="8" r="6"/><path d="M8 4.5V8l2.5 1.5"/>',
    queue: '<path d="M3 4h10M3 8h10M3 12h6"/>',
    nodes: '<rect x="1.5" y="2.5" width="5" height="4" rx="1"/><rect x="9.5" y="9.5" width="5" height="4" rx="1"/><path d="M6.5 4.5c4 0 0 7 3 7"/>',
    models: '<path d="M8 1.8 14 5v6l-6 3.2L2 11V5z"/><path d="M2 5l6 3.2L14 5M8 8.2v6"/>',
    flow: '<rect x="2" y="2" width="12" height="12" rx="2"/><path d="M5 6h6M5 10h4"/>',
    gear: '<circle cx="8" cy="8" r="2.4"/><path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3.4 3.4l1.4 1.4M11.2 11.2l1.4 1.4M3.4 12.6l1.4-1.4M11.2 4.8l1.4-1.4"/>',
    play: '<path d="M4.5 3v10l8-5z" fill="currentColor"/>',
    search: '<circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5 14 14"/>',
    lock: '<rect x="3" y="7" width="10" height="7" rx="1.5"/><path d="M5 7V5a3 3 0 0 1 6 0v2"/>',
    back: '<path d="M10 3 5 8l5 5"/>',
    fwd: '<path d="M6 3l5 5-5 5"/>',
    reload: '<path d="M13 8a5 5 0 1 1-1.5-3.6M13 2.5v3h-3"/>',
    branch: '<circle cx="4.5" cy="3.5" r="1.6"/><circle cx="4.5" cy="12.5" r="1.6"/><circle cx="11.5" cy="5.5" r="1.6"/><path d="M4.5 5.1v5.8M11.5 7.1c0 3-7 2-7 3.8"/>',
    wifi: '<path d="M1.5 6a9.5 9.5 0 0 1 13 0M3.8 8.6a6.2 6.2 0 0 1 8.4 0M6.1 11.1a2.9 2.9 0 0 1 3.8 0"/><circle cx="8" cy="13.4" r=".9" fill="currentColor"/>',
    ask: '<path d="M2.5 3.5h11v7h-6l-3 2.5v-2.5h-2z"/>',
    memory: '<rect x="2.5" y="2.5" width="11" height="11" rx="2"/><path d="M5 6h6M5 8.5h6M5 11h3.5"/>',
    conflict: '<path d="M8 2 14.5 13.5h-13z"/><path d="M8 6.5v3.2M8 11.6v.2"/>',
    inbox: '<path d="M2 9.5 4 3.5h8l2 6v4H2z"/><path d="M2 9.5h3.5l1 1.6h3l1-1.6H14"/>',
  };
  function icon(name, size = 12, extra = '') {
    return `<svg class="ico ${extra}" width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${ICONS[name] || ''}</svg>`;
  }
  /** the pastel de nata module icon: flaky crust, custard, burnt spots */
  function nata(size = 14) {
    return `<svg class="ico" width="${size}" height="${size}" viewBox="0 0 16 16"><path d="M1.5 8.2 3 12.6c.4 1 2.4 1.9 5 1.9s4.6-.9 5-1.9l1.5-4.4z" fill="#c9893a"/><path d="M2.6 9.8h10.8M3.2 11.4h9.6" stroke="#9a5f22" stroke-width=".7"/>
      <ellipse cx="8" cy="8" rx="6.6" ry="3.2" fill="#e3a648"/><ellipse cx="8" cy="7.8" rx="5.3" ry="2.5" fill="#f5cf5e"/>
      <circle cx="6" cy="7.4" r="1" fill="#6b3b17"/><circle cx="9.4" cy="8.4" r=".8" fill="#6b3b17"/><circle cx="10.6" cy="7" r=".6" fill="#7d4a1c"/><circle cx="7.8" cy="6.6" r=".5" fill="#7d4a1c"/></svg>`;
  }

  G.LXArt = { bike, layout, gouache, pigeon, icon, nata, rng };
})(window);
