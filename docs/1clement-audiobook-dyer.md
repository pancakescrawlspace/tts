# 1 Clement audiobook in Jay Dyer's voice: log

The 1 Clement audiobook again, this time read by a VoxCPM2 clone of Jay Dyer's voice.
Produced 2026-11-23.

**For the user's personal listening only.** Jay Dyer hasn't consented to having his voice
cloned. The user asked for this strictly for private use (see
[pilot-2026-11.md](pilot-2026-11.md), step 7). The audio stays in the gitignored `out/`
and is not to be shared or published. Fish Audio Drama 3's licence forbids this kind of
cloning, so the voice comes from VoxCPM2 (Apache 2.0), the model the pilot tested with
this voice.

Everything that isn't the voice is the same as in the first audiobook
([1clement-audiobook.md](1clement-audiobook.md)): the same source text, clean-up, section
layout, chapter markers and encoder settings.

| Step | What | Tool |
|---|---|---|
| 1 | Source text: the same file as the first audiobook | `tools/extract.py` |
| 2 | Voice: VoxCPM2 cloning a 16.7 s clip | from the pilot |
| 3 | Render one WAV per section, reusing the pilot's 19 | `tools/pilot_render.py` |
| 4 | Check the words and the voice | `tools/pilot_check.py` |
| 5 | Join the sections and write chapter metadata | `tools/join.py` |
| 6 | Encode to AAC (.m4b) and MP3 | `ffmpeg` |
| 7 | Verify | `ffprobe` |

## Reproduce

Run from the repo root, after the pilot's setup (`.venv-mlx`, `out/pilot/1clement.txt`, and
the reference clip `out/pilot/dyer/dyer_ref.wav` with its transcript).

```bash
B=out/1clement_dyer; mkdir -p $B/sections
.venv-mlx/bin/python tools/pilot_render.py voxcpm2 out/pilot/1clement.txt $B/sections \
  out/pilot/dyer/dyer_ref.wav out/pilot/dyer/dyer_ref.txt --vox-mode prompt
.venv-mlx/bin/python tools/pilot_check.py out/pilot/1clement.txt out/pilot/dyer/dyer_ref.wav $B/sections
.venv-mlx/bin/python -I tools/join.py $B/sections $B/joined.wav $B/chapters.txt
ffmpeg -i $B/joined.wav -i $B/chapters.txt -map 0:a -map_metadata 1 -map_chapters 1 \
  -metadata comment="Synthetic voice (VoxCPM2 clone). Private copy, not for distribution." \
  -ac 1 -c:a aac_at -b:a 64k -movflags +faststart out/1clement_dyer_voxcpm2.m4b
ffmpeg -i $B/joined.wav -i $B/chapters.txt -map 0:a -map_metadata 1 -map_chapters 1 \
  -metadata comment="Synthetic voice (VoxCPM2 clone). Private copy, not for distribution." \
  -ac 1 -c:a libmp3lame -b:a 64k -id3v2_version 3 out/1clement_dyer_voxcpm2.mp3
```

## 1. Source text

The text is `out/pilot/1clement.txt`, extracted from the same page with the same script as
the first audiobook. Its SHA-256 is `ee2b790b0bd488b2cda87169195435faba8070904c8f1f846a5b9a028769dc7a`,
identical to the first audiobook's. That's 67 sections (title, greeting, chapters 1–65)
and 13,451 words. The clean-up for speech (translator's note dropped, square brackets
removed) is done by `pilot_render.py`, the same way `render.py` does it.

## 2. Voice

- **Model:** `mlx-community/VoxCPM2-bf16` through mlx-audio 0.6.7, in "prompt" mode: the
  reference clip plus its exact transcript serve as a continuation prompt. In the pilot,
  this mode gave the closest clone.
- **Reference:** `out/pilot/dyer/dyer_ref.wav`, 16.70 s. It was cut from a recording the
  user supplied, at 10:24.75–10:41.45, where he speaks alone with no music (noise floor
  −79 dBFS). The transcript and how the clip was chosen are in the pilot log, step 7.
- **Settings:** default sampling (10 diffusion steps, CFG 2.0), seed 0, speed 1.0. Each
  section body is cut into chunks of at most 300 characters at sentence ends, with 0.25 s
  of silence between chunks.

In the pilot this voice came out accurate (0.91% WER, nothing skipped). It was less
steady than a synthetic-voice clone, though: consistency 0.864 against 0.925, with the
weakest spots at the start of chapters 12 and 15. It reads at about 158 wpm, against
Kokoro's 204, so this audiobook runs longer than the first one.

## 3. Render

- **19 sections reused** from the pilot run (`out/pilot/runs/voxcpm2_dyer`): the title, the
  greeting, chapters 1–16 and chapter 65 (pilot section 18 became section 66 here). They
  were made with the same model, reference, mode and settings. The text of chapter 65 was
  compared and is identical. Their timings were copied into `timings.jsonl`, marked
  `"reused_from"`.
