/* Scene G: Priya, day one (120–131 s). PLACEHOLDER: replace with the real scene. */
(function () {
  let card;
  Scene({ id: 'G', start: 120, end: 131, drift: 0,
    build(root) { card = el('div', { cls: 'abs hero', style: 'left:0;right:0;top:470px;text-align:center;font-size:72px', text: 'Scene G · Priya, day one' }, root); },
    render(t) { show(card, t, 120 + .2, .5); },
  });
})();
