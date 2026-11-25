/* Lisbon desk: the words on the screens. Text only (no DOM); desk.js lays it out.
 *
 * What's real here:
 *   - every endpoint (method, path, tool name) and count comes from endpoints.js, which export_endpoints.js reads out
 *     of the real Synapse scans in .demo/montage;
 *   - Barnaby's log follows what his Connect really does (barnaby/systems.py Registry.connect, barnaby/synapse.py):
 *     the event order, the two Synapse runs (--all-endpoints, then --endpoints with the starter set), the default
 *     starter (the first six GETs), the read-only counts, POST /api/connect and its reply. The timings are staged.
 * What's staged: the Quorum crew data, the render queue, the studio people, Theo's files. Original writing. */
(function (G) {
  'use strict';
  const E = G.LX_ENDPOINTS || {};
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const sp = (cls, s) => `<span class="${cls}">${esc(s)}</span>`;

  /* ------------------------------------------------------------------ Theo's editor ------------------------------ */
  const CODE = [
    '"""Last night\'s renders, ready for dailies.',
    '',
    'For whoever looks after this next: it\'s',
    'small on purpose. Read it top to bottom.',
    '"""',
    'from pathlib import Path',
    'import datetime as dt',
    '',
    'RENDERS = Path("/mnt/renderbox/output")',
    'DAILIES = Path("/studio/dailies")',
    'SINCE = dt.time(19, 0)   # last night, 19:00',
    '',
    '',
    'def last_night(now: dt.datetime) -> list:',
    '    """Frames done since 19:00 yesterday."""',
    '    day = now.date() - dt.timedelta(days=1)',
    '    start = dt.datetime.combine(day, SINCE)',
    '    t0 = start.timestamp()',
    '    return sorted(',
    '        f for f in RENDERS.glob("sc*/*.png")',
    '        if f.stat().st_mtime >= t0',
    '    )',
    '',
    '',
    'def by_shot(frames):',
    '    shots = {}',
    '    for f in frames:',
    '        key = f.parent.name',
    '        shots.setdefault(key, []).append(f)',
    '    return shots',
    '',
    '',
    '# TODO(theo): ask the render box its queue',
  ];
  // git signs: lines Theo has touched since his commit (1-based)
  const CODE_SIGNS = { 25: 'add', 26: 'add', 27: 'add', 28: 'add', 29: 'add', 30: 'add', 33: 'add', 11: 'chg' };

  const KW = new Set(['def', 'return', 'for', 'in', 'if', 'else', 'elif', 'import', 'from', 'as', 'with', 'while', 'class', 'not', 'and', 'or', 'is', 'lambda', 'yield', 'try', 'except', 'pass']);
  const CONST = new Set(['None', 'True', 'False']);
  const BUILTIN = new Set(['sorted', 'list', 'dict', 'len', 'print', 'range', 'open', 'str', 'int']);
  /** Python -> highlighted HTML, one line at a time; `st.doc` carries an open triple-quoted string across lines. */
  function hlPy(line, st) {
    let i = 0, out = '';
    const n = line.length;
    if (st.doc) {
      const j = line.indexOf('"""');
      if (j < 0) return sp('py-doc', line);
      st.doc = false; out += sp('py-doc', line.slice(0, j + 3)); i = j + 3;
    }
    let prev = '';
    while (i < n) {
      const rest = line.slice(i);
      let m;
      if (rest.startsWith('"""')) {
        const j = line.indexOf('"""', i + 3);
        if (j < 0) { st.doc = true; out += sp('py-doc', rest); break; }
        out += sp('py-doc', line.slice(i, j + 3)); i = j + 3; continue;
      }
      if (rest[0] === '#') {
        const todo = rest.match(/^(#\s*)(TODO\(\w+\):)(.*)$/);
        out += todo ? sp('py-com', todo[1]) + sp('py-todo', todo[2]) + sp('py-com', todo[3]) : sp('py-com', rest);
        break;
      }
      if ((m = rest.match(/^"[^"]*"/))) { out += sp('py-str', m[0]); i += m[0].length; continue; }
      if ((m = rest.match(/^[A-Za-z_]\w*/))) {
        const w = m[0];
        const cls = KW.has(w) ? 'py-kw' : CONST.has(w) ? 'py-const' : prev === 'def' ? 'py-fn'
          : BUILTIN.has(w) ? 'py-bi' : /^[A-Z][A-Z_]+$/.test(w) ? 'py-cst' : /^[A-Z]/.test(w) ? 'py-ty'
          : line[i + w.length] === '(' ? 'py-call' : line[i + w.length] === ':' && /\(/.test(line.slice(0, i)) ? 'py-arg' : 'py-id';
        out += sp(cls, w); i += w.length; prev = w; continue;
      }
      if ((m = rest.match(/^\d+(\.\d+)?/))) { out += sp('py-num', m[0]); i += m[0].length; continue; }
      if ((m = rest.match(/^(->|>=|<=|==|!=|[=+\-*/<>])/))) { out += sp('py-op', m[0]); i += m[0].length; continue; }
      if ((m = rest.match(/^[()[\]{}.,:]/))) { out += sp('py-pun', m[0]); i += 1; continue; }
      out += esc(rest[0]); i += 1;
    }
    return out;
  }
  function codeHTML() { const st = { doc: false }; return CODE.map(l => hlPy(l, st)); }

  /* ------------------------------------------------------------------ todo.txt ----------------------------------- */
  // `barnaby: n` items get ticked by state.tick (the film can tick them as each house is read); `evening` items are
  // done by the evening (state.evening = 1). It's Tuesday, Theo's second day: Monday's items are already struck.
  const TODO = [
    { t: 'badge, desk 14, wifi', done: true },
    { t: 'plant survived the flight', done: true },
    { t: 'first commit!!', done: true },
    { t: 'barnaby → the crew\'s memory', barnaby: 1 },
    { t: 'barnaby → the render box', barnaby: 2 },
    { t: 'find the good pastelaria (ask inês)', done: true },
    { t: 'ring uncle M at lunch (shop ok?)', evening: 1 },
    { t: 'learn 10 words of pt (obrigado ✓)' },
  ];

  /* ------------------------------------------------------------------ the terminal ------------------------------- */
  // A session is a list of entries: {k:'prompt', host, path, branch, cmd, at} | {k:'line', html} | {k:'spin', ...}.
  // The LAST prompt is "current": state.type types its command, state.out reveals the lines after it.
  const P = (path, cmd, o = {}) => ({ k: 'prompt', host: o.host || 'lisboa', path, branch: o.branch === undefined ? null : o.branch, cmd, at: o.at || '', st: o.st || 0 });
  const L = (html, cls) => ({ k: 'line', html, cls });
  const BL = L('');

  const FETCH_INFO = [
    [sp('t-user', 'theo') + sp('t-mu', '@') + sp('t-host', 'lisboa')],
    [sp('t-mu', '──────────────')],
    ['os', 'linux, rolling'],
    ['wm', 'tiling · gaps 10'],
    ['shell', 'zsh'],
    ['theme', 'nata (dark)'],
    ['font', 'fira code 12'],
    ['uptime', '1 day, 47 mins'],
    ['desk', '14, by the window'],
    ['day', '2 :)'],
  ];
  function fetchLines() {      // Theo's own `fetch` script: his drawn bike (shown inline, the way image-capable terminals do)
    const rows = FETCH_INFO.map(r => r.length === 1 ? r[0] : sp('t-key', r[0].padEnd(8)) + sp('t-fg', r[1]));
    rows.push('');
    rows.push(['#e0675a', '#f2c14e', '#a8c47a', '#7fc8c0', '#7fb0e6', '#c79be0', '#e9e1d3', '#d9822b'].map(c => `<span class="t-swatch" style="background:${c}"></span>`).join(''));
    return rows.map((h, i) => L(`<span class="t-fetch-pad"></span>${h}` + (i === 0 ? `<span class="t-fetch-art">${G.LXArt.bike(150)}</span>` : ''), i === 0 ? 'art' : ''));
  }
  const GITLOG = [
    ['a41c9e2', '1d', 'theo', 'first commit at the new job!! (olá lisboa)', true],
    ['3f0b7d1', '4d', 'inês', 'dailies: read render paths from box config'],
    ['9c2e44a', '5d', 'marta', 'shotlist: add sc015'],
    ['e17d0b8', '1w', 'rui', 'renderbox: queue limit back to 4'],
  ];
  const gitLines = () => GITLOG.map(([h, t, a, msg, hero]) => L(sp('t-yel', '* ') + sp('t-hash', h) + '  ' + sp('t-mu', t.padEnd(3)) + ' ' + sp('t-auth', a.padEnd(6)) +
    sp(hero ? 't-hero' : 't-fg', msg)));

  // ---- Barnaby's own work, as he logs it. Connect (the app's form, or POST /api/connect) runs Registry.connect:
  // system.connecting -> synapse.run --all-endpoints -> synapse.built -> synapse.run --endpoints "<starter>" ->
  // synapse.built -> system.connected, all written to $BARNABY_STATE/events.jsonl. Theo tails it with his alias `blog`.
  // The starter is the configured one, else the first six read-only (GET) endpoints in scan order.
  function starterOf(key, configured) {
    const r = E[key];
    if (!r) return { keys: [], readOnly: 0, n: 0 };
    const all = r.endpoints.map(e => `${e.m} ${e.p}`), gets = r.endpoints.filter(e => e.m === 'GET');
    const keys = configured ? configured.filter(k => all.includes(k)) : gets.slice(0, 6).map(e => `GET ${e.p}`);
    return { keys, readOnly: gets.length, n: r.count };
  }
  const TAG = { connect: 'b-con', synapse: 'b-syn', ready: 'b-ok', heard: 'b-heard', call: 'b-call', say: 'b-say' };
  /** One event line: time, tag, text; `more` are continuation lines under the text column. */
  const EV = (at, tag, html, ...more) => [
    L(sp('b-time', at) + '  ' + sp(TAG[tag] || 'b-tag', tag.padEnd(8)) + '  ' + html),
    ...more.map(m => L(' '.repeat(20) + m)),
  ];
  /** The endpoint list as `--endpoints` gets it, wrapped at ~50 columns. */
  function wrapList(keys, width = 50) {
    const out = []; let line = '--endpoints "';
    keys.forEach((k, i) => {
      const piece = k + (i < keys.length - 1 ? ',' : '"');
      if ((line + piece).length > width) { out.push(line); line = ''; }
      line += piece;
    });
    out.push(line);
    return out;
  }
  function connectEvents(key, repo, url, t, secs, configured) {
    const st = starterOf(key, configured);
    const list = wrapList(st.keys).map(l => sp('b-arg', l));
    return [
      ...EV(t[0], 'connect', sp('b-name', key) + '  ' + sp('b-arg', repo), sp('b-dim', '→ ') + sp('b-arg', url)),
      ...EV(t[0], 'synapse', sp('b-arg', 'build --auto --local --all-endpoints'),
        sp('s-ok', '✓') + ' ' + sp('s-hero', `Extracted ${st.n} endpoint(s)`) + sp('b-dim', ` · ${secs[0]} s`)),
      ...EV(t[1], 'synapse', sp('b-arg', 'build --auto --local'), ...list,
        sp('s-ok', '✓') + ' ' + sp('b-txt', `${st.keys.length} of ${st.n} exposed`) + sp('b-dim', ` · ${secs[1]} s`)),
      ...EV(t[2], 'ready', sp('b-name', key) + sp('b-txt', ` · ${st.n} endpoints · ${st.readOnly} read-only · ${st.keys.length} exposed`)),
    ];
  }
  const COMFY_STARTER = ['GET /system_stats', 'GET /queue', 'GET /api/jobs', 'GET /history', 'GET /object_info', 'GET /models'];
  function wrapWords(text, width = 50) {
    const out = []; let line = '';
    for (const w of text.split(' ')) { if ((line + ' ' + w).trim().length > width) { out.push(line); line = w; } else line = (line + ' ' + w).trim(); }
    if (line) out.push(line);
    return out;
  }
  const SAY_EV = (at, text) => { const w = wrapWords(text); return EV(at, 'say', sp('b-said', w[0]), ...w.slice(1).map(x => sp('b-said', x))); };

  /** The log pane: its head (Theo's `blog`), its lines in order, and where each beat ends (state.out = lines shown). */
  function barnabyLog() {
    const lines = [], marks = {};
    const push = (name, arr) => { lines.push(...arr); marks[name] = lines.length; };
    push('connectQ', connectEvents('quorum', '/home/theo/crew/quorum', 'http://localhost:8001', ['09:39:58', '09:39:59', '09:40:00'], ['0.51', '0.38']));
    push('quorum', [...EV('09:41:02', 'heard', sp('b-heard-t', '"Barnaby — new job. This is the crew’s memory."')),
      ...EV('09:41:04', 'call', sp('b-name', 'quorum') + sp('b-dim', '.') + sp('b-txt', 'state')),
      ...SAY_EV('09:41:07', SAY.quorum)]);
    push('theo', [...EV('09:41:12', 'heard', sp('b-heard-t', '"Still Theo."')), ...SAY_EV('09:41:13', SAY.theo)]);
    push('connectC', connectEvents('comfyui', '/mnt/renderbox/ComfyUI', 'http://renderbox:8188', ['09:42:31', '09:42:32', '09:42:33'], ['0.66', '0.41'], COMFY_STARTER));
    push('comfy', [...EV('09:43:05', 'heard', sp('b-heard-t', '"And the render box?"')),
      ...EV('09:43:06', 'call', sp('b-name', 'comfyui') + sp('b-dim', '.') + sp('b-txt', 'system_stats')),
      ...EV('09:43:06', 'call', sp('b-name', 'comfyui') + sp('b-dim', '.') + sp('b-txt', 'get_queue')),
      ...SAY_EV('09:43:09', SAY.comfy)]);
    return { head: [P('~', 'blog', { at: '09:38' }), L(sp('b-dim', '── following ~/.barnaby/events.jsonl ──'))], lines, marks };
  }

  // A real morning's scrollback. The prompt is one line; its right side shows the previous command's exit status
  // (when it failed) and the time. Lines longer than the pane wrap, as they do in a terminal (desk.js counts rows).
  const W = 68;                                   // pytest's rule width at this pane's size
  const bar = (title, cls) => { const t = ` ${title} `, n = Math.max(4, W - t.length), a = Math.floor(n / 2); return L(sp(cls, '='.repeat(a) + t + '='.repeat(n - a))); };
  const PIPE = (cmd, at, st) => P('~/work/pipeline', cmd, { branch: 'main', at, st });
  function morning() {
    return [
      ...fetchLines(), BL,                         // .zshrc runs fetch when a shell starts (09:12)
      P('~', 'cd work/pipeline', { at: '09:12' }),
      PIPE('git pull', '09:12'), L(sp('t-fg', 'Already up to date.')),
      PIPE('git lg -3', '09:13'), ...gitLines().slice(0, 3),
      PIPE('gti status', '09:13'), L(sp('t-fg', 'zsh: command not found: gti')),
      PIPE('git status', '09:13', 127),
      L(sp('t-fg', 'On branch main')), L(sp('t-fg', 'Your branch is up to date with \'origin/main\'.')), BL,
      L(sp('t-fg', 'Changes not staged for commit:')),
      L(sp('t-fg', '  (use "git add <file>..." to update what will be committed)')),
      L(sp('t-fg', '  (use "git restore <file>..." to discard changes in working directory)')),
      L('        ' + sp('t-red', 'modified:   dailies.py')), BL,
      L(sp('t-fg', 'no changes added to commit (use "git add" and/or "git commit -a")')),
      PIPE('python -m pytest -q --tb=line', '09:14'),
      L(sp('t-grn', '..') + sp('t-red', 'F') + ' '.repeat(W - 9) + sp('t-fg', '[100%]')),
      bar('FAILURES', 't-red'),
      L(sp('t-fg', '/home/theo/work/pipeline/tests/test_dailies.py:21: assert 0 == 3')),
      bar('short test summary info', 't-cyan'),
      L(sp('t-red', 'FAILED') + sp('t-fg', ' tests/test_dailies.py::test_last_night - assert 0 == 3')),
      L(sp('t-red', '1 failed') + sp('t-fg', ', ') + sp('t-grn', '2 passed') + sp('t-red', ' in 0.31s')),
      PIPE('ls ~/crew', '09:15', 1), L(sp('t-dir', 'quorum')),
    ];
  }

  function sessions() {
    const am = morning();
    const S = {};
    S.fetch = { entries: [...am, PIPE('', '09:15')] };
    // 09:38 a tmux pane opens under this one, tailing Barnaby (`blog`); this shell waits
    S.idle = { entries: [...am, PIPE('', '09:15')] };
    // 09:42 Theo connects the render box himself, through the same API the app's form posts to, with a starter
    // set that can see the card and the queue (the default would be the first six GETs: /ws, /, /embeddings...)
    const cont = [
      sp('t-mu', '> ') + sp('t-flag', '-H ') + sp('t-str', '\'content-type: application/json\' ') + sp('t-fg', '\\'),
      sp('t-mu', '> ') + sp('t-flag', '-d ') + sp('t-str', '\'{"name":"comfyui","repo":"/mnt/renderbox/ComfyUI",'),
      sp('t-mu', 'quote> ') + sp('t-str', '"base_url":"http://renderbox:8188",'),
      sp('t-mu', 'quote> ') + sp('t-str', '"starter":["GET /system_stats","GET /queue",'),
      sp('t-mu', 'quote> ') + sp('t-str', '"GET /api/jobs","GET /history","GET /object_info",'),
      sp('t-mu', 'quote> ') + sp('t-str', '"GET /models"]}\''),
    ].map(h => L(h));
    S.comfy = { entries: [...am, PIPE('curl -s localhost:8700/api/connect \\', '09:42'), ...cont,
      L(sp('t-fg', '{"ok":true,"system":"comfyui"}')), PIPE('', '09:42')] };
    // Tuesday evening: the test passes, Marta's 14:06 commit comes down, Theo commits this morning's TODO and pushes
    S.night = { entries: [
      PIPE('python -m pytest -q', '17:05'),
      L(sp('t-grn', '...') + ' '.repeat(W - 9) + sp('t-fg', '[100%]')), L(sp('t-grn', '3 passed in 0.29s')),
      PIPE('git pull', '17:05'),
      L(sp('t-fg', 'Updating a41c9e2..5d02c91')), L(sp('t-fg', 'Fast-forward')),
      L(sp('t-fg', ' shotlist/sc014.csv | 2 ') + sp('t-grn', '+') + sp('t-red', '-')),
      L(sp('t-fg', ' 1 file changed, 1 insertion(+), 1 deletion(-)')),
      PIPE('git commit -am "dailies: ask the render box what\'s queued"', '17:06'),
      L(sp('t-fg', '[main b7e1f20] dailies: ask the render box what\'s queued')),
      L(sp('t-fg', ' 1 file changed, 14 insertions(+), 2 deletions(-)')),
      PIPE('git push', '17:06'),
      ...['Enumerating objects: 5, done.', 'Counting objects: 100% (5/5), done.', 'Delta compression using up to 16 threads',
        'Compressing objects: 100% (3/3), done.', 'Writing objects: 100% (3/3), 641 bytes | 641.00 KiB/s, done.',
        'Total 3 (delta 2), reused 0 (delta 0), pack-reused 0', 'To git.studio.lan:pombo/pipeline.git',
        '   5d02c91..b7e1f20  main -> main'].map(t => L(sp('t-fg', t))),
      PIPE('git lg -3', '20:06'),
      ...[['b7e1f20', '3h', 'theo', "dailies: ask the render box what's queued"], ['5d02c91', '6h', 'marta', 'shotlist: sc014 animatic due Thu 26 Nov'],
        ['a41c9e2', '1d', 'theo', 'first commit at the new job!! (olá lisboa)']].map(([hh, t, a, msg]) =>
        L(sp('t-yel', '* ') + sp('t-hash', hh) + '  ' + sp('t-mu', t.padEnd(3)) + ' ' + sp('t-auth', a.padEnd(6)) + sp('t-fg', msg))),
      PIPE('', '20:07')] };
    return S;
  }

  /* ------------------------------------------------------------------ the crew chat (staged) ---------------------- */
  // The studio's team chat, #pombo-crew. A message shows once state.time has reached it (pure: filtered by time).
  const CHAT = [
    // yesterday (Theo's first day), above the Today divider
    { mon: 1, at: '16:12', who: 'rui', text: 'welcome to the crew, theo! desk 14 is yours' },
    { mon: 1, at: '16:15', who: 'theo', text: 'obrigado! the plant made it too' },
    { mon: 1, at: '17:40', who: 'inês', text: 'render box access sorted: ssh renderbox, the queue is shared so be nice' },
    { mon: 1, at: '18:03', who: 'marta', text: 'sc015 shotlist is up' },
    { at: '08:47', who: 'inês', text: 'bom dia! last night\'s BG passes are in /mnt/renderbox/output' },
    { at: '09:02', who: 'rui', text: 'dailies 10:00, screening room. bring the pombo pencil test' },
    { at: '09:20', who: 'marta', text: '@theo can you check the sc14 animatic date? producer says thu, my note from the call says fri', mention: true },
    { at: '09:36', who: 'theo', text: 'on it. hooking barnaby up to quorum' },
    { at: '09:40', who: 'inês', text: 'barnaby??' },
    { at: '09:42', who: 'theo', text: 'you\'ll see :)' },
    { at: '14:05', who: 'marta', text: 'sc14 animatic is THU 26. resolved in quorum, thanks barnaby' },
    { at: '18:02', who: 'inês', text: 'overnight batch queued, 6 jobs. hands off the box pls' },
    { at: '19:58', who: 'theo', text: 'boa noite, crew' },
  ];
  const WHO = { 'inês': '#e0a35c', rui: '#7fc8a9', marta: '#c79be0', theo: '#7fb0e6' };

  /* ------------------------------------------------------------------ Barnaby (placeholder words) ---------------- */
  // script v2.1, scene 8: with Theo he speaks a developer's language ("endpoints"), and says "sir" once
  const SAY = {
    quorum: 'Thirteen endpoints, sir — and two deadlines in dispute. Shall I flag them?',
    theo: 'Theo.',                                   // after Theo's "Still Theo."
    comfy: 'Twenty-eight endpoints. It’s on the big card, and three jobs are queued.',
  };
  // his read of each system: every real endpoint (endpoints.js); the ones he exposed (the starter, as in the log)
  const PLAN = {
    quorum: { repo: 'quorum', title: 'quorum · the crew’s memory', note: [['red', '2 deadlines in dispute']], flag: { state: 'red' } },
    comfy: { repo: 'comfyui', starter: 'comfy', title: 'comfyui · the render box', note: [['amber', '3 jobs queued'], ['blue', 'gpu0 · 48 GB, the big card']], flag: { get_queue: 'amber', system_stats: 'blue' } },
    // flag = the endpoints he called for his answer (marked in the list); ■ exposed, □ discovered, not yet his
  };

  /* ------------------------------------------------------------------ the render box (staged) -------------------- */
  // The render box's jobs in submission order. state.job = the one running, state.queued = how many wait behind it.
  // Tue 09:15: job 0 running, 2 queued; 09:39-09:41: job 2, 3 queued; 09:43: job 3, 3 queued ("three jobs are queued"); Tue 20:07: the overnight batch.
  const JOBS = [
    ['sc014_bg_A', 'inês'], ['sc014_bg_B', 'inês'], ['sc015_bg_A', 'marta'], ['sc015_fx_mist', 'rui'],
    ['sc016_bg_A', 'inês'], ['sc016_bg_B', 'marta'], ['sc016_fx_rain', 'rui'], ['sc017_bg_A', 'inês'],
    ['sc017_bg_B', 'inês'], ['sc018_bg_A', 'marta'], ['sc018_bg_B', 'marta'], ['sc018_fx_dust', 'rui'],
    ['sc019_bg_A', 'inês'], ['sc019_bg_B', 'inês'], ['sc020_bg_A', 'marta'], ['sc020_bg_B', 'marta'],
  ].map(([name, who]) => ({ name, who }));
  const OLD_JOBS = ['sc013_bg_C', 'sc013_bg_B', 'sc013_bg_A', 'sc012_bg_D', 'sc012_bg_C', 'sc012_bg_B'];
  const T = { MODEL: '#b39ddb', CLIP: '#ffd500', VAE: '#ff6e6e', IMAGE: '#64b5f6', MASK: '#81c784', CONDITIONING: '#ffa931', LATENT: '#ff9cf9' };
  // node graph in canvas px. Slot rows are 16px under a 22px title; widgets follow the slots.
  const NODES = [
    // one clean left-to-right chain (no backward links): loaders | prompts + encode | sampler | decode | save
    { id: 'ckpt', title: 'Load Checkpoint', x: 0, y: 40, w: 172, out: [['MODEL', 'MODEL'], ['CLIP', 'CLIP'], ['VAE', 'VAE']], wid: [['ckpt_name', 'studio_bg_v3.safetensors', 'combo']] },
    { id: 'img', title: 'Load Image', x: 0, y: 160, w: 172, out: [['IMAGE', 'IMAGE'], ['MASK', 'MASK']], wid: [['image', 'sc014_layout_A.png', 'combo'], ['', 'choose file to upload', 'button']], preview: 'layout', ph: 104 },
    { id: 'note', title: 'Note', tint: 'note', x: 0, y: 404, w: 172, note: 'inês: BG passes in the queue before 18:00 please, the render box is shared!! ♥' },
    { id: 'pos', title: 'CLIP Text Encode (Prompt)', tint: 'green', x: 192, y: 0, w: 210, in: [['clip', 'CLIP']], out: [['CONDITIONING', 'CONDITIONING']], text: 'sc014 background, lisbon rooftops at first light, gouache, flat shapes, studio palette, soft haze over the river', th: 74 },
    { id: 'neg', title: 'CLIP Text Encode (Prompt)', tint: 'red', x: 192, y: 146, w: 210, in: [['clip', 'CLIP']], out: [['CONDITIONING', 'CONDITIONING']], text: 'text, watermark, people, harsh outlines', th: 34 },
    { id: 'enc', title: 'VAE Encode', x: 192, y: 262, w: 150, in: [['pixels', 'IMAGE'], ['vae', 'VAE']], out: [['LATENT', 'LATENT']] },
    { id: 'ks', title: 'KSampler', x: 424, y: 20, w: 198, in: [['model', 'MODEL'], ['positive', 'CONDITIONING'], ['negative', 'CONDITIONING'], ['latent_image', 'LATENT']], out: [['LATENT', 'LATENT']],
      wid: [['seed', '1987', 'num'], ['control_after_generate', 'fixed', 'combo'], ['steps', '28', 'num'], ['cfg', '6.5', 'num'], ['sampler_name', 'euler', 'combo'], ['scheduler', 'normal', 'combo'], ['denoise', '0.62', 'num']] },
    { id: 'dec', title: 'VAE Decode', x: 644, y: 40, w: 132, in: [['samples', 'LATENT'], ['vae', 'VAE']], out: [['IMAGE', 'IMAGE']] },
    { id: 'save', title: 'Save Image', x: 798, y: 40, w: 214, in: [['images', 'IMAGE']], wid: [['filename_prefix', 'pombo/sc014/bg', 'text']], preview: 'gouache', ph: 150 },
  ];
  const LINKS = [['ckpt', 0, 'ks', 0], ['ckpt', 1, 'pos', 0], ['ckpt', 1, 'neg', 0], ['ckpt', 2, 'enc', 1], ['ckpt', 2, 'dec', 1],
    ['img', 0, 'enc', 0], ['pos', 0, 'ks', 1], ['neg', 0, 'ks', 2], ['enc', 0, 'ks', 3], ['ks', 0, 'dec', 0], ['dec', 0, 'save', 0]];
  const GPU_PROCS = [['4127', 'comfy', '40.9G', 'python main.py --listen'], ['3982', 'rui', ' 0.3G', 'python preview.py']];

  /* ------------------------------------------------------------------ Quorum on the laptop (staged) -------------- */
  const QUORUM = {
    conflicts: [
      { what: 'Sc 14 animatic: due date', a: ['the producer\'s email', 'Thu 26 Nov'], b: ['Marta\'s note from the call', 'Fri 27 Nov'], owner: 'Marta' },
      { what: 'Lighting pass to the render box: deadline', a: ['Inês at stand-up', 'Mon 30 Nov'], b: ['the schedule sheet', 'Wed 2 Dec'], owner: 'Inês' },
    ],
    inbox: [
      { from: 'Rui', subj: 'Welcome to the studio, Theo!', claims: 2, at: 'Mon' },
      { from: 'Producer', subj: 'Re: sc14 animatic, Thursday please', claims: 1, at: 'Fri', dispute: true },
      { from: 'Inês', subj: 'render box etiquette (pls read)', claims: 1, at: 'Fri' },
    ],
    claims: [
      // newest first; it's Tuesday morning, so yesterday's are "Mon"
      { t: 'Ring uncle M at lunch', src: 'typed note · Theo', tier: 'device', at: '08:58' },
      { t: 'Marta\'s birthday is 3 Dec', src: 'typed note · Theo', tier: 'mine', at: 'Mon' },
      { t: 'Theo starts Mon 23 Nov, desk 14', src: 'welcome email · Rui', tier: 'team', at: 'Mon' },
      { t: 'Dailies at 10:00 in the screening room', src: 'email · Rui', tier: 'team', at: 'Fri' },
      { t: 'Render box: big jobs in the queue before 18:00', src: 'stand-up note · Inês', tier: 'team', at: 'Fri' },
      { t: 'Pombo client review moved to Fri 4 Dec', src: 'email · producer', tier: 'team', at: 'Thu' },
    ],
  };

  G.LX_CONTENT = { esc, sp, CODE, CODE_SIGNS, codeHTML, TODO, CHAT, WHO, sessions, barnabyLog, COMFY_STARTER, starterOf, SAY, PLAN, JOBS, OLD_JOBS, T, NODES, LINKS, GPU_PROCS, QUORUM };
})(window);
