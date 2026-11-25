"""Film state for Martin's two comps (worlds2 martin-key.html, martin-build.html): window.COMP.render(state) redraws
the frame from a state; with no state (the page load) it draws the approved frame. Run once from the repo root:
python video/v2/film/tools/patch_martin_comps.py"""
import pathlib, re
C = pathlib.Path('video/v2/look/worlds2/comps')

def swap_script(path, new):
    p = C / path
    s = p.read_text(encoding='utf-8')
    i = s.index('<script>\n(function () {')
    j = s.index('</script>', i)
    p.write_text(s[:i] + new + s[j:], encoding='utf-8')

KEY = r"""<script>
(function () {
  const { el, bell, key, esc } = W2, M = MARTIN, S = WORLDS.story.martinKey;
  const svg = document.getElementById('plan');
  const mini = (id, size) => { const s = W2.svg(document.getElementById(id), size, size); bell(s, size / 2, size / 2 + .5, size * .62, M.GOLD_LT); };
  mini('here-bell', 40); mini('say-bell', 40);
  const ck = document.getElementById('card-key');
  el('circle', { cx: 32, cy: 32, r: 29, fill: '#fff', stroke: M.INK, 'stroke-width': 3.5 }, ck); key(ck, 32, 32, 40, M.GOLD);

  const martinEl = document.getElementById('martin'), barnabyEl = document.getElementById('barnaby');
  const card = document.querySelector('.card'), yes = document.getElementById('yes'), when = document.querySelector('.head .when b');
  martinEl.textContent = '“' + S.martin + '”';
  barnabyEl.textContent = S.barnaby;
  document.getElementById('card-title').textContent = S.card.title;
  document.getElementById('card-lines').innerHTML = S.card.lines.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('');
  yes.textContent = S.card.yes; document.getElementById('no').textContent = S.card.no;

  // his walk this morning (canon: the last pair of pads is in drawer 1 of the parts cabinet on the back-office
  // shelf): tomorrow's jobs on the job board (08:53), through the arch and behind the counter into the back office
  // by its door (08:54, the parts drawer), out past the office window to the back door (08:55)
  const ROUTE = [[7.3, 8.05], [7.0, 6.2], [5.75, 5.6], [5.75, 1.65], [8.3, 1.65], [9.3, 2.2], [9.3, 3.95], [14.3, 3.95], [14.3, 7.25], [18.15, 7.25]];
  const seg = ROUTE.slice(1).map((p, i) => Math.hypot(p[0] - ROUTE[i][0], p[1] - ROUTE[i][1])), LEN = seg.reduce((a, b) => a + b, 0);
  const AT_DRAWER = seg.slice(0, 4).reduce((a, b) => a + b, 0) / LEN;        // the walk's fraction at drawer 1 (08:54)
  const MARK = [18.6, 6.95];                                                  // where he stands at the back door

  /* film state (all optional; none = the approved frame, 08:55): walk 0..1 along his route (WALK_AT_DRAWER = at the
     drawer), pads 0..1 the shortfall note, ask 0..1 the key disc, keyRot deg (the key turning), card 0..1 sliding in,
     martin 0..1 his line, say 0..1 Barnaby's line typed, press 0..1 Allow pressed, time 'HH:MM' */
  function render(st) {
    st = st || {};
    const walk = st.walk == null ? 1 : st.walk, pads = st.pads == null ? 1 : st.pads, ask = st.ask == null ? 1 : st.ask;
    svg.innerHTML = '';
    const route = M.cut(ROUTE, walk), here = route[route.length - 1], arr = Math.max(0, Math.min(1, (walk - .985) / .015));
    M.plan(svg, {
      moment: 'martinKey', x: 90, y: 286, s: 60, focus: 'goodsin', built: false, labelSize: 32, pipR: 7,
      labelAt: { shop: [0.5, 6.1], office: [6.78, 2.42], reports: [10.08, 1.42], workshop: [7.0, 4.78], stockroom: [15.32, 4.22], goodsin: [15.32, 6.12] },
      labelLines: { office: ['Back', 'office'] }, labelSizes: { office: 28 },
      standNames: true, standNameSize: 19,
      route, stops: (walk > .012 ? [[7.3, 8.05, '08:53', -82, 0]] : []).concat(walk >= AT_DRAWER ? [[8.3, 1.65]] : []),   // the stamp as he sets off
      keyAsk: [20.02, 7.05], keyR: 40, keyK: ask >= 1 ? undefined : ask, keyRot: st.keyRot || 0,
      marker: walk >= 1 ? MARK : [here[0] + (MARK[0] - ROUTE[9][0]) * arr, here[1] + (MARK[1] - ROUTE[9][1]) * arr], markerR: 30, markerLabel: walk >= .985 ? ['Barnaby', 0, 28] : null,     // his name in white, once he's on the blue
    });
    // the shortfall, stuck on above the back office, pointing at the drawer where he found it
    const T = (x, y) => [90 + x * 60, 286 + y * 60];
    if (pads > 0) {
      const pg = pads < 1 ? el('g', { opacity: Math.min(1, pads * 1.6).toFixed(3) }, svg) : svg;
      const p = T(8.3, 1.65), sx = 452, sy = 186, nw = 344, top = pads < 1 ? p[1] - 9 - (p[1] - 9 - sy - 68) * Math.min(1, pads * 1.4) : sy + 68;
      el('path', { d: `M${p[0]},${p[1] - 9} L${p[0]},${top}`, stroke: M.INK, 'stroke-width': 3 }, pg);
      const k = pads < 1 ? 1 - Math.pow(1 - Math.max(0, (pads - .3) / .7), 3) : 1;
      if (k > 0) {
        const sg = el('g', { transform: `translate(${sx},${sy + (1 - k) * 18}) rotate(-2)` + (k < 1 ? ` translate(${nw / 2},34) scale(${(.9 + .1 * k).toFixed(4)}) translate(${-nw / 2},-34)` : '') }, pg);
        if (k < 1) sg.setAttribute('opacity', k.toFixed(3));
        el('rect', { x: 3, y: 5, width: nw, height: 68, rx: 8, fill: 'rgba(0,0,0,.18)' }, sg);
        el('rect', { x: 0, y: 0, width: nw, height: 68, rx: 8, fill: '#fff', stroke: '#A3261B', 'stroke-width': 2.5 }, sg);
        W2.warn(sg, 26, 34, 28, '#A3261B');
        const nf = { 'font-family': W2.FONT.martin, 'font-size': 22, 'font-weight': 700, fill: '#A3261B' };
        const t1 = W2.text(sg, 52, 29, 'Pads: 1 pair left', nf), x1 = 52 + t1.getComputedTextLength();
        el('circle', { cx: x1 + 12, cy: 22, r: 2.6, fill: '#A3261B' }, sg);
        W2.text(sg, x1 + 24, 29, 'drawer 1', nf);
        W2.text(sg, 52, 55, 'Anika’s brakes need 2', { 'font-family': W2.FONT.martin, 'font-size': 20, fill: M.INK });
        const pl = M.pill(k < 1 ? sg.parentNode : svg, sx + nw + 14, sy + 30, '08:54', { fs: 18 });
        if (k < 1) pl.g.setAttribute('opacity', k.toFixed(3));
      }
    }
    if (walk >= 1) M.pill(svg, ...T(16.9, 6.7), '08:55', { fs: 18 });   // where he is now: the back door
    M.legend(svg, 92, 912, ['can', 'key', 'shut', 'walk', 'asking'], { fs: 21, gap: 38 });
    // the side: Martin's line, Barnaby's (typed as he says it), the card sliding in, Allow pressed
    const say = st.say == null ? 1 : st.say, cardK = st.card == null ? 1 : st.card, press = st.press || 0;
    martinEl.style.opacity = st.martin == null || st.martin >= 1 ? '' : String(st.martin);
    barnabyEl.textContent = say >= 1 ? S.barnaby : S.barnaby.slice(0, Math.round(S.barnaby.length * Math.max(0, say)));
    barnabyEl.parentNode.style.opacity = say > 0 ? '' : '0';
    const ce = 1 - Math.pow(1 - cardK, 3);
    card.style.transform = cardK >= 1 ? '' : `translateX(${((1 - ce) * 560).toFixed(1)}px)`;
    card.style.opacity = cardK >= 1 ? '' : Math.min(1, cardK * 2).toFixed(3);
    yes.style.filter = press > 0 ? `brightness(${(1 - .28 * press).toFixed(3)})` : '';
    yes.style.transform = press > 0 ? `scale(${(1 - .04 * press).toFixed(4)})` : '';
    when.textContent = st.time || S.time;
  }
  window.COMP = { render, AT_DRAWER, yes };
  document.fonts.ready.then(() => { render(); document.body.dataset.ready = '1'; });
})();
"""
swap_script('martin-key.html', KEY)

