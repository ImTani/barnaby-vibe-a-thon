# Barnaby: the soundtrack

`video/v2/audio/soundtrack.wav` (48 kHz stereo, the cue sheet's length: 300.05 s for the v2.3 timing, Barnaby at 185 words a minute, with the 6 s end card) and its stems `music.wav` + `sfx.wav` +
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
| integrated loudness | -16 LUFS | -16.0 LUFS (ffmpeg ebur128), -16.08 (pyloudnorm) |
| true peak | <= -1 dBTP | -1.8 dBTP (ffmpeg, 4x), -1.8 dBTP (4x polyphase) |
| loudness range | - | 17.9 LU |
| format | 48 kHz stereo | 48000 Hz, 2 ch, PCM_16, 302.69 s (film 302.69 s) |
| music + effects + ambience + voice = soundtrack | exact | max difference -76.3 dBFS (dither) |
| sfx.wav = effects + ambience | exact | max difference -84.3 dBFS (dither) |
| stems, integrated | - | music -27.5 LUFS, effects -27.8 LUFS, ambience -37.4 LUFS, voice -15.0 LUFS |
| dialogue over everything under it | always clear | min 9.5 dB (line 17), median 17.1 dB over 54 lines (RMS in each line's speech window) |
| voices, level per speaker | consistent | Martin -14.7 LUFS (-16.4..-13.6, 18 lines, cached); Theo -16.0 LUFS (-17.5..-15.2, 10 lines, cached); Barnaby -14.3 LUFS (-15.6..-13.2, 23 lines, take); Priya -14.2 LUFS (-14.3..-14.0, 3 lines, cached) |
| effects on their cues | on the cue | 93 one-shots: median 2 ms, max 32 ms from cue to the first rise in the effects stem |

## Levels by category, against the dialogue

Each category re-rendered alone with the mix's ducking and master gain. The dialogue's reference: its typical short-term (3 s) level -16.7 LUFS and typical momentary (400 ms) level -15.5 LUFS while someone speaks (voice stem: peak -1.2 dBFS, integrated -15.0 LUFS). Targets: beds -14 to -20 LU under the dialogue (short-term max), the opening's rain and fan at the quiet end; foley and UI never louder than a voice (momentary max under the dialogue's typical momentary level).

| category | peak dBFS | short-term max LUFS (vs dialogue) | momentary max LUFS (vs dialogue) | integrated while playing LUFS (vs dialogue) |
|---|---|---|---|---|
| rain | -25.6 | -35.3 (-18.6 LU) | -35.1 (-19.6 LU) | -38.6 (-21.9 LU) |
| fan (2009 PC) | -30.1 | -40.0 (-23.3 LU) | -38.3 (-22.8 LU) | -42.2 (-25.5 LU) |
| radio (scene 1) | -32.6 | -46.1 (-29.4 LU) | -42.4 (-26.9 LU) | -48.0 (-31.3 LU) |
| room tone (back office) | -29.4 | -40.9 (-24.2 LU) | -40.0 (-24.5 LU) | -43.3 (-26.6 LU) |
| workshop | -17.8 | -31.9 (-15.2 LU) | -29.0 (-13.5 LU) | -39.5 (-22.8 LU) |
| workshop, Tuesday | -13.6 | -32.6 (-15.9 LU) | -29.0 (-13.5 LU) | -36.9 (-20.2 LU) |
| Lisbon street | -24.0 | -34.0 (-17.3 LU) | -33.8 (-18.3 LU) | -37.7 (-21.0 LU) |
| Lisbon street, night | -23.5 | -34.5 (-17.8 LU) | -32.9 (-17.4 LU) | -37.7 (-20.9 LU) |
| foley | -3.3 | -28.7 (-12.0 LU) | -22.1 (-6.6 LU) | -30.0 (-13.3 LU) |
| UI (clicks, reload, pops, ding) | -8.8 | -29.6 (-12.9 LU) | -21.8 (-6.3 LU) | -31.9 (-15.2 LU) |
| worlds (steps, chimes, drawer, soft bells, swell) | -11.0 | -23.9 (-7.2 LU) | -19.8 (-4.3 LU) | -25.4 (-8.7 LU) |
| the bell | -5.5 | -24.5 (-7.8 LU) | -16.5 (-1.0 LU) | -23.4 (-6.7 LU) |

## Key moments (excerpts in .cache/audio/excerpts/)

| moment | excerpt | excerpt loudness | at the event: peak / loudest 400 ms | stems RMS at the event (dBFS) |
|---|---|---|---|---|
| s2_bell_arrival | 44.35-50.35 s | -17.6 LUFS | -5.3 dBFS / -16.3 LUFS | music -36.5, effects -22.5, ambience -37.1, voice -96.4 |
| s4_key_turn | 108.2-111.8 s | -18.6 LUFS | -3.4 dBFS / -22.4 LUFS | music -29.6, effects -31.4, ambience -42.8, voice -96.4 |
| s6_click_tab_change | 197.24-202.24 s | -20.2 LUFS | -6.5 dBFS / -19.4 LUFS | music -37.8, effects -35.9, ambience -46.9, voice -25.0 |
| s9_final_bell | 286.49-292.49 s | -24.8 LUFS | -6.6 dBFS / -16.7 LUFS | music -28.0, effects -23.1, ambience -37.2, voice -96.4 |

## Effect cues: source and processing

Core Library paths are under `C:/ProgramData/Ableton/Live 12 Suite/Resources/Core Library/Samples/`. Measured: onset = cue to the first rise in the effects stem; peak and loudest 400 ms of the effects stem alone (0-0.6 s after the cue; overlapping sounds count).

### rain

Source: `Loops/Texture/Rain and Train.wav`

Processing: rain on the window: random 7-15 s stretches of the steady rain (2 s crossfades), HP 110 Hz, LP 7.5 kHz, -3 dB shelf above 2.5 kHz (the glass), gentle peak compression

| from | to | level | label |
|---|---|---|---|
| 0.00 | 75.62 | 1.0 x 0.006 RMS | rain on the window (bed) |
| 272.57 | 302.69 | 0.8 x 0.006 RMS | rain returns over the shop (bed; leads the cut) |

### office_night

Source: synth: room tone; `Loops/Texture/Machine Noise Ambient.wav`

Processing: a low room tone (synth: brown noise LP 160 Hz) with the machine loop -5 st LP 400 Hz under it

| from | to | level | label |
|---|---|---|---|
| 0.00 | 75.62 | 1.0 x 0.005 RMS | the back office at night (derived: scenes 1-2) |
| 273.57 | 302.69 | 0.8 x 0.005 RMS | the back office at night (derived: scene 9) |

### radio

Source: `Loops/Texture/Radio Station Search.wav`

Processing: the radio recording through a small speaker (BP 450 Hz-3 kHz, +4 dB at 1.1 kHz, soft saturation, LP 2.4 kHz), panned right, very low

| from | to | level | label |
|---|---|---|---|
| 0.40 | 74.62 | 0.55 x 0.0035 RMS | a radio far off in the workshop (bed) |

### fan

Source: `Loops/Texture/Machine Noise Ambient.wav`

Processing: the machine loop varispeeded up from 25 % over 1.6 s (the fan spinning up), BP 70 Hz-3.2 kHz, panned left

| from | to | level | label |
|---|---|---|---|
| 0.60 | 75.22 | 1.0 x 0.004 RMS | PC fan spins up, then hums (bed) |

### hdd

Source: `One Shots/Drums/Misc Percussion/Perc Tiny.wav`

Processing: 10 ms grains of the tiny perc (-3..+2 st) at irregular seek intervals, HP 400 Hz, LP 6.5 kHz, a +5 dB resonance at 900 Hz (the drive cage); under the desk, left; office room 12 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 4.20 | hard drive chatter | +0 ms | -20.2 | -36.1 LUFS |
| 15.55 |  | -30 ms | -19.1 | -34.2 LUFS |
| 18.10 |  | -30 ms | -19.5 | -35.9 LUFS |
| 19.80 |  | -30 ms | -19.4 | -33.2 LUFS |

### tab

Source: `One Shots/Drums/Wood/Wood Insert Cassette.wav`; `One Shots/Drums/Misc Percussion/Click Vinyl.wav`

Processing: old shop mouse: the cassette's latch (from 46 ms) -1 st (down) + vinyl click +4 st 85 ms later (up); HP 380 Hz, LP 9 kHz, +3 dB at 2.6 kHz; fast peak compressor; a little width; office room 22 %; pan follows the tab a little

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 13.80 |  | -8 ms | -14.0 | -34.5 LUFS |
| 14.65 |  | -8 ms | -13.9 | -34.5 LUFS |
| 15.50 |  | -8 ms | -13.7 | -32.3 LUFS |
| 16.35 |  | -8 ms | -13.6 | -34.5 LUFS |
| 17.20 |  | -8 ms | -13.6 | -34.5 LUFS |
| 18.05 |  | -8 ms | -13.5 | -32.3 LUFS |
| 18.90 |  | -8 ms | -13.4 | -34.6 LUFS |
| 19.75 |  | -8 ms | -13.3 | -31.1 LUFS |
| 20.60 |  | -8 ms | -13.2 | -34.5 LUFS |
| 24.79 |  | -8 ms | -15.6 | -36.5 LUFS |
| 25.63 |  | -8 ms | -16.7 | -37.5 LUFS |

### radio_off

Source: `One Shots/Drums/Misc Percussion/Click Vinyl.wav`; `One Shots/Drums/Wood/Wood Insert Cassette.wav`

Processing: a dry switch: vinyl click -2 st + the cassette latch -5 st, HP 300 Hz, LP 6 kHz; through the workshop door (workshop room 60 %, right); the radio bed stops on it

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 29.28 | the workshop radio clicks off (o.s.) | -2 ms | -14.3 | -33.5 LUFS |

### shutter

Source: `One Shots/Drums/Misc Percussion/Perc Metallic Clatter.aif`; `Loops/Texture/Machine Noise Ambient.wav`; `One Shots/FX/Impact Short Metal.wav`

Processing: the metallic clatter -5 st, looped (forward, reversed) to the cue's length and pulsed at 9-14 slats a second, BP 250 Hz-4.5 kHz, a little rumble (machine loop -8 st LP 300 Hz), and the bottom bar landing (metal impact -4 st, LP 3.5 kHz) at the end; off-screen: workshop room 85 %, right, low

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 29.78 | Martin pulls the shop shutter down for the night (o.s.) | +14 ms | -12.0 | -23.5 LUFS |

### tab_close

Source: `One Shots/Drums/Wood/Wood Insert Cassette.wav`; `One Shots/Drums/Misc Percussion/Click Vinyl.wav`

Processing: as tab, a little lighter

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 40.15 |  | -8 ms | -15.6 | -37.0 LUFS |
| 40.55 |  | -8 ms | -15.7 | -36.9 LUFS |
| 40.95 |  | -8 ms | -15.7 | -36.9 LUFS |
| 41.35 |  | -8 ms | -15.9 | -36.9 LUFS |
| 41.75 |  | -8 ms | -15.9 | -37.0 LUFS |
| 42.40 |  | -8 ms | -16.0 | -37.1 LUFS |
| 43.05 |  | -8 ms | -16.2 | -37.2 LUFS |
| 43.70 |  | -8 ms | -16.3 | -37.0 LUFS |
| 44.35 |  | -8 ms | -16.3 | -37.1 LUFS |

### bell

Source: `One Shots/Drums/Bell/Bell Cash.aif`; modal ring (fitted to the sample)

Processing: the counter bell: Bell Cash tuned +0.3 st to E6; the recording's strike for 0.2 s, then a modal ring fitted to its own four partials (1318, 1998, 3009, 8700 Hz: amplitude and phase measured at 0.2 s; T60 5.0, 1.8, 3.4, 1.0 s; slow doublet beats), a raised-cosine hand-over over 0.25 s with the recording kept at 30 % under it; HP 400 Hz; office room 35 % (50 % for the last bell) plus an air halo in the world room; the score ducks 3 dB for the last one

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 45.85 | the brass bell: Barnaby arrives | +0 ms | -5.5 | -16.4 LUFS |
| 287.99 | the real bell, once | +0 ms | -7.1 | -17.1 LUFS |

### pop

Source: `One Shots/Drums/FX Hit/FX Drip 2.wav`

Processing: a water drip tuned up the D major pentatonic, LP 4.2 kHz, HP 250 Hz; six rising pops 75 ms apart for 'six light up', two for 'two rows change'; world room 40 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 55.74 | six light up | -4 ms | -13.5 | -25.4 LUFS |
| 117.32 | order 3 lands | -4 ms | -14.2 | -29.3 LUFS |
| 212.56 | two rows change | -4 ms | -14.2 | -26.5 LUFS |

### key_tap

Source: `One Shots/Drums/Misc Percussion/Foley Coin LDre.wav`; `One Shots/Drums/Misc Percussion/Perc Plastic 2.wav`

Processing: the coin's first impact only (45-200 ms: the ring damped by the keys), HP 900 Hz, on a plastic tap -2 st LP 5 kHz; fast compressor; office room 18 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 70.07 | the key on the keyboard: a small clean metal tap | -4 ms | -9.9 | -28.7 LUFS |

### lamp_click

Source: `One Shots/Drums/Wood/Wood Insert Cassette.wav`; `One Shots/Drums/Misc Percussion/Click Vinyl.wav`

Processing: vinyl click +2 st, then the cassette latch -4 st 12 ms later; HP 250 Hz, LP 8 kHz, +2 dB at 1.8 kHz; fast compressor; panned left (the lamp); office room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 72.42 | the lamp clicks off | -2 ms | -10.1 | -30.9 LUFS |

### timelapse

Source: `One Shots/FX/Swell Short Noise.wav`; `One Shots/FX/Bowl Swell B1.aif`

Processing: a noise swell varispeeded to the cue's length, LP 4.5 kHz, with a singing bowl +3 st (B -> D) LP 1.5 kHz; world room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 74.02 | time passes: a soft swell | (swell or derived: not timed) | | |

### workshop

Source: synth: room tone; `Loops/Texture/Nuts and Bolts.wav`

Processing: room tone (synth) + tools now and then (the parts trays: nuts and bolts, BP 300 Hz-5 kHz, peak-compressed, on a slow random gate ~25 % on, peak-compressed hard so no clink pokes out); no voices, no radio

| from | to | level | label |
|---|---|---|---|
| 76.02 | 215.76 | 1.0 x 0.0065 RMS | workshop morning bed: room, radio, tools |

### freewheel

Source: `One Shots/Drums/Misc Percussion/Perc Tiny.wav`

Processing: 12 ms grains of the tiny perc +6 st at 24 Hz slowing to 5 Hz, HP 1.5 kHz; off-screen: workshop room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 78.22 |  | +0 ms | -15.1 | -27.6 LUFS |

### chair

Source: `One Shots/Drums/Misc Percussion/Perc Hit Soft.aif`; `One Shots/Drums/Wood/Wood Rough Low.aif`; `One Shots/Drums/FX Hit/FX Squeak.aif`; `One Shots/FX/Riser Taka Breath.wav`

Processing: the cushion (soft hit -8 st LP 500 Hz), the seat's creak (rough wood -5 st LP 2.5 kHz), the spring's squeak -7 st LP 4 kHz, and a breath out 0.45 s later (the breath riser's tail, BP 250 Hz-2.8 kHz); office room 20 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 78.62 | a chair creaks: Martin sits, a breath out | -30 ms | -15.1 | -27.8 LUFS |

### compressor

Source: `Loops/Texture/Machine Noise Ambient.wav`; `Loops/Texture/Sink Noise.wav`

Processing: a 1.2 s run: the machine loop varispeed-spun up (0.55 -> 1.0 in 0.35 s), LP 2.2 kHz, a 9-24 Hz chug, air hiss (sink noise, BP 1.2-6 kHz); off-screen: workshop room 80 %, panned right

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 86.12 |  | (swell or derived: not timed) | | |

### step

Source: `One Shots/Drums/Misc Percussion/Perc Hit Soft.aif`; `One Shots/Instrument/Mallets/Marimba Cloth C3.aif`

Processing: a soft hit -5 st LP 1.4 kHz + a cloth-mallet marimba note an octave down (D or A, alternate feet) LP 900 Hz; Barnaby's world room 30 %; alternate pan +-0.08 (the marimba is on D or A)

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 87.67 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | -2 ms | -19.6 | -35.2 LUFS |
| 88.13 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | -2 ms | -19.6 | -34.7 LUFS |
| 88.58 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | +0 ms | -21.4 | -36.9 LUFS |
| 89.04 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | -1 ms | -21.4 | -36.3 LUFS |
| 89.49 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | -1 ms | -21.4 | -36.6 LUFS |
| 89.95 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | -1 ms | -21.4 | -36.1 LUFS |
| 90.41 | Barnaby walks the workshop floor to drawer 1 (derived from marks.walk, marks.pads_callout) | -1 ms | -23.2 | -38.3 LUFS |
| 129.48 |  | -2 ms | -11.8 | -23.0 LUFS |
| 129.93 |  | +0 ms | -12.2 | -22.3 LUFS |
| 130.38 |  | +0 ms | -12.0 | -20.8 LUFS |
| 130.83 |  | +0 ms | -12.0 | -19.8 LUFS |
| 132.97 |  | -2 ms | -12.7 | -22.6 LUFS |
| 133.23 |  | +0 ms | -11.0 | -21.2 LUFS |
| 133.49 |  | +0 ms | -11.0 | -19.8 LUFS |
| 133.75 |  | +0 ms | -11.0 | -21.0 LUFS |
| 136.12 | Barnaby's walk 3, quicker (derived from marks.walk3) | -2 ms | -12.2 | -20.6 LUFS |
| 136.29 | Barnaby's walk 3, quicker (derived from marks.walk3) | +1 ms | -12.2 | -20.0 LUFS |
| 136.46 | Barnaby's walk 3, quicker (derived from marks.walk3) | +0 ms | -12.5 | -20.0 LUFS |
| 136.63 | Barnaby's walk 3, quicker (derived from marks.walk3) | -1 ms | -12.5 | -22.2 LUFS |

### drawer

Source: `One Shots/Drums/Misc Percussion/Perc Wood Scratch.aif`; `One Shots/Drums/Wood/Wood Dry Low.aif`

Processing: the wood scratch -7 st (a slow slide, LP 3.5 kHz, rising) and a dry wood knock -3 st as it stops; world room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 93.95 | drawer 1 of the parts cabinet slides open in the shelf shot (derived from marks.shelf) | +0 ms | -15.4 | -29.5 LUFS |

### mouse_click

Source: `One Shots/Drums/Wood/Wood Insert Cassette.wav`; `One Shots/Drums/Misc Percussion/Click Vinyl.wav`

Processing: the shop: as tab (the old shop mouse). Lisbon: Theo's modern mouse, +2.5 st, shorter, HP 600 Hz, +3 dB at 3.4 kHz, Lisbon room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 108.82 |  | -8 ms | -8.8 | -29.7 LUFS |
| 116.52 |  | -8 ms | -11.1 | -32.1 LUFS |
| 128.09 |  | -8 ms | -11.8 | -33.0 LUFS |
| 128.84 |  | -8 ms | -11.9 | -32.9 LUFS |
| 198.24 |  | -8 ms | -10.1 | -31.0 LUFS |
| 251.54 | Connect | -8 ms | -9.9 | -31.9 LUFS |

### key_turn

Source: `One Shots/FX/Foley Door Lock.wav`

Processing: the lock recording as is (lead-in trimmed): the key in, the turn, the bolt; HP 140 Hz, LP 11 kHz, -2 dB at 3.2 kHz; fast compressor; office room 25 %; the score ducks 5 dB around it

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 109.30 | a real key turning in a lock | -6 ms | -3.3 | -24.0 LUFS |

### bell_soft

Source: `One Shots/Drums/Bell/Bell Cash.aif`; modal ring (fitted to the sample)

Processing: the same bell, its strike rounded (12 ms attack) and darker (LP 3.8 kHz), lower, world room 70 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 110.20 | the bell's soft confirm | +0 ms | -13.5 | -21.5 LUFS |
| 145.95 | the passage opens | -32 ms | -19.1 | -26.2 LUFS |
| 201.64 | a new room | +0 ms | -14.0 | -22.0 LUFS |

### clunk

Source: `One Shots/Drums/Misc Percussion/Perc Hit Hard.aif`; `One Shots/FX/Impact Short Metal.wav`; `One Shots/Drums/Misc Percussion/Perc Pan.wav`

Processing: the lever's crack (hit, +-1 st) + the jaw's clunk (metal impact -2 st, 35 ms later) + a short pan ring; HP 70 Hz, LP 5 kHz; off-screen: workshop room 75 %, panned right, low

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 121.12 | repair stand clamp releases: Sofia's | -2 ms | -11.8 | -22.0 LUFS |
| 131.78 | Kwame's | -2 ms | -13.6 | -23.9 LUFS |
| 134.45 | Jana's | -2 ms | -12.8 | -23.2 LUFS |
| 147.55 | Tom's Brompton | -2 ms | -12.6 | -23.7 LUFS |

### chime

Source: `One Shots/Instrument/Mallets/Celeste C6.wav`

Processing: the hand-back figure, one note per step: the celeste tuned to D5, F#5, A5, D6 (-10, -6, -3, +2 st), cut to 1.2x the step interval (0.54 s, 0.31 s, 0.2 s), LP 6 kHz; panned left to right across the four stops; world room 35 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 129.48 | hand-back chime 1/4 (the job), walk 1 | -2 ms | -11.8 | -23.0 LUFS |
| 129.93 | hand-back chime 2/4 (the customer), walk 1 | +0 ms | -12.2 | -22.3 LUFS |
| 130.38 | hand-back chime 3/4 (a text), walk 1 | +0 ms | -12.0 | -20.8 LUFS |
| 130.83 | hand-back chime 4/4 (the status), walk 1 | +0 ms | -12.0 | -19.8 LUFS |
| 132.97 | hand-back chime 1/4 (the job), walk 2 | -2 ms | -12.7 | -22.6 LUFS |
| 133.23 | hand-back chime 2/4 (the customer), walk 2 | +0 ms | -11.0 | -21.2 LUFS |
| 133.49 | hand-back chime 3/4 (a text), walk 2 | +0 ms | -11.0 | -19.8 LUFS |
| 133.75 | hand-back chime 4/4 (the status), walk 2 | +0 ms | -11.0 | -21.0 LUFS |
| 136.12 | hand-back chime 1/4 (the job), walk 3 | -2 ms | -12.2 | -20.6 LUFS |
| 136.29 | hand-back chime 2/4 (the customer), walk 3 | +1 ms | -12.2 | -20.0 LUFS |
| 136.46 | hand-back chime 3/4 (a text), walk 3 | +0 ms | -12.5 | -20.0 LUFS |
| 136.63 | hand-back chime 4/4 (the status), walk 3 | -1 ms | -12.5 | -22.2 LUFS |

### chime_chord

Source: `One Shots/Instrument/Mallets/Celeste C6.wav`

Processing: the four notes at once (D5 F#5 A5 D6), 2.6 s, LP 6 kHz; world room 45 %; replaces the passage's soft bell

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 145.90 | the passage: the four notes as one chord | -2 ms | -15.9 | -25.6 LUFS |
| 149.29 | Tom's Brompton in one step: the chord once | -2 ms | -18.1 | -27.8 LUFS |

### lamp_on

Source: `One Shots/Drums/Wood/Wood Insert Cassette.wav`; `One Shots/Drums/Misc Percussion/Click Vinyl.wav`

Processing: as lamp_click (another take of the same switch)

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 153.87 | the desk lamp clicks on: dusk, Martin at Theo's desk | -2 ms | -10.2 | -31.0 LUFS |

### typing

Source: `One Shots/Drums/Misc Percussion/Perc Plastic 1.wav`; `One Shots/Drums/Misc Percussion/Perc Plastic 2.wav`; `One Shots/Drums/Wood/Wood Prod Soft.wav`

Processing: the old keyboard: plastic taps (two samples, +-1.5 st; the space bar -3 st and louder) with a soft wooden upstroke +3 st 70-110 ms later; word gaps; HP 220 Hz, LP 9 kHz, -7 dB at 500 Hz (the samples' plastic ring), +2.5 dB at 2.2 kHz; office room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 174.45 | keyboard foley under the code | +0 ms | -12.3 | -29.6 LUFS |

### ding

Source: `One Shots/Instrument/Mallets/Celeste C6.wav`

Processing: the celeste on D (+2 st) with a quiet A above 70 ms later, LP 7 kHz; world room 45 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 180.25 | checks pass | -2 ms | -15.1 | -21.7 LUFS |

### reload

Source: `One Shots/Drums/Misc Percussion/Perc Tiny.wav`; `Loops/Texture/Machine Noise Ambient.wav`

Processing: a 0.55 s burst of the drive's seeks + the fan bed rising and falling over 1.8 s

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 198.64 | the page reloads | +0 ms | -15.9 | -32.0 LUFS |

### bustle

Source: synth: room tone; `Loops/Texture/Nuts and Bolts.wav`; `Loops/Texture/Tea Cups.wav`

Processing: the same, busier (gate ~40 % on), and a mug now and then; no voices

| from | to | level | label |
|---|---|---|---|
| 214.16 | 240.54 | 1.0 x 0.009 RMS | Tuesday workshop bustle (bed; leads the cut) |

### street

Source: synth: traffic; `Loops/Texture/Forest Ambience.wav`

Processing: traffic below the window (synth: a rumble and passing cars, each a filtered noise swell with a slow pan) + birds (HP 1.5 kHz); LP 6 kHz (the window); no voices

| from | to | level | label |
|---|---|---|---|
| 239.24 | 274.17 | 1.0 x 0.008 RMS | Lisbon: street below the window (bed; leads the cut) |

### cup

Source: `Loops/Texture/Tea Cups.wav`

Processing: one clink from the tea-cups recording (2.865-3.35 s) and a small settle (3.935 s) 75 ms later, HP 350 Hz; Lisbon room 22 %

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 243.64 | an espresso cup set down on its saucer | -2 ms | -12.2 | -29.4 LUFS |

### keys_modern

Source: `One Shots/Drums/Misc Percussion/Perc Plastic 1.wav`; `One Shots/Drums/Misc Percussion/Perc Plastic 2.wav`

Processing: Theo's modern keyboard: the same taps -4 st, 50 ms long, LP 3.8 kHz, -7 dB at 380 Hz, quicker, no upstroke; Lisbon room

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 246.04 | Theo types the name, pastes the repo path, types the URL | +6 ms | -15.2 | -33.0 LUFS |

### coat

Source: `Loops/Texture/Paper LDre.wav`; `One Shots/Drums/Shaker/Shake Maracas Soft.aif`

Processing: the paper rustle -4 st LP 3 kHz (cloth) between two sleeve swishes (soft maracas -10 st LP 2.2 kHz); off-screen: workshop room 45 %, left, low

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 274.57 | Martin's coat on | -8 ms | -22.6 | -35.0 LUFS |

### keys_jingle

Source: `One Shots/Drums/Misc Percussion/Perc Jingle.wav`

Processing: two overlapping handfuls of the jingle (+-0.5 st), HP 500 Hz, LP 6 kHz; off-screen: workshop room 70 %, panned left, low

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 275.37 | Martin's keys | +0 ms | -14.6 | -24.6 LUFS |

### door_shop

Source: `One Shots/Drums/Wood/Wood Rough Low.aif`; `One Shots/FX/Foley Door Lock.wav`

Processing: a door = its wooden body (rough low wood -7 st, LP 1.2 kHz) + the latch (the lock's bolt, LP 5 kHz); the back-office door, then 1.7 s later the shop door, bigger, darker (LP 2.5 kHz), further off (90 % room)

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 279.37 | the back-office door, then the shop door (o.s.) | -2 ms | -14.9 | -26.4 LUFS |

### street_night

Source: synth: traffic; `Loops/Texture/Wind Air God.wav`

Processing: sparser traffic (synth) + night air (wind, LP 2.5 kHz); LP 4.5 kHz

| from | to | level | label |
|---|---|---|---|
| 280.07 | 302.69 | 1.0 x 0.0065 RMS | a quieter street outside in Lisbon (bed) |

### door_lisbon

Source: `One Shots/Drums/Wood/Wood Rough Low.aif`; `One Shots/FX/Foley Door Lock.wav`

Processing: the same door, smaller, LP 3.5 kHz, off in Theo's flat (Lisbon room 70 %), right

| cue (s) | label | onset | peak dBFS | loudest 400 ms |
|---|---|---|---|---|
| 285.84 | the studio door (o.s.) | -2 ms | -13.7 | -28.4 LUFS |

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
