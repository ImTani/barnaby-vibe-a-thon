"""v2.3 titles and the product end card (SHOTLIST v2.3 revisions 7; video/v2/film/TITLES.md). Run from video/v2/film."""
import pathlib
p = pathlib.Path('scenes/s9.js'); s = p.read_text(encoding='utf-8')
i = s.index("      rightOff = el('div', { cls: 'ov' }, root);")
j = s.index("  });\n})();")
NEW = r"""      rightOff = el('div', { cls: 'ov' }, root);     // the new desk fades (right half, soft edge)
      css(rightOff, { background: 'linear-gradient(90deg, rgba(0,0,0,0) 900px, #000 1020px)', display: 'none' });
      // the titles over the two desks (TITLES.md): a scrim, the lockup, the line, its coda; one centred column
      shade = el('div', { cls: 'ov' }, root);
      css(shade, { background: 'linear-gradient(180deg, rgba(12,11,10,.80) 0px, rgba(12,11,10,.58) 360px, rgba(12,11,10,0) 600px)', display: 'none' });
      const T = el('div', { cls: 'ov t-titles' }, root);
      T.innerHTML = `
        <div class="lock"><span class="m"></span><span class="w">Barnaby</span></div>
        <div class="line">Every system deserves a butler.</div>
        <div class="line coda">Even the old ones.</div>`;
      css(T, { display: 'none' });
      title = T.querySelector('.lock'); tag = T.querySelectorAll('.line')[0]; old = T.querySelectorAll('.line')[1];
      mark = T.querySelector('.m'); mark.innerHTML = markSVG('#D3A14A');
      // the product end card: warm charcoal, a 12-column grid (192 px margins), brass only in the mark
      card = el('div', { cls: 'ov t-card' }, root);
      card.innerHTML = `
        <div class="head"><span class="m"></span><div class="w">Barnaby</div>
          <div class="what">A voice-first butler for the software your business already runs.</div></div>
        <div class="grow">
          <div><b>Ask</b><span>Answers from what your system can already do.</span></div>
          <div><b>Unlock</b><span>Asks you for a key to what it could do.</span></div>
          <div><b>Compose</b><span>Turns steps he keeps repeating into one.</span></div>
          <div><b>Build</b><span>Writes what’s missing, and adds it when you say so.</span></div>
        </div>
        <div class="cred"><span><b>Built on Synapse</b></span><span class="ev">2nd Brain Labs × Geek Room Vibe-a-thon</span>${REPO ? `<span class="repo">${REPO}</span>` : ''}</div>
        <div class="fine">Recreated from a real recorded run. Quorum and ComfyUI scenes are staged; endpoint counts come from real Synapse scans. Synthetic voices; Barnaby’s voice: ElevenLabs. Spokes &amp; Sprockets is a fictional shop.</div>`;
      card.querySelector('.m').innerHTML = markSVG('#D3A14A');
      cardParts = [card.querySelector('.head'), card.querySelector('.grow'), card.querySelector('.cred'), card.querySelector('.fine')];
      css(card, { display: 'none' });
    },
    render(t) {
      run.render(t);
      const nd = M('new_desk_fades'), EC = CUES.marks.end_card != null ? M('end_card') : M('credit') - .2, out = EC - .7;
      rightOff.style.display = t > nd ? 'block' : 'none';
      rightOff.style.opacity = (.94 * easeInOutSine(P(t, nd, 1.4))).toFixed(3);
      // titles: in on the music (the lockup, then its line), the coda as the new desk fades; out together, calmly
      const tOut = 1 - easeInOutSine(P(t, out, .7));
      const rise = (e, a, d) => { const k = easeOutCubic(P(t, a, d)) * tOut; e.style.opacity = k.toFixed(4); e.style.transform = `translateY(${((1 - easeOutCubic(P(t, a, d))) * 8).toFixed(2)}px)`; return k; };
      const on = t > M('title') - .7 && t < out + .75;
      shade.parentNode && (shade.style.display = on ? 'block' : 'none');
      shade.style.opacity = (easeInOutSine(P(t, M('title') - .7, 1.2)) * tOut).toFixed(3);
      title.parentNode.style.display = on ? 'flex' : 'none';
      rise(title, M('title'), 1.1);
      rise(tag, M('title') + 1.0, 1.0);
      rise(old, M('old_ones'), 1.0);
      markAnim(mark, t, M('bell_final') + .55);            // the mark rings once, just after the real bell
      // the end card: a dissolve in over the titles' exit, then its rows settle in turn
      const ck = easeInOutSine(P(t, EC - .1, .8));
      card.style.display = ck > .001 ? 'block' : 'none';
      card.style.opacity = ck.toFixed(4);
      cardParts.forEach((e, i) => { const k = easeOutCubic(P(t, EC + [.0, .35, .6, .8][i], .7)); e.style.opacity = k.toFixed(4); e.style.transform = `translateY(${((1 - k) * 6).toFixed(2)}px)`; });
      Q.setBlack(easeInOutSine(P(t, M('fade_out'), M('end') - M('fade_out'))));
    },
"""
s = s[:i] + NEW + s[j:]
s = s.replace("  let run, dimmer, rightOff, shade, title, mark, tag, old, credit, small;",
              "  let run, dimmer, rightOff, shade, title, mark, tag, old, card, cardParts;\n  const REPO = '';                                   // the public repo, once confirmed (no remote in this checkout)")
