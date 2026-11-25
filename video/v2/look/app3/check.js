/* Checks for the round-3 look (?skin=app3): the round-2 app checks carried over, plus what round 3 adds (the work inline
   and collapsed, the live line with his mark at work, light and dark, the inspector, the mark and the favicon).
   Run alongside ../app/check.js --skins app3. Needs the core running (.venv/Scripts/python -m barnaby serve).
   node video/v2/look/app3/check.js */
const path = require('path');
const puppeteer = require(path.resolve(__dirname, '../../../node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.env.BARNABY_URL || 'http://127.0.0.1:8700';
const SK = 'skin=app3';
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
    await p.setViewport({ width: w, height: h }); await p.evaluateOnNewDocument(() => { try { localStorage.removeItem('barnaby-theme'); } catch (_) {} });
    return p;
  };

  // 1. the look, the type, the mark, the favicon; the other looks untouched
  let p = await page();
  await p.goto(`${BASE}/?${SK}&static=1`, { waitUntil: 'networkidle0' });
  ok('?skin=app3 loads skins/app3.css', await p.evaluate(() => [...document.styleSheets].some(s => /skins\/app3\.css/.test(s.href || ''))));
  const faces = await p.evaluate(() => ({ words: getComputedStyle(document.querySelector('.msg .text')).fontFamily, ui: getComputedStyle(document.body).fontFamily }));
  ok('his words in a reading serif, the UI in Segoe', /Sitka|Constantia/.test(faces.words) && /Segoe UI/.test(faces.ui), `${faces.words.split(',')[0]} / ${faces.ui.split(',')[0]}`);
  ok('the mark is his bell and bow tie (masked), in the bar and the welcome', await p.evaluate(() => !!document.getElementById('bb-tie') && document.querySelectorAll('.brand .bmark, .intro .bmark').length === 2));
  const fav = await p.evaluate(async () => { const l = document.querySelector('link[rel="icon"]'); if (!l) return 0; const r = await fetch(l.href); return r.status; });
  ok('the favicon is served', fav === 200, String(fav));
  for (const [q, want, what] of [['', /skins\/app3\.css$/, 'the default ("/") is this look'], ['?skin=classic', /\/ui\/style\.css$/, 'the old look at ?skin=classic'], ['?skin=app', /skins\/app\.css$/, 'round 2 at ?skin=app']]) {
    const o = await page();
    await o.goto(`${BASE}/${q}${q ? '&' : '?'}static=1`, { waitUntil: 'networkidle0' });
    const css = await o.evaluate(() => [...document.styleSheets].map(s => s.href || '').find(h => /\/ui\/(style|skins\/app3?)\.css/.test(h)) || '');
    ok(what, want.test(css), css.split('/ui/')[1]);
    await o.close();
  }
  await p.close();

  // 2. empty: the welcome teaches the controls and offers the way in
  p = await page();
  await p.setRequestInterception(true);
  p.on('request', r => r.url().includes('/api/state') ? r.respond({ status: 200, contentType: 'application/json', body: EMPTY_STATE }) : r.continue());
  await p.goto(`${BASE}/?${SK}&static=1`, { waitUntil: 'networkidle0' });
  ok('welcome asks in his voice and teaches the two controls', /Good day\. What can I look into\?/.test(await p.$eval('.intro .text', n => n.textContent)) && await p.$$eval('.intro .how li', n => n.length) === 2);
  ok('no system: "Connect a system" shows', await p.$eval('.connect-first', n => getComputedStyle(n).display !== 'none'));
  await p.click('.connect-first'); await wait(200);
  ok('it opens the connect form, focused', await p.evaluate(() => !document.getElementById('map').hidden && document.activeElement && document.activeElement.name === 'name'));
  ok('the sheet covers the side panel, not the conversation', await p.evaluate(() => { const m = document.getElementById('map').getBoundingClientRect(), c = document.querySelector('.intro').getBoundingClientRect(); return m.left >= c.right; }));
  await p.close();

  // 3. working: the work is inline, one live line with his mark at work, a present-tense sentence and a timer
  p = await page();
  await p.goto(`${BASE}/?${SK}&mock=1&turn=2&speed=1`, { waitUntil: 'networkidle0' });
  let seen = '';
  for (let i = 0; i < 40 && !/^Looking at /.test(seen); i++) { await wait(150); seen = await p.$eval('#status-text', n => n.textContent); }
  ok('status: "Looking at …" while he looks', /^Looking at /.test(seen), seen);
  const live = await p.evaluate(() => { const a = document.querySelector('.act.live'); return a && { text: a.querySelector('.act-text').textContent, time: a.querySelector('.act-time').textContent, work: !!a.querySelector('.bmark.work'), anim: getComputedStyle(a.querySelector('.bmark .knob')).animationName }; });
  ok('the live line says the same, with a timer', live && /^Looking at /.test(live.text) && /^\d+s$/.test(live.time), live && `${live.text} · ${live.time}`);
  ok('his mark is at work on the live line', live && live.work && live.anim === 'tap', live && live.anim);
  ok('only one live line (the pending line hides)', await p.evaluate(() => { const pend = document.querySelector('.msg.pending'); return !pend || getComputedStyle(pend).display === 'none'; }));
  ok('no separate trace column', await p.evaluate(() => getComputedStyle(document.querySelector('section.trace')).display === 'contents'));
  await p.close();

  // 4. after a turn: the work collapsed into one plain line between the question and the answer; it opens to the steps
  p = await page();
  await p.goto(`${BASE}/?${SK}&mock=1&turn=3&paused=1`, { waitUntil: 'networkidle0' });
  await wait(600);
  const line = await p.evaluate(() => {
    const q = [...document.querySelectorAll('.msg.user')].find(x => /due tomorrow/.test(x.textContent));
    const a = [...document.querySelectorAll('.act:not(.ask-only)')].find(x => /due on/.test(x.textContent));
    const ans = [...document.querySelectorAll('.msg.barnaby')].find(x => /Five repairs/.test(x.textContent));
    return a && { text: a.querySelector('.act-text').textContent, between: +q.style.order < +a.style.order && +a.style.order < +ans.style.order,
      folded: [...document.querySelectorAll(`.tr.step[data-b="${a.dataset.b}"]`)].every(s => s.classList.contains('folded')) };
  });
  ok('one plain line for the batch', line && /^Looked at repair jobs due on .+ and 5 repair jobs$/.test(line.text), line && line.text);
  ok('…between the question and the answer, steps folded', line && line.between && line.folded);
  const opened = await p.evaluate(() => { const a = [...document.querySelectorAll('.act .act-line')].find(x => /due on/.test(x.textContent)); a.click();
    const b = a.closest('.act').dataset.b; return [...document.querySelectorAll(`.tr.step[data-b="${b}"]`)].filter(s => s.getBoundingClientRect().height > 10).length; });
  ok('clicking it opens the steps', opened >= 5, `${opened} steps`);
  await p.close();

  // 5. the Build card: lead line, facts, the change by its counts, the decision stays in reach with the change open
  p = await page();
  await p.goto(`${BASE}/?${SK}&mock=1&turn=4&speed=20`, { waitUntil: 'networkidle0' });
  await p.waitForSelector('#card-a3', { timeout: 30000 });
  await wait(400);
  ok('card leads with what it does', /^It shows how many hours/.test(await p.$eval('#card-a3 .lede', n => n.textContent)));
  ok('the card says what kind of ask it is', await p.$eval('#card-a3 .kind-line', n => n.textContent) === 'A new piece for the system');
  ok('checks carry a tick and the count', await p.$eval('#card-a3 .fact.checks dd', n => !!n.querySelector('.ico') && /19 checks/.test(n.textContent)));
  ok('"See the change" shows its counts, closed', /^See the change3 files\+\d+−0$/.test(await p.$eval('#card-a3 details.change summary', n => n.textContent)));
  ok('yes is the last button (right), no before it', await p.$$eval('#card-a3 .actions button', n => n.map(x => x.className).join(',')) === 'secondary,primary');
  await p.click('#card-a3 details.change > summary'); await wait(500);
  ok('with the change open, yes and no stay in view', await p.evaluate(() => {
    const c = document.querySelector('main').getBoundingClientRect(), a = document.querySelector('#card-a3 .actions').getBoundingClientRect();
    return a.top >= c.top && a.bottom <= c.bottom + 1;
  }));
  ok('the summary flips to "Hide the change"', /^Hide the change/.test(await p.$eval('#card-a3 details.change summary', n => n.textContent)));
  await p.close();

  // 6. hold to talk with a connected voice bot (a stand-in): the button says it is listening, and stops
  p = await page();
  await p.evaluateOnNewDocument(FAKE_VOICE);
  await p.setRequestInterception(true);
  p.on('request', r => r.url().includes('/api/voice/offer') ? r.respond({ status: 200, contentType: 'application/json', body: '{"type":"answer","sdp":""}' }) : r.continue());
  await p.goto(`${BASE}/?${SK}&mock=1&turn=2&paused=1`, { waitUntil: 'networkidle0' });
  let bx = await (await p.$('#talk')).boundingBox();
  await p.mouse.move(bx.x + 20, bx.y + 15); await p.mouse.down(); await wait(500);
  ok('held: "Listening…" on the button and in the status', await p.evaluate(() => document.querySelector('#talk .label').textContent === 'Listening…' && /Listening/.test(document.getElementById('status-text').textContent)));
  await p.mouse.up(); await wait(300);
  ok('let go: back to "Hold to talk"', await p.$eval('#talk .label', n => n.textContent) === 'Hold to talk');
  await p.keyboard.down('Space'); await wait(300);
  ok('the space bar holds it too', await p.$eval('#talk', n => n.classList.contains('on')));
  await p.keyboard.up('Space'); await wait(200);
  await p.close();

  // 7. voice not running: a plain error with the raw message folded
  p = await page();
  await p.setRequestInterception(true);
  p.on('request', r => r.url().includes('/api/voice/offer') ? r.respond({ status: 503, body: 'no voice bot' }) : r.continue());
  await p.goto(`${BASE}/?${SK}&mock=1&turn=2&paused=1`, { waitUntil: 'networkidle0' });
  bx = await (await p.$('#talk')).boundingBox();
  await p.mouse.move(bx.x + 20, bx.y + 15); await p.mouse.down(); await wait(400); await p.mouse.up(); await wait(400);
  const err = await p.$eval('.msg.error', n => ({ who: n.querySelector('.who').textContent, raw: n.querySelector('details') && !n.querySelector('details').open }));
  ok('voice error is said in plain words', err.who === 'Voice isn’t available just now', err.who);
  ok('the raw message is folded under Details', err.raw);
  await p.close();

  // 8. typing: the primary control turns from Hold to talk into Send; Enter sends
  p = await page();
  let asked = null;
  await p.setRequestInterception(true);
  p.on('request', r => { if (r.url().includes('/api/ask')) { asked = r.postData(); return r.respond({ status: 200, body: '{"ok":true}' }); } r.continue(); });
  await p.goto(`${BASE}/?${SK}&static=1`, { waitUntil: 'networkidle0' });
  const vis = sel => p.$eval(sel, n => getComputedStyle(n).display !== 'none');
  const before = [await vis('#talk'), await vis('#ask-form button')];
  await p.type('#ask-input', 'Who is in today?');
  const after = [await vis('#talk'), await vis('#ask-form button')];
  ok('empty: Hold to talk; typing: Send', before[0] && !before[1] && !after[0] && after[1], JSON.stringify({ before, after }));
  await p.keyboard.press('Enter'); await wait(300);
  ok('Enter sends the question', asked && JSON.parse(asked).text === 'Who is in today?');
  for (let i = 0; i < 3; i++) { await p.keyboard.press('Tab'); if (await p.evaluate(() => document.activeElement !== document.body)) break; }   // the composer is last on the page
  ok('keyboard focus is visible', await p.evaluate(() => { const a = document.activeElement; const s = getComputedStyle(a); return a && a !== document.body && s.outlineStyle !== 'none'; }));
  await p.close();

  // 9. light and dark; the inspector
  p = await page();
  await p.goto(`${BASE}/?${SK}&mock=1&turn=3&paused=1`, { waitUntil: 'networkidle0' });
  await wait(600);
  const ground = () => p.evaluate(() => getComputedStyle(document.body).backgroundColor);
  const light = await ground();
  await p.click('.icon-btn.theme'); await wait(150);
  const dark = await ground();
  ok('light by default (a warm ivory), the switch turns it dark', light === 'rgb(246, 244, 238)' && dark === 'rgb(31, 30, 28)', `${light} -> ${dark}`);
  ok('the choice is remembered', await p.evaluate(() => localStorage.getItem('barnaby-theme') === 'dark'));
  const q = await page();
  await q.goto(`${BASE}/?${SK}&theme=dark&static=1`, { waitUntil: 'networkidle0' });
  ok('?theme=dark opens dark', await q.evaluate(() => document.documentElement.dataset.theme === 'dark'));
  await q.close();
  const insp = await p.evaluate(() => { const i = document.getElementById('inspector'); return { shown: !i.hidden && i.getBoundingClientRect().width > 250, text: i.innerText }; });
  ok('the inspector shows the system and how much he can use', insp.shown && /He can use\s+6 of 23/.test(insp.text), insp.text.replace(/\s+/g, ' ').slice(0, 80));
  await p.click('.icon-btn.panel'); await wait(150);
  ok('…and folds away', await p.evaluate(() => getComputedStyle(document.getElementById('inspector')).display === 'none'));
  await p.close();

  // 10. what he can do: a word for every state, the new piece marked; technical names on request
  p = await page();
  await p.goto(`${BASE}/?${SK}&mock=1&turn=9&speed=20`, { waitUntil: 'networkidle0' });
  await wait(600); await p.click('#toggle-map'); await wait(200);
  const states = await p.$$eval('#map .ab', n => n.map(x => (x.querySelector('.state, .today') || {}).textContent));
  ok('every ability has its state in words', states.length > 20 && states.every(Boolean), `${states.length} abilities`);
  ok('the new report and the one-step are "Added today"; keys given today say so', states.filter(s => s === 'Added today').length >= 2 && states.filter(s => s === 'Key given today').length === 2);
  ok('kept shut is shown', states.includes('Kept shut'));
  const techShown = () => p.$$eval('#map .ab .tech', n => n.filter(x => x.offsetParent).length);
  ok('technical names are folded by default', await techShown() === 0);
  await p.click('.tech-toggle'); await wait(100);
  ok('…and shown on request', await techShown() > 20);
  ok('the inspector lists the keys and what he made', await p.evaluate(() => { const t = document.getElementById('inspector').innerText; return /Order parts from your suppliers/.test(t) && /weekly workload report/i.test(t) && /Hand back a bike in one step/.test(t); }));
  await p.close();

  // 11. the replay's own words and order: plain decisions, the yes before the act
  p = await page();
  await p.goto(`${BASE}/?${SK}&mock=1&turn=4&paused=1`, { waitUntil: 'networkidle0' });
  await wait(600);
  const dec = await p.$$eval('.msg.decision .text', n => n.map(x => x.textContent));
  ok('kept decisions name the thing, not its arguments', dec.some(t => /Ten pairs of the Shimano resin pads from Madison/.test(t)) && !dec.some(t => /part 1/.test(t)), dec.join(' | '));
  const order = await p.evaluate(() => {
    const yes = [...document.querySelectorAll('.msg.decision')].find(x => /Ten pairs/.test(x.textContent));
    const act = [...document.querySelectorAll('.act')].find(x => /Ordered more of a part/.test(x.textContent));
    return yes && act ? [+yes.style.order, +act.style.order] : null;
  });
  ok('the yes comes before the order it allowed', order && order[0] < order[1], JSON.stringify(order));
  await p.close();

  // 12. sizes: nothing spills sideways; Hold to talk and "Yes, add it" in view; no script errors
  for (const [w, h, qs] of [[1920, 1080, 'mock=1&turn=4&speed=20'], [1440, 900, 'mock=1&turn=4&speed=20'], [560, 860, 'mock=1&overlay=1&turn=4&speed=20'], [1440, 900, 'mock=1&turn=4&speed=20&theme=dark']]) {
    const s = await page(w, h);
    await s.goto(`${BASE}/?${SK}&${qs}`, { waitUntil: 'networkidle0' });
    await s.waitForSelector('#card-a3', { timeout: 30000 }); await wait(500);
    const r = await s.evaluate(() => ({
      over: document.documentElement.scrollWidth > innerWidth + 1,
      talk: (() => { const t = document.getElementById('talk').getBoundingClientRect(); return t.bottom <= innerHeight && t.top >= 0; })(),
      yes: (() => { const y = document.querySelector('#card-a3 .primary').getBoundingClientRect(); return y.bottom <= innerHeight && y.top >= 0; })(),
    }));
    ok(`${w}x${h}${/dark/.test(qs) ? ' dark' : ''}: no sideways overflow, talk and "Yes, add it" in view`, !r.over && r.talk && r.yes, JSON.stringify(r));
    ok(`${w}x${h}${/dark/.test(qs) ? ' dark' : ''}: no script errors`, s.errors.length === 0, s.errors.join(' / '));
    await s.close();
  }

  await b.close();
  console.log(fails ? `${fails} FAILED` : 'all passed');
  process.exit(fails ? 1 : 0);
})();