BUILD = r"""<script>
(function () {
  const { bell, esc } = W2, M = MARTIN, S = WORLDS.story.build;
  const svg = document.getElementById('plan');
  const mini = (id, size) => { const s = W2.svg(document.getElementById(id), size, size); bell(s, size / 2, size / 2 + .5, size * .62, M.GOLD_LT); };
  mini('here-bell', 40); mini('say-bell', 40);
  document.getElementById('martin').textContent = '“' + S.martin + '”';
  document.getElementById('barnaby').textContent = S.after;
  // the report's own result (data/story.js: [name, booked, weekly capacity]); one scale for all three bars
  const max = Math.max(...S.result.map(r => Math.max(r[1], r[2]))), pct = h => (h / max * 100).toFixed(2) + '%';
  const hrs = h => String(h).replace('.5', '½');
  document.getElementById('rows').innerHTML = S.result.map(([n, b, c]) => {
    const over = b > c ? b - c : 0;
    const bar = `<div class="bar"><i style="width:${pct(Math.min(b, c))}"></i>${over ? `<i class="over" style="left:${pct(c)};width:${pct(over)}"></i>` : ''}<u style="left:calc(${pct(c)} - 1.5px)"></u></div>`;
    const v = n === 'Priya' ? `<b>0 h</b> of ${c} · starts tomorrow` : over ? `<b>${hrs(b)} h</b> of ${c} · <span class="over">${hrs(over)} h over</span>` : `<b>${hrs(b)} h</b> of ${c}`;
    return `<div class="n">${esc(n)}</div><div>${bar}<div class="v">${v}</div></div>`;
  }).join('');
  const T0 = S.technical, engine = document.getElementById('engine'), when = document.querySelector('.head .when b');
  const FOOT = `on a copy · ${T0.files.length} files · tests 22 passed   ·   synapse --discover · 24 capabilities`;
  engine.textContent = FOOT;

  /* film only: two other moments of the same side panel, in the page's own card style (hidden unless asked for).
     'card': 16:08-16:16, before the click: Barnaby's explanation card (story.js build.card, "Add it").
     'handback': the afternoon, Sofia's bike: Martin's line, Barnaby's, and the two quick cards from the script
     ("Let Barnaby text customers." "Let Barnaby mark bikes ready."). */
  const side = document.querySelector('.side'), R = WORLDS.ROOMS, room = id => R.find(r => r.id === id);
  const alt = (html, hue) => { const d = document.createElement('div'); d.className = 'side'; d.style.display = 'none'; d.innerHTML = html; side.parentNode.insertBefore(d, side.nextSibling);
    d.querySelectorAll('.bell-dot').forEach(b => { const s = W2.svg(b, 40, 40); bell(s, 20, 20.5, 24.8, M.GOLD_LT); }); return d; };
  const C = S.card;
  const sideCard = alt(`<div class="here" style="background:${room('reports').hue}"><div class="dot bell-dot"></div><div><b>Reports</b><span>planned 2011</span></div></div>
    <div class="who">Martin · 16:08</div><div class="martin-says">“${esc(S.martin)}”</div>
    <div class="card" style="border:3px solid ${room('reports').hue}"><h2 style="color:${room('reports').deep}">${esc(C.title)}</h2>
      <dl>${C.lines.map(([k, v]) => `<div><dt style="color:${room('reports').deep}">${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>
      <div class="btns"><button class="btn yes" style="background:${room('reports').hue};border-color:${room('reports').hue}">${esc(C.yes)}</button><button class="btn">${esc(C.no)}</button></div></div>`);
  const HB = { martin: 'Barnaby, Sofia’s bike’s done.', say: 'I’ll need to text her and mark it ready. May I?',
    cards: [['Let Barnaby text customers', 'shop'], ['Let Barnaby mark bikes ready', 'workshop']] };
  const quick = ([t, r]) => `<div class="card quick" style="border:3px solid ${room(r).hue};padding:20px 24px 22px;margin-top:22px"><h2 style="font-size:28px;color:${room(r).deep}">${esc(t)}</h2>
      <div class="btns" style="margin-top:16px"><button class="btn yes" style="background:${room(r).hue};border-color:${room(r).hue}">Allow</button><button class="btn">Not now</button></div></div>`;
  const sideHB = alt(`<div class="here" style="background:${room('workshop').hue}"><div class="dot bell-dot"></div><div><b>Workshop</b><span>Sofia’s bike, off the stand</span></div></div>
    <div class="who">Martin</div><div class="martin-says">“${esc(HB.martin)}”</div>
    <div class="barnaby-says"><div class="bell bell-dot"></div><div class="hb-say"></div></div>${HB.cards.map(quick).join('')}`);
  const hbSay = sideHB.querySelector('.hb-say'), hbCards = [...sideHB.querySelectorAll('.card')], cardEl = sideCard.querySelector('.card');

  const PASSAGE = [[10.55, 6.22], [6.95, 6.02], [5.05, 4.1]];
  /* film state (all optional; none = the approved frame, 16:16): room 0..1 the Workload room built (0 = "Reports,
     planned 2011", dashed), sticker 0..1 its NEW sticker, passage 0..1 the shortcut drawn, marker [x, y] (plan units)
     or null, route [[x,y]...] + stops (his walk), side 'build' | 'card' | 'handback', card 0..1 sliding in, say 0..1,
     cards 0..2 the quick cards in, press [0..1, 0..1] their Allow (or the card's "Add it") pressed, time, foot */
  function render(st) {
    st = st || {};
    const rk = st.room == null ? 1 : st.room;
    svg.innerHTML = '';
    const base = {
      moment: 'build', x: 90, y: 286, s: 60, labelSize: 32, labelSizes: { reports: 28 }, pipR: 7,
      labelAt: { shop: [0.5, 6.1], office: [6.78, 1.78], reports: [9.97, 1.08], workshop: [7.0, 4.78], stockroom: [15.32, 4.22], goodsin: [15.32, 6.12] },
      standNames: true, standNameSize: 19,
      passage: true, passagePath: PASSAGE, passageW: 18, passageLabel: [10.95, 6.0], passageLabelSize: 20,
      passageK: st.passage == null ? undefined : st.passage,
      route: st.route, stops: st.stops, routeOpacity: st.routeOpacity,
    };
    const mk = st.marker === undefined ? [11.62, 2.3] : st.marker;
    const drawMarker = !(rk >= 1 && st.marker === undefined && st.sticker == null);
    if (rk < 1) {                                   // before: Reports, planned 2011 (the moment's abilities, minus the new one)
      M.plan(svg, Object.assign({}, base, { built: false, focus: null,
        labelAt: Object.assign({}, base.labelAt, { reports: [10.08, 1.42] }), marker: drawMarker ? null : mk }));
    }
    if (rk > 0) {
      const g = rk < 1 ? W2.el('g', { opacity: rk.toFixed(3) }, svg) : svg;
      M.plan(g, Object.assign({}, base, { focus: 'reports', built: true, newSticker: [12.05, 0.12, 7, 100, 44],
        stickerK: st.sticker == null ? undefined : st.sticker, marker: drawMarker ? null : mk, markerR: 27,
        route: rk < 1 ? undefined : base.route }));
    }
    if (drawMarker && mk) {                           // Barnaby on top of whichever plan is up
      const mg = W2.el('g', {}, svg);
      M.plan(mg, { moment: 'build', x: 90, y: 286, s: 60, marker: mk, markerR: 27, labelAt: {}, streets: false, pips: false, wallW: 0, gutter: 0, built: true, onlyMarker: true });
    }
    M.legend(svg, 92, 912, rk >= 1 ? ['can', 'key', 'shut', 'passage', 'new', 'barnaby'] : ['can', 'key', 'shut', 'passage', 'barnaby'], { fs: 21, gap: 36 });
    // the side panel
    const which = st.side || 'build';
    side.style.display = which === 'build' ? '' : 'none';
    sideCard.style.display = which === 'card' ? '' : 'none';
    sideHB.style.display = which === 'handback' ? '' : 'none';
    const press = st.press || [0, 0], ck = st.card == null ? 1 : st.card, ce = 1 - Math.pow(1 - ck, 3);
    const slide = (e, k) => { const q = 1 - Math.pow(1 - Math.max(0, Math.min(1, k)), 3); e.style.transform = k >= 1 ? '' : `translateX(${((1 - q) * 560).toFixed(1)}px)`; e.style.opacity = k >= 1 ? '' : Math.min(1, k * 2).toFixed(3); };
    const pressBtn = (b, k) => { b.style.filter = k > 0 ? `brightness(${(1 - .28 * k).toFixed(3)})` : ''; b.style.transform = k > 0 ? `scale(${(1 - .04 * k).toFixed(4)})` : ''; };
    if (which === 'card') { slide(cardEl, ck); pressBtn(cardEl.querySelector('.yes'), press[0]); }
    if (which === 'handback') {
      const say = st.say == null ? 1 : st.say, n = st.cards == null ? 2 : st.cards;
      hbSay.textContent = HB.say.slice(0, Math.round(HB.say.length * Math.max(0, Math.min(1, say))));
      hbSay.parentNode.style.opacity = say > 0 ? '' : '0';
      hbCards.forEach((c, i) => { slide(c, n - i); pressBtn(c.querySelector('.yes'), press[i] || 0); });
    }
    when.textContent = st.time || '16:16';
    engine.textContent = st.foot == null ? FOOT : st.foot;
  }
  window.COMP = { render, sideCard, sideHB };
  document.fonts.ready.then(() => { render(); document.body.dataset.ready = '1'; });
})();
"""
swap_script('martin-build.html', BUILD)
print('patched martin comps')
