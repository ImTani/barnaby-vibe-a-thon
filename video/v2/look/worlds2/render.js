/* Film-world comps -> PNG. Run from anywhere:
 *   node video/v2/look/worlds2/render.js [substring ...]      renders comps/<name>.html -> frames/<name>.png (1920x1080)
 *   node video/v2/look/worlds2/render.js zoom <name> x,y,w,h   2x crop of one comp -> frames/_zoom-<name>.png
 *   node video/v2/look/worlds2/render.js panels [substring ...] comps/panels/<name>.html -> frames/panels/<name>.png (640x1080)
 * Uses video/node_modules/puppeteer-core and the installed Chrome; nothing is downloaded. A comp signals it is ready by
 * setting document.body.dataset.ready = '1' (after document.fonts.ready). */
const fs = require('fs');
const path = require('path');
const HERE = __dirname;
const VIDEO = path.resolve(HERE, '../../..');
const puppeteer = require(path.join(VIDEO, 'node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';

(async () => {
  let args = process.argv.slice(2);
  const panels = args[0] === 'panels'; if (panels) args = args.slice(1);
  const W = panels ? 640 : 1920, H = 1080;
  const COMPS = path.join(HERE, panels ? 'comps/panels' : 'comps'), OUT = path.join(HERE, panels ? 'frames/panels' : 'frames');
  const zoom = args[0] === 'zoom' ? { name: args[1], clip: args[2].split(',').map(Number) } : null;
  const names = fs.readdirSync(COMPS).filter(f => f.endsWith('.html') && !f.startsWith('_')).map(f => f.slice(0, -5))
    .filter(n => zoom ? n === zoom.name : (!args.length || args.some(a => n.includes(a))));
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true,
    args: ['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none', '--allow-file-access-from-files'] });
  const page = await browser.newPage();
  let errors = 0;
  page.on('pageerror', e => { errors++; console.error('page error:', e.message); });
  page.on('console', m => { if (m.type() === 'error') { errors++; console.error('console:', m.text()); } });
  await page.setViewport({ width: W, height: H, deviceScaleFactor: zoom ? 2 : 1 });
  for (const n of names) {
    await page.goto(require('url').pathToFileURL(path.join(COMPS, n + '.html')).href, { waitUntil: 'load' });
    await page.waitForSelector('body[data-ready="1"]', { timeout: 15000 });
    await new Promise(r => setTimeout(r, 150));
    const out = zoom ? path.join(OUT, `_zoom-${n}.png`) : path.join(OUT, n + '.png');
    const [x, y, width, height] = zoom ? zoom.clip : [0, 0, W, H];
    await page.screenshot({ path: out, clip: { x, y, width, height } });
    console.log(out);
  }
  await browser.close();
  process.exit(errors ? 2 : 0);
})().catch(e => { console.error(e); process.exit(1); });