- **48 sections rendered now:** chapters 17–64. That's 60.8 minutes of audio in 30.7
  minutes (1.98x realtime), with a steady 10.5 GB peak. No section failed or was
  re-rendered.

The whole book comes to 83.9 minutes of sections: 23.1 minutes from the 19 pilot
sections and 60.8 new. Joined, it's 85.0 minutes, against 65.9 for the `am_onyx` version,
because this voice reads at 161 wpm against 204.

## 4. Checks

`pilot_check.py` transcribes every section with Parakeet and Whisper. Dropped text counts
only when both recognisers miss it, and added text comes from Parakeet alone. How these
rules were arrived at, and the self-test, are in the pilot log, step 5.

| Sections | Audio | WER | 3+ word errors | Clone similarity | Voice consistency (mean / p5 / min) | Loudness spread | Words/min | Clipped |
|---|---|---|---|---|---|---|---|---|
| 67 | 83.9 min | 0.82% | 0 | 0.763 | 0.864 / 0.800 / 0.471 | 0.53 dB | 161 | 0 |

- **Nothing skipped, repeated or invented.** The WER is at the level of the Kokoro
  baseline's recogniser noise (names, archaic words).
- **The voice is as steady as in the pilot** (0.864 mean, the same as there). The one low
  outlier needs explaining. The weakest window, 0.471, is the first 6 s of chapter 55.
  Between "Chapter 55." and the body there are about 3.5 s of near-silence with a single
  short word in them ("But,", from the source's "But, to bring forward…"). Three seconds
  that are mostly silence give the speaker embedding too little to work with, so this is
  a measurement artifact, not a voice change. From 6 s on, the scores are 0.64–0.70, which
  is normal. Parakeet hears the word correctly. Whisper drops that sentence, its usual
  failure.
- **Long pauses.** The audio contains 131 silences of 1.5 s or more inside sections, beyond
  the designed 0.25/0.5 s gaps. That's about 1.6 per minute, the longest 2.5 s, and 49 of
  them fall right after a "Chapter N." heading. This belongs to the voice, not the model:
  across the same 19 pilot sections, VoxCPM2 cloning `am_onyx` has none, and Kokoro has
  one. The clone picked up the pausing from the reference clip, which itself has pauses of
  nearly a second. Shortening every pause over 1 s to about 1 s (silence only) was
  offered, and the user chose to keep them as rendered. The longest pauses, for listening:

  | Pause | Where (in section) |
  |---|---|
  | 2.5 s | chapter 45, 0:02 |
  | 2.4 s | chapter 50, 0:01 |
  | 2.3 s | chapter 55, 0:02 |
  | 2.3 s | chapter 56, 0:03 |
  | 2.2 s | chapter 43, 0:19 |

## 5. Join

`tools/join.py` was changed for this run. It had 24 kHz (Kokoro) built in and asserted it,
but VoxCPM2 writes 48 kHz. It now takes the sample rate from the first section, and the
chapter timebase follows (`TIMEBASE=1/48000`). For Kokoro's files nothing changes.

```
$ .venv-mlx/bin/python -I tools/join.py out/1clement_dyer/sections out/1clement_dyer/joined.wav out/1clement_dyer/chapters.txt
67 sections, 85.0 min
```

## 6. Encode

The same commands as the first audiobook (mono, 64 kbps, AAC via `aac_at` and MP3 via
`libmp3lame`), plus a `comment` tag on both files: *"Synthetic voice (VoxCPM2 clone).
Private copy, not for distribution."* That way the file explains itself if it ever turns
up in a player or library outside this repo. The commands are under *Reproduce*.

## 7. Verify and clean up

Checked with `ffprobe`:

| File | Codec | Duration | Bitrate | Size | Chapters |
|---|---|---|---|---|---|
| `out/1clement_dyer_voxcpm2.m4b` | AAC, 48 kHz mono | 1:24:59 | 65.5 kbps | 41.8 MB | 67 |
| `out/1clement_dyer_voxcpm2.mp3` | MP3, 48 kHz mono | 1:24:59 | 64.0 kbps | 40.8 MB | 67 |

- **Chapters:** both files report the same start times: Title 0:00, Greeting 0:08,
  Chapter 1 0:27, …, Chapter 64 1:23:36, Chapter 65 1:24:15.
- **Tags:** title, artist and the comment tag are present in both. The `.m4b` also has a
  `bin_data` stream, which is its chapter-title track.
- **Cleaned up:** the joined WAV (489 MB) was deleted after encoding.
- **Kept:** the 67 section WAVs, their transcripts and `chapters.txt`, in
  `out/1clement_dyer/` (461 MB). They're kept so single sections can be re-rendered or the
  pauses tightened without starting over. They can be deleted once the audiobook is
  final.
