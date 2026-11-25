"""Film engine for the v2.2 shot plan (video/v2/SHOTLIST.md): the push into the screen (corner pin), the room finish
(grain + vignette on room shots only), hard cuts (dissolves only where asked), new world stills by file and size.
Run once from video/v2/film: python tools/patch_engine_v22.py"""
import pathlib

def sub(path, a, b):
    p = pathlib.Path(path); s = p.read_text(encoding='utf-8')
    assert s.count(a) == 1, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

sub('shots.js', """const sizeOf = key => {
  if (key.startsWith('rapp/')) return SIZE['realapp/barnaby-connect.png'];
  return SIZE[key] || [1920, 1080];
};""", """const sizeOf = key => {
  if (key.startsWith('rapp/')) return SIZE['realapp/barnaby-connect.png'];
  const wf = G.WORLD_FILES && key.startsWith('world/') && G.WORLD_FILES[key.slice(6)];
  return wf || SIZE[key] || [1920, 1080];
};
/** The first world still of `keys` that exists on disk (render.js lists ../world/out as window.WORLD_FILES): the
 * Blender agent's new stills swap in when they land, the approved ones stand in until then. */
const pick = (...keys) => { const wf = G.WORLD_FILES; if (!wf) return keys[keys.length - 1]; return keys.find(k => !k.startsWith('world/') || wf[k.slice(6)]) || keys[keys.length - 1]; };
const isRoom = key => key.startsWith('world/');""")

sub('shots.js', """/** A run of shots on one clock. Each shot is fully opaque until the next shot has finished fading in. */
function seq(root, items, end) {
  const list = items.map(it => ({ ...it, s: still(root, it.src, it) }));
  list.forEach((it, i) => {
    const nx = list[i + 1];
    it.end = it.until != null ? it.until : nx ? nx.at + (nx.fi || 0) : end;
    it.bl = blenderFor(it.src, it.at, it.end);
    if (it.bl) { it.blDir = `../world/out/anim/${it.bl.id}/`; it.blN = -1; }
    if (it.build) it.build(it.s.layer, it.s);
  });""", """/** A run of shots on one clock. Each shot is fully opaque until the next shot has finished fading in.
 * The finish (SHOTLIST section 3): hard cuts; a shot's fi is honoured only where dissolves belong (o.dissolves: scene
 * 9 and the titles), for the short crossfade of a push into the screen (pin), or an item's own keepFi. Room shots
 * (world stills and Blender sequences) get the fine grain and the soft vignette; screens and worlds stay clean. */
function seq(root, items, end, o = {}) {
  const list = items.map(it => ({ ...it, s: still(root, it.src, it) }));
  list.forEach(it => {
    if (!o.dissolves && !it.keepFi && !it.pin) it.fi = 0;
    if (it.pin) { it.quad = quadOf(it.pin.shot); if (!it.quad) it.fi = 0; }
  });
  list.forEach((it, i) => {
    const nx = list[i + 1];
    it.end = it.until != null ? it.until : nx ? nx.at + Math.max(nx.fi || 0, nx.quad ? nx.pin.d || .6 : 0) : end;
    it.bl = blenderFor(it.src, it.at, it.end);
    if (it.bl) { it.blDir = `../world/out/anim/${it.bl.id}/`; it.blN = -1; }
    if (isRoom(it.src) && !it.clean) it.finish = finish(it.s.box);
    if (it.build) it.build(it.s.layer, it.s);
  });""")

sub('shots.js', """        } else it.s.place(t, typeof it.cam === 'function' ? it.cam(t, it) : it.cam, it.fit);""",
"""        } else if (it.quad && t < it.at + (it.pin.d || .6)) {          // the push into the screen: pinned, growing
          const u = easeInOutCubic(clamp((t - it.at) / (it.pin.d || .6))), F = [[0, 0], [W, 0], [W, H], [0, H]];
          const q = it.quad.map((p, k) => [lerp(p[0], F[k][0], u), lerp(p[1], F[k][1], u)]);
          it.s.img.style.transform = it.s.layer.style.transform = pinMatrix(q, it.s.w, it.s.h);
        } else it.s.place(t, typeof it.cam === 'function' ? it.cam(t, it) : it.cam, it.fit);
        if (it.finish) it.finish(t);""")

