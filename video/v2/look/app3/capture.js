/* Screenshots of the REAL display (ui/) in the app look, at the key moments, driven through the mock replay.
   Round 3 (?skin=app3): the same scenes and mock moments as ../app2/capture.js, light and dark, into this folder's
   frames/ as app3-[dark-]<scene>-<width>.png. --theme light,dark picks the themes (default both).
   Needs the core running: .venv/Scripts/python -m barnaby serve  (http://127.0.0.1:8700)

   node video/v2/look/app3/capture.js [--skins app3] [--theme light,dark] [--sizes 1920x1080,1440x900] [--only answer,build]

   Scenes: empty (no system; the welcome), connect (no system; "What he can do" open on the connect form),
   answer (turn 2 answered), working (mid-build), unlock (the key card), build (the Build card), change ("See the
   change" open), compose (the one-step card), map ("What he can do" after the run), detail (an activity line opened
   to its technical record), listening (hold to talk held), error (voice not reachable), overlay (the compact window).
   For "listening" the voice bot is a stand-in (a fake peer connection answering at once), so the held state is the one a
   connected bot gives; "error" is the real path when the bot is not running.
   Frames land in frames/<skin>-<scene>-<width>.png. */
const path = require('path'), fs = require('fs');
const puppeteer = require(path.resolve(__dirname, '../../../node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.env.BARNABY_URL || 'http://127.0.0.1:8700';
const OUT = path.join(__dirname, 'frames');

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const skins = arg('skins', 'app3').split(',');
const themes = arg('theme', 'light,dark').split(',');
const sizes = arg('sizes', '1920x1080,1440x900').split(',').map(s => s.split('x').map(Number));
const only = arg('only', '');
const wait = ms => new Promise(r => setTimeout(r, ms));

let THEME = 'light';
const url = (skin, q) => `${BASE}/?${q}${skin === 'default' ? '' : '&skin=' + skin}&theme=${THEME}`;
const EMPTY_STATE = JSON.stringify({ busy: false, systems: [], approvals: [] });
const emptyState = async p => {
  await p.setRequestInterception(true);
  p.on('request', r => r.url().includes('/api/state')
    ? r.respond({ status: 200, contentType: 'application/json', body: EMPTY_STATE }) : r.continue());
};
// a stand-in voice bot: the peer connection "connects" at once, so holding the button shows the listening state
const FAKE_VOICE = () => {
  class FakePC {
    constructor() { this.connectionState = 'connected'; this.iceGatheringState = 'complete'; this.localDescription = null; }
    addTransceiver() {} async createOffer() { return { type: 'offer', sdp: '' }; }
    async setLocalDescription(d) { this.localDescription = d; } async setRemoteDescription() {} close() {}
  }
  window.RTCPeerConnection = FakePC;
};

const SCENES = {
  async empty(p, skin) {
    await emptyState(p);
    await p.goto(url(skin, 'static=1'), { waitUntil: 'networkidle0' });
    await wait(400);
  },
  async connect(p, skin) {
    await emptyState(p);
    await p.goto(url(skin, 'static=1'), { waitUntil: 'networkidle0' });
    await p.click('#toggle-map');
    await wait(300);
    await p.focus('#connect-form input[name="name"]');
    await p.keyboard.type('shop');
    await wait(300);
  },
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
  async map(p, skin) {                         // "What he can do" after the whole run: keys given, the new piece, the one-step
    await p.goto(url(skin, 'mock=1&turn=9&speed=10'), { waitUntil: 'networkidle0' });
    await wait(700);
    await p.click('#toggle-map');
    await wait(400);
  },
  async 'map-today'(p, skin) {                 // the developer's view: technical names on, scrolled to what changed today
    await p.goto(url(skin, 'mock=1&turn=9&speed=10'), { waitUntil: 'networkidle0' });
    await wait(700);
    await p.click('#toggle-map');
    await wait(300);
    if (await p.$('.tech-toggle')) { await p.click('.tech-toggle'); await wait(200); }
    await p.evaluate(() => { const n = document.querySelector('#map .ab.new'); if (n) n.closest('ul').previousElementSibling.scrollIntoView({ block: 'start' }); document.getElementById('map').scrollTop -= 64; });
    await wait(300);
  },
  async detail(p, skin) {
    await p.goto(url(skin, 'mock=1&turn=3&paused=1&speed=10'), { waitUntil: 'networkidle0' });
    await wait(500);
    const line = await p.evaluateHandle(() => [...document.querySelectorAll('#trace .act .act-line')].find(x => /due on/i.test(x.textContent)));
    if (line && line.asElement()) { await line.asElement().click(); await wait(300); }      // app3: open the work line first
    const row = await p.evaluateHandle(() => [...document.querySelectorAll('#trace .tr.step:not(.past)')].find(x => /due on/i.test(x.textContent)));
    const box = await row.boundingBox();
    await p.mouse.move(box.x + box.width / 2, box.y + 12);
    await p.evaluate(r => { const d = r.querySelector('details'); if (d) d.open = true; }, row);
    await wait(400);
  },
  async listening(p, skin) {
    await p.evaluateOnNewDocument(FAKE_VOICE);
    await p.setRequestInterception(true);
    p.on('request', r => r.url().includes('/api/voice/offer')
      ? r.respond({ status: 200, contentType: 'application/json', body: '{"type":"answer","sdp":""}' }) : r.continue());
    await p.goto(url(skin, 'mock=1&turn=4&paused=1&speed=10'), { waitUntil: 'networkidle0' });
    await wait(500);
    const b = await (await p.$('#talk')).boundingBox();
    await p.mouse.move(b.x + b.width / 2, b.y + b.height / 2); await p.mouse.down();
    await wait(700);
  },
  async error(p, skin) {                       // the real path with no voice bot running: hold, let go, the message
    await p.setRequestInterception(true);
    p.on('request', r => r.url().includes('/api/voice/offer') ? r.respond({ status: 503, body: 'voice bot not running' }) : r.continue());
    await p.goto(url(skin, 'mock=1&turn=3&paused=1&speed=10'), { waitUntil: 'networkidle0' });
    await wait(500);
    const b = await (await p.$('#talk')).boundingBox();
    await p.mouse.move(b.x + b.width / 2, b.y + b.height / 2); await p.mouse.down(); await wait(500); await p.mouse.up();
    await p.mouse.move(b.x + b.width / 2, b.y - 200);
    await wait(700);
  },
  async overlay(p, skin) {
    await p.goto(url(skin, 'mock=1&overlay=1&turn=3&speed=10'), { waitUntil: 'networkidle0' });
    await p.waitForSelector('#card-a1', { timeout: 20000 });
    await wait(700);
  },
  async 'overlay-build'(p, skin) {
    await p.goto(url(skin, 'mock=1&overlay=1&turn=4&speed=10'), { waitUntil: 'networkidle0' });
    await p.waitForSelector('#card-a3', { timeout: 30000 });
    await wait(900);
  },
};

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await puppeteer.launch({ executablePath: CHROME, headless: true,
    args: ['--hide-scrollbars', '--force-device-scale-factor=1', '--font-render-hinting=none',
      '--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'] });
  let errs = 0;
  for (const theme of themes) for (const skin of skins) for (const [name, run] of Object.entries(SCENES)) {
    if (only && !only.split(',').includes(name)) continue;
    THEME = theme;
    const sz = name.startsWith('overlay') ? [[560, 860]] : sizes;
    for (const [w, h] of sz) {
      const p = await b.newPage();
      p.on('pageerror', e => { errs++; console.error(`[${skin}/${name}] page error:`, e.message); });
      p.on('console', m => { if (m.type() === 'error' && !/503|Failed to load resource/.test(m.text())) console.error(`[${skin}/${name}] console:`, m.text()); });
      await p.setViewport({ width: w, height: h });
      try {
        await run(p, skin);
        const out = path.join(OUT, `${skin}-${theme === 'dark' ? 'dark-' : ''}${name}-${w}.png`);
        await p.screenshot({ path: out });
        console.log(out);
      } catch (e) { errs++; console.error(`[${skin}/${name}@${w}]`, e.message); }
      await p.close();
    }
  }
  await b.close();
  process.exit(errs ? 2 : 0);
})();
