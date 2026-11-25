/* PRIYA: her bench, rebalanced. Usable first: her two jobs as the paper repair tags Martin writes (big, the facts she
   works from: who, which bike, what, when, are the parts there); then the things she can ask, on a toolroll laid open
   along the bottom, one pocket each, every question printed flat and readable, each tagged with the room it happens in
   (the same room colours as Martin's plan). The fun lives in the details: the tags' string and eyelet, Martin's hand
   crossing Dev out, a grease thumbprint, the tools in their pockets, Theo's README line on a torn slip.
   PRIYA.tag(job, o) -> HTML; PRIYA.tool(kind) -> SVG markup; PRIYA.asks(list) -> HTML. Pure functions. */
(function () {
  const { esc } = window.W2, W = window.WORLDS;
  const room = id => W.ROOMS.find(r => r.id === id);
  const hrs = h => String(h).replace('.5', '½');

  function tag(j, o = {}) {
    const ok = j.parts.every(p => p[1]);
    const short = j.parts.find(p => !p[1]);
    const due = j.due === 'Today' ? '<span class="due now">Due today</span>' : `<span class="due">Due ${esc(j.due)}</span>`;
    const parts = ok
      ? `<div class="parts ok"><svg viewBox="0 0 24 24"><path d="M4 12.6 9.4 18 20 6.4"/></svg><span>Spokes and rim on the shelf</span></div>`
      : `<div class="parts short"><svg viewBox="0 0 24 24"><path class="tri" d="M12 2.6 23 21.4H1Z"/><path class="bar" d="M12 9v5.6"/><circle cx="12" cy="18.1" r="1.5"/></svg><span><b>Spokes short</b><br>${esc(short[2].replace('; both wheels need 64', ''))}; both wheels need 64</span></div>`;
    const kind = j.work.replace('Wheel build, ', '').replace(', 32 hole', '');
    return `<div class="tag ${o.ghost ? 'ghost' : ''}" style="${o.style || ''}">
      ${o.ghost ? '<svg class="gh" viewBox="0 0 600 420" preserveAspectRatio="none"><polygon points="64,2 598,2 598,418 64,418 2,356 2,64" fill="none" stroke="#2B2416" stroke-width="3" stroke-dasharray="12 9"/></svg>' : ''}
      <div class="eyelet"></div>
      <div class="t-top"><span class="no">${j.job}</span>${o.ghost ? '<span class="due offered">Offered to you</span>' : due}</div>
      <div class="who">${esc(j.who)}</div>
      <div class="bike">${esc(j.bike)}</div>
      <div class="work">${esc(kind[0].toUpperCase() + kind.slice(1))} wheel build · 32 hole <span class="h">${hrs(j.hours)} h</span></div>
      ${o.ghost ? '' : `<div class="perf"></div>${parts}`}
      <div class="mech">Mech: <s>Dev</s> <span class="pri">Priya</span></div>
      ${o.thumb ? '<div class="thumb"></div>' : ''}
    </div>`;
  }

  /* tools for the pockets: steel, one stroke weight, drawn upright in a 60x150 box (the part that shows above the pocket) */
  const STEEL = '#AEB3B9', EDGE = '#4E545B';
  const TOOLS = {
    spanner: `<path d="M23 150V40h14v110z" fill="${STEEL}" stroke="${EDGE}" stroke-width="2.5"/><path d="M30 6a22 22 0 1 0 .1 0zM22 12h16v22H22z" fill="${STEEL}" stroke="${EDGE}" stroke-width="2.5" fill-rule="evenodd"/>`,
    spokekey: `<circle cx="30" cy="34" r="22" fill="${STEEL}" stroke="${EDGE}" stroke-width="2.5"/><circle cx="30" cy="34" r="7" fill="#5f5a49" stroke="${EDGE}" stroke-width="2"/><path d="M30 12v8M52 34h-8M30 56v-8M8 34h8" stroke="${EDGE}" stroke-width="4"/><path d="M26 56h8v94h-8z" fill="#C25E17" stroke="${EDGE}" stroke-width="2.5"/>`,
    lever: `<path d="M20 150V30c0-14 5-22 14-24 7-1 10 4 7 9-3 4-7 6-7 14v121z" fill="${STEEL}" stroke="${EDGE}" stroke-width="2.5"/>`,
    cutters: `<path d="M24 150 28 70 22 40c-3-14 0-28 8-32 8 4 11 18 8 32l-6 30 4 80z" fill="${STEEL}" stroke="${EDGE}" stroke-width="2.5"/><circle cx="30" cy="62" r="5" fill="${EDGE}"/><path d="M18 150 22 92h16l4 58z" fill="#3B3F45"/>`,
    driver: `<path d="M27 8h6v66h-6z" fill="${STEEL}" stroke="${EDGE}" stroke-width="2.5"/><path d="M27 8l3-6 3 6" fill="${STEEL}" stroke="${EDGE}" stroke-width="2"/><path d="M19 74h22l-2 76H21z" fill="#2F6B5A" stroke="${EDGE}" stroke-width="2.5"/>`,
    spoke: `<path d="M30 150V18" stroke="${EDGE}" stroke-width="5.5"/><path d="M30 150V18" stroke="${STEEL}" stroke-width="3"/><path d="M30 18c0-8 6-12 12-10" fill="none" stroke="${EDGE}" stroke-width="5.5"/><path d="M30 18c0-8 6-12 12-10" fill="none" stroke="${STEEL}" stroke-width="3"/><path d="M26 140h8v10h-8z" fill="#C9A44C" stroke="${EDGE}" stroke-width="2"/>`,
  };
  const tool = (k, w = 60, h = 150) => `<svg class="tool" width="${w}" height="${h}" viewBox="0 0 60 150">${TOOLS[k]}</svg>`;

  /* the asks: [question, room id | 'passage', tool] */
  function asks(list, o = {}) {
    return list.map(([q, rid, tl]) => {
      const chip = rid === 'passage'
        ? '<span class="chip pass"><i></i>his shortcut</span>'
        : `<span class="chip"><i style="background:${room(rid).hue}"></i>${esc(room(rid).short.toLowerCase())}</span>`;
      return `<div class="pocket">${tool(tl)}<div class="pk"><div class="q">${esc(q)}</div>${chip}${o.newTool === tl ? '<span class="new">new today</span>' : ''}</div></div>`;
    }).join('');
  }

  window.PRIYA = { tag, tool, asks, hrs, room };
})();
