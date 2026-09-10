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
A reference sample should be 6-30 seconds of clean speech, no music or noise.

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
