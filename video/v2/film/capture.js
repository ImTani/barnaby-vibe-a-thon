/* The REAL Barnaby app, typed into, for scene 8 (the film's only capture; everything else runs live). Same set-up as
 * look/lisbon-pc/render.js realapp: `python -m barnaby serve` (.venv) on a fresh temp BARNABY_STATE (no systems),
 * its Capabilities panel open, at the browser tile's size (890x798 CSS at 1.6x = 1424x1277, as realapp/*.png).
 * Writes assets/realapp/ (gitignored, regenerable): base.jpg (the whole app, empty form, nothing focused) and
 * f_NNN.jpg, the Connect form region only (FORM below) after each step: the click into Name, each key Theo types
 * (quorum · /home/theo/crew/quorum · http://localhost:8001), the clicks into the next field, the pointer over
 * Connect (hover) and the button held down (pressed). Nothing is submitted: the page closes with the button still
 * down, the server is stopped and the temp state deleted. manifest.json lists the steps.
 *   node video/v2/film/capture.js
 * Uses video/node_modules/puppeteer-core, the installed Chrome and the repo's .venv. Nothing is downloaded. */
const fs = require('fs'), path = require('path'), http = require('http'), os = require('os');
const { spawn, execFileSync } = require('child_process');
const HERE = __dirname, VIDEO = path.resolve(HERE, '../..'), ROOT = path.resolve(VIDEO, '..');
const puppeteer = require(path.join(VIDEO, 'node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const OUT = path.join(HERE, 'assets', 'realapp');
const APP = 'http://127.0.0.1:8700/';
const FORM = { x: 700, y: 400, width: 724, height: 440 };      // device px of the 1424x1277 capture (CSS / 1.6)
const FIELDS = [['name', 'quorum'], ['repo', '/home/theo/crew/quorum'], ['base_url', 'http://localhost:8001']];

function get(url) { return new Promise(res => { const rq = http.get(url, r => { r.resume(); res(r.statusCode); }); rq.on('error', () => res(0)); rq.setTimeout(1000, () => { rq.destroy(); res(0); }); }); }

(async () => {
  if (await get(APP)) throw new Error('something is already on :8700; not starting another server');
  fs.mkdirSync(OUT, { recursive: true });
  const state = fs.mkdtempSync(path.join(os.tmpdir(), 'barnaby-state-'));
  const srv = spawn(path.join(ROOT, '.venv/Scripts/python.exe'), ['-m', 'barnaby', 'serve'], { cwd: ROOT, env: { ...process.env, BARNABY_STATE: state }, stdio: 'ignore', windowsHide: true });
  console.log('started barnaby serve, pid', srv.pid);
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none'] });
  try {
    let up = 0;
    for (let i = 0; i < 100 && !up; i++) { up = await get(APP); if (!up) await new Promise(r => setTimeout(r, 300)); }
    if (!up) throw new Error('barnaby serve did not come up');
    const page = await browser.newPage();
    await page.setViewport({ width: 890, height: 798, deviceScaleFactor: 1.6 });
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
    await page.goto(APP, { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 800));
    const systems = await page.evaluate(async () => (await (await fetch('/api/state')).json()).systems.length);
    if (systems) throw new Error(`expected a fresh registry, found ${systems} system(s)`);
    await page.click('#toggle-map');
    await new Promise(r => setTimeout(r, 400));
    await page.evaluate(() => document.activeElement && document.activeElement.blur());
    await page.mouse.move(5, 790);
    await new Promise(r => setTimeout(r, 200));
    await page.screenshot({ path: path.join(OUT, 'base.jpg'), type: 'jpeg', quality: 94 });
    const steps = []; let n = 0;
    const clip = { x: FORM.x / 1.6, y: FORM.y / 1.6, width: FORM.width / 1.6, height: FORM.height / 1.6 };
    const shot = async what => {
      await new Promise(r => setTimeout(r, 60));
      const f = `f_${String(n++).padStart(3, '0')}.jpg`;
      await page.screenshot({ path: path.join(OUT, f), type: 'jpeg', quality: 94, clip });
      steps.push([f, what]);
    };
    await shot('empty');
    for (const [name, text] of FIELDS) {
      const sel = `#connect-form input[name="${name}"]`;
      await page.click(sel);
      await shot('click ' + name);
      for (const ch of text) { await page.type(sel, ch); await shot(`type ${name} ${ch}`); }
    }
    // the pointer to Connect: hover, then held down (not released: nothing is submitted)
    const btn = await page.$('#connect-form button[type="submit"], #connect-form button');
    const bb = await btn.boundingBox();
    await page.mouse.move(bb.x + bb.width * .45, bb.y + bb.height * .55);
    await new Promise(r => setTimeout(r, 250));
    await shot('hover connect');
    await page.mouse.down();
    await new Promise(r => setTimeout(r, 120));
    await shot('press connect');
    const box = { x: bb.x * 1.6, y: bb.y * 1.6, w: bb.width * 1.6, h: bb.height * 1.6 };
    fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify({ form: FORM, size: [1424, 1277], connect: box, steps }, null, 1));
    await page.close();
    console.log(`wrote ${steps.length} form states + base.jpg to ${OUT}`);
  } finally {
    await browser.close();
    try { execFileSync('taskkill', ['/PID', String(srv.pid), '/T', '/F'], { stdio: 'ignore' }); } catch (e) { srv.kill(); }
    await new Promise(r => setTimeout(r, 800));
    console.log('stopped barnaby serve;', (await get(APP)) ? 'STILL ANSWERING' : ':8700 closed');
    fs.rmSync(state, { recursive: true, force: true });
  }
})().catch(e => { console.error(e); process.exit(1); });
