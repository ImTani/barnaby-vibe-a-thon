"""Probe: can DawDreamer load and render a VST instrument (or effect) headlessly? Renders a short phrase to a WAV.

  runtime/audio/.venv/Scripts/python video/audio/vst_probe.py <plugin path> <out.wav> [--effect] [--notes 40,47,52]
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import soundfile as sf

SR, BLOCK = 48000, 512


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plugin")
    ap.add_argument("out")
    ap.add_argument("--effect", action="store_true", help="feed a plucked test tone through it instead of MIDI")
    ap.add_argument("--notes", default="52,56,59,64")
    ap.add_argument("--seconds", type=float, default=5.0)
    a = ap.parse_args()
    import dawdreamer as daw
    engine = daw.RenderEngine(SR, BLOCK)
    proc = engine.make_plugin_processor("p", a.plugin)
    print(f"loaded: {proc.get_name()}  inputs={proc.get_num_input_channels()} outputs={proc.get_num_output_channels()} "
          f"params={proc.get_plugin_parameter_size()}")
    if a.effect:
        t = np.arange(int(SR * a.seconds)) / SR
        tone = (np.sin(2 * np.pi * 220 * t) * np.exp(-3 * (t % 1.0)) * 0.3).astype(np.float32)
        src = engine.make_playback_processor("src", np.stack([tone, tone]))
        engine.load_graph([(src, []), (proc, ["src"])])
    else:
        notes = [int(n) for n in a.notes.split(",")]
        for i, n in enumerate(notes):                      # a little arpeggio, then the chord
            proc.add_midi_note(n, 90, 0.5 + i * 0.35, 1.2)
        for n in notes:
            proc.add_midi_note(n, 80, 2.2, 2.2)
        engine.load_graph([(proc, [])])
    engine.render(a.seconds)
    audio = engine.get_audio()
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    sf.write(a.out, audio.T, SR)
    print(f"rendered {audio.shape} peak={peak:.3f} -> {a.out}")
    return 0 if peak > 1e-4 else 3


if __name__ == "__main__":
    sys.exit(main())
