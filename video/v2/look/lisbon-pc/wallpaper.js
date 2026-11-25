/* Theo's wallpaper: "Lisboa, first morning", his own flat illustration (original artwork, no landmarks traced, no
 * logos). Hills of houses stepping down to the river, a yellow tram, a bike against the wall, an azulejo band along
 * the bottom, signed like the 2009 one ("made by theo :) 2009" -> "made by theo :) lisboa 2026").
 *
 *   LXWall.svg(w, h)  -> an <svg> string, deterministic (seeded), sliced to fill any aspect (16:9 monitors, 16:10 laptop).
 * Only the gaps of the tiling layout show it on the monitors; the laptop's empty workspace shows all of it. */
(function (G) {
  'use strict';

  function rng(seed) {                       // mulberry32: same houses on every render
    return function () {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  const mix = (a, b, k) => {
    const pa = [1, 3, 5].map(i => parseInt(a.slice(i, i + 2), 16)), pb = [1, 3, 5].map(i => parseInt(b.slice(i, i + 2), 16));
    return '#' + pa.map((v, i) => Math.round(v + (pb[i] - v) * k).toString(16).padStart(2, '0')).join('');
  };

  const FACADES = ['#f1e4cc', '#f3c9a8', '#e9cf7e', '#a9c6e8', '#e7a07a', '#f6f0e4', '#d7e3c4', '#f0b9b0'];
  const ROOF = '#c35d38', ROOF2 = '#a94a2d', WIN = '#3b3550', SHUT = '#5f8a6a', HAZE = '#9db0d4';

  /** One band of houses along a hill curve. depth 0 = near (full colour), 1 = far (hazy). */
  function houses(r, yOf, x0, x1, depth, out) {
    let x = x0;
    while (x < x1) {
      const w = 26 + r() * 30 * (1 - depth * .45), h = 30 + r() * 44 * (1 - depth * .4);
      const base = yOf(x + w / 2) + 6;
      const top = base - h;
      const k = depth * .72;
      const fac = mix(FACADES[Math.floor(r() * FACADES.length)], HAZE, k);
      const roof = mix(r() < .5 ? ROOF : ROOF2, HAZE, k);
      out.push(`<rect x="${x.toFixed(1)}" y="${top.toFixed(1)}" width="${(w + .6).toFixed(1)}" height="${(h + 60).toFixed(1)}" fill="${fac}"/>`);
      // roof: pitched (terracotta) or flat with a parapet
      if (r() < .72) {
        const ov = 3;
        out.push(`<path d="M${(x - ov).toFixed(1)} ${top.toFixed(1)} L${(x + w / 2).toFixed(1)} ${(top - 9 - r() * 6).toFixed(1)} L${(x + w + ov).toFixed(1)} ${top.toFixed(1)}Z" fill="${roof}"/>`);
      } else {
        out.push(`<rect x="${x.toFixed(1)}" y="${(top - 3).toFixed(1)}" width="${w.toFixed(1)}" height="3" fill="${mix(fac, '#000000', .12)}"/>`);
      }
      // windows: a grid of tall Lisbon windows, some with green shutters
      if (depth < .85) {
        const cols = Math.max(1, Math.floor(w / 11)), rows = Math.max(1, Math.floor((h - 8) / 15));
        const ww = 4.2 * (1 - depth * .4), wh = 7.5 * (1 - depth * .4);
        for (let cy = 0; cy < rows; cy++) for (let cx = 0; cx < cols; cx++) {
          if (r() < .12) continue;
          const wx = x + (w / cols) * (cx + .5) - ww / 2, wy = top + 6 + cy * 15;
          const c = r() < .22 ? mix(SHUT, HAZE, k) : mix(WIN, HAZE, k * .9);
          out.push(`<rect x="${wx.toFixed(1)}" y="${wy.toFixed(1)}" width="${ww.toFixed(1)}" height="${wh.toFixed(1)}" fill="${c}"/>`);
        }
      }
      x += w + (r() < .15 ? 2 + r() * 4 : 0);
    }
  }

  function azulejo(id) {          // a 60px tile: white glaze, cobalt quarter-circles, a four-petal flower, corner dots
    const b = '#2f5f9e', b2 = '#5d8bc8', g = '#f4f1ea';
    return `<pattern id="${id}" width="60" height="60" patternUnits="userSpaceOnUse">
      <rect width="60" height="60" fill="${g}"/>
      <path d="M0 0h60v60H0z" fill="none" stroke="#d9d3c4" stroke-width="1"/>
      <path d="M0 18 A18 18 0 0 0 18 0 L0 0Z M60 18 A18 18 0 0 1 42 0 L60 0Z M0 42 A18 18 0 0 1 18 60 L0 60Z M60 42 A18 18 0 0 0 42 60 L60 60Z" fill="${b}"/>
      <path d="M30 12 C36 22 36 24 30 30 C24 24 24 22 30 12Z M30 48 C24 38 24 36 30 30 C36 36 36 38 30 48Z M12 30 C22 24 24 24 30 30 C24 36 22 36 12 30Z M48 30 C38 36 36 36 30 30 C36 24 38 24 48 30Z" fill="${b}"/>
      <circle cx="30" cy="30" r="3.4" fill="${g}"/><circle cx="30" cy="30" r="1.6" fill="${b}"/>
      <path d="M30 2 v6 M30 52 v6 M2 30 h6 M52 30 h6" stroke="${b2}" stroke-width="2.2" stroke-linecap="round"/>
    </pattern>`;
  }

  function tram(x, y, s) {       // the yellow tram, side on, heading downhill (left)
    const Y = '#f2c14e', Yd = '#d9a531', W = '#f6f0e0', D = '#2a2433';
    return `<g transform="translate(${x} ${y}) rotate(-4) scale(${s})">
      <path d="M-4 -78 L64 -96" stroke="${D}" stroke-width="2"/>
      <path d="M44 -58 L60 -95" stroke="${D}" stroke-width="2"/>
      <rect x="-6" y="-60" width="132" height="8" rx="3" fill="${W}"/>
      <rect x="-2" y="-54" width="124" height="52" rx="6" fill="${Y}"/>
      <rect x="-2" y="-20" width="124" height="18" rx="2" fill="${Yd}"/>
      <rect x="-2" y="-24" width="124" height="4" fill="${W}"/>
      ${[0, 1, 2, 3, 4].map(i => `<rect x="${6 + i * 23}" y="-48" width="17" height="20" rx="2" fill="#384a66"/><rect x="${6 + i * 23}" y="-48" width="17" height="6" rx="2" fill="#5b7398"/>`).join('')}
      <text x="113" y="-31" font-family="Fira Code, monospace" font-size="9" font-weight="700" fill="${D}" text-anchor="middle">28</text>
      <rect x="10" y="-2" width="100" height="5" fill="${D}"/>
      <circle cx="26" cy="5" r="7" fill="${D}"/><circle cx="94" cy="5" r="7" fill="${D}"/>
      <circle cx="26" cy="5" r="2.4" fill="#8a7f70"/><circle cx="94" cy="5" r="2.4" fill="#8a7f70"/>
    </g>`;
  }

  function bike(x, y, s) {       // a town bike leaning on the wall (the shop, in a line drawing)
    const D = '#2a2433';
    return `<g transform="translate(${x} ${y}) scale(${s})" fill="none" stroke="${D}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="0" cy="0" r="26"/><circle cx="78" cy="0" r="26"/>
      <circle cx="0" cy="0" r="3" fill="${D}"/><circle cx="78" cy="0" r="3" fill="${D}"/>
      <path d="M0 0 L30 -2 L22 -40 L0 0 M30 -2 L66 -40 L78 0 M22 -40 L64 -40 M18 -50 L30 -50 M66 -40 L62 -56 L72 -60"/>
      <circle cx="30" cy="-2" r="6"/>
      <path d="M60 -48 C70 -46 80 -44 84 -38" stroke="#c35d38" stroke-width="4"/>
    </g>`;
  }

  function svg(w, h) {
    const W = 1600, H = 900;                       // design canvas; sliced to the target aspect (16:10 keeps x 80..1520)
    const r = rng(20261123);
    const sky = `<linearGradient id="lxSky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#1b2f52"/><stop offset=".34" stop-color="#355d93"/>
        <stop offset=".56" stop-color="#7f97bd"/><stop offset=".7" stop-color="#e3b680"/><stop offset=".78" stop-color="#f3d49c"/></linearGradient>
      <radialGradient id="lxSun" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff2c8"/><stop offset=".35" stop-color="#f8dc8e" stop-opacity=".9"/><stop offset="1" stop-color="#f3c46a" stop-opacity="0"/></radialGradient>
      <linearGradient id="lxRiver" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8fa9cf"/><stop offset="1" stop-color="#4d74a8"/></linearGradient>
      <linearGradient id="lxShade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#14101a" stop-opacity=".35"/></linearGradient>
      ${azulejo('lxTile')}`;
    const o = [];
    o.push(`<rect width="${W}" height="${H}" fill="url(#lxSky)"/>`);
    // a few stars still out at the top (it's early), and long morning clouds
    for (let i = 0; i < 40; i++) o.push(`<circle cx="${(r() * W).toFixed(0)}" cy="${(r() * 200).toFixed(0)}" r="${(.6 + r() * 1.1).toFixed(2)}" fill="#f6efe0" opacity="${(.25 + r() * .5).toFixed(2)}"/>`);
    o.push(`<circle cx="1190" cy="520" r="210" fill="url(#lxSun)"/><circle cx="1190" cy="520" r="44" fill="#fff0c4"/>`);
    for (const [cx, cy, rx, op] of [[380, 330, 260, .22], [980, 290, 200, .18], [1380, 400, 230, .2], [700, 430, 300, .16]]) {
      o.push(`<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${(rx * .055).toFixed(1)}" fill="#f6dcc0" opacity="${op}"/>`);
    }
    // the far bank and the river, a suspension bridge in the haze
    o.push(`<path d="M0 568 C200 556 420 572 640 560 C900 548 1150 566 1600 552 L1600 640 L0 640Z" fill="#8d97bb"/>`);
    o.push(`<rect y="586" width="${W}" height="80" fill="url(#lxRiver)"/>`);
    for (let i = 0; i < 26; i++) { const gx = 820 + r() * 620, gy = 596 + r() * 60; o.push(`<rect x="${gx.toFixed(0)}" y="${gy.toFixed(0)}" width="${(10 + r() * 46).toFixed(0)}" height="1.6" fill="#fbe7b4" opacity="${(.35 + r() * .5).toFixed(2)}"/>`); }
    o.push(`<g stroke="#b04a32" fill="none" opacity=".8"><path d="M560 596 L1240 590" stroke-width="5"/><path d="M700 520 v80 M1080 516 v80" stroke-width="7"/>
      <path d="M560 560 Q630 600 700 522 Q890 612 1080 518 Q1160 590 1240 556" stroke-width="2.2"/></g>`);
    // three bands of houses on the hills: far, middle, near
    houses(r, x => 600 - 90 * Math.exp(-Math.pow((x - 260) / 300, 2)) - 40 * Math.exp(-Math.pow((x - 1420) / 260, 2)), -20, W + 20, .85, o);
    houses(r, x => 650 - 150 * Math.exp(-Math.pow((x - 140) / 380, 2)) - 70 * Math.exp(-Math.pow((x - 1500) / 300, 2)), -20, W + 20, .45, o);
    o.push(`<rect y="640" width="${W}" height="${H - 640}" fill="url(#lxShade)"/>`);
    houses(r, x => 760 - 210 * Math.exp(-Math.pow((x + 60) / 420, 2)) - 40 * Math.exp(-Math.pow((x - 1640) / 220, 2)), -40, W + 40, 0, o);
    // the street: cobbles, rails, wires, the tram coming down
    o.push(`<path d="M0 760 L1600 808 L1600 900 L0 900Z" fill="#3d3446"/>`);
    o.push(`<path d="M0 772 L1600 822 M0 792 L1600 842" stroke="#a49a8c" stroke-width="2.2" opacity=".75"/>`);
    o.push(`<path d="M-10 668 L1610 714" stroke="#2a2433" stroke-width="1.4" opacity=".8"/>`);
    o.push(tram(620, 792, 1.25));
    o.push(bike(1090, 812, .78));
    // three pigeons over the river (the studio's film is about one)
    for (const [bx, by, s] of [[930, 250, 1], [968, 236, .8], [1010, 262, .9]]) o.push(`<path d="M${bx - 9 * s} ${by} q${4.5 * s} ${-6 * s} ${9 * s} 0 q${4.5 * s} ${-6 * s} ${9 * s} 0" stroke="#22304d" stroke-width="2" fill="none" stroke-linecap="round"/>`);
    // azulejo band along the bottom, with its shadow line
    o.push(`<rect y="830" width="${W}" height="70" fill="url(#lxTile)"/>`);
    o.push(`<rect y="826" width="${W}" height="5" fill="#2a2433" opacity=".5"/>`);
    o.push(`<text x="1490" y="818" font-family="Segoe Print, Fira Code, cursive" font-size="15" fill="#f6efe0" opacity=".85" text-anchor="end">made by theo :) lisboa 2026</text>`);
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMax slice"><defs>${sky}</defs>${o.join('')}</svg>`;
  }

  G.LXWall = { svg };
})(window);
