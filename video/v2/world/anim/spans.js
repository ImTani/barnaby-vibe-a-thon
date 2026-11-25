// Resolve every world/ still's on-screen span from the animatic scene files and cues.json (read-only).
// node video/v2/world/anim/spans.js  -> JSON list of {scene, i, src, at, fi, end, cam}
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
const CUES = JSON.parse(fs.readFileSync(path.join(ROOT, 'cues.json'), 'utf8'));
const V = n => CUES.voice[n - 1].speech[0], VE = n => CUES.voice[n - 1].speech[1];
const M = k => { const v = CUES.marks[k]; if (v == null) throw new Error('no mark ' + k); return v; };
const out = [];
let scene = 0;
const noop = new Proxy(function () {}, { get: () => noop, apply: () => noop });
const env = new Proxy({ CUES, V, VE, M, Math, JSON, Number, String, Array, Object, console,
  Scene: o => o.build(noop),
  seq: (root, items, end) => {
    items.forEach((it, i) => {
      const nx = items[i + 1];
      const e = it.until != null ? it.until : nx ? nx.at + (nx.fi || 0) : end;
      out.push({ scene, i, src: it.src, at: +it.at.toFixed(3), fi: it.fi || 0, end: +e.toFixed(3), cam: it.cam });
    });
    return noop;
  } }, { has: () => true, get: (t, k) => (k in t ? t[k] : k === Symbol.unscopables ? undefined : noop) });
for (let s = 1; s <= 9; s++) {
  scene = s;
  const src = fs.readFileSync(path.join(ROOT, 'animatic', 'scenes', `s${s}.js`), 'utf8');
  new Function('env', `with (env) { ${src} }`)(env);
}
console.log(JSON.stringify(out.filter(o => o.src.startsWith('world/')), null, 0).replace(/\},\{/g, '},\n{'));
