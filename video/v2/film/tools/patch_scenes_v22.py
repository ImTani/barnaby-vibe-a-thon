"""Scenes on the v2.2 shot plan (video/v2/SHOTLIST.md section 5). Run once from video/v2/film:
python tools/patch_scenes_v22.py"""
import pathlib, re

def sub(path, a, b, count=1):
    p = pathlib.Path(path); s = p.read_text(encoding='utf-8')
    assert s.count(a) == count, (path, a[:80], s.count(a))
    p.write_text(s.replace(a, b), encoding='utf-8')

def block(path, new):
    """replace the scene's `run = seq(root, [ ... ], E...);` block"""
    p = pathlib.Path(path); s = p.read_text(encoding='utf-8')
    i = s.index('      run = seq(root, [')
    j = s.index('], E', i); j = s.index(';', j) + 1
    p.write_text(s[:i] + new.strip('\n') + s[j:], encoding='utf-8')

# hard cuts between scenes too (time jumps cut on the sound bridge); only scene 9's own dissolves remain
for n in range(2, 10):
    p = pathlib.Path(f'scenes/s{n}.js'); s = p.read_text(encoding='utf-8')
    s2 = re.sub(r"fadeIn: FI,", "fadeIn: 0,", s)
    s2 = s2.replace("at: S - FI,", "at: S,")
    p.write_text(s2, encoding='utf-8')

# ---- 1 · the opening: held wide, one approach (on the stills; Blender's s1_open when done), then the push in
sub('scenes/s1.js', """        { src: 'world/01_wide_night.png', at: S,
          cam: [[M('light_up'), 960, 540, 1.0], [M('medium') + .5, 880, 455, 1.3]],
          grade: t => `brightness(${easeInOutSine(P(t, M('light_up'), 1.8)).toFixed(3)})` },
        { src: 'world/02_medium_night.png', at: M('medium'), fi: .45,
          cam: [[M('medium'), 880, 640, 1.04], [M('screen') + .4, 842, 626, 1.6]] },
        { src: 'live/shop', at: M('screen'), fi: .35, cam: tabCam, state: t => state(t) },""",
"""        { src: 'world/01_wide_night.png', at: S, cam: hold(960, 540, 1.0),
          grade: t => `brightness(${easeInOutSine(P(t, M('light_up'), 1.8)).toFixed(3)})` },
        { src: 'world/02_medium_night.png', at: M('medium'), cam: move(M('medium') + .4, M('screen') - M('medium') - .5, [880, 640, 1.04], [842, 626, 1.6], 0) },
        // 1.2 into the screen: the live desktop pinned on the monitor's glass grows to full frame (a cut without a quad)
        { src: 'live/shop', at: M('screen'), fi: .12, pin: { shot: 's1_open', d: .6 }, cam: tabCam, state: t => state(t) },""")

