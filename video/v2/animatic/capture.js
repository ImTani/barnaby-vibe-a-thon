/* Intermediate screen states for the animatic, rendered from the approved look-dev pages through their ?state= presets
 * (nothing about the designs changes: only the documented state keys are set). Writes assets/screens/<name>.jpg
 * at 1920x1080. Run from anywhere:   node video/v2/animatic/capture.js [filter ...]
 * Uses video/node_modules/puppeteer-core and the installed Chrome. Nothing is downloaded. */
const fs = require('fs');
const path = require('path');
const HERE = __dirname;
const VIDEO = path.resolve(HERE, '../..');
const puppeteer = require(path.join(VIDEO, 'node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const OUT = path.join(HERE, 'assets', 'screens');
const SHOP = 'file:///' + path.join(VIDEO, 'v2/look/shop-pc/index.html').replace(/\\/g, '/');
const LIS = 'file:///' + path.join(VIDEO, 'v2/look/lisbon-pc/index.html').replace(/\\/g, '/');

const TABS = ['shop', 'supplier', 'sms', 'xls', 'parts', 'invoices', 'email', 'bank', 'cal'];
const lerp = (a, b, k) => a + (b - a) * k;
const r2 = x => Math.round(x * 100) / 100;

function list() {
  const L = [];
  // 1 · nine tabs opening, Thu 19 Nov 21:47, the memory needle climbing into the red (preset `tabs` ends at .93)
  for (let k = 1; k <= 9; k++) {
    const f = (k - 1) / 8;
    L.push([`s1_tabs_${k}`, `${SHOP}?state=tabs&tabs=${TABS.slice(0, k).join(',')}&active=${TABS[k - 1]}&ram=${r2(lerp(.42, .93, f))}&cpu=${r2(lerp(.22, .71, f))}&blur=0`]);
  }
  // "Tab four." (workload.xls active), then the preset tabs-parts is "five" (approved frame 03b)
  L.push(['s1_tab4', `${SHOP}?state=tabs-parts&active=xls&blur=0`]);
  // 2 · he closes the tabs one by one (the rightmost first), then the desktop at night
  for (let k = 8; k >= 1; k--) {
    const f = (k - 1) / 8;
    L.push([`s2_close_${k}`, `${SHOP}?state=tabs&tabs=${TABS.slice(0, k).join(',')}&active=${TABS[k - 1]}&ram=${r2(lerp(.4, .9, f))}&cpu=${r2(lerp(.12, .5, f))}&cursor=&blur=0`]);
  }
  L.push(['s2_desktop_night', `${SHOP}?state=desktop&date=2026-11-19&time=21:47&ram=.36&cpu=.08&blur=0`]);
  // 4 · Purchase Orders, 09:04: order 3 sliding in
  L.push(['s4_po_0', `${SHOP}?state=shop-po&po=0&poHl=0&blur=0`]);
  L.push(['s4_po_5', `${SHOP}?state=shop-po&po=.5&poHl=.5&blur=0`]);
  // 6 · the reload at 16:16 (status bar loading over the old page), then the approved 07
  L.push(['s6_reload', `${SHOP}?state=shop-reports-soon&time=16:16&loading=.6&blur=0`]);
  // 6 · Dev -> Priya, 16:21 (approved 08 is reassign .62)
  L.push(['s6_reassign_0', `${SHOP}?state=shop-jobs-after&reassign=0&blur=0`]);
  L.push(['s6_reassign_4', `${SHOP}?state=shop-jobs-after&reassign=.4&blur=0`]);
  L.push(['s6_reassign_1', `${SHOP}?state=shop-jobs-after&reassign=1&blur=0`]);
  // 8 · Lisbon main monitor, 09:39-09:41: the real-app tile sliding in, then Barnaby's log as Synapse reads Quorum
  L.push(['s8_app_0', `${LIS}?monitor=main&state=realapp&app=0`, 'lis']);
  L.push(['s8_app_5', `${LIS}?monitor=main&state=realapp&app=.5`, 'lis']);
  L.push(['s8_log_4', `${LIS}?monitor=main&state=quorum&out=4&say=&sayK=0&plan=&mode=thinking&level=0&notify=0&time=09:40`, 'lis']);
  L.push(['s8_log_10', `${LIS}?monitor=main&state=quorum&out=10&sayK=0&planK=.4&mode=thinking&level=0&notify=0&time=09:40`, 'lis']);
  L.push(['s8_studio_q0', `${LIS}?monitor=studio&state=comfy&queueOpen=0&queueHl=0`, 'lis']);
  return L;
}

(async () => {
  const want = process.argv.slice(2);
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true,
    args: ['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none', '--allow-file-access-from-files'] });
  const page = await browser.newPage();
  let errors = 0;
  page.on('pageerror', e => { errors++; console.error('page error:', e.message); });
  for (const [name, url, kind] of list().filter(([n]) => !want.length || want.some(w => n.includes(w)))) {
    if (kind === 'lis') await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1.5 });
    else await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
    await page.goto(url, { waitUntil: 'load' });
    await page.waitForSelector('body[data-ready="1"]', { timeout: 15000 });
    await new Promise(r => setTimeout(r, 120));
    const out = path.join(OUT, name + '.jpg');
    await page.screenshot({ path: out, type: 'jpeg', quality: 92 });
    console.log(out);
  }
  await browser.close();
  process.exit(errors ? 2 : 0);
})().catch(e => { console.error(e); process.exit(1); });
