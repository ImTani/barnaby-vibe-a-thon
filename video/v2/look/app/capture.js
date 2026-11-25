/* Screenshots of the REAL display (ui/) in each skin, at the key moments, driven through the mock replay.
   Needs the core running: .venv/Scripts/python -m barnaby serve  (http://127.0.0.1:8700)

   node video/v2/look/app/capture.js [--skins default,ledger] [--sizes 1920x1080,1440x900] [--only answer,build]

   Scenes: answer (turn 2 answered), unlock (the key card), build (the Build card), change ("See the change" open),
   compose (the one-step card), working (mid-turn, activity filling), empty (no systems, the connect form open),
   overlay (the compact HUD), detail (an activity line opened to its technical detail).
   Frames land in frames/<skin>-<scene>-<width>.png. */
const path = require('path'), fs = require('fs');
const puppeteer = require(path.resolve(__dirname, '../../../node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.env.BARNABY_URL || 'http://127.0.0.1:8700';
const OUT = path.join(__dirname, 'frames');

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const skins = arg('skins', 'default').split(',');
const sizes = arg('sizes', '1920x1080,1440x900').split(',').map(s => s.split('x').map(Number));
const only = arg('only', '');
const wait = ms => new Promise(r => setTimeout(r, ms));

const url = (skin, q) => `${BASE}/?${q}${skin === 'default' ? '' : '&skin=' + skin}`;
const EMPTY_STATE = JSON.stringify({ busy: false, systems: [], approvals: [] });

const SCENES = {
  async answer(p, skin) {
    await p.goto(url(skin, 'mock=1&turn=3&paused=1&speed=10'), { waitUntil: 'networkidle0' });
    await wait(700);
  },
  async working(p, skin) {
    await p.goto(url(skin, 'mock=1&turn=4&speed=4'), { waitUntil: 'networkidle0' });
    await wait(2900);                           // mid-build; Space would also start hold-to-talk, so no pause key
  },
  async unlock(p, skin) {
    await p.goto(url(skin, 'mock=1&turn=3&speed=10'), { waitUntil: 'networkidle0' });
    await p.waitForSelector('#card-a1', { timeout: 20000 });
    await wait(700);
  },
  async build(p, skin) {
    await p.goto(url(skin, 'mock=1&turn=4&speed=10'), { waitUntil: 'networkidle0' });
    await p.waitForSelector('#card-a3', { timeout: 30000 });
    await wait(900);
  },
  async change(p, skin) {                      // the Build card with "See the change" opened by a real click
    await p.goto(url(skin, 'mock=1&turn=4&speed=10'), { waitUntil: 'networkidle0' });
    await p.waitForSelector('#card-a3', { timeout: 30000 });
    await wait(700);
    await p.click('#card-a3 details.change > summary');
    await wait(900);
  },
  async compose(p, skin) {
    await p.goto(url(skin, 'mock=1&turn=6&speed=10'), { waitUntil: 'networkidle0' });
    await p.waitForSelector('#card-a7', { timeout: 30000 });
    await wait(700);
  },
  async detail(p, skin) {
    await p.goto(url(skin, 'mock=1&turn=3&paused=1&speed=10'), { waitUntil: 'networkidle0' });
    await wait(500);
    await p.evaluate(() => {
      const rows = [...document.querySelectorAll('#trace .tr')];
      const r = rows.find(x => /jobs_due|due/i.test(x.textContent)) || rows[rows.length - 1];
      if (r) { r.classList.add('open'); const d = r.querySelector('details'); if (d) d.open = true; }
    });
    await wait(400);
  },
  async empty(p, skin) {
    await p.setRequestInterception(true);
    p.on('request', r => r.url().includes('/api/state')
      ? r.respond({ status: 200, contentType: 'application/json', body: EMPTY_STATE }) : r.continue());
    await p.goto(url(skin, 'static=1'), { waitUntil: 'networkidle0' });
    await p.click('#toggle-map');
    await wait(300);
    await p.focus('#connect-form input[name="name"]');
    await p.keyboard.type('shop');
    await wait(300);
  },
  async map(p, skin) {                         // "What he can do" after the whole run: keys given, the new room, the passage
    await p.goto(url(skin, 'mock=1&turn=9&speed=10'), { waitUntil: 'networkidle0' });
    await wait(700);
    await p.click('#toggle-map');
    await wait(400);
  },
  async overlay(p, skin) {
    await p.goto(url(skin, 'mock=1&overlay=1&turn=3&speed=10'), { waitUntil: 'networkidle0' });
    await p.waitForSelector('#card-a1', { timeout: 20000 });
    await wait(700);
  },
};

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await puppeteer.launch({ executablePath: CHROME, headless: true,
    args: ['--hide-scrollbars', '--force-device-scale-factor=1', '--font-render-hinting=none'] });
  let errs = 0;
  for (const skin of skins) for (const [name, run] of Object.entries(SCENES)) {
    if (only && !only.split(',').includes(name)) continue;
    const sz = name === 'overlay' ? [[560, 860]] : sizes;
    for (const [w, h] of sz) {
      const p = await b.newPage();
      p.on('pageerror', e => { errs++; console.error(`[${skin}/${name}] page error:`, e.message); });
      p.on('console', m => { if (m.type() === 'error') console.error(`[${skin}/${name}] console:`, m.text()); });
      await p.setViewport({ width: w, height: h });
      try {
        await run(p, skin);
        const out = path.join(OUT, `${skin}-${name}-${w}.png`);
        await p.screenshot({ path: out });
        console.log(out);
      } catch (e) { errs++; console.error(`[${skin}/${name}@${w}]`, e.message); }
      await p.close();
    }
  }
  await b.close();
  process.exit(errs ? 2 : 0);
})();
