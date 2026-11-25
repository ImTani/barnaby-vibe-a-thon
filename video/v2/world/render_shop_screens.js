/* The shop PC's screens for the 3D monitor, at its own 16:10 shape (1920x1200, the page's lw=1280&lh=800 layout),
 * rendered from the look-dev page (video/v2/look/shop-pc/index.html) with video/node_modules/puppeteer-core and the
 * installed Chrome. Nothing is downloaded. Called by make_screens.py; or run:
 *     node video/v2/world/render_shop_screens.js
 * Writes video/v2/world/screens/shop-<name>-16x10.png. */
const fs = require('fs');
const path = require('path');

const HERE = __dirname;
const VIDEO = path.resolve(HERE, '../..');
const PAGE = path.resolve(HERE, '../look/shop-pc/index.html');
const OUT = path.join(HERE, 'screens');
const puppeteer = require(path.join(VIDEO, 'node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';

const SHOTS = [
  // Thursday 19 Nov, 21:47: the nine tabs, the calendar active, the memory needle in the red (scenes 1-2)
  ['night', 'state=tabs'],
  // Tuesday 24 Nov, 08:34 (scene 7): Theo's Jobs page as the shop prints it that morning, Dev's two wheel builds now
  // Priya's, Monday's four hand-backs collected on Monday evening (look-dev preset shop-tuesday)
  ['tuesday', 'state=shop-tuesday'],
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true,
    args: ['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none', '--allow-file-access-from-files'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1200, deviceScaleFactor: 1 });
  let errors = 0;
  page.on('pageerror', e => { errors++; console.error('page error:', e.message); });
  const url = 'file:///' + PAGE.replace(/\\/g, '/');
  for (const [name, qs] of SHOTS) {
    await page.goto(`${url}?${qs}&lw=1280&lh=800&blur=0`, { waitUntil: 'load' });
    await page.waitForSelector('body[data-ready="1"]', { timeout: 10000 });
    await new Promise(r => setTimeout(r, 150));
    const out = path.join(OUT, `shop-${name}-16x10.png`);
    await page.screenshot({ path: out });
    console.log(out);
  }
  await browser.close();
  process.exit(errors ? 2 : 0);
})().catch(e => { console.error(e); process.exit(1); });
