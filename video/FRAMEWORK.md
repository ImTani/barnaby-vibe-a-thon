# Barnaby film framework: API for scene authors

Read `STORYBOARD.md` first (it's frozen: timing, style bible, and every scene's beats). `scenes/B.js` is the full
reference scene, and `scenes/_TEMPLATE.js` is the starting point. The film is 160 s, 1920×1080, 30 fps.
All commands run from `video/`.

## Ground rules
1. **Only edit your own `scenes/X.js`.** Keep helpers inside your scene's IIFE. If you need a change to `lib.js`,
   `components.js`, `index.html`, `main.js` or `render.js`, ask for it in your final report instead of making it.
   Scene-scoped CSS is fine: add an `el('style', {text: '#scene-X .foo{...}'}, root)` in `build()`.
2. **Everything is a pure function of `t`.** Don't use `Date.now()`, `Math.random()` (use `rand(i, salt)`), CSS
   transitions or animations, timers, or rAF. Create DOM once in `build()`. In `render()`, set **every animated
   property every frame**. For example, `show(el, t, 3, .6)` always writes, but `if (t > 3) el.style.opacity = 1`
   leaks state when frames render out of order.
3. **Don't move key events.** The soundtrack (voice lines, sound effects and music sections in `cues.json`) is cut
   to the storyboard's times. If you must move something, list the actual times in your report.
4. **Honesty.** The film is a staged recreation of a real recorded run. Numbers, names, the diff and the test count
   come from `window.DATA` (`data.js`) or the storyboard. Don't invent other figures.
5. **Test your scene:**
   - `node render.js sheet <start> <end> 8` writes `stills/sheet_<start>_<end>.jpg`, 8 time-stamped tiles. Look at it.
   - `node render.js test 61 62.5` writes `stills/test_61.jpg` and `stills/test_62.5.jpg` at full size.
   - `node render.js verify 60 65 70` checks determinism (each frame rendered in two different orders must match;
     on a mismatch it saves `stills/verify_<t>_a.png` and `_b.png`). A one-off mismatch on the first frame of a run
     can be font warm-up; re-run before chasing it.
   - Page exceptions are printed, and the exit code is 2 if any occur.

## Layers (bottom to top)
`#bg` brass grid (drifts) → `#glow` → `#vig` vignette → **`#stage`** (one root div per scene, stacked by start time)
→ **`canvas#fx`** (`Q.fx`, a free 2D context above the DOM, cleared every frame) → **caption** → `#black`
(`Q.setBlack(v)`).

## Scene registry
```js
Scene({ id: 'D', start: 47, end: 69,
  fadeIn: .5, fadeOut: .5,   // crossfade seconds, centred on the boundary (both scenes at 50% at t = start)
  drift: .02,                // root zoom 1.00 -> 1.02 across the scene (0 = off). Style bible: .02
  captions: [[66.0, 68.6, 'Unlock: Synapse had already found it. Barnaby asked, then took it.']],
  build(root, scene) {...},  // once, at load. Put DOM inside root (a 1920x1080 div with id "scene-D").
  render(t, lt, fade) {...}  // every frame while visible: t in (start - fadeIn/2, end + fadeOut/2)
});
```
- `lt = t - start`. `fade` is the scene's current crossfade weight (0..1).
- The framework owns `root.style.opacity` and `root.style.transform`, so don't set them. Use an inner wrapper div if
  you need to move everything.
- Anything you draw on `Q.fx` is **not** faded by the root, so multiply your alpha by `fade`.
- An exception in your build or render is caught and logged. It won't break other scenes.
- Captions: use exactly the scene's caption from `cues.json → captions`, in `Scene({captions})`.