p.write_text(s, encoding='utf-8')

# the type: Barnaby's own faces (DESIGN.md): Sitka Subheading for the name, Sitka Text upright for his line, Segoe UI
# for the interface voice, Cascadia Mono only for the repo
q = pathlib.Path('index.html'); h = q.read_text(encoding='utf-8')
CSS = """/* titles and the end card (TITLES.md) */
.t-titles{display:flex;flex-direction:column;align-items:center;padding-top:150px}
.t-titles .lock{display:flex;align-items:center;gap:30px;font:600 112px/1 "Sitka Subheading","Sitka Text",Constantia,Georgia,serif;color:#EEEAE1;letter-spacing:-.012em;margin-right:30px}
.t-titles .lock .m{display:block;width:96px;height:96px;margin-top:-10px}
.t-titles .line{font:400 46px/1.25 "Sitka Text",Constantia,Georgia,serif;color:rgba(238,234,225,.92);letter-spacing:.003em;margin-top:44px}
.t-titles .coda{color:#D3A14A;margin-top:10px}
.t-card{background:#1F1E1C;color:#EEEAE1;font-family:"Segoe UI Variable Text","Segoe UI",system-ui,sans-serif}
.t-card .head{position:absolute;left:192px;right:192px;top:150px;display:flex;flex-direction:column;align-items:center}
.t-card .head .m{display:block;width:92px;height:92px}
.t-card .head .w{font:600 88px/1 "Sitka Subheading","Sitka Text",Constantia,Georgia,serif;letter-spacing:-.012em;margin-top:22px}
.t-card .head .what{font:400 34px/1.3 "Sitka Text",Constantia,Georgia,serif;color:#C2BBAE;margin-top:26px;text-wrap:balance;text-align:center}
.t-card .grow{position:absolute;left:192px;right:192px;top:548px;display:grid;grid-template-columns:repeat(4,1fr);column-gap:48px;border-top:1px solid #36342F;padding-top:40px}
.t-card .grow b{display:block;font:600 34px/1.1 "Sitka Subheading","Sitka Text",Constantia,Georgia,serif;color:#EEEAE1}
.t-card .grow span{display:block;font:400 20px/1.45 "Segoe UI Variable Text","Segoe UI",sans-serif;color:#9A9488;margin-top:14px;max-width:300px;text-wrap:pretty}
.t-card .cred{position:absolute;left:192px;right:192px;top:812px;display:flex;gap:28px;align-items:baseline;border-top:1px solid #36342F;padding-top:34px;font:400 21px/1.3 "Segoe UI Variable Text","Segoe UI",sans-serif;color:#C2BBAE}
.t-card .cred b{font-weight:600;color:#EEEAE1}
.t-card .cred .repo{margin-left:auto;font:400 19px "Cascadia Mono","Cascadia Code",Consolas,monospace;color:#C2BBAE}
.t-card .fine{position:absolute;left:192px;right:192px;top:972px;font:400 16px/1.45 "Segoe UI Variable Text","Segoe UI",sans-serif;color:#8A847A}
"""
h = h.replace("#fontwarm{", CSS + "#fontwarm{", 1)
q.write_text(h, encoding='utf-8')
print('titles patched')