# ---- 2 · the handover
block('scenes/s2.js', """      run = seq(root, [
        // 2.1 the photo: a very slow push (memory); 2.2 the calendar, held; 2.3 the desk at night for "Seventeen years."
        { src: 'world/photo_2009.png', at: S, cam: move(S + .3, M('calendar') - S - .5, [750, 550, 1.04], [730, 540, 1.12], 0) },
        { src: 'world/x_board_night.png', at: M('calendar'), cam: hold(400, 620, 1.55) },
        { src: 'world/02_medium_night.png', at: M('box'), cam: hold(960, 610, 1.08) },
        // 2.4 the tabs close (locked); 2.5 on the bell, Barnaby's window opens on the desktop, his mark ringing
        { src: 'live/shop', at: ct(), cam: [960, 540, 1], state: t => shopState(t),
          build: l => { bellWin = el('div', {}, l); css(bellWin, { position: 'absolute', display: 'none', background: '#14110E' });
            bellMark = el('div', { html: markSVG('#D3A14A') }, bellWin); css(bellMark, { position: 'absolute', width: '150px', height: '150px' }); },
          over: t => {
            if (!BW || t < M('bell_arrive') - .05) { bellWin.style.display = 'none'; return; }
            const k = easeOutCubic(clamp((t - M('bell_arrive') + .05) / .35));
            css(bellWin, { display: 'block', left: BW[0] + 'px', top: BW[1] + 'px', width: BW[2] + 'px', height: BW[3] + 'px', opacity: k.toFixed(3) });
            css(bellMark, { left: (BW[2] / 2 - 75) + 'px', top: (BW[3] / 2 - 95) + 'px' });
            markAnim(bellMark, t, sfxT('bell', M('bell_arrive')));
          } },
        // 2.6 Theo's hologram (held): the scan, the six; 2.7 the same, modest, on the 2009 PC (locked)
        { src: 'comp/theo-handover-1-reading', at: M('reading'), cam: [960, 540, 1],
          state: t => ({ scan: +lerp(-.6, 20.6, easeInOutSine(clamp((t - sweepA) / (sweepB - sweepA)))).toFixed(3),
            heardK: +clamp((t - V(5)) / (VE(5) - V(5) - .1)).toFixed(3) }) },
        { src: 'comp/theo-handover-2-taken', at: M('six_lit'), cam: [960, 540, 1],
          state: t => ({ lit: +clamp((t - SIX) / .26, 0, 6).toFixed(3), counts: +clamp((t - SIX - 1.6) / .4).toFixed(3),
            sayK: +clamp((t - V(6)) / (VE(6) - V(6) - .1)).toFixed(3) }) },
        { src: 'comp/theo-handover-pc', at: M('old_pc'), cam: [960, 540, 1],
          state: t => ({ lit: +clamp((t - M('old_pc') - .2) / .16, 0, 6).toFixed(3), sayK: +clamp((t - V(6)) / (VE(6) - V(6) - .1)).toFixed(3) }) },
        // 2.8 back to the room: the desk at night for "It's Theo..." / "Noted."; 2.9 the key (Blender's s2_key_lamp)
        { src: 'world/02_medium_night.png', at: M('desk_detail'), cam: hold(960, 620, 1.1) },
        { src: 'world/03_keys_night.png', at: M('key'), cam: move(M('key') + .2, 1.6, [760, 700, 1.1], [700, 800, 1.3], 0),
          grade: t => `brightness(${lerp(1, .16, easeOutCubic(P(t, M('lamp_off'), .15))).toFixed(3)})` },
      ], E);""")
sub('scenes/s2.js', """  let run, shop, X = null;""", """  let run, shop, X = null, BW = null, bellWin, bellMark;""")
sub('scenes/s2.js', """    if (n === 0) Object.assign(st, { browser: false, tabs: [] });""",
"""    if (n === 0) Object.assign(st, { browser: false, tabs: [], barnaby: t >= M('bell_arrive') - .05 ? 'frame' : 'off' });""")
sub('scenes/s2.js', """        X[n] = [(r.left + r.width * .45) / 1.5, (r.top + r.height * .5) / 1.5];
      }""", """        X[n] = [(r.left + r.width * .45) / 1.5, (r.top + r.height * .5) / 1.5];
      }
      // Barnaby's window on the night desktop: its client area (1920x1080 px), where his bell rings
      pc.render(pc.preset('desktop', { date: '2026-11-19', time: '21:47', barnaby: 'frame', cursor: null }));
      const c = d.querySelector('#barnaby-client').getBoundingClientRect();
      BW = [c.left, c.top, c.width, c.height];""")