## Timing and easing (globals from lib.js)
| fn | meaning |
|---|---|
| `P(t,a,d=.6)` | linear clamped progress 0..1 over [a, a+d] |
| `E(t,a,d=.6,ease=easeOutExpo)` | eased progress |
| `easeOutExpo, easeInExpo, easeInOutExpo, easeOutCubic, easeInCubic, easeInOutCubic, easeInOutSine, easeOutQuart, easeOutBack(x,s), spring(x,damping=6.5,freq=2.1), linear` | easings on x in 0..1 |
| `pulse(t,t0,w=.15)` | gaussian bump (flashes, button presses, glows) |
| `win(t,a,b,fi=.5,fo=.5)` | 0→1 at a, 1→0 by b |
| `blink(t,rate=2)` | 0/1 square blink |
| `keyframes(t, [[t0,v0],[t1,v1],...], ease)` | piecewise tween of numbers, arrays or objects |
| `lerp, invLerp, remap, clamp, lerp3, mixAny` | math |
| `rand(i,salt)`, `randn(i,salt)`, `seeded(seed)` (build only), `wiggle(t,seed,freq,amp)` | deterministic randomness |
| `mixColor(a,b,k)`, `rgba(hex,a)`, `hexToRgb` | colour |

**Palette (`COL`)**: `brass #D4A85A` (Barnaby, accents), `brassDeep`, `brassLt`, `ink #F1ECE1` (text), `sub #C2BBA9`,
`muted #8D8778`, `bg #0E1117`, `card #161A22`, `card2 #1B202A`, `hair #262B35`. Tiers (never use them for anything
else): `read #3987E5`, `write #D95926`, `grow` (= brass), `build #9085E9` (violet), `good #22C55E` (success).
`bad #E66767`, `warn #FAB219`. 2009 colours: `xpBlue, xpBanner, xpYellow, xpGrey, xpBeige`.

## DOM and text helpers
- `el(tag, {cls, style, html, text, attrs}, parent)` and `h(htmlString, parent)` create elements; `css(el, obj)`.
- `setText(el, s)` / `setHTML(el, s)` write only when the value changes (fast). Always use them in render().
- `xf(el, {x, y, s, sx, sy, r, rx, ry, persp, o, blur})` sets transform and opacity in one call.
- `show(el, t, a, d=.6, {dy=24, dx=0, scale=1, ease=easeOutExpo, blur=0, out, outD=.4, outDy})`: the standard
  entrance (and optional exit starting at `out`). Returns the visible amount.
- `pop(el, t, a, d=.7, from=.6)`: spring scale pop (only for button presses and the moment a new tool appears).
- `hideAfter(el, t, a, d=.4)`: multiplies the current opacity by an exit fade. Call it after `show`.
- `typeText(el, str, t, start, cps=28, {cursor=true, cursorColor, hold=1.2})`: types with a blinking cursor.
- `staggerIn(els, t, start, gap=.08, showOpts)`: staggered entrances (style bible: 60–120 ms).
- `countUp(t, a, d, from, to)`, `chip(html, color, parent, style)`.
- CSS classes: `.abs`, `.card`, `.mono`, `.serif`, `.hero`, `.brass .good .bad .sub .muted`, `.chip`, `.btn`, `.btn.ghost`.
- Canvas: `drawGlow(ctx, x, y, r, color, alpha)`, `glowLine(ctx, x1, y1, x2, y2, color, alpha, width)`, `roundRect`.

