# 1 Clement audiobook in a designed voice ("British elder"): log

The 1 Clement audiobook read by a voice that VoxCPM2 invented from a text description.
Unlike the Jay Dyer and Tim Dillon versions, **this one may be published online**:

- **Model:** VoxCPM2, Apache 2.0, "free for commercial use".
- **Voice:** designed by the model, not cloned from a person.
- **Text:** Lightfoot's translation (1891), in the public domain.

The licence reasoning, the auditions, and why designed voices need "takes" are in
[licensed-voices-2026-11.md](licensed-voices-2026-11.md). Produced 2026-11-23.

Everything that isn't the voice is the same as in the other audiobooks
([1clement-audiobook.md](1clement-audiobook.md)): the same source text, clean-up,
section layout, chapter markers and encoder settings. The chunking includes the
capitalisation fix from [1clement-audiobook-dillon.md](1clement-audiobook-dillon.md),
step 2a.

## Reproduce

Run from the repo root, after the pilot's setup (`.venv-mlx`, `out/pilot/1clement.txt`).

```bash
B=out/1clement_british_elder; mkdir -p $B
# the voice: VoxCPM2 voice design, seed 0 ("take 1"), reading the opening of chapter 20
.venv-mlx/bin/python - <<'PY'
import numpy as np, soundfile as sf, mlx.core as mx
from mlx_audio.tts.utils import load
tts = load("mlx-community/VoxCPM2-bf16")
text = open("out/pilot/ref/ref.txt").read().strip()
d = ("An older British man with a gentle, resonant voice, measured and reverent, "
     "like a narrator of classic literature")
mx.random.seed(0)
a = np.concatenate([np.asarray(r.audio, dtype=np.float32).reshape(-1) for r in tts.generate(text=text, instruct=d)])
sf.write("out/1clement_british_elder/ref.wav", a, tts.sample_rate)
PY
cp out/pilot/ref/ref.txt $B/ref.txt
.venv-mlx/bin/python tools/pilot_render.py voxcpm2 out/pilot/1clement.txt $B/sections $B/ref.wav $B/ref.txt --vox-mode prompt
.venv-mlx/bin/python tools/pilot_check.py --chunk-starts out/pilot/1clement.txt $B/ref.wav $B/sections
.venv-mlx/bin/python -I tools/join.py $B/sections $B/joined.wav $B/chapters.txt
C="Narrated by a synthetic voice, designed with VoxCPM2 (Apache 2.0). Translation by J. B. Lightfoot (1891), public domain."
ffmpeg -i $B/joined.wav -i $B/chapters.txt -map 0:a -map_metadata 1 -map_chapters 1 -metadata comment="$C" \
  -ac 1 -c:a aac_at -b:a 64k -movflags +faststart out/1clement_british_elder_voxcpm2.m4b
ffmpeg -i $B/joined.wav -i $B/chapters.txt -map 0:a -map_metadata 1 -map_chapters 1 -metadata comment="$C" \
  -ac 1 -c:a libmp3lame -b:a 64k -id3v2_version 3 out/1clement_british_elder_voxcpm2.mp3
```

## 1. Voice

- **Description:** "An older British man with a gentle, resonant voice, measured and reverent,
  like a narrator of classic literature".
- **Choosing a take.** The user picked this description from the auditions but had no
  preference between its two takes. They are different voices (ECAPA similarity 0.549).
  An unheard new take was ruled out, since nobody had listened to it. Instead, both
  takes read the title, greeting and chapter 1 (prompt mode, the capitalisation fix
  in place), and were checked:

  | Take (seed) | Audio | WER | Chunk openings misheard | Clone similarity | Voice consistency (mean / min) | Loudness spread | Words/min |
  |---|---|---|---|---|---|---|---|
  | **1 (seed 0)** | 1.9 min | **0.00%** | 0 of 2 | **0.834** | **0.930 / 0.874** | **0.28 dB** | 148 |
  | 2 (seed 1) | 1.8 min | 1.02% | 0 of 2 | 0.805 | 0.929 / 0.846 | 0.79 dB | 164 |

  Take 1 was chosen. It was better on every measure except pace, and its slower pace
  suits the "measured and reverent" description.
