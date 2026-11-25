/* Which Blender frame plays at given film times (render-time manifest): node tools/event_check.js t1 t2 ... */
const path = require('path'), fs = require('fs');
const puppeteer = require(path.resolve(__dirname, '../../../node_modules/puppeteer-core'));
(async () => {
  const man = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../world/anim/shots.json'), 'utf8'));
  const b = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true, args: ['--allow-file-access-from-files', '--hide-scrollbars'] });
  const p = await b.newPage(); await p.setViewport({ width: 1920, height: 1080 });
  await p.evaluateOnNewDocument(m => { window.BLENDER = m; }, man);
  await p.goto(require('url').pathToFileURL(path.resolve(__dirname, '../index.html')).href);
  await p.waitForFunction('window.__ready === true', { timeout: 120000 });
  for (const t of process.argv.slice(2).map(Number)) {
    const r = await p.evaluate(async t => { window.render(t); await window.settle();
      const vis = [...document.querySelectorAll('.scene')].filter(s => s.style.display !== 'none').flatMap(s => [...s.querySelectorAll('.shot')].filter(b => b.style.display !== 'none'));
      return vis.map(b => { const im = b.querySelector('img'); return im ? im.getAttribute('src').replace(/^.*\/anim\//, 'anim/') : 'live'; }); }, t);
    console.log(t, r.join(' | '));
  }
  await b.close();
})();
