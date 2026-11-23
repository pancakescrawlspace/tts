# 1 Clement audiobook in Tim Dillon's voice: log

The 1 Clement audiobook a third time, now read by a VoxCPM2 clone of Tim Dillon's voice.
Produced 2026-11-23.

**For the user's personal listening only.** Tim Dillon hasn't consented to having his
voice cloned, so this follows the same rules as the Jay Dyer version
([1clement-audiobook-dyer.md](1clement-audiobook-dyer.md)):
- The audio stays in the gitignored `out/` and is not to be shared or published.
- The voice comes from VoxCPM2 (Apache 2.0), because Fish Audio Drama 3's licence forbids
  cloning a real person without consent.

Everything that isn't the voice is the same as in the first two audiobooks: the same source
text, clean-up, section layout, chapter markers and encoder settings. Only the differences
are described here.

## Reproduce

Run from the repo root, after the pilot's setup (`.venv-mlx`, `out/pilot/1clement.txt`, and
the reference clip `out/pilot/dillon/dillon_ref.wav` with its transcript).

```bash
B=out/1clement_dillon; mkdir -p $B/sections
.venv-mlx/bin/python tools/pilot_render.py voxcpm2 out/pilot/1clement.txt $B/sections \
  out/pilot/dillon/dillon_ref.wav out/pilot/dillon/dillon_ref.txt --vox-mode prompt
.venv-mlx/bin/python tools/pilot_check.py out/pilot/1clement.txt out/pilot/dillon/dillon_ref.wav $B/sections
.venv-mlx/bin/python -I tools/join.py $B/sections $B/joined.wav $B/chapters.txt
ffmpeg -i $B/joined.wav -i $B/chapters.txt -map 0:a -map_metadata 1 -map_chapters 1 \
  -metadata comment="Synthetic voice (VoxCPM2 clone). Private copy, not for distribution." \
  -ac 1 -c:a aac_at -b:a 64k -movflags +faststart out/1clement_dillon_voxcpm2.m4b
ffmpeg -i $B/joined.wav -i $B/chapters.txt -map 0:a -map_metadata 1 -map_chapters 1 \
  -metadata comment="Synthetic voice (VoxCPM2 clone). Private copy, not for distribution." \
  -ac 1 -c:a libmp3lame -b:a 64k -id3v2_version 3 out/1clement_dillon_voxcpm2.mp3
```

## 1. Voice

- **Model:** `mlx-community/VoxCPM2-bf16` (mlx-audio 0.6.7), prompt mode, default sampling,
  seed 0. The same as the Jay Dyer version.
- **Reference:** `out/pilot/dillon/dillon_ref.wav`, 10.48 s, the first 10.5 s of a clip the
  user supplied, where Dillon speaks alone. The clip also holds JD Vance's voice, in the
  interview excerpts Dillon reacts to. How the two were told apart, the transcript, and
  the noise level (about −45 dBFS between phrases) are in the pilot log, step 7.
- **Sample first:** the title, greeting and chapter 1 were rendered in the pilot:
  - 0.34% WER, nothing skipped.
  - Clone similarity 0.736.
  - Voice consistency 0.879 on average, 0.831 at worst.
  - 168 wpm.

## 2. Render

- **3 sections reused** from the pilot sample (`out/pilot/runs/voxcpm2_dillon`): the title,
  the greeting and chapter 1. They were made with the same model, reference, mode and
  settings, and their timings are marked `"reused_from"` in `timings.jsonl`.
- **64 sections rendered now:** chapters 2–65. That's 71.3 minutes of audio in 35.6
  minutes (2.0x realtime), peak memory 10.1 GB.

The first full check was clean by its own rules: 0.86% WER, no 3+ word errors, voice
consistency 0.88. But a search of the transcripts for spoken punctuation found the word
"dot" where the source has none. The next steps track that down.

### 2a. A stray word where chunks are cut

Chapter 32, "…all men that have been from the beginning; to whom be the glory…", came out
as "from the beginning **dot** to whom be the glory". Both recognisers heard it. Chapter 58
had a "dot" too (Parakeet only), after "so surely shall he,". The Jay Dyer book, made with
the same text and chunker, had none.

Both spots are where VoxCPM2's chunker cuts a sentence that's too long for one 300-character
chunk. It cuts at a semicolon or comma, and the next chunk starts mid-sentence. Three fixes
were tried on those two sections:

| Attempt | Chapter 32 | Chapter 58 |
|---|---|---|
| Original (seed 0) | "beginning **dot** to whom" | "he **dot** who" (Parakeet only) |
| Re-rendered with seed 1 | Whisper: "beginning, **dot**, to whom"; Parakeet: clean | "he, **God** who" (both) |
| Full stop instead of the `;`/`,` at the end of the chunk | "beginning, **that** to whom" (both) | "he. **Dot** who" (both) |

So the stray word wasn't at the end of the first chunk but at the start of the next one,
which begins in lowercase ("to whom…", "who with…"). A test isolated that. Both chunk
openings were generated 4 times each (seeds 0–3), once as written and once with the
first letter capitalised. Parakeet heard:

