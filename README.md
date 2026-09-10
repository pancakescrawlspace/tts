# Local text-to-speech playground

Three open-source, fully offline TTS engines.

| | Piper | Kokoro | Coqui XTTS-v2 |
|---|---|---|---|
| Quality | Good, slightly robotic | Noticeably more natural | Very good, clones voices |
| Speed | ~8x faster than real-time | ~1-2x real-time | Slower than real-time |
| Languages | 30+, incl. Dutch | English (US/UK) | 17, incl. Dutch |
| Size | 60 MB per voice | 330 MB + ~2 GB PyTorch | ~2 GB + ~2.5 GB PyTorch |
| Licence | MIT | Apache 2.0 | Code MPL-2.0, **weights non-commercial** |
| Venv | `.venv/` | `.venv/` | `.venv-coqui/` |
| Script | `tts.py` | `tts.py` | `coqui.py` |

Coqui needs its own venv: it pins `transformers<5`, which would break Kokoro.

## Setup

```bash
git clone <this repo> && cd text2speech
./setup.sh
```

`setup.sh` builds both venvs from the pinned requirements and downloads the Piper
voices (~370 MB). It's re-runnable and skips whatever is already there. Needs
Python 3.10-3.12; override with `PYTHON=/path/to/python3.11 ./setup.sh`.

**Don't clone this somewhere with a very long path.** espeak-ng, which both Piper and
Kokoro use for grapheme-to-phoneme conversion, holds its data directory in a fixed
160-byte buffer (`N_PATH_HOME`). Past that it silently falls back to a path baked in
on its build machine and every synthesis fails with:

```
Error processing file '/Users/runner/work/piper1-gpl/.../espeak-ng-data/phontab'
```

Measured: a data dir at 145 chars works, 165 fails. `~/dev/text2speech` lands around
83, so this only bites in deeply nested directories. It's an upstream espeak-ng
limitation, not something this repo can work around.

The scripts re-exec themselves under the right venv, so there's nothing to activate.

## Usage

```bash
./tts.py "Hello there"                          # Piper, US English, plays it
./tts.py -v nl_NL-ronnie-medium "Goedemorgen"   # Piper, Dutch
./tts.py -e kokoro "Hello there"                # Kokoro
./tts.py -e kokoro -v bm_george "Hello there"   # Kokoro, UK male
./tts.py --list                                 # all installed voices
./tts.py -s 1.2 "A little faster"               # speed
./tts.py -i chapter.txt -o book.wav --no-play   # a whole text file
cat notes.md | ./tts.py                         # or pipe it in
```

WAVs land in `out/`. Playback uses macOS `afplay`.

## Coqui XTTS-v2 (voice cloning)

The XTTS-v2 **weights** are under the [Coqui Public Model License](https://coqui.ai/cpml)
— non-commercial use only. The model won't download until you agree:

```bash
export COQUI_TOS_AGREED=1
```

```bash
./coqui.py --speakers                                 # ~50 built-in voices
./coqui.py -S "Claribel Dervla" "Hello there"         # use a built-in voice
./coqui.py -r me.wav "This should sound like me"      # clone from a 6s+ sample
./coqui.py -r me.wav -l nl "Dit is mijn eigen stem"   # cloned voice, in Dutch
```

Languages: en es fr de it pt pl tr ru nl cs ar zh-cn hu ko ja hi.

`-r` needs a real recording of the voice you want to clone - `me.wav` above is a
placeholder, not a file that ships with this repo. Aim for 6-30 seconds of clean
speech, no music or background noise, as WAV, FLAC or OGG. Record one with Voice
Memos, or:

```bash
ffmpeg -f avfoundation -i :default -t 15 me.wav
```

### Why decoding goes through soundfile

torchaudio 2.11 routes every `load()` through torchcodec, which needs FFmpeg's
shared libraries. On macOS 26 with MacPorts FFmpeg that fails for every backend
version, because `libavfilter` references `_CGLGetCurrentContext` - an OpenGL
symbol Apple removed - and the error surfaces as a wall of `dlopen` tracebacks
ending in `Failed to create AudioDecoder`.

XTTS only decodes one file (the reference clip), and resampling afterwards is pure
torch, so `coqui.py` points `torchaudio.load` at soundfile, which reads WAV/FLAC/OGG
without FFmpeg. torchaudio stays as the fallback for formats soundfile can't open.

## Adding voices

Piper (see the [catalogue](https://huggingface.co/rhasspy/piper-voices)):

```bash
.venv/bin/python -m piper.download_voices --download-dir voices de_DE-thorsten-medium
```

Kokoro voices download automatically on first use; the full list is at
[hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M/tree/main/voices).

## Notes

- This python.org Python ships without a CA bundle, so model downloads failed with
  `CERTIFICATE_VERIFY_FAILED`. `.venv/.../sitecustomize.py` points it at `certifi`.
- Kokoro used to print an HF Hub rate-limit warning on every run. The cause was that
  it re-validates its model against the Hub each time, even when fully cached. `tts.py`
  now sets `HF_HUB_OFFLINE=1` once model + requested voice are on disk, so runs are
  genuinely offline and silent; an uncached voice still downloads normally. Its two
  PyTorch deprecation warnings are filtered in the same place.
- Coqui still prints PyTorch deprecation warnings on startup; harmless.
- coqui-tts needed two fixes beyond `pip install`: `transformers<5` (5.x dropped a
  function it calls) and the `[codec]` extra (torch 2.9+ moved audio IO to torchcodec).
- Models cache in `~/Library/Application Support/tts/`, not in this directory.
