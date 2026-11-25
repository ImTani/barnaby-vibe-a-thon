"""Film state keys for Theo's hologram comps (worlds2), added minimally; with no state the comps draw exactly the
approved frames. Run once from the repo root: python video/v2/film/tools/patch_theo.py"""
import pathlib
C = pathlib.Path('video/v2/look/worlds2/comps')

def sub(path, a, b, count=1):
    p = C / path
    s = p.read_text(encoding='utf-8')
    assert s.count(a) == count, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

# theo.js: model() may keep only some of the lit endpoints lit (the six lighting up one by one)
sub('lib/theo.js', """      .map(a => o.allFound ? Object.assign({}, a, { state: 'key' }) : a)
""", """      .map(a => o.allFound ? Object.assign({}, a, { state: 'key' }) : a)
      .map(a => o.litOnly && a.state === 'lit' && !o.litOnly.includes(a.tool) ? Object.assign({}, a, { state: 'key' }) : a)
""")
sub('lib/theo.js', """  /* draw the hologram. o: { P (projection), px (px per metre), moment, scanX (reading beat: bricks past it unread),
     fidelity, built, defs } -> { pos: {tool: [x,y] top of brick} } */""",
"""  /* draw the hologram. o: { P (projection), px (px per metre), moment, scanX (reading beat: bricks past it unread),
     fidelity, built, defs, litOnly (film: only these lit ones lit yet) } -> { pos: {tool: [x,y] top of brick} } */""")

# theo-scenes.js: film state for the handover beats (all optional; defaults = the approved frames)
sub('lib/theo-scenes.js', """  function ground(svg, w, h, d, o = {}) {""",
"""  // film state: the first k (0..1) of the characters of a run of lines
  function upto(lines, k) {
    if (k == null || k >= 1) return lines;
    let n = Math.round(lines.join('').length * Math.max(0, k));
    return lines.map(l => { const s = l.slice(0, Math.max(0, n)); n -= l.length; return s; });
  }

  function ground(svg, w, h, d, o = {}) {""")
sub('lib/theo-scenes.js', """  function handoverWide(svg, beat) {
    const w = 1920, h = 1080, d = H.defs(svg), Sh = S.handover, sy = Sh.synapse;
    ground(svg, w, h, d);
    const px = 56, P = T0.projection({ cx: 930, cy: 452, s: px, yaw: -0.36, pitch: 0.6 });
    const reading = beat === 'reading', scanX = 12.7;
""", """  /* film state (optional, defaults = the approved frames): reading: scan (the plane's x; past 20.5 it has read the
     lot), heardK (0..1 of Theo's line); taken: lit (0..6, the six lighting up in turn, fractional = the next fading
     in), sayK (0..1 of his line), counts (0..1 the count line) */
  function handoverWide(svg, beat, fs = {}) {
    const w = 1920, h = 1080, d = H.defs(svg), Sh = S.handover, sy = Sh.synapse;
    ground(svg, w, h, d);
    const px = 56, P = T0.projection({ cx: 930, cy: 452, s: px, yaw: -0.36, pitch: 0.6 });
    const reading = beat === 'reading', scanX = fs.scan == null ? 12.7 : fs.scan;
""")
sub('lib/theo-scenes.js', """    if (reading) text(top, 64, 108, `reading ${sy.repo} …  17 endpoints so far`, { fill: C.amberLine, 'font-size': 16 });""",
"""    const soFar = fs.scan == null ? 17 : W.state('handover').filter(a => a.state !== 'planned' && a.anchor[0] < scanX).length;
    if (reading) text(top, 64, 108, `reading ${sy.repo} …  ${soFar} endpoint${soFar === 1 ? '' : 's'} so far`, { fill: C.amberLine, 'font-size': 16 });""")
sub('lib/theo-scenes.js', """      const tp = H.scan(svg, P, scanX);
      const lg = el('g', {}, svg);
      text(lg, tp[0] + 14, tp[1] + 6, 'reading the workshop', { fill: C.accent, 'font-family': FONT.mono, 'font-size': 18, 'font-weight': 600 });
      H.heard(svg, 120, 900, 'THEO', ['Right. Barnaby, this is the shop’s system. I wrote it when I was', 'fourteen, so be kind. Look after them for me.'], { fs: 27, indent: 96 });
      return;
    }

    // what matters: the six he took, each named once, where it lives
    const m = H.model(svg, { P, px, moment: 'handover', fidelity: 'modest', built: false, defs: d, keyOpacity: .5 });""",
"""      if (scanX < 20.5) {
        const tp = H.scan(svg, P, scanX);
        const lg = el('g', {}, svg);
        text(lg, tp[0] + 14, tp[1] + 6, 'reading the workshop', { fill: C.accent, 'font-family': FONT.mono, 'font-size': 18, 'font-weight': 600 });
      }
      H.heard(svg, 120, 900, 'THEO', upto(['Right. Barnaby, this is the shop’s system. I wrote it when I was', 'fourteen, so be kind. Look after them for me.'], fs.heardK), { fs: 27, indent: 96 });
      return;
    }

    // what matters: the six he took, each named once, where it lives
    const SIX = ['search', 'mechanics', 'parts_low', 'open_jobs', 'jobs_due', 'job_detail'], nLit = fs.lit == null ? 6 : fs.lit;
    const m = H.model(svg, { P, px, moment: 'handover', fidelity: 'modest', built: false, defs: d, keyOpacity: .5, litOnly: SIX.slice(0, Math.ceil(nLit)) });""")
