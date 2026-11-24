# Audiobook to video: one still picture plus the audio

How to turn a finished audiobook (MP3 or M4B) into an MP4 that shows one picture for the
whole length, e.g. to upload as a podcast video. The video track stays tiny, so the file is
barely bigger than the audio. Worked out and tested 2026-11-24 on
`out/1clement_dyer_voxcpm2.mp3` (85 min) with ffmpeg 9.0.2.

**The Jay Dyer audiobooks are for private use only** (see
[1clement-audiobook-dyer.md](1clement-audiobook-dyer.md)). Making an MP4 of one for
yourself is fine. An unlisted video is not: anyone with the link can watch it.

One exception, the user's own decision on 2026-11-24: the Dyer 1 Clement MP4 was uploaded
as a **Private** YouTube video, shared with one friend by email invite, with the AI
disclosure set to "Yes" (see [Uploading to YouTube](#uploading-to-youtube)). That covers this one file for this one person only. It doesn't extend
to other files, other people, or unlisted or public uploads.

Voices that may be published, like the designed "British elder" voice
([1clement-audiobook-british-elder.md](1clement-audiobook-british-elder.md)), can be
uploaded however you like.

## Command

```bash
ffmpeg -loop 1 -framerate 1 -i cover.jpg -i out/BOOK.m4b \
  -map 0:v -map 1:a -map_chapters -1 \
  -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
  -c:v libx264 -tune stillimage -crf 28 \
  -c:a copy -shortest -movflags +faststart \
  out/BOOK.mp4
```

Replace `cover.jpg` with the picture and `BOOK` with the audiobook's name. The audio can
come from either encoding:

- **The `.m4b` (recommended):** its AAC audio goes into the MP4 unchanged. AAC is the
  standard audio format for MP4, so every player and site accepts it.
- **The `.mp3`:** also works with the same command, and also isn't re-encoded. MP4 can
  hold MP3 audio, and YouTube and most players accept it. If one doesn't, swap
  `-c:a copy` for `-c:a aac -b:a 96k`. That re-encodes the voice, which loses a little
  quality.

## What the options do

| Option | Why |
|---|---|
| `-loop 1 -framerate 1` | Repeats the picture once per second instead of 25–30 times. A still picture doesn't need more. |
| `-map 0:v -map 1:a` | Takes the picture from the first input and the audio from the second. |
| `-map_chapters -1` | Leaves out the chapter markers. See [Chapters](#chapters) for why. |
| `scale=…,pad=…` | Fits any picture into 1280×720 and adds black bars where its shape doesn't match. Use `1920:1080` in both places for full HD. The file grows only slightly. |
| `format=yuv420p` | The pixel format QuickTime, phones and browsers need. Without it, a PNG source can give a video that won't play there. |
| `-tune stillimage -crf 28` | Tells the encoder the picture never changes, so every frame after the first costs almost nothing. |
| `-c:a copy` | Puts the audio in as-is, with no quality loss and no encoding time. |
| `-shortest` | Ends the video when the audio ends. Without it the looped picture never stops. |
| `-movflags +faststart` | Moves the index to the front of the file, so playback can start before the download finishes. |

## The picture

- 16:9 fits the frame exactly: 1280×720, 1920×1080 or larger. Other shapes get black bars.
  A portrait picture gets wide bars on both sides.
- JPG, PNG and WebP all work. ffmpeg goes by the file's contents, not its name: the icon
  used for 1 Clement is a WebP saved as `.jpg`, and the command handled it unchanged.
- Text in the picture should be readable at phone size. A 1280×720 frame is often shown
  much smaller than that.

## Results

On the 85-minute 1 Clement audiobook:

| Picture | Audio source | Video track | MP4 size | Audio file size | Time |
|---|---|---|---|---|---|
| test pattern, 1600×1000 | `.mp3` | 2.5 kbit/s | 42.5 MB | 40.7 MB | about 20 s |
| test pattern, 1600×1000 | `.m4b` | 2.5 kbit/s | 43.4 MB | 41.7 MB | about 20 s |
| icon of St Clement, 647×906 | `.mp3` | 9.3 kbit/s | 46.8 MB | 40.7 MB | 13 s |

The last row is the real video, `out/1clement_dyer_voxcpm2.mp4` (private, see above). Its
detailed, textured picture costs about 6 MB of video over the whole length, against 1.6 MB
for the plain test pattern. Either way, most of the file is the audio.

To check a result:

```bash
ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,bit_rate -of csv=p=0 out/BOOK.mp4
```

## Uploading to YouTube

Checked on 2026-11-24, when the Dyer MP4 was shared:

- **Videos over 15 minutes need a verified account** (phone number, at youtube.com/verify).
- **The AI disclosure is hidden at first.** In the upload dialog, on the first tab
  ("Details"), click **"Show more"**. The question is "Was AI used to generate or edit your
  content in any of the following ways?". For a cloned voice of a real person, set "Make a
  real person appear to say or do something they didn't say or do…" to **Yes**. Older help
  pages call this setting "altered content".
- **Private, not Unlisted, for sharing with specific people.** A private video plays only
  for the Google accounts you invite by email. Anyone else who gets the link can't watch.
- **Chapters:** paste the timestamp list (see below) into the description.

## Chapters

The audiobooks have chapter markers (67 for 1 Clement), but the command above leaves them
out on purpose. **ffmpeg 9.0.2 writes broken chapters into MP4 files longer than about 18
minutes.** In the test, chapters 59–65 all ended up at 18:19 (1099 s) instead of their real
times, and ffmpeg warned `Application provided duration … is invalid`. The bug is in the
MP4 writer: it happens with audio only, too, and with every workaround tried (a fixed video
timescale, audio as the first track, chapters from a metadata file, a coarser chapter
timebase).

If chapters are needed:

- **YouTube** doesn't read chapters stored in the file anyway. It builds them from
  timestamps in the video description. This prints such a list from the audiobook's
  chapters:

  ```bash
  ffprobe -v error -show_chapters -of csv=p=0:s='|' \
    -show_entries chapter=start_time,end_time:chapter_tags=title out/BOOK.mp3 \
  | awk -F'|' '{ if (p == "") p = $1
      if ($2 - p < 10) next
      s = int(p + 0.5); h = int(s/3600); m = int(s%3600/60); x = s%60
      if (h) printf "%d:%02d:%02d %s\n", h, m, x, $3; else printf "%d:%02d %s\n", m, x, $3
      p = "" }'
  ```

  YouTube wants every chapter to be at least 10 seconds long, so a shorter one is merged
  into the next. For 1 Clement, the 8.5-second "Title" merges into "Greeting", and the
  list starts `0:00 Greeting`, `0:27 Chapter 1`, `1:54 Chapter 2`.
- **For playing locally,** write `.mkv` instead of `.mp4`, leave out `-map_chapters -1`
  and `-movflags +faststart`, and keep everything else. Tested: all 67 chapters come
  through in the right order and with the right lengths. Each starts 23 ms earlier than in
  the MP3, which is the MP3's encoder delay being trimmed and too small to hear.
- **Later ffmpeg versions** may fix the bug. To test one, run the command without
  `-map_chapters -1` and compare
  `ffprobe -show_chapters out/BOOK.mp4` with the same command on the audiobook.