# ---- 3 · Monday: the time-lapse, the push into the screen, the plan (whole shop, one reframe), the drawer
block('scenes/s3.js', """      run = seq(root, [
        { src: 'world/02_medium_night.png', at: S, cam: [960, 600, 1.12], grade: 'brightness(.16)' },
        { src: 'world/04_medium_monday.png', at: S + .35, fi: 1.5, keepFi: true, cam: hold(960, 600, 1.12, -.01),
          grade: t => `brightness(${lerp(1.35, 1, easeInOutSine(P(t, S + .6, 1.6))).toFixed(3)})` },
        // 3.3 into the screen (the push, from the end of s3_timelapse): Theo's Back Office, full frame, locked, the
        // clock gadget readable as the taskbar turns 08:51 -> 08:52
        { src: 'live/shop', at: M('clock'), fi: .12, pin: { shot: 's3_timelapse', d: .6 }, cam: [960, 540, 1],
          state: t => ({ preset: 'shop-jobs', time: t < flip ? '08:51' : '08:52', secs: (58 + Math.floor(t - flip + 2)) % 60 }) },
        // 3.4 Martin's plan, the whole shop held; Barnaby walks inside it; the one reframe, to the back-office wing,
        // as he reaches drawer 1 and the pads note drops on
        { src: 'comp/martin-key', at: M('martin_world'),
          cam: move(M('pads_callout') - .15, 1.4, [690, 545, 1.48], [620, 310, 2.0], 0),
          state: t => ({ walk: +walkAt(t).toFixed(4), pads: +clamp((t - M('pads_callout')) / .55).toFixed(3), ask: 0, card: 0, say: 0, martin: 0, time: '08:54' }),
          build: l => {
            // Barnaby listening at the job board while Martin asks: his ring breathes (a brass ring, his colour)
            ring = el('div', {}, l); css(ring, { width: '0px', height: '0px', borderRadius: '50%', border: '3px solid #E2B54E', display: 'none' });
          },
          over: t => {
            const p = [90 + 7.3 * 60, 286 + 8.05 * 60];
            const u = ((t - M('martin_world') - .6) / 1.4) % 1, on = t > M('martin_world') + .6 && t < M('walk');
            if (!on || u < 0) { ring.style.display = 'none'; return; }
            const r = lerp(32, 60, easeOutCubic(u));
            css(ring, { display: 'block', left: (p[0] - r).toFixed(1) + 'px', top: (p[1] - r).toFixed(1) + 'px', width: 2 * r + 'px', height: 2 * r + 'px', opacity: (.8 * (1 - u)).toFixed(3) });
          } },
        { src: 'world/x_shelf_monday.png', at: M('shelf'), cam: hold(680, 400, 1.18) },
      ], E);""")
sub('scenes/s3.js', """      mk = run.list[4].s;""", """      mk = run.list[3].s;""")

# ---- 5 · the passage forms under a slow push; Blender's afternoon keeps the AFT grade (its notes)
sub('scenes/s5.js', """        { src: 'world/04_medium_monday.png', at: S, grade: AFT, cam: hold(960, 600, 1.1) },""",
"""        { src: 'world/04_medium_monday.png', at: S, grade: AFT, keepGrade: true, cam: hold(960, 600, 1.1) },""")
sub('scenes/s5.js', """        planItem({ at: M('walk1'), cam: [620, 540, 1.62] }),""",
"""        planItem({ at: M('walk1'), cam: move(M('passage') + .05, 2.2, [620, 540, 1.62], [600, 525, 1.8], 0) }),   // 5.4 the slow push as it forms""")

