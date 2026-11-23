# Which models can clone a voice: log

Checked 2026-11-23, after it turned out that Voxtral can't clone. The question: which
models can clone a voice from a recording, in particular the user's own Dutch voice,
running on this Mac?

## Method

- **Code check:** every text-to-speech model in the installed mlx-audio 0.6.7 (45 model
  folders under `mlx_audio/tts/models/`) was searched for reference-audio parameters
  in its `generate()`: `ref_audio`, `prompt_audio`, `audio_prompt` and so on. Then each
  candidate's README was read for languages and licence.
- **Why a parameter alone isn't proof:** some implementations accept arguments they
  ignore, e.g. VoxCPM2's `ref_text`. And Phonon's code accepts `ref_audio`, but the
  published checkpoint lacks the speaker encoder it needs.
- **Combined with** the survey's model-card findings ([tts-survey-2026-11.md](tts-survey-2026-11.md))
  and the tests run so far.
- **Licence yardstick:** the user's use is personal, or at most a non-monetised YouTube
  channel ([licensed-voices-2026-11.md](licensed-voices-2026-11.md)), so non-commercial
  licences are acceptable.

## Clones a voice and speaks Dutch, runs on this Mac

| Model | Size | Licence | Status |
|---|---|---|---|
| **VoxCPM2** (OpenBMB) | 2B, 5 GB | Apache 2.0 | **Tested with the user's voice:** Dutch WER 2.2%, clone similarity 0.774, 144 wpm, 1.7x realtime ([pilot](pilot-2026-11.md), step 7) |
| **Fish Audio Drama 3** | 35B MoE, 24 GB (4-bit) | Fish Audio Community License: non-commercial fine; commercial below USD 500k/yr | **Tested with the user's voice:** Dutch WER 2.2%, clone similarity 0.799, slow 106 wpm, needs 29 GB |
| **Audio8 TTS Realistic Air** (Edge0) | 0.6B, 2.6 GB (`mlx-community/Audio8-TTS-Realistic-0.6b-bf16`) | Apache 2.0 | **Not tested.** New since the survey (November 2026). 23 languages incl. Dutch, cloning from a reference plus its transcript, 44.1 kHz. mlx-audio type `arktts`. |
| **OmniVoice** (k2-fsa) | 0.6B (`mlx-community/OmniVoice-bfloat16`) | CC BY-NC (weights) | **Not tested.** 646+ languages; Dutch is among its best-quality ones. Also does voice design. |
| **MOSS-TTS v1.5** (OpenMOSS) | 8B | Apache 2.0 (HF tag) | **Not tested.** 31 languages incl. Dutch; pass `language` for non-English. |
| **Chatterbox Multilingual V3** (Resemble AI) | 0.5B | Code MIT; weights licence not stated | **Not tested.** 23 languages incl. Dutch. The project was retired in August 2026. |
| **Coqui XTTS-v2** | ~2 GB | Coqui Public Model License (non-commercial) | **Already in this repo:** `./coqui.py -r me.wav -l nl`. The oldest option, and 18th of 20 on the leaderboard. |

## Clones a voice, but no (confirmed) Dutch

| Model | Licence | Languages / note |
|---|---|---|
| Qwen3-TTS Base (Alibaba) | Apache 2.0 | 10 languages, no Dutch. Cloning only on the Base models. |
| Reverb-TTS (Software Mansion) | CC BY-NC | en, de, fr, es, it, pl, pt |
| Higgs Audio V3 (Boson AI) | Research and non-commercial | "100+ languages"; Dutch not confirmed |
| Fish Audio S2 Pro | Fish research licence (non-commercial) | "80+ languages"; Dutch not confirmed. Superseded by Drama 3. |
| Echo-TTS | CC BY-NC-SA 4.0 | Not stated |
| ZONOS3-Mini (Zyphra) | Apache 2.0 | Not stated in the README; 27 built-in voices |
| Ming-3.0 TTS (Ant Group) | MIT | zh, en, de, es, fr, ko, ja |
| Confucius4 | Not stated | zh, en, vi, ja, ko, th |
| Maya2 | Not stated | 11 Indic languages + English. The README asks for "permission to clone" the reference. |
| Step Audio EditX (StepFun) | Apache 2.0 | zh, en, ja, ko + dialects. Runs via mlx-speech, not mlx-audio. |
| Others in mlx-audio: Spark, Dia, CSM (Sesame), OuteTTS, IndexTTS, Zonos (v2), Higgs Audio v2, LongCat AudioDiT, Dramabox, TADA | various | Mostly English and/or Chinese |

## Can't clone (as published)

- **Phonon 31M:** the open checkpoint has no speaker encoder; cloning is in Gradium's hosted
  Studio only.
- **Voxtral TTS:** 20 preset voices; custom voices only via Mistral's hosted AI Studio.
- **No cloning at all:** Kokoro, Piper, Kitten TTS, MeloTTS, Soprano, Bark (presets), and
  KugelAudio ("not supported in this open-source release").
- **Kyutai Pocket TTS:** the full model clones, but its weights are gated (CC BY 4.0), and the
  ungated variant mlx-audio uses has no cloning.

## Test: four cloners, the user's voice

Audio8 TTS Realistic Air and OmniVoice were tested the same way as VoxCPM2 and Drama 3
in the pilot ([pilot-2026-11.md](pilot-2026-11.md), step 7):
- **Reference:** the user's 18.6 s Dutch recording (`out/pilot/me/me_nl_ref.wav`) with
  its transcript.
