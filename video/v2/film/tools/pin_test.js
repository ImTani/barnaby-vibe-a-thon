/* Check the push into the screen with a made-up quad (no Blender needed): node tools/pin_test.js -> out/stills/pin_*.jpg
 * The fake manifest marks s1_open done with a screen_quad but points at no frames, so the room is the still. */
const path = require('path'), fs = require('fs');
const puppeteer = require(path.resolve(__dirname, '../../../node_modules/puppeteer-core'));
(async () => {
  const cues = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../cues.json'), 'utf8')), t0 = cues.marks.screen;
  const fake = { complete: false, fps: 24, shots: [{ id: 's1_open', scene: 1, replaces: ['world/none.png'], start: 0, frames: 1, status: 'done',
    screen_quad: [[812, 352], [1118, 360], [1112, 548], [808, 538]] }] };
  const b = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true, args: ['--allow-file-access-from-files', '--hide-scrollbars'] });
  const p = await b.newPage(); await p.setViewport({ width: 1920, height: 1080 });
  await p.evaluateOnNewDocument(m => { window.BLENDER = m; }, fake);
  await p.goto(require('url').pathToFileURL(path.resolve(__dirname, '../index.html')).href);
  await p.waitForFunction('window.__ready === true', { timeout: 120000 });
  for (const dt of [-.05, .05, .2, .4, .65]) {
    await p.evaluate(async t => { window.render(t); await window.settle(); }, t0 + dt);
    await p.screenshot({ path: path.resolve(__dirname, `../out/stills/pin_${dt}.jpg`), type: 'jpeg', quality: 85 });
  }
  console.log(await p.evaluate(() => window.__errors));
  await b.close();
})();
