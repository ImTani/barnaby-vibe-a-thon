"""The checks after app3 became the default (no ?skin = app3; ?skin=classic = the old look; ?skin=app = round 2)."""
import io


def patch(p, pairs):
    s = io.open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) >= 1, (p, old[:80], s.count(old))
        s = s.replace(old, new)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('patched', p)


# the original harness: "default" (no ?skin) is now the approved household look; "classic" is the old developer look
patch('video/v2/look/app/check.js', [
    ("""   connected for real.   node video/v2/look/app/check.js [--skins default,signpost,ticket] */""",
     """   connected for real.   node video/v2/look/app/check.js [--skins default,classic,signpost,ticket]
   "default" is the display with no ?skin, which since round 3 is the approved app look (app3); "classic" is the old
   developer look (?skin=classic), the only one without the household view's plain words. */"""),
    ("""const skins = arg('skins', 'default,signpost,ticket').split(',');""",
     """const skins = arg('skins', 'default,classic,signpost,ticket').split(',');
const HOUSEHOLD = skin => skin !== 'classic';           // every look but the old one speaks in plain words"""),
    ("""    if (skin !== 'default') ok(skin, 'card leads with the plain title'""", """    if (HOUSEHOLD(skin)) ok(skin, 'card leads with the plain title'"""),
    ("""    if (skin !== 'default') ok(skin, 'the yes is kept in the conversation'""", """    if (HOUSEHOLD(skin)) ok(skin, 'the yes is kept in the conversation'"""),
    ("""    if (skin !== 'default') {""", """    if (HOUSEHOLD(skin)) {"""),
    ("""    if (skin !== 'default') ok(skin, 'not now is kept'""", """    if (HOUSEHOLD(skin)) ok(skin, 'not now is kept'"""),
    ("""    if (skin !== 'default') ok(skin, 'nothing half-covered by the drawer'""", """    if (HOUSEHOLD(skin)) ok(skin, 'nothing half-covered by the drawer'"""),
    ("""ok(skin, 'drawer lists what the system can do', skin === 'default' ? /GET \\/api/.test(mapText)""",
     """ok(skin, 'drawer lists what the system can do', !HOUSEHOLD(skin) ? /GET \\/api/.test(mapText)"""),
])

# round 2's checks: "/" is now app3; the old look is at ?skin=classic
patch('video/v2/look/app2/check.js', [
    ("""  for (const q of ['', '?skin=classic']) {
    const o = await page();
    await o.goto(`${BASE}/${q}${q ? '&' : '?'}static=1`, { waitUntil: 'networkidle0' });
    ok(`old look unchanged at "/${q}"`, await o.evaluate(() => [...document.styleSheets].some(s => /\\/ui\\/style\\.css/.test(s.href || '')) && !document.documentElement.dataset.skin));
    await o.close();
  }""",
     """  for (const [q, want] of [['?skin=classic', /\\/ui\\/style\\.css/], ['', /\\/ui\\/skins\\/app3\\.css/]]) {   // "/" is app3 since round 3
    const o = await page();
    await o.goto(`${BASE}/${q}${q ? '&' : '?'}static=1`, { waitUntil: 'networkidle0' });
    ok(q ? `old look still at "/${q}"` : 'the default ("/") is the approved round-3 look', await o.evaluate(w => [...document.styleSheets].some(s => new RegExp(w).test(s.href || '')), want.source));
    await o.close();
  }"""),
])

# round 3's checks: "/" is app3 itself; the old look and round 2 stay reachable
patch('video/v2/look/app3/check.js', [
    ("""  for (const q of ['', '?skin=classic', '?skin=app']) {
    const o = await page();
    await o.goto(`${BASE}/${q}${q ? '&' : '?'}static=1`, { waitUntil: 'networkidle0' });
    const css = await o.evaluate(() => [...document.styleSheets].map(s => s.href || '').find(h => /\\/ui\\/(style|skins\\/app)\\.css/.test(h)) || '');
    ok(`other looks untouched at "/${q}"`, q === '?skin=app' ? /skins\\/app\\.css/.test(css) : /\\/ui\\/style\\.css/.test(css), css.split('/ui/')[1]);
    await o.close();
  }""",
     """  for (const [q, want, what] of [['', /skins\\/app3\\.css$/, 'the default ("/") is this look'], ['?skin=classic', /\\/ui\\/style\\.css$/, 'the old look at ?skin=classic'], ['?skin=app', /skins\\/app\\.css$/, 'round 2 at ?skin=app']]) {
    const o = await page();
    await o.goto(`${BASE}/${q}${q ? '&' : '?'}static=1`, { waitUntil: 'networkidle0' });
    const css = await o.evaluate(() => [...document.styleSheets].map(s => s.href || '').find(h => /\\/ui\\/(style|skins\\/app3?)\\.css/.test(h)) || '');
    ok(what, want.test(css), css.split('/ui/')[1]);
    await o.close();
  }"""),
])