## Components (components.js)
All are look-alikes of the real app (`ui/`) and the real 2009 shop (`systems/spokes-and-sprockets`).
```js
// The 2009 back office window (IE7, Verdana, bevels). page: which nav tab is "on" ('Jobs', 'Purchase Orders', ...).
const shop = shop2009({ parent: root, x: 110, y: 150, w: 1000, page: 'Jobs', rows: SHOP_ROWS });
shop.el; shop.cells[r][c];                    // rows: [job, mechanic, work, customer, hrs, due]
shop.set(r, c, text, hl);                     // set a cell; hl 0..1 = soft yellow highlight. Call EVERY frame.
// Need another page (e.g. Purchase Orders)? Build a second shop2009 with page + rows and crossfade, or
// replace the .xp-body innerHTML once in build() on a second instance.

// Barnaby's display panel. Children flow vertically: head, you, trace, say, cards.
const hd = hud({ parent: root, x: 1080, y: 120, w: 720 });
hd.setState('listening' | 'thinking' | 'speaking' | ...);   // call every frame
hd.setYou('Martin', 'Which repairs…');        // the person's request line ('' to clear). Call every frame.
hd.say(text, t, start, cps);                  // Barnaby's line typed from `start`; returns progress
hd.trace, hd.cards                            // containers for trace rows / cards (in normal flow)

// A live-trace row (tier colour on the left edge). kind: read | write | grow | build | synapse | ok
const r = traceRow(hd.trace, { kind: 'read', name: 'jobs_due', args: '{day: tomorrow}', tag: 'read' });
r.render(t, at);                              // slides in at `at`

// An approval card. kind: write | grow | build. diff: unified diff text (optional), diffLines: lines shown.
const card = approvalCard({ parent: root, x, y, w: 760, kind: 'grow', title: 'Unlock POST /api/purchase-orders',
                            detail: 'Order more of a part from a supplier.', primary: 'Unlock' });
show(card.el, t, 58.9, .5); card.press(t, 60.6);   // press: a pulse on the primary button at time `at`

diffView(parentEl, diffText, maxLines);       // just the diff box
const term = terminal({ parent: root, x, y, w: 800, h: 300, title: 'TERMINAL' });
term.render(t, [{ t: 61.0, text: '$ synapse build …', cls: 'p' }, { t: 61.4, text: 'rebuilt in 0.38 s', cls: 'ok' }], 60);
//   cls 'p' = brass prompt, 'ok' = green. terminal() is position:absolute; for one inside the HUD, roll a small
//   in-flow div like scenes/B.js does.

const map = endpointMap({ parent: holder, x: 0, y: 0, w: 672 });   // chips for DATA.endpoints (23)
map.render(t, bloomAt, litSet, freshSet, gap);  // lit = brass (exposed), fresh = violet (new). Call every frame.
const c = map.add('GET /api/reports/workload/{day}');            // in build(): add the 24th chip, then control it in render

const ln = line(root, { x, y, w: 1200, who: 'Martin' | 'Theo' | 'Priya' | 'Barnaby', text, size: 34 });
ln.render(t, at, cps);                        // speaker label + typed line (Barnaby's in serif italic)

BELL(size)                                    // the brass bell SVG string (Barnaby's mark)
```

## Data (`window.DATA`, from a real recorded run)
- `DATA.endpoints`: the 23 discovered endpoints `{key, tool, read_only, description}` (key like `"GET /api/jobs/open"`).
- `DATA.starter`: the 6 read-only endpoint keys exposed on arrival.
- `DATA.turns[i]`: `{ask, calls: [{system, tool, input}], said}` for Ask, Unlock, Build, Act.
- `DATA.build`: `{diff, tested, endpoints, tools}`: the real diff Barnaby wrote, the test result and new endpoint.
- `DATA.gitlog`: newest first, `{date, author, subject}` (the first is Barnaby's own commit).

## Speech on screen
Spoken lines appear as text too, timed to the voice line: start at the `cues.json → voice` time, and type at
`text.length / (dur * .92)` characters per second, where `dur` comes from `audio/voice/manifest.json`, so the text
finishes just before the voice does. Barnaby's lines go in `hd.say` (or a Barnaby `line()`), and human lines in
`hd.setYou` or `line()`.

## Globals
`Q.t`, `Q.fx` (front 2D ctx), `Q.setBlack(v)` (fade to black, the max over all scenes), `Q.scene`, `W=1920`,
`H=1080`, `FPS=30`, `DURATION=160`. `window.__errors` collects exceptions.

## render.js
```
node render.js                        # full 0-160 s -> frames/ -> out/barnaby-silent.mp4 (+ out/barnaby.mp4 if audio/soundtrack.wav)
node render.js range 47 69            # frames for 47-69 s -> out/range_47_69.mp4   (--no-encode to skip)
node render.js test 61 62.5           # stills/test_<t>.jpg
node render.js sheet 47 69 8          # stills/sheet_47_69.jpg (8 time-stamped tiles)
node render.js verify 50 60 65        # determinism check
node render.js encode                 # re-encode existing frames
flags: --workers=8 --fps=30 --quality=92
```