sub('shots.js', """/* ---- the director's camera rules""", """/* ---- the push into the screen: a corner pin onto the monitor's glass (shots.json screen_quad) ---------------- */
function quadOf(id) {
  const m = blenderManifest(); if (!m || !m.shots) return null;
  const sh = m.shots.find(x => x.id === id);
  if (!sh || sh.status !== 'done') return null;
  let q = sh.screen_quad || (sh.screen && sh.screen.quad);
  if (!q) return null;
  if (!Array.isArray(q)) q = [q.tl, q.tr, q.br, q.bl];
  if (q.length !== 4 || q.some(p => !Array.isArray(p) || p.length < 2)) return null;
  const norm = q.every(p => Math.abs(p[0]) <= 1.5 && Math.abs(p[1]) <= 1.5);
  return q.map(p => norm ? [p[0] * W, p[1] * H] : [+p[0], +p[1]]);
}
/** CSS matrix3d taking a w x h box onto the quad [TL, TR, BR, BL] (a projective map, Heckbert's square-to-quad). */
function pinMatrix(q, w, h) {
  const [[x0, y0], [x1, y1], [x2, y2], [x3, y3]] = q;
  const dx1 = x1 - x2, dx2 = x3 - x2, dx3 = x0 - x1 + x2 - x3, dy1 = y1 - y2, dy2 = y3 - y2, dy3 = y0 - y1 + y2 - y3;
  const den = dx1 * dy2 - dx2 * dy1 || 1e-9;
  const g = (dx3 * dy2 - dx2 * dy3) / den, hh = (dx1 * dy3 - dx3 * dy1) / den;
  const a = x1 - x0 + g * x1, b = x3 - x0 + hh * x3, c = x0, d = y1 - y0 + g * y1, e = y3 - y0 + hh * y3, f = y0;
  const m = [a / w, d / w, 0, g / w, b / h, e / h, 0, hh / h, 0, 0, 1, 0, c, f, 0, 1];
  return `matrix3d(${m.map(v => +v.toFixed(8)).join(',')})`;
}

/* ---- the room finish: fine deterministic grain (about 2/255, a new pattern each frame) and a soft vignette --- */
const GRAIN = [];
function grainTiles() {
  if (GRAIN.length) return GRAIN;
  for (let k = 0; k < 6; k++) {
    const c = document.createElement('canvas'); c.width = c.height = 256;
    const x = c.getContext('2d'), im = x.createImageData(256, 256), r = seeded(9001 + k);
    for (let i = 0; i < im.data.length; i += 4) { const v = r() < .5 ? 0 : 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = Math.round(r() * 5); }
    x.putImageData(im, 0, 0); GRAIN.push(c.toDataURL('image/png'));
  }
  return GRAIN;
}
function finish(box) {
  const tiles = grainTiles();
  const vig = el('div', {}, box), gr = el('div', {}, box);
  css(vig, { position: 'absolute', left: '0', top: '0', width: W + 'px', height: H + 'px', zIndex: 40, pointerEvents: 'none',
    background: 'radial-gradient(ellipse 75% 75% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,.12) 100%)' });
  css(gr, { position: 'absolute', left: '0', top: '0', width: W + 'px', height: H + 'px', zIndex: 41, pointerEvents: 'none' });
  let last = null;
  return t => {
    const f = Math.floor(t * FILM_FPS + 1e-6);
    if (f === last) return; last = f;
    gr.style.backgroundImage = `url(${tiles[((f % tiles.length) + tiles.length) % tiles.length]})`;
    gr.style.backgroundPosition = `${Math.floor(rand(f, 31) * 256)}px ${Math.floor(rand(f, 32) * 256)}px`;
  };
}

/* ---- the director's camera rules""")

sub('shots.js', """  cursor, path2, clickK, typed, LIVE_FRAMES: frames, FILM_FPS, hold, move, sfxT, sfxAll, hand, pressAt });""",
"""  cursor, path2, clickK, typed, LIVE_FRAMES: frames, FILM_FPS, hold, move, sfxT, sfxAll, hand, pressAt, pick, quadOf });""")

sub('render.js', """  await p.evaluateOnNewDocument(m => { window.BLENDER = m; }, readBlender());""",
"""  await p.evaluateOnNewDocument((m, wf) => { window.BLENDER = m; window.WORLD_FILES = wf; }, readBlender(), worldFiles());""")
sub('render.js', """// a shot counts as done only if""", """// the world stills on disk, with their pixel sizes (PNG header), so new Blender stills swap in when they land
function worldFiles() {
  const dir = path.resolve(HERE, '../world/out'), out = {};
  for (const f of fs.readdirSync(dir)) {
    if (!/[.]png$/i.test(f)) continue;
    try { const b = Buffer.alloc(24), fd = fs.openSync(path.join(dir, f), 'r'); fs.readSync(fd, b, 0, 24, 0); fs.closeSync(fd); out[f] = [b.readUInt32BE(16), b.readUInt32BE(20)]; } catch (e) { }
  }
  return out;
}
// a shot counts as done only if""")
print('engine patched')
