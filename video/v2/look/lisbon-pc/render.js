/* Lisbon desk stills. Run from anywhere:   node video/v2/look/lisbon-pc/render.js [filter ...]
 *
 *   (no args)        every state x monitor: panels (main/studio 2560x1440, laptop 1920x1200) + 1920x1080 cut-ins,
 *                    and one review sheet per state (the three screens together)
 *   <filter ...>     only stills whose name contains a filter, e.g.  quorum   main   rest-studio
 *   sheet            only the review sheets
 *   verify           purity check: every preset renders identically after rendering another one in between
 *   realapp          re-capture the REAL Barnaby app: starts `python -m barnaby serve` (.venv) on a fresh temp
 *                    BARNABY_STATE (no systems), opens its Capabilities panel and types Quorum into "Connect a repo"
 *                    (not submitted), screenshots at the browser tile's size (712x638 at 80% zoom, 2x) into
 *                    realapp/barnaby-connect.png (+ -empty.png before typing), stops the server, deletes the temp dir
 *   zoom "<query>" x,y,w,h out.png    a 2x crop of a 1280x720 render, for detail checks
 * Uses video/node_modules/puppeteer-core and the installed Chrome. Nothing is downloaded. */
const fs = require('fs');
const path = require('path');
const http = require('http');
const os = require('os');
const { spawn, execFileSync } = require('child_process');

const HERE = __dirname;
const VIDEO = path.resolve(HERE, '../../..');
const ROOT = path.resolve(VIDEO, '..');
const OUT = path.resolve(HERE, '../frames');
const puppeteer = require(path.join(VIDEO, 'node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL0 = 'file:///' + path.join(HERE, 'index.html').replace(/\\/g, '/');

const STATES = [['01', 'rest'], ['02', 'realapp'], ['03', 'quorum'], ['03b', 'quorum-theo'], ['04', 'comfy'], ['05', 'night']];
const MONITORS = ['main', 'studio', 'laptop'];
function stills() {
  const list = [];
  for (const [nn, st] of STATES) for (const m of MONITORS) {
    const panel = m === 'laptop' ? { lw: 1280, lh: 800, dsf: 1.5 } : { lw: 1280, lh: 720, dsf: 2 };
    list.push({ name: `lisbon-${nn}-${st}-${m}`, qs: `monitor=${m}&state=${st}&lw=${panel.lw}&lh=${panel.lh}`, ...panel });
    list.push({ name: `lisbon-${nn}-${st}-${m}-1080`, qs: `monitor=${m}&state=${st}`, lw: 1280, lh: 720, dsf: 1.5 });
  }
  list.push({ name: 'lisbon-06-slot-main', qs: 'monitor=main&state=slot', lw: 1280, lh: 720, dsf: 2 });
  list.push({ name: 'lisbon-06-frame-main-1080', qs: 'monitor=main&state=frame', lw: 1280, lh: 720, dsf: 1.5 });
  return list;
}

async function shoot(page, qs, lw, lh, dsf, out) {
  await page.setViewport({ width: lw, height: lh, deviceScaleFactor: dsf });
  await page.goto(`${URL0}?${qs}`, { waitUntil: 'load' });
  await page.waitForSelector('body[data-ready="1"]', { timeout: 15000 });
  await new Promise(r => setTimeout(r, 80));
  return page.screenshot(out ? { path: out } : { encoding: 'base64' });
}

/** One review sheet per state: main and studio side by side (as on the desk), the laptop below. 1920 wide. */
async function sheets(page) {
  for (const [nn, st] of STATES) {
    const a = await shoot(page, `monitor=main&state=${st}`, 1280, 720, .75);
    const b = await shoot(page, `monitor=studio&state=${st}`, 1280, 720, .75);
    const c = await shoot(page, `monitor=laptop&state=${st}&lw=1280&lh=800`, 1280, 800, .5);
    await page.setViewport({ width: 1920, height: 1040, deviceScaleFactor: 1 });
    await page.setContent(`<body style="margin:0;background:#2b2622;font:600 15px Segoe UI;color:#e8dcc8">
      <div style="display:flex;gap:0;padding:0"><img src="data:image/png;base64,${a}" style="width:960px"><img src="data:image/png;base64,${b}" style="width:960px"></div>
      <div style="display:flex;gap:24px;align-items:flex-start;padding:14px 20px"><img src="data:image/png;base64,${c}" style="width:640px;border:6px solid #111;border-radius:6px">
      <div style="padding-top:8px;line-height:1.6">${st} · main (DP-1) · studio (DP-2) · laptop (eDP-1, docked)</div></div></body>`);
    const out = path.join(OUT, `lisbon-00-sheet-${nn}-${st}.png`);
    await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1920, height: 1040 } });
    console.log(out);
  }
}

