#!/usr/bin/env python3
"""Coqui XTTS-v2: multilingual TTS with voice cloning from a short sample.

Lives in its own venv (.venv-coqui) because it pins older torch/transformers
than Kokoro does. Use tts.py for Piper and Kokoro.

NOTE: the XTTS-v2 *weights* are under the Coqui Public Model License (CPML),
which is non-commercial only. You must agree to it before the model downloads:
    export COQUI_TOS_AGREED=1
The code itself is MPL-2.0.

Examples:
    ./coqui.py --speakers                                    # built-in voices
    ./coqui.py -S "Claribel Dervla" "Hello there"            # built-in speaker
    ./coqui.py -r me.wav "Hello, this is my cloned voice"    # clone from a sample
    ./coqui.py -r me.wav -l nl "Hallo, dit is mijn stem"     # ...in Dutch
"""
import os
import sys
from pathlib import Path

# Re-exec under this project's venv so ./coqui.py works from a fresh clone
# without anyone having to activate anything first.
_VENV = Path(__file__).resolve().parent / ".venv-coqui" / "bin" / "python"
if Path(sys.prefix).resolve() != _VENV.parent.parent and _VENV.exists():
    os.execv(str(_VENV), [str(_VENV), str(Path(__file__).resolve()), *sys.argv[1:]])
if not _VENV.exists():
    sys.exit("Missing .venv-coqui/ - run ./setup.sh first.")

import argparse
import re
import subprocess

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
LANGS = "en es fr de it pt pl tr ru nl cs ar zh-cn hu ko ja hi".split()


def check_tos():
    if os.environ.get("COQUI_TOS_AGREED") == "1":
        return
    sys.exit(
        "XTTS-v2's weights are under the Coqui Public Model License (non-commercial).\n"
        "Read it at https://coqui.ai/cpml, then, if you accept:\n\n"
        "    export COQUI_TOS_AGREED=1\n"
    )


def use_soundfile_for_decoding():
    """Decode the reference clip with soundfile instead of torchcodec.

    torchaudio 2.11 routes every load() through torchcodec, which needs FFmpeg's
    shared libraries. That can fail for reasons unrelated to this project - on
    macOS 26 with MacPorts FFmpeg, libavfilter references _CGLGetCurrentContext,
    an OpenGL symbol Apple removed, so no torchcodec backend loads at all.

    XTTS only decodes one thing (the speaker reference); resampling afterwards is
    pure torch. soundfile reads WAV/FLAC/OGG with no FFmpeg involved, so prefer
    it and keep torchaudio as the fallback for anything it can't open.
    """
    import soundfile as sf
    import torch
    import torchaudio

    original_load = torchaudio.load

    def load_via_soundfile(path, *args, **kwargs):
        try:
            data, rate = sf.read(str(path), dtype="float32", always_2d=True)
        except Exception:
            return original_load(path, *args, **kwargs)
        return torch.from_numpy(data.T).contiguous(), rate

    torchaudio.load = load_via_soundfile


def load():
    from TTS.api import TTS
    import torch

    use_soundfile_for_decoding()
    # Apple Silicon GPU where possible; XTTS falls back to CPU for some ops.
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    return TTS(MODEL).to(device)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="?")
    ap.add_argument("-r", "--reference", help="WAV of the voice to clone (6+ seconds)")
    ap.add_argument("-S", "--speaker", help="built-in speaker name (see --speakers)")
    ap.add_argument("-l", "--lang", default="en", choices=LANGS)
    ap.add_argument("-i", "--input-file")
    ap.add_argument("-o", "--output")
    ap.add_argument("--no-play", action="store_true")
    ap.add_argument("--speakers", action="store_true", help="list built-in speakers")
    args = ap.parse_args()

    check_tos()

    if args.speakers:
        for name in load().synthesizer.tts_model.speaker_manager.speakers:
            print(f"  {name}")
        return

    if args.input_file:
        text = Path(args.input_file).read_text()
    elif args.text:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        ap.error("give some text, -i FILE, or pipe it in on stdin")

    if not args.reference and not args.speaker:
        ap.error("pick a voice: -r sample.wav to clone one, or -S NAME (see --speakers)")

    if args.reference and not Path(args.reference).is_file():
        sys.exit(
            f"No such reference file: {args.reference}\n"
            "-r takes a recording of the voice you want to clone: 6-30 seconds of\n"
            "clean speech as WAV, FLAC or OGG. On macOS you can record one with\n"
            "Voice Memos, or from the terminal with:\n"
            "    ffmpeg -f avfoundation -i :default -t 15 me.wav"
        )

    OUT.mkdir(exist_ok=True)
    if args.output:
        out_path = Path(args.output)
    else:
        # Name the file after the voice as well as the language, so trying a
        # second speaker doesn't quietly overwrite the take you liked.
        voice = Path(args.reference).stem if args.reference else args.speaker
        slug = re.sub(r"[^a-z0-9]+", "_", voice.lower()).strip("_")
        out_path = OUT / f"coqui_{args.lang}_{slug}.wav"

    kwargs = {"speaker_wav": args.reference} if args.reference else {"speaker": args.speaker}
    load().tts_to_file(text=text, language=args.lang, file_path=str(out_path), **kwargs)

    print(f"\n-> {out_path}")
    if not args.no_play:
        subprocess.run(["afplay", str(out_path)])


if __name__ == "__main__":
    main()