# ---- 6 · dusk
block('scenes/s6.js', """      run = seq(root, [
        // 6.1 dusk: the room deep blue, then the lamp comes on (Blender's s6_lamp_on / 06_medium_dusk when they land;
        // until then the Monday desk in the late grade, its light stepping up on the lamp's click)
        { src: DUSK, at: S, cam: hold(960, 610, 1.08), keepGrade: true,
          grade: t => DUSK === MON ? `${LATE} brightness(${lerp(.62, 1, easeOutCubic(P(t, M('lamp_on'), .12))).toFixed(3)})` : '' },
        // 6.2 the sticky note, in Theo's hand; 6.3 Reports (coming soon!!), locked and held for the joke
        { src: STICKY, at: M('sticky'), grade: STICKY === MON ? LATE : '', cam: STICKY === MON ? hold(948, 766, 3.1, .006) : hold(960, 540, 1.0) },
        { src: 'live/shop', at: M('soon_tab'), cam: [960, 540, 1],
          state: t => {
            const b = Math.max(M('soon_tab') + 1.4, V(29) + 4), c = path2(t, [[b - .9, 700, 470], [b - .1, 578, 258], [b + 3, 582, 261]]);   // Martin's hand to the tab
            return { preset: 'shop-reports-soon', marquee: +(((t - M('soon_tab')) * 60) % 2000).toFixed(1), secs: Math.floor(t - M('soon_tab')) + 14,
              cursor: { x: +(c[0] + wiggle(t, 31, 2, 1.2)).toFixed(2), y: +(c[1] + wiggle(t, 32, 1.7, 1)).toFixed(2) } };
          } },
        // 6.4 back to the dusk desk: "I could write it" / "You can do that?" / "With your say-so"
        { src: DUSK, at: V(30), grade: DUSK === MON ? LATE : '', cam: hold(960, 610, 1.08) },
        // 6.5 the change, written and checked (locked)
        { src: 'comp/same-butler', at: M('code'), cam: [314, 690, 3.0],
          state: t => ({ files: +clamp(3 * (t - filesA) / (filesB - filesA), 0, 3).toFixed(3), tests: +(22 * clamp((t - M('checks')) / (testsB - M('checks')))).toFixed(2) - (t < M('checks') ? 1 : 0),
            added: 0, rediscover: 0 }) },
        // 6.6 Martin's plan with the explanation card; mid-line, his reading glasses on the dusk desk; back to the card
        cardItem(V(33)),
        { src: GLASSES, at: M('glasses'), grade: GLASSES === MON ? LATE : '', cam: GLASSES === MON ? hold(640, 865, 2.05) : hold(960, 540, 1.0) },
        cardItem(M('glasses') + 2.4),
        // 6.8 the reload, the tab turns Reports (locked); 6.9 the scene's one move: the Workload room appears
        { src: 'live/shop', at: M('reload'), cam: [960, 540, 1],
          state: t => t < M('tab_change')
            ? { preset: 'shop-reports-soon', time: '16:16', loading: +lerp(.08, .96, easeInOutSine(clamp((t - M('reload')) / (M('tab_change') - M('reload'))))).toFixed(3), secs: 2 }
            : { preset: 'shop-reports', loading: +(t < M('tab_change') + .15 ? 1 : 0), secs: 3 + Math.floor(t - M('tab_change')) } },
        { src: 'comp/martin-build', at: M('new_room'), cam: move(M('new_room') + .05, 1.15, [700, 560, 1.32], [760, 420, 1.62], 0),
          state: t => ({ room: +easeInOutSine(clamp((t - M('new_room') - .1) / .6)).toFixed(3),
            sticker: +easeOutBack(clamp((t - M('new_room') - .75) / .35), 2.6).toFixed(3), side: 'build' }) },
        // 6.10 the same event in all three worlds, held through Dev's line and "Good idea."
        { src: 'comp/same-butler', at: M('same_butler'), cam: [960, 540, 1],
          build: l => { rv.sb = reveal(l, SB, [[722, 986, 1170, 1015], [722, 1020, 801, 1046]], { color: '#F5F2EA', a: V(37), b: V(37) + n37 * 51 / 115 }); },
          over: t => rv.sb.render(t) },
        // 6.11 the jobs page: Dev -> Priya (locked, held)
        { src: 'live/shop', at: M('reassign') - .1, cam: [960, 540, 1],
          state: t => ({ preset: 'shop-jobs-after', reassign: +clamp((t - M('reassign') - .25) / 1.3).toFixed(3), secs: 5 + Math.floor(t - M('reassign')) }) },
      ], E);""")
sub('scenes/s6.js', """      const cardAt = M('glasses') + 3.2, cb = sfxT('mouse_click', M('click_build'));""",
"""      const cb = sfxT('mouse_click', M('click_build')), cardAt = V(33);
      const MON = 'world/04_medium_monday.png', DUSK = pick('world/06_medium_dusk.png', MON), STICKY = pick('world/x_sticky_dusk.png', MON), GLASSES = pick('world/x_glasses_dusk.png', MON);
      const cardItem = at => ({ src: 'comp/martin-build', at, cam: [960, 540, 1],
          state: t => ({ room: 0, side: 'card', time: '16:16', foot: '', martinSay: t >= V(36) ? 'Fussy.' : t >= V(34) ? 'Add it.' : 'You can do that?', card: +clamp((t - cardAt - .3) / .6).toFixed(3), marker: [11.62, 2.45], passage: 1,
            press: [+pressAt(t, cb).toFixed(3), 0] }),
          build: l => { const cur = cursor(l, 1.5); (rv.curs = rv.curs || []).push(cur); },
          over: (t, l) => {
            const cur = rv.curs[at === cardAt ? 0 : 1], from = Math.min(V(35) + 1.2, cb - 1.3);
            if (!AddIt || t < from) { cur.at(0, 0, false); return; }
            const c = hand(t, [from, AddIt[0] - 260, AddIt[1] + 230], [{ t: cb, x: AddIt[0], y: AddIt[1] }]);
            cur.at(c[0], c[1], true);
          } });""")
