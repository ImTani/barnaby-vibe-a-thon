# Speech in the v2 film: pace, pauses, and why "for me" came apart

Read with `WORLD.md` (who speaks and how). This file is the source for the pace targets that
`video/audio/voices.py` renders to, and the record of the "Look after them | for me" fix in `voice/tts.py`.

Director's notes this answers:
1. "All of the speech is a little too slow. Rather than an arbitrary +30%, look up actual speeds of people
   speaking, decide which speed suits which sentence by which person, and model the speech appropriately."
2. "In Theo's first line I could hear 'for me' being delivered explicitly differently than 'look after them'."

## 1. What the research says

### How fast people talk
| Measure | Figure | Source |
|---|---|---|
| American English telephone conversation, whole conversations | 196 wpm; 236 wpm with silences removed ("net"); 164 wpm summed per turn | Yuan, Liberman & Cieri 2006 (Switchboard) |
| Talking to family and friends vs to strangers | 214 ± 7 wpm vs 193 ± 1 wpm (shorter turns with intimates) | Yuan et al. 2006 (CallHome vs Fisher) |
| Topic effect | 152 to ~170 wpm by topic; "important or unexpected" turns are longer and slower | Yuan et al. 2006 |
| Age and sex | older speakers slower; men ~2% faster than women | Yuan et al. 2006 |
| Young adults, conversation vs reading aloud | 183 wpm (SD 17) vs 220 wpm (SD 37); rates fall with age | Duchin & Mysak 1987, as quoted on the Auditory list |
| British English, conversation | ~260 syllables/min = 4.3 syl/s, pauses included; normal range ~130-220 wpm; lectures slower; prepared speech and holding the floor slow people down | Tauroza & Allison 1990 (260 syl/min as reported by Plug et al. 2021; the range and genre notes from secondary summaries) |
| British radio news | 168 wpm (BBC bulletins) | Rodero, cited in Wikipedia "Speech tempo" |
| Typical English | about 4 syllables/s | Cruttenden 2014, *Gimson's Pronunciation of English* |
| Across emotional and social contexts | 3.3 to 5.9 syl/s | Arnfield et al. 1995 |
| Young men, Southern Standard British English, fluent stretches (articulation rate: no pauses at all) | 6.55 syl/s canonical, 6.21 surface; US men ~5 | Plug, Lennon & Gold 2021 (DyViS, after Gold 2014) |
| Audiobook narration | ~150-160 wpm (ACX/Audible estimate at ~150) | industry convention, not research |

### Rate by emotion and by utterance length
- **Emotion** (Murray & Arnott 1993, as tabulated by Breazeal 2001): anger *slightly faster*, fear *much faster*,
  joy *faster or slower*, sorrow *slightly slower*, disgust *very much slower*, surprise *much faster*. "Speech is faster
  with higher arousal and slower with lower arousal… faster speech is accompanied with shorter pauses."
- **Length:** per word, rate rises steeply from 1-word to ~7-word turns (final lengthening and anticipatory
  shortening), stays level from about 8 to 30 words, then rises slowly (Yuan et al. 2006). One-word answers are
  slow per word; that is normal, not a fault.
- **Word length:** wpm counts a "yes" and a "workload" alike. Measured in syllables, Tauroza & Allison found radio,
  interviews and conversation alike and only lectures slower: syllables are the steadier unit. But unstressed
  syllables are short in English, so a line of long words is not proportionally slower either.

