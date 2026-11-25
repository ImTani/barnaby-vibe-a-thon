/* Captures the Codex app UI shown on the public product page (https://openai.com/codex/) for the round-3 reference study.
   Headless Chrome; declines non-essential cookies when a banner offers it; never signs in, never accepts anything.
   node video/v2/look/app3/tools/capture-codex.js [--probe]
   --probe: full-page shot + a list of the large images/videos and their positions (to find the app screenshots).
   Otherwise: screenshots of each large product visual into ../refs/codex-*.png. */
const path = require('path'), fs = require('fs');
const puppeteer = require(path.resolve(__dirname, '../../../../node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'https://openai.com/codex/';
const OUT = path.resolve(__dirname, '../refs');
const probe = process.argv.includes('--probe');
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--force-device-scale-factor=1', '--hide-scrollbars'] });
  const p = await b.newPage();
  await p.setViewport({ width: 1440, height: 900 });
  const res = await p.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  console.log('status', res && res.status(), 'title', await p.title());
  await wait(2500);
  // decline non-essential cookies if a banner offers it (never accept)
  const declined = await p.evaluate(() => {
    const words = /^(reject( all)?|decline( all)?|necessary only|only necessary|reject non-essential|use necessary cookies only)$/i;
    const btn = [...document.querySelectorAll('button, a[role="button"]')].find(x => words.test((x.textContent || '').trim()));
    if (btn) { btn.click(); return btn.textContent.trim(); }
    return '';
  });
  console.log('cookies:', declined || 'no decline button found');
  await wait(1200);
  // scroll through so lazy media load
  const H = await p.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < H; y += 700) { await p.evaluate(v => window.scrollTo(0, v), y); await wait(350); }
  await p.evaluate(() => window.scrollTo(0, 0)); await wait(800);
  const media = await p.evaluate(() => [...document.querySelectorAll('img, video, picture, canvas')].map(n => {
    const r = n.getBoundingClientRect();
    return { tag: n.tagName, w: Math.round(r.width), h: Math.round(r.height), top: Math.round(r.top + scrollY), left: Math.round(r.left),
      alt: (n.getAttribute('alt') || n.getAttribute('aria-label') || '').slice(0, 80), src: (n.currentSrc || n.src || n.poster || '').slice(0, 90) };
  }).filter(m => m.w >= 500 && m.h >= 280));
  if (probe) {
    console.log(JSON.stringify(media, null, 1));
    console.log('page height', await p.evaluate(() => document.documentElement.scrollHeight));
    await p.screenshot({ path: path.join(OUT, 'codex-page-full.png'), fullPage: true });
    console.log('wrote refs/codex-page-full.png');
  } else {
    let i = 0;
    for (const m of media) {
      await p.evaluate(y => window.scrollTo(0, Math.max(0, y - 60)), m.top); await wait(900);
      const clip = await p.evaluate((top, left, w, h) => ({ x: Math.max(0, left), y: top - scrollY, width: Math.min(w, innerWidth), height: Math.min(h, innerHeight) }), m.top, m.left, m.w, m.h);
      if (clip.y < 0 || clip.height < 200) continue;
      const out = path.join(OUT, `codex-ui-${++i}.png`);
      await p.screenshot({ path: out, clip });
      console.log(out, `${m.w}x${m.h}`, m.alt);
    }
  }
  await b.close();
})().catch(e => { console.error(e.message); process.exit(1); });
