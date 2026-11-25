/* Scene C: Monday (30–47 s). PLACEHOLDER: replace with the real scene. */
(function () {
  let card;
  Scene({ id: 'C', start: 30, end: 47, drift: 0,
    build(root) { card = el('div', { cls: 'abs hero', style: 'left:0;right:0;top:470px;text-align:center;font-size:72px', text: 'Scene C · Monday' }, root); },
    render(t) { show(card, t, 30 + .2, .5); },
  });
})();
