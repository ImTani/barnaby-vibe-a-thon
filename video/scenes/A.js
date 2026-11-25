/* Scene A: Nine tabs (0–11 s). PLACEHOLDER: replace with the real scene. */
(function () {
  let card;
  Scene({ id: 'A', start: 0, end: 11, drift: 0,
    build(root) { card = el('div', { cls: 'abs hero', style: 'left:0;right:0;top:470px;text-align:center;font-size:72px', text: 'Scene A · Nine tabs' }, root); },
    render(t) { show(card, t, 0 + .2, .5); },
  });
})();
