# Voxtral TTS test: log

A test of Mistral's Voxtral TTS, which the survey
([tts-survey-2026-11.md](tts-survey-2026-11.md)) listed as 8th on the open-weights
leaderboard, and as one of the few models that speak Dutch. Run 2026-11-23 on the M3 Max.

## The model

- **Checkpoint:** `mlx-community/Voxtral-4B-TTS-2603-mlx-bf16` (8.0 GB, not gated), the MLX
  conversion of `mistralai/Voxtral-4B-TTS-2603`. It runs through mlx-audio 0.6.7.
- **Licence:** CC BY-NC 4.0. That's fine for the user's use (personal, or a non-monetised
  YouTube channel), with attribution, e.g. "Voxtral TTS by Mistral AI, CC BY-NC 4.0". It's
  not fine for anything commercial. See
  [licensed-voices-2026-11.md](licensed-voices-2026-11.md).
- **Languages:** English, French, Spanish, German, Italian, Portuguese, Dutch, Arabic, Hindi.
- **Voices: 20 presets, no cloning.** mlx-audio's implementation takes only a `voice` preset
  name, with no reference audio. That's in line with the model card, which sends custom
  voices to Mistral's hosted AI Studio. So the user's own voice can't be used. The presets:
  - **English:** `casual_male`, `casual_female`, `cheerful_female`, `neutral_male`,
    `neutral_female`.
  - **Dutch:** `nl_male`, `nl_female`.
  - **Other languages:** `fr_*`, `es_*`, `de_*`, `it_*`, `pt_*`, `ar_male`, `hi_*`.
- **Long text:** Voxtral doesn't split text into sentences itself. Its own "chunks" only
  serve streaming. So `pilot_render.py` gained a `voxtral` engine that feeds it the same
  300-character chunks as VoxCPM2, with the first letter of each chunk capitalised (see
  [1clement-audiobook-dillon.md](1clement-audiobook-dillon.md), step 2a).
- **Streaming:** supported (`stream=True`, in steps of 80 ms frames).

## The test

The test script is `out/voxtral/run.sh`. It waited for the British-elder audiobook render to
finish, so the two didn't share the GPU.

1. **Auditions** (`out/voxtral/auditions/`): the 5 English presets read the two sentences
   from the other auditions (the opening of 1 Clement chapter 20). The 2 Dutch presets read
   the user's two Dutch reference sentences ("Het was al laat in de middag…").
2. **English sample:** the title, greeting and chapter 1 of 1 Clement with `neutral_male` and
   `casual_male`, checked with `pilot_check.py --chunk-starts`. Each voice's audition clip
   serves as its "reference" for the voice checks.
3. **Dutch:** the Dutch test text from the pilot (a novel passage plus a podcast monologue)
   with `nl_male` and `nl_female`, checked with `--lang nl`. This is directly comparable
   with VoxCPM2 and Drama 3 reading the same text in the user's own voice
   ([pilot-2026-11.md](pilot-2026-11.md), step 7).
4. **Real-time:** time to first audio with `stream=True` against a whole-sentence call, on
   the same sentence as the other latency measurements.

### A missing dependency

The first run failed as soon as the model loaded:

```
RuntimeError: Voxtral TTS tekken tokenizers require mistral-common[audio]. Install the `tts`
extra or add `mistral-common[audio]` to your environment.
```

mlx-audio doesn't install that package by default. `pip install "mistral-common[audio]"`
added mistral-common 1.13.1 and a few small dependencies (tiktoken, soxr, pycountry,
pillow and others). It also **downgraded numpy from 2.4.6 to 2.3.5**. mlx 0.32.4,
mlx-audio, scipy and soundfile all import fine with it, and `requirements-mlx.txt` was
updated. Nothing had been rendered, so the test was requeued to run after the
Audio8/OmniVoice clone test, which the early failure had let start first.

## Results

