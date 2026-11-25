/* Scene F: Build (82–120 s). PLACEHOLDER: replace with the real scene. */
(function () {
  let card;
  Scene({ id: 'F', start: 82, end: 120, drift: 0,
    build(root) { card = el('div', { cls: 'abs hero', style: 'left:0;right:0;top:470px;text-align:center;font-size:72px', text: 'Scene F · Build' }, root); },
    render(t) { show(card, t, 82 + .2, .5); },
  });
})();
