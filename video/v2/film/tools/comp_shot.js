/* A worlds2 comp drawn with a film state, for a look:  node comp_shot.js <name> '<state json>' <out.jpg> [scale] */
const path = require('path');
const VIDEO = path.resolve(__dirname, '../../..');
const puppeteer = require(path.join(VIDEO, 'node_modules/puppeteer-core'));
(async () => {
  const [name, st, out, sc] = process.argv.slice(2);
  const b = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true, args: ['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none', '--allow-file-access-from-files'] });
  const p = await b.newPage(); await p.setViewport({ width: 1920, height: 1080, deviceScaleFactor: +(sc || .5) });
  p.on('pageerror', e => console.log('pageerror', e.message));
  await p.goto(require('url').pathToFileURL(path.join(VIDEO, 'v2/look/worlds2/comps', name + '.html')).href);
  await p.waitForSelector('body[data-ready="1"]');
  await p.evaluate(s => COMP.render(JSON.parse(s)), st || '{}');
  await p.screenshot({ path: out, type: 'jpeg', quality: 88 });
  await b.close();
})();
