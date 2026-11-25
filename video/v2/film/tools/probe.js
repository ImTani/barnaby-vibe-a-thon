// debug probe: node tools/probe.js <t> "<js expression evaluated in the page after render(t)>"
const path = require('path'); const puppeteer = require(path.resolve(__dirname, '../../../node_modules/puppeteer-core'));
(async () => {
  const b = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true, args: ['--allow-file-access-from-files', '--hide-scrollbars'] });
  const p = await b.newPage(); await p.setViewport({ width: 1920, height: 1080 });
  p.on('console', m => console.log('[console]', m.text())); p.on('pageerror', e => console.log('[pageerror]', e.message));
  await p.goto(require('url').pathToFileURL(path.resolve(__dirname, '../index.html')).href);
  await p.waitForFunction('window.__ready === true', { timeout: 120000 });
  const t = +process.argv[2];
  console.log(await p.evaluate(async (t, ex) => { window.render(t); await window.settle(); return JSON.stringify(eval(ex)); }, t, process.argv[3] || 'window.__errors'));
  await b.close();
})();
