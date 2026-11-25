/* Scene E: Compose (69–82 s).
 * Barnaby's display, centred. The same four-step chain he ran four times today stacks up (×1…×4). He offers to
 * make it a single motion; Synapse Custom composes one MCP tool; at 78.8 the four rows square up like a deck,
 * the chips slide into the middle and fuse into one skill, finish_bike_and_notify_customer (brass, violet edge).
 */
(function () {
  const START = 69, END = 82;
  const VO = { barnaby: 72.4 };                                                     // cues.json -> voice
  const SAY = "You've had me do these four steps four times today. Shall I make it a single motion?", SAY_DUR = 5.99;
  const CPS = SAY.length / (SAY_DUR * .92);
  const ROW_AT = [69.5, 70.1, 70.7, 71.3];                                         // the four ticks
  const T = { term: 76.4, compose: 77.4, took: 78.1, out: 78.25, converge: 77.9, squeeze: 78.3, fuse: 78.8 };
  const SKILL = 'finish_bike_and_notify_customer';
  const STEPS = ['job_detail', 'customer_detail', 'notify', 'update_status'];
  const tierOf = tool => { const e = DATA.endpoints.find(x => x.tool === tool); return e && e.read_only ? COL.read : COL.write; };
  const LINES = [
    { t: T.term, text: '$ synapse build --custom -q "hand back a finished bike"', cls: 'p', cps: 60 },
    { t: T.compose, text: 'Composing MCP tool …', cls: 'c', cps: 70 },
    { t: T.out, text: '✓ ' + SKILL + '_server.py', cls: 'ok', cps: 110 },
  ];
  // geometry inside the stack (the HUD's trace area, 1350 px wide)
  const IW = 1350, ROW_W = 1180, ROW_H = 70, ROW_GAP = 86, ROW_X = (IW - ROW_W) / 2;
  const CHIP_W = 232, CHIP_X0 = 96, CHIP_STEP = 272;
  const STACK_H = 3 * ROW_GAP + ROW_H, MID = STACK_H / 2;                            // 328, 164
  const ROW_CX = ROW_W / 2;

  let hd, stack, tWrap, tBox, rows = [], skillWrap, skillFrame, skill, steps;

  Scene({
    id: 'E', start: START, end: END, drift: .02,
    captions: [[79.2, 81.8, 'Compose: one verified skill instead of four steps.']],

    build(root) {
      el('style', { text: `
        #scene-E .hud-you{display:none}
        #scene-E .hud-head{margin-bottom:22px}
        #scene-E .hud-trace{position:relative;height:${STACK_H}px;margin-bottom:26px}
        #scene-E .hud-say{font-size:31px;height:48px;text-align:center}
        #scene-E .chain{position:absolute;left:${ROW_X}px;width:${ROW_W}px;height:${ROW_H}px;background:#1B202A;border:1px solid #262B35;border-left:4px solid #3A404C;border-radius:14px}
        #scene-E .chain .x{position:absolute;left:22px;top:0;font:600 22px "Cascadia Mono",Consolas,monospace;line-height:${ROW_H - 2}px;color:#8D8778}
        #scene-E .chain .ch{position:absolute;top:12px;width:${CHIP_W}px;height:44px;display:flex;align-items:center;justify-content:center;gap:10px;font:600 20px "Cascadia Mono",Consolas,monospace;color:#F1ECE1;border:1px solid;border-radius:10px}
        #scene-E .chain .ch i{width:9px;height:9px;border-radius:50%;flex:none}
        #scene-E .chain .ar{position:absolute;top:0;width:${CHIP_STEP - CHIP_W}px;text-align:center;font:22px "Segoe UI",sans-serif;line-height:${ROW_H - 2}px;color:#5A5F6B}
        /* the new skill gets its own compositing layer: otherwise how it rasterises as it appears depends on what the
           panel painted seconds earlier, and verify (rendering out of order) sees a few pixels differ */
        #scene-E .skillwrap{position:absolute;left:0;right:0;text-align:center;will-change:opacity}
        #scene-E .skill{position:relative;display:inline-flex;align-items:center;gap:.485em;padding:.545em .91em .545em .79em;font:600 33px "Cascadia Mono",Consolas,monospace;color:#F1ECE1;border:2px solid transparent}
        /* the pill itself: flat fill (brass 18% over #1B202A), solid brass border, crisp violet edge; no gradient, no blur */
        #scene-E .skillframe{position:absolute;background:#766EBF;border-radius:19px}   /* violet 80% over the panel, opaque */
        #scene-E .skillframe i{position:absolute;inset:3px;background:#3C3933;border:2px solid #D4A85A;border-radius:16px}
        #scene-E .skill .d{width:.39em;height:.39em;border-radius:50%;background:#D4A85A;flex:none}
        #scene-E .skill .tag{font:600 .39em "Segoe UI",sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#D4A85A;margin-left:.62em}
        #scene-E .steps{position:absolute;left:0;right:0;text-align:center;font:18px "Cascadia Mono",Consolas,monospace;color:#8D8778}
        #scene-E .tbox{font-size:19px;line-height:1.6;color:#C2BBA9;background:#0B0E13;border:1px solid #262B35;border-radius:12px;padding:11px 18px}
        #scene-E .tbox .p{color:#D4A85A}#scene-E .tbox .ok{color:#22C55E}#scene-E .tbox .took{color:#F1ECE1}
      ` }, root);

      hd = hud({ parent: root, x: 260, y: 185, w: 1400 });
      stack = hd.trace;

      // the four identical chains
      for (let i = 0; i < 4; i++) {
        const row = el('div', { cls: 'chain', style: `top:${i * ROW_GAP}px` }, stack);
        const x = el('div', { cls: 'x', text: '×' + (i + 1) }, row);
        const chips = [], arrows = [];
        STEPS.forEach((s, j) => {
          const c = tierOf(s);
          const ch = el('div', { cls: 'ch', html: `<i style="background:${c}"></i><span>${s}</span>`, style: `left:${CHIP_X0 + j * CHIP_STEP}px;border-color:${rgba(c, .55)};background:${rgba(c, .13)}` }, row);
          chips.push({ el: ch, label: ch.lastElementChild, c, cx: CHIP_X0 + j * CHIP_STEP + CHIP_W / 2 });
          if (j < 3) arrows.push(el('div', { cls: 'ar', text: '→', style: `left:${CHIP_X0 + j * CHIP_STEP + CHIP_W}px` }, row));
        });
        rows.push({ el: row, x, chips, arrows, top: i * ROW_GAP });
      }

      // the composed skill and, under it, what it does
      skillWrap = el('div', { cls: 'skillwrap', style: `top:${MID - 39}px` }, stack);
      skillFrame = el('div', { cls: 'skillframe', html: '<i></i>' }, skillWrap);   // violet edge = an outer box, not a shadow
      skill = el('div', { cls: 'skill', html: `<span class="d"></span>${SKILL}<span class="tag">new skill</span>` }, skillWrap);
      steps = el('div', { cls: 'steps', style: `top:${MID + 64}px`, text: STEPS.join('  →  ') }, stack);

      // Synapse Custom's terminal, opening under Barnaby's line
      tWrap = el('div', {}, hd.cards);
      tBox = el('div', { cls: 'mono tbox' }, tWrap);
    },

    render(t, lt, fade) {
      show(hd.el, t, START - .3, .8, { dy: 16 });                                   // rises in as D dips out
      hd.setState(t < VO.barnaby ? 'thinking' : t < T.term ? 'speaking' : t < T.fuse + .6 ? 'growing a tool' : 'at your service');
      hd.say(SAY, t, VO.barnaby, CPS);

      // ---- fusion progress
      const kV = E(t, T.converge, .75, easeInOutCubic);                            // rows square up to the middle
      const kH = E(t, T.squeeze, .5, easeInOutCubic);                              // chips slide together
      const fused = t >= T.fuse;

      rows.forEach((r, i) => {
        // stack in (one tick each), chips stagger left to right
        const k = show(r.el, t, ROW_AT[i], .45, { dy: 18 });
        const y = lerp(r.top, MID - ROW_H / 2, kV);
        r.el.style.top = y.toFixed(2) + 'px';
        r.el.style.transform = `translate(0,${((1 - E(t, ROW_AT[i], .45)) * 18).toFixed(2)}px)`;
        r.el.style.opacity = clamp(Math.min(k * 1.15, 1) * (fused ? 0 : 1));
        const clip = 50 * .86 * kH;                                                 // the row's body squeezes to its centre
        r.el.style.clipPath = clip > .01 ? `inset(0 ${clip.toFixed(2)}% 0 ${clip.toFixed(2)}% round 14px)` : 'none';
        // "four times": the row labels catch the light one by one
        const pr = pulse(t, 74.65 + i * .13, .2);
        r.x.style.color = mixColor(COL.muted, COL.brass, pr);
        r.el.style.borderColor = mixColor('#262B35', '#6B5631', pr);
        r.el.style.borderLeftColor = mixColor('#3A404C', COL.brass, pr);
        r.x.style.opacity = 1 - P(t, T.converge, .35);
        r.arrows.forEach(a => { a.style.opacity = 1 - P(t, T.squeeze - .05, .25); });
        r.chips.forEach((c, j) => {
          const kc = show(c.el, t, ROW_AT[i] + .05 + j * .07, .4, { dy: 8 });
          // "these four steps": each step lights in turn, down all four rows at once
          const pc = pulse(t, 73.6 + j * .13, .2);
          c.el.style.background = rgba(c.c, .13 + .2 * pc);
          c.el.style.boxShadow = pc > .02 ? `0 0 ${(18 * pc).toFixed(2)}px ${rgba(c.c, .5 * pc)}` : 'none';
          const dx = (ROW_CX - c.cx) * kH;
          c.el.style.transform = `translate(${dx.toFixed(2)}px,${((1 - E(t, ROW_AT[i] + .05 + j * .07, .4)) * 8).toFixed(2)}px) scale(${lerp(1, .62, kH).toFixed(4)})`;
          c.el.style.opacity = clamp(Math.min(kc * 1.15, 1) * (1 - easeInCubic(clamp((kH - .45) / .55))));
          c.label.style.opacity = 1 - easeOutCubic(clamp(kH / .4));               // names dissolve first; the pills merge
        });
      });

      // ---- the new skill: a spring pop at 78.8, then a slow breath of light
      // The pill (a flat frame) springs open from the point of light while its name fades in at its final size. Flat
      // fills, solid borders and fixed-size text on purpose: scaled text, resized gradients and large changing blurs
      // rasterise slightly differently depending on earlier frames. The glow is light on the FX canvas (below).
      const kp = spring(P(t, T.fuse, .9)), W0 = skill.offsetWidth, H0 = skill.offsetHeight;
      const fw = 2 * Math.round(W0 * lerp(.12, 1, kp) / 2), fh = 2 * Math.round(H0 * lerp(.45, 1, kp) / 2);
      skillWrap.style.top = Math.round(MID - H0 / 2) + 'px';
      css(skillFrame, { left: Math.round((IW - fw) / 2) - 3 + 'px', top: Math.round((H0 - fh) / 2) - 3 + 'px', width: fw + 6 + 'px', height: fh + 6 + 'px',
        opacity: fused ? '1' : '0' });
      skill.style.opacity = E(t, T.fuse + .08, .35, easeOutCubic).toFixed(4);
      show(steps, t, T.fuse + .55, .6, { dy: 8 });

      // ---- Synapse Custom
      const html = [];
      for (const L of LINES) {
        if (t < L.t) { html.push('<div>&nbsp;</div>'); continue; }
        const n = Math.floor(clamp((t - L.t) * L.cps, 0, L.text.length));
        let s = `<span class="${L.cls}">${esc(L.text.slice(0, n))}</span>`;
        if (L.cls === 'c' && t >= T.took) s += '<span class="took"> 16 s</span>';
        html.push(`<div>${s}</div>`);
      }
      setHTML(tBox, html.join(''));
      // the terminal opens under Barnaby's line (measured after this frame's text is in)
      const kt = E(t, T.term - .3, .45, easeInOutCubic);
      tWrap.style.height = (tBox.offsetHeight * kt).toFixed(2) + 'px';
      tWrap.style.overflow = kt < 1 ? 'hidden' : 'visible';
      show(tBox, t, T.term - .3, .5, { dy: 10 });

      // ---- light (front canvas, so scale by `fade`): gathers where the chips meet, then one warm flash as the skill
      // appears, with a wider violet bloom behind it
      const ctx = Q.fx, sr = stack.getBoundingClientRect(), sc = sr.width / IW;
      const cx = sr.left + (ROW_X + ROW_CX) * sc, cy = sr.top + MID * sc;
      const gather = kH * (1 - P(t, T.fuse, .05));
      if (gather > .01) drawGlow(ctx, cx, cy, lerp(80, 260, kH) * sc, COL.brass, .32 * gather * fade, false);
      if (t >= T.fuse - .02 && t < T.fuse + 1.6) {
        drawGlow(ctx, cx, cy, 420 * sc, COL.brass, .42 * pulse(t, T.fuse + .05, .22) * fade, false);
        drawGlow(ctx, cx, cy, 620 * sc, COL.build, .28 * pulse(t, T.fuse + .14, .4) * fade, false);
      }
      // then the new skill keeps a slow, warm breath of light (brass, with violet wings at its ends)
      const hold = E(t, T.fuse, .5, easeOutCubic), breath = .5 + .5 * Math.sin((t - T.fuse) * 2.2);
      if (hold > .01) {
        const w = skill.offsetWidth * sc;
        drawGlow(ctx, cx, cy, 300 * sc, COL.brass, (.13 + .04 * breath) * hold * fade, false);
        for (const sx of [-1, 1]) drawGlow(ctx, cx + sx * w * .46, cy, 120 * sc, COL.build, (.16 + .05 * breath) * hold * fade, false);
      }
    },
  });
})();
