# 1 Clement audiobook: pipeline log

How `out/1clement_am_onyx.m4b` and `out/1clement_am_onyx.mp3` were made from the
source text. Produced 2026-11-22 with this repo's Kokoro setup.

| Step | What | Tool |
|---|---|---|
| 1 | Download the source text | `curl` |
| 2 | Extract plain text, grouped by chapter | `tools/extract.py` (stdlib Python) |
| 3 | Clean it up for speech | inside `tools/render.py` |
| 4 | Pick a voice from rendered samples | Kokoro, `afplay` |
| 5 | Render one WAV per section | `tools/render.py` (Kokoro) |
| 6 | Join the sections, build chapter metadata | `tools/join.py` |
| 7 | Encode to AAC (.m4b) and MP3 | `ffmpeg` |
| 8 | Verify and remove intermediate files | `tools/check.py`, `ffprobe` |

The scripts in `tools/` are the ones that were run. Only their usage docstrings were
added afterwards. `tools/check.py` combines two check scripts that were run separately
at the time.

## Reproduce

Run this from the repo root. `work/` is any scratch directory.

```bash
mkdir -p work
curl -sL -A "Mozilla/5.0" -o work/lightfoot.html \
  https://www.earlychristianwritings.com/text/1clement-lightfoot.html
python3 -I tools/extract.py work/lightfoot.html work/1clement.txt
.venv/bin/python tools/render.py work/1clement.txt work/sections am_onyx 1.0
.venv/bin/python -I tools/check.py work/1clement.txt work/sections
.venv/bin/python -I tools/join.py work/sections work/joined.wav work/chapters.txt
ffmpeg -i work/joined.wav -i work/chapters.txt -map 0:a -map_metadata 1 -map_chapters 1 \
  -ac 1 -c:a aac_at -b:a 64k -movflags +faststart out/1clement_am_onyx.m4b
ffmpeg -i work/joined.wav -i work/chapters.txt -map 0:a -map_metadata 1 -map_chapters 1 \
  -ac 1 -c:a libmp3lame -b:a 64k -id3v2_version 3 out/1clement_am_onyx.mp3
rm -r work
```

The details of each step are below.

---

## 1. Source text

- **Text:** The First Epistle of Clement to the Corinthians (*1 Clement*), c. AD 96
- **Translation:** J. B. Lightfoot, *The Apostolic Fathers* (1891), public domain
- **URL:** <https://www.earlychristianwritings.com/text/1clement-lightfoot.html>

| File | SHA-256 |
|---|---|
| `lightfoot.html` (116,750 bytes, ISO-8859-1) | `50a953f1ea5bbfd0e07f88f8685c6fc831fe67805db594b15dc3556e33ab4d22` |

The page puts each verse in its own paragraph, as `<p>1Clem 4:7<br> ...text... </p>`,
with the greeting marked `1Clem prologue:1`. That makes it easy to extract without
picking up the site's navigation menus.

## 2. Extract plain text: `tools/extract.py`

The script pulls every verse paragraph out, strips inline tags (such as `<I>` for
quotations), decodes HTML entities and collapses the hard line breaks. It then joins
the verses of each chapter into one paragraph headed `Chapter N.`, and puts a spoken
title line first.

```
$ python3 -I tools/extract.py lightfoot.html 1clement.txt
392 verses, 66 sections, 13451 words
```

Result: `1clement.txt` has 67 blocks separated by blank lines: the title line, the
greeting, and chapters 1-65.
SHA-256 `ee2b790b0bd488b2cda87169195435faba8070904c8f1f846a5b9a028769dc7a`.

Checks run on the extracted text:

- **Chapter numbering is continuous, 1 to 65.** No chapter is missing or duplicated.
- **Unusual characters:** only 5 `[...]` pairs and 1 `{...}` pair. Both are handled in step 3.

## 3. Clean up for speech

These changes happen at the top of `tools/render.py`. `1clement.txt` itself is left
unchanged.

- **Removed a translator's note.** In chapter 4, the Cain and Abel passage has an
  alternative reading in braces. It isn't part of the letter, and read aloud it would
  sound like part of the quotation, so it's dropped:
  > {This last phrase has also been translated: Be at peace: thine offering returns to
  > thyself, and thou shalt again possess it.}
- **Removed square brackets but kept the words.** Lightfoot uses brackets for words
  he supplied to complete the sense. They're part of the reading, so only the bracket
  characters go: `[king of Israel]`, `[Christ]`, `[Grant unto us, Lord,]`,
  `[that we may be saved,]`, `[their steps]`.
- **Spoken chapter headings.** Each `Chapter N.` line is read aloud and followed by a
  short pause.

The archaic English ("sojourneth", "ye", "hath") is left as it is. Kokoro's G2P
(misaki, with an espeak-ng fallback) pronounces these words.

## 4. Choose a voice

**Request:** a voice like Jay Dyer's (YouTuber). This wasn't done by cloning. He's a
real person who hasn't consented to having his voice cloned, so the reading uses one
of the stock voices instead, chosen to be in a similar register: American, male, lower
pitch.

**Engine:** Kokoro (`./tts.py -e kokoro`). Piper sounds noticeably robotic over a long
reading, and XTTS runs slower than real time. On this machine Kokoro renders about 10x
faster than real time.