The requeued run had the GPU to itself. Everything ran at about 2.3x realtime, with a
peak of 9.7 GB.

**Auditions** (`out/voxtral/auditions/`, 24 kHz). These are the 7 clips to listen to when
choosing a voice:

| Voice | Text | Audio | Time |
|---|---|---|---|
| `neutral_male` | English | 10.5 s | 5.4 s |
| `casual_male` | English | 8.6 s | 4.0 s |
| `neutral_female` | English | 12.2 s | 5.6 s |
| `casual_female` | English | 11.8 s | 5.4 s |
| `cheerful_female` | English | 12.2 s | 5.5 s |
| `nl_male` | Dutch | 11.6 s | 5.3 s |
| `nl_female` | Dutch | 9.8 s | 4.5 s |

**English sample** (title, greeting, chapter 1 of 1 Clement):

| Voice | Audio | WER | 3+ word errors | Chunk openings misheard | Voice consistency (mean / min) | Loudness spread | Words/min |
|---|---|---|---|---|---|---|---|
| `neutral_male` | 1.8 min | **0.00%** | 0 | 0 of 2 | **0.906 / 0.871** | 1.39 dB | 165 |
| `casual_male` | 1.7 min | 0.68% | 0 | 0 of 2 | 0.869 / 0.754 | 0.49 dB | 175 |

`neutral_male` read the sample without a single word error, matching the British elder
take 1. Its loudness varies a little more between sections (1.39 dB).

**Dutch test text** (novel passage plus podcast monologue):

| Voice | Audio | WER | 3+ word errors | Voice consistency (mean / min) | Words/min |
|---|---|---|---|---|---|
| `nl_female` | 1.3 min | **1.74%** | 0 | 0.904 / 0.859 | 176 |
| `nl_male` | 1.5 min | 2.17% | 0 | 0.897 / 0.821 | 156 |

These are the best Dutch scores in any test so far. What's left is writing, not speech:
- "één" → "1" and "eruitzag" → "er uitzag", which all models get.
- A lone "Podcast." heading the recognisers miss. The audio shows it was spoken (0.62–0.63 s
  of speech before the pause; see [cloning-models-2026-11.md](cloning-models-2026-11.md)).
- From `nl_male`, a fast "hij er" heard as "hier".

The comparison with the cloners isn't quite even, though: Voxtral reads in its own
trained Dutch voices, while the cloners imitate the user's voice from 18.6 s of audio.

**Real time** (the 1 Clement chapter 7 sentence from the other latency tests, `neutral_male`,
after a warm-up):

| Mode | First audio after | Audio | Total | Speed |
|---|---|---|---|---|
| `stream=True`, 0.5 s pieces | **375 ms** | 6.2 s | 3.0 s | 2.0x |
| Whole sentence | 3,096 ms | 6.6 s | 3.1 s | 2.1x |

Unlike VoxCPM2 in mlx-audio, Voxtral streams. It starts speaking after about 0.4 s, close
to Phonon's 0.2 s, and generates twice as fast as playback, so it can keep up with live
text.

## Conclusions

- **Voxtral is a strong preset-voice model.** It's accurate (0% WER for `neutral_male` in
  English, the best Dutch so far), steady, 2.3x realtime, 10 GB, and it streams with about
  0.4 s latency.
- **Its two limits:** no cloning, so not the user's own voice; and the CC BY-NC licence,
  which is fine for the user's personal or non-monetised YouTube use, with attribution
  ("Voxtral TTS by Mistral AI, CC BY-NC 4.0").
- **For Dutch in a stock voice**, it's the best option tested. For English in a stock voice
  it rivals the designed VoxCPM2 voice, and it adds real-time streaming that VoxCPM2 lacks
  in mlx-audio.

Listening files: `out/voxtral/en_neutral_male.wav`, `en_casual_male.wav`, `nl_nl_female.wav`,
`nl_nl_male.wav`.