/** The film's rule: render() is a pure function of state. For each preset A: render A, then B (every animatable value
 * pushed off its default), then A again, in the same page. A leak is any pixel more than 32/255 off (the shop PC's
 * rule); below that it's antialiasing from layers that a dimmed (filtered) frame promoted. */
async function verify(page) {
  const names = ['rest', 'realapp', 'quorum', 'quorum-theo', 'comfy', 'night', 'slot', 'frame'];
  let bad = 0;
  for (const m of MONITORS) for (let i = 0; i < names.length; i++) {
    const a = names[i], b = names[(i + 2) % names.length];
    await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1 });
    await page.goto(`${URL0}?monitor=${m}&state=${a}`, { waitUntil: 'load' });
    await page.waitForSelector('body[data-ready="1"]', { timeout: 15000 });
    await page.evaluate(a => desk.render(LX.preset(a)), a);
    const first = await page.screenshot({ encoding: 'base64' });
    await page.evaluate((a, b) => {
      desk.render(LX.preset(b, { out: 3, split: .5, type: .5, sayK: .3, planK: .6, app: .5, queueOpen: .4, queueHl: .7, step: 3, gpu: .2, vram: 9, frame: 7, lapIn: .5, qHl: .6, dim: .3, tick: 1, day: 2, edTop: 5, blink: 0, level: .9, secs: 11 }));
      desk.render(LX.preset(a));
    }, a, b);
    const again = await page.screenshot({ encoding: 'base64' });
    const r = await page.evaluate(async (x, y) => {
      const load = s => new Promise(res => { const im = new Image(); im.onload = () => res(im); im.src = 'data:image/png;base64,' + s; });
      const [ia, ib] = await Promise.all([load(x), load(y)]);
      const c = document.createElement('canvas'); c.width = ia.width; c.height = ia.height; const g = c.getContext('2d');
      g.drawImage(ia, 0, 0); const A = g.getImageData(0, 0, c.width, c.height).data; g.drawImage(ib, 0, 0); const B = g.getImageData(0, 0, c.width, c.height).data;
      let n = 0, mx = 0, big = 0;
      for (let k = 0; k < A.length; k += 4) { const d = Math.max(Math.abs(A[k] - B[k]), Math.abs(A[k + 1] - B[k + 1]), Math.abs(A[k + 2] - B[k + 2])); if (d) { n++; if (d > 32) big++; if (d > mx) mx = d; } }
      return { n, mx, big };
    }, first, again);
    if (r.big) { bad++; fs.writeFileSync(path.join(OUT, `_verify_${m}_${a}_a.png`), Buffer.from(first, 'base64')); fs.writeFileSync(path.join(OUT, `_verify_${m}_${a}_b.png`), Buffer.from(again, 'base64')); }
    console.log(`${r.big ? 'LEAK' : r.n ? 'ok~ ' : 'ok  '} ${m} ${a} (via ${b})  ${r.n} px differ, max ${r.mx}/255, ${r.big} over 32`);
  }
  console.log(bad ? `${bad} state(s) leaked` : 'no leaks: every preset is a function of its state');
}

