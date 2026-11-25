/* Scene B: Theo's handover (11–30 s). REFERENCE SCENE: read this before writing yours.
 * Theo's 2009 window slides in, his git log types out, he hands over to Barnaby, Synapse scans the repo,
 * 23 endpoint chips bloom in Barnaby's display and the six read-only starters light brass.
 */
(function () {
  const START = 11, END = 30;
  const VO = { theo: 17.3, barnaby: 24.3 };                         // cues.json -> voice
  const SAY = "Twenty-three endpoints, sir. I've started with the six that only read.";
  const SAY_DUR = 5.35;                                               // audio/voice/manifest.json
  let shop, git, theo, hd, tbox, map, gitLines = [];

  Scene({
    id: 'B', start: START, end: END, drift: .02,
    captions: [[12.0, 16.8, "Theo wrote the shop's back office in 2009. On Friday, he leaves."]],

    build(root) {
      shop = shop2009({ parent: root, x: 110, y: 150, w: 1000, page: 'Jobs' });

      // git log, oldest first, without Barnaby's own commit (that comes later in the story)
      git = terminal({ parent: root, x: 1160, y: 150, w: 680, h: 330, title: 'GIT LOG · spokes-and-sprockets' });
      const commits = DATA.gitlog.filter(c => c.author !== 'Barnaby').slice().reverse();
      gitLines = commits.map((c, i) => ({ t: 12.5 + i * .72, text: `${c.date}  ${c.subject}`, cps: 90 }));

      theo = line(root, { x: 110, y: 780, w: 1000, who: 'Theo', text: 'Barnaby, this is the shop’s system. Look after them for me.', size: 36 });

      hd = hud({ parent: root, x: 1080, y: 120, w: 720 });
      // a small in-flow terminal inside the HUD (the component terminal() is absolutely positioned, so roll a tiny one)
      tbox = el('div', { cls: 'mono', style: 'font-size:17px;line-height:1.55;color:#C2BBA9;background:#0B0E13;border:1px solid #262B35;border-radius:12px;padding:10px 14px;margin-bottom:14px;height:76px' }, hd.trace);
      // endpoint chips, smaller than the default so 23 fit in the HUD
      const holder = el('div', { style: 'position:relative;height:300px' }, hd.trace);
      el('style', { text: '#scene-B .bmap .ep{font-size:12.5px;padding:4px 8px;margin:0 6px 6px 0}' }, root);
      map = endpointMap({ parent: holder, x: 0, y: 0, w: 672 });
      map.el.classList.add('bmap');
    },

    render(t) {
      // the 2009 window: slides in from the left and stays
      show(shop.el, t, 11.5, .6, { dx: -80, dy: 0 });

      // git log: types oldest-first, fades out as the HUD arrives
      show(git.el, t, 12.3, .5, { dy: 20, out: 19.7, outD: .4 });
      git.render(t, gitLines);

      // Theo's line, typed at about his speaking rate; it leaves as Barnaby's answer starts
      theo.render(t, VO.theo, 15);
      hideAfter(theo.el, t, 23.8, .5);

      // Barnaby's display
      show(hd.el, t, 20.0, .6, { dx: 60, dy: 0 });
      hd.setState(t < 24.0 ? 'connecting' : t < VO.barnaby ? 'connected' : 'speaking');
      hd.setYou('', '');

      const cmd = '$ synapse build --auto --local';
      const n = Math.floor(clamp((t - 20.5) * 40, 0, cmd.length));
      setHTML(tbox, `<span style="color:${COL.brass}">${esc(cmd.slice(0, n))}</span>` +
        (t >= 21.4 ? `<br><span style="color:${COL.good}">✓ Extracted 23 endpoint(s)</span>` : ''));

      // 23 chips bloom (≈0.085 s apart); at 24.0 the six starters light brass (chime in the soundtrack)
      const lit = t >= 24.0 ? new Set(DATA.starter) : new Set();
      map.render(t, 21.6, lit, new Set(), .085);
      for (const c of map.chips) if (lit.has(c.key)) c.el.style.boxShadow = `0 0 ${18 * pulse(t, 24.0, .35)}px ${rgba(COL.brass, .8)}`;
        else c.el.style.boxShadow = '';

      // his line types out at about the speaking rate, finishing just before the voice does
      hd.say(SAY, t, VO.barnaby, SAY.length / (SAY_DUR * .92));
    },
  });
})();
