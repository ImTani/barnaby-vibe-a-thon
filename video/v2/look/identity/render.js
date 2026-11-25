/* Identity look-dev renderer. Run from anywhere:  node video/v2/look/identity/render.js [direction ...] [--only 1,3b] [--compare]
   1. writes <direction>/content.js = _content.js + the real run's data (video/data.js), so each folder is self-contained;
   2. screenshots every moment of every direction at 1920x1080 into frames/<direction>-<moment>.png.
   3. --compare renders compare.html (the three directions side by side, one moment per sheet) into frames/_compare-<moment>.png.
   Uses video/node_modules/puppeteer-core and the installed Chrome. Nothing is downloaded. */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const HERE = __dirname;
const VIDEO = path.resolve(HERE, '../../..');
const puppeteer = require(path.join(VIDEO, 'node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const DIRECTIONS = ['job-card', 'livery', 'bell-board'];
const MOMENTS = ['0', '1a', '1', '2', '3', '3b', '4', '5', '6'];  // 0 identity sheet · 1a working · 1 answer · 2 key · 3 change · 3b change opened · 4 Martin · 5 Theo · 6 Priya

function realData() {
  const ctx = { window: {} };
  vm.runInNewContext(fs.readFileSync(path.join(VIDEO, 'data.js'), 'utf8'), ctx);
  const D = ctx.window.DATA;
  return { endpoints: D.endpoints, starter: D.starter, diff: D.build.diff, tested: D.build.tested, built: D.build.endpoints, gitlog: D.gitlog };
}

function writeContent(dirs) {
  const src = fs.readFileSync(path.join(HERE, '_content.js'), 'utf8');
  const data = realData();
  // every real ability must be in exactly one room
  const ctx = { window: {} };
  vm.runInNewContext(src, ctx);
  const inRooms = ctx.window.STORY.rooms.flatMap(r => r.items.map(i => i[0]));
  const all = [...data.endpoints.map(e => e.key), ...data.built];
  const missing = all.filter(k => !inRooms.includes(k));
  const extra = inRooms.filter(k => !all.includes(k));
  if (missing.length || extra.length || inRooms.length !== all.length) {
    throw new Error(`rooms don't match the real abilities: missing ${missing} extra ${extra}`);
  }
  const out = `${src}\n/* the real run (generated from video/data.js) */\nwindow.STORY.real = ${JSON.stringify(data)};\n`;
  for (const d of dirs) fs.writeFileSync(path.join(HERE, d, 'content.js'), out);
  console.log(`content: ${all.length} abilities in ${ctx.window.STORY.rooms.length} rooms -> ${dirs.join(', ')}`);
}

(async () => {
  const args = process.argv.slice(2);
  const oi = args.indexOf('--only');
  const only = oi >= 0 ? args.splice(oi, 2)[1].split(',') : MOMENTS;
  const ci = args.indexOf('--compare');              // --compare: the side-by-side sheets from frames already rendered
  const compare = ci >= 0 && args.splice(ci, 1);
  const dirs = compare ? [] : args.length ? args : DIRECTIONS;
  if (dirs.length) writeContent(dirs);
  fs.mkdirSync(path.join(HERE, 'frames'), { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true,
    args: ['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('page error:', e.message));
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warn') console.error('console:', m.text()); });
  if (compare) {
    for (const m of only) {
      await page.goto('file:///' + path.join(HERE, 'compare.html').replace(/\\/g, '/') + `?m=${m}`, { waitUntil: 'load' });
      await new Promise(r => setTimeout(r, 200));
      const out = path.join(HERE, 'frames', `_compare-${m}.png`);
      await page.screenshot({ path: out });
      console.log(out);
    }
  }
  for (const d of dirs) {
    for (const m of only) {
      const url = 'file:///' + path.join(HERE, d, 'index.html').replace(/\\/g, '/') + `?m=${m}&still=1`;
      await page.goto(url, { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
      await new Promise(r => setTimeout(r, 150));
      const out = path.join(HERE, 'frames', `${d}-${m}.png`);
      await page.screenshot({ path: out });
      console.log(out);
    }
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
