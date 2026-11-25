/* 9 · Goodnight. The shop at 18:40 (x_close_night: glasses folded on the keyboard, the PC asleep, Barnaby's bell in the
 * corner of the screen) -> Lisbon at 20:07 (lisbon_03: the monitors dim to a single small glow) -> the two desks side by
 * side (close_two_desks) -> the bell, once -> "Barnaby" / "Every system deserves a butler." -> the new desk fades; on the
 * old one: "Even the old ones." -> "Built on Synapse · 2nd Brain Labs × Geek Room Vibe-a-thon" -> the small print ->
 * black. Titles in Barnaby's own type and brass (ui/skins/app3.css), with his mark ringing once (its working animation). */
(function () {
  const C = CUES.scenes[8], S = C.start, E = C.end, FI = .6;
  let run, dimmer, rightOff, shade, title, mark, tag, old, card, cardParts, seam;
  const LOCK_TOP = 396;          // the lockup's top: its cap height sits on the frame's centre line, the hand below it
  const REPO = 'github.com/ImTani/barnaby-vibe-a-thon';   // the public repo (confirmed by the coordinator)
  /** Theo's hand, written on: word by word, left to right, behind a soft-edged mask at a pen's pace (each word's time
   * by its letters, a short lift of the pen between words). h = {e, wd: [{e, n}]}; a = start, d = the whole line,
   * k = the titles' fade (1 = up). Word widths are measured once, laid out in the loaded hand. */
  function write(h, t, a, d, k) {
    h.e.style.opacity = k.toFixed(4);
    const LIFT = .09, F = 30, letters = h.wd.reduce((s, w) => s + w.n, 0), per = (d - LIFT * (h.wd.length - 1)) / letters;
    let at = a;
    for (const w of h.wd) {
      if (!w.px) w.px = w.e.offsetWidth;
      const dur = w.n * per, u = clamp((t - at) / dur), x = u * (w.px + F);
      const m = u >= 1 ? 'none' : `linear-gradient(90deg, #000 ${(x - F).toFixed(1)}px, rgba(0,0,0,0) ${x.toFixed(1)}px)`;
      w.e.style.webkitMaskImage = m; w.e.style.maskImage = m;
      at += dur + LIFT;
    }
  }
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
      // the titles over the two desks (TITLES.md): the wordmark at the centre of the frame, and under it the line and
      // its coda in Theo's hand (Segoe Print, as on his sticky note: make_note.py), written on word by word; a soft
      // oval scrim keeps them legible over the desks. Styles live here (s9-titles), not in index.html.
      if (!document.getElementById('s9-titles')) el('style', { attrs: { id: 's9-titles' }, html: `
        @font-face{font-family:"TheoHand";src:url("file:///C:/Windows/Fonts/segoepr.ttf") format("truetype"),local("Segoe Print");font-weight:400}
        .s9-titles{display:flex;flex-direction:column;align-items:center;padding-top:${LOCK_TOP}px}
        .s9-titles .lock{display:flex;align-items:flex-end;gap:28px;margin-left:-14px;font:600 124px/1 "Sitka Subheading","Sitka Text",Constantia,Georgia,serif;
          color:#EEEAE1;letter-spacing:-.012em;text-shadow:0 2px 22px rgba(8,7,6,.55)}
        .s9-titles .lock .m{display:block;width:100px;height:100px;margin-bottom:16px;filter:drop-shadow(0 0 18px rgba(211,161,74,.22))}
        .s9-titles .hand{font:400 58px/1.2 "TheoHand","Segoe Print",cursive;color:#F1ECE2;white-space:nowrap;margin-top:58px;
          text-shadow:0 1px 16px rgba(8,7,6,.75)}
        .s9-titles .hand.coda{color:#D3A14A;margin-top:4px;font-size:56px;transform:rotate(-1.6deg) translateX(34px)}
        .s9-titles .hand .wd{display:inline-block;padding:.12em .3em .3em;margin:-.12em -.3em -.3em}
        .s9-titles .hand .sp{display:inline-block;width:.32em}
        .t-card .cred .vox{margin-left:auto;color:#A8A194}
        .s9-warm{position:absolute;left:-9999px;top:0;visibility:hidden;font:400 40px "TheoHand"}
      ` }, document.head);
      el('span', { cls: 's9-warm', text: 'Every system deserves a butler. Even the old ones.' }, root);
      try { document.fonts.load('400 58px "TheoHand"'); } catch (e) { }
      shade = el('div', { cls: 'ov' }, root);
      css(shade, { background: 'radial-gradient(ellipse 1080px 470px at 960px 600px, rgba(9,8,7,.8) 0%, rgba(9,8,7,.66) 42%, rgba(9,8,7,.3) 72%, rgba(9,8,7,0) 100%)', display: 'none' });
      const T = el('div', { cls: 'ov s9-titles' }, root);
      const words = s => s.split(' ').map(w => `<span class="wd">${w}</span>`).join('<span class="sp"></span>');
      T.innerHTML = `
        <div class="lock"><span class="m"></span><span class="w">Barnaby</span></div>
        <div class="hand">${words('Every system deserves a butler.')}</div>
        <div class="hand coda">${words('Even the old ones.')}</div>`;
      css(T, { display: 'none' });
      title = T.querySelector('.lock');
      tag = { e: T.querySelectorAll('.hand')[0] }; old = { e: T.querySelectorAll('.hand')[1] };
      for (const h of [tag, old]) h.wd = [...h.e.querySelectorAll('.wd')].map(e => ({ e, n: e.textContent.length }));
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
        <div class="cred"><span><b>Built on Synapse</b></span><span class="ev">2nd Brain Labs × Geek Room Vibe-a-thon</span><span class="vox">Voices: zoonie and sylenthsnares</span></div>
        ${REPO ? `<div class="repo">${REPO}</div>` : ''}
        <div class="fine">Recreated from a real recorded run. Quorum and ComfyUI scenes are staged; endpoint counts come from real Synapse scans. Martin, Theo and Priya voiced by real people; Barnaby’s voice: ElevenLabs. Spokes &amp; Sprockets is a fictional shop.</div>`;
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
      const nd = M('new_desk_fades'), EC = CUES.marks.end_card != null ? M('end_card') : M('credit') - .2, out = EC - .75;
      rightOff.style.display = t > nd ? 'block' : 'none';
      rightOff.style.opacity = (.66 * easeInOutSine(P(t, nd, 1.6))).toFixed(3);      // the new desk recedes, not gone
      // titles: the lockup up on the music, then the line written on in Theo's hand;
      // the coda written as the new desk fades; all out together, calmly, gone before the card's dissolve (no double name)
      const tOut = 1 - easeInOutSine(P(t, out, .7));
      const rise = (e, a, d) => { const k = easeOutCubic(P(t, a, d)) * tOut; e.style.opacity = k.toFixed(4); e.style.transform = `translateY(${((1 - easeOutCubic(P(t, a, d))) * 8).toFixed(2)}px)`; return k; };
      const on = t > M('title') - .7 && t < out + .75;
      // the scrim stays down until the card has covered the desks (no lift in the light between the two)
      const sOn = t > M('title') - .7 && t < EC + .75;
      shade.parentNode && (shade.style.display = sOn ? 'block' : 'none');
      shade.style.opacity = (easeInOutSine(P(t, M('title') - .7, 1.4)) * (1 - easeInOutSine(P(t, EC - .1, .8)))).toFixed(3);
      title.parentNode.style.display = on ? 'flex' : 'none';
      rise(title, M('title'), 1.1);
      if (on) { write(tag, t, M('title') + 1.2, 2.1, tOut); write(old, t, M('old_ones'), 1.2, tOut); }
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