### Pauses
| Pause | Figure | Source |
|---|---|---|
| Read English, the two pause classes | brief ≈ 126 ms (7%), medium ≈ 512 ms (93%); none over 1 s in reading | Campione & Véronis 2002 |
| Spontaneous speech | the same classes, shorter (78 and 426 ms in French), plus long pauses ≈ 1.6 s | Campione & Véronis 2002 |
| Within one speaker, task dialogue (HCRC Map Task, Scottish English) | median 580 ms (geometric mean 632 ms) | Heldner & Edlund 2010 |
| Between speakers | Map Task gaps median 470 ms; counting overlaps, the commonest transition in all three corpora studied is a gap of ~200 ms; ~40% of speaker changes overlap (Spoken Dutch Corpus) | Heldner & Edlund 2010 |
| What a listener notices | gaps under ~200 ms go unnoticed; silences under 200 ms are hard to tell from stop closures | Heldner & Edlund 2010; Campione & Véronis 2002 |
| Pause vs phrase length | longer around longer phrases (the two lengths interact); pauses under 300 ms almost only between short phrases (≲ 10 syllables) | Zvonik & Cummins 2003, as summarised by Kentner 2007 |
| Turn-taking across languages | silence between turns is minimised everywhere; language means differ by < 250 ms | Stivers et al. 2009 |

So: **sentence pauses inside a turn** belong in the medium class, short (~300 ms) between short sentences and
~500 ms between long ones. **Comma pauses** are brief (~100-200 ms) or just a boundary tone. **Speaker changes**
in natural talk are ~200 ms, and seldom more than half a second.

## 2. How we measure
`video/v2/speech_probe.py` (and `voices.py`, which imports it) measures every line the same way:
- **Active span:** from the first to the last 10 ms frame above -40 dB re the line's loudest frame. Leading and
  trailing silence is excluded. Pauses inside the line are included, as in the turn rates above.
- **Speaking rate (wpm):** spoken words ÷ active span. "twenty-three" and "say-so" count as two words;
  "Anika's" and "I've" count as one. This is the number the targets are written in.
- **Syllable rate (syl/s):** syllables counted from the phonemes Kokoro is given (one per vowel nucleus,
  `voice/tts.py: syllables`), ÷ active span.
- **Articulation rate:** syllables ÷ (active span − pauses of 100 ms or more).
- **Pauses:** internal silences of 60 ms or more below -40 dB. Thresholds change pause statistics (Campione &
  Véronis warn about this), so compare only numbers measured this way.

## 3. Pace table
Targets are line rates in wpm, measured as above. **target = character × situation × short line × word length**,
unless a cue line sets `"wpm"` itself.

| Character | Default wpm | Why |
|---|---|---|
| **Barnaby** | **170** | "Unhurried, never slow." Above narration (150-160) and the BBC bulletin (168), below everyday conversation (183-214). He speaks to employers: politeness, like talking to strangers, slows people slightly (Yuan). |
| **Theo** (31) | **195** | Quick and funny, talking to family (CallHome 214), young-adult conversation (183) plus his quickness. |
| **Martin** (61) | **180** | Older speakers are slower (Yuan; Duchin & Mysak), but he's busy and plain. His short sentences are already slower per word through the short-line factor. |
| **Priya** (24) | **190** | Young and sharp. Her dryness is a situation, below. |

| Situation (`"pace"` on a cue line) | × | Basis |
|---|---|---|
| neutral | 1.00 | |
| brisk (practical, busy, impatient) | 1.06 | higher arousal, faster (Murray & Arnott) |
| surprised | 1.08 | surprise "much faster" (Murray & Arnott) |
| tired / sighing | 0.92 | lower arousal, slower (Murray & Arnott) |
| wistful / sentimental | 0.92 | sorrow "slightly slower" (Murray & Arnott) |
| explain (a change, a number that matters) | 0.95 | important or unexpected content is slower (Yuan) |
| dry (deadpan aside) | 0.95 | a craft choice, not a finding: the beat lets the joke land |
| closing (tagline, goodnight) | 0.90 | prepared, declarative speech is slower (Tauroza & Allison) |

| Short line (words) | 1 | 2 | 3 | 4 | 5+ |
|---|---|---|---|---|---|
| × | 0.68 | 0.76 | 0.84 | 0.92 | 1.00 |

This follows Yuan's rise over 1 to 7 words. The exact steps are our fit; trust your ear over them.

