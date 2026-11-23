#!/usr/bin/env python3
"""Render a chaptered text with an MLX TTS engine, one WAV per section (resumable).

The pilot counterpart of render.py, for the engines in docs/pilot-2026-11.md.
It applies the same text clean-up and section layout: each line of a section
("Chapter N." then the body) is rendered separately, followed by 0.5 s of
silence.

  phonon   gradium/phonon-31m-en                  splits long text itself
  drama3   mlx-community/fish-audio-drama-3-4bit  splits long text itself
  voxcpm2  mlx-community/VoxCPM2-bf16             no splitting of its own: the body is cut
                                                  into chunks of at most 300 characters
                                                  at sentence ends, with 0.25 s between them

A sentence too long for one chunk is cut at ; or :, then at commas, so the
next chunk starts mid-sentence in lowercase ("who with lowliness..."). Each
chunk is given to the model with its first letter capitalised. Without that,
the VoxCPM2 clone of Tim Dillon garbled or prefixed such openings in 5 of 8
test takes ("Dot who", "Wahu, with", "God to him be"); capitalised, all 8
were clean. See docs/1clement-audiobook-dillon.md.

The voice is cloned from REF_WAV, with its transcript REF_TXT (Drama 3 needs
the transcript), so every engine reads in the same voice. --voice default
uses Phonon's built-in voice instead. --vox-mode picks how VoxCPM2 uses the
reference: "ref" (audio only), "prompt" (audio + transcript as a
continuation prompt) or "both".

Writes OUTDIR/NNN.wav (native sample rate, 16-bit) and one JSON line per
section to OUTDIR/timings.jsonl. Sections that already exist are skipped.

usage: .venv-mlx/bin/python tools/pilot_render.py ENGINE TEXT OUTDIR REF_WAV REF_TXT
           [--only N] [--voice default] [--vox-mode ref|prompt|both] [--seed S]
"""
import argparse, json, re, time, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np, soundfile as sf
import mlx.core as mx
from mlx_audio.tts.utils import load
from textchunks import chunks          # VoxCPM2 only; Drama 3's own splitter uses 300 bytes too

REPOS = {
    "phonon": "gradium/phonon-31m-en",
    "drama3": "mlx-community/fish-audio-drama-3-4bit",
    "voxcpm2": "mlx-community/VoxCPM2-bf16",
}

ap = argparse.ArgumentParser()
ap.add_argument("engine", choices=REPOS)
ap.add_argument("text", type=Path)
ap.add_argument("outdir", type=Path)
ap.add_argument("ref_wav")
ap.add_argument("ref_txt", type=Path)
ap.add_argument("--only", type=int)
ap.add_argument("--voice")
ap.add_argument("--vox-mode", default="ref", choices=["ref", "prompt", "both"])
ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()

text = args.text.read_text()
text = re.sub(r"\s*\{[^}]*\}", "", text)          # drop translator's footnote
text = text.replace("[", "").replace("]", "")     # editorial insertions: keep words
sections = [s.strip() for s in text.split("\n\n") if s.strip()]
ref_text = args.ref_txt.read_text().strip()


def kwargs():
    if args.engine == "phonon":
        return {"voice": args.voice} if args.voice else {"ref_audio": args.ref_wav}
    if args.engine == "drama3":
        return {"ref_audio": args.ref_wav, "ref_text": ref_text}
    kw = {}
    if args.vox_mode in ("ref", "both"):
        kw["ref_audio"] = args.ref_wav
    if args.vox_mode in ("prompt", "both"):
        kw.update(prompt_audio=args.ref_wav, prompt_text=ref_text)
    return kw


mx.random.seed(args.seed)
t = time.time()
model = load(REPOS[args.engine])
print(f"loaded {REPOS[args.engine]} in {time.time() - t:.1f}s", flush=True)
sr = model.sample_rate
kw = kwargs()


def say(line):
    """Audio for one line, plus the number of generate() calls it took."""
    parts = chunks(line) if args.engine == "voxcpm2" else [line]
    gap = np.zeros(int(sr * 0.25), dtype=np.float32)
    out = []
    for i, p in enumerate(parts):
        if i:
            out.append(gap)
        if args.engine == "voxcpm2":
            p = p[:1].upper() + p[1:]            # mid-sentence starts get garbled otherwise
        for r in model.generate(text=p, **kw):
            out.append(np.asarray(r.audio, dtype=np.float32).reshape(-1))
    return np.concatenate(out), len(parts)


args.outdir.mkdir(parents=True, exist_ok=True)
log = (args.outdir / "timings.jsonl").open("a")
pause = np.zeros(int(sr * 0.5), dtype=np.float32)
for i, sec in enumerate(sections):
    if args.only is not None and i >= args.only:
        break
    f = args.outdir / f"{i:03d}.wav"
    if f.exists():
        continue
    t, parts, calls = time.time(), [], 0
    for line in sec.split("\n"):                   # "Chapter N." then body
        audio, n = say(line)
        parts += [audio, pause]
        calls += n
    audio = np.concatenate(parts)
    sf.write(f, audio, sr)
    wall = time.time() - t
    rec = {"section": i, "audio_s": round(len(audio) / sr, 2), "wall_s": round(wall, 2),
           "calls": calls, "peak_gb": round(mx.get_peak_memory() / 1e9, 2), "sr": sr}
    log.write(json.dumps(rec) + "\n"); log.flush()
    print(f"[{i + 1}/{len(sections)}] {rec['audio_s']:6.1f}s audio in {wall:6.1f}s "
          f"({rec['audio_s'] / wall:4.2f}x realtime), peak {rec['peak_gb']} GB", flush=True)
