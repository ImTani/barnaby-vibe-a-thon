"""Titles and end card, round 2 (the coordinator's review): the seam between the desks softened into a feathered
gutter, the Lisbon half kept faintly alive, the titles' scrim and a soft shadow for the coda; the end card on one
spacing scale (48 / 32 / 24, 12 inside a step) in one flowing column on the grid, the descriptions and the small
print raised in contrast, and a calm build: mark and name, the line, the four steps 120 ms apart, the credit, the
small print. Run once from video/v2/film."""
import pathlib

def sub(path, a, b):
    p = pathlib.Path(path); s = p.read_text(encoding='utf-8')
    assert s.count(a) == 1, (path, a[:70], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

# ---- index.html: the card as one column on the grid, one spacing scale
h = pathlib.Path('index.html'); s = h.read_text(encoding='utf-8')
i = s.index('.t-card{'); j = s.index('#fontwarm{')
s = s[:i] + """.t-card{background:#1F1E1C;color:#EEEAE1;font-family:"Segoe UI Variable Text","Segoe UI",system-ui,sans-serif;
  display:flex;flex-direction:column;justify-content:center;padding:0 192px}
.t-card .head{display:flex;flex-direction:column;align-items:center}
.t-card .head .m{display:block;width:88px;height:88px}
.t-card .head .w{font:600 88px/1 "Sitka Subheading","Sitka Text",Constantia,Georgia,serif;letter-spacing:-.012em;margin-top:24px}
.t-card .head .what{font:400 34px/1.3 "Sitka Text",Constantia,Georgia,serif;color:#C2BBAE;margin-top:24px;text-wrap:balance;text-align:center}
.t-card .grow{display:grid;grid-template-columns:repeat(4,1fr);column-gap:48px;border-top:1px solid #3B3934;margin-top:48px;padding-top:32px}
.t-card .grow b{display:block;font:600 34px/1.1 "Sitka Subheading","Sitka Text",Constantia,Georgia,serif;color:#EEEAE1}
.t-card .grow span{display:block;font:400 21px/1.45 "Segoe UI Variable Text","Segoe UI",sans-serif;color:#B1AA9C;margin-top:12px;max-width:310px;text-wrap:pretty}
.t-card .cred{display:flex;gap:28px;align-items:baseline;border-top:1px solid #3B3934;margin-top:48px;padding-top:32px;font:400 21px/1.3 "Segoe UI Variable Text","Segoe UI",sans-serif;color:#C2BBAE}
.t-card .cred b{font-weight:600;color:#EEEAE1}
.t-card .cred .repo{margin-left:auto;font:400 19px "Cascadia Mono","Cascadia Code",Consolas,monospace;color:#C2BBAE}
.t-card .fine{margin-top:24px;font:400 16px/1.45 "Segoe UI Variable Text","Segoe UI",sans-serif;color:#A39C8F}
""" + s[j:]
s = s.replace('.t-titles .line{font:400 46px/1.25 "Sitka Text",Constantia,Georgia,serif;color:rgba(238,234,225,.92);letter-spacing:.003em;margin-top:44px}',
              '.t-titles .line{font:400 46px/1.25 "Sitka Text",Constantia,Georgia,serif;color:rgba(238,234,225,.94);letter-spacing:.003em;margin-top:44px;text-shadow:0 1px 14px rgba(8,7,6,.7)}')
s = s.replace('.t-titles .lock{display:flex;', '.t-titles .lock{text-shadow:0 2px 18px rgba(8,7,6,.6);display:flex;')
h.write_text(s, encoding='utf-8')

# ---- s9.js: the composite (Blender's s9_two_desks when it lands), the seam, the scrim, the build
sub('scenes/s9.js', """        { src: 'world/close_two_desks.png', at: M('two_desks'), fi: .9, cam: [[M('two_desks'), 960, 540, 1.0], [E, 960, 560, 1.04]] },""",
"""        { src: pick('world/s9_two_desks.png', 'world/close_two_desks.png'), at: M('two_desks'), fi: .9, cam: [[M('two_desks'), 960, 540, 1.0], [E, 960, 560, 1.04]],
          build: l => { seam = el('div', {}, l);       // the join between the two desks: a thin, feathered dark gutter
            css(seam, { left: '924px', top: '0px', width: '72px', height: '1080px', background: 'linear-gradient(90deg, rgba(8,7,6,0) 0px, rgba(8,7,6,.88) 30px, rgba(8,7,6,.88) 42px, rgba(8,7,6,0) 72px)' }); } },""")
sub('scenes/s9.js', """  let run, dimmer, rightOff, shade, title, mark, tag, old, card, cardParts;""",
"""  let run, dimmer, rightOff, shade, title, mark, tag, old, card, cardParts, seam;""")
sub('scenes/s9.js', """      rightOff.style.opacity = (.94 * easeInOutSine(P(t, nd, 1.4))).toFixed(3);""",
"""      rightOff.style.opacity = (.66 * easeInOutSine(P(t, nd, 1.6))).toFixed(3);      // the new desk recedes, not gone""")
sub('scenes/s9.js', """      css(rightOff, { background: 'linear-gradient(90deg, rgba(0,0,0,0) 900px, #000 1020px)', display: 'none' });""",
"""      css(rightOff, { background: 'linear-gradient(90deg, rgba(0,0,0,0) 940px, rgba(6,5,4,1) 1010px)', display: 'none' });""")
sub('scenes/s9.js', """css(shade, { background: 'linear-gradient(180deg, rgba(12,11,10,.82) 0px, rgba(12,11,10,.64) 400px, rgba(12,11,10,0) 660px)', display: 'none' });""",
"""css(shade, { background: 'linear-gradient(180deg, rgba(10,9,8,.86) 0px, rgba(10,9,8,.74) 440px, rgba(10,9,8,0) 720px)', display: 'none' });""")
sub('scenes/s9.js', """      cardParts = [card.querySelector('.head'), card.querySelector('.grow'), card.querySelector('.cred'), card.querySelector('.fine')];""",
"""      // the build, in reading order: the mark and the name, the line, the four steps, the credit, the small print
      const head = card.querySelector('.head');
      cardParts = [[head.querySelector('.m'), 0], [head.querySelector('.w'), 0], [head.querySelector('.what'), .4]]
        .concat([...card.querySelectorAll('.grow > div')].map((e, i) => [e, .85 + .12 * i]))
        .concat([[card.querySelector('.grow'), -1], [card.querySelector('.cred'), 1.55], [card.querySelector('.fine'), 1.75]]);""")
sub('scenes/s9.js', """      cardParts.forEach((e, i) => { const k = easeOutCubic(P(t, EC + [.0, .35, .6, .8][i], .7)); e.style.opacity = k.toFixed(4); e.style.transform = `translateY(${((1 - k) * 6).toFixed(2)}px)`; });""",
"""      for (const [e, d] of cardParts) {
        if (d < 0) { e.style.borderTopColor = `rgba(59,57,52,${easeOutCubic(P(t, EC + .85, .6)).toFixed(3)})`; continue; }   // its rule draws with the steps
        const k = easeOutCubic(P(t, EC + d, .75)); e.style.opacity = k.toFixed(4); e.style.transform = `translateY(${((1 - k) * 10).toFixed(2)}px)`;
      }""")
print('titles round 2 patched')
