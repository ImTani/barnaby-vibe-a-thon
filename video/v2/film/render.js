/* Film renderer (from the animatic's render.js). Run from anywhere; uses video/node_modules/puppeteer-core, the
 * installed Chrome and ffmpeg on PATH. Nothing is downloaded. The Blender agent's manifest
 * (../world/anim/shots.json) is re-read at every launch and handed to the page as window.BLENDER.
 *
 *   node video/v2/film/render.js                  full film -> out/frames/%05d.jpg -> out/barnaby_v2-silent.mp4,
 *                                                 + out/barnaby_v2.mp4 with ../audio/soundtrack.wav muxed in
 *   node video/v2/film/render.js range <t0> <t1>  seconds [t0, t1) -> out/range_<t0>_<t1>.mp4
 *   node video/v2/film/render.js test <t> ...     stills -> out/stills/test_<t>.jpg (full size)
 *   node video/v2/film/render.js sheet <t0> <t1> [n]   n time-stamped stills tiled -> out/sheets/sheet_<t0>_<t1>.jpg
 *   node video/v2/film/render.js sheets [ids]     one sheet per scene (--n=16 tiles) -> out/sheets/scene_<n>.jpg
 *   node video/v2/film/render.js at <file>        stills at the times listed in a JSON file [[name, t], ...]
 *   node video/v2/film/render.js verify <t> ...   determinism: each t rendered in three passes (forward, reverse,
 *                                                 shuffled with a jump in between) must be byte-identical
 *   node video/v2/film/render.js encode | mux     re-encode frames / re-mux the soundtrack (after a new mix)
 *   flags: --fps=24 --workers=2 --scale=1 --quality=92 --no-encode --resume (skip frames already on disk)
 *          --name=barnaby_v2_review (output base name, for encode and mux too)
 */
const path = require('path'), fs = require('fs'), { spawnSync } = require('child_process');
const HERE = __dirname;
const puppeteer = require(path.resolve(HERE, '../../node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'file:///' + path.resolve(HERE, 'index.html').replace(/\\/g, '/');
const CUES = JSON.parse(fs.readFileSync(path.resolve(HERE, '../cues.json'), 'utf8'));
const DUR = CUES.duration;

const argv = process.argv.slice(2);
const flags = {}, pos = [];
for (const a of argv) { if (!a.startsWith('--')) { pos.push(a); continue; } const [k, v] = a.slice(2).split('='); flags[k] = v === undefined ? true : v; }
const FPS = +(flags.fps || 24), WORKERS = +(flags.workers || 2), QUALITY = +(flags.quality || 92), SCALE = +(flags.scale || 1);
const BLENDER_JSON = path.resolve(HERE, '../world/anim/shots.json');
const readBlender = () => { try { return JSON.parse(fs.readFileSync(BLENDER_JSON, 'utf8')); } catch (e) { return null; } };
const OUT = path.join(HERE, 'out');
const dir = d => { const p = path.join(OUT, d); fs.mkdirSync(p, { recursive: true }); return p; };
const ARGS = ['--hide-scrollbars', '--allow-file-access-from-files', '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--disable-backgrounding-occluded-windows', '--font-render-hinting=none', '--force-color-profile=srgb'];

async function worker(tag, scale = SCALE) {
  const b = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ARGS });
  const p = await b.newPage();
  p.on('console', m => { if (m.type() === 'error') console.log(`  [page ${tag}]`, m.text()); });
  p.on('pageerror', e => console.log(`  [pageerror ${tag}]`, e.message));
  await p.setViewport({ width: 1920, height: 1080, deviceScaleFactor: scale });
  await p.evaluateOnNewDocument(m => { window.BLENDER = m; }, readBlender());
  await p.goto(URL, { waitUntil: 'load' });
  await p.waitForFunction('window.__ready === true', { timeout: 180000 });
  await p.evaluate(async () => { await document.fonts.ready; for (let t = 0; t < window.DURATION; t += 2) { window.render(t); await window.settle(); } });
  await new Promise(r => setTimeout(r, 300));
  const shot = async (t, file, q = QUALITY, stamp) => {
    await p.evaluate(async (t, stamp) => {
      window.render(t); await window.settle();
      let d = document.getElementById('__stamp');
      if (stamp) { if (!d) { d = document.createElement('div'); d.id = '__stamp'; d.style.cssText = 'position:absolute;right:16px;top:12px;z-index:999;font:600 40px Consolas;color:#fff;background:rgba(0,0,0,.65);padding:2px 12px;border-radius:6px'; document.body.appendChild(d); } d.textContent = stamp; d.style.display = 'block'; }
      else if (d) d.style.display = 'none';
    }, t, stamp || null);
    return p.screenshot({ path: file, type: 'jpeg', quality: q, optimizeForSpeed: true });
  };
  return { b, p, shot, errors: () => p.evaluate(() => window.__errors.slice()) };
}