**Word length:** × (1.3 ÷ the line's syllables per word)^0.5, kept within 0.8 to 1.2. 1.3 is the film's own
average (all v1.1 cue lines and the v2 script: 1.28). A line of pure monosyllables gets 1.14× the word rate, and
"You've had me do these four steps four times today…" (1.18 syllables per word) 1.05×. A line of two-syllable
words ("Every system deserves a butler") gets 0.8×. The square root splits the difference between a constant word rate and a constant syllable rate, because
unstressed syllables are short.

**Pauses scale with pace:** × 170 ÷ the character-and-situation wpm (0.8 to 1.2). Faster speakers pause less
(Murray & Arnott).

Typical results. These are wpm for an average-length line of five or more words; the syl/s figure follows at
1.3 syllables per word.

| | neutral | brisk | wistful / tired | dry / explain | closing |
|---|---|---|---|---|---|
| Barnaby | 170 (3.7 syl/s) | 180 | 156 | 162 | 153 |
| Theo | 195 (4.2 syl/s) | 207 | 179 | 185 | 176 |
| Martin | 180 (3.9 syl/s) | 191 | 166 | 171 | 162 |
| Priya | 190 (4.1 syl/s) | 201 | 175 | 181 | 171 |

These overall rates sit at or just under the 4.3 syl/s Tauroza & Allison measured in British conversation,
pauses included, with Barnaby the most measured.

### Situations given to the current cue lines (test copy `.demo/voice-v2/cues_paced.json`)
`video/cues.json` (v1.1) has no `pace` fields yet. The test copy uses these, from the scenes in `WORLD.md`:
- **01 Theo, wistful:** the handover. "Look after them for me" is the most sentimental line in the film.
- **03 and 05 Martin, brisk:** a working morning.
- **08 and 14 Barnaby, dry:** the "four times today" and "Twenty-four things" asides.
- **15 and 16 Barnaby, closing:** the tagline.
- **Everything else, neutral.**

When the v2 lines go into `cues.json`, give each one a `pace`, or a `wpm` where the director wants an exact number.

## 4. Pauses we generate (`voice/tts.py`)
- **Between sentences in a line:** audible silence = 0.26 s after "." or "!", or 0.34 s after "?", plus 8 ms per
  syllable of the two sentences either side, at most 0.70 s, × the pace factor above. That gives 0.29-0.40 s
  between short sentences and ~0.5 s between long ones (Zvonik & Cummins; Campione & Véronis). The silence is
  measured: the quiet already at the edges of each Kokoro sentence is subtracted, so the pause heard is the pause
  planned. Theo's line, re-rendered at its old speed: 380 ms planned, 380 ms measured. Across the new renders:
  380-460 ms (was 430-580 ms: a fixed 0.34/0.46 s plus the edges).
- **Commas, colons, semicolons:** Kokoro makes these inside the sentence, and they are the same before and after.
  - Commas are mostly just a boundary tone (no silence at -40 dB in "tomorrow, and", "pairs, from", "Yes, please",
    "endpoints, sir"). Where there is one it is 60-110 ms ("yet, but", "Barnaby,"), or 210 ms ("pads, and"):
    the brief class.
  - The colon in "short: Anika's" gives 320 ms and the semicolon in "twenty-three; I" 230 ms.

  We do not splice silence into a sentence: a cut inside one synthesis call breaks its prosody, which is the very
  fault in note 2.
- **Between speakers:** set by the cue sheet's timing, not here. For the animatic, natural back-and-forth (a "Yes."
  after "May I?") wants a 200-500 ms gap; much longer reads as hesitation.

## 5. Why "for me" came apart

### What tts.py sent to Kokoro
"Barnaby, this is the shop's system. Look after them for me." was split at the full stop into two Kokoro calls.
Each call was one batch: kokoro-onnx only cuts past 510 phonemes, and these are 34 and 26.

| Call | Phonemes (misaki, British) | Speed | Style row |
|---|---|---|---|
| 1 | `bˈɑːnəbi, ðɪs ɪz ðə ʃˈɒps sˈɪstɪm.` | 0.978 | for 34 phonemes |
| 2 | `lˈʊk ˈɑːftə ðˌɛm fɔː mˌiː.` | 0.998 | for 26 phonemes |