- **Reference:** `out/1clement_british_elder/ref.wav` (= `out/licensed/auditions/voxcpm2_british_elder_take1.wav`),
  11.7 s, 48 kHz. Its transcript is the opening of chapter 20 ("The heavens are moved by
  His direction…"), which the take says exactly (checked with Parakeet).

## 2. Render

- **3 sections reused** from the take-1 test: the title, the greeting and chapter 1. They
  were made with the same reference, mode and settings, and their timings are marked
  `"reused_from"`.
- **64 sections rendered:** chapters 2–65. Started 20:38: 85.6 minutes of audio in 42.8
  minutes (2.0x realtime), peak memory 11.0 GB. No section needed re-rendering.

## 3. Checks

`pilot_check.py --chunk-starts` on all 67 sections:

| Sections | Audio | WER | 3+ word errors | Chunk openings misheard | Clone similarity | Voice consistency (mean / p5 / min) | Loudness spread | Words/min | Clipped |
|---|---|---|---|---|---|---|---|---|---|
| 67 | 87.6 min | **0.47%** | 0 | **0 of 38** | 0.831 | **0.918** / 0.876 / 0.466 | 0.24 dB | 152 | 0 |

- **The cleanest of the four audiobooks.** It has the lowest WER (against 0.82–0.85% for
  the Dyer and Dillon clones), and no chunk opening is misheard. The capitalisation fix
  held across the whole book. No skipped, repeated or invented passages, and no spoken
  punctuation.
- **The one low voice window (0.466) is a measurement artifact.** It's the same spot as in
  the Dillon book: the last 3.2 s of chapter 32 (66.0–69.2 s), less than half of it speech.
  It holds the closing "…for ever and ever. Amen." and the section's trailing silence. The
  next lowest windows are 0.663 and 0.731, and the 5th percentile is 0.876.
- **No long pauses at all:** not one silence of 1.5 s or more inside a section. The Jay Dyer
  clone has 131 and the Tim Dillon clone 73, so their long pauses came from the cloned
  speakers, not from VoxCPM2.
- **Pace:** 152 wpm, slow and even, as the description asked.

## 4. Join

```
$ .venv-mlx/bin/python -I tools/join.py out/1clement_british_elder/sections out/1clement_british_elder/joined.wav out/1clement_british_elder/chapters.txt
67 sections, 88.7 min
```

## 5. Encode

The same encoder settings as the other audiobooks, but a different comment tag. Because
this version may be shared, it tells listeners the narration is synthetic and credits the
model and the translation: *"Narrated by a synthetic voice, designed with VoxCPM2
(Apache 2.0). Translation by J. B. Lightfoot (1891), public domain."*

## 6. Verify and clean up

| File | Codec | Duration | Bitrate | Size | Chapters |
|---|---|---|---|---|---|
| `out/1clement_british_elder_voxcpm2.m4b` | AAC, 48 kHz mono | 1:28:42 | 65.5 kbps | 43.6 MB | 67 |
| `out/1clement_british_elder_voxcpm2.mp3` | MP3, 48 kHz mono | 1:28:42 | 64.0 kbps | 42.6 MB | 67 |

- **Chapters:** both files report the same start times: Title 0:00, Greeting 0:07,
  Chapter 1 0:27, …, Chapter 64 1:27:14, Chapter 65 1:27:54.
- **Tags:** title, artist and the comment tag are present in both.
- **Cleaned up:** the joined WAV was deleted after encoding.
- **Kept:** the section WAVs, transcripts and `chapters.txt` (482 MB), plus the take-2 test
  run, in `out/1clement_british_elder/`.

## Publishing notes

- **The audio may be shared** under the licence reasoning in
  [licensed-voices-2026-11.md](licensed-voices-2026-11.md). The user's plan is at most a
  non-monetised, usually unlisted, YouTube video.
- **Suggested description text:** "Narrated by an AI voice (VoxCPM2 by OpenBMB, Apache 2.0).
  Text: The First Epistle of Clement to the Corinthians, translated by J. B. Lightfoot
  (1891), public domain."
