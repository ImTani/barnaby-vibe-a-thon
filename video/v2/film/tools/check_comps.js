/* Purity check for the film's state keys in the worlds2 comps: each comp, drawn with no state, must match its approved
 * frame (look/worlds2/frames/<name>.png) pixel for pixel, both at page load and again after COMP.render() has drawn
 * a film state in between (the redraw keeps nothing from the last state). Reports max channel difference.
 *   node video/v2/film/tools/check_comps.js [name ...]
 * Uses video/node_modules/puppeteer-core and the installed Chrome; nothing is downloaded or written. */
const fs = require('fs'), path = require('path');
const VIDEO = path.resolve(__dirname, '../../..');
const puppeteer = require(path.join(VIDEO, 'node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const COMPS = path.join(VIDEO, 'v2/look/worlds2/comps'), FRAMES = path.join(VIDEO, 'v2/look/worlds2/frames');
// a film state per comp, drawn between the two checks
const PROBE = {
  'theo-handover-1-reading': { scan: 4, heardK: .3 }, 'theo-handover-2-taken': { lit: 2.5, sayK: .4, counts: 0 },
  'theo-handover-pc': { lit: 3, sayK: .2 }, 'martin-key': { walk: .3, pads: 0, ask: 0, card: .5, say: .2, martin: 0, time: '08:53', keyTurn: .5, press: 1 },
  'martin-build': { room: .4, passage: .5, side: 'handback', cards: 1, allowed: 1, marker: [7, 6], walk: .5, walkN: 1 },
  'same-butler': { files: 1.5, tests: 11, added: 0, say: .3 }, 'priya-tuesday': { cards: .5, note: 0, say: .5 },
  'theo-lisbon': { lit: 2, sayK: .3 },
};
(async () => {
  const want = process.argv.slice(2);
  const names = Object.keys(PROBE).filter(n => fs.existsSync(path.join(COMPS, n + '.html')) && (!want.length || want.includes(n)));
  const b = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none', '--allow-file-access-from-files'] });
  const p = await b.newPage(); await p.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  let bad = 0;
  const cmp = async (shot, ref) => p.evaluate(async (a, r) => {
    const load = src => new Promise(res => { const i = new Image(); i.onload = () => res(i); i.src = src; });
    const [A, R] = await Promise.all([load('data:image/png;base64,' + a), load(r)]);
    const px = im => { const c = document.createElement('canvas'); c.width = 1920; c.height = 1080; const x = c.getContext('2d'); x.drawImage(im, 0, 0); return x.getImageData(0, 0, 1920, 1080).data; };
    const da = px(A), dr = px(R); let max = 0, n = 0;
    for (let i = 0; i < da.length; i++) { const d = Math.abs(da[i] - dr[i]); if (d) { n++; if (d > max) max = d; } }
    return { max, n };
  }, shot.toString('base64'), require('url').pathToFileURL(path.join(FRAMES, path.basename(ref))).href);
  for (const n of names) {
    await p.goto(require('url').pathToFileURL(path.join(COMPS, n + '.html')).href, { waitUntil: 'load' });
    await p.waitForSelector('body[data-ready="1"]', { timeout: 15000 });
    await new Promise(r => setTimeout(r, 150));
    const has = await p.evaluate(() => !!(window.COMP && window.COMP.render));
    const a = await cmp(await p.screenshot({ type: 'png' }), n + '.png');
    let c = { max: 0, n: 0 };
    if (has) {
      await p.evaluate(s => { COMP.render(s); COMP.render(); }, PROBE[n]);
      await new Promise(r => setTimeout(r, 50));
      c = await cmp(await p.screenshot({ type: 'png' }), n + '.png');
    }
    const noise = r => r.n === 0 || (r.max <= 1 && r.n < 2000);       // +-1 level on a few px: the raster's own noise, run to run
    const ok = noise(a) && noise(c);
    if (!ok) bad++;
    console.log(`${ok ? 'OK  ' : 'DIFF'} ${n}: load ${a.n} px differ (max ${a.max}); after a film state and back ${has ? `${c.n} px (max ${c.max})` : 'no COMP API'}`);
  }
  await b.close(); process.exit(bad ? 2 : 0);
})().catch(e => { console.error(e); process.exit(1); });
