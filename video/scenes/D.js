/* Scene D: Unlock (47–69 s).
 * Martin asks for brake pads. Barnaby checks his capabilities: six tools exposed, and an ordering endpoint that
 * Synapse already found but he hasn't taken. He asks; Martin clicks Unlock; Synapse rebuilds in 0.38 s and the
 * purchase-order chip lights brass. Then the write itself is confirmed ("Yes.") and the 2009 window's Purchase
 * Orders page gets PO 3. Starts from scene C's layout (shop x 80 / w 1100, HUD x 1000 / w 840) for a soft cut.
 */
(function () {
  const START = 47, END = 69;
  const VO = { martin: 47.6, barnaby: 51.2, yes: 64.0 };                          // cues.json -> voice
  const ASK = 'Order ten pairs, from the usual supplier.', ASK_DUR = 3.03;           // audio/voice/manifest.json
  const SAY = "I can't yet, but the system can. There's an ordering endpoint I haven't taken. May I?", SAY_DUR = 7.53;
  const YES = 'Yes.', YES_DUR = .87;
  const T = { cap: 50.8, grow: 58.9, unlock: 60.6, rebuild: 61.0, rebuilt: 61.5, lit: 61.6, write: 62.6, approve: 64.3, po: 65.4 };
  const PO_EP = 'POST /api/purchase-orders';
  const N_EP = DATA.endpoints.length, N_ON = DATA.starter.length;
  const CMD = '$ synapse build --auto --local --endpoints "…,POST /api/purchase-orders"';
  const IW = 790;                                                                   // HUD inner width (840 - padding - border)
  // The Purchase Orders page. POs 1 and 2 are the 2009 system's own seed rows (systems/spokes-and-sprockets/seed.py);
  // PO 3 is the one Barnaby placed in the recorded run (DATA.turns[1]).
  const PO_ROWS = [
    ['1', 'Chain KMC X11', '10', 'Madison', 'received'],
    ['2', 'Tyre Continental GP5000 28c', '8', 'Continental UK', 'received'],
    ['3', 'Brake pads (Shimano resin, pair)', '10', 'Madison', 'ordered'],
  ];
  const CURSOR = '<svg width="30" height="40" viewBox="0 0 15 20"><path d="M1 1 L1 16 L4.6 12.6 L7.2 18.6 L9.6 17.6 L7 11.7 L12 11.7 Z" fill="#fff" stroke="#111" stroke-width="1.1" stroke-linejoin="round"/></svg>';

  let layer, shop, shopPO, jobsBody, poBody, poRow, poCells, poIns;
  let hd, youEl, sayEl, capWrap, capInner, capRow, mapWrap, mapBox, mapHead, mapChips = [], poChip;
  let slot, growCard, cursor, term, writeCard, rowWrap, writeRow, writeRes;

  /** a wrapper whose height opens from 0 to its content's height (keeps the HUD from carrying empty space) */
  function reveal(wrap, inner, t, at, d = .45) {
    const k = E(t, at, d, easeInOutCubic);
    wrap.style.height = (inner.offsetHeight * k).toFixed(2) + 'px';
    wrap.style.overflow = k < 1 ? 'hidden' : 'visible';
    return k;
  }

  Scene({
    id: 'D', start: START, end: END, drift: .02,
    captions: [[66.0, 68.6, 'Unlock: Synapse had already found it. Barnaby asked, then took it.']],

    build(root) {
      el('style', { text: `
        #scene-D .hud{background:#0E1117}                /* as scene C has it, so the cut matches */
        #scene-D .hud-you{min-height:26px}
        #scene-D .hud-say{margin-bottom:0;overflow:visible}
        #scene-D .hud-cards{position:relative}
        #scene-D .capbox{background:#0B0E13;border:1px solid #262B35;border-radius:12px;padding:10px 12px 6px;margin:0 0 14px}
        #scene-D .caphead{font:600 12px "Segoe UI",sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#8D8778;margin:0 0 8px 2px}
        #scene-D .caphead b{color:#D4A85A;font-weight:600}
        #scene-D .capbox .ep{font-size:13px;padding:4px 8px;margin:0 6px 6px 0}
        #scene-D .capbox .ep.po{border-style:dashed}
        #scene-D .capbox .more{display:inline-block;font:13px "Cascadia Mono",Consolas,monospace;color:#8D8778;padding:4px 4px}
        #scene-D .dterm{position:absolute;left:0;top:0;font-size:16px;line-height:1.6;color:#C2BBA9;background:#0B0E13;border:1px solid #262B35;border-radius:12px;padding:9px 14px;height:78px;white-space:nowrap;overflow:hidden}
        #scene-D .apcard .t{font-size:27px}
        #scene-D .apcard.wr .sub{font-family:"Cascadia Mono",Consolas,monospace;font-size:15px!important;color:#C2BBA9}
        #scene-D .xp table.po{width:860px}
        #scene-D .xp table.po td.st{font-weight:bold}
        #scene-D .xp table.po td.wait{color:#b35900}
        #scene-D .wres{font:600 13px "Segoe UI",sans-serif;letter-spacing:.08em;color:#22C55E;margin-left:10px;white-space:nowrap}
      ` }, root);

      // everything sits on one layer, so the scene can start at scene C's final 2% drift and settle back
      layer = el('div', { cls: 'abs', style: 'left:0;top:0;width:1920px;height:1080px;transform-origin:960px 540px' }, root);
      // the 2009 window, as scene C left it (Jobs page, Anika's brake job highlighted) ...
      shop = shop2009({ parent: layer, x: 80, y: 150, w: 1100, page: 'Jobs' });
      jobsBody = shop.el.querySelector('.xp-body');
      // ... and the same window on its Purchase Orders page (same size; the page is shorter, as a real one would be)
      shopPO = shop2009({ parent: layer, x: 80, y: 150, w: 1100, page: 'Purchase Orders', rows: [] });
      poBody = shopPO.el.querySelector('.xp-body');
      poBody.innerHTML = `<h4>Purchase orders</h4><table class="po"><tr><th>PO #</th><th>Part</th><th>Qty</th><th>Supplier</th><th>Status</th></tr>` +
        PO_ROWS.map(r => `<tr>${r.map((c, i) => `<td class="${i === 4 ? 'st' + (c === 'ordered' ? ' wait' : '') : ''}">${esc(c)}</td>`).join('')}</tr>`).join('') + '</table>';
      const trs = poBody.querySelectorAll('tr');
      poRow = trs[3]; poCells = [...poRow.children];
      // the new row slides in via block wrappers inside its cells, rather than by transforming the <tr> itself
      poIns = poCells.map(td => { const d = el('div', { text: td.textContent }); td.textContent = ''; td.appendChild(d); return d; });

      // Barnaby's display
      hd = hud({ parent: layer, x: 1000, y: 120, w: 840 });
      youEl = hd.el.querySelector('.hud-you');
      sayEl = hd.el.querySelector('.hud-say');

      // trace: barnaby · capabilities, then what it found (6 of 23 exposed; the ordering endpoint is there, not taken)
      capWrap = el('div', {}, hd.trace); capInner = el('div', {}, capWrap);
      capRow = traceRow(capInner, { kind: 'grow', name: 'barnaby · capabilities', args: '{system: shop}', tag: 'grow' });
      mapWrap = el('div', {}, hd.trace);
      mapBox = el('div', { cls: 'capbox' }, mapWrap);
      mapHead = el('div', { cls: 'caphead' }, mapBox);
      const chipsEl = el('div', {}, mapBox);
      for (const k of DATA.starter) mapChips.push(el('span', { cls: 'ep on', text: k }, chipsEl));
      poChip = el('span', { cls: 'ep po', text: PO_EP }, chipsEl); mapChips.push(poChip);
      mapChips.push(el('span', { cls: 'more', text: `+${N_EP - N_ON - 1} more` }, chipsEl));

      // approval cards, terminal and the write call share one slot under Barnaby's line
      slot = hd.cards;
      growCard = approvalCard({ parent: slot, x: 0, y: 14, w: IW, kind: 'grow', title: 'Unlock ' + PO_EP,
        detail: 'Order more of a part from a supplier.', primary: 'Unlock' });
      cursor = el('div', { cls: 'abs', html: CURSOR, style: 'left:0;top:0;filter:drop-shadow(0 3px 4px rgba(0,0,0,.6))' }, growCard.el);
      term = el('div', { cls: 'mono dterm', style: `top:14px;width:${IW}px` }, slot);
      const call = DATA.turns[1].calls.find(c => c.tool === 'create_purchase_order').input;
      writeCard = approvalCard({ parent: slot, x: 0, y: 106, w: IW, kind: 'write', title: 'Order 10 × Brake pads (Shimano resin) from Madison',
        detail: `${PO_EP} · ${JSON.stringify(call).replace(/,/g, ', ').replace(/:/g, ': ')}`, primary: 'Approve' });
      writeCard.el.classList.add('wr');
      rowWrap = el('div', { cls: 'abs', style: `left:0;top:106px;width:${IW}px` }, slot);
      writeRow = traceRow(rowWrap, { kind: 'write', name: 'shop · create_purchase_order', args: `{part_id: ${call.part_id}, quantity: ${call.quantity}}`, tag: 'write' });
      writeRes = el('span', { cls: 'wres', text: '✓ PO 3' });
      writeRow.el.insertBefore(writeRes, writeRow.el.lastElementChild);
    },

    render(t, lt, fade) {
      // ---- framing: C ends at its 2% drift; start there and settle back while our own drift begins.
      // Near the end, dip the layer out under the crossfade so D and E don't double up.
      xf(layer, { s: lerp(1.02, 1, E(t, START + .3, 1.8, easeInOutSine)), o: 1 - easeInOutCubic(P(t, END - .6, .55)) });

      // ---- the 2009 window: already in place from scene C; switches to Purchase Orders at 65.4
      const kPO = P(t, T.po - .25, .15);                                            // a 2009 page load: quick, no easing
      // the Jobs page is taken out once PO is up: left under an identical window it leaves a 1 px seam that
      // depends on the previous frame
      xf(shop.el, { o: kPO < 1 ? 1 : 0 });
      shop.el.style.visibility = kPO < 1 ? 'visible' : 'hidden';
      const hl4478 = .95 * (1 - P(t, T.po - .2, .15));                             // scene C holds it at .95
      for (let c = 0; c < 6; c++) shop.set(3, c, SHOP_ROWS[3][c], hl4478);
      poBody.style.height = jobsBody.offsetHeight + 'px';
      xf(shopPO.el, { o: kPO });
      shopPO.el.style.visibility = kPO > 0 ? 'visible' : 'hidden';
      let kr = 0;
      for (const d of poIns) kr = show(d, t, T.po, .45, { dy: -14 });
      poRow.style.opacity = kr > 0 ? 1 : 0;
      const hl = kr * (1 - .35 * E(t, T.po + 1.2, 1.5, easeInOutCubic));
      for (const td of poCells) td.style.background = hl > 0 ? mixColor('#ffffff', '#FFF6BF', clamp(hl)) : '';

      // ---- Barnaby's display (already up from scene C)
      xf(hd.el, { o: 1 });
      hd.setState(t < T.cap ? 'listening' : t < VO.barnaby ? 'thinking' : t < T.grow - .1 ? 'speaking'
        : t < T.lit + .3 ? 'growing a tool' : t < T.approve ? 'listening' : t < T.po ? 'thinking' : 'at your service');

      // Martin's request types with his voice; at 64.0 it becomes his "Yes."
      if (t < VO.yes) {
        const n = Math.floor(clamp((t - VO.martin) * ASK.length / (ASK_DUR * .92), 0, ASK.length));
        hd.setYou('Martin', ASK.slice(0, n));
        youEl.style.opacity = 1 - easeInOutCubic(P(t, VO.yes - .3, .3));
      } else {
        const n = Math.floor(clamp((t - VO.yes) * YES.length / (YES_DUR * .92), 0, YES.length));
        hd.setYou('Martin', YES.slice(0, n));
        youEl.style.opacity = 1;
      }

      // trace: capabilities row (tick at 50.8), then the map of what the shop offers
      reveal(capWrap, capInner, t, T.cap - .1, .35);
      capRow.render(t, T.cap);
      reveal(mapWrap, mapBox, t, T.cap + .2, .45);
      show(mapBox, t, T.cap + .2, .5, { dy: 10 });
      mapChips.forEach((c, i) => show(c, t, T.cap + .35 + i * .07, .4, { dy: 6 }));
      const lit = t >= T.lit;
      setHTML(mapHead, `shop · <b>${N_ON + (lit ? 1 : 0)}</b> of ${N_EP} tools exposed`);
      // the ordering endpoint: dim (found by Synapse, not taken) -> noticed as he mentions it -> lit at 61.6 (chime)
      const noticed = E(t, 54.3, .9, easeInOutCubic) * (1 - P(t, T.lit, .01));
      // (every property written every frame, never cleared, so the chip's style is identical in any render order)
      poChip.className = 'ep po' + (lit ? ' on' : '');
      const flare = lit ? pulse(t, T.lit + .1, .35) : 0;
      css(poChip, {
        borderStyle: lit ? 'solid' : 'dashed',
        borderColor: lit ? COL.brassDeep : mixColor('#262B35', COL.brass, .75 * noticed),
        color: lit ? COL.ink : mixColor(COL.muted, COL.ink, noticed),
        boxShadow: lit ? `0 0 ${(6 + 22 * flare).toFixed(2)}px ${rgba(COL.brass, .35 + .5 * flare)}` : `0 0 ${(12 * noticed).toFixed(2)}px ${rgba(COL.brass, .22 * noticed)}`,
        background: lit ? `rgba(212,168,90,${(.1 + .25 * flare).toFixed(4)})` : COL.bg,
      });

      // Barnaby's line
      sayEl.style.height = (78 * E(t, VO.barnaby - .25, .45, easeInOutCubic)).toFixed(2) + 'px';
      hd.say(SAY, t, VO.barnaby, SAY.length / (SAY_DUR * .92));

      // ---- slot: grow card -> terminal -> write card -> the write call
      const hG = growCard.el.offsetHeight + 14, hW = writeCard.el.offsetHeight + 106, hR = writeRow.el.offsetHeight + 106;
      const hS = keyframes(t, [[T.grow - .25, 0], [T.grow + .25, hG], [T.write - .15, hG], [T.write + .35, hW], [T.approve + .25, hW], [T.approve + .7, hR]]);
      slot.style.height = hS.toFixed(2) + 'px';

      show(growCard.el, t, T.grow, .5, { dy: 16, out: T.unlock + .22, outD: .3, outDy: 8 });
      growCard.press(t, T.unlock);
      // Martin's pointer comes in from the shop side and clicks Unlock
      const bx = growCard.btn.offsetLeft + growCard.btn.offsetWidth * .55, by = growCard.btn.offsetTop + growCard.btn.offsetHeight * .6;
      const kc = E(t, T.unlock - .85, .75, easeInOutCubic);
      const cx = lerp(-260, bx, kc), cy = lerp(growCard.el.offsetHeight + 150, by, kc) + 18 * Math.sin(Math.PI * kc) * -1;
      xf(cursor, { x: cx, y: cy, s: 1 - .12 * pulse(t, T.unlock, .08), o: P(t, T.unlock - .9, .25) });

      show(term, t, T.rebuild - .1, .4, { dy: 8 });
      const n = Math.floor(clamp((t - T.rebuild) * 160, 0, CMD.length));
      setHTML(term, `<span style="color:${COL.brass}">${esc(CMD.slice(0, n))}</span>` +
        (t >= T.rebuilt ? `<br><span style="color:${COL.good}">✓ rebuilt in 0.38 s</span>` +
          `<span style="color:${COL.muted}">${t >= T.lit ? ' · create_purchase_order is live' : ''}</span>` : ''));

      show(writeCard.el, t, T.write, .5, { dy: 16, out: T.approve + .2, outD: .3, outDy: 8 });
      writeCard.press(t, T.approve);
      writeRow.render(t, T.approve + .4);
      show(writeRes, t, T.po, .4, { dy: 0, dx: -8 });

      // ---- light: the chip's chime, and the new purchase order landing in the 2009 window
      const ctx = Q.fx;
      if (flare > .01) {
        const r = poChip.getBoundingClientRect();
        drawGlow(ctx, r.left + r.width / 2, r.top + r.height / 2, 150, COL.brass, .45 * flare * fade, false);
      }
      const land = pulse(t, T.po + .25, .35);
      if (land > .01) {
        const r = poRow.getBoundingClientRect();
        drawGlow(ctx, r.left + r.width * .3, r.top + r.height / 2, 240, '#FFE9A8', .18 * land * fade, false);
      }
    },
  });
})();
