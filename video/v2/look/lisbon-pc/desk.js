/* Theo's Lisbon desk (film v2 look-dev): one Linux session, a tiling window manager, three outputs.
 *
 *   const d = LX.build(rootEl, { monitor: 'main' | 'studio' | 'laptop', lw: 1280, lh: 720 });  // once
 *   d.render(state);                                                                              // every frame
 *
 * render() is a pure function of `state` (merged over LX.DEFAULT): every animatable property is written on every
 * call, nothing is animated by CSS, so frames can be rendered in any order. Presets: LX.STATES. Logical px; scale
 * the root yourself (index.html does) or render at a device scale factor (render.js: 2x = 2560x1440).
 * Depends on endpoints.js, content.js, art.js, wallpaper.js. All artwork original; no distro or brand logos. */
(function (G) {
  'use strict';
  const C = G.LX_CONTENT, A = G.LXArt, E = G.LX_ENDPOINTS || {};
  const { esc, sp } = C;
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const ease = k => (k = clamp(k), k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
  const px = v => `${Math.round(v * 100) / 100}px`;

  function h(tag, cls, parent, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    if (parent) parent.appendChild(e);
    return e;
  }
  function set(el, html) { if (el._h !== html) { el.innerHTML = html; el._h = html; } }
  function box(el, r) { el.style.left = px(r.x); el.style.top = px(r.y); el.style.width = px(r.w); el.style.height = px(r.h); }

  const DAYS = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'];          // Theo set his clock to pt_PT on day one
  const MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

  /* ------------------------------------------------------------------ state ------------------------------------- */
  const DEFAULT = {
    date: '2026-11-24', time: '09:15', secs: 0,   // Tue 24 Nov 2026: Theo's second day (scene 8), same as the closing night
    evening: 0,              // 0 = the working morning (09:15-09:43), 1 = the evening (20:07): todo.txt, git signs, dailies note
    cpu: .07, mem: 6.1, netDown: .4, netUp: .1, nata: 1,
    temp: 17,                // Lisbon outside, °C (17 on a late-November morning, 13 in the evening)
    // main monitor (DP-1)
    focus: 'edit',           // focused tile: term | edit | todo | barnaby | web
    term: 'fetch',           // Theo's shell: fetch (09:15) | idle (09:38) | comfy (09:42, the curl) | night
    type: 1,                 // 0..1 the shell's current command being typed
    split: 0,                // 0..1 the second terminal opening under the shell: Barnaby's log (`blog`)
    out: 0,                  // Barnaby's log: event lines shown (beats end at LX.marks(): connectQ, quorum, theo, connectC, comfy)
    blink: 1,                // 0|1 terminal cursor
    edTop: 1, edLine: 14,    // editor: first visible line, cursor line
    tick: 0,                 // todo.txt: Barnaby items ticked (0, 1, 2)
    barnaby: 'placeholder',  // Barnaby's slot: off | slot (dashed guide) | frame (empty tile, mount his UI) | placeholder
    say: '', sayK: 1,        // Barnaby's line (a LX_CONTENT.SAY key or literal text) and its reveal 0..1
    plan: '', planK: 1,      // the endpoints he read: '' | quorum | comfy, and their reveal 0..1
    mode: 'idle',            // presence: idle | listening | thinking | speaking
    level: 0,                // 0..1 voice level (drive it from the audio)
    app: 0,                  // 0..1 the browser tile with the REAL Barnaby app sliding in beside the terminal
    // studio monitor (DP-2)
    queueOpen: 0,            // 0..1 the queue sidebar sliding open
    queueHl: 0,              // 0..1 highlight on "3 waiting"
    job: 0,                  // the render box's running job (index into LX_CONTENT.JOBS)
    queued: 3,               // jobs waiting behind it (the "N queued" badge and the queue panel)
    synced: '09:40',         // Quorum's last hub sync on the laptop
    step: 17,                // the running job's sampler step (of 28)
    gpu: .97, vram: 41.2,    // render box gpu0 utilisation 0..1, VRAM GB (of 48)
    frame: 113,              // pencil test frame; drawings on twos sit on odd frames (the head bobs on a 12-frame cycle)
    // laptop (eDP-1)
    lap: 'wall',             // wall (empty workspace: Theo's wallpaper) | quorum
    lapIn: 1,                // 0..1 the Quorum window opening
    qHl: 0,                  // 0..1 highlight on the two disputed deadlines
    dim: 0,                  // 0..1 screen dimming
  };
  const M = C.barnabyLog().marks;      // where each beat ends in Barnaby's log
  const STATES = {
    rest: { queued: 2 },
    // 09:39: Theo fills in the real app's Connect form; the log terminal is open and waiting under his shell
    realapp: { time: '09:39', cpu: .11, focus: 'web', term: 'idle', split: 1, out: 0, app: 1, job: 2, step: 11, frame: 115, lap: 'quorum', synced: '09:38' },
    // 09:41: Connect ran at 09:39:58 (Barnaby's own two Synapse runs, in the log), Theo spoke, Barnaby answers
    quorum: { time: '09:41', cpu: .24, focus: 'log', term: 'idle', split: 1, out: M.quorum, tick: 1, say: 'quorum', plan: 'quorum', mode: 'speaking', level: .55, secs: 7, job: 2, step: 22, frame: 119, lap: 'quorum', qHl: 1 },
    'quorum-theo': { time: '09:41', cpu: .2, focus: 'log', term: 'idle', split: 1, out: M.theo, tick: 1, say: 'theo', plan: 'quorum', mode: 'speaking', level: .4, secs: 9, job: 2, step: 23, frame: 119, lap: 'quorum', qHl: 1 },
    // 09:42 Theo connects the render box with curl (shell); 09:43 he asks, Barnaby reads the card and the queue
    comfy: { time: '09:43', cpu: .19, focus: 'log', term: 'comfy', split: 1, out: M.comfy, tick: 2, say: 'comfy', plan: 'comfy', mode: 'speaking', level: .5, secs: 3, queueOpen: 1, queueHl: 1, job: 3, step: 9, frame: 123, lap: 'quorum', edTop: 11, edLine: 33 },
    night: { evening: 1, time: '20:07', temp: 13, cpu: .04, nata: 3, focus: 'term', term: 'night', tick: 2, mode: 'idle', edTop: 1, edLine: 1,
      step: 9, gpu: 1, vram: 44.6, job: 9, queued: 6, frame: 97, lap: 'wall', synced: '19:58', dim: .5 },
    slot: { barnaby: 'slot' },
    frame: { barnaby: 'frame' },
  };
  function preset(name, over) { return { ...DEFAULT, ...(STATES[name] || {}), ...(over || {}) }; }

  /* ------------------------------------------------------------------ geometry ---------------------------------- */
  const GAP = 10, IN = 8, BAR_H = 26, TOP = 8 + BAR_H + IN;
  function geometry(monitor, LW, LH) {
    const W = LW - 2 * GAP, H = LH - GAP - TOP, g = { bar: { x: GAP, y: 8, w: W, h: BAR_H } };
    if (monitor === 'main') {
      const a = Math.round((W - 2 * IN) * .4309), b = Math.round((W - 2 * IN) * .2974), c = W - 2 * IN - a - b;
      const eh = Math.round((H - IN) * .64);
      g.term = { x: GAP, y: TOP, w: a, h: H };
      const th = Math.round((H - IN) * .42);
      g.termTop = { x: GAP, y: TOP, w: a, h: th };                       // with the log open: the shell on top
      g.log = { x: GAP, y: TOP + th + IN, w: a, h: H - th - IN };        // Barnaby's log under it
      g.edit = { x: GAP + a + IN, y: TOP, w: b, h: eh };
      g.todo = { x: GAP + a + IN, y: TOP + eh + IN, w: b, h: H - eh - IN };
      g.slot = { x: GAP + a + b + 2 * IN, y: TOP, w: c, h: H };
      g.web = { x: GAP + a + IN, y: TOP, w: b + IN + c, h: H };     // the browser: the right-hand container, beside the terminal
    } else if (monitor === 'studio') {
      const a = Math.round((W - IN) * .757), b = W - IN - a, gh = Math.round((H - IN) * .43);
      g.comfy = { x: GAP, y: TOP, w: a, h: H };
      g.gpu = { x: GAP + a + IN, y: TOP, w: b, h: gh };
      g.pencil = { x: GAP + a + IN, y: TOP + gh + IN, w: b, h: H - gh - IN };
    } else {
      g.crew = { x: GAP, y: TOP, w: W, h: H };
    }
    return g;
  }

  /* ------------------------------------------------------------------ the bar ----------------------------------- */
  const WS = { main: [[1, 'dev'], [2, 'web'], [3, 'chat']], studio: [[4, 'render'], [5, 'ref'], [6, 'music']], laptop: [[7, 'crew'], [8, 'mail'], [9, 'notes']] };
  function clock(s) {
    const d = new Date(s.date + 'T12:00:00');
    return `${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
  }
  function spark(v, n, seed) {         // a little cpu history ending at v
    const bars = '▁▂▃▄▅▆▇█';
    let o = '';
    for (let i = 0; i < n; i++) {
      const k = i / (n - 1), x = Math.abs(Math.sin((i + seed) * 1.7) * .5 + Math.sin((i + seed) * .43) * .5);
      const val = lerp(x * .35, v, k * k);
      o += bars[Math.round(clamp(val) * 7)];
    }
    return o;
  }
  function barHTML(monitor, s) {
    const focused = monitor === 'main';
    const active = monitor === 'main' ? 1 : monitor === 'studio' ? 4 : 7;
    const occupied = { 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 0, 7: s.lap === 'quorum' ? 1 : 0, 8: 1, 9: 0 };
    const ws = WS[monitor].map(([n, name]) => `<span class="ws ${n === active ? (focused ? 'on' : 'vis') : ''} ${occupied[n] ? 'occ' : ''}"><b>${n}</b>${name}</span>`).join('');
    const title = monitor === 'main'
      ? (s.app >= .5 ? 'Barnaby · 127.0.0.1:8700' : { term: 'theo@lisboa: ~/work/pipeline', log: 'theo@lisboa: blog · barnaby events', edit: 'dailies.py · ~/work/pipeline', todo: 'todo.txt', barnaby: 'barnaby', web: 'Barnaby · 127.0.0.1:8700' }[s.focus] || '')
      : monitor === 'studio' ? 'ComfyUI · renderbox:8188' : s.lap === 'quorum' ? 'Quorum · the crew\'s memory' : '';
    const cpuPct = Math.round(s.cpu * 100);
    const mods = [];
    if (monitor === 'main') {
      mods.push(`<span class="mod barnaby-bar ${s.barnaby === 'slot' ? 'show' : ''}" id="barnaby-bar"></span>`);
      mods.push(`<span class="mod nata">${A.nata(13)}<b>×${s.nata}</b></span>`);
    }
    mods.push(`<span class="mod">${A.icon('eth', 12)}studio-lan <i>${s.netDown.toFixed(1)}↓ ${s.netUp.toFixed(1)}↑</i></span>`);
    mods.push(`<span class="mod cpu">${A.icon('cpu', 12)}<i class="sparkc">${spark(s.cpu, 8, 3)}</i>${String(cpuPct).padStart(2, ' ')}%</span>`);
    if (monitor !== 'laptop') mods.push(`<span class="mod">${A.icon('mem', 12)}${s.mem.toFixed(1)}G</span>`);
    if (monitor === 'main') mods.push(`<span class="mod">${A.icon('vol', 12)}40%</span>`);
    if (monitor === 'laptop') mods.push(`<span class="mod">${A.icon('bat', 12)}100% · docked</span>`);
    mods.push(`<span class="mod">${A.icon(+s.time.slice(0, 2) >= 18 || +s.time.slice(0, 2) < 7 ? 'moon' : 'sun', 12)}${Math.round(s.temp)}° lisboa</span>`);
    return `<div class="bar-l">${ws}<span class="layout">[]=</span><span class="wtitle">${esc(title)}</span></div>
      <div class="bar-c"><span class="date">${clock(s)}</span><span class="time">${esc(s.time)}</span></div>
      <div class="bar-r">${mods.join('')}</div>`;
  }

  /* ------------------------------------------------------------------ the terminal ------------------------------ */
  const SESSIONS = C.sessions();
  function cmdHTML(cmd) {               // zsh-syntax-highlighting style: command green, flags blue, paths underlined
    return cmd.split(/(\s+)/).map((w, i) => !w.trim() ? w : i === 0 ? sp('t-cmd', w) : w.startsWith('-') ? sp('t-flag', w) : w.startsWith('~') || w.includes('/') ? sp('t-pathu', w) : sp('t-fg', w)).join('');
  }
  function promptLines(p, typed, cursor) {
    const remote = p.host !== 'lisboa';
    const l1 = `<div class="tl tp"><span>${sp('t-user', 'theo')}${sp('t-mu', '@')}${sp(remote ? 't-host-r' : 't-host', p.host)}${remote ? sp('t-ssh', ' (ssh)') : ''} ${sp('t-path', p.path)}` +
      (p.branch ? ` ${sp('t-mu', 'on')} <span class="t-branch">${A.icon('branch', 10)}${esc(p.branch)}</span>` : '') + `</span>${sp('t-rt', p.at)}</div>`;
    const l2 = `<div class="tl">${sp('t-caret', '❯')} ${cmdHTML(typed)}${cursor ? '<span class="t-cur"></span>' : ''}</div>`;
    return [l1, l2];
  }
  function entryHTML(e) {
    if (e.k === 'line') return [`<div class="tl ${e.cls || ''}">${e.html || '&nbsp;'}</div>`];
    if (e.k === 'prompt') return promptLines(e, e.cmd, false);
    return [];
  }
  /** Theo's shell: every entry before the last prompt as it was; the last prompt's command typed by state.type. */
  function termHTML(s, rows) {
    const en = (SESSIONS[s.term] || SESSIONS.fetch).entries;
    let cur = en.length - 1;
    while (cur >= 0 && en[cur].k !== 'prompt') cur--;
    const lines = [];
    for (let i = 0; i < cur; i++) lines.push(...entryHTML(en[i]));
    const p = en[cur];
    lines.push(...promptLines(p, p.cmd.slice(0, Math.round(p.cmd.length * clamp(s.type))), s.blink >= .5 && s.focus === 'term'));
    for (const e of en.slice(cur + 1)) lines.push(...entryHTML(e));
    return lines.slice(Math.max(0, lines.length - rows)).join('');
  }
  /** Barnaby's log (Theo's `blog`, tailing $BARNABY_STATE/events.jsonl): its head, then state.out event lines. */
  const LOG = C.barnabyLog();
  function logHTML(s, rows) {
    const n = Math.max(0, Math.min(LOG.lines.length, Math.floor(s.out)));
    const lines = [];
    for (const e of LOG.head) lines.push(...entryHTML(e));
    for (const e of LOG.lines.slice(0, n)) lines.push(...entryHTML(e));
    if (s.blink >= .5 && s.focus === 'log') lines.push('<div class="tl"><span class="t-cur dim"></span></div>');
    return lines.slice(Math.max(0, lines.length - rows)).join('');
  }
  /** Where the film's beats end in Barnaby's log (values for state.out). */
  function marks() { return { total: LOG.lines.length, ...LOG.marks }; }

  /* ------------------------------------------------------------------ the editor -------------------------------- */
  const CODE = C.codeHTML();
  function editorHTML(s, rows) {
    const top = clamp(Math.round(s.edTop), 1, CODE.length);
    const body = [];
    for (let n = top; n < top + rows; n++) {
      if (n > CODE.length) { body.push(`<div class="el"><span class="es"></span><span class="en"></span><span class="ec t-tilde">~</span></div>`); continue; }
      const cur = n === s.edLine, sign = s.evening >= .5 ? '' : C.CODE_SIGNS[n];   // evening: all committed
      const num = cur ? String(n) : String(Math.abs(n - s.edLine));
      body.push(`<div class="el ${cur ? 'cur' : ''}"><span class="es ${sign || ''}"></span><span class="en">${num}</span><span class="ec">${CODE[n - 1] || ''}</span></div>`);
    }
    const pct = Math.round((top - 1) / Math.max(1, CODE.length - rows) * 100);
    return `<div class="ed-tabs"><span class="tab on">${A.icon('flow', 10)} dailies.py ${s.evening >= .5 ? '' : '<i>+</i>'}</span><span class="tab">README.md</span><span class="ed-path">~/work/pipeline</span></div>
      <div class="ed-body">${body.join('')}</div>
      <div class="ed-status"><span class="mode">NORMAL</span><span class="br">${A.icon('branch', 10)} main</span><span class="fn">dailies.py</span><span class="sp"></span><span>utf-8</span><span class="pos">${s.edLine}:1</span><span class="pct">${top === 1 ? 'top' : pct >= 100 ? 'bot' : pct + '%'}</span></div>`;
  }

  /* ------------------------------------------------------------------ todo.txt ---------------------------------- */
  function todoHTML(s) {
    const rows = C.TODO.map((t, i) => {
      const done = t.done || (t.barnaby && s.tick >= t.barnaby) || (t.evening && s.evening >= .5);
      return `<div class="td ${done ? 'done' : ''} ${t.barnaby ? 'bn' : ''}"><span class="tdn">${i + 1}</span><span class="tdb">${done ? '[x]' : '[ ]'}</span><span class="tdt">${esc(t.t)}</span></div>`;
    }).join('');
    return `<div class="td-head"><span>~/todo.txt</span><span>${clock(s)}</span></div><div class="td-body">${rows}</div>`;
  }

  /* ------------------------------------------------------------------ Barnaby's slot (placeholder) --------------- */
  /** His read of the system: every real endpoint (endpoints.js), revealed in order by k, the relevant ones flagged. */
  function endpointsHTML(key, k) {
    const meta = C.PLAN[key] || {}, r = E[meta.repo];
    const eps = r ? r.endpoints : [];
    const exposed = new Set(C.starterOf(meta.repo, meta.starter === 'comfy' ? C.COMFY_STARTER : undefined).keys);
    const n = eps.length, dense = n > 16;
    const verb = { GET: 'v-get', POST: 'v-post', PUT: 'v-put', PATCH: 'v-put', DELETE: 'v-del' };
    return `<div class="bn-eps ${dense ? 'dense' : ''}">${eps.map((e, i) => {
      const local = clamp(k * (n + 2) - i - 1), flag = (meta.flag || {})[e.tool];
      const on = exposed.has(`${e.m} ${e.p}`);
      return `<div class="ep ${on ? 'on' : 'off'} ${flag ? 'flag-' + flag : ''}" style="opacity:${local.toFixed(3)}"><i>${on ? '■' : '□'}</i><span class="${verb[e.m] || ''}">${esc(e.m)}</span><span class="p">${esc(e.p)}</span></div>`;
    }).join('')}</div>`;
  }
  function presenceSVG(s, size) {
    const c = size / 2, R = size * .27, bars = [];
    const speaking = s.mode === 'speaking', lv = speaking ? clamp(s.level) : 0;
    for (let i = 0; i < 36; i++) {
      const a = i / 36 * Math.PI * 2;
      const wob = .5 + .5 * Math.sin(i * 2.3 + s.secs * 9.1) * Math.sin(i * .7 + s.secs * 4.3);
      const len = 3 + (speaking ? lv * 16 * wob : s.mode === 'listening' ? 3 + 2 * Math.sin(i + s.secs * 3) : 1.5);
      const r0 = R + 6, r1 = r0 + len;
      bars.push(`<line x1="${(c + Math.cos(a) * r0).toFixed(1)}" y1="${(c + Math.sin(a) * r0).toFixed(1)}" x2="${(c + Math.cos(a) * r1).toFixed(1)}" y2="${(c + Math.sin(a) * r1).toFixed(1)}"/>`);
    }
    return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" class="bn-pres ${s.mode}">
      <circle cx="${c}" cy="${c}" r="${R}" class="ring"/><circle cx="${c}" cy="${c}" r="${R * .55}" class="ring2"/><circle cx="${c}" cy="${c}" r="${R * .16}" class="core"/>
      <g class="bars">${bars.join('')}</g></svg>`;
  }
  /** At rest: the systems he's connected to on this desk (none at 09:15; Quorum and ComfyUI once read). */
  function idleHTML(s) {
    const known = [['quorum', 'quorum', 'the crew’s memory'], ['comfyui', 'comfyui', 'the render box']].slice(0, clamp(Math.round(s.tick), 0, 2));
    const rows = known.map(([k, nm, what]) => `<div class="bn-house"><span class="hn">${esc(nm)}</span><span class="hw">${esc(what)}</span><span class="hr">${E[k] ? E[k].count : ''} endpoints</span></div>`).join('');
    return `<div class="bn-idle"><div class="bn-idle-h">systems on this desk</div>${rows || '<div class="bn-house none">none yet. New desk for both of us.</div>'}</div>`;
  }
  function slotHTML(s, r) {
    const line = C.SAY[s.say] || s.say || '';
    const shown = line.slice(0, Math.round(line.length * clamp(s.sayK)));
    const meta = C.PLAN[s.plan];
    const n = meta && E[meta.repo] ? E[meta.repo].count : (s.plan === 'comfy' ? 28 : 13);
    const modeLabel = { idle: 'standing by', listening: 'listening', thinking: 'thinking', speaking: 'speaking' }[s.mode] || s.mode;
    return `<div class="bn-head"><span class="bn-name">Barnaby</span><span class="bn-mode ${s.mode}">${modeLabel}</span></div>
      <div class="bn-pwrap ${!line && !meta ? 'idle' : ''}">${presenceSVG(s, !line && !meta ? 188 : n > 16 ? 96 : 124)}</div>
      ${!line && !meta ? idleHTML(s) : ''}
      <div class="bn-line ${meta && n > 16 ? 'tight' : ''}">${line ? `<span class="q">“</span>${esc(shown)}<span class="ghost">${esc(line.slice(shown.length))}</span>${shown.length === line.length ? '<span class="q">”</span>' : ''}` : ''}</div>
      ${meta ? `<div class="bn-plan"><div class="bn-plan-h"><span>${esc(meta.title)}</span><b>■ ${C.starterOf(meta.repo, meta.starter === 'comfy' ? C.COMFY_STARTER : undefined).keys.length} of ${Math.round(clamp(s.planK) * n)} exposed</b></div>
        ${endpointsHTML(s.plan, clamp(s.planK))}
        <div class="bn-notes" style="opacity:${clamp((s.planK - .8) * 5).toFixed(2)}">${meta.note.map(([c, t]) => `<span class="nt ${c}"><i></i>${esc(t)}</span>`).join('')}</div></div>` : ''}`;
  }

  /* ------------------------------------------------------------------ studio: ComfyUI (staged) ------------------- */
  const SLOT0 = 22 + 6, SLOT_H = 16, WID_H = 20;
  function nodeLayout(nd) {
    const rows = Math.max((nd.in || []).length, (nd.out || []).length);
    let hgt = SLOT0 + rows * SLOT_H + 4;
    if (nd.text) hgt += nd.th + 8;
    if (nd.wid) hgt += nd.wid.length * (WID_H + 3) + 2;
    if (nd.preview) hgt += nd.ph + 6;
    if (nd.note) hgt = 106;
    return { ...nd, h: hgt, rows };
  }
  const NODES = C.NODES.map(nodeLayout), NODE = Object.fromEntries(NODES.map(n => [n.id, n]));
  const sockY = (nd, i) => nd.y + SLOT0 + i * SLOT_H + 8;
  function nodeHTML(nd) {
    const ins = nd.in || [], outs = nd.out || [];
    let rows = '';
    for (let i = 0; i < nd.rows; i++) {
      const a = ins[i], b = outs[i];
      rows += `<div class="cn-row">${a ? `<span class="cn-in"><i style="background:${C.T[a[1]]}"></i>${esc(a[0])}</span>` : '<span></span>'}${b ? `<span class="cn-out">${esc(b[0])}<i style="background:${C.T[b[1]]}"></i></span>` : ''}</div>`;
    }
    let body = '';
    if (nd.text) body += `<div class="cn-text" style="height:${nd.th}px">${esc(nd.text)}</div>`;
    for (const [k, v, kind] of nd.wid || []) {
      body += kind === 'button' ? `<div class="cn-w btn">${esc(v)}</div>`
        : kind === 'text' ? `<div class="cn-w"><span class="k">${esc(k)}</span><span class="v">${esc(v)}</span></div>`
        : `<div class="cn-w"><span class="ar">◀</span><span class="k">${esc(k)}</span><span class="v">${esc(v)}</span><span class="ar">▶</span></div>`;
    }
    if (nd.preview) body += `<div class="cn-prev" style="height:${nd.ph}px">${nd.preview === 'layout' ? A.layout(nd.w - 12, nd.ph) : A.gouache(nd.w - 12, nd.ph, 2)}</div>`;
    if (nd.note) body = `<div class="cn-note">${esc(nd.note)}</div>`;
    return `<div class="cn ${nd.tint ? 't-' + nd.tint : ''}" data-id="${nd.id}" style="left:${nd.x}px;top:${nd.y}px;width:${nd.w}px;height:${nd.h}px">
      <div class="cn-title"><i></i>${esc(nd.title)}</div><div class="cn-prog"></div>${rows}${body}</div>`;
  }
  function linksSVG() {
    const paths = C.LINKS.map(([a, ai, b, bi]) => {
      const A1 = NODE[a], B1 = NODE[b];
      const x1 = A1.x + A1.w, y1 = sockY(A1, ai), x2 = B1.x, y2 = sockY(B1, bi), dx = Math.max(40, (x2 - x1) * .5);
      const col = C.T[(A1.out || [])[ai][1]];
      return `<path d="M${x1} ${y1} C${x1 + dx} ${y1} ${x2 - dx} ${y2} ${x2} ${y2}" stroke="${col}"/>`;
    });
    return `<svg class="cn-links" width="1040" height="640">${paths.join('')}</svg>`;
  }
  function queueHTML(s) {
    const J = C.JOBS, steps = 28, st = clamp(s.step / steps), k = clamp(Math.round(s.job), 0, J.length - 1);
    const run = J[k], queued = Math.max(0, Math.round(s.queued));
    const waiting = J.slice(k + 1, k + 1 + Math.min(3, queued));
    const wait = waiting.map((j, i) => `<div class="qj wait"><span class="qn">${i + 1}</span><span class="qthumb ph"></span><span class="qt"><b>${esc(j.name)}</b><i>${esc(j.who)} · waiting</i></span></div>`).join('') +
      (queued > 3 ? `<div class="q-more">+ ${queued - 3} more</div>` : '');
    const done = [...J.slice(0, k).reverse(), ...C.OLD_JOBS].slice(0, 6);
    const hist = done.map((j, i) => `<div class="qh"><span>${A.gouache(58, 33, 3 + ((k - i) % 6 + 6) % 6)}</span><i>${esc(j.name || j)}</i></div>`).join('');
    return `<div class="q-head"><span>QUEUE</span><span class="q-count">1 running</span></div>
      <div class="qj run"><span class="qthumb">${A.gouache(66, 38, 1 + k, .3 + .7 * st)}</span><span class="qt"><b>${esc(run.name)}</b><i>${esc(run.who)} · step ${Math.round(s.step)}/${steps}</i></span><span class="qbar"><span style="width:${(st * 100).toFixed(1)}%"></span></span></div>
      <div class="q-wait" style="--hl:${clamp(s.queueHl).toFixed(3)}"><span class="q-dot"></span>${queued} waiting</div>${wait}
      <div class="q-head h2"><span>HISTORY</span><span class="q-count">today</span></div><div class="q-hist">${hist}</div>`;
  }
  function gpuHTML(s, w) {
    const cols = Math.floor((w - 20) / 6.3);
    const bar = (v, n) => { const full = Math.floor(v * n), part = Math.round((v * n - full) * 8); return '█'.repeat(full) + (part ? '▏▎▍▌▋▊▉'[part - 1] : '') + ' '.repeat(Math.max(0, n - full - (part ? 1 : 0))); };
    const bw = Math.max(10, cols - 20), u = clamp(s.gpu), vr = clamp(s.vram / 48);
    const hist = []; for (let i = 0; i < cols - 2; i++) { const k = i / (cols - 3); const v = clamp(lerp(.15 + .1 * Math.sin(i * 1.3), u - .04 * Math.abs(Math.sin(i * 2.1)), clamp(k * 1.6))); hist.push('▁▂▃▄▅▆▇█'[Math.round(v * 7)]); }
    const rule = '─'.repeat(cols - 1);
    const L = [
      `${sp('g-host', 'renderbox')} ${sp('t-mu', '·')} ${sp('g-k', 'gpu0')} ${sp('t-mu', '· 48 GB')}<span class="g-rt">${esc(s.time)}</span>`,
      sp('t-faint', rule),
      `${sp('g-k', 'util')} ${sp('t-mu', '▕')}${sp('g-bar', bar(u, bw))}${sp('t-mu', '▏')}${sp('g-v', String(Math.round(u * 100)).padStart(3) + '%')}`,
      `${sp('g-k', 'vram')} ${sp('t-mu', '▕')}${sp('g-bar2', bar(vr, bw))}${sp('t-mu', '▏')}${sp('g-v', s.vram.toFixed(1) + 'G')}`,
      `${sp('g-k', 'temp')} ${sp('t-fg', '71°C')}   ${sp('g-k', 'fan')} ${sp('t-fg', '64%')}   ${sp('g-k', 'pwr')} ${sp('t-fg', Math.round(120 + 200 * u) + '/350W')}`,
      sp('t-faint', rule),
      sp('t-mu', 'util · last 2 min'),
      sp('g-hist', hist.join('')),
      sp('t-faint', rule),
      `${sp('g-th', 'PID'.padEnd(6))}${sp('g-th', 'USER'.padEnd(7))}${sp('g-th', 'VRAM'.padEnd(7))}${sp('g-th', 'COMMAND')}`,
      ...C.GPU_PROCS.map(([pid, user, v, cmd], i) => `${sp('t-fg', pid.padEnd(6))}${sp('t-auth', user.padEnd(7))}${sp(i ? 't-fg' : 'g-v', v.padEnd(7))}${sp('t-fg', cmd)}`),
      sp('t-faint', rule),
      `${sp('g-k', 'clock')} ${sp('t-fg', (1.2 + 1.3 * u).toFixed(2) + ' GHz')}   ${sp('g-k', 'pcie')} ${sp('t-fg', 'x16')}   ${sp('g-k', 'up')} ${sp('t-fg', '12d 4h')}`,
    ];
    return `<div class="gpu-title">theo@renderbox: gpu</div><div class="gpu-body">${L.map(l => `<div class="tl">${l}</div>`).join('')}</div>`;
  }
  /** The last dailies note on this shot, by the clock: Monday's until Tuesday's 10:00 dailies, then Tuesday's. */
  function dailiesNote(s) {
    const [who, txt] = s.evening >= .5 || s.time >= '10:30' ? ['tue dailies · rui:', 'the head hold reads now. on to clean-up']
      : ['mon dailies · rui:', 'better! ease the head back, don’t snap it'];
    return `<div class="pv-note"><b>${who}</b> ${esc(txt)}</div>`;
  }
  function pencilHTML(s, r) {
    const iw = r.w - 16, ih = Math.round(iw * 260 / 400);
    const f = Math.round(s.frame), total = 240;
    const ticks = []; for (let i = 0; i < 48; i++) ticks.push(`<i class="${i % 6 === 0 ? 'key' : ''} ${Math.floor(f / 5) === i ? 'now' : ''}"></i>`);
    return `<div class="pv-title"><span>pombo_sc014_anim_v0${s.evening >= .5 ? 4 : 3}.mov</span><span>pencil test</span></div>
      <div class="pv-img">${A.pigeon(iw, ih, f)}</div>
      <div class="pv-osd"><span class="pv-play">${A.icon('play', 10)}</span><span class="pv-f">${String(f).padStart(4, '0')} / ${String(total).padStart(4, '0')}</span><span>24 fps</span><span>on twos</span></div>
      <div class="pv-ticks">${ticks.join('')}</div>
      ${dailiesNote(s)}`;
  }

  /* ------------------------------------------------------------------ laptop: Quorum (staged) -------------------- */
  function quorumHTML(s, lh) {
    const Q = C.QUORUM, hl = clamp(s.qHl);
    const conf = Q.conflicts.map(c => `<div class="qc" style="--hl:${hl.toFixed(3)}"><div class="qc-h"><span class="tag">DISPUTED</span><b>${esc(c.what)}</b></div>
      <p><b>${esc(c.a[0])}</b> says <span class="d">${esc(c.a[1])}</span>; <b>${esc(c.b[0])}</b> says <span class="d">${esc(c.b[1])}</span>.</p>
      <div class="qc-f"><span class="own">owner · ${esc(c.owner)} resolves</span><span class="btn">Draft a message to ${esc(c.owner)}</span></div></div>`).join('');
    const tierName = { team: 'Team', mine: 'My devices', device: 'Device only' };
    const claims = Q.claims.map(c => `<div class="qcl"><div class="qcl-t">${esc(c.t)}</div><div class="qcl-m"><span class="src">${esc(c.src)}</span><span class="tier ${c.tier}">${tierName[c.tier]}</span><span class="at">${esc(c.at)}</span></div></div>`).join('');
    return `<div class="br-bar"><span class="br-tab on">${A.icon('memory', 10)} Quorum</span><span class="br-url">${A.icon('lock', 10)} localhost:8001</span></div>
      <div class="qa">
        <div class="qa-top"><div class="qa-brand"><b>Quorum</b><span>the crew's memory</span></div>
          <div class="qa-nav"><span>${A.icon('ask', 12)}Ask</span><span>${A.icon('memory', 12)}Memory</span><span class="on">${A.icon('conflict', 12)}Conflicts <i>2</i></span><span>${A.icon('inbox', 12)}Inbox</span></div>
          <div class="qa-dev"><span class="sync"><i></i>synced ${esc(s.synced)}</span><span class="dev">theo-laptop · this device</span></div></div>
        <div class="qa-body">
          <div class="qa-col">
            <div class="qa-sec"><span>Conflicts</span><i>2 open · the owner resolves</i></div>${conf}
            <div class="qa-sec"><span>Ask</span></div>
            <div class="qa-ask"><div class="q">${A.icon('search', 12)} when is the sc14 animatic due?</div>
              <div class="a"><b>Disputed:</b> the producer's email says <span class="d">Thu 26 Nov</span>; Marta's note from the call says <span class="d">Fri 27 Nov</span>.</div></div>
            <div class="qa-sec"><span>Inbox</span><i>read on this device</i></div>
            <div class="qa-inbox">${Q.inbox.slice(0, lh >= 800 ? 3 : 2).map(m => `<div class="qi ${m.dispute ? 'disp' : ''}"><span class="from">${esc(m.from)}</span><span class="subj">${esc(m.subj)}</span><span class="cl">${m.claims} claim${m.claims > 1 ? 's' : ''}${m.dispute ? ' · disputed' : ''}</span><span class="at">${esc(m.at)}</span></div>`).join('')}</div>
          </div>
          <div class="qa-col side"><div class="qa-sec"><span>Latest</span><i>claims, with sources</i></div>${claims}</div>
        </div>
        <div class="qa-foot"><span><i class="g"></i>hub synced</span><span>outbox 0</span><span>search runs on this device</span></div>
      </div>`;
  }

  /* ------------------------------------------------------------------ build ------------------------------------- */
  function build(root, opts = {}) {
    const monitor = opts.monitor || 'main', LW = opts.lw || 1280, LH = opts.lh || 720;
    root.classList.add('lx', 'lx-' + monitor);
    root.style.width = LW + 'px'; root.style.height = LH + 'px';
    root.innerHTML = '';
    const g = geometry(monitor, LW, LH);
    const wall = h('div', 'lx-wall', root, G.LXWall.svg(LW, LH));
    const bar = h('div', 'lx-bar', root); box(bar, g.bar);
    const d = { monitor, root, geometry: g, lw: LW, lh: LH };
    const tile = (parent, cls, r) => { const t = h('div', 'tile ' + cls, parent); box(t, r); return t; };

    if (monitor === 'main') {
      const ws1 = h('div', 'ws-layer', root);
      d.term = tile(ws1, 'term', g.term);
      d.termIn = h('div', 'term-in', d.term);
      d.log = tile(ws1, 'term log', g.log);
      d.logIn = h('div', 'term-in', d.log);
      d.edit = tile(ws1, 'edit', g.edit);
      d.todo = tile(ws1, 'todo', g.todo);
      d.slot = tile(ws1, 'slot', g.slot); d.slot.id = 'barnaby-slot';
      d.slotPh = h('div', 'bn-ph', d.slot);
      d.client = h('div', 'bn-client', d.slot); d.client.id = 'barnaby-client';
      d.guide = h('div', 'bn-guide', d.slot);
      const sx = g.slot;
      d.guide.innerHTML = `<b>#barnaby-slot</b><span>logical x=${sx.x} y=${sx.y} w=${sx.w} h=${sx.h}</span><span>2560×1440: x=${sx.x * 2} y=${sx.y * 2} ${sx.w * 2}×${sx.h * 2}</span><span>1920×1080: x=${sx.x * 1.5} y=${sx.y * 1.5} ${sx.w * 1.5}×${sx.h * 1.5}</span><span class="small">mount his UI in #barnaby-client, or replace the slot; #barnaby-layer (whole monitor) and #barnaby-bar (status bar) are free too</span>`;
      d.web = tile(ws1, 'web', g.web);
      d.web.innerHTML = `<div class="br-bar"><span class="br-nav">${A.icon('back', 11)}${A.icon('fwd', 11)}${A.icon('reload', 11)}</span><span class="br-tab on"><span class="fav"></span>Barnaby</span><span class="br-url">${A.icon('lock', 10)} 127.0.0.1:8700</span></div>
        <div class="br-page"><img class="realapp" alt="the real Barnaby app" src="${opts.realapp || 'realapp/barnaby-connect.png'}"></div>`;
      d.layer = h('div', 'barnaby-layer', root); d.layer.id = 'barnaby-layer';
      d.logRows = Math.floor((g.log.h - 14) / 15);
      d.edRows = Math.floor((g.edit.h - 46) / 15.5);
    } else if (monitor === 'studio') {
      d.comfy = tile(root, 'comfy', g.comfy);
      d.comfy.innerHTML = `<div class="br-bar"><span class="br-nav">${A.icon('back', 11)}${A.icon('fwd', 11)}${A.icon('reload', 11)}</span><span class="br-tab on"><span class="fav cf"></span>ComfyUI</span><span class="br-tab">pombo · shot list</span><span class="br-url">renderbox:8188</span></div>
        <div class="cf-app"><div class="cf-top"><span class="cf-menu">Workflow</span><span class="cf-menu">Edit</span><span class="cf-menu">Help</span>
          <span class="cf-wtab on">sc014_bg_paintover</span><span class="cf-wtab">sc015_bg</span><span class="cf-sp"></span><span class="cf-qbadge"></span><span class="cf-run">${A.icon('play', 10)} Run</span></div>
          <div class="cf-main"><div class="cf-rail"><span class="r-q">${A.icon('queue', 15)}</span><span>${A.icon('nodes', 15)}</span><span>${A.icon('models', 15)}</span><span>${A.icon('flow', 15)}</span><span class="r-end">${A.icon('gear', 15)}</span></div>
            <div class="cf-canvas"><div class="cf-panel"></div><div class="cf-graph">${linksSVG()}${NODES.map(nodeHTML).join('')}</div>
            <div class="cf-zoom">${A.icon('search', 11)} 84%</div></div></div></div>`;
      d.cfPanel = d.comfy.querySelector('.cf-panel');
      d.cfGraph = d.comfy.querySelector('.cf-graph');
      d.cfBadge = d.comfy.querySelector('.cf-qbadge');
      d.cfRailQ = d.comfy.querySelector('.r-q');
      d.ksProg = d.comfy.querySelector('.cn[data-id="ks"] .cn-prog');
      d.ksNode = d.comfy.querySelector('.cn[data-id="ks"]');
      d.gpu = tile(root, 'gpu', g.gpu);
      d.pencil = tile(root, 'pencil', g.pencil);
    } else {
      d.crew = tile(root, 'crew', g.crew);
    }
    d.dim = h('div', 'lx-dim', root);

    d.render = function (state) {
      const s = { ...DEFAULT, ...state };
      set(bar, barHTML(monitor, s));
      if (monitor === 'main') {
        // the browser slides in over the right-hand container (editor, todo, Barnaby's slot) and back out
        const k = ease(s.app);
        d.web.style.transform = `translateX(${px((LW - g.web.x) * (1 - k))})`;
        d.web.style.visibility = k <= 0 ? 'hidden' : 'visible';
        for (const el of [d.edit, d.todo, d.slot]) el.style.visibility = k >= 1 ? 'hidden' : 'visible';
        // the log terminal opens under the shell (a new window in the left column; the shell shrinks)
        const sk = ease(s.split), th = lerp(g.term.h, g.termTop.h, sk);
        d.term.style.height = px(th);
        d.log.style.transform = `translateY(${px((1 - sk) * (g.log.h + IN))})`;
        d.log.style.visibility = sk <= 0 ? 'hidden' : 'visible';
        d.log.style.opacity = String(clamp(sk * 3));
        set(d.termIn, termHTML(s, Math.floor((th - 14) / 16)));
        set(d.logIn, sk > 0 ? logHTML(s, d.logRows) : '');
        set(d.edit, editorHTML(s, d.edRows));
        set(d.todo, todoHTML(s));
        const f = s.app >= .5 ? 'web' : s.focus;
        for (const [name, el] of [['term', d.term], ['log', d.log], ['edit', d.edit], ['todo', d.todo], ['barnaby', d.slot], ['web', d.web]]) el.classList.toggle('focus', f === name);
        const mode = s.barnaby;
        d.slot.dataset.mode = mode;
        d.slot.style.display = mode === 'off' ? 'none' : '';
        set(d.slotPh, mode === 'placeholder' ? slotHTML(s, g.slot) : '');
      } else if (monitor === 'studio') {
        const qo = ease(s.queueOpen), pw = 214;
        d.cfPanel.style.width = px(pw * qo);
        set(d.cfPanel, qo > 0 ? `<div class="cf-panel-in" style="width:${pw}px">${queueHTML(s)}</div>` : '');
        // the queue panel overlays the canvas; Theo pans so it covers whole columns (loaders, prompts), never half a node
        d.cfGraph.style.transform = `translate(${px(lerp(14, -134, qo))}, 64px) scale(.84)`;
        d.cfRailQ.classList.toggle('on', qo > .5);
        set(d.cfBadge, `<span style="--hl:${clamp(s.queueHl).toFixed(3)}">${Math.round(s.queued)} queued</span>`);
        d.ksProg.style.width = `${(clamp(s.step / 28) * 100).toFixed(2)}%`;
        set(d.gpu, gpuHTML(s, g.gpu.w));
        set(d.pencil, pencilHTML(s, g.pencil));
      } else {
        const on = s.lap === 'quorum', k = on ? ease(s.lapIn) : 0;
        d.crew.style.display = k > 0 ? '' : 'none';
        d.crew.style.opacity = String(clamp(k * 2));
        d.crew.style.transform = `scale(${(.96 + .04 * k).toFixed(4)})`;
        set(d.crew, on ? quorumHTML(s, LH) : '');
      }
      if (monitor === 'main') {          // the screens dim; Barnaby's slot stays lit (as his bell does at the shop)
        const b = clamp(s.dim), f = b > 0 ? `brightness(${(1 - b).toFixed(3)})` : '';
        for (const el of [wall, bar, d.term, d.log, d.edit, d.todo, d.web]) el.style.filter = f;
        d.slot.style.filter = b > 0 ? `brightness(${(1 - b * .25).toFixed(3)})` : '';
        d.dim.style.opacity = '0';
      } else d.dim.style.opacity = String(clamp(s.dim));
    };
    d.preset = preset;
    d.barnabySlot = d.slot || null;
    d.barnabyClient = d.client || null;
    d.barnabyLayer = d.layer || null;
    return d;
  }

  G.LX = { build, preset, DEFAULT, STATES, geometry, marks };
})(window);
