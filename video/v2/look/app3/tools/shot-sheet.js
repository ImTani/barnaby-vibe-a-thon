/* Renders the icon sheet (video/v2/look/app3/icon-sheet.html) to frames/app3-icons.png.
   node video/v2/look/app3/tools/shot-sheet.js */
const path = require('path');
const { pathToFileURL } = require('url');
const puppeteer = require(path.resolve(__dirname, '../../../../node_modules/puppeteer-core'));
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true,
    args: ['--force-device-scale-factor=1', '--hide-scrollbars', '--allow-file-access-from-files'] });
  const p = await b.newPage(); await p.setViewport({ width: 1600, height: 900 });
  await p.goto(pathToFileURL(path.resolve(__dirname, '../icon-sheet.html')).href, { waitUntil: 'load' });
  await new Promise(r => setTimeout(r, 600));
  const out = path.resolve(__dirname, '../frames/app3-icons.png');
  await p.screenshot({ path: out, fullPage: true });
  console.log(out);
  await b.close();
})();
