#!/usr/bin/env python3
"""Try out two open-source TTS engines: Piper (fast, offline, multilingual)
and Kokoro (slower, more natural-sounding English).

Examples:
    ./tts.py "Hello there"                          # Piper, default English voice
    ./tts.py -v nl_NL-ronnie-medium "Goedemorgen"   # Piper, Dutch
    ./tts.py -e kokoro "Hello there"                # Kokoro
    ./tts.py -e kokoro -v am_michael "Hello there"
    ./tts.py --list                                 # show available voices
    ./tts.py -i chapter.txt -o book.wav --no-play   # read from a file
"""
import os
import sys
from pathlib import Path

# Re-exec under this project's venv so ./tts.py works from a fresh clone
# without anyone having to activate anything first.
_VENV = Path(__file__).resolve().parent / ".venv" / "bin" / "python"
if Path(sys.prefix).resolve() != _VENV.parent.parent and _VENV.exists():
    os.execv(str(_VENV), [str(_VENV), str(Path(__file__).resolve()), *sys.argv[1:]])
if not _VENV.exists():
    sys.exit("Missing .venv/ - run ./setup.sh first.")

import argparse
import subprocess
import warnings

ROOT = Path(__file__).resolve().parent
VOICES = ROOT / "voices"
OUT = ROOT / "out"

# A handful of Kokoro voices; the full set lives at hf.co/hexgrad/Kokoro-82M
KOKORO_VOICES = {
    "af_heart": "US female, warm (default)",
    "af_bella": "US female, expressive",
    "af_nicole": "US female, soft/ASMR",
    "am_michael": "US male",
    "am_fenrir": "US male, deeper",
    "bf_emma": "UK female",
    "bm_george": "UK male",
}


def list_voices():
    print("Piper voices (offline, in ./voices):")
    for f in sorted(VOICES.glob("*.onnx")):
        print(f"  {f.stem}")
    print("\n  More: python -m piper.download_voices --download-dir voices <name>")
    print("  Catalogue: https://huggingface.co/rhasspy/piper-voices\n")
    print("Kokoro voices (downloaded on first use):")
    for name, desc in KOKORO_VOICES.items():
        print(f"  {name:<12} {desc}")


def piper(text, voice, out_path, speed):
    model = VOICES / f"{voice}.onnx"
    if not model.exists():
        sys.exit(f"No such Piper voice: {voice}\nRun --list to see what's installed.")
    subprocess.run(
        [str(Path(sys.executable).with_name("piper")), "-m", str(model), "-f", str(out_path),
         "--length-scale", str(1.0 / speed)],
        input=text, text=True, check=True,
    )


KOKORO_CACHE = Path.home() / ".cache/huggingface/hub/models--hexgrad--Kokoro-82M/snapshots"


def kokoro_is_cached(voice):
    """True if both the model and this particular voice are already downloaded."""
    if not KOKORO_CACHE.is_dir():
        return False
    return any((snap / "kokoro-v1_0.pth").exists() and (snap / "voices" / f"{voice}.pt").exists()
               for snap in KOKORO_CACHE.iterdir())


def kokoro(text, voice, out_path, speed):
    # Kokoro re-validates its files against the HuggingFace Hub on *every* run,
    # even when they're already cached. That needs a network round-trip, slows
    # startup, and makes the Hub echo back a "set an HF_TOKEN for higher rate
    # limits" warning. Once model + voice are on disk, pin it offline instead.
    if kokoro_is_cached(voice):
        os.environ["HF_HUB_OFFLINE"] = "1"   # must be set before the import below
    else:
        print(f"Downloading Kokoro model/voice '{voice}' (first use only)...", file=sys.stderr)

    # Kokoro's architecture trips two torch deprecation warnings on load; nothing
    # we can act on from here.
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning, module=r"torch\..*")

    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    # 'b' selects the British-English G2P for the bf_/bm_ voices.
    pipeline = KPipeline(lang_code="b" if voice.startswith(("bf_", "bm_")) else "a",
                         repo_id="hexgrad/Kokoro-82M")
    chunks = [audio for _, _, audio in pipeline(text, voice=voice, speed=speed)]
    if not chunks:
        sys.exit("Kokoro produced no audio.")
    sf.write(out_path, np.concatenate(chunks), 24000)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="?", help="text to speak")
    ap.add_argument("-e", "--engine", choices=["piper", "kokoro"], default="piper")
    ap.add_argument("-v", "--voice", help="voice name (see --list)")
    ap.add_argument("-i", "--input-file", help="read text from a file instead")
    ap.add_argument("-o", "--output", help="output WAV path (default: out/<engine>.wav)")
    ap.add_argument("-s", "--speed", type=float, default=1.0, help="1.0 = normal")
    ap.add_argument("--no-play", action="store_true", help="don't play the result")
    ap.add_argument("--list", action="store_true", help="list available voices")
    args = ap.parse_args()

    if args.list:
        list_voices()
        return

    if args.input_file:
        text = Path(args.input_file).read_text()
    elif args.text:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        ap.error("give some text, -i FILE, or pipe it in on stdin")

    voice = args.voice or ("af_heart" if args.engine == "kokoro" else "en_US-lessac-medium")
    OUT.mkdir(exist_ok=True)
    out_path = Path(args.output) if args.output else OUT / f"{args.engine}_{voice}.wav"

    (kokoro if args.engine == "kokoro" else piper)(text, voice, out_path, args.speed)

    print(f"\n-> {out_path}")
    if not args.no_play:
        subprocess.run(["afplay", str(out_path)])


if __name__ == "__main__":
    main()
