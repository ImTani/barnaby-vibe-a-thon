/* 4 · A key. Mon 23 Nov, 08:55-09:04. Martin's world LIVE (worlds2 martin-key), from the pads note: "Order ten from
 * Madison, then." prints in the side panel; Barnaby walks on from drawer 1, past the office window, to the back door
 * (08:55); the key disc pops up by the door; his answer types as he says it; the card slides in. "Go on, then." -> the
 * cursor comes in and clicks Allow -> we push into the back door: the key turns in its disc, a ring of brass, and the
 * engine note from the script -> "Yes." -> Theo's Purchase Orders page LIVE (shop-pc, 09:04): the page reloads and
 * order 3 slides in, highlighted (look book 05 is where it lands). */
(function () {
  const C = CUES.scenes[3], S = C.start, E = C.end;
  const AT_DRAWER = .3936;
  let run, note, keyRing, flash, cur, mk, Y = null;
  Scene({
    id: '4', start: S, end: E, fadeIn: 0,
    build(root) {
      const u = M('unlock'), cu = sfxT('mouse_click', M('click_unlock')), arrive = V(14) + .6;   // the press, on its click
      const walkAt = t => lerp(AT_DRAWER, 1, easeInOutSine(clamp((t - (S + .3)) / (arrive - S - .3))));
      const keyState = t => ({
            walk: +walkAt(t).toFixed(4), ask: +easeOutBack(clamp((t - arrive - .15) / .45), 2.4).toFixed(3),
            card: +clamp((t - M('card')) / .6).toFixed(3), martin: +clamp((t - V(13)) / .35).toFixed(3),
            say: +clamp((t - V(14)) / (VE(14) - V(14) - .15)).toFixed(3), time: t < arrive ? '08:54' : '08:55',
            press: +pressAt(t, cu).toFixed(3),
            keyRot: +(90 * easeInOutCubic(P(t, u, .4))).toFixed(2), given: t >= u + .42 ? 1 : 0,
            martinSay: t >= V(17) ? 'Yes.' : t >= V(15) ? 'Go on, then.' : undefined,
          });
      run = seq(root, [
        // Martin's whole world, locked: Barnaby walks on to the back door, the key disc, his answer, the card, the
        // cursor on Allow. The scene's one move, from the click: in to the back door as the key turns in its lock
        { src: 'comp/martin-key', at: S, cam: move(cu + .05, u + .4 - (cu + .05), [960, 540, 1], [1235, 680, 2.0], 0), state: keyState,
          build: l => {
            flash = el('div', {}, l); css(flash, { left: '1251px', top: '669px', width: '80px', height: '80px', borderRadius: '50%', background: '#fff', mixBlendMode: 'screen' });
            keyRing = el('div', {}, l); css(keyRing, { left: '1291px', top: '709px', width: '0px', height: '0px', borderRadius: '50%', border: '5px solid #D3A14A' });
            cur = cursor(l, 1.5);
          },
          over: t => {
            const k = P(t, u + .3, .9), r = lerp(44, 130, easeOutCubic(k));
            css(keyRing, { left: (1291 - r) + 'px', top: (709 - r) + 'px', width: 2 * r + 'px', height: 2 * r + 'px', opacity: (k > 0 && k < 1 ? 1 - k : 0).toFixed(3) });
            flash.style.opacity = (.5 * pulse(t, u + .42, .18)).toFixed(3);
            // the cursor: Martin's hand on the mouse as he says "Go on, then.", to Allow at human speed, the press
            const from = Math.min(V(15), cu - 1.4);
            if (!Y || t < from || t > cu + .9) { cur.at(0, 0, false); return; }
            const p = hand(t, [from, Y[0] + 260, Y[1] + 190], [{ t: cu, x: Y[0], y: Y[1] }], [cu + .9, Y[0] - 40, Y[1] + 60]);
            cur.at(p[0], p[1], true);
          } },
        // "Ten pairs from Madison...": back to the whole world, locked
        { src: 'comp/martin-key', at: V(16), cam: [960, 540, 1], state: keyState },
        { src: 'live/shop', at: M('click_order') - .02, cam: [960, 540, 1],
          state: t => {
            const a = M('po') + .3;
            return { preset: 'shop-po', po: +easeOutCubic(clamp((t - a) / .45)).toFixed(4), poHl: +clamp((t - a) / .3).toFixed(3),
              loading: t >= M('po') && t < a ? +lerp(.2, 1, (t - M('po')) / .3).toFixed(3) : 0, secs: Math.floor(t - M('click_order')) + 20 };
          } },
      ], E, { scene: 4 });
      mk = run.list[0].s;
      // engine note (script, scene 4), in the Martin pages' footer style (worlds2 martin-page.css .foot)
      note = label(root, 'synapse · rebuilt with 1 more capability · 0.38 s',
        'left:0;top:996px;width:1920px;height:84px;padding:22px 64px 0;font:500 26px "Cascadia Code","Cascadia Mono",Consolas,monospace;color:#7D766A;letter-spacing:.02em;background:#F5F2EA;border-top:1px solid #E5DED0');
    },
    ready() {
      const r = mk.win().COMP.yes.getBoundingClientRect();          // Allow, where the card lands (comp px = source px)
      Y = [r.left + r.width * .42, r.top + r.height * .55];
    },
    render(t) {
      run.render(t);
      fadeEl(note, t, M('engine_unlock'), M('click_order'), .35, .2);
    },
  });
})();
