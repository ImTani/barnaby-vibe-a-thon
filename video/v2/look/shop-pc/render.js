/* Shop PC stills. Run from anywhere:  node video/v2/look/shop-pc/render.js [name ...]
 * Screenshots each preset at 1920x1080 into video/v2/look/frames/shop-pc-<nn>-<name>.png using
 * video/node_modules/puppeteer-core and the installed Chrome. Nothing is downloaded. */
const fs = require('fs');
const path = require('path');

const HERE = __dirname;
const VIDEO = path.resolve(HERE, '../../..');
const OUT = path.resolve(HERE, '../frames');
const puppeteer = require(path.join(VIDEO, 'node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';

const STILLS = [
  ['01-desktop', 'state=desktop'],
  ['02-start', 'state=start'],
  ['03-tabs', 'state=tabs'],
  ['03b-tabs-parts', 'state=tabs-parts'],
  ['03c-tabs-busy', 'state=tabs-busy'],
  ['04-shop-jobs', 'state=shop-jobs'],
  ['05-shop-po', 'state=shop-po'],
  ['06-shop-reports-soon', 'state=shop-reports-soon'],
  ['07-shop-reports', 'state=shop-reports'],
  ['08-shop-jobs-after', 'state=shop-jobs-after'],
  ['09-barnaby-slot', 'state=barnaby'],
  ['09b-barnaby-frame', 'state=barnaby-frame'],
  ['10-tabs-opening', 'state=tabs&tabs=shop,supplier,sms,xls&tabIn=.55&ram=.58&cpu=.34&time=21:46&cursor=700,300'],
  ['12-desktop-16x10', 'state=shop-jobs&lw=1280&lh=800', 1200],   // the 3D monitor is 16:10: same desktop, 80 more lines
];

/** A review sheet: the eight non-shop tabs, each as it looks when active, tiled 4x2 at 1920x1080. */
async function sheet(page, out) {
  const ids = ['supplier', 'sms', 'xls', 'invoices', 'parts', 'email', 'bank', 'cal'];
  const url = 'file:///' + path.join(HERE, 'index.html').replace(/\\/g, '/');
  const shots = [];
  for (const id of ids) {
    await page.goto(`${url}?state=tabs&active=${id}&cursor=`, { waitUntil: 'load' });
    await page.waitForSelector('body[data-ready="1"]', { timeout: 10000 });
    shots.push((await page.screenshot({ encoding: 'base64', clip: { x: 0, y: 0, width: 1920, height: 1080 } })));
  }
  await page.setViewport({ width: 1920, height: 2160, deviceScaleFactor: 1 });
  await page.setContent(`<body style="margin:0;background:#111;display:grid;grid-template-columns:repeat(2,960px);grid-template-rows:repeat(4,540px)">${shots.map((b, i) => `<div style="position:relative"><img style="width:960px;height:540px;display:block" src="data:image/png;base64,${b}"><span style="position:absolute;left:8px;bottom:6px;font:bold 18px Segoe UI;color:#fff;background:#000b;padding:2px 8px">${ids[i]}</span></div>`).join('')}</body>`);
  await page.screenshot({ path: out });
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  console.log(out);
}

/** The film's rule: render() is a pure function of state. For each preset A: re-render A (reference), then render B
 * (with every animatable value pushed off its default), then A again, in the same page. A leak is any pixel more than
 * 32/255 off; below that it's text antialiasing / glass-compositing noise (use ?blur=0 for bit-exact frames). */
async function verify(page, browser) {
  const url = 'file:///' + path.join(HERE, 'index.html').replace(/\\/g, '/');
  const names = ['desktop', 'start', 'tabs', 'tabs-parts', 'tabs-busy', 'shop-jobs', 'shop-po', 'shop-reports-soon', 'shop-reports', 'shop-jobs-after', 'shop-tuesday', 'barnaby', 'barnaby-frame'];
  let bad = 0;
  for (let i = 0; i < names.length; i++) {
    const a = names[i], b = names[(i + 5) % names.length];
    await page.goto(`${url}?state=${a}${process.env.NOBLUR ? '&blur=0' : ''}`, { waitUntil: 'load' });
    await page.waitForSelector('body[data-ready="1"]', { timeout: 10000 });
    await page.evaluate(a => pc.render(pc.preset(a)), a);
    const first = await page.screenshot({ encoding: 'base64' });
    await page.evaluate((a, b) => { pc.render(pc.preset(b, { po: .3, poHl: .5, reassign: .9, handedBack: 2, scroll: 120, marquee: 333, start: .6, tabIn: .2, dim: .4, secs: 17 })); pc.render(pc.preset(a)); }, a, b);
    const again = await page.screenshot({ encoding: 'base64' });
    const r = await page.evaluate(async (x, y) => {   // decode + compare off-DOM, in the same tab
      const load = s => new Promise(res => { const im = new Image(); im.onload = () => res(im); im.src = 'data:image/png;base64,' + s; });
      const [ia, ib] = await Promise.all([load(x), load(y)]);
      const c = document.createElement('canvas'); c.width = ia.width; c.height = ia.height; const g = c.getContext('2d');
      g.drawImage(ia, 0, 0); const A = g.getImageData(0, 0, c.width, c.height).data; g.drawImage(ib, 0, 0); const B = g.getImageData(0, 0, c.width, c.height).data;
      let n = 0, big = 0, mx = 0;
      for (let k = 0; k < A.length; k += 4) { const d = Math.max(Math.abs(A[k] - B[k]), Math.abs(A[k + 1] - B[k + 1]), Math.abs(A[k + 2] - B[k + 2])); if (d) { n++; if (d > 32) big++; if (d > mx) mx = d; } }
      return { n, big, mx };
    }, first, again);
    if (r.big) { bad++; fs.writeFileSync(path.join(OUT, `_verify_${a}_a.png`), Buffer.from(first, 'base64')); fs.writeFileSync(path.join(OUT, `_verify_${a}_b.png`), Buffer.from(again, 'base64')); }
    console.log(`${r.big ? 'LEAK' : r.n ? 'ok~ ' : 'ok  '} ${a} (via ${b})  ${r.n} px differ, max ${r.mx}/255, ${r.big} over 32`);
  }
  console.log(bad ? `${bad} state(s) leaked` : 'no leaks: every preset is a function of its state');
}

(async () => {
  let want = process.argv.slice(2);
  // detail check:  node render.js zoom "<query>" x,y,w,h out.png   (2x crop of the 1920x1080 frame)
  const zoom = want[0] === 'zoom' ? { qs: want[1], clip: want[2].split(',').map(Number), out: want[3] } : null;
  if (zoom) want = [];
  const list = want.length ? STILLS.filter(([n]) => want.some(w => n.includes(w))) : STILLS;
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true,
    args: ['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none', '--allow-file-access-from-files'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: zoom ? 2 : 1 });
  if (want[0] === 'verify') { await verify(page, browser); await browser.close(); return; }
  if (!zoom && (!want.length || want.some(w => 'sheet'.includes(w) || w === 'sheet'))) await sheet(page, path.join(OUT, 'shop-pc-11-tab-pages-sheet.png'));
  if (zoom) {
    const [x, y, width, height] = zoom.clip;
    await page.goto('file:///' + path.join(HERE, 'index.html').replace(/\\/g, '/') + '?' + zoom.qs, { waitUntil: 'load' });
    await page.waitForSelector('body[data-ready="1"]', { timeout: 10000 });
    await page.screenshot({ path: path.resolve(zoom.out), clip: { x, y, width, height } });
    console.log(path.resolve(zoom.out));
    await browser.close();
    return;
  }
  let errors = 0;
  page.on('pageerror', e => { errors++; console.error('page error:', e.message); });
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.error('console:', m.text()); });
  const url = 'file:///' + path.join(HERE, 'index.html').replace(/\\/g, '/');
  for (const [name, qs, h = 1080] of list) {
    await page.setViewport({ width: 1920, height: h, deviceScaleFactor: 1 });
    await page.goto(`${url}?${qs}`, { waitUntil: 'load' });
    await page.waitForSelector('body[data-ready="1"]', { timeout: 10000 });
    await new Promise(r => setTimeout(r, 120));
    const out = path.join(OUT, `shop-pc-${name}.png`);
    await page.screenshot({ path: out });
    console.log(out);
  }
  await browser.close();
  process.exit(errors ? 2 : 0);
})().catch(e => { console.error(e); process.exit(1); });