sub('scenes/s6.js', """      cardPlan = run.list[6].s;""", """      cardPlan = run.list[7].s;""")

# ---- 7 · Priya: the desk, the bench held with one reframe to the note, the desk for "Noted."
block('scenes/s7.js', """      run = seq(root, [
        { src: 'world/05_medium_tuesday.png', at: S, cam: hold(960, 600, 1.12) },
        { src: 'comp/priya-tuesday', at: M('priya_world'), state: st, cam: move(M('readme_note') - .1, 1.3, [960, 540, 1], [1600, 560, 1.75], 0) },
        { src: 'world/05_medium_tuesday.png', at: V(43), cam: hold(1150, 600, 1.2) },
      ], E);""")

# ---- 8 · Lisbon: the approach (Blender), the cup, the push into the main monitor, the real app, the log, his world,
# the render box, the desk for "Show-off."
block('scenes/s8.js', """      run = seq(root, [
        { src: 'world/lisbon_01_wide_day.png', at: S, cam: move(S + .4, M('nata') - S - .6, [970, 540, 1.0], [1000, 560, 1.12], 0) },
        { src: 'world/x_lisbon_detail_day.png', at: M('nata'), cam: hold(880, 580, 1.06) },
        { src: 'live/lis-main-empty', at: M('realapp'), fi: .12, pin: { shot: 's8_lisbon_day', d: .6 }, cam: [960, 540, 1],
          state: t => ({ preset: 'realapp', app: +easeOutCubic(clamp((t - M('realapp') - .05) / .6)).toFixed(4), secs: 40 + Math.floor(t - M('realapp')) }) },
        { src: 'rapp/base.jpg', at: M('realapp_full'), cam: [712, 560, 1],
          build: l => {
            forms = [];
            for (let i = 0; i <= 54; i++) {
              const im = el('img', { attrs: { src: `assets/realapp/f_${String(i).padStart(3, '0')}.jpg`, decoding: 'sync' } }, l);
              css(im, { position: 'absolute', left: FORM.x + 'px', top: FORM.y + 'px', width: FORM.w + 'px', height: FORM.h + 'px', display: 'none' });
              forms.push(im);
            }
            fcur = cursor(l, 1.6);
          },
          over: t => {
            const k = stepOf(t);
            forms.forEach((im, i) => { const on = i === k; if ((im.style.display !== 'none') !== on) im.style.display = on ? 'block' : 'none'; });
            // Theo's pointer: off the form while he types, then to Connect at human speed, the press on its click
            const from = Math.max(stepAt[51] + .05, PRESS() - 1.15);
            if (t < from) { fcur.at(0, 0, false); return; }
            const c = hand(t, [from, BTN[0] + 330, BTN[1] + 150], [{ t: PRESS(), x: BTN[0] + 6, y: BTN[1] + 4 }]);
            fcur.at(c[0], c[1], true);
          } },
        { src: 'live/lis-main', at: M('synapse_log') - .1, cam: [600, 700, 1.6],               // Barnaby's log pane, held
          state: t => ({ preset: 'quorum', time: '09:40', secs: 2 + Math.floor((t - M('synapse_log')) * 2), out: Math.floor(lerp(0, 10.99, clamp((t - M('synapse_log')) / 1.6))),
            say: '', sayK: 0, plan: '', mode: 'thinking', level: 0, notify: 0 }) },
        { src: TL, at: M('theo_world'), cam: [960, 540, 1],
          build: l => { rv = reveal(l, TL, [[1466, 884, 1840, 912], [1467, 922, 1846, 950], [1467, 959, 1604, 987]], { color: '#14110E', a: V(45), b: VE(45) - .1, chars: [30, 33, 11] }); },
          over: t => rv.render(t) },
        { src: 'live/lis-studio', at: V(48), cam: [960, 540, 1],
          state: t => ({ preset: 'comfy', queueOpen: +easeInOutCubic(clamp((t - qOpen + .45) / .55)).toFixed(4), queueHl: +clamp((t - qOpen - .2) / .4).toFixed(3),
            step: Math.min(28, 9 + Math.floor((t - V(48)) * 2)), frame: 123 + 2 * Math.floor((t - V(48)) * 6), secs: 3 + Math.floor(t - V(48)) }) },
        { src: 'world/lisbon_02_medium_day.png', at: V(50), cam: hold(970, 560, 1.12) },
      ], E);""")