So "Look after them" and "for me" were **one call, one speed, one style**. Speed and jitter are applied per call,
not inside one. The two calls are stitched with zeros after trimming. kokoro-onnx 0.6.1's own pause inserter needs
a model with a duration output, and this one has none (`has_timings = False`), so it does nothing. **No splitting
or stitching happens inside the sentence.**

### What the waveform shows (`video/audio/voice/01_Theo.wav`, a bit-exact re-render)
Inside sentence 2 (2.61-4.17 s):
- "them" (3.29-3.54 s) is lengthened and falls to Theo's pitch floor: ~62 Hz, as at the end of a sentence.
- Then comes **digital silence, 3.60-3.70 s (about -81 dB), 130 ms below -55 dB**.
- Then "f-" and **"for me" restart a new phrase: 83 Hz flat, then falling, +12 dB louder.**

That is an intonation-phrase boundary, made by the model itself: "Look after them. | For me."

### What causes it
Probes are in `.demo/voice-v2/probe/`: `forensics.py`, `theo_grid.py`, `breaks*.py`. The longest internal silence
below -55 dB across 3 speeds × 2 style rows per voice:

| "them for me" as | lewis (Theo) | george | Barnaby blend | fable | daniel |
|---|---|---|---|---|---|
| misaki: `ðˌɛm fɔː mˌiː` | **170 ms** | **120 ms** | 10 | 0 | 0 |
| `ðˌɛm fə mi` (stressed "them" kept) | **150 ms** | **80 ms** | 10 | 0 | 0 |
| `ðəm fɔː mi` | 40 | 10 | 0 | 0 | 0 |
| `ðəm fə mˌiː` (what tts.py now sends) | 20 | 10 | 10 | 0 | 0 |
| `ðəm fə mi` | 20 | 10 | 10 | 0 | 10 |

- **Not speed:** the break is there at 0.90, 1.0, 1.1 and 1.2.
- **Not mainly the style row:** Kokoro picks a style vector by phoneme count, so a short sentence gets a
  short-utterance style. Giving every sentence the whole line's row (60) still breaks: 70 ms on Lewis. It only
  helped in the long v2 version of the line (~120). Across the corpus it moved flags around rather than
  removing them (`breaks.py`: 10 → 8 of 76, and one new).
- **It's the pronoun.** misaki's British lexicon stores function words in citation form: "them" `ðˌɛm` (a
  stress mark and a full vowel), "for" `fɔː`, "me" `mˌiː`. A stressed full-vowel "them" after the nucleus "after"
  is read by Kokoro as the last word of a phrase. It lengthens it, drops it to the floor and predicts a pause; "for
  me" then becomes its own phrase. A reduced "them" removes the break in every voice, speed and row tried.
  Reducing "for" too takes it to the 10-20 ms of an ordinary closure.
- **It's voice-dependent:** Lewis and George break, Fable and Daniel don't, and the Barnaby blend hardly does. So
  it showed up in Theo's line, but the same input could do it to anyone.

In spoken English, unstressed function words take their **weak forms**: "Look after them for me" is
/lʊk ˈɑːftə ðəm fə miː/ (Cruttenden; Wells). The fix is to send Kokoro what a speaker says.

