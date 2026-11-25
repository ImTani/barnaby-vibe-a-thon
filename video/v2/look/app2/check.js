/* Checks for what only the app look (?skin=app) adds, on top of ../app/check.js (run that one with --skins app too).
   Needs the core running (.venv/Scripts/python -m barnaby serve). Nothing is connected for real.
   node video/v2/look/app2/check.js */
const path = require('path');
const puppeteer = require(path.resolve(__dirname, '../../../node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.env.BARNABY_URL || 'http://127.0.0.1:8700';
const wait = ms => new Promise(r => setTimeout(r, ms));
const EMPTY_STATE = JSON.stringify({ busy: false, systems: [], approvals: [] });
const FAKE_VOICE = () => {
  class FakePC {
    constructor() { this.connectionState = 'connected'; this.iceGatheringState = 'complete'; this.localDescription = null; }
    addTransceiver() {} async createOffer() { return { type: 'offer', sdp: '' }; }
    async setLocalDescription(d) { this.localDescription = d; } async setRemoteDescription() {} close() {}
  }
  window.RTCPeerConnection = FakePC;
};

(async () => {
  const b = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'] });
  let fails = 0;
  const ok = (what, cond, extra = '') => { if (!cond) fails++; console.log(`${cond ? 'PASS' : 'FAIL'}  ${what}${extra ? '  (' + extra + ')' : ''}`); };
  const page = async (w = 1440, h = 900) => {
    const p = await b.newPage(); p.errors = []; p.on('pageerror', e => p.errors.push(e.message));
    await p.setViewport({ width: w, height: h }); return p;
  };

  // 1. the look loads, and the old one is still there
  let p = await page();
  await p.goto(`${BASE}/?skin=app&static=1`, { waitUntil: 'networkidle0' });
  ok('?skin=app loads skins/app.css', await p.evaluate(() => [...document.styleSheets].some(s => /skins\/app\.css/.test(s.href || ''))));
  const font = await p.evaluate(() => getComputedStyle(document.querySelector('.msg .text')).fontFamily);
  ok('set in Segoe UI', /Segoe UI/.test(font), font.split(',')[0]);
  for (const q of ['', '?skin=classic']) {
    const o = await page();
    await o.goto(`${BASE}/${q}${q ? '&' : '?'}static=1`, { waitUntil: 'networkidle0' });
    ok(`old look unchanged at "/${q}"`, await o.evaluate(() => [...document.styleSheets].some(s => /\/ui\/style\.css/.test(s.href || '')) && !document.documentElement.dataset.skin));
    await o.close();
  }
  await p.close();

  // 2. empty: the welcome teaches the controls and offers the way in
  p = await page();
  await p.setRequestInterception(true);
  p.on('request', r => r.url().includes('/api/state') ? r.respond({ status: 200, contentType: 'application/json', body: EMPTY_STATE }) : r.continue());
  await p.goto(`${BASE}/?skin=app&static=1`, { waitUntil: 'networkidle0' });
  ok('welcome says how to talk and type', await p.$$eval('.intro .how li', n => n.length) === 2);
  ok('no system: "Connect a system" shows', await p.$eval('.connect-first', n => getComputedStyle(n).display !== 'none'));
  await p.click('.connect-first'); await wait(200);
  ok('it opens the connect form, focused', await p.evaluate(() => !document.getElementById('map').hidden && document.activeElement && document.activeElement.name === 'name'));
  ok('the panel takes the inspector\'s place', await p.evaluate(() => getComputedStyle(document.querySelector('.trace')).display === 'none'));
  await p.close();

  // 3. working: the status says what he is doing now, in the present tense
  p = await page();
  await p.goto(`${BASE}/?skin=app&mock=1&turn=2&speed=1`, { waitUntil: 'networkidle0' });
  let seen = '';
  for (let i = 0; i < 40 && !/^Looking at /.test(seen); i++) { await wait(150); seen = await p.$eval('#status-text', n => n.textContent); }
  ok('status: "Looking at …" while he looks', /^Looking at /.test(seen), seen);
  ok('the pending line says the same', await p.evaluate(t => { const n = document.querySelector('.msg.pending .thinking'); return !!n && n.textContent === t; }, seen));
  await p.close();

  // 4. the Build card: lead line, facts, the decision stays in reach with the change open
  p = await page();
  await p.goto(`${BASE}/?skin=app&mock=1&turn=4&speed=20`, { waitUntil: 'networkidle0' });
  await p.waitForSelector('#card-a3', { timeout: 30000 });
  await wait(400);
  ok('card leads with what it does', /^It shows how many hours/.test(await p.$eval('#card-a3 .lede', n => n.textContent)));
  ok('checks carry a tick and the count', await p.$eval('#card-a3 .fact.checks dd', n => !!n.querySelector('.ico') && /19 checks/.test(n.textContent)));
  ok('"See the change" says how big it is, closed', /3 files, \d+ lines added, nothing removed/.test(await p.$eval('#card-a3 details.change summary', n => n.textContent)));
  ok('yes is the last button (right), no before it', await p.$$eval('#card-a3 .actions button', n => n.map(x => x.className).join(',')) === 'secondary,primary');
  await p.click('#card-a3 details.change > summary'); await wait(500);
  const docked = await p.evaluate(() => {
    const c = document.querySelector('.convo').getBoundingClientRect(), a = document.querySelector('#card-a3 .actions').getBoundingClientRect();
    return a.top >= c.top && a.bottom <= c.bottom + 1;
  });
  ok('with the change open, yes and no stay in view', docked);
  ok('the summary flips to "Hide the change"', /^Hide the change/.test(await p.$eval('#card-a3 details.change summary', n => n.textContent)));
  await p.close();

  // 5. hold to talk with a connected voice bot (a stand-in): the button says it is listening, and stops
  p = await page();
  await p.evaluateOnNewDocument(FAKE_VOICE);
  await p.setRequestInterception(true);
  p.on('request', r => r.url().includes('/api/voice/offer') ? r.respond({ status: 200, contentType: 'application/json', body: '{"type":"answer","sdp":""}' }) : r.continue());
  await p.goto(`${BASE}/?skin=app&mock=1&turn=2&paused=1`, { waitUntil: 'networkidle0' });
  let bx = await (await p.$('#talk')).boundingBox();
  await p.mouse.move(bx.x + 20, bx.y + 20); await p.mouse.down(); await wait(500);
  ok('held: "Listening…" on the button and in the status', await p.evaluate(() => document.querySelector('#talk .label').textContent === 'Listening…' && /Listening/.test(document.getElementById('status-text').textContent)));
  await p.mouse.up(); await wait(300);
  ok('let go: back to "Hold to talk"', await p.$eval('#talk .label', n => n.textContent) === 'Hold to talk');
  await p.keyboard.down('Space'); await wait(300);
  ok('the space bar holds it too', await p.$eval('#talk', n => n.classList.contains('on')));
  await p.keyboard.up('Space'); await wait(200);
  await p.close();

  // 6. voice not running: a plain error with the raw message folded
  p = await page();
  await p.setRequestInterception(true);
  p.on('request', r => r.url().includes('/api/voice/offer') ? r.respond({ status: 503, body: 'no voice bot' }) : r.continue());
  await p.goto(`${BASE}/?skin=app&mock=1&turn=2&paused=1`, { waitUntil: 'networkidle0' });
  bx = await (await p.$('#talk')).boundingBox();
  await p.mouse.move(bx.x + 20, bx.y + 20); await p.mouse.down(); await wait(400); await p.mouse.up(); await wait(400);
  const err = await p.$eval('.msg.error', n => ({ who: n.querySelector('.who').textContent, raw: n.querySelector('details') && !n.querySelector('details').open }));
  ok('voice error is said in plain words', err.who === 'Voice isn’t available just now', err.who);
  ok('the raw message is folded under Details', err.raw);
  await p.close();

  // 7. typing: Ask lights up with text and sends
  p = await page();
  let asked = null;
  await p.setRequestInterception(true);
  p.on('request', r => { if (r.url().includes('/api/ask')) { asked = r.postData(); return r.respond({ status: 200, body: '{"ok":true}' }); } r.continue(); });
  await p.goto(`${BASE}/?skin=app&static=1`, { waitUntil: 'networkidle0' });
  const idle = await p.$eval('#ask-form button', n => getComputedStyle(n).backgroundColor);
  await p.type('#ask-input', 'Who is in today?');
  const live = await p.$eval('#ask-form button', n => getComputedStyle(n).backgroundColor);
  ok('Ask button turns primary when there is text', idle !== live, `${idle} -> ${live}`);
  await p.keyboard.press('Enter'); await wait(300);
  ok('Enter sends the question', asked && JSON.parse(asked).text === 'Who is in today?');
  await p.keyboard.press('Tab');
  ok('keyboard focus is visible', await p.evaluate(() => { const a = document.activeElement; const s = getComputedStyle(a); return a && a !== document.body && s.outlineStyle !== 'none'; }));
  await p.close();

  // 8. what he can do: a word for every state, the new piece marked
  p = await page();
  await p.goto(`${BASE}/?skin=app&mock=1&turn=9&speed=20`, { waitUntil: 'networkidle0' });
  await wait(600); await p.click('#toggle-map'); await wait(200);
  const states = await p.$$eval('#map .ab', n => n.map(x => (x.querySelector('.state, .today') || {}).textContent));
  ok('every ability has its state in words', states.length > 20 && states.every(Boolean), `${states.length} abilities`);
  ok("the new report and the one-step are \"Added today\"; keys given today say so", states.filter(s => s === "Added today").length >= 2 && states.filter(s => s === "Key given today").length === 2);
  ok('kept shut is shown', states.includes('Kept shut'));
  ok('no capsules: state words are plain text', await p.$$eval('#map .ab .today', n => n.every(x => parseFloat(getComputedStyle(x).borderTopLeftRadius) === 0 && getComputedStyle(x).backgroundColor === 'rgba(0, 0, 0, 0)')));
  const techShown = () => p.$$eval('#map .ab .tech', n => n.filter(x => x.offsetParent).length);
  ok('technical names are folded by default', await techShown() === 0);
  await p.click('.tech-toggle'); await wait(100);
  ok('…and shown on request', await techShown() > 20);

  // 8b. the replay's own words and counts: plain decisions, the yes before the act, the count of that moment
  const q = await page();
  await q.goto(`${BASE}/?skin=app&mock=1&turn=4&paused=1`, { waitUntil: 'networkidle0' });
  await wait(600);
  const dec = await q.$$eval('.msg.decision .text', n => n.map(x => x.textContent));
  ok('kept decisions name the thing, not its arguments', dec.some(t => /Ten pairs of the Shimano resin pads from Madison/.test(t)) && !dec.some(t => /part 1/.test(t)), dec.join(' | '));
  const order = await q.$$eval('#trace .tr.step', n => n.map(x => x.querySelector('.say').textContent));
  const yesAt = order.findIndex(t => /^You said yes: Ten pairs/.test(t)), actAt = order.findIndex(t => /^Ordered more of a part/.test(t));
  ok('the yes comes before the order it allowed', yesAt >= 0 && actAt > yesAt, `${yesAt} < ${actAt}`);
  await q.goto(`${BASE}/?skin=app&mock=1&turn=3&paused=1`, { waitUntil: 'networkidle0' });
  await wait(1200);
  const chip = await q.$eval('.sys-chip span', n => n.textContent);
  ok('toolbar count is the replay\'s, not the server\'s', chip === 'He can use 6 of its 23 things', chip);
  await q.close();

  // 9. sizes: nothing spills sideways, the overlay keeps its controls in view
  for (const [w, h, q] of [[1920, 1080, 'mock=1&turn=4&speed=20'], [1440, 900, 'mock=1&turn=4&speed=20'], [560, 860, 'mock=1&overlay=1&turn=4&speed=20']]) {
    const s = await page(w, h);
    await s.goto(`${BASE}/?skin=app&${q}`, { waitUntil: 'networkidle0' });
    await s.waitForSelector('#card-a3', { timeout: 30000 }); await wait(500);
    const r = await s.evaluate(() => ({
      over: document.documentElement.scrollWidth > innerWidth + 1,
      talk: (() => { const t = document.getElementById('talk').getBoundingClientRect(); return t.bottom <= innerHeight && t.top >= 0; })(),
      yes: (() => { const y = document.querySelector('#card-a3 .primary').getBoundingClientRect(); return y.bottom <= innerHeight && y.top >= 0; })(),
    }));
    ok(`${w}x${h}: no sideways overflow, talk and "Yes, add it" in view`, !r.over && r.talk && r.yes, JSON.stringify(r));
    ok(`${w}x${h}: no script errors`, s.errors.length === 0, s.errors.join(' / '));
    await s.close();
  }
  ok('no script errors', p.errors.length === 0, p.errors.join(' / '));
  await p.close();

  await b.close();
  console.log(fails ? `${fails} FAILED` : 'all passed');
  process.exit(fails ? 1 : 0);
})();
