"""Guards for the last renders: a Blender frame that is missing (deleted mid-render) falls back to its shot's still for
that frame, logged, not an error; and the encode refuses a frames folder with a missing, empty or undecodable frame.
Run once from video/v2/film."""
import pathlib

def sub(path, a, b):
    p = pathlib.Path(path); s = p.read_text(encoding='utf-8')
    assert s.count(a) == 1, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

sub('shots.js', """            G.__pending.push(it.s.img.decode().catch(() => { G.__errors && G.__errors.push('[blender] missing ' + it.s.img.src); }));""",
"""            const img = it.s.img, want = img.src;
            G.__pending.push(img.decode().catch(() => {        // the frame isn't there: this frame shows the shot's still
              (G.__fallbacks = G.__fallbacks || []).push(`${it.bl.id} frame ${n}: missing, the still for this frame`);
              console.warn(`[blender] ${it.bl.id} frame ${n} missing: the still ${it.src} for this frame`);
              if (img.src === want) { img.src = path(it.src); it.blN = -1; return img.decode().catch(() => {}); }
            }));""")

sub('render.js', """function encode(f0, f1, name) {
  const silent = path.join(OUT, name || BASE + '-silent.mp4');""",
"""/** Every frame there, non-empty and decodable, before an encode (ffmpeg decodes them all to null). */
function checkFrames(f0, f1) {
  const dirF = path.join(OUT, 'frames'), bad = [];
  for (let f = f0; f < f1; f++) {
    const p = path.join(dirF, String(f).padStart(5, '0') + '.jpg');
    if (!fs.existsSync(p) || fs.statSync(p).size < 1000) bad.push(f);
  }
  if (bad.length) throw new Error(`frames missing or empty: ${bad.length} (first ${bad.slice(0, 8).join(', ')})`);
  const r = spawnSync('ffmpeg', ['-hide_banner', '-v', 'error', '-framerate', String(FPS), '-start_number', String(f0), '-i', path.join(dirF, '%05d.jpg'),
    '-frames:v', String(f1 - f0), '-f', 'null', '-'], { encoding: 'utf8' });
  if (r.status !== 0 || (r.stderr || '').trim()) throw new Error('frames that do not decode:\\n' + (r.stderr || '').slice(0, 2000));
  console.log(`checked ${f1 - f0} frames: all there, non-empty, decodable`);
}
function encode(f0, f1, name) {
  checkFrames(f0, f1);
  const silent = path.join(OUT, name || BASE + '-silent.mp4');""")
# the log of fallbacks after a render
sub('render.js', """  return { b, p, shot, errors: () => p.evaluate(() => window.__errors.slice()) };""",
"""  return { b, p, shot, errors: () => p.evaluate(() => window.__errors.slice()), fallbacks: () => p.evaluate(() => (window.__fallbacks || []).slice()) };""")
sub('render.js', """    errs += (await k.errors()).length; await k.b.close();
  }));""", """    errs += (await k.errors()).length; fb = fb.concat(await k.fallbacks()); await k.b.close();
  }));
  if (fb.length) console.log(`blender frames missing, the still used instead: ${fb.length}\\n  ` + fb.slice(0, 20).join('\\n  '));""")
sub('render.js', """  const out = dir('frames'); const t0 = Date.now(); let done = 0; const W = Math.min(WORKERS, f1 - f0); let errs = 0; const ms = [];""",
"""  const out = dir('frames'); const t0 = Date.now(); let done = 0; const W = Math.min(WORKERS, f1 - f0); let errs = 0, fb = []; const ms = [];""")
print('guards patched')
