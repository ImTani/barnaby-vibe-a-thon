/* Scene G: Priya, day one (120–131 s).
 * Priya, the new hire, asks what the system can actually do. A large map of all 24 endpoints blooms: the eight Barnaby
 * has (the six read-only starters, the purchase order he unlocked, the assign he used) glow brass, and the one he
 * wrote himself glows violet. Barnaby: "Twenty-four things. Theo wrote twenty-three; I wrote one more."
 */
(function () {
  const START = 120, END = 131;
  const VO = { priya: 120.6, barnaby: 123.2 };                                // cues.json -> voice
  const ASK = 'What can this system actually do?', ASK_DUR = 2.22;             // audio/voice/manifest.json
  const SAY = 'Twenty-four things. Theo wrote twenty-three; I wrote one more.', SAY_DUR = 5.03;
  const ASK_CPS = ASK.length / (ASK_DUR * .92), SAY_CPS = SAY.length / (SAY_DUR * .92);
  const T_THEO = VO.barnaby + SAY.indexOf('Theo') / SAY_CPS;                  // "...Theo wrote twenty-three"
  const T_MINE = VO.barnaby + SAY.indexOf('I wrote') / SAY_CPS;               // "...I wrote one more"
  const NEW = 'GET /api/reports/workload/{day}';                              // endpoint 24, built in scene F
  const BLOOM = 122.0, GAP = .06;                                             // shimmer sfx 122.0 (1.5 s)
  let chap, priya, barn, card, map, num, legend = [], exposed, fresh;

  Scene({
    id: 'G', start: START, end: END, drift: .02,
    captions: [[128.4, 130.8, "The departing expert's knowledge, kept."]],

    build(root) {
      el('style', { text: `
#scene-G .ghead{display:flex;align-items:center;gap:14px}
#scene-G .ghead .nm{font-size:32px;color:${COL.ink}}
#scene-G .ghead .tg{font-size:20px;color:${COL.muted}}
#scene-G .ghead .ct{margin-left:auto;display:flex;align-items:baseline;gap:12px}
#scene-G .ghead .ct b{font:400 50px/1 "Palatino Linotype",Palatino,Georgia,serif;color:${COL.brass};min-width:60px;text-align:right}
#scene-G .ghead .ct span{font-size:15px;letter-spacing:.14em;text-transform:uppercase;color:${COL.sub}}
#scene-G .gmap{text-align:center}
#scene-G .gmap .ep{font-size:21px;padding:8px 15px;margin:0 6px 12px;border-radius:10px}
#scene-G .gmap .brk{display:block;height:4px}
#scene-G .gleg{display:flex;justify-content:center;gap:48px;font-size:18px;color:${COL.sub};margin-top:4px}
#scene-G .gleg span{display:inline-block}
#scene-G .gleg i{display:inline-block;width:16px;height:16px;border-radius:5px;margin-right:10px;vertical-align:-2px;border:1px solid}
#scene-G .gleg b{color:${COL.ink};font-weight:600;margin-left:10px}
` }, root);

      exposed = new Set([...DATA.starter, 'POST /api/purchase-orders', 'POST /api/jobs/{job_id}/assign']);
      fresh = new Set([NEW]);

      chap = chip('Priya · day one', COL.brass, root, 'position:absolute;left:160px;top:40px;font-size:18px;letter-spacing:.06em');
      priya = line(root, { x: 160, y: 84, w: 1600, who: 'Priya', text: ASK, size: 44 });

      card = el('div', { cls: 'card', style: 'left:160px;top:196px;width:1600px;padding:22px 30px 20px' }, root);
      el('div', { cls: 'ghead', html: `${BELL(30)}<span class="serif nm">Spokes &amp; Sprockets</span>` +
        `<span class="tg">· Theo’s back office, 2009</span><span class="ct"><b>0</b><span>endpoints</span></span>` }, card);
      num = card.querySelector('.ct b');
      el('div', { style: `height:1px;background:${COL.hair};margin:14px 0 18px` }, card);

      // the endpoint map, large and centred; it flows in the card (not absolutely positioned)
      map = endpointMap({ parent: card, x: 0, y: 0, w: 1540 });
      map.el.style.position = 'relative';
      map.el.classList.add('gmap');
      // Barnaby's own endpoint sits on a row of its own, under Theo's twenty-three
      const mine = map.add(NEW);
      map.el.insertBefore(el('div', { cls: 'brk' }), mine.el);

      const total = map.chips.length, nExp = map.chips.filter(c => exposed.has(c.key)).length;
      const leg = el('div', { cls: 'gleg' }, card);
      legend = [
        el('span', { html: `<i style="background:${rgba(COL.brass, .18)};border-color:${COL.brassDeep}"></i>Exposed to Barnaby<b>${nExp}</b>` }, leg),
        el('span', { html: `<i style="background:${rgba(COL.build, .25)};border-color:${COL.build}"></i>Written by Barnaby<b>${fresh.size}</b>` }, leg),
        el('span', { html: `<i style="background:${COL.bg};border-color:#5A606C"></i>Found, not yet needed<b>${total - nExp - fresh.size}</b>` }, leg),
      ];

      barn = line(root, { x: 160, y: 790, w: 1600, who: 'Barnaby', text: SAY, size: 40 });
    },

    render(t) {
      // chapter chip, like scene C's "Monday · 8:52am"
      show(chap, t, 120.3, .5, { dy: -10, out: 123.4, outD: .5 });

      // Priya's question; once Barnaby answers, it steps back a little
      priya.render(t, VO.priya, ASK_CPS);
      priya.el.style.opacity = +priya.el.style.opacity * (1 - .4 * E(t, VO.barnaby, .8, easeInOutCubic));

      // the map: card arrives just before the chips bloom with the shimmer
      show(card, t, 121.6, .6, { dy: 30 });
      map.render(t, BLOOM, exposed, fresh, GAP);
      const n = t < BLOOM ? 0 : Math.min(map.chips.length, Math.floor((t - BLOOM) / GAP) + 1);
      setText(num, String(n));
      const k24 = pulse(t, VO.barnaby + .35, .45);                               // "Twenty-four things."
      num.style.textShadow = k24 > .01 ? `0 0 ${26 * k24}px ${rgba(COL.brass, .8 * k24)}` : 'none';

      map.chips.forEach((c, i) => {
        const isNew = fresh.has(c.key), lit = exposed.has(c.key);
        const flash = pulse(t, BLOOM + i * GAP + .2, .25);                       // a soft glint as each chip lands
        const theo = isNew ? 0 : pulse(t, T_THEO + .2 + i * .03, .32);           // a wave over Theo's 23
        const mine = isNew ? pulse(t, T_MINE + .35, .5) : 0;                     // Barnaby's one
        if (isNew) {
          c.el.style.boxShadow = `0 0 0 ${4 + 4 * mine}px ${rgba(COL.build, .22 + .2 * mine)}, 0 0 ${22 + 34 * mine}px ${rgba(COL.build, .3 + .4 * mine)}`;
          c.el.style.transform += ` scale(${1 + .07 * mine})`;
        } else if (lit) {
          c.el.style.boxShadow = `0 0 ${14 + 16 * theo + 12 * flash}px ${rgba(COL.brass, .2 + .3 * theo + .35 * flash)}`;
        } else {
          c.el.style.boxShadow = theo > .02 ? `0 0 ${14 * theo}px ${rgba(COL.sub, .22 * theo)}` : 'none';
        }
        c.el.style.filter = theo > .01 ? `brightness(${1 + .4 * theo})` : 'none';
      });

      staggerIn(legend, t, 123.5, .1, { d: .5, dy: 10 });

      // Barnaby's answer, typed at the speaking rate
      barn.render(t, VO.barnaby, SAY_CPS);
    },
  });
})();