### The fix (`voice/tts.py`)
- **Weak forms.** After misaki, each function word that misaki left without a primary stress, and that has another
  word after it in the phrase, takes its RP weak form: them ðəm, me mi, him hɪm, her hə, us əs, for fə, from fɹəm,
  of əv, at ət, and ənd, but bət, can kən, was wəz, were wə, are ə.
  - The weak form works on misaki's tokens, so "four" (`fˈɔː`) is never taken for "for".
  - RP linking r is kept: "for a" is `fəɹ ɐ`.
  - Strong forms stay where English keeps them: when stressed (`kˈan` in "the system can.") and when stranded
    before punctuation ("What's it for?").
  - Relative "that" was tried and dropped: weak `ðət` made Kokoro break before it ("the six | that only read",
    80-140 ms at speeds 0.85-1.05; misaki's `ðat` never did; `probe/that.py`).
  - "sir" is untouched: same phonemes, and the same level as before (-13.8 and -15.8 dB re the loudest frame;
    was -13.5 and -15.0), an unaccented tail after the nucleus.
    - In line 10 its contour is as before: 115 → 128 Hz, was 119 → 125.
    - In line 02, at the faster pace, it ends with a small lift: 112 → 143 Hz, was 126 → 117.

    Removing its stress mark made no consistent difference across speeds (`probe/sir.py`).
- **One sentence, one call.** The splitter used to cut mid-sentence at any full stop: "Ten pairs at £6.50 each."
  became "Ten pairs at £6." + "50 each." (two calls, a pause, two speeds and two styles). "Mr.", "e.g." and "v2.3"
  did the same. Sentences now end only at . ? ! followed by a space or the end, not after a title, not before a
  lower-case word, and "..." only before a capital. The cue lines never hit this, but the live bot, reading model
  text with prices and versions, would have.
- **Kept:** Barnaby's George 75% + Fable 25% blend, the lexicon, "?" in the text so yes/no questions rise, ±3%
  speed per sentence (deterministic), slightly slower questions and closing sentences.

Result across 76 sentences (the v1.1 cue lines and the v2 script lines, each in its character's voice):
`breaks3.py` flags a silence away from punctuation that is ≥ 100 ms below -55 dB, or ≥ 80 ms with a fall to
the pitch floor and a +2 st reset.

| Pipeline | Sentences flagged | Theo's "them \| for me" |
|---|---|---|
| old forms, old speeds (what the film has now) | 10 / 76 | flagged: 130 ms, 63 → 82 Hz, both versions of the line |
| new forms, old speeds | 8 / 76 | gone; nothing new flagged |
| new forms, the new paced speeds | 6 / 76 | gone |

The same line, four ways: the longest silence inside "Look after them for me" (-40 dB, `speech_probe.py`).

| | old speed (1.00) | new paced speed (1.06) |
|---|---|---|
| old forms `ðˌɛm fɔː mˌiː` | **170 ms** (`video/audio/voice/01_Theo.wav`) | **180 ms** (`.demo/voice-v2/theo/01_Theo_oldforms_newspeed.wav`) |
| new forms `ðəm fə mˌiː` | none (`.demo/voice-v2/theo/01_Theo_new_speed1.0.wav`) | none (`.demo/voice-v2/render/01_Theo.wav`) |

The remaining flags were there before this change and are not touched by it:
- "Barnaby, this is the | shop's system": 110 ms, no pitch reset;
- "Dev has thirty-one hours | booked against twenty": 140 ms, +9.5 st; 200 ms at -40 dB in the render;
- "Every system | deserves a butler": 100 ms, +6.2 st;
- "It's the one | with the spanner": 80 ms, +2.3 st;
- "Dev's carrying thirty-one hours | against his twenty": 120 ms, +6.8 st.

All of them fall at a syntactic boundary where a speaker may phrase. "endpoint | I" and "stock | count" were
flagged at the old speeds and are gone at the new ones.

## 6. Before and after (current cue lines)
Rendered by `voices.py --cues .demo/voice-v2/cues_paced.json --out .demo/voice-v2/render --compare
video/audio/voice`. Old = the files in `video/audio/voice/` now (speed 0.92 for Barnaby, 1.0 for the others),
measured the same way.

| # | who | line | pace | target wpm | speed | old wpm | new wpm | syl/s | old dur (s) | new dur (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Theo | Barnaby, this is the shop's system. Look after them for me. | wistful | 175 | 1.061 | 160 | 172 | 3.92 | 4.27 | 3.96 |
| 2 | Barnaby | Twenty-three endpoints, sir. I've started with the six that only read. | neutral | 168 | 1.091 | 141 | 165 | 3.66 | 5.35 | 4.55 |
| 3 | Martin | Which repairs are due tomorrow, and are we short on parts? | brisk | 193 | 1.0 | 186 | 191 | 4.06 | 3.67 | 3.56 |
| 4 | Barnaby | Five are due tomorrow. Only one is short: Anika's brake job needs two pairs of pads, and we have one. | neutral | 173 | 1.036 | 159 | 173 | 3.61 | 7.70 | 7.08 |
| 5 | Martin | Order ten pairs, from the usual supplier. | brisk | 174 | 1.282 | 144 | 175 | 4.17 | 3.03 | 2.52 |
| 6 | Barnaby | I can't yet, but the system can. There's an ordering endpoint I haven't taken. May I? | neutral | 165 | 1.141 | 131 | 164 | 3.93 | 7.53 | 5.99 |
| 7 | Martin | Yes. | neutral | 140 | 1.8 | 76 | 136 | 2.27 | 0.87 | 0.49 |
| 8 | Barnaby | You've had me do these four steps four times today. Shall I make it a single motion? | dry | 170 | 0.882 | 178 | 173 | 3.56 | 5.99 | 6.15 |
| 9 | Martin | Who's overloaded this week? | neutral | 143 | 1.25 | 111 | 141 | 4.12 | 2.30 | 1.81 |
| 10 | Barnaby | The system has no notion of workload, sir. I can teach it. | neutral | 173 | 1.06 | 149 | 172 | 3.58 | 4.97 | 4.34 |
| 11 | Barnaby | Dev has thirty-one hours booked against twenty. Shall I move the two wheel builds to Priya? | neutral | 170 | 0.981 | 156 | 173 | 3.57 | 6.80 | 6.13 |
| 12 | Martin | Yes, please. | neutral | 156 | 1.8 | 82 | 136 (off target) | 2.27 | 1.58 | 0.95 |
| 13 | Priya | What can this system actually do? | neutral | 177 | 0.937 | 185 | 180 | 4.5 | 2.22 | 2.26 |
| 14 | Barnaby | Twenty-four things. Theo wrote twenty-three; I wrote one more. | dry | 163 | 1.06 | 137 | 161 | 3.16 | 5.03 | 4.30 |
| 15 | Barnaby | Every system deserves a butler. | closing | 123 | 0.946 | 121 | 124 | 4.55 | 2.67 | 2.62 |
| 16 | Barnaby | Even the old ones. | closing | 144 | 0.837 | 161 | 144 | 3.59 | 1.73 | 1.94 |

- **Barnaby, neutral lines:** mean 147 → 169 wpm (+15%). Fitted speeds 0.98-1.14, median 1.06; was 0.92 for all.
- **All 16 lines:** 65.7 s → 58.7 s of speech. No line runs into the next cue (`render.log`).
- **On target:** 15 of 16 within ±2%. "Yes, please." is 13% slow at the speed ceiling (section 7).
- **Some lines are slower on purpose:**
  - 08 "four times today" is a dry aside of short words;
  - 16 "Even the old ones." is the closing tagline.

  Set `"wpm"` on the cue to overrule either.
- **Pauses between sentences:** 380-460 ms, was 430-580 ms.

**Listen** (16-bit WAV, 24 kHz):
- **Every line, new:** `.demo/voice-v2/render/NN_<who>.wav`.
- **Every line, old:** `video/audio/voice/NN_<who>.wav` (untouched).
- **Theo A/B:**
  - `video/audio/voice/01_Theo.wav` (old);
  - `.demo/voice-v2/theo/01_Theo_new_speed1.0.wav` (fix only, old pace);
  - `.demo/voice-v2/theo/01_Theo_oldforms_newspeed.wav` (pace only, no fix: the break is still there);
  - `.demo/voice-v2/render/01_Theo.wav` (both).
- **Measured rates:** `.demo/voice-v2/render/manifest.json` and `render.log`.

## 7. Open points
- **Martin's placeholder needs Kokoro's speed ceiling on very short replies.** Kokoro lengthens isolated one- and
  two-word replies far more than people do, so "Yes." and "Yes, please." need speed ~1.8 (our ceiling) and
  "Yes, please." still lands 13% slow. Tani's recorded takes replace these lines; `voices.py` measures takes but
  never re-times them.
- **Other model-made breaks remain where syntax allows one,** unchanged by this fix, and worth a listen:
  - "thirty-one hours | booked against twenty";
  - "Every system | deserves a butler";
  - "It's the one | with the spanner".

  Rewording is the cheapest cure if one jars ("Dev's booked for thirty-one hours…").
- **"sir" in line 02 now ends with a small lift** (a polite low rise) where it used to fall. If it reads as a
  question, give that cue a slightly lower `wpm`: at speed 0.94 the same "sir" fell (`probe/sir.py`).
- **The steps of the short-line factor, the word-length exponent and the dry factor are fitted or judged, not
  measured.** The defaults and the emotion directions are from the sources.
- **The live bot now speaks at `tts.BARNABY_SPEED = 1.06` (was 0.92),** the median speed the film fit chose for
  Barnaby's neutral lines. It also gets the weak forms and the sentence-splitting fix. `BarnabyKokoroTTS` takes
  its speed from `tts.BARNABY_SPEED`; the `BARNABY_SPEED` env var in `voice/bot.py` (default 0.95) only reaches
  pipecat's own settings, which the overridden `run_tts` doesn't read. Revert the constant if the bot should keep
  its old pace.

## Sources
- Arnfield, S., Roach, P., Setter, J., Greasley, P. & Horton, D. (1995). Emotional stress and speech tempo variability.
  *ESCA/NATO Workshop on Speech Under Stress*, 13-15. (Range quoted from Wikipedia, "Speech tempo".)
- Breazeal, C. (2001). Emotive qualities in robot speech. *IROS 2001* (Fig. 1 after Murray & Arnott 1993).
  https://groups.csail.mit.edu/lbr/mars/pubs/iros.pdf
- Campione, E. & Véronis, J. (2002). A large-scale multilingual study of silent pause duration. *Speech Prosody 2002*.
  (local copy `.demo/voice-v2/papers/campione2002.txt`)
- Cruttenden, A. (2014). *Gimson's Pronunciation of English*, 8th ed. Routledge. (rate, p. 54; weak forms)
- Duchin, S. W. & Mysak, E. D. (1987), as quoted at https://www.auditory.org/postings/2016/329.html (not read in the original).
- Heldner, M. & Edlund, J. (2010). Pauses, gaps and overlaps in conversations. *J. Phonetics* 38, 555-568.
  (local copy `.demo/voice-v2/papers/heldner2010.txt`)
- Kentner, G. (2007). *Interspeech 2007* (summarising Zvonik & Cummins).
  https://www.isca-archive.org/interspeech_2007/kentner07_interspeech.pdf
- Murray, I. R. & Arnott, J. L. (1993). Toward the simulation of emotion in synthetic speech: a review of the literature
  on human vocal emotion. *JASA* 93, 1097-1108.
- Plug, L., Lennon, R. & Gold, E. (2021). Articulation rates' inter-correlations and discriminating powers in an English
  speech corpus. *Speech Communication* 132, 40-54. https://eprints.whiterose.ac.uk/172033/
  (local copy `.demo/voice-v2/papers/plug2021.txt`)
- Stivers, T. et al. (2009). Universals and cultural variation in turn-taking in conversation. *PNAS* 106, 10587-10592.
  https://pubmed.ncbi.nlm.nih.gov/19553212/
- Tauroza, S. & Allison, D. (1990). Speech rates in British English. *Applied Linguistics* 11(1), 90-105. (Not read in
  the original: the 260 syllables/min is as reported by Plug et al. 2021, the range and genre notes from secondary
  summaries.)
- Wells, J. C. (2008). *Longman Pronunciation Dictionary*, 3rd ed. (weak forms)
- Wikipedia, "Speech tempo". https://en.wikipedia.org/wiki/Speech_tempo
- Yuan, J., Liberman, M. & Cieri, C. (2006). Towards an integrated understanding of speaking rate in conversation.
  *Interspeech 2006*. (local copy `.demo/voice-v2/papers/yuan2006.txt`)
- Zvonik, E. & Cummins, F. (2003). The effect of surrounding phrase lengths on pause duration. *Eurospeech 2003*.
  https://www.isca-archive.org/eurospeech_2003/zvonik03_eurospeech.html
