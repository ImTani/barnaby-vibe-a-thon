/* 9 · Goodnight. The shop at 18:40 (x_close_night: glasses folded on the keyboard, the PC asleep, Barnaby's bell in the
 * corner of the screen) -> Lisbon at 20:07 (lisbon_03: the monitors dim to a single small glow) -> the two desks side by
 * side (close_two_desks) -> the bell, once -> "Barnaby" / "Every system deserves a butler." -> the new desk fades; on the
 * old one: "Even the old ones." -> "Built on Synapse · 2nd Brain Labs × Geek Room Vibe-a-thon" -> the small print ->
 * black. Titles in Barnaby's own type and brass (ui/skins/app3.css), with his mark ringing once (its working animation). */
(function () {
  const C = CUES.scenes[8], S = C.start, E = C.end, FI = .6;
  let run, dimmer, rightOff, shade, title, mark, tag, old, card, cardParts, seam;
  const REPO = 'github.com/ImTani/barnaby-vibe-a-thon';   // the public repo (confirmed by the coordinator)
  Scene({
    id: '9', start: S, end: E, fadeIn: 0,
    build(root) {
      const LNIGHT = shotDone('s9_lisbon_night');
      const ASLEEP = pick('world/lisbon_03_medium_night_asleep.png', 'world/lisbon_03_asleep_night.png', 'world/lisbon_03_night_asleep.png', '');
      run = seq(root, [
        { src: 'world/x_close_night.png', at: S, cam: hold(940, 570, 1.08) },
        { src: LNIGHT ? 'world/lisbon_03_medium_night.png' : pick('world/lisbon_03_medium_night_on.png', 'world/lisbon_03_medium_night.png'), at: M('lisbon_night'), fi: .9, cam: hold(1010, 525, 1.06),
          build: l => {
            dimmer = el('div', {}, l);       // everything but Barnaby's slot sinks: the two monitors dim to one small glow
            css(dimmer, { left: '0px', top: '0px', width: '1920px', height: '1080px', background: 'radial-gradient(circle at 1148px 480px, rgba(0,0,0,0) 0px, rgba(0,0,0,0) 60px, rgba(0,0,0,.72) 260px)' });
          },
          over: t => { dimmer.style.opacity = ASLEEP || LNIGHT ? '0' : easeInOutSine(P(t, M('dim'), 1.6)).toFixed(3); } },
      ].concat(ASLEEP && !LNIGHT ? [{ src: ASLEEP, at: M('dim'), fi: 1.6, cam: hold(1010, 525, 1.06) }] : []).concat([
        // the last move: the two desks, closing gently as the bell rings and the titles come up
        { src: pick('world/s9_two_desks.png', 'world/close_two_desks.png'), at: M('two_desks'), fi: .9, cam: [[M('two_desks'), 960, 540, 1.0], [E, 960, 560, 1.04]],
          build: l => { seam = el('div', {}, l);       // the join between the two desks: a thin, feathered dark gutter
            css(seam, { left: '924px', top: '0px', width: '72px', height: '1080px', background: 'linear-gradient(90deg, rgba(8,7,6,0) 0px, rgba(8,7,6,.88) 30px, rgba(8,7,6,.88) 42px, rgba(8,7,6,0) 72px)' }); } },
      ]), E, { dissolves: true, scene: 9 });
      rightOff = el('div', { cls: 'ov' }, root);     // the new desk fades (right half, soft edge)
      css(rightOff, { background: 'linear-gradient(90deg, rgba(0,0,0,0) 940px, rgba(6,5,4,1) 1010px)', display: 'none' });
      // the titles over the two desks (TITLES.md): a scrim, the lockup, the line, its coda; one centred column
      shade = el('div', { cls: 'ov' }, root);
      css(shade, { background: 'linear-gradient(180deg, rgba(10,9,8,.86) 0px, rgba(10,9,8,.74) 440px, rgba(10,9,8,0) 720px)', display: 'none' });
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
        <div class="cred"><span><b>Built on Synapse</b></span><span class="ev">2nd Brain Labs × Geek Room Vibe-a-thon</span></div>
        ${REPO ? `<div class="repo">${REPO}</div>` : ''}
        <div class="fine">Recreated from a real recorded run. Quorum and ComfyUI scenes are staged; endpoint counts come from real Synapse scans. Synthetic voices; Barnaby’s voice: ElevenLabs. Spokes &amp; Sprockets is a fictional shop.</div>`;
      const cm = card.querySelector('.m'); cm.innerHTML = markSVG('#D3A14A'); markAnim(cm, 0, -100);   // at rest: no ring arcs
      // the build, in reading order: the mark and the name, the line, the four steps, the credit, the small print
      const head = card.querySelector('.head');
      cardParts = [[head.querySelector('.m'), 0], [head.querySelector('.w'), 0], [head.querySelector('.what'), .4]]
        .concat([...card.querySelectorAll('.grow > div')].map((e, i) => [e, .85 + .12 * i]))
        .concat([[card.querySelector('.grow'), -1], [card.querySelector('.cred'), 1.55]])
        .concat(card.querySelector('.repo') ? [[card.querySelector('.repo'), 1.65]] : []).concat([[card.querySelector('.fine'), 1.8]]);
      css(card, { display: 'none' });
    },
    render(t) {
      run.render(t);
      const nd = M('new_desk_fades'), EC = CUES.marks.end_card != null ? M('end_card') : M('credit') - .2, out = EC - .7;
      rightOff.style.display = t > nd ? 'block' : 'none';
      rightOff.style.opacity = (.66 * easeInOutSine(P(t, nd, 1.6))).toFixed(3);      // the new desk recedes, not gone
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
      card.style.display = ck > .001 ? 'flex' : 'none';
      card.style.opacity = ck.toFixed(4);
      for (const [e, d] of cardParts) {
        if (d < 0) { e.style.borderTopColor = `rgba(59,57,52,${easeOutCubic(P(t, EC + .85, .6)).toFixed(3)})`; continue; }   // its rule draws with the steps
        const k = easeOutCubic(P(t, EC + d, .75)); e.style.opacity = k.toFixed(4); e.style.transform = `translateY(${((1 - k) * 10).toFixed(2)}px)`;
      }
      Q.setBlack(easeInOutSine(P(t, M('fade_out'), M('end') - M('fade_out'))));
    },
  });
})();
