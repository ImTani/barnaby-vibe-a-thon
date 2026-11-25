/* Shop PC wallpaper: the one Theo made in 2009 (in an image editor, at 14, with every filter switched on).
 * Deep aqua-blue, light trails, bokeh, a glass chainring with its chain melting into the light, the shop's
 * yellow line ("dont touch the yellow line, mum likes it"), a glossy wordmark with a reflection, a lens flare.
 * Original artwork, drawn in a 1280x720 viewBox and scaled to cover. WALLPAPER() returns an <svg> string. */
(function (G) {
  const { gearPath, circ, spider } = G.ICONS;

  function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

  /** Points along the chain: top run (leftwards), the front arc, bottom run (leftwards). */
  function chainPoints(cx, cy, rp, pitch, runLen) {
    const pts = [], slope = Math.tan(7 * Math.PI / 180);
    const nRun = Math.floor(runLen / pitch);
    for (let i = nRun; i > 0; i--) pts.push([cx - i * pitch, cy - rp + i * pitch * slope]);
    const step = pitch / rp;
    for (let a = -Math.PI / 2; a <= Math.PI / 2 + 1e-6; a += step) pts.push([cx + rp * Math.cos(a), cy + rp * Math.sin(a)]);
    const last = pts[pts.length - 1];
    for (let i = 1; i <= nRun; i++) pts.push([last[0] - i * pitch, last[1] - i * pitch * slope]);
    return pts;
  }

  function chainSVG(pts, fadeId) {
    let plates = '', rollers = '';
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
      const ang = Math.atan2(y1 - y0, x1 - x0) * 180 / Math.PI, len = Math.hypot(x1 - x0, y1 - y0);
      const outer = i % 2 === 0, h = outer ? 15 : 12.5, ext = outer ? 8 : 6;
      plates += `<rect x="${(-ext).toFixed(1)}" y="${(-h / 2).toFixed(1)}" width="${(len + 2 * ext).toFixed(1)}" height="${h}" rx="${h / 2}" transform="translate(${x0.toFixed(1)} ${y0.toFixed(1)}) rotate(${ang.toFixed(2)})" fill="${outer ? 'rgba(220,240,255,.10)' : 'rgba(160,210,255,.07)'}" stroke="rgba(235,248,255,${outer ? .55 : .35})" stroke-width="1"/>`;
    }
    for (const [x, y] of pts) rollers += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.6" fill="rgba(255,255,255,.22)" stroke="rgba(255,255,255,.7)" stroke-width=".8"/>`;
    return `<g mask="url(#${fadeId})">${plates}${rollers}</g>`;
  }

  function WALLPAPER() {
    const W = 1280, H = 720, R = rng(1987);
    const cx = 736, cy = 302, R1 = 196, R0 = 183, RI = 146, RP = 190;
    let bokeh = '';
    for (let i = 0; i < 34; i++) {
      const x = R() * W, y = R() * H * .9, r = 5 + Math.pow(R(), 2) * 38, o = .025 + R() * .07;
      bokeh += `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${r.toFixed(1)}" fill="rgba(200,235,255,${o.toFixed(3)})" stroke="rgba(220,245,255,${(o * 1.6).toFixed(3)})" stroke-width="1"/>`;
    }
    const ribbon = 'M-120 590 C 180 430, 470 650, 760 500 S 1120 250, 1420 300';
    const ribbon2 = 'M-120 640 C 220 520, 520 700, 840 560 S 1180 360, 1420 380';
    const ribbon3 = 'M-120 470 C 160 360, 420 520, 640 420 S 980 170, 1420 190';
    const gold = 'M-80 640 C 260 560, 560 712, 930 662 S 1230 470, 1400 470';
    const bolts = [0, 1, 2, 3, 4].map(i => { const a = i / 5 * Math.PI * 2 - Math.PI / 2; return `<circle cx="${(cx + Math.cos(a) * (RI - 9)).toFixed(1)}" cy="${(cy + Math.sin(a) * (RI - 9)).toFixed(1)}" r="5.5" fill="rgba(255,255,255,.25)" stroke="rgba(255,255,255,.75)"/>`; }).join('');
    const chain = chainPoints(cx, cy, RP, 26.4, 520);
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid slice" width="100%" height="100%">
<defs>
  <linearGradient id="wpBg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05284f"/><stop offset=".55" stop-color="#0a4c80"/><stop offset="1" stop-color="#062a4c"/></linearGradient>
  <radialGradient id="wpGlowA" cx="${cx / W}" cy="${cy / H}" r=".55"><stop offset="0" stop-color="#3fb0ee" stop-opacity=".75"/><stop offset=".5" stop-color="#1a6fb0" stop-opacity=".3"/><stop offset="1" stop-color="#0a3b6c" stop-opacity="0"/></radialGradient>
  <radialGradient id="wpGlowB" cx=".08" cy=".95" r=".5"><stop offset="0" stop-color="#2ad1c1" stop-opacity=".45"/><stop offset="1" stop-color="#2ad1c1" stop-opacity="0"/></radialGradient>
  <linearGradient id="wpRib" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#2ae0c8" stop-opacity="0"/><stop offset=".25" stop-color="#3fe6d0"/><stop offset=".6" stop-color="#7fd6ff"/><stop offset="1" stop-color="#ffffff" stop-opacity=".2"/></linearGradient>
  <linearGradient id="wpGold" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffcc00" stop-opacity="0"/><stop offset=".2" stop-color="#ffcc00"/><stop offset=".8" stop-color="#ffe066"/><stop offset="1" stop-color="#ffcc00" stop-opacity="0"/></linearGradient>
  <linearGradient id="wpRing" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity=".34"/><stop offset=".45" stop-color="#bfe6ff" stop-opacity=".1"/><stop offset=".75" stop-color="#7cc8ff" stop-opacity=".06"/><stop offset="1" stop-color="#ffffff" stop-opacity=".24"/></linearGradient>
  <linearGradient id="wpWord" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".5" stop-color="#e6f4ff"/><stop offset=".52" stop-color="#b8dcf7"/><stop offset="1" stop-color="#e9f6ff"/></linearGradient>
  <linearGradient id="wpRefl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".42"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <mask id="wpReflMask"><rect x="0" y="582" width="${W}" height="44" fill="url(#wpRefl)"/></mask>
  <linearGradient id="wpChainFadeG" x1="0" y1="0" x2="1" y2="0"><stop offset=".22" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff"/></linearGradient>
  <mask id="wpChainFade"><rect width="${W}" height="${H}" fill="url(#wpChainFadeG)"/></mask>
  <radialGradient id="wpFlare" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff"/><stop offset=".25" stop-color="#e9f7ff" stop-opacity=".7"/><stop offset="1" stop-color="#9fdcff" stop-opacity="0"/></radialGradient>
  <filter id="wpB30" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="26"/></filter>
  <filter id="wpB10" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="9"/></filter>
  <filter id="wpB3" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="2.6"/></filter>
  <filter id="wpB1"><feGaussianBlur stdDeviation="1.2"/></filter>
</defs>
<rect width="${W}" height="${H}" fill="url(#wpBg)"/>
<rect width="${W}" height="${H}" fill="url(#wpGlowA)"/>
<rect width="${W}" height="${H}" fill="url(#wpGlowB)"/>
<g opacity=".9">${bokeh}</g>
<path d="${ribbon3}" stroke="url(#wpRib)" stroke-width="70" fill="none" opacity=".22" filter="url(#wpB30)"/>
<path d="${ribbon}" stroke="url(#wpRib)" stroke-width="120" fill="none" opacity=".35" filter="url(#wpB30)"/>
<path d="${ribbon}" stroke="url(#wpRib)" stroke-width="26" fill="none" opacity=".45" filter="url(#wpB10)"/>
<path d="${ribbon2}" stroke="url(#wpRib)" stroke-width="40" fill="none" opacity=".25" filter="url(#wpB10)"/>
<path d="${ribbon}" stroke="#fff" stroke-width="1.4" fill="none" opacity=".75"/>
<path d="${ribbon2}" stroke="#dff6ff" stroke-width="1" fill="none" opacity=".5"/>
<path d="${ribbon3}" stroke="#dff6ff" stroke-width="1" fill="none" opacity=".4"/>
<path d="${gold}" stroke="url(#wpGold)" stroke-width="10" fill="none" opacity=".55" filter="url(#wpB10)"/>
<path d="${gold}" stroke="url(#wpGold)" stroke-width="2.6" fill="none"/>
<circle cx="${cx}" cy="${cy}" r="${R1 + 40}" fill="#7fd0ff" opacity=".16" filter="url(#wpB30)"/>
${chainSVG(chain, 'wpChainFade')}
<path d="${gearPath(cx, cy, 42, R0, R1, .38, .58)} ${circ(cx, cy, RI)}" fill="url(#wpRing)" fill-rule="evenodd" stroke="rgba(235,248,255,.8)" stroke-width="1.5" stroke-linejoin="round"/>
<path d="${circ(cx, cy, RI)} ${circ(cx, cy, RI - 20)}" fill="rgba(255,255,255,.06)" fill-rule="evenodd" stroke="rgba(255,255,255,.4)"/>
<path d="${spider(cx, cy, 5, 52, RI - 18, 30)}" fill="url(#wpRing)" stroke="rgba(235,248,255,.7)" stroke-width="1.2" stroke-linejoin="round"/>
<circle cx="${cx}" cy="${cy}" r="46" fill="url(#wpRing)" stroke="rgba(235,248,255,.8)" stroke-width="1.4"/>
<circle cx="${cx}" cy="${cy}" r="20" fill="rgba(4,30,60,.45)" stroke="rgba(235,248,255,.7)"/>
${bolts}
<path d="M${cx - R1 + 22} ${cy - 40} A ${R1 - 8} ${R1 - 8} 0 0 1 ${cx - 40} ${cy - R1 + 18}" fill="none" stroke="#fff" stroke-width="5" opacity=".55" stroke-linecap="round" filter="url(#wpB3)"/>
<path d="M${cx - R1 + 22} ${cy - 40} A ${R1 - 8} ${R1 - 8} 0 0 1 ${cx - 40} ${cy - R1 + 18}" fill="none" stroke="#fff" stroke-width="1.4" opacity=".9" stroke-linecap="round"/>
<g transform="translate(${cx - 118} ${cy - 160})">
  <circle r="44" fill="url(#wpFlare)" opacity=".85"/><ellipse rx="190" ry="1.6" fill="#fff" opacity=".7" filter="url(#wpB1)"/><ellipse rx="1.6" ry="60" fill="#fff" opacity=".5" filter="url(#wpB1)"/>
  <path d="M0 -12 L3 -3 L12 0 L3 3 L0 12 L-3 3 L-12 0 L-3 -3z" fill="#fff"/></g>
<g opacity=".5">
  <circle cx="${cx + 40}" cy="${cy + 30}" r="16" fill="#9fe6ff" opacity=".18"/><circle cx="${cx + 130}" cy="${cy + 122}" r="30" fill="#ffd36a" opacity=".1"/>
  <circle cx="${cx + 190}" cy="${cy + 182}" r="9" fill="#bdf" opacity=".25"/><polygon points="${hex(cx + 260, cy + 250, 22)}" fill="#7fc8ff" opacity=".12"/></g>
<text x="${cx}" y="536" text-anchor="middle" font-family="Trebuchet MS, Verdana, sans-serif" font-size="13" letter-spacing="4.2" fill="#ffe680" opacity=".92">A HARTLEY FAMILY WORKSHOP · EST. 1987</text>
<g font-family="Trebuchet MS, Verdana, sans-serif" font-style="italic" font-weight="700" font-size="50" text-anchor="middle">
  <text x="${cx}" y="584" fill="#03213f" opacity=".55" filter="url(#wpB3)" dx="3" dy="4">Spokes &amp; Sprockets</text>
  <text x="${cx}" y="584" fill="url(#wpWord)" stroke="#0c3c6a" stroke-width=".6">Spokes &amp; Sprockets</text>
  <g mask="url(#wpReflMask)"><text x="${cx}" y="584" fill="#cfe9ff" transform="translate(0 1172) scale(1 -1)">Spokes &amp; Sprockets</text></g>
</g>
<text x="${W - 84}" y="${H - 50}" text-anchor="end" font-family="Verdana" font-size="8.5" fill="#cfe7ff" opacity=".4">made by theo :) 2009</text>
</svg>`;
  }
  function hex(x, y, r) { let p = []; for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2; p.push(`${(x + r * Math.cos(a)).toFixed(1)},${(y + r * Math.sin(a)).toFixed(1)}`); } return p.join(' '); }

  G.WALLPAPER = WALLPAPER;
})(window);
