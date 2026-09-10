#!/Users/rene/dev/text2speech/.venv-coqui/bin/python
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
import argparse
import os
import subprocess
import sys
from pathlib import Path

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


def load():
    from TTS.api import TTS
    import torch
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

    OUT.mkdir(exist_ok=True)
    out_path = Path(args.output) if args.output else OUT / f"coqui_{args.lang}.wav"

    kwargs = {"speaker_wav": args.reference} if args.reference else {"speaker": args.speaker}
    load().tts_to_file(text=text, language=args.lang, file_path=str(out_path), **kwargs)

    print(f"\n-> {out_path}")
    if not args.no_play:
        subprocess.run(["afplay", str(out_path)])


if __name__ == "__main__":
    main()