# the typing: "quorum" typed, the repo path PASTED (Ctrl+V), the URL typed, at about 8 a second, from the `typing` mark
sub('scenes/s8.js', """    const gap = (k, i) => k === 'click' ? 0 : k === 'tab' ? .34 + .1 * rand(i, 91) : (1 / 7) * (.65 + .7 * rand(i, 92)) + (rand(i, 93) < .08 ? .18 : 0);
    const t0 = Math.max(M('realapp_full') + .45, sfxT('keys_modern', M('realapp_full')) - .05), t1 = PRESS() - 1.25;""",
"""    const repo = i => i >= 8 && i <= 29;                         // the repo path's 22 keys arrive at once: pasted
    const gap = (k, i) => k === 'click' ? 0 : k === 'tab' ? .34 + .1 * rand(i, 91) : repo(i) ? (i === 8 ? .42 : 0) : (1 / 8) * (.65 + .7 * rand(i, 92)) + (rand(i, 93) < .08 ? .16 : 0);
    const t0 = CUES.marks.typing != null ? M('typing') : Math.max(M('realapp_full') + .45, sfxT('keys_modern', M('realapp_full')) - .05), t1 = PRESS() - 1.25;""")
sub('scenes/s8.js', """  // Theo types at about 7 characters a second, unevenly, a Tab between fields (the form shows the same focus as a
  // click); from the typing sound on the cue sheet (keys_modern) or just after the app comes up, done in time for
  // the hand to reach Connect at human speed (0.9 s) and press on the click sound. With less room it types faster.""",
"""  // From the `typing` mark Theo types "quorum" at about 8 characters a second, unevenly, Tab, pastes the repo path
  // (Ctrl+V), Tab, types the URL, in time for the hand to reach Connect at human speed and press on the click sound.
  // With less room than that it types faster (window.__typingFit < 1).""")
sub('scenes/s8.js', """      const qOpen = V(49) + 2.9;""", """      const qOpen = M('queue') - .3;""")

# ---- 9 · goodnight: dissolves; Lisbon's monitors dim by the "on" -> "asleep" stills when they land
block('scenes/s9.js', """      const ASLEEP = pick('world/lisbon_03_medium_night_asleep.png', 'world/lisbon_03_asleep_night.png', 'world/lisbon_03_night_asleep.png', '');
      run = seq(root, [
        { src: 'world/x_close_night.png', at: S, cam: hold(940, 570, 1.08) },
        { src: 'world/lisbon_03_medium_night.png', at: M('lisbon_night'), fi: .9, cam: hold(1010, 525, 1.06),
          build: l => {
            dimmer = el('div', {}, l);       // everything but Barnaby's slot sinks: the two monitors dim to one small glow
            css(dimmer, { left: '0px', top: '0px', width: '1920px', height: '1080px', background: 'radial-gradient(circle at 1148px 480px, rgba(0,0,0,0) 0px, rgba(0,0,0,0) 60px, rgba(0,0,0,.72) 260px)' });
          },
          over: t => { dimmer.style.opacity = ASLEEP ? '0' : easeInOutSine(P(t, M('dim'), 1.6)).toFixed(3); } },
      ].concat(ASLEEP ? [{ src: ASLEEP, at: M('dim'), fi: 1.6, cam: hold(1010, 525, 1.06) }] : []).concat([
        // the last move: the two desks, closing gently as the bell rings and the titles come up
        { src: 'world/close_two_desks.png', at: M('two_desks'), fi: .9, cam: [[M('two_desks'), 960, 540, 1.0], [E, 960, 560, 1.04]] },
      ]), E, { dissolves: true });""")
print('scenes patched')
