# Barnaby: the soundtrack

`video/v2/audio/soundtrack.wav` (48 kHz stereo, the cue sheet's length: 306.55 s for the final timing with the real
cast's takes, Barnaby as the ElevenLabs takes, with the 6 s end card) and its stems `music.wav` + `sfx.wav` +
`voice.wav`, which sum to it; `sfx.wav` is `effects.wav` + `ambience.wav` (kept whole because the DubMate backing is
music + sfx). All wav files are gitignored; this file and the scripts are the record.

```
runtime/audio/.venv/Scripts/python video/v2/audio/score_v2.py     # music (VSTs) + foley + voices -> mix and master
runtime/audio/.venv/Scripts/python video/v2/audio/check.py --sound-md   # measure; rewrite the tables below
runtime/audio/.venv/Scripts/python video/v2/audio/foley.py     # every one-shot alone -> .cache/audio/foley_reel.wav
```

- `score_v2.py`: the music (Ample Guitar M Lite II, MODO BASS 2, Valhalla VintageVerb as a send, hosted by DawDreamer;
  renders cached under `.cache/audio/music/`), the voices (`voice/manifest.json`; recorded takes come in through
  `video/audio/voices.py --takes`), ducking, and the master.
- `foley.py`: every effect and ambience bed, from the Ableton Live 12 Suite Core Library. The samples are read in place
  and never copied into the repo (licensed for productions, not redistribution); their 48 kHz conversions are cached as
  `.npy` under the gitignored `.cache/audio/samples/`.
- `check.py`: loudness, true peak, cue timing, dialogue clearance, excerpts at the key moments.

## v2.4: the real cast in one room (review cut 3)

Martin, Theo and Priya are now real people, each recorded on a different mic; Barnaby is ElevenLabs. The director's
notes: there is noise, especially on Martin's lines; run a simple vocal chain (EQ, compression); make everyone sound
cohesive, matched to Barnaby; the beds are still a little loud; the tool clinks are overused. Every line now goes
through one chain in `score_v2.py`'s voice stage, so any re-run applies it:

1. **High-pass at 75 Hz** (as before).
2. **Supertone Clear** (`X:\VST Plugins\VST3\Clear.vst3`, AI noise reduction) runs headless in DawDreamer on the
   recorded takes. It loads in about 20 s with no UI and no licence prompt. Settings: Ambience at -60 dB on Martin's
   takes. His mic's noise floor was about -62 dBFS; between words it now measures about -88 dB (median over 18 takes)
   while the words keep their level (the 95th-percentile 10 ms frame is the same before and after). Theo's and Priya's takes get a light clean (Ambience
   -20.7 dB). Voice and Voice Reverb stay at 0 dB. The plugin adds about 36 ms of latency; it is measured on each take by
   cross-correlation and removed. The cleaned takes are cached in `.cache/audio/voice_chain/`, keyed by the take's
   bytes and the setting. Barnaby is the reference and is not cleaned.
3. **Match EQ to Barnaby.** For each speaker, the long-term average spectrum over the voiced frames of all their lines,
   in 1/3-octave bands. The correction is Barnaby's spectrum minus the speaker's, then:
   - level-matched over 150 Hz (or 1.25x the speaker's pitch, if higher) to 6 kHz;
   - smoothed across neighbouring bands;
   - held to +-6 dB;
   - eased to 0 dB below the speaker's own median pitch (Martin ~117 Hz, Theo ~121 Hz, Priya ~207 Hz; Barnaby ~143
     Hz) and above 12 kHz. Priya's voice has nothing below its pitch to match, so it gets no low boost.

   It is applied as a linear-phase FIR. The deltas (dB):

   | speaker | 100 | 125 | 160 | 200 | 400 | 630 | 800 | 1k | 2k | 3.15k | 5k | 8k | 10k | 12.5k |
   |---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
   | Martin | +1.8 | +6.0 | +6.0 | +2.1 | +1.1 | -2.0 | -3.4 | -2.7 | +0.5 | +1.1 | -1.5 | -1.6 | -2.7 | -4.7 |
   | Theo | -0.2 | +0.1 | +1.7 | +1.5 | +1.6 | -1.8 | -2.8 | -1.9 | +1.7 | -1.7 | -1.3 | -2.8 | -4.2 | -4.4 |
   | Priya | 0 | 0 | 0 | +4.9 | +1.7 | -4.5 | -6.0 | -3.4 | -0.1 | +2.6 | +3.0 | +0.4 | +0.2 | -1.3 |

   How far each speaker's spectrum sits from Barnaby's, from 150 Hz (Priya: 259 Hz) to 10 kHz, as the RMS of the
   per-band differences (largest band in brackets), whole chain against Barnaby through the same de-esser and
   compressor: Martin 2.5 dB (7.0) before, 1.1 dB (1.9) after; Theo 2.3 dB (4.2) before, 1.1 dB (2.6) after; Priya
   3.5 dB (8.1) before, 1.6 dB (3.5) after.
4. **De-esser, 5-9 kHz,** split band. A zero-phase FIR band plus the rest add back to the line exactly. The band comes
   down only on the sibilants: where it runs above its own 92nd percentile in the line's voiced frames, or comes within
   3 dB of the whole voice (an "s" dominating). The cut is 0.6 dB per dB over, at most 6 dB, with 2 ms attack and 60 ms
   release. It cuts more than 3 dB on 3-7 % of the voiced time.
5. **Compressor:** 2.5:1, RMS detection, 15 ms attack, 150 ms release, a 6 dB soft knee. The threshold is set per line
   so the louder words (the 90th percentile of the voiced envelope) see about 3 dB of gain reduction. On the final sheet
   the median is 3.4 dB, the range 3.0-5.0 dB. Barnaby goes through the de-esser and the compressor too.
6. **The same loudness for every line** (BS.1770, gated, as before). Then **one short room for all four voices**: a
   0.28 s room (HP 250 Hz, LP 6.5 kHz, 4 ms predelay) at a low send, so they sit in one space. The off-screen lines keep
   their treatment: Martin from the workshop in scene 1 and the two goodnights get a high-cut and the farther 0.55 s room.

- **Beds 4-6 dB lower.** Every bed is down 4.4 dB from v2.3. The rain and the PC fan (the opening) are down 6 dB. The
  workshop beds are now levelled by their room tone alone, 3 dB under its v2.3 share; most of their drop comes from the
  thinned clinks. Short-term max against the dialogue (the levels table below), v2.3 then now:

  | bed | v2.3 | now |
  |---|---|---|
  | rain | -19.0 LU | -25.9 LU |
  | fan | -23.7 LU | -30.7 LU |
  | radio | -29.8 LU | -35.0 LU |
  | back-office room tone | -24.6 LU | -29.8 LU |
  | workshop | -14.5 LU | -24.4 LU |
  | Tuesday | -15.8 LU | -26.3 LU |
  | Lisbon street | -17.2 LU | -23.9 LU |
  | Lisbon at night | -20.4 LU | -23.7 LU |

  The night street's short-term max is only 3.3 LU lower. Its integrated level, while it plays, is 5.5 LU lower (-22.4
  to -27.9 LU).