**Samples:** the title and greeting were rendered with three US male voices
(`tools/render.py ... VOICE 1.0 --only 2`) and played back with `afplay` in this order:

| Voice | Description | Greeting length |
|---|---|---|
| `am_fenrir` | US male, deeper | 16.6 s |
| `am_michael` | US male | 18.1 s |
| `am_onyx` | US male | 15.0 s |

**Chosen: `am_onyx`.**

A full render with `am_fenrir` had already started before the choice was made. It was
stopped about halfway, and none of its files are used in the output.

## 5. Render: `tools/render.py`

The script runs under the repo's `.venv` (kokoro 0.9.4, misaki 0.9.4, torch 2.14.0,
Python 3.11.6, model `hexgrad/Kokoro-82M` snapshot `f3ff357`).

Settings:

- **Pipeline:** `lang_code="a"` (US English G2P)
- **Speed:** 1.0
- **Output:** 24 kHz mono
- **Splitting:** each section is split on its newline into the heading and the body.
  Kokoro then splits the body into chunks of at most 510 phoneme tokens, on sentence
  boundaries where it can.
- **Silence:** 0.25 s after each Kokoro chunk, plus 0.5 s after the heading and after
  the body. Without this the chunks would butt up against each other.
- **Resumable:** one WAV per section (`000.wav` to `066.wav`), and sections that
  already exist are skipped. The title and greeting from the `am_onyx` samples in
  step 4 were rendered with identical settings, so they were copied in rather than
  rendered again.
- **Offline:** `HF_HUB_OFFLINE=1` is set once the voice is cached, the same as `tts.py`.

```bash
mkdir -p full_am_onyx && cp -n sample_am_onyx/*.wav full_am_onyx/
.venv/bin/python tools/render.py 1clement.txt full_am_onyx am_onyx 1.0
```

**Run:** the remaining 65 sections took 365 s and produced 64.4 minutes of
audio, about 10.6x real time.

## 6. Join sections and build chapter markers: `tools/join.py`

The script concatenates the 67 section WAVs in order, with 1.0 s of silence after each
one. It also writes an ffmpeg metadata file with the title, artist, album and genre
tags, plus one chapter per section ("Title", "Greeting", "Chapter 1" to "Chapter 65").
Chapter boundaries are counted in samples, `TIMEBASE=1/24000`, so they line up exactly
with the section joins.

```
$ .venv/bin/python -I tools/join.py full_am_onyx 1clement_am_onyx.wav chapters.txt
67 sections, 65.9 min
```

The joined WAV (190 MB) is only an intermediate file. It's encoded in step 7 and then
deleted.

## 7. Encode

Both files are mono at 64 kbps, which is plenty for a single speaking voice and about
6x smaller than the WAV. The metadata and chapters from step 6 are written into both.

```bash
# AAC audiobook, using Apple's AudioToolbox encoder (aac_at); moov atom moved to the front
ffmpeg -i 1clement_am_onyx.wav -i chapters.txt -map 0:a -map_metadata 1 -map_chapters 1 \
  -ac 1 -c:a aac_at -b:a 64k -movflags +faststart out/1clement_am_onyx.m4b

# MP3 for players that can't open .m4b; chapters as ID3v2.3 CHAP frames
ffmpeg -i 1clement_am_onyx.wav -i chapters.txt -map 0:a -map_metadata 1 -map_chapters 1 \
  -ac 1 -c:a libmp3lame -b:a 64k -id3v2_version 3 out/1clement_am_onyx.mp3
```

Before the full run, the same commands were tested on the two sample sections.

**Which file to use:** the `.m4b` in Apple Books or a podcast or audiobook app, which
show the chapters and remember where you stopped. The `.mp3` plays anywhere, but many
MP3 players ignore the chapter markers.

## 8. Verify and clean up

**Output files** (checked with `ffprobe`):

| File | Codec | Duration | Bitrate | Size | Chapters |
|---|---|---|---|---|---|
| `out/1clement_am_onyx.m4b` | AAC, 24 kHz mono | 1:05:54 | 64.8 kbps | 32.0 MB | 67 |
| `out/1clement_am_onyx.mp3` | MP3, 24 kHz mono | 1:05:54 | 64.0 kbps | 31.6 MB | 67 |

Both files report the same chapter start times: Title 0:00, Greeting 0:07,
Chapter 1 0:23, ..., Chapter 64 1:04:48, Chapter 65 1:05:17. The title and artist tags
are present in both.

**Content checks** (`tools/check.py` on the 67 section WAVs):

- **Nothing dropped:** 0 of 67 sections differ. Kokoro's chunk text was compared word
  for word with the cleaned source, which rules out Kokoro silently cutting off text
  that doesn't fit in a chunk.
- **Speaking rate:** median 204 words per minute. The slowest is the title, at 125 wpm,
  because it's short with pauses around it. The fastest is chapter 16, at 238 wpm, the
  long Isaiah 53 quotation. That's within normal pacing variation, and the coverage
  check above already rules out missing text.
- **Clipping:** 8 of 93,282,600 samples are at full scale, about 0.3 ms in total, which
  is inaudible.

**Cleaned up:** the per-section WAVs, the joined WAV, the abandoned `am_fenrir` render,
the voice samples and the encoder test files were all in a temporary scratch directory
and have been deleted. Only the two compressed files in `out/` are kept.
