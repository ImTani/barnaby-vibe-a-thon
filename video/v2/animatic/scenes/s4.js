/* 4 · A key. Mon 23 Nov, 08:55-09:04. From the pads callout the camera pulls back to the whole of Martin's world as
 * the card arrives (worlds2 martin-key, 08:55: "Let Barnaby order parts from your suppliers", the key on the back
 * door). "Go on, then." -> the click (x_mouse_monday) -> on the plan the key turns and the back door unlocks (a simple
 * move of the approved key: the "unlocked" state is not designed yet) + the engine note from the script -> "Yes."
 * -> Theo's Purchase Orders page, 09:04: order 3 slides in (shop-pc po 0 -> .5 -> 1, i.e. look book 05). */
(function () {
  const C = CUES.scenes[3], S = C.start, E = C.end;
  const KEY = 'worlds/martin-key.png';
  let run, rv, note, keySprite, ring, flash;
  Scene({
    id: '4', start: S, end: E, fadeIn: 0,
    build(root) {
      const poCam = [[M('click_order'), 960, 540, 1.0], [E, 660, 470, 1.6]];
      run = seq(root, [
        { src: KEY, at: S, cam: [[S, 640, 330, 1.9], [V(14), 700, 470, 1.45], [M('card'), 960, 540, 1.0], [M('click_unlock'), 975, 540, 1.04]],
          build: l => { rv = reveal(l, KEY, [[1428, 352, 1857, 380], [1426, 391, 1835, 419], [1427, 431, 1678, 452]], { color: '#F5F2EA', a: V(14), b: VE(14) - .1, chars: [36, 31, 21] }); },
          over: t => rv.render(t) },
        { src: 'world/x_mouse_monday.png', at: M('click_unlock') - .1, fi: .15, cam: [[M('click_unlock'), 960, 560, 1.05], [M('unlock'), 960, 578, 1.1]] },
        { src: KEY, at: M('unlock') - .15, fi: .2, cam: [[M('unlock') - .15, 1180, 655, 2.0], [M('click_order'), 1150, 650, 2.25]],
          build: l => {
            flash = el('div', {}, l); css(flash, { left: '990px', top: '585px', width: '300px', height: '240px', background: '#fff', mixBlendMode: 'screen' });
            ring = el('div', {}, l); css(ring, { left: '1291px', top: '709px', width: '0px', height: '0px', borderRadius: '50%', border: '4px solid #D3A14A' });
            keySprite = el('div', {}, l);
            css(keySprite, { left: '1249px', top: '667px', width: '84px', height: '84px', borderRadius: '50%', backgroundImage: `url("${imgPath(KEY)}")`,
              backgroundPosition: '-1249px -667px', backgroundSize: '1920px 1080px', transformOrigin: '42px 42px' });
          },
          over: t => {
            const u = M('unlock');
            keySprite.style.transform = `rotate(${(90 * easeInOutCubic(P(t, u, .4))).toFixed(2)}deg)`;
            const k = P(t, u + .3, .9);
            const r = lerp(40, 120, easeOutCubic(k));
            css(ring, { left: (1291 - r) + 'px', top: (709 - r) + 'px', width: 2 * r + 'px', height: 2 * r + 'px', opacity: (k > 0 && k < 1 ? 1 - k : 0).toFixed(3) });
            flash.style.opacity = (.45 * pulse(t, u + .45, .35)).toFixed(3);
          } },
        { src: 'scr/s4_po_0.jpg', at: M('click_order') - .02, cam: poCam },
        { src: 'scr/s4_po_5.jpg', at: M('po') + .3, cam: poCam },
        { src: 'look/shop-pc-05-shop-po.png', at: M('po') + .55, fi: .25, cam: poCam },
      ], E);
      // engine note (script, scene 4), in the Martin pages' footer style (worlds2 martin-page.css .foot)
      note = label(root, 'synapse · rebuilt with 1 more capability · 0.38 s',
        'left:0;top:996px;width:1920px;height:84px;padding:22px 64px 0;font:500 26px "Cascadia Code","Cascadia Mono",Consolas,monospace;color:#7D766A;letter-spacing:.02em;background:#F5F2EA;border-top:1px solid #E5DED0');
    },
    render(t) {
      run.render(t);
      fadeEl(note, t, M('engine_unlock'), M('click_order'), .35, .2);
    },
  });
})();
