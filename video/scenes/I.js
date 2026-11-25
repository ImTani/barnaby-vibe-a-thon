/* Scene I: Close (146–160 s).
 * The bell rings (146.5), and Barnaby's mark and wordmark settle in the centre. He says the title, word by word with
 * his voice, then "Even the old ones." in brass. Credits line, a small honesty note bottom-left, fade to black.
 */
(function () {
  const START = 146, END = 160;
  const T1 = 'Every system deserves a butler.', T1_AT = 148.5, T1_DUR = 2.67;  // cues.json + manifest.json
  const T2 = 'Even the old ones.', T2_AT = 151.6, T2_DUR = 1.73;
  const RING = 146.5, MARK_AT = 147.0, GLIDE = 148.0, BUILT_AT = 154.0, DISC = [155.0, 159.5], BLACK = 158.5;
  let halo, markWrap, mark, bellEl, words1, words2, rule, built, disc;

  // spans for each word, each revealed when the voice reaches it (by character position)
  function words(parent, text) {
    let idx = 0;
    return text.split(' ').map(w => {
      const o = { el: el('span', { text: w, style: 'display:inline-block;margin:0 .13em' }, parent), k: idx / text.length };
      idx += w.length + 1; return o;
    });
  }

  Scene({
    id: 'I', start: START, end: END, drift: .02,

    build(root) {
      // a warm light behind the mark, rising with the bell
      halo = el('div', { cls: 'abs', style: 'left:360px;top:0;width:1200px;height:560px;border-radius:50%;' +
        'background:radial-gradient(closest-side,rgba(212,168,90,.20),rgba(212,168,90,.07) 50%,rgba(212,168,90,0))' }, root);

      markWrap = el('div', { cls: 'abs', style: 'left:0;right:0;top:284px;height:170px' }, root);
      mark = el('div', { style: 'display:flex;justify-content:center;align-items:center;gap:30px;height:170px' }, markWrap);
      bellEl = el('div', { html: BELL(128), style: 'line-height:0;transform-origin:50% 20%;margin-top:30px' }, mark);
      el('div', { cls: 'serif', text: 'Barnaby', style: `font-size:150px;line-height:1;color:${COL.ink};letter-spacing:.005em;` +
        `text-shadow:0 0 60px ${rgba(COL.brass, .18)}` }, mark);

      const t1 = el('div', { cls: 'abs serif', style: `left:0;right:0;top:506px;text-align:center;font-size:64px;line-height:1.2;color:${COL.ink}` }, root);
      words1 = words(t1, T1);
      const t2 = el('div', { cls: 'abs serif', style: `left:0;right:0;top:604px;text-align:center;font-size:48px;line-height:1.2;font-style:italic;color:${COL.brass}` }, root);
      words2 = words(t2, T2);

      rule = el('div', { cls: 'abs', style: `left:900px;top:724px;width:120px;height:1px;background:${rgba(COL.brass, .55)}` }, root);
      built = el('div', { cls: 'abs', style: `left:0;right:0;top:752px;text-align:center;font-size:22px;letter-spacing:.06em;color:${COL.sub}`,
        html: `Built on <span style="color:${COL.ink}">Synapse</span> <span style="color:${COL.muted}">&nbsp;·&nbsp;</span> 2nd Brain Labs × Geek Room Vibe-a-thon` }, root);
      disc = el('div', { cls: 'abs', style: `left:64px;top:1020px;font-size:16px;color:${COL.muted}`,
        text: 'Scenes recreated from a real recorded run. See the README for what’s real.' }, root);
    },

    render(t) {
      // the mark: fades in centred at 147.0, then glides up to make room for the title
      const lift = lerp(150, 0, E(t, GLIDE, 1.1, easeInOutCubic));
      xf(markWrap, { y: lift });
      show(mark, t, MARK_AT, 1.0, { dy: 0, scale: .96, ease: easeOutCubic, blur: 8 });
      // the bell swings gently, as if just rung, and settles
      const st = t - (MARK_AT - .3);
      bellEl.style.transform = `rotate(${st > 0 ? 6 * Math.exp(-1.6 * st) * Math.sin(2 * Math.PI * 1.1 * st) : 0}deg)`;
      halo.style.top = (284 + 85 - 280 + lift) + 'px';
      halo.style.opacity = clamp(.85 * E(t, RING, 1.8, easeOutCubic) + .35 * pulse(t, RING + .25, .45));

      // his words, as titles, revealed with the voice
      for (const w of words1) show(w.el, t, T1_AT + w.k * T1_DUR * .92, .6, { dy: 16, blur: 6 });
      for (const w of words2) show(w.el, t, T2_AT + w.k * T2_DUR * .92, .6, { dy: 14, blur: 6 });

      // credits
      const kr = E(t, BUILT_AT - .2, .9, easeOutCubic);
      rule.style.opacity = kr; rule.style.transform = `scaleX(${kr})`;
      show(built, t, BUILT_AT, .8, { dy: 10 });
      disc.style.opacity = .9 * win(t, DISC[0], DISC[1], .6, .6);

      Q.setBlack(easeInOutSine(P(t, BLACK, END - BLACK)));
    },
  });
})();