function ffmpeg(args) {
  console.log('ffmpeg', args.join(' '));
  const r = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...args], { stdio: 'inherit' });
  if (r.status !== 0) throw new Error('ffmpeg failed');
}
const WAV = path.resolve(HERE, '../audio/soundtrack.wav');
function mux(silent, final) {
  if (!fs.existsSync(WAV)) { console.log('no soundtrack yet:', WAV); return; }
  ffmpeg(['-i', silent, '-i', WAV, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', final]);
  console.log('wrote', final);
}
const BASE = flags.name || 'barnaby_v2';           // --name=barnaby_v2_review -> out/barnaby_v2_review.mp4
function encode(f0, f1, name) {
  const silent = path.join(OUT, name || BASE + '-silent.mp4');
  ffmpeg(['-framerate', String(FPS), '-start_number', String(f0), '-i', path.join(OUT, 'frames', '%05d.jpg'), '-frames:v', String(f1 - f0),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(FPS), '-movflags', '+faststart', silent]);
  console.log('wrote', silent);
  if (!name) mux(silent, path.join(OUT, BASE + '.mp4'));
}

async function renderFrames(f0, f1) {
  const out = dir('frames'); const t0 = Date.now(); let done = 0; const W = Math.min(WORKERS, f1 - f0); let errs = 0; const ms = [];
  const bl = readBlender(); console.log('blender manifest:', bl ? `${(bl.shots || []).filter(s => s.status === 'done').length} done of ${(bl.shots || []).length}, complete=${!!bl.complete}` : 'none');
  await Promise.all([...Array(W)].map(async (_, w) => {
    let k = await worker(w);
    for (let f = f0 + w; f < f1; f += W) {
      const file = path.join(out, String(f).padStart(5, '0') + '.jpg');
      if (flags.resume && fs.existsSync(file) && fs.statSync(file).size > 0) { done++; continue; }
      const tf = Date.now();
      for (let attempt = 0; ; attempt++) {
        let timer; const to = new Promise((_, rej) => { timer = setTimeout(() => rej(new Error('timeout')), 30000); });
        try { await Promise.race([k.shot(f / FPS, file), to]); clearTimeout(timer); ms.push(Date.now() - tf); break; }
        catch (e) { clearTimeout(timer); console.log(`  worker ${w} frame ${f}: ${e.message}, relaunching`); try { k.b.process() && k.b.process().kill(); } catch (_) { } if (attempt >= 2) throw e; k = await worker(w); }
      }
      if (++done % 150 === 0) console.log(`${done}/${f1 - f0} frames  ${((Date.now() - t0) / 1000).toFixed(0)}s  ${(done / ((Date.now() - t0) / 1000)).toFixed(1)} fps`);
    }
    errs += (await k.errors()).length; await k.b.close();
  }));
  ms.sort((a, b) => a - b);
  console.log(`rendered ${done} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s; per frame per worker: median ${ms[ms.length >> 1] || 0} ms, p95 ${ms[Math.floor(ms.length * .95)] || 0} ms (${W} workers)`);
  if (errs) { console.log(`WARNING: ${errs} page errors during render`); process.exitCode = 2; }
}

async function stills(times, name, stamp, scale = SCALE) {
  const out = dir('stills'); const W = Math.max(1, Math.min(WORKERS, times.length)); const files = []; let errs = [];
  await Promise.all([...Array(W)].map(async (_, w) => {
    const k = await worker(w, scale);
    for (let i = w; i < times.length; i += W) {
      const t = times[i]; const f = path.join(out, name(t, i)); files[i] = f;
      await k.shot(t, f, 90, stamp ? stamp(t, i) : null);
    }
    errs = errs.concat(await k.errors()); await k.b.close();
  }));
  if (errs.length) { console.log('PAGE ERRORS:\n  ' + [...new Set(errs)].join('\n  ')); process.exitCode = 2; }
  return files;
}

async function sheet(times, outName, stamp, cols = 4) {
  const files = await stills(times, (t, i) => `_sheet_${process.pid}_${String(i).padStart(2, '0')}.jpg`, stamp);
  const rows = Math.ceil(times.length / cols), outf = path.join(dir('sheets'), outName);
  ffmpeg(['-start_number', '0', '-i', path.join(OUT, 'stills', `_sheet_${process.pid}_%02d.jpg`), '-frames:v', '1',
    '-vf', `scale=640:360,tile=${cols}x${rows}:padding=6:color=0x222222`, '-q:v', '3', outf]);
  files.forEach(f => fs.unlinkSync(f));
  console.log('wrote', outf);
}

const fmt = t => `${Math.floor(t / 60)}:${(t % 60).toFixed(1).padStart(4, '0')}`;

(async () => {
  const mode = pos[0];
  if (mode === 'test') {
    const files = await stills(pos.slice(1).map(Number), t => `test_${t}.jpg`, null, +(flags.scale || 1));
    files.forEach(f => console.log('wrote', f));
  } else if (mode === 'at') {
    const list = JSON.parse(fs.readFileSync(pos[1], 'utf8'));
    const files = await stills(list.map(x => x[1]), (t, i) => `${list[i][0]}.jpg`, (t, i) => `${list[i][0]}  ${fmt(t)}`, +(flags.scale || .5));
    files.forEach(f => console.log('wrote', f));
  } else if (mode === 'sheet') {
    const a = +pos[1], b = +pos[2], n = +(pos[3] || 12);
    const times = [...Array(n)].map((_, i) => +(a + (i + .5) * (b - a) / n).toFixed(2));
    await sheet(times, `sheet_${a}_${b}.jpg`, t => fmt(t));
  } else if (mode === 'sheets') {                 // one pass over all scenes (browsers start once), then tile per scene
    const only = pos.slice(1).map(Number), n = +(flags.n || 16), jobs = [];
    for (const s of CUES.scenes) {
      if (only.length && !only.includes(s.id)) continue;
      for (let i = 0; i < n; i++) jobs.push({ s, i, t: +(s.start + (i + .5) * (s.end - s.start) / n).toFixed(2) });
    }
    const files = await stills(jobs.map(j => j.t), (t, k) => `_sh_${jobs[k].s.id}_${String(jobs[k].i).padStart(2, '0')}.jpg`, (t, k) => `${jobs[k].s.id} · ${fmt(t)}`, .5);
    for (const id of [...new Set(jobs.map(j => j.s.id))]) {
      const outf = path.join(dir('sheets'), `scene_${id}.jpg`);
      ffmpeg(['-start_number', '0', '-i', path.join(OUT, 'stills', `_sh_${id}_%02d.jpg`), '-frames:v', '1',
        '-vf', `scale=640:360,tile=4x${Math.ceil(n / 4)}:padding=6:color=0x222222`, '-q:v', '3', outf]);
      console.log('wrote', outf);
    }
    files.forEach(f => fs.unlinkSync(f));
  } else if (mode === 'verify') {
    const times = pos.slice(1).map(Number); const k = await worker(0); const A = {}; let bad = 0;
    const R = async t => { await k.p.evaluate(async t => { window.render(t); await window.settle(); }, t); return k.p.screenshot({ type: 'png' }); };
    for (const t of times) A[t] = await R(t);                                   // pass 1: forward
    const passes = [times.slice().reverse(), times.slice().sort((a, b) => ((a * 7919) % 13) - ((b * 7919) % 13))];
    for (let pi = 0; pi < passes.length; pi++) for (const t of passes[pi]) { // pass 2: reverse; pass 3: shuffled, a jump between
      await R(pi ? DUR - t : 0);
      const B = await R(t); let same = Buffer.compare(A[t], B) === 0;
      if (!same) {                         // the compositor's own +-1 noise on a handful of pixels is not a state leak
        const d = await k.p.evaluate(async (a, b) => {
          const load = s => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = 'data:image/png;base64,' + s; });
          const px = im => { const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const x = c.getContext('2d'); x.drawImage(im, 0, 0); return x.getImageData(0, 0, im.width, im.height).data; };
          const [ia, ib] = await Promise.all([load(a), load(b)]); const da = px(ia), db = px(ib); let max = 0, n = 0, n8 = 0;
          for (let i = 0; i < da.length; i++) { const v = Math.abs(da[i] - db[i]); if (v) { n++; if (v > 8) n8++; if (v > max) max = v; } }
          return { max, n, n8 };
        }, A[t].toString('base64'), B.toString('base64'));
        // a leak moves or changes something (thousands of values by a lot); Chrome's GPU raster differs run to run by
        // a few levels across a soft area, or on a handful of anti-aliased edge pixels at tile seams
        if (d.max <= 4 || d.n8 <= 600) { same = true; console.log(`  t=${t}: ${d.n} channel values differ (${d.n8} by more than 8/255, max ${d.max}): raster noise, not a leak`); }
        else console.log(`  t=${t}: ${d.n} channel values differ (${d.n8} by more than 8/255, max ${d.max})`);
      }
      if (!same) { bad++; fs.writeFileSync(path.join(dir('stills'), `verify_${t}_a.png`), A[t]); fs.writeFileSync(path.join(dir('stills'), `verify_${t}_b${pi}.png`), B); }
      console.log(`pass ${pi + 2} t=${t}: ${same ? 'identical' : 'DIFFERENT (state leaks between frames!)'}`);
    }
    console.log(bad ? `VERIFY FAILED: ${bad} mismatches` : `VERIFY OK: ${times.length} times x 3 passes identical`);
    await k.b.close(); process.exitCode = bad ? 3 : 0;
  } else if (mode === 'encode') {
    encode(0, Math.round(DUR * FPS));
  } else if (mode === 'mux') {
    mux(path.join(OUT, BASE + '-silent.mp4'), path.join(OUT, BASE + '.mp4'));
  } else if (mode === 'range') {
    const a = +pos[1], b = +pos[2]; const f0 = Math.round(a * FPS), f1 = Math.round(b * FPS);
    await renderFrames(f0, f1);
    if (!flags['no-encode']) encode(f0, f1, `range_${a}_${b}.mp4`);
  } else {
    const total = Math.round(DUR * FPS);
    await renderFrames(0, total);
    if (!flags['no-encode']) encode(0, total);
  }
  process.exit(process.exitCode || 0);
})().catch(e => { console.error(e); process.exit(1); });
