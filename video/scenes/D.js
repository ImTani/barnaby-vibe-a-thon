/* Scene D: Unlock (47–69 s). PLACEHOLDER: replace with the real scene. */
(function () {
  let card;
  Scene({ id: 'D', start: 47, end: 69, drift: 0,
    build(root) { card = el('div', { cls: 'abs hero', style: 'left:0;right:0;top:470px;text-align:center;font-size:72px', text: 'Scene D · Unlock' }, root); },
    render(t) { show(card, t, 47 + .2, .5); },
  });
})();
