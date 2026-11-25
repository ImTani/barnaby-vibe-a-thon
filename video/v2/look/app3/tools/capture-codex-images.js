/* The Codex desktop-app screenshots shown on https://openai.com/codex/ , rendered at their natural size into ../refs/.
   The page itself answers headless Chrome with a bot challenge, so it was opened in an ordinary browser (cookies:
   "Reject non-essential"), the product images' addresses were read from it, and only those images are rendered here.
   node video/v2/look/app3/tools/capture-codex-images.js */
const path = require('path'), fs = require('fs');
const puppeteer = require(path.resolve(__dirname, '../../../../node_modules/puppeteer-core'));
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const OUT = path.resolve(__dirname, '../refs');
const CDN = 'https://images.ctfassets.net/kftzwdyauwt9/';
const SHOTS = [
  ['codex-new-task-dark', '4QumXadILq80dZ6wg8Ty8C/6030766fdaf6ab00e0d9a3794bd7d480/figma-codexmini-desktop-dark.png'],
  ['codex-task-progress-review', '3Oi7squKBZwF5QsKY8n8iJ/20344a07080e252f389f7806a32a5b41/figma-builtDesktop.png'],
  ['codex-parallel-agents', '4baKFoCwcNWcZG3AlIgUTv/c1734650b683d79a9333d448fcde684d/figma-designedDesktop.png'],
  ['codex-code-review-pr', '3GDuk6TAsJfjD6E5d1fIe0/aa9e210b9c6e065814ae06af00916cff/Scale_-_Dark.png'],
  ['codex-sidebar-tasks', '5kCPrE8dvckkGbzFQzZrMp/fd80e1499471614430fdf615c9b6a0a7/ChatGPT-1.png'],
  ['codex-work-location-menu', '4yPFRrrlboBU46RA9kx0lI/137f4713b0de1cb9410f9f804bb7d07e/Cloud-1.png'],
  ['codex-edited-files-review', '1KMqKRVQrp4xaSTFN6qYxH/f18c309d8140a5c4308c15c7eca6a2ed/IDE-1.png'],
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--force-device-scale-factor=1', '--hide-scrollbars'] });
  for (const [name, rel] of SHOTS) {
    const p = await b.newPage();
    await p.setViewport({ width: 1600, height: 1300 });
    await p.setContent(`<body style="margin:0;background:#000"><img id="i" src="${CDN}${rel}?w=1920&q=90&fm=png" style="display:block"></body>`, { waitUntil: 'networkidle0', timeout: 60000 });
    const sz = await p.$eval('#i', i => ({ w: i.naturalWidth, h: i.naturalHeight }));
    if (!sz.w) { console.error(name, 'did not load'); await p.close(); continue; }
    await p.setViewport({ width: sz.w, height: sz.h });
    const out = path.join(OUT, name + '.png');
    await p.screenshot({ path: out, clip: { x: 0, y: 0, width: sz.w, height: sz.h } });
    console.log(out, `${sz.w}x${sz.h}`);
    await p.close();
  }
  await b.close();
})().catch(e => { console.error(e.message); process.exit(1); });
