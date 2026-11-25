/* Scene X: <name> (<start>–<end> s). Copy to scenes/X.js. Only edit your own scene file.
 * Timing comes from STORYBOARD.md and cues.json. Everything must be a pure function of t:
 *  - create DOM ONCE in build(); in render() only SET properties, and set them every frame
 *    (use show()/typeText()/xf()/setText(), which always write, instead of `if (t > x) el.style...`).
 *  - no Date.now(), Math.random(), CSS transitions/animations, setTimeout, rAF. Use rand(i, salt).
 * See scenes/B.js for a complete example.
 */
(function () {
  const START = 0, END = 10;                // <- from the storyboard
  const VO = { line: 3.0 };                 // <- cues.json -> voice
  const SAY = 'A line Barnaby says.', SAY_DUR = 2.5;   // <- audio/voice/manifest.json
  let shop, hd, row;                        // DOM refs created in build()

  Scene({
    id: 'X', start: START, end: END, drift: .02,
    captions: [[START + 6, END - .2, 'Caption text, at least 3 words per second of hold.']],

    build(root) {
      shop = shop2009({ parent: root, x: 80, y: 150, w: 1100, page: 'Jobs' });
      hd = hud({ parent: root, x: 1000, y: 120, w: 840 });
      row = traceRow(hd.trace, { kind: 'read', name: 'jobs_due', args: '{day: tomorrow}', tag: 'read' });
    },

    render(t) {
      show(shop.el, t, START + .3, .6, { dx: -60, dy: 0 });
      show(hd.el, t, START + .5, .6, { dx: 60, dy: 0 });
      hd.setState(t < VO.line ? 'thinking' : 'speaking');
      hd.setYou('Martin', 'Which repairs are due tomorrow?');
      row.render(t, START + 1.0);
      hd.say(SAY, t, VO.line, SAY.length / (SAY_DUR * .92));
      shop.set(3, 0, '4478', .8 * E(t, START + 2, .5));
    },
  });
})();
