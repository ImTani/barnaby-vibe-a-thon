/* 9 · Goodnight. The shop at 18:40 (x_close_night: glasses folded on the keyboard, the PC asleep, Barnaby's bell in the
 * corner of the screen) -> Lisbon at 20:07 (lisbon_03: the monitors dim to a single small glow) -> the two desks side by
 * side (close_two_desks) -> the bell, once -> "Barnaby" / "Every system deserves a butler." -> the new desk fades; on the
 * old one: "Even the old ones." -> "Built on Synapse · 2nd Brain Labs × Geek Room Vibe-a-thon" -> the small print ->
 * black. Titles in Barnaby's own type and brass (ui/skins/app3.css), with his mark ringing once (its working animation). */
(function () {
  const C = CUES.scenes[8], S = C.start, E = C.end, FI = .6;
  let run, dimmer, rightOff, shade, title, mark, tag, old, credit, small;
  Scene({
    id: '9', start: S, end: E, fadeIn: 0,
    build(root) {
      const ASLEEP = pick('world/lisbon_03_medium_night_asleep.png', 'world/lisbon_03_asleep_night.png', 'world/lisbon_03_night_asleep.png', '');
      run = seq(root, [
        { src: 'world/x_close_night.png', at: S, cam: hold(940, 570, 1.08) },
        { src: pick('world/lisbon_03_medium_night_on.png', 'world/lisbon_03_medium_night.png'), at: M('lisbon_night'), fi: .9, cam: hold(1010, 525, 1.06),
          build: l => {
            dimmer = el('div', {}, l);       // everything but Barnaby's slot sinks: the two monitors dim to one small glow
            css(dimmer, { left: '0px', top: '0px', width: '1920px', height: '1080px', background: 'radial-gradient(circle at 1148px 480px, rgba(0,0,0,0) 0px, rgba(0,0,0,0) 60px, rgba(0,0,0,.72) 260px)' });
          },
          over: t => { dimmer.style.opacity = ASLEEP ? '0' : easeInOutSine(P(t, M('dim'), 1.6)).toFixed(3); } },
      ].concat(ASLEEP ? [{ src: ASLEEP, at: M('dim'), fi: 1.6, cam: hold(1010, 525, 1.06) }] : []).concat([
        // the last move: the two desks, closing gently as the bell rings and the titles come up
        { src: 'world/close_two_desks.png', at: M('two_desks'), fi: .9, cam: [[M('two_desks'), 960, 540, 1.0], [E, 960, 560, 1.04]] },
      ]), E, { dissolves: true });
      rightOff = el('div', { cls: 'ov' }, root);     // the new desk fades (right half, soft edge)
      css(rightOff, { background: 'linear-gradient(90deg, rgba(0,0,0,0) 900px, #000 1020px)', display: 'none' });
      shade = el('div', { cls: 'ov' }, root);        // a little dark at the top for the titles
      css(shade, { background: 'linear-gradient(180deg, rgba(0,0,0,.72) 0px, rgba(0,0,0,.45) 330px, rgba(0,0,0,0) 520px)', display: 'none' });
      title = label(root, '<span class="m" style="display:inline-block;width:92px;height:92px;vertical-align:-14px;margin-right:26px"></span>Barnaby',
        'left:0;width:1920px;top:118px;text-align:center;font:600 104px "Sitka Subheading","Sitka Text",Constantia,Georgia,serif;color:#EEEAE1;letter-spacing:-.005em');
      mark = title.querySelector('.m'); mark.innerHTML = markSVG('#D3A14A');
      tag = label(root, 'Every system deserves a butler.', 'left:0;width:1920px;top:268px;text-align:center;font:400 52px "Sitka Text",Constantia,Georgia,serif;color:#EEEAE1');
      old = label(root, 'Even the old ones.', 'left:0;width:960px;top:356px;text-align:center;font:italic 400 50px "Sitka Text",Constantia,Georgia,serif;color:#D3A14A');
      credit = label(root, 'Built on Synapse · 2nd Brain Labs × Geek Room Vibe-a-thon', 'left:0;width:1920px;top:930px;text-align:center;font:500 34px "Segoe UI",sans-serif;color:#EEEAE1;letter-spacing:.01em;text-shadow:0 2px 12px #000');
      small = label(root, 'Recreated from a real recorded run. Quorum and ComfyUI staged. See the README.', 'left:0;width:1920px;top:990px;text-align:center;font:400 22px "Segoe UI",sans-serif;color:rgba(238,234,225,.72);text-shadow:0 1px 8px #000');
    },
    render(t) {
      run.render(t);
      const nd = M('new_desk_fades');
      rightOff.style.display = t > nd ? 'block' : 'none';
      rightOff.style.opacity = (.94 * easeInOutSine(P(t, nd, 1.4))).toFixed(3);
      shade.style.display = t > M('title') - .6 ? 'block' : 'none';
      shade.style.opacity = easeInOutSine(P(t, M('title') - .6, 1.0)).toFixed(3);
      fadeEl(title, t, M('title'), null, .8);
      markAnim(mark, t, M('bell_final') + .55);            // the mark rings once, just after the real bell
      fadeEl(tag, t, M('title') + .9, null, .8);
      fadeEl(old, t, M('old_ones'), null, .9);
      fadeEl(credit, t, M('credit'), null, .7);
      fadeEl(small, t, M('small_print'), null, .7);
      Q.setBlack(easeInOutSine(P(t, M('fade_out'), M('end') - M('fade_out'))));
    },
  });
})();
