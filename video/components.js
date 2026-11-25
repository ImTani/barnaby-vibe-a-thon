/* components.js: Barnaby's film components. Build once in a scene's build(); update in render() as a pure function of t.
 * All look-alikes of the real app (ui/) and the real 2009 shop system (systems/spokes-and-sprockets).
 * Data shown comes from window.DATA (video/data.js), exported from a real recorded run. */
(function (G) {
'use strict';

const BELL = (size = 40) => `<svg width="${size}" height="${size}" viewBox="0 0 64 64"><defs><linearGradient id="bg${size}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f0cf8f"/><stop offset=".55" stop-color="#d4a85a"/><stop offset="1" stop-color="#9c7232"/></linearGradient></defs><circle cx="32" cy="13" r="3.6" fill="url(#bg${size})"/><rect x="30.4" y="15.5" width="3.2" height="6" rx="1.2" fill="url(#bg${size})"/><path d="M9 45 A23 23 0 0 1 55 45 Z" fill="url(#bg${size})"/><path d="M17 38 A16 16 0 0 1 27 26" fill="none" stroke="#fff3d6" stroke-opacity=".55" stroke-width="2.2" stroke-linecap="round"/><rect x="5" y="46" width="54" height="5.5" rx="2.75" fill="url(#bg${size})"/></svg>`;

/** The 2009 back office window. rows: [[job, mechanic, work, customer, hrs, due], ...] */
const SHOP_ROWS = [
  ['4471', 'Dev', 'Wheel build (front, 32 hole)', 'Rachel Okafor', '6.0', 'Tue'],
  ['4472', 'Dev', 'Wheel build (rear, 32 hole)', 'Magnus Lindqvist', '5.5', 'Wed'],
  ['4475', 'Ravi', 'Full service', 'Sofia Ferreira', '3.0', 'Tue'],
  ['4478', 'Dev', 'Brake bleed + new pads', 'Anika Banerjee', '1.5', 'Tue'],
  ['4481', 'Dev', 'Full service', 'Tom Whitfield', '3.0', 'Mon'],
  ['4483', 'Dev', 'Drivetrain overhaul', 'Funmi Adeyemi', '4.5', 'Wed'],
  ['4485', 'Dev', 'Headset replacement', 'Thanh Nguyen', '1.0', 'Tue'],
  ['4488', 'Ravi', 'Suspension fork service', 'Jana Novak', '4.0', 'Thu'],
  ['4490', 'Ravi', 'Bottom bracket replacement', 'Kwame Mensah', '1.5', 'Tue'],
];

function shop2009(o = {}) {
  const { parent, x = 120, y = 120, w = 1100, page = 'Jobs', rows = SHOP_ROWS } = o;
  const root = el('div', { cls: 'xp abs', style: `left:${x}px;top:${y}px;width:${w}px` }, parent);
  root.innerHTML = `<div class="xp-title"><span>Spokes &amp; Sprockets Back Office v2.3 - Windows Internet Explorer</span><span class="b"><i></i><i></i><i></i></span></div>
    <div class="xp-banner"><b>Spokes &amp; Sprockets</b><span>A Hartley family workshop &middot; est. 1987</span></div>
    <div class="xp-nav">${['Jobs', 'Customers', 'Parts', 'Purchase Orders', 'Mechanics', 'Invoices', 'Reports (coming soon!!)']
      .map(p => `<a class="${p.startsWith(page) ? 'on' : ''}">${p}</a>`).join('')}</div>
    <div class="xp-body"><h4>Open repair jobs &ndash; this week</h4><table><tr><th>Job #</th><th>Mechanic</th><th>Work</th><th>Customer</th><th>Hrs</th><th>Due</th></tr>
    ${rows.map(r => `<tr>${r.map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</table></div>
    <div class="xp-foot"><span>Best viewed in Internet Explorer 7 at 1024&times;768 &middot; &copy; 2009 Theo H.</span><span>You are visitor No. 004127</span></div>`;
  const cells = [...root.querySelectorAll('tr')].slice(1).map(tr => [...tr.children]);
  return {
    el: root, cells,
    /** set cell text (row index, col index) and optional highlight amount 0..1 */
    set(r, c, text, hl = 0) {
      const td = cells[r] && cells[r][c]; if (!td) return;
      setText(td, text);
      td.style.background = hl > 0 ? mixColor('#ffffff', '#FFF6BF', clamp(hl)) : '';
    },
  };
}

/** Barnaby's display panel (HUD). */
function hud(o = {}) {
  const { parent, x = 1000, y = 200, w = 760 } = o;
  const root = el('div', { cls: 'hud', style: `left:${x}px;top:${y}px;width:${w}px` }, parent);
  root.innerHTML = `<div class="hud-head">${BELL(34)}<span class="hud-name">Barnaby</span><span class="hud-state">at your service</span></div>
    <div class="hud-you"></div><div class="hud-trace"></div><div class="hud-say"></div><div class="hud-cards"></div>`;
  const state = root.querySelector('.hud-state'), you = root.querySelector('.hud-you'), say = root.querySelector('.hud-say');
  return {
    el: root, trace: root.querySelector('.hud-trace'), cards: root.querySelector('.hud-cards'),
    setState(s) { setText(state, s); },
    setYou(who, text) { setHTML(you, text ? `<b>${esc(who)}</b>&ldquo;${esc(text)}&rdquo;` : ''); },
    /** Barnaby's line, typed out from `start` at `cps` characters per second */
    say(text, t, start, cps = 32) {
      const n = Math.floor(clamp((t - start) * cps, 0, text.length));
      setText(say, n > 0 ? '“' + text.slice(0, n) + (n < text.length ? '' : '”') : '');
      return n / text.length;
    },
  };
}

const TIER = { read: COL.read, write: COL.write, grow: COL.grow, build: COL.build, synapse: COL.brass, ok: COL.good };

/** A live-trace row. Build once; call .render(t, at) to slide it in at time `at`. */
function traceRow(parent, { kind = 'read', name = '', args = '', tag = '' } = {}) {
  const c = TIER[kind] || COL.muted;
  const row = el('div', { cls: 'tr', style: `border-left-color:${c}` }, parent);
  row.innerHTML = `<span class="d" style="background:${c}"></span><span><b>${name}</b> ${args ? `<span class="muted">${esc(args)}</span>` : ''}</span><span class="tag" style="color:${c}">${esc(tag)}</span>`;
  return { el: row, render(t, at) { return show(row, t, at, .35, { dy: 10 }); } };
}

/** An approval card. diff: unified diff text (optional). */
function approvalCard(o = {}) {
  const { parent, x = 0, y = 0, w = 760, kind = 'write', title = '', detail = '', diff = '', diffLines = 14, primary = 'Approve' } = o;
  const labels = { write: 'Confirm a change', grow: 'Barnaby would like to grow', build: 'Barnaby wrote new code' };
  const c = TIER[kind];
  const root = el('div', { cls: 'apcard', style: `left:${x}px;top:${y}px;width:${w}px` }, parent);
  root.innerHTML = `<div class="k" style="color:${c}">${labels[kind] || 'Approval'}</div><div class="t">${esc(title)}</div>
    ${detail ? `<div class="sub" style="font-size:18px;margin-bottom:12px">${esc(detail)}</div>` : ''}<div class="dslot"></div>
    <div style="display:flex;gap:10px;margin-top:12px"><span class="btn">${esc(primary)}</span><span class="btn ghost">${kind === 'grow' ? 'Not now' : 'Decline'}</span></div>`;
  if (diff) diffView(root.querySelector('.dslot'), diff, diffLines);
  const btn = root.querySelector('.btn');
  return { el: root, btn, press(t, at) { const k = pulse(t, at, .12); btn.style.transform = `scale(${1 - .08 * k})`; btn.style.filter = `brightness(${1 + .4 * k})`; } };
}

/** Render a unified diff (first `maxLines` meaningful lines). */
function diffView(parent, diff, maxLines = 18) {
  const box = el('div', { cls: 'diff' }, parent);
  let n = 0;
  for (const line of diff.split('\n')) {
    if (n >= maxLines) break;
    if (line.startsWith('diff --git')) { el('div', { cls: 'f', text: line.replace(/^diff --git a\/(\S+).*$/, '$1') }, box); continue; }
    if (/^(index |--- |\+\+\+ |new file mode)/.test(line)) continue;
    const cls = line.startsWith('@@') ? 'hk' : line.startsWith('+') ? 'a' : line.startsWith('-') ? 'r' : '';
    el('div', { cls: 'l ' + cls, text: line || ' ' }, box); n++;
  }
  return box;
}

/** A terminal that types lines. lines: [{t: startTime, text, cls}] (cls: 'p' prompt, 'ok' green). */
function terminal(o = {}) {
  const { parent, x = 0, y = 0, w = 800, h = 300, title = '' } = o;
  const root = el('div', { cls: 'term', style: `left:${x}px;top:${y}px;width:${w}px;height:${h}px` }, parent);
  if (title) el('div', { cls: 'muted', text: title, style: 'font-size:14px;margin-bottom:8px;letter-spacing:.08em' }, root);
  const body = el('div', {}, root);
  return {
    el: root,
    render(t, lines, cps = 60) {
      const html = [];
      for (const L of lines) {
        if (t < L.t) break;
        const n = Math.floor(clamp((t - L.t) * (L.cps || cps), 0, L.text.length));
        html.push(`<div class="${L.cls || ''}">${esc(L.text.slice(0, n))}</div>`);
      }
      setHTML(body, html.join(''));
    },
  };
}

/** Synapse endpoint map: chips for every discovered endpoint; exposed ones glow brass, new ones violet. */
function endpointMap(o = {}) {
  const { parent, x = 0, y = 0, w = 900, endpoints = (G.DATA && DATA.endpoints) || [] } = o;
  const root = el('div', { cls: 'abs', style: `left:${x}px;top:${y}px;width:${w}px` }, parent);
  const chips = endpoints.map(e => ({ key: e.key, el: el('span', { cls: 'ep', text: e.key }, root) }));
  return {
    el: root, chips,
    /** bloomAt: when chips appear (staggered); exposed: Set of keys lit; fresh: Set of keys marked new */
    render(t, bloomAt, exposed = new Set(), fresh = new Set(), gap = .05) {
      chips.forEach((c, i) => {
        show(c.el, t, bloomAt + i * gap, .3, { dy: 8 });
        c.el.className = 'ep' + (exposed.has(c.key) ? ' on' : '') + (fresh.has(c.key) ? ' new' : '');
      });
    },
    add(key) { const c = { key, el: el('span', { cls: 'ep', text: key }, root) }; chips.push(c); return c; },
  };
}

/** A speaker label + line, for on-screen dialogue (who: 'Theo'|'Martin'|'Priya'|'Barnaby'). */
function line(parent, { x = 0, y = 0, w = 1200, who = 'Martin', text = '', size = 34 } = {}) {
  const isB = who === 'Barnaby';
  const root = el('div', { cls: 'abs', style: `left:${x}px;top:${y}px;width:${w}px` }, parent);
  root.innerHTML = `<div style="font:600 15px 'Segoe UI',sans-serif;letter-spacing:.16em;text-transform:uppercase;color:${isB ? COL.brass : COL.muted};margin-bottom:6px">${esc(who)}</div>
    <div class="${isB ? 'serif' : ''}" style="font-size:${size}px;line-height:1.35;${isB ? 'font-style:italic;' : ''}color:${COL.ink}"></div>`;
  const body = root.lastElementChild;
  return { el: root, render(t, at, cps = 30) { show(root, t, at, .4, { dy: 14 }); const n = Math.floor(clamp((t - at) * cps, 0, text.length)); setText(body, (isB ? '“' : '') + text.slice(0, n) + (isB && n >= text.length ? '”' : '')); } };
}

Object.assign(G, { BELL, SHOP_ROWS, shop2009, hud, traceRow, approvalCard, diffView, terminal, endpointMap, line, TIER });
})(window);