- **The tool clinks thinned.** The parts trays' nuts and bolts (and Tuesday's mug) now sound only in the pauses between
  lines, from 0.4 s after one line to 0.5 s before the next. They come as one 0.6-1.6 s burst in half the pauses of 1.2
  s or more (65 % on Tuesday; the mug in 20 %), and they are quieter. Measured on the 1-5 kHz band of the two workshop
  beds over the film (50 ms RMS):
  - bursts: 62 in v2.3, 6 now;
  - loudest: -32.3 dB in v2.3, -44.6 dB now;
  - share of speech time with a clink above -60 dB: 18 % in v2.3, 0 % now.

  In the mix, the loudest workshop moment (a clink between lines) peaks at -24.3 dBFS, against -17.7 in v2.3. Its
  momentary max is -21.2 LU under the dialogue, against -13.1. The two workshop beds as a whole are 4.8 and 4.7 dB
  quieter (RMS, before the master).

## v2.3: the director's sound notes (review cut 2)

- **Beds much lower, the opening especially.** Every category is measured alone against the dialogue (the levels table
  below, from `check.py --levels`). Rain went down 9.5 dB, the PC fan 6 dB, the street 6 dB, the
  workshop 4.6 dB, Tuesday 4.4 dB, the radio 2 dB;
  the workshop's tool clinks are peak-compressed hard so none pokes out.
- **No voices in any bed.** The crowd recording is gone from the workshop, Tuesday and Lisbon; the talk radio is gone
  from the workshop beds too (it stays only in scene 1, far off, where it is switched off on screen). What is left:
  room tone, tools now and then, a mug, traffic, birds, night air.
- **Targeted effects:** the compressor runs 1.2 s, the freewheel 1.6 s, Martin's keys are two handfuls, not three; the
  passage's soft bell gives way to the hand-back chord.
- **The hand-back chimes (scene 5).** A hand-back is four steps (the job, the customer, a text, the status); each step
  gets one note of the same figure, **D5-F#5-A5-D6** (the score's key, D major), on the celeste (`Celeste C6`, tuned down
  10, 6 and 3 semitones and up 2), each note as long as its step (1.2x the interval) and panned left to right across the
  four stops. The notes sit on Barnaby's steps from the cue sheet: walk 1 (`marks.walk1`, steps 0.45 s apart), walk 2
  (`walk2`, 0.26 s apart), walk 3 (`walk3`: the sheet has no steps there, so four are derived 0.17 s apart, quicker
  again). At the passage (`marks.passage` + 0.35 s) the four notes sound as **one chord**: the steps have become one.
  For Tom's Brompton (`marks.walk4`) the chord sounds once more, alone.
- **Every line at the same loudness.** Each voice line is levelled to the same BS.1770 loudness (gated, so pauses don't
  count) before the mix, so the ElevenLabs Barnaby (mastered louder and more compressed) sits with the TTS voices; the
  per-speaker check is in the table below.
- **The timing follows the cue sheet.** Everything is placed from `cues.json` (marks, sfx, music sections) and the
  voice manifest, so a new layout (faster Barnaby, or an ElevenLabs voice) only needs `score_v2.py` and `check.py` re-run.

## The approach

- **Real recordings first.** Each cue is the best-fitting Core Library recording, layered where one sample is not the
  whole gesture (a mouse is a press and a release; the stand's clamp is a lever, a jaw and a ring), pitched by varispeed,
  EQ'd and placed in one of four short convolution rooms: the back office (0.38 s), the workshop heard through the door
  (1.05 s, darker, more send: everything off-screen goes here), Barnaby's worlds (1.3 s, a soft air for the stylised
  sounds) and Theo's flat in Lisbon (0.45 s). Level and pan follow the perspective: the desk is close and centred, the
  lamp left, the drive under the desk, the workshop off to the right and further back.
- **The bell.** Barnaby's signature is the Core Library's `Bell Cash`, a small struck bell recorded dry, whose partials
  (1 : 1.52 : 2.28 : 6.6) sit where a counter bell's do; it is tuned to E6, the 9th of D, so it belongs to the score's
  last chord. The recording is damped (it dies in ~0.7 s), so its strike plays as recorded and a modal model fitted to its
  own four partials (frequency, amplitude and phase measured 0.2 s in) carries the ring on for ~4 s with the slow beat of
  each mode's split doublet. The model hands over from the recording without a seam because it starts in phase with it.
