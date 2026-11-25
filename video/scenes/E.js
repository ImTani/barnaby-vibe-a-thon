/* Scene E: Compose (69–82 s). PLACEHOLDER: replace with the real scene. */
(function () {
  let card;
  Scene({ id: 'E', start: 69, end: 82, drift: 0,
    build(root) { card = el('div', { cls: 'abs hero', style: 'left:0;right:0;top:470px;text-align:center;font-size:72px', text: 'Scene E · Compose' }, root); },
    render(t) { show(card, t, 69 + .2, .5); },
  });
})();
