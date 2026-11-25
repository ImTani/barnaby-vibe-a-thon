/* Drives the real display in each skin and checks that every feature still works (no screenshots).
   Needs the core running (.venv/Scripts/python -m barnaby serve). The connect POST is intercepted, so nothing is
   connected for real.   node video/v2/look/app/check.js [--skins default,signpost,ticket] */
const path = require('path');
const puppeteer = require(path.resolve(__dirname, '../../../node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.env.BARNABY_URL || 'http://127.0.0.1:8700';
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const skins = arg('skins', 'default,signpost,ticket').split(',');
const wait = ms => new Promise(r => setTimeout(r, ms));
const url = (skin, q) => `${BASE}/?${q}${skin === 'default' ? '' : '&skin=' + skin}`;

(async () => {
  const b = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'] });
  let fails = 0;
  const ok = (skin, what, cond, extra = '') => { if (!cond) fails++; console.log(`${cond ? 'PASS' : 'FAIL'}  ${skin.padEnd(9)} ${what}${extra ? '  (' + extra + ')' : ''}`); };
  for (const skin of skins) {
    const p = await b.newPage();
    const errors = [];
    p.on('pageerror', e => errors.push(e.message));
    await p.setViewport({ width: 1440, height: 900 });
    await p.setRequestInterception(true);
    let connectBody = null, approvals = [];
    p.on('request', r => {
      const u = r.url();
      if (u.includes('/api/connect')) { connectBody = r.postData(); return r.respond({ status: 200, contentType: 'application/json', body: '{"ok":true}' }); }
      if (u.includes('/api/voice/offer')) return r.respond({ status: 503, body: 'no voice bot in this check' });
      r.continue();
    });

    // 1. the replay: answer, then the key card, approve it by click, the replay carries on
    await p.goto(url(skin, 'mock=1&turn=3&speed=20'), { waitUntil: 'networkidle0' });
    await p.waitForSelector('#card-a1', { timeout: 20000 });
    ok(skin, 'unlock card shows', true);
    const card = await p.$eval('#card-a1', n => ({ text: n.innerText, buttons: [...n.querySelectorAll('button')].map(x => x.textContent) }));
    if (skin !== 'default') ok(skin, 'card leads with the plain title', /order parts from your suppliers/i.test(card.text.split('\n')[0]));
    ok(skin, 'card has yes and no', card.buttons.length === 2, card.buttons.join(' | '));
    await p.click('#card-a1 button.primary');
    await p.waitForSelector('#card-a2', { timeout: 20000 });
    ok(skin, 'click approves; replay continues to the next card', true);
    if (skin !== 'default') ok(skin, 'the yes is kept in the conversation', await p.$$eval('.msg.decision.yes', n => n.length) >= 1);
    await p.keyboard.press('y');                                     // mock: Y approves the open card
    await wait(400);
    ok(skin, 'Y key approves', !(await p.$('#card-a2')));
    const acts = await p.$$eval('#trace li', n => n.map(x => x.innerText.trim()).filter(Boolean));
    ok(skin, 'activity is listed', acts.length > 5, acts.length + ' rows');
    if (skin !== 'default') {
      ok(skin, 'activity reads in plain words', acts.some(t => /^Looked at repair jobs due on/m.test(t)), acts.find(t => /due/.test(t)) || '');
      ok(skin, 'no developer words in activity', !acts.some(t => /endpoint|\bAPI\b|\btool\b|MCP/i.test(t.split('\n')[0])));
      const opened = await p.evaluate(() => { const d = document.querySelector('#trace .tr.step details'); if (!d) return ''; d.open = true; return d.querySelector('.technical-body').textContent; });
      ok(skin, 'technical detail folded under a step', opened.trim().length > 0, opened.slice(0, 50).replace(/\n/g, ' '));
    }

    // 2. the Build card: the summary, See the change, technical detail
    await p.goto(url(skin, 'mock=1&turn=4&speed=20'), { waitUntil: 'networkidle0' });
    await p.waitForSelector('#card-a3', { timeout: 30000 });
    const build = await p.$eval('#card-a3', n => n.innerText);
    for (const w of ['reads', 'changes', '19 checks', 'undone']) ok(skin, `build card says "${w}"`, build.toLowerCase().includes(w));
    await p.click('#card-a3 details.change > summary');
    await wait(300);
    const diffShown = await p.$eval('#card-a3 details.change', d => d.open && d.querySelectorAll('.diff .add').length);
    ok(skin, 'See the change opens the diff', diffShown > 50, diffShown + ' added lines');
    ok(skin, 'technical detail is folded', await p.$eval('#card-a3 details.technical', d => !d.open));
    const hint = await p.$eval('#card-a3 .hint', n => n.textContent);
    ok(skin, 'build is click only', /click/i.test(hint), hint);

    // 3. compose
    await p.goto(url(skin, 'mock=1&turn=6&speed=20'), { waitUntil: 'networkidle0' });
    await p.waitForSelector('#card-a7', { timeout: 30000 });
    ok(skin, 'compose card shows', /Hand back a bike in one step/.test(await p.$eval('#card-a7', n => n.innerText)));
    await p.click('#card-a7 button.secondary, #card-a7 button:not(.primary)');
    await wait(500);
    if (skin !== 'default') ok(skin, 'not now is kept', await p.$$eval('.msg.decision.no', n => n.length) === 1);

    // 4. hold to talk (fake mic; the voice bot is absent, so it reports that, as before)
    await p.goto(url(skin, 'mock=1&turn=2&paused=1'), { waitUntil: 'networkidle0' });
    const talk = await p.$('#talk');
    const box = await talk.boundingBox();
    await p.mouse.move(box.x + 20, box.y + 20); await p.mouse.down(); await wait(250);
    const holding = await p.evaluate(() => document.getElementById('talk').classList.contains('on') && document.body.classList.contains('s-listening'));
    await p.mouse.up(); await wait(400);
    ok(skin, 'hold to talk lights while held', holding);
    ok(skin, 'and lets go', !(await p.$eval('#talk', n => n.classList.contains('on'))));
    ok(skin, 'talk button keeps its label', /Hold to talk|Connecting/.test(await p.$eval('#talk .label', n => n.textContent)));

    // 5. empty state + the capabilities drawer with the connect form
    await p.goto(url(skin, 'static=1'), { waitUntil: 'networkidle0' });
    ok(skin, 'empty state greets', /Good day/.test(await p.$eval('#messages', n => n.innerText)));
    await p.click('#toggle-map');
    ok(skin, 'drawer opens', await p.$eval('#map', n => !n.hidden && n.getBoundingClientRect().width > 300));
    const covered = await p.evaluate(() => {         // is any conversation text under the drawer?
      const m = document.getElementById('map').getBoundingClientRect();
      return [...document.querySelectorAll('#messages .text')].some(t => { const r = t.getBoundingClientRect(); return r.right > m.left + 2 && r.width > 0; });
    });
    if (skin !== 'default') ok(skin, 'nothing half-covered by the drawer', !covered);
    await p.type('#connect-form input[name="name"]', 'shop');
    await p.type('#connect-form input[name="repo"]', 'X:\\shop');
    await p.type('#connect-form input[name="base_url"]', 'http://127.0.0.1:8101');
    await p.click('#connect-form button[type="submit"]');
    await wait(400);
    ok(skin, 'connect form posts', connectBody && JSON.parse(connectBody).repo === 'X:\\shop', connectBody || 'no request');
    await p.click('#close-map');
    ok(skin, 'drawer closes', await p.$eval('#map', n => n.hidden));
    // the drawer with a system in it
    await p.goto(url(skin, 'mock=1&turn=7&speed=20'), { waitUntil: 'networkidle0' });
    await wait(600);
    await p.click('#toggle-map'); await wait(200);
    const mapText = await p.$eval('#map-body', n => n.innerText);
    ok(skin, 'drawer lists what the system can do', skin === 'default' ? /GET \/api/.test(mapText) : /Repair jobs due on a given day/i.test(mapText), mapText.slice(0, 60).replace(/\n/g, ' '));

    // 6. overlay
    await p.setViewport({ width: 560, height: 860 });
    await p.goto(url(skin, 'mock=1&overlay=1&turn=3&speed=20'), { waitUntil: 'networkidle0' });
    await p.waitForSelector('#card-a1', { timeout: 20000 });
    ok(skin, 'overlay hides the activity column', await p.$eval('.trace', n => getComputedStyle(n).display === 'none'));
    const overflow = await p.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
    ok(skin, 'overlay has no sideways overflow', !overflow);

    ok(skin, 'no script errors', errors.length === 0, errors.join(' / '));
    await p.close();
  }
  await b.close();
  console.log(fails ? `${fails} FAILED` : 'all passed');
  process.exit(fails ? 1 : 0);
})();