- **Synthesis only where the library has nothing:** road traffic in Lisbon (filtered noise swells with Doppler-ish
  sweeps and slow pans), and the low room tone under the back office and the workshop (brown noise, low-passed). The
  derived cues (Barnaby's steps across the workshop floor and drawer 1 sliding open in scene 3, which the shot plan
  describes but `cues.json` does not carry) come from marks, not from changes to the voice timing.
- **The implied people (v2.2):** the radio switched off and the roller shutter coming down as Martin leaves (scene 1-2),
  the chair taking Martin's weight and his breath out (scene 3), the lamp switched on at dusk (scene 6), Theo's espresso
  cup (scene 8), Martin's coat and keys and the two doors as he leaves, and Theo's studio door (scene 9). All are
  Core Library recordings: the shutter is the metallic clatter looped and pulsed slat by slat over a rumble, landing on a
  metal impact; a door is a rough low wood hit (its body) with the lock recording's bolt (its latch).
- **Sound leads picture:** the beds the cue sheet marks "leads the cut" (the Tuesday bustle, the Lisbon street, the rain
  for goodnight) start a second before their scene with a short (0.6 s; the rain 1.6 s) fade in; the outgoing bed
  carries on under the first second of the new scene and fades over 1.6 s.
- **The mix:** dialogue first. Under speech (with 60 ms of look-ahead, so the first syllable is clear) the music ducks 8 dB (up to 4 dB
  more where it runs hot, as in the Lisbon strums) with a further 3 dB presence dip around 2.5 kHz; the ambience ducks 4 dB and the effects 2 dB. The score steps
  back 5 dB for the key turning and 3 dB from "Fussy." through the click. Off-screen lines (Martin from the
  workshop, the two goodnights from the door) are high-cut and sent further into the room. One gain curve masters all
  four stems: a slow glue compressor, the end fade, the level to -16 LUFS integrated and a true-peak limiter (4x
  oversampled detection) at -1.8 dBTP.

## The music against the clock

The same instruments and the same grid (D major, 80 BPM, a bar line exactly on `marks.tab_change`), fitted to whatever
the cue sheet says, under the shot plan's rule that the music is Barnaby (`video/v2/SHOTLIST.md`, section 4).
`score_v2.py` prints each section's cue time against its bar line on every run and refuses to render if the lift misses
the tab change or the handover has not resolved before the key.

- **Nothing before the bell:** the music stem is digital silence until `marks.bell_arrive`; the entry roll comes 0.5 s
  after the bell, the soft picking on the first full bar after it.
- **The handover resolves before the key:** the picking ends on Asus4, then one D roll whose notes end 0.5 s before
  `marks.key`; the stem is faded to silence over the last 0.6 s. **Rain only** under the key, the lamp-off and the
  time-lapse, until Monday's walking music starts on the first bar of the `work` section.
- **It thins under "Who's got too much on this week?"** and **builds from the code to the click** (8 bars from the first
  bar line after `marks.code`, climbing to sixteenths) into **the lift, exactly on the tab change**; the score steps back
  3 dB from "Fussy." through the click.
- One strum rings over the cut into Tuesday; the soft picking settles for Priya. **Brighter for Lisbon** (full strums
  after the street has come in), one strum ringing into the night, held chords under the goodnights, and **the final
  Dadd9 resolves on the last bell** (0.25 s after `marks.bell_final`: the bell is heard first and becomes its 9th).
- **The end card:** the roll under "Even the old ones." is the last chord; it carries into the end card (`marks.end_card`)
  and fades out over the card, gone by `marks.fade_out`.

<!-- generated by check.py --sound-md: begin -->

## Mix: targets and measured