| Chunk text | As written | Capitalised |
|---|---|---|
| "to whom be the glory…" | "To him be the", "To whom be the", "**God** to him be", "To whom be the" | "To whom be the" ×4 |
| "who with lowliness…" | "**Wahu**, with", "**You said Dihol** with", "**Dot** who", "**Twilama**, lowliness" | "Who with lowliness" ×4 |

As written, 5 of 8 takes garbled or prefixed the opening. Capitalised, all 8 were clean.

**Fix:** `pilot_render.py` now capitalises the first letter of every chunk it gives
VoxCPM2. The full-stop change was reverted: it didn't help, and it would make a
mid-sentence cut sound like the end of a sentence. The chunker itself moved into
`tools/textchunks.py`, so `pilot_check.py` can find the chunk starts too.

### 2b. How widespread, and the re-render

The whole book has 38 chunks that start mid-sentence in lowercase, spread over 26
sections. A new option, `pilot_check.py --chunk-starts`, lists the ones whose first words
both recognisers mishear. In the first render that was 8 of 38:

| Chapter | Source | Heard (Parakeet / Whisper) |
|---|---|---|
| 3 | "seeing that they have" | "heart **edfrey** seeing" / "heart **edfrace** seeing" |
| 12 | "then she answered the" | "ordereth **that** she" / same |
| 25 | "and in the daytime" | "sun **it send** in" / "sun **it said** in" |
| 32 | "of him are kings" | "flesh **thought** of" / "32 **so** out of" |
| 32 | "to whom be the" | "beginning **that** to" / same |
| 58 | "who with lowliness of" | "he **dot** who" / same |
| 59 | "who layest low in" | "holy **ad** who" / "holy **and** who" |
| 59 | "who multipliest the nations" | "spirit **do** multiplice the" / "spirit **you** multipliest" |

All 26 sections with a mid-sentence chunk start were re-rendered with the fix. The
replaced takes are kept in `out/1clement_dillon/replaced/` (`v1/` is the first render,
`seed1/` and `fullstop/` the experiments on chapters 32 and 58). The other 41 sections
were left alone: their text is identical under the new rule, because none of their chunks
starts in lowercase.

The re-render: 26 sections, 31.2 minutes of audio in 15.9 minutes (about 2x realtime).
Chapter 1 was among them, so of the pilot sample only the title and greeting remain in
the final book.

## 3. Checks

The final book, with `pilot_check.py --chunk-starts`:

| Sections | Audio | WER | 3+ word errors | Chunk openings misheard | Clone similarity | Voice consistency (mean / p5 / min) | Loudness spread | Words/min | Clipped |
|---|---|---|---|---|---|---|---|---|---|
| 67 | 73.5 min | 0.85% | 0 | 1 of 38 | 0.748 | 0.877 / 0.805 / 0.722 | 0.38 dB | 183 | 0 |

- **Chunk openings: 1 of 38, down from 8.** The one left isn't a garble. In "who
  multipliest the nations" (chapter 59), both recognisers write the archaic "multipliest"
  as "multiplies", and the opening word "who" is right.
- **No spoken punctuation:** the transcripts contain no "dot", "comma" and so on that isn't
  in the source.
- **Voice:** steady. The weakest window (0.722) is the start of chapter 3, which is no
  outlier. The first render's weakest window, 0.53 at the end of chapter 32, was
  replaced.
- **Pace and pauses:** 183 wpm, faster than the Jay Dyer clone (161), and with fewer long
  pauses. There are 73 silences of 1.5 s or more (1.0 per minute, 25 of them right after a
  heading, the longest 2.4 s), against Jay Dyer's 131 (1.6 per minute).

## 4. Join

```
$ .venv-mlx/bin/python -I tools/join.py out/1clement_dillon/sections out/1clement_dillon/joined.wav out/1clement_dillon/chapters.txt
67 sections, 74.6 min
```

## 5. Encode

The same commands and comment tag as the Jay Dyer version (see *Reproduce*).

## 6. Verify and clean up

Checked with `ffprobe`:

| File | Codec | Duration | Bitrate | Size | Chapters |
|---|---|---|---|---|---|
| `out/1clement_dillon_voxcpm2.m4b` | AAC, 48 kHz mono | 1:14:35 | 65.5 kbps | 36.6 MB | 67 |
| `out/1clement_dillon_voxcpm2.mp3` | MP3, 48 kHz mono | 1:14:35 | 64.0 kbps | 35.8 MB | 67 |

- **Chapters:** both files report the same start times: Title 0:00, Greeting 0:07,
  Chapter 1 0:24, …, Chapter 64 1:13:22, Chapter 65 1:13:52.
- **Tags:** title, artist and the comment tag are present in both.
- **Cleaned up:** the joined WAV (430 MB) was deleted after encoding.
- **Kept:** the section WAVs, transcripts and `chapters.txt` (404 MB), and the replaced takes
  (188 MB), all in `out/1clement_dillon/`. They can be deleted once the audiobook is final.