sub('lib/theo-scenes.js', """    for (const tool in place) {
      const [x, y, al] = place[tool], [mth, path] = PATHS[tool];
      H.callout(svg, pos[tool], [x, y], mth, path, { fs: 19, align: al });
    }
    H.counts(svg, 1236, 660, [['lit', '6 taken · read-only'], ['key', '16 need a key'], ['shut', '1 denied']], { fs: 17, gap: 28 });
    H.says(svg, 120, 892, ['Twenty-three endpoints, sir. I’ve taken the six', 'that only read; nobody’s given me any keys yet.'], { fs: 46, lh: 60 });
  }""", """    SIX.forEach((tool, i) => {
      const k = clamp01(nLit - i); if (k <= 0) return;
      const [x, y, al] = place[tool], [mth, path] = PATHS[tool];
      const cg = H.callout(svg, pos[tool], [x, y], mth, path, { fs: 19, align: al });
      if (k < 1) cg.setAttribute('opacity', k.toFixed(3));
    });
    const kc = fs.counts == null ? 1 : clamp01(fs.counts);
    if (kc > 0) { const cg = H.counts(svg, 1236, 660, [['lit', '6 taken · read-only'], ['key', '16 need a key'], ['shut', '1 denied']], { fs: 17, gap: 28 }); if (kc < 1) cg.setAttribute('opacity', kc.toFixed(3)); }
    H.says(svg, 120, 892, upto(['Twenty-three endpoints, sir. I’ve taken the six', 'that only read; nobody’s given me any keys yet.'], fs.sayK), { fs: 46, lh: 60 });
  }
  function clamp01(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }""")
sub('lib/theo-scenes.js', """  function handoverTall(svg, w, h) {""", """  function handoverTall(svg, w, h, fs = {}) {      // film state: lit (0..6 listed so far), sayK (0..1 of his line)""")
sub('lib/theo-scenes.js', """    H.model(svg, { P, px, moment: 'handover', fidelity: 'modest', built: false, defs: d, keyOpacity: .5 });
    // the six, listed once, by room (the model shows where; the list says what)
    const lit = W.state('handover').filter(a => a.state === 'lit');""", """    const lit = W.state('handover').filter(a => a.state === 'lit'), nLit = fs.lit == null ? 6 : fs.lit;
    const order = [['counter'], ['workshop'], ['stockroom']].flatMap(([g]) => lit.filter(x => x.group === g).map(x => x.tool));
    H.model(svg, { P, px, moment: 'handover', fidelity: 'modest', built: false, defs: d, keyOpacity: .5, litOnly: order.slice(0, Math.ceil(nLit)) });
    // the six, listed once, by room (the model shows where; the list says what)""")
sub('lib/theo-scenes.js', """      for (const a of lit.filter(x => x.group === gid)) {
        const [mth, path] = PATHS[a.tool];
        el('rect', { x: 18, y: y - 8.5, width: 8.5, height: 8.5, fill: C.white }, svg);
        text(svg, 36, y, mth, { 'font-family': FONT.mono, 'font-size': 10, fill: C.mute });
        text(svg, 64, y, path, { 'font-family': FONT.mono, 'font-size': 12, 'font-weight': 600, fill: C.white });
        y += 16;
      }""", """      for (const a of lit.filter(x => x.group === gid)) {
        const [mth, path] = PATHS[a.tool], k = clamp01(nLit - order.indexOf(a.tool));
        const row = el('g', k < 1 ? { opacity: k.toFixed(3) } : {}, svg);
        el('rect', { x: 18, y: y - 8.5, width: 8.5, height: 8.5, fill: C.white }, row);
        text(row, 36, y, mth, { 'font-family': FONT.mono, 'font-size': 10, fill: C.mute });
        text(row, 64, y, path, { 'font-family': FONT.mono, 'font-size': 12, 'font-weight': 600, fill: C.white });
        y += 16;
      }""")
sub('lib/theo-scenes.js', """    H.says(svg, 14, h - 80, ['Twenty-three endpoints, sir.', 'I’ve taken the six that only read;', 'nobody’s given me any keys yet.'], { fs: 19, lh: 25 });""",
"""    H.says(svg, 14, h - 80, upto(['Twenty-three endpoints, sir.', 'I’ve taken the six that only read;', 'nobody’s given me any keys yet.'], fs.sayK), { fs: 19, lh: 25 });""")

# the comps: window.COMP.render(state) redraws from the state (film use); the page load draws the approved frame
for name, beat in (('theo-handover-1-reading.html', 'reading'), ('theo-handover-2-taken.html', 'taken')):
    sub(name, f"""<script>document.fonts.ready.then(() => {{ THEO_SCENES.handoverWide(document.getElementById('s'), '{beat}'); document.body.dataset.ready = '1'; }});</script>""",
        f"""<script>
// film use: COMP.render(state) redraws the frame from its state (lib/theo-scenes.js handoverWide); no state = this frame
window.COMP = {{ render(st) {{ const s = document.getElementById('s'); s.innerHTML = ''; THEO_SCENES.handoverWide(s, '{beat}', st || {{}}); }} }};
document.fonts.ready.then(() => {{ COMP.render(); document.body.dataset.ready = '1'; }});</script>""")
sub('theo-handover-pc.html', """    const svg = W2.svg(c, w, h);
    THEO_SCENES.handoverTall(svg, w, h);
    document.body.dataset.ready = '1';""", """    const svg = W2.svg(c, w, h);
    // film use: COMP.render(state) redraws Barnaby's window from its state (handoverTall: lit, sayK); no state = this frame
    window.COMP = { render(st) { svg.innerHTML = ''; THEO_SCENES.handoverTall(svg, w, h, st || {}); } };
    COMP.render();
    document.body.dataset.ready = '1';""")
print('patched')