/* ---- the real app ------------------------------------------------------------------------------------------------ */
function get(url) { return new Promise(res => { const rq = http.get(url, r => { r.resume(); res(r.statusCode); }); rq.on('error', () => res(0)); rq.setTimeout(1000, () => { rq.destroy(); res(0); }); }); }
async function realapp(browser) {
  // Theo's own fresh Barnaby: a brand-new state dir (no systems yet), the UI exactly as it ships, its Capabilities
  // panel open and "Connect a repo" filled in the way Theo would type it. Nothing is submitted.
  const APP = 'http://127.0.0.1:8700/';
  if (await get(APP)) throw new Error('something is already on :8700; not starting another server');
  const state = fs.mkdtempSync(path.join(os.tmpdir(), 'barnaby-state-'));
  const py = path.join(ROOT, '.venv/Scripts/python.exe');
  const srv = spawn(py, ['-m', 'barnaby', 'serve'], { cwd: ROOT, env: { ...process.env, BARNABY_STATE: state }, stdio: 'ignore', windowsHide: true });
  console.log('started barnaby serve, pid', srv.pid, 'BARNABY_STATE', state);
  try {
    let up = 0;
    for (let i = 0; i < 100 && !up; i++) { up = await get(APP); if (!up) await new Promise(r => setTimeout(r, 300)); }
    if (!up) throw new Error('barnaby serve did not come up');
    const page = await browser.newPage();
    // the browser tile's page area is 712x638 logical; Theo's browser is at 80% zoom (CSS 890x798), rendered 2x
    await page.setViewport({ width: 890, height: 798, deviceScaleFactor: 1.6 });
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
    await page.goto(APP, { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 800));
    const systems = await page.evaluate(async () => (await (await fetch('/api/state')).json()).systems.length);
    if (systems) throw new Error(`expected a fresh registry, found ${systems} system(s)`);
    fs.mkdirSync(path.join(HERE, 'realapp'), { recursive: true });
    await page.click('#toggle-map');
    await new Promise(r => setTimeout(r, 300));
    await page.screenshot({ path: path.join(HERE, 'realapp', 'barnaby-connect-empty.png') });
    await page.type('#connect-form input[name="name"]', 'quorum', { delay: 40 });
    await page.type('#connect-form input[name="repo"]', '/home/theo/crew/quorum', { delay: 30 });
    await page.type('#connect-form input[name="base_url"]', 'http://localhost:8001', { delay: 30 });
    await new Promise(r => setTimeout(r, 400));
    const out = path.join(HERE, 'realapp', 'barnaby-connect.png');
    await page.screenshot({ path: out });
    console.log(out, '(and barnaby-connect-empty.png)');
    await page.close();
  } finally {
    try { execFileSync('taskkill', ['/PID', String(srv.pid), '/T', '/F'], { stdio: 'ignore' }); } catch (e) { srv.kill(); }
    await new Promise(r => setTimeout(r, 800));
    console.log('stopped barnaby serve;', (await get(APP)) ? 'STILL ANSWERING' : ':8700 closed');
    fs.rmSync(state, { recursive: true, force: true });
  }
}

(async () => {
  let want = process.argv.slice(2);
  const zoom = want[0] === 'zoom' ? { qs: want[1], clip: want[2].split(',').map(Number), out: want[3] } : null;
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true,
    args: ['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none', '--allow-file-access-from-files'] });
  const page = await browser.newPage();
  let errors = 0;
  page.on('pageerror', e => { errors++; console.error('page error:', e.message); });
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.error('console:', m.text()); });
  try {
    if (want[0] === 'realapp') return await realapp(browser);
    if (want[0] === 'verify') return await verify(page);
    if (zoom) {
      const [x, y, width, height] = zoom.clip;
      await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 2 });
      await page.goto(`${URL0}?${zoom.qs}`, { waitUntil: 'load' });
      await page.waitForSelector('body[data-ready="1"]', { timeout: 15000 });
      await page.screenshot({ path: path.resolve(zoom.out), clip: { x, y, width, height } });
      console.log(path.resolve(zoom.out));
      return;
    }
    const onlySheet = want.length === 1 && want[0] === 'sheet';
    if (!onlySheet) {
      const list = want.length ? stills().filter(s => want.some(w => s.name.includes(w))) : stills();
      for (const s of list) {
        const out = path.join(OUT, s.name + '.png');
        await shoot(page, s.qs, s.lw, s.lh, s.dsf, out);
        console.log(out);
      }
    }
    if (!want.length || onlySheet) await sheets(page);
  } finally {
    await browser.close();
  }
  process.exit(errors ? 2 : 0);
})().catch(e => { console.error(e); process.exit(1); });
