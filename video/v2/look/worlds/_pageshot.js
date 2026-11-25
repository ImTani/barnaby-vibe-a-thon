/* Full-page screenshot of the decision page for review: node _pageshot.js [out.png] [width] */
const path = require('path');
const puppeteer = require(path.resolve(__dirname, '../../../node_modules/puppeteer-core'));
(async () => {
  const b = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true, args: ['--hide-scrollbars', '--allow-file-access-from-files'] });
  const p = await b.newPage(); let errs = 0;
  p.on('pageerror', e => { errs++; console.error('page error:', e.message); });
  await p.setViewport({ width: +(process.argv[3] || 1600), height: 1000 });
  await p.goto(require('url').pathToFileURL(path.join(__dirname, 'index.html')).href, { waitUntil: 'load' });
  await new Promise(r => setTimeout(r, 400));
  const out = path.resolve(process.argv[2] || path.join(__dirname, 'frames/_page.png'));
  await p.screenshot({ path: out, fullPage: true });
  console.log(out, await p.evaluate(() => document.body.scrollHeight)); await b.close(); process.exit(errs ? 2 : 0);
})();
