"""The v2.1 animatic's timing: every voice line, sound effect, music section and picture mark, laid out from the
real rendered voice durations. Writes video/v2/cues.json (the cue sheet) and video/v2/animatic/cues.js (the same
data for the animatic page).

  runtime/voice/.venv/Scripts/python video/v2/audio/layout.py

How lines are placed: each line's *speech* (first to last 10 ms frame above -40 dB, as SPEECH.md measures) starts a
gap after the previous line's speech ends, so the gaps below are the silences you hear. Gaps follow SPEECH.md:
speaker changes ~200-500 ms (SPK 0.30 s; QUICK 0.22 s for a snap answer like "Yes." after "Shall I?"); a beat or an
action between lines is written out explicitly. Nothing overlaps (checked at the end).

Edit the beat sheet in build() and re-run; then re-run voices.py (cached) to refresh the manifest's t values:
  runtime/voice/.venv/Scripts/python video/audio/voices.py --cues video/v2/cues.json --out video/v2/audio/voice --only none
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
ROOT = V2.parents[1]
sys.path.insert(0, str(V2))
from speech_probe import active_span, load  # noqa: E402

CUES = V2 / "cues.json"
MANIFEST = HERE / "voice" / "manifest.json"
PAGE_CUES = V2 / "animatic" / "cues.js"

SPK, QUICK, SAME = 0.30, 0.22, 0.45

SCRIPT_TIMES = {1: (0, 12), 2: (12, 40), 3: (40, 56), 4: (56, 73), 5: (73, 95), 6: (95, 128), 7: (128, 144),
                8: (144, 165), 9: (165, 180)}
TITLES = {1: "Nine tabs", 2: "The handover", 3: "Monday", 4: "A key", 5: "The same four steps",
          6: "A room Theo never built", 7: "Priya, day one", 8: "Any house", 9: "Goodnight"}
WHERE = {1: "Shop, Thu 19 Nov 21:47", 2: "Shop, Thu 19 Nov night", 3: "Shop, Mon 23 Nov 08:52", 4: "Shop, Mon 23 Nov",
         5: "Shop, Mon 23 Nov afternoon", 6: "Shop, Mon 23 Nov 16:08-16:21", 7: "Shop, Tue 24 Nov 08:34",
         8: "Lisbon, Tue 24 Nov 09:39", 9: "Shop 18:40 / Lisbon 20:07, Tue 24 Nov"}


class Timeline:
    def __init__(self, lines: list[dict], spans: list[tuple[float, float, float]]):
        self.lines, self.spans = lines, spans          # spans[i] = (speech onset, speech end, file length)
        self.t: dict[int, float] = {}                   # line number (1-based) -> file start time
        self.last = 0
        self.marks: dict[str, float] = {}
        self.sfx: list[dict] = []
        self.music: list[dict] = []
        self.scenes: list[dict] = []

    # -- voice --
    def on(self, n: int) -> float:
        return self.t[n] + self.spans[n - 1][0]

    def off(self, n: int) -> float:
        return self.t[n] + self.spans[n - 1][1]

    def line(self, n: int, at: float | None = None, gap: float = SPK, after: int | None = None) -> float:
        """Place line n so its speech starts at `at`, or `gap` after the speech of line `after` (default: the
        previously placed line) ends. Returns the speech onset."""
        onset = at if at is not None else self.off(after or self.last) + gap
        self.t[n] = round(onset - self.spans[n - 1][0], 3)
        self.last = n
        return onset

    # -- everything else --
    def mark(self, name: str, t: float) -> float:
        self.marks[name] = round(t, 3)
        return t

    def fx(self, typ: str, t: float, **kw) -> float:
        self.sfx.append({"t": round(t, 3), "type": typ, **{k: (round(v, 3) if isinstance(v, float) else v)
                                                          for k, v in kw.items()}})
        return t

    def section(self, name: str, t: float, mood: str) -> None:
        self.music.append({"t": round(t, 3), "section": name, "mood": mood})

    def scene(self, n: int, start: float) -> None:
        if self.scenes:
            self.scenes[-1]["end"] = round(start, 3)
        self.scenes.append({"id": n, "title": TITLES[n], "where": WHERE[n], "start": round(start, 3), "end": None,
                            "script": list(SCRIPT_TIMES[n])})


def build(T: Timeline) -> float:
    m, fx, L, on, off = T.mark, T.fx, T.line, T.on, T.off

    # ── 1 · Nine tabs (Thu 19 Nov, 21:47) ─────────────────────────────────────────────────────────────────────────
    T.scene(1, 0.0)
    fx("rain", 0.0, fade_in=2.2, level=1.0, label="rain on the window (bed)")
    fx("fan", 0.35, level=1.0, label="PC fan spins up, then hums (bed)")
    fx("hdd", 0.9, dur=1.6, label="hard drive chatter")
    fx("radio", 0.2, level=.55, label="a radio far off in the workshop (bed)")
    m("light_up", 0.7)                                     # light comes up on the wide
    m("medium", 2.9)                                       # cut to the medium, drifting to the monitor
    m("screen", 4.1)                                       # full-screen: the shop PC
    for i in range(9):                                     # nine tabs, one after another, the needle climbing
        t = m(f"tab{i + 1}", 4.35 + i * 0.34)
        fx("tab", t, pan=-.35 + .08 * i)
        if i in (2, 5, 7):
            fx("hdd", t + .05, dur=.5)
    L(1, at=m("martin_os", 5.2))                           # (o.s., from the workshop, tired)
    L(2, gap=SPK)                                          # "Tab four. No — five."
    m("tab4_active", on(2) + .05)
    fx("tab", on(2) + .12, pan=-.1)
    m("tab5_active", on(2) + .78)
    fx("tab", on(2) + .84, pan=-.05)
    L(3, gap=.55)                                          # (beat) "It's the one with the spanner."
    m("spanner", on(3))

    # ── 2 · The handover (night, cont'd) ──────────────────────────────────────────────────────────────────────────
    s2 = off(3) + .45
    T.scene(2, s2)
    m("photo", s2)                                         # the 2009 photo
    m("calendar", s2 + 1.25)                               # Friday circled
    m("box", s2 + 2.45)                                    # the moving box
    L(4, at=s2 + 2.75)                                     # "Seventeen years." (quietly)
    m("close_tabs", off(4) + .35)                          # he closes the tabs, one by one
    for i in range(9):
        fx("tab_close", T.marks["close_tabs"] + .25 + i * .2, pan=.3 - .07 * i)
    m("desktop_night", T.marks["close_tabs"] + .25 + 9 * .2)
    bell = fx("bell", m("bell_arrive", T.marks["desktop_night"] + .35), gain=.5, label="the brass bell: Barnaby arrives")
    T.section("handover", bell + .15, "sparse, warm acoustic guitar enters after the bell")
    L(5, at=bell + 1.05)                                   # "Right. Barnaby — this is the shop's system..."
    m("reading", on(5) + .15)                              # Theo's view: Synapse reading his code
    m("six_lit", off(5) - .2)                              # 23 endpoints; six light up
    fx("pop", T.marks["six_lit"] + .1, gain=.18, label="six light up")
    L(6, gap=SPK)                                          # Barnaby: "Twenty-three endpoints, sir..."
    m("old_pc", on(6) + 3.2)                               # the whole 2009 desktop: modest on old hardware
    L(7, gap=SPK)                                          # Theo: "It's Theo. And don't call my uncle sir..."
    m("desk_detail", on(7) - .2)
    L(8, gap=SPK)                                          # Barnaby: "Noted."
    m("key", off(8) + .25)                                 # the key slides off his ring onto the keyboard
    fx("key_tap", T.marks["key"] + .55, gain=.6, label="the key on the keyboard: a small clean metal tap")
    fx("lamp_click", m("lamp_off", T.marks["key"] + 1.75), gain=.55, label="the lamp clicks off")
    s3 = T.marks["lamp_off"] + .55

    # ── 3 · Monday (Mon 23 Nov, 08:52) ────────────────────────────────────────────────────────────────────────────
    T.scene(3, s3)
    m("timelapse", s3)                                     # daylight sweeps across the desk; Theo's things gone
    fx("timelapse", s3, dur=2.2, gain=.35, label="time passes: a soft swell")
    fx("workshop", s3 + 1.4, level=1.0, label="workshop morning bed: room, radio, tools")
    fx("freewheel", s3 + 3.0, gain=.3)
    m("monday", s3 + 1.4)                                  # the Monday desk: mug, glasses, rag, job card
    m("clock", s3 + 2.6)                                   # the screen clock: 08:52
    T.section("work", s3 + 2.0, "light, walking pace")
    L(9, at=s3 + 3.1)                                      # Martin (sitting, a sigh): "Right. Barnaby, is it?"
    L(10, gap=SPK)                                         # "Good morning, Martin."
    m("martin_world", on(10) - .1)
    L(11, gap=SPK)                                         # "What's due tomorrow — and are we short on anything?"
    m("walk", off(11) + .05)                               # Barnaby walks the workshop floor, then the drawer
    fx("compressor", off(11) - 1.2, gain=.22)
    L(12, gap=.55)                                         # "Five bikes due tomorrow. Only Anika's is a problem..."
    m("pads_callout", on(12) + 2.6)
    m("shelf", off(12) - 1.9)                              # the parts box: one pair of pads inside
    s4 = off(12) + .45

    # ── 4 · A key (Mon, 08:55-09:04) ──────────────────────────────────────────────────────────────────────────────
    T.scene(4, s4)
    L(13, at=s4 + .3)                                      # "Order ten from Madison, then."
    L(14, gap=SPK)                                         # "I can't order parts myself yet..."
    m("card", on(14) + 2.2)                                # the card: Let Barnaby order parts...
    L(15, gap=SPK)                                         # "Go on, then."
    m("click_unlock", off(15) + .3)
    fx("mouse_click", T.marks["click_unlock"] + .12, gain=.6)
    fx("key_turn", m("unlock", T.marks["click_unlock"] + .55), gain=.65, label="a real key turning in a lock")
    fx("bell_soft", T.marks["unlock"] + .75, gain=.32, label="the bell's soft confirm")
    m("engine_unlock", T.marks["unlock"] + .5)
    L(16, at=T.marks["unlock"] + 1.25)                     # "Ten pairs from Madison, at six pounds fifty a pair. Shall I?"
    L(17, gap=QUICK)                                       # "Yes."
    fx("mouse_click", m("click_order", off(17) + .12), gain=.55)
    m("po", T.marks["click_order"] + .15)                  # Purchase Orders: order 3 slides in
    fx("pop", T.marks["po"] + .55, gain=.2, label="order 3 lands")
    s5 = T.marks["po"] + 2.0

    # ── 5 · The same four steps (Mon afternoon) ──────────────────────────────────────────────────────────────────
    T.scene(5, s5)
    m("afternoon", s5)                                     # light slides across the desk
    fx("clunk", m("clunk1", s5 + .35), gain=.55, label="repair stand clamp releases: Sofia's")
    L(18, at=s5 + .8)                                      # "Barnaby — Sofia's bike's done."
    L(19, gap=SPK)                                         # "I'll need to text her and mark it ready. May I?"
    m("cards2", on(19) + 1.2)                              # two quick cards
    L(20, gap=QUICK)                                       # "Go on." (clicking both)
    fx("mouse_click", m("click_text", on(20) + .05), gain=.5)
    fx("mouse_click", m("click_ready", on(20) + .45), gain=.5)
    m("walk1", off(20) + .1)                               # Barnaby walks four rooms
    for k in range(4):
        fx("step", T.marks["walk1"] + .15 + k * .38, gain=.16)
    fx("clunk", m("clunk2", T.marks["walk1"] + 1.75), gain=.5, label="Kwame's")
    L(21, at=T.marks["clunk2"] + .3)                       # "Kwame's."
    m("walk2", off(21) + .05)
    for k in range(4):
        fx("step", T.marks["walk2"] + .1 + k * .2, gain=.15)
    fx("clunk", m("clunk3", T.marks["walk2"] + .95), gain=.5, label="Jana's")
    L(22, at=T.marks["clunk3"] + .28)                      # "And Jana's."
    m("walk3", off(22) + .02)
    L(23, gap=SPK)                                         # "That's three bikes handed back..."
    L(24, gap=QUICK)                                       # "Can you?"
    L(25, gap=SPK)                                         # "Give me a moment."
    m("passage", off(25) + .2)                             # a passage opens through the four rooms
    fx("bell_soft", T.marks["passage"] + .35, gain=.28, label="the passage opens")
    m("engine_compose", T.marks["passage"] + .6)
    fx("clunk", m("clunk4", T.marks["passage"] + 1.25), gain=.5, label="Tom's Brompton")
    L(26, at=T.marks["clunk4"] + .3)                       # "Tom's Brompton."
    m("walk4", off(26) + .05)                              # one step
    L(27, gap=SPK)                                         # "Tom's been texted, and it's marked ready."
    s6 = off(27) + .5

    # ── 6 · A room Theo never built (Mon 16:08-16:21) ────────────────────────────────────────────────────────────
    T.scene(6, s6)
    m("late", s6)
    L(28, at=s6 + .35)                                     # "Who's got too much on this week?"
    T.section("before_build", s6, "quieter, the walking figure thins out under the question")
    L(29, gap=SPK)                                         # "The system can't tell me — there's no report for it..."
    m("sticky", on(29) + .3)                               # the sticky note on the bezel
    m("soon_tab", on(29) + 3.0)                            # Reports (coming soon!!)
    L(30, gap=SAME)                                        # "I could write it, if you like."
    L(31, gap=SPK)                                         # "You can do that?"
    L(32, gap=SPK)                                         # "With your say-so. I'll work on a copy..."
    m("code", off(32) - 1.2)                               # code, written line by line
    fx("typing", T.marks["code"], dur=4.2, gain=.55, label="keyboard foley under the code")
    T.section("build", T.marks["code"], "rising, focused: builds to the click")
    m("checks", T.marks["code"] + 3.4)                     # a row of checks turns green
    fx("ding", T.marks["checks"], gain=.25, label="checks pass")
    L(33, at=T.marks["code"] + 4.3)                        # "Done. It adds up each mechanic's hours..."
    m("glasses", on(33) + 4.0)
    L(34, gap=SPK)                                         # "Add it."
    L(35, gap=SPK)                                         # "That one needs your click, Martin..."
    L(36, gap=SPK)                                         # "Fussy." (clicking)
    fx("mouse_click", m("click_build", on(36) + .3), gain=.62)
    m("reload", T.marks["click_build"] + .3)               # Theo's system reloads
    fx("reload", T.marks["reload"], gain=.25, label="the page reloads")
    m("tab_change", T.marks["reload"] + .8)                # "Reports (coming soon!!)" -> "Reports"
    T.section("lift", T.marks["tab_change"], "release on the click and the tab change")
    m("new_room", T.marks["tab_change"] + 1.35)            # on the plan: Workload
    fx("bell_soft", T.marks["new_room"] + .1, gain=.3, label="a new room")
    L(37, at=T.marks["new_room"] + .9)                     # "Dev's carrying thirty-one hours against his twenty..."
    m("same_butler", on(37) + .4)                          # three worlds, one event
    L(38, gap=SPK)                                         # "Good idea."
    m("reassign", off(38) + .2)                            # Dev -> Priya
    fx("pop", T.marks["reassign"] + .5, gain=.18, label="two rows change")
    s7 = T.marks["reassign"] + 2.0

    # ── 7 · Priya, day one (Tue 24 Nov, 08:34) ───────────────────────────────────────────────────────────────────
    T.scene(7, s7)
    fx("bustle", s7, level=1.0, label="Tuesday workshop bustle (bed)")
    T.section("tuesday", s7, "settles: soft picking")
    L(39, at=s7 + 1.3)                                     # "So you're why I've got two wheel builds on my first day?"
    L(40, gap=SPK)                                         # "Guilty. Dev had thirty-one hours booked. You had none."
    m("priya_world", on(40) - .1)
    L(41, gap=SPK)                                         # "Fair. What else can this thing do?"
    L(42, gap=SPK)                                         # "Your jobs, the parts they need, who's collecting what..."
    m("readme_note", on(42) + 4.4)                         # never trust the stock count on a Friday
    L(43, gap=SPK)                                         # "Noted." (a small laugh)
    s8 = off(43) + .6

    # ── 8 · Any house (Lisbon, Tue 24 Nov 09:39) ─────────────────────────────────────────────────────────────────
    T.scene(8, s8)
    fx("street", s8, level=1.0, label="Lisbon: street below the window (bed)")
    T.section("lisbon", s8, "brighter, fuller: the new desk")
    m("lisbon_wide", s8)
    m("nata", s8 + 1.5)
    m("realapp", s8 + 2.7)                                 # the real Barnaby app in a browser tile
    m("realapp_full", s8 + 3.6)
    fx("keys_modern", s8 + 3.7, dur=1.0, gain=.4, label="Theo types")
    fx("mouse_click", m("connect", s8 + 5.0), gain=.5, label="Connect")
    L(44, at=T.marks["connect"] + .3)                      # "Barnaby — new job. This is the crew's memory."
    m("synapse_log", on(44) + .9)                          # Synapse reads it in seconds
    m("theo_world", off(44) + .1)
    L(45, gap=SPK)                                         # "Thirteen endpoints, sir — and two deadlines in dispute..."
    L(46, gap=SPK)                                         # "Still Theo."
    m("still_theo", on(46) - .1)
    L(47, gap=SPK)                                         # "Theo."
    L(48, gap=SPK)                                         # "And the render box?" (nodding at the second monitor)
    m("render_box", on(48) - .15)
    L(49, gap=SPK)                                         # "Twenty-eight endpoints. It's on the big card..."
    m("queue", on(49) + 1.6)
    L(50, gap=SPK)                                         # "Show-off."
    s9 = off(50) + .75

    # ── 9 · Goodnight (shop 18:40, Lisbon 20:07) ─────────────────────────────────────────────────────────────────
    T.scene(9, s9)
    m("shop_night", s9)
    fx("rain", s9, fade_in=1.2, level=.8, label="rain returns over the shop (bed)")
    T.section("close", s9, "resolve: a held chord, the bell, a last roll")
    L(51, at=s9 + .9)                                      # Martin (o.s., coat on, keys): "Night, Barnaby."
    fx("keys_jingle", on(51) - .5, gain=.3, label="Martin's keys")
    L(52, gap=SPK)                                         # "Goodnight, Martin."
    m("lisbon_night", off(52) + .3)
    fx("street_night", T.marks["lisbon_night"], level=1.0, label="a quieter street outside in Lisbon (bed)")
    m("dim", T.marks["lisbon_night"] + .5)
    L(53, at=T.marks["lisbon_night"] + .9)                 # Theo (o.s., leaving): "Night, Barnaby."
    L(54, gap=SPK)                                         # "Goodnight, Theo."
    m("two_desks", off(54) + .45)
    fx("bell", m("bell_final", T.marks["two_desks"] + .6), gain=.42, label="the real bell, once")
    m("title", T.marks["bell_final"] + .5)                 # Barnaby / Every system deserves a butler.
    m("new_desk_fades", T.marks["title"] + 2.9)
    m("old_ones", T.marks["new_desk_fades"] + .7)          # Even the old ones.
    m("credit", T.marks["old_ones"] + 2.0)                 # Built on Synapse · 2nd Brain Labs × Geek Room Vibe-a-thon
    m("small_print", T.marks["credit"] + .3)
    m("fade_out", T.marks["credit"] + 2.6)
    end = T.marks["fade_out"] + 1.0
    m("end", end)
    T.scenes[-1]["end"] = round(end, 3)

    # ambience beds: each runs until the next place or time of day (score_v2 fades them in and out)
    until = {"rain": T.marks["timelapse"] + 1.6, "fan": s3 + 1.2, "radio": s3 + .6, "workshop": s7 + .8,
             "bustle": s8 + .3, "street": s9 + .6}
    for s in T.sfx:
        if s["type"] in until and "until" not in s and s["t"] < until[s["type"]]:
            s["until"] = round(until[s["type"]], 3)
        if s["type"] in ("rain", "street_night") and "until" not in s:
            s["until"] = round(end, 3)
    return end


def main() -> int:
    cues = json.loads(CUES.read_text(encoding="utf-8"))
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    lines = cues["voice"]
    assert len(man) == len(lines), "manifest and cue lines differ: re-run voices.py first"
    spans = []
    for v, mm in zip(lines, man):
        assert v["text"] == mm["text"], f"manifest out of date for: {v['text']}"
        x, sr = load(HERE / mm["file"])
        a, b = active_span(x, sr)
        spans.append((a, b, len(x) / sr))
    T = Timeline(lines, spans)
    end = build(T)
    missing = [i for i in range(1, len(lines) + 1) if i not in T.t]
    assert not missing, f"lines not placed: {missing}"

    # nothing overlaps (speech end of one line to the speech onset of the next, in time order)
    order = sorted(T.t, key=lambda n: T.on(n))
    worst = min(T.on(b) - T.off(a) for a, b in zip(order, order[1:]))
    clashes = [(a, b) for a, b in zip(order, order[1:]) if T.on(b) - T.off(a) < 0.15]

    for i, v in enumerate(lines, 1):
        v["t"] = T.t[i]
        v["speech"] = [round(T.on(i), 3), round(T.off(i), 3)]
    out = {
        "version": "2.1 animatic (timed from the rendered voices by video/v2/audio/layout.py)",
        "duration": round(end, 2),
        "fps": 15,
        "voices": cues["voices"],
        "scenes": T.scenes,
        "voice": lines,
        "sfx": sorted(T.sfx, key=lambda s: s["t"]),
        "music": T.music,
        "marks": T.marks,
    }
    CUES.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    PAGE_CUES.parent.mkdir(parents=True, exist_ok=True)
    PAGE_CUES.write_text("/* generated by video/v2/audio/layout.py: do not edit */\nwindow.CUES = "
                         + json.dumps(out, ensure_ascii=False) + ";\n", encoding="utf-8")

    print(f"{'scene':<28} {'start':>7} {'end':>7} {'len':>6}   script")
    for s in T.scenes:
        a, b = s["script"]
        print(f"{s['id']} {s['title']:<26} {s['start']:7.2f} {s['end']:7.2f} {s['end'] - s['start']:6.2f}   "
              f"{a // 60}:{a % 60:02d}-{b // 60}:{b % 60:02d} ({b - a}s)")
    print(f"total {end:.2f}s = {int(end // 60)}:{end % 60:05.2f}; tightest gap {worst * 1000:.0f} ms; "
          f"{len(clashes)} clash(es) {clashes or ''}")
    return 1 if clashes else 0


if __name__ == "__main__":
    raise SystemExit(main())