| | target | measured |
|---|---|---|
| integrated loudness | -16 LUFS | -16.1 LUFS (ffmpeg ebur128), -16.09 (pyloudnorm) |
| true peak | <= -1 dBTP | -1.8 dBTP (ffmpeg, 4x), -1.8 dBTP (4x polyphase) |
| loudness range | - | 14.6 LU |
| format | 48 kHz stereo | 48000 Hz, 2 ch, PCM_16, 306.55 s (film 306.55 s) |
| music + effects + ambience + voice = soundtrack | exact | max difference -76.3 dBFS (dither) |
| sfx.wav = effects + ambience | exact | max difference -84.3 dBFS (dither) |
| stems, integrated | - | music -27.8 LUFS, effects -28.9 LUFS, ambience -44.8 LUFS, voice -15.3 LUFS |
| dialogue over everything under it | always clear | min 9.4 dB (line 48), median 18.9 dB over 54 lines (RMS in each line's speech window) |
| voices, level per speaker | consistent | Martin -15.5 LUFS (-16.5..-13.4, 18 lines, take); Theo -15.6 LUFS (-17.5..-14.6, 10 lines, take); Barnaby -14.8 LUFS (-15.2..-13.7, 23 lines, take); Priya -14.3 LUFS (-14.7..-13.7, 3 lines, take) |
| effects on their cues | on the cue | 92 one-shots: median 2 ms, max 30 ms from cue to the first rise in the effects stem |

## Levels by category, against the dialogue

Each category re-rendered alone with the mix's ducking and master gain. The dialogue's reference: its typical short-term (3 s) level -16.7 LUFS and typical momentary (400 ms) level -15.5 LUFS while someone speaks (voice stem: peak -1.4 dBFS, integrated -15.3 LUFS). Targets (v2.4): beds 4-6 dB under v2.3's -14 to -20 LU, so about -20 to -30 LU under the dialogue (short-term max), the opening's rain and fan at the quiet end; foley and UI never louder than a voice (momentary max under the dialogue's typical momentary level).

| category | peak dBFS | short-term max LUFS (vs dialogue) | momentary max LUFS (vs dialogue) | integrated while playing LUFS (vs dialogue) |
|---|---|---|---|---|
| rain | -32.8 | -42.5 (-25.9 LU) | -42.3 (-26.8 LU) | -45.8 (-29.2 LU) |
| fan (2009 PC) | -38.0 | -47.4 (-30.7 LU) | -46.1 (-30.6 LU) | -49.6 (-32.9 LU) |
| radio (scene 1) | -38.2 | -51.6 (-35.0 LU) | -48.0 (-32.5 LU) | -53.7 (-37.1 LU) |
| room tone (back office) | -35.1 | -46.4 (-29.8 LU) | -44.7 (-29.2 LU) | -49.0 (-32.4 LU) |
| workshop | -24.3 | -41.0 (-24.4 LU) | -36.7 (-21.2 LU) | -47.9 (-31.2 LU) |
| workshop, Tuesday | -31.1 | -43.0 (-26.3 LU) | -41.8 (-26.3 LU) | -46.3 (-29.6 LU) |
| Lisbon street | -30.2 | -40.6 (-23.9 LU) | -39.2 (-23.7 LU) | -43.7 (-27.0 LU) |
| Lisbon street, night | -29.2 | -40.4 (-23.7 LU) | -38.5 (-23.0 LU) | -44.6 (-27.9 LU) |
| foley | -4.6 | -28.3 (-11.6 LU) | -24.5 (-9.0 LU) | -30.7 (-14.0 LU) |
| UI (clicks, reload, pops, ding) | -10.7 | -30.8 (-14.2 LU) | -23.1 (-7.6 LU) | -33.2 (-16.6 LU) |
| worlds (steps, chimes, drawer, soft bells, swell) | -12.2 | -25.3 (-8.6 LU) | -20.7 (-5.2 LU) | -26.3 (-9.7 LU) |
| the bell | -6.7 | -25.7 (-9.0 LU) | -17.6 (-2.1 LU) | -24.6 (-7.9 LU) |

## Key moments (excerpts in .cache/audio/excerpts/)

| moment | excerpt | excerpt loudness | at the event: peak / loudest 400 ms | stems RMS at the event (dBFS) |
|---|---|---|---|---|
| s2_bell_arrival | 45.52-51.52 s | -18.4 LUFS | -6.9 dBFS / -17.6 LUFS | music -38.8, effects -23.7, ambience -44.1, voice -96.4 |
| s4_key_turn | 108.8-112.4 s | -19.4 LUFS | -4.7 dBFS / -25.0 LUFS | music -39.3, effects -32.7, ambience -46.2, voice -96.7 |
| s6_click_tab_change | 198.73-203.73 s | -18.8 LUFS | -2.3 dBFS / -15.8 LUFS | music -40.7, effects -37.3, ambience -50.4, voice -20.6 |
| s9_final_bell | 290.35-296.35 s | -23.7 LUFS | -7.8 dBFS / -18.0 LUFS | music -27.4, effects -24.3, ambience -44.3, voice -96.3 |

## Effect cues: source and processing

Core Library paths are under `C:/ProgramData/Ableton/Live 12 Suite/Resources/Core Library/Samples/`. Measured: onset = cue to the first rise in the effects stem; peak and loudest 400 ms of the effects stem alone (0-0.6 s after the cue; overlapping sounds count).

### rain

Source: `Loops/Texture/Rain and Train.wav`

Processing: rain on the window: random 7-15 s stretches of the steady rain (2 s crossfades), HP 110 Hz, LP 7.5 kHz, -3 dB shelf above 2.5 kHz (the glass), gentle peak compression

| from | to | level | label |
|---|---|---|---|
| 0.00 | 77.38 | 1.0 x 0.003 RMS | rain on the window (bed) |
| 276.27 | 306.55 | 0.8 x 0.003 RMS | rain returns over the shop (bed; leads the cut) |

### office_night

Source: synth: room tone; `Loops/Texture/Machine Noise Ambient.wav`

Processing: a low room tone (synth: brown noise LP 160 Hz) with the machine loop -5 st LP 400 Hz under it

| from | to | level | label |
|---|---|---|---|
| 0.00 | 77.38 | 1.0 x 0.003 RMS | the back office at night (derived: scenes 1-2) |
| 277.27 | 306.55 | 0.8 x 0.003 RMS | the back office at night (derived: scene 9) |

### radio

Source: `Loops/Texture/Radio Station Search.wav`

Processing: the radio recording through a small speaker (BP 450 Hz-3 kHz, +4 dB at 1.1 kHz, soft saturation, LP 2.4 kHz), panned right, very low

| from | to | level | label |
|---|---|---|---|
| 0.40 | 76.38 | 0.55 x 0.0021 RMS | a radio far off in the workshop (bed) |

### fan

Source: `Loops/Texture/Machine Noise Ambient.wav`

Processing: the machine loop varispeeded up from 25 % over 1.6 s (the fan spinning up), BP 70 Hz-3.2 kHz, panned left

| from | to | level | label |
|---|---|---|---|
| 0.60 | 76.98 | 1.0 x 0.002 RMS | PC fan spins up, then hums (bed) |

### hdd

Source: `One Shots/Drums/Misc Percussion/Perc Tiny.wav`

Processing: 10 ms grains of the tiny perc (-3..+2 st) at irregular seek intervals, HP 400 Hz, LP 6.5 kHz, a +5 dB resonance at 900 Hz (the drive cage); under the desk, left; office room 12 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 4.20 | hard drive chatter | +0 ms | -21.4 | -37.3 LUFS |
| 15.55 |  | -30 ms | -20.3 | -35.4 LUFS |
| 18.10 |  | -30 ms | -20.7 | -37.0 LUFS |
| 19.80 |  | -30 ms | -20.6 | -34.4 LUFS |

### tab

Source: `One Shots/Drums/Wood/Wood Insert Cassette.wav`; `One Shots/Drums/Misc Percussion/Click Vinyl.wav`

Processing: old shop mouse: the cassette's latch (from 46 ms) -1 st (down) + vinyl click +4 st 85 ms later (up); HP 380 Hz, LP 9 kHz, +3 dB at 2.6 kHz; fast peak compressor; a little width; office room 22 %; pan follows the tab a little

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 13.80 |  | -8 ms | -15.2 | -35.7 LUFS |
| 14.65 |  | -8 ms | -15.1 | -35.7 LUFS |
| 15.50 |  | -8 ms | -14.9 | -33.5 LUFS |
| 16.35 |  | -8 ms | -14.8 | -35.7 LUFS |
| 17.20 |  | -8 ms | -14.7 | -35.7 LUFS |
| 18.05 |  | -8 ms | -14.7 | -33.5 LUFS |
| 18.90 |  | -8 ms | -14.5 | -35.7 LUFS |
| 19.75 |  | -8 ms | -14.4 | -32.3 LUFS |
| 20.60 |  | -8 ms | -14.3 | -35.7 LUFS |
| 24.97 |  | -8 ms | -16.8 | -37.7 LUFS |
| 25.91 |  | -8 ms | -16.8 | -37.6 LUFS |

### radio_off

Source: `One Shots/Drums/Misc Percussion/Click Vinyl.wav`; `One Shots/Drums/Wood/Wood Insert Cassette.wav`

Processing: a dry switch: vinyl click -2 st + the cassette latch -5 st, HP 300 Hz, LP 6 kHz; through the workshop door (workshop room 60 %, right); the radio bed stops on it

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 29.14 | the workshop radio clicks off (o.s.) | -2 ms | -15.6 | -35.0 LUFS |

### shutter

Source: `One Shots/Drums/Misc Percussion/Perc Metallic Clatter.aif`; `Loops/Texture/Machine Noise Ambient.wav`; `One Shots/FX/Impact Short Metal.wav`

Processing: the metallic clatter -5 st, looped (forward, reversed) to the cue's length and pulsed at 9-14 slats a second, BP 250 Hz-4.5 kHz, a little rumble (machine loop -8 st LP 300 Hz), and the bottom bar landing (metal impact -4 st, LP 3.5 kHz) at the end; off-screen: workshop room 85 %, right, low

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 29.64 | Martin pulls the shop shutter down for the night (o.s.) | +14 ms | -13.3 | -24.9 LUFS |

### tab_close

Source: `One Shots/Drums/Wood/Wood Insert Cassette.wav`; `One Shots/Drums/Misc Percussion/Click Vinyl.wav`

Processing: as tab, a little lighter

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 41.32 |  | -8 ms | -16.9 | -38.2 LUFS |
| 41.72 |  | -8 ms | -16.9 | -38.1 LUFS |
| 42.12 |  | -8 ms | -16.9 | -38.1 LUFS |
| 42.52 |  | -8 ms | -17.1 | -38.1 LUFS |
| 42.92 |  | -8 ms | -17.1 | -38.2 LUFS |
| 43.57 |  | -8 ms | -17.2 | -38.2 LUFS |
| 44.22 |  | -8 ms | -17.3 | -38.4 LUFS |
| 44.87 |  | -8 ms | -17.5 | -38.1 LUFS |
| 45.52 |  | -8 ms | -17.5 | -38.3 LUFS |

### bell

Source: `One Shots/Drums/Bell/Bell Cash.aif`; modal ring (fitted to the sample)

Processing: the counter bell: Bell Cash tuned +0.3 st to E6; the recording's strike for 0.2 s, then a modal ring fitted to its own four partials (1318, 1998, 3009, 8700 Hz: amplitude and phase measured at 0.2 s; T60 5.0, 1.8, 3.4, 1.0 s; slow doublet beats), a raised-cosine hand-over over 0.25 s with the recording kept at 30 % under it; HP 400 Hz; office room 35 % (50 % for the last bell) plus an air halo in the world room; the score ducks 3 dB for the last one

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 47.02 | the brass bell: Barnaby arrives | +0 ms | -6.7 | -17.6 LUFS |
| 291.85 | the real bell, once | +0 ms | -8.3 | -18.3 LUFS |

### pop

Source: `One Shots/Drums/FX Hit/FX Drip 2.wav`

Processing: a water drip tuned up the D major pentatonic, LP 4.2 kHz, HP 250 Hz; six rising pops 75 ms apart for 'six light up', two for 'two rows change'; world room 40 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 56.88 | six light up | -4 ms | -14.7 | -26.6 LUFS |
| 118.16 | order 3 lands | -4 ms | -15.2 | -30.4 LUFS |
| 213.17 | two rows change | -4 ms | -15.7 | -28.1 LUFS |

### key_tap

Source: `One Shots/Drums/Misc Percussion/Foley Coin LDre.wav`; `One Shots/Drums/Misc Percussion/Perc Plastic 2.wav`

Processing: the coin's first impact only (45-200 ms: the ring damped by the keys), HP 900 Hz, on a plastic tap -2 st LP 5 kHz; fast compressor; office room 18 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 71.49 | the key on the keyboard: a small clean metal tap | -4 ms | -11.1 | -29.9 LUFS |

### lamp_click

Source: `One Shots/Drums/Wood/Wood Insert Cassette.wav`; `One Shots/Drums/Misc Percussion/Click Vinyl.wav`

Processing: vinyl click +2 st, then the cassette latch -4 st 12 ms later; HP 250 Hz, LP 8 kHz, +2 dB at 1.8 kHz; fast compressor; panned left (the lamp); office room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 74.18 | the lamp clicks off | -2 ms | -11.3 | -32.1 LUFS |

### timelapse

Source: `One Shots/FX/Swell Short Noise.wav`; `One Shots/FX/Bowl Swell B1.aif`

Processing: a noise swell varispeeded to the cue's length, LP 4.5 kHz, with a singing bowl +3 st (B -> D) LP 1.5 kHz; world room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 75.78 | time passes: a soft swell | (swell or derived: not timed) | | |

### workshop

Source: synth: room tone; `Loops/Texture/Nuts and Bolts.wav`

Processing: room tone (synth) + tools now and then (the parts trays: nuts and bolts, BP 300 Hz-5 kHz, peak-compressed hard so no clink pokes out), thinned in v2.4: only in the pauses between lines (from 0.4 s after one to 0.5 s before the next), a 0.6-1.6 s burst in half the pauses of 1.2 s or more, quieter; no voices, no radio

| from | to | level | label |
|---|---|---|---|
| 77.78 | 217.97 | 1.0 x 0.0039 RMS | workshop morning bed: room, radio, tools |

### freewheel

Source: `One Shots/Drums/Misc Percussion/Perc Tiny.wav`

Processing: 12 ms grains of the tiny perc +6 st at 24 Hz slowing to 5 Hz, HP 1.5 kHz; off-screen: workshop room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 79.98 |  | +0 ms | -16.2 | -28.8 LUFS |

### chair

Source: `One Shots/Drums/Misc Percussion/Perc Hit Soft.aif`; `One Shots/Drums/Wood/Wood Rough Low.aif`; `One Shots/Drums/FX Hit/FX Squeak.aif`; `One Shots/FX/Riser Taka Breath.wav`

Processing: the cushion (soft hit -8 st LP 500 Hz), the seat's creak (rough wood -5 st LP 2.5 kHz), the spring's squeak -7 st LP 4 kHz, and a breath out 0.45 s later (the breath riser's tail, BP 250 Hz-2.8 kHz); office room 20 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 80.38 | a chair creaks: Martin sits, a breath out | -30 ms | -16.2 | -29.0 LUFS |

### compressor

Source: `Loops/Texture/Machine Noise Ambient.wav`; `Loops/Texture/Sink Noise.wav`

Processing: a 1.2 s run: the machine loop varispeed-spun up (0.55 -> 1.0 in 0.35 s), LP 2.2 kHz, a 9-24 Hz chug, air hiss (sink noise, BP 1.2-6 kHz); off-screen: workshop room 80 %, panned right

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 87.96 |  | (swell or derived: not timed) | | |

### step

Source: `One Shots/Drums/Misc Percussion/Perc Hit Soft.aif`; `One Shots/Instrument/Mallets/Marimba Cloth C3.aif`

Processing: a soft hit -5 st LP 1.4 kHz + a cloth-mallet marimba note an octave down (D or A, alternate feet) LP 900 Hz; Barnaby's world room 30 %; alternate pan +-0.08 (the marimba is on D or A)

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 89.51 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | -2 ms | -21.1 | -37.0 LUFS |
| 89.98 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | -2 ms | -21.1 | -36.4 LUFS |
| 90.46 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | -2 ms | -22.9 | -38.3 LUFS |
| 90.93 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | -1 ms | -22.9 | -37.6 LUFS |
| 91.41 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | -1 ms | -23.0 | -37.9 LUFS |
| 91.88 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | -1 ms | -24.9 | -39.6 LUFS |
| 130.24 |  | -2 ms | -13.8 | -24.6 LUFS |
| 130.69 |  | +0 ms | -13.6 | -23.7 LUFS |
| 131.14 |  | +0 ms | -12.8 | -22.1 LUFS |
| 131.59 |  | +0 ms | -12.8 | -21.0 LUFS |
| 133.82 |  | -2 ms | -14.5 | -23.9 LUFS |
| 134.08 |  | +0 ms | -12.2 | -22.7 LUFS |
| 134.34 |  | +0 ms | -12.2 | -21.2 LUFS |
| 134.60 |  | +0 ms | -12.2 | -22.3 LUFS |
| 137.76 | Barnaby's walk 3, quicker (derived from marks.walk3) | -2 ms | -12.6 | -21.1 LUFS |
| 137.93 | Barnaby's walk 3, quicker (derived from marks.walk3) | +1 ms | -12.6 | -20.7 LUFS |
| 138.10 | Barnaby's walk 3, quicker (derived from marks.walk3) | +0 ms | -13.0 | -20.7 LUFS |
| 138.27 | Barnaby's walk 3, quicker (derived from marks.walk3) | -1 ms | -13.0 | -23.1 LUFS |

### drawer

Source: `One Shots/Drums/Misc Percussion/Perc Wood Scratch.aif`; `One Shots/Drums/Wood/Wood Dry Low.aif`

Processing: the wood scratch -7 st (a slow slide, LP 3.5 kHz, rising) and a dry wood knock -3 st as it stops; world room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 95.15 | drawer 1 of the parts cabinet slides open in the shelf shot (derived from marks.shelf) | +0 ms | -17.2 | -31.3 LUFS |

### mouse_click

Source: `One Shots/Drums/Wood/Wood Insert Cassette.wav`; `One Shots/Drums/Misc Percussion/Click Vinyl.wav`

Processing: the shop: as tab (the old shop mouse). Lisbon: Theo's modern mouse, +2.5 st, shorter, HP 600 Hz, +3 dB at 3.4 kHz, Lisbon room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 109.42 |  | -8 ms | -10.7 | -31.7 LUFS |
| 117.36 |  | -8 ms | -11.8 | -32.7 LUFS |
| 128.85 |  | -8 ms | -13.0 | -34.1 LUFS |
| 129.60 |  | -8 ms | -13.0 | -34.1 LUFS |
| 199.73 |  | -8 ms | -12.5 | -33.3 LUFS |
| 254.64 | Connect | -8 ms | -11.0 | -33.0 LUFS |

### key_turn

Source: `One Shots/FX/Foley Door Lock.wav`

Processing: the lock recording as is (lead-in trimmed): the key in, the turn, the bolt; HP 140 Hz, LP 11 kHz, -2 dB at 3.2 kHz; fast compressor; office room 25 %; the score ducks 5 dB around it

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 109.90 | a real key turning in a lock | -6 ms | -4.6 | -25.3 LUFS |

### bell_soft

Source: `One Shots/Drums/Bell/Bell Cash.aif`; modal ring (fitted to the sample)

Processing: the same bell, its strike rounded (12 ms attack) and darker (LP 3.8 kHz), lower, world room 70 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 110.80 | the bell's soft confirm | +0 ms | -14.7 | -22.7 LUFS |
| 148.07 | the passage opens | -30 ms | -20.0 | -27.2 LUFS |
| 203.13 | a new room | +0 ms | -15.2 | -23.2 LUFS |

### clunk

Source: `One Shots/Drums/Misc Percussion/Perc Hit Hard.aif`; `One Shots/FX/Impact Short Metal.wav`; `One Shots/Drums/Misc Percussion/Perc Pan.wav`

Processing: the lever's crack (hit, +-1 st) + the jaw's clunk (metal impact -2 st, 35 ms later) + a short pan ring; HP 70 Hz, LP 5 kHz; off-screen: workshop room 75 %, panned right, low

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 121.96 | repair stand clamp releases: Sofia's | -2 ms | -12.9 | -24.5 LUFS |
| 132.54 | Kwame's | -2 ms | -13.6 | -24.4 LUFS |
| 135.30 | Jana's | -2 ms | -13.5 | -26.0 LUFS |
| 149.67 | Tom's Brompton | +0 ms | -12.9 | -24.5 LUFS |

### chime

Source: `One Shots/Instrument/Mallets/Celeste C6.wav`

Processing: the hand-back figure, one note per step: the celeste tuned to D5, F#5, A5, D6 (-10, -6, -3, +2 st), cut to 1.2x the step interval (0.54 s, 0.31 s, 0.2 s), LP 6 kHz; panned left to right across the four stops; world room 35 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 130.24 | hand-back chime 1/4 (the job), walk 1 | -2 ms | -13.8 | -24.6 LUFS |
| 130.69 | hand-back chime 2/4 (the customer), walk 1 | +0 ms | -13.6 | -23.7 LUFS |
| 131.14 | hand-back chime 3/4 (a text), walk 1 | +0 ms | -12.8 | -22.1 LUFS |
| 131.59 | hand-back chime 4/4 (the status), walk 1 | +0 ms | -12.8 | -21.0 LUFS |
| 133.82 | hand-back chime 1/4 (the job), walk 2 | -2 ms | -14.5 | -23.9 LUFS |
| 134.08 | hand-back chime 2/4 (the customer), walk 2 | +0 ms | -12.2 | -22.7 LUFS |
| 134.34 | hand-back chime 3/4 (a text), walk 2 | +0 ms | -12.2 | -21.2 LUFS |
| 134.60 | hand-back chime 4/4 (the status), walk 2 | +0 ms | -12.2 | -22.3 LUFS |
| 137.76 | hand-back chime 1/4 (the job), walk 3 | -2 ms | -12.6 | -21.1 LUFS |
| 137.93 | hand-back chime 2/4 (the customer), walk 3 | +1 ms | -12.6 | -20.7 LUFS |
| 138.10 | hand-back chime 3/4 (a text), walk 3 | +0 ms | -13.0 | -20.7 LUFS |
| 138.27 | hand-back chime 4/4 (the status), walk 3 | -1 ms | -13.0 | -23.1 LUFS |

### chime_chord

Source: `One Shots/Instrument/Mallets/Celeste C6.wav`

Processing: the four notes at once (D5 F#5 A5 D6), 2.6 s, LP 6 kHz; world room 45 %; replaces the passage's soft bell

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 148.02 | the passage: the four notes as one chord | -2 ms | -16.8 | -26.5 LUFS |
| 151.60 | Tom's Brompton in one step: the chord once | -2 ms | -19.3 | -29.2 LUFS |

### lamp_on

Source: `One Shots/Drums/Wood/Wood Insert Cassette.wav`; `One Shots/Drums/Misc Percussion/Click Vinyl.wav`

Processing: as lamp_click (another take of the same switch)

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 156.14 | the desk lamp clicks on: dusk, Martin at Theo's desk | -2 ms | -11.4 | -32.2 LUFS |

### typing

Source: `One Shots/Drums/Misc Percussion/Perc Plastic 1.wav`; `One Shots/Drums/Misc Percussion/Perc Plastic 2.wav`; `One Shots/Drums/Wood/Wood Prod Soft.wav`

Processing: the old keyboard: plastic taps (two samples, +-1.5 st; the space bar -3 st and louder) with a soft wooden upstroke +3 st 70-110 ms later; word gaps; HP 220 Hz, LP 9 kHz, -7 dB at 500 Hz (the samples' plastic ring), +2.5 dB at 2.2 kHz; office room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 176.58 | keyboard foley under the code | +0 ms | -12.9 | -30.7 LUFS |

### ding

Source: `One Shots/Instrument/Mallets/Celeste C6.wav`

Processing: the celeste on D (+2 st) with a quiet A above 70 ms later, LP 7 kHz; world room 45 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 182.38 | checks pass | -2 ms | -16.3 | -22.8 LUFS |

### reload

Source: `One Shots/Drums/Misc Percussion/Perc Tiny.wav`; `Loops/Texture/Machine Noise Ambient.wav`

Processing: a 0.55 s burst of the drive's seeks + the fan bed rising and falling over 1.8 s

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 200.13 | the page reloads | +0 ms | -17.3 | -31.7 LUFS |

### bustle

Source: synth: room tone; `Loops/Texture/Nuts and Bolts.wav`; `Loops/Texture/Tea Cups.wav`

Processing: the same, busier (a burst in 65 % of the pauses), and a mug now and then (20 % of the pauses); no voices

| from | to | level | label |
|---|---|---|---|
| 216.37 | 243.64 | 1.0 x 0.0054 RMS | Tuesday workshop bustle (bed; leads the cut) |

### street

Source: synth: traffic; `Loops/Texture/Forest Ambience.wav`

Processing: traffic below the window (synth: a rumble and passing cars, each a filtered noise swell with a slow pan) + birds (HP 1.5 kHz); LP 6 kHz (the window); no voices

| from | to | level | label |
|---|---|---|---|
| 242.34 | 277.87 | 1.0 x 0.0048 RMS | Lisbon: street below the window (bed; leads the cut) |

### cup

Source: `Loops/Texture/Tea Cups.wav`

Processing: one clink from the tea-cups recording (2.865-3.35 s) and a small settle (3.935 s) 75 ms later, HP 350 Hz; Lisbon room 22 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 246.74 | an espresso cup set down on its saucer | -2 ms | -13.4 | -30.6 LUFS |

### keys_modern

Source: `One Shots/Drums/Misc Percussion/Perc Plastic 1.wav`; `One Shots/Drums/Misc Percussion/Perc Plastic 2.wav`

Processing: Theo's modern keyboard: the same taps -4 st, 50 ms long, LP 3.8 kHz, -7 dB at 380 Hz, quicker, no upstroke; Lisbon room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 249.14 | Theo types the name, pastes the repo path, types the URL | +0 ms | -15.4 | -30.9 LUFS |

### coat

Source: `Loops/Texture/Paper LDre.wav`; `One Shots/Drums/Shaker/Shake Maracas Soft.aif`

Processing: the paper rustle -4 st LP 3 kHz (cloth) between two sleeve swishes (soft maracas -10 st LP 2.2 kHz); off-screen: workshop room 45 %, left, low

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 278.27 | Martin's coat on | -8 ms | -23.7 | -36.2 LUFS |

### keys_jingle

Source: `One Shots/Drums/Misc Percussion/Perc Jingle.wav`

Processing: two overlapping handfuls of the jingle (+-0.5 st), HP 500 Hz, LP 6 kHz; off-screen: workshop room 70 %, panned left, low

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 279.07 | Martin's keys | +0 ms | -16.0 | -25.9 LUFS |

### door_shop

Source: `One Shots/Drums/Wood/Wood Rough Low.aif`; `One Shots/FX/Foley Door Lock.wav`

Processing: a door = its wooden body (rough low wood -7 st, LP 1.2 kHz) + the latch (the lock's bolt, LP 5 kHz); the back-office door, then 1.7 s later the shop door, bigger, darker (LP 2.5 kHz), further off (90 % room)

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 283.49 | the back-office door, then the shop door (o.s.) | -2 ms | -16.0 | -27.9 LUFS |

### street_night

Source: synth: traffic; `Loops/Texture/Wind Air God.wav`

Processing: sparser traffic (synth) + night air (wind, LP 2.5 kHz); LP 4.5 kHz

| from | to | level | label |
|---|---|---|---|
| 284.19 | 306.55 | 1.0 x 0.0039 RMS | a quieter street outside in Lisbon (bed) |

### door_lisbon

Source: `One Shots/Drums/Wood/Wood Rough Low.aif`; `One Shots/FX/Foley Door Lock.wav`

Processing: the same door, smaller, LP 3.5 kHz, off in Theo's flat (Lisbon room 70 %), right

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 289.70 | the studio door (o.s.) | -2 ms | -15.0 | -29.7 LUFS |

<!-- generated by check.py --sound-md: end -->

## What could be better

- In the dense opening (tabs every 0.34 s with drive chatter between them) the onset column can show a neighbouring
  click; each sound is placed on its cue by construction (the first transient of the clip on the cue time).
- The time-lapse swell and the compressor rise slowly by design and are not timed by onset.
- The grid is locked to the tab change, so the build starts on the first bar line after `marks.code` (2.2 s later), and
  Tuesday's soft picking 1.3 s after its cut (one strum rings over it). "Fussy." has the least clearance (9.5 dB), with
  the build's top bar under it even after the score steps back.
- No shutter, door, coat or breath recordings exist in the library: the shutter and the doors are built from metal and
  wood hits and the lock's bolt; the coat from a paper rustle and soft maracas (kept quiet, off-screen); the chair's breath
  out is the tail of a breath riser, kept low under Martin's own sigh.
- The film-pace voices peak harder: the limiter takes up to 2.4 dB on a few plosives. The loudness range is 12.2 LU
  (long, quiet openings by design).

- The library has no road traffic, so Lisbon's street is part synthesis; it sits low, behind people and birds.
- The radio (scene 1 only) is the library's `Radio Station Search` through a small speaker in another room: very low,
  so it reads as a radio rather than as a programme.