- **Texts:** the Dutch test text (a novel passage plus a podcast monologue), and the
  English 1 Clement sample (title, greeting, chapter 1).
- **Engines:** `pilot_render.py` gained `audio8` and `omnivoice`. Both get the text in
  300-character chunks, with the first letter capitalised. OmniVoice needed two settings:
  - `language` (`--lang nl` / `en`).
  - `ref_audio_max_duration_s=30`. Its default trims a reference to 10 s but keeps the full
    transcript, so audio and transcript wouldn't match.
- **Script:** `out/clonetest/run.sh`. It ran with the GPU to itself.
- **Checks:** `pilot_check.py --chunk-starts` (`--lang nl` for Dutch).

**Dutch** (1.6–2.1 min of audio):

| Model | WER | 3+ word errors | Clone similarity | Voice consistency (mean / min) | Words/min | Speed | Peak memory |
|---|---|---|---|---|---|---|---|
| VoxCPM2 *(pilot)* | **2.17%** | 0 | 0.774 | **0.902** / 0.806 | 144 | 1.7x | 10.3 GB |
| Drama 3 *(pilot)* | **2.17%** | 0 | 0.799 | 0.898 / 0.786 | 106 | (not comparable) | 28.6 GB |
| Audio8 Realistic Air | 3.48% | 0 | 0.763 | 0.882 / 0.791 | 125 | 1.1x | 12.1 GB |
| OmniVoice | 2.61% | 0 | **0.818** | **0.902** / **0.820** | 145 | **2.3x** | **5.8 GB** |

**English sample, from the Dutch reference** (2.0–2.5 min):

| Model | WER | 3+ word errors | Clone similarity | Voice consistency (mean / min) | Words/min | Speed | Peak memory |
|---|---|---|---|---|---|---|---|
| VoxCPM2 *(pilot)* | **1.70%** | 0 | 0.756 | 0.900 / 0.793 | 129 | 1.5x | 11.4 GB |
| Audio8 Realistic Air | **1.70%** | 0 | 0.725 | 0.888 / 0.766 | 119 | 1.2x | 11.7 GB |
| OmniVoice | 2.72% | **1** | **0.801** | **0.908 / 0.881** | 146 | **2.7x** | **5.8 GB** |

What the numbers hide:
- **OmniVoice skipped words.** In chapter 1 it read "rendering to the older men ~~among you
  the honor~~ which is their due". Both recognisers agree. In Dutch it also skipped the
  one-word heading "Podcast." (see below). Otherwise it's the closest
  clone, the steadiest, the fastest and the lightest. But for audiobooks a model that can
  drop words needs the full check on every render. It's a non-autoregressive model that
  predicts the length of its output up front, which is a known source of skipped words.
- **Audio8 mispronounces some Dutch:** both recognisers hear something other than "groen"
  ("gron" / "grond"), and Whisper hears "boorderij" for "boerderij". It's the slowest
  reader (119–125 wpm, closest to the slow reference) and the slowest renderer here
  (1.1–1.2x).
- **The Dutch WER is mostly writing, not speech.** All models get "één"/"twintig" written
  as digits and "eruitzag" split in two. The real differences are the slips above.
- **Caveat:** the pilot's VoxCPM2 and Drama 3 runs predate the chunk-capitalisation fix.
  The Dutch text has no mid-sentence chunk starts, so the Dutch rows are unaffected. The
  English sample has two, which weren't checked for VoxCPM2.

### The "Podcast" heading

Both recognisers miss the one-word heading "Podcast." in almost every Dutch run. That
first looked like a pattern of models skipping it (and the pilot log said so for
Drama 3). The audio itself says otherwise. Each heading is rendered on its own and
followed by 0.5 s of silence, so the first burst of speech in the section is the heading:

| Model | Speech before the pause |
|---|---|
| VoxCPM2 | 0.76 s |
| Drama 3 | 0.81 s |
| Audio8 Realistic Air | 0.88 s |
| Voxtral `nl_female` / `nl_male` | 0.63 s / 0.62 s |
| **OmniVoice** | **0.01 s** |

So the heading was spoken in every run except OmniVoice's. The recognisers drop a lone
loanword before a pause; they're unreliable for one-word lines. OmniVoice really skipped
it, in line with the words it skipped in the English sample.

Listening files: `out/clonetest/audio8_me_nl.wav`, `audio8_me_en.wav`,
`omnivoice_me_nl.wav`, `omnivoice_me_en.wav`, next to the pilot's `out/pilot/voxcpm2_me_*.wav`
and `drama3_me_nl.wav`.

## Shortlist for the user's own voice in Dutch

1. **VoxCPM2:** tested, permissive licence, the best balance of quality and speed.
2. **Drama 3:** tested, the closest clone, but heavy and slow-paced.
3. **OmniVoice:** tested. The closest and steadiest clone, and the fastest and lightest
   (2.3–2.7x, 5.8 GB). But it skipped four words in the English sample. Good for short
   pieces such as podcast segments, where a listen-through catches slips; for long
   audiobooks only with the full check. Non-commercial licence, fine for the user's use.
4. **Audio8 TTS Realistic Air:** tested. No advantage over VoxCPM2: a less close clone, some
   Dutch mispronunciations, and slower.

The order after testing: **VoxCPM2** stays the all-rounder. **OmniVoice** is the one to
listen to for your voice, especially for short, real-time-ish uses. **Drama 3** if the
closest clone matters more than speed. **Audio8** is out.
