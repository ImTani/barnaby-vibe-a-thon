/* Scene I: Close (146–160 s). PLACEHOLDER: replace with the real scene. */
(function () {
  let card;
  Scene({ id: 'I', start: 146, end: 160, drift: 0,
    build(root) { card = el('div', { cls: 'abs hero', style: 'left:0;right:0;top:470px;text-align:center;font-size:72px', text: 'Scene I · Close' }, root); },
    render(t) { show(card, t, 146 + .2, .5); },
  });
})();
