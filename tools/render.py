#!/usr/bin/env python3
"""Render a chaptered text with Kokoro, one WAV per section (resumable).

Sections are blocks separated by blank lines; within a section, each line
(e.g. "Chapter N." then the body) is rendered separately with a pause after it.
Sections whose WAV already exists in OUTDIR are skipped, so an interrupted run
picks up where it stopped. --only N renders just the first N sections (samples).

Needs the repo's .venv (Kokoro).

usage: .venv/bin/python tools/render.py TEXT OUTDIR VOICE [SPEED] [--only N]
"""
import os, re, sys, time, warnings
from pathlib import Path
src, outdir, voice = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
speed = float(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith("--") else 1.0
only = int(sys.argv[sys.argv.index("--only") + 1]) if "--only" in sys.argv else None

snap = Path.home() / ".cache/huggingface/hub/models--hexgrad--Kokoro-82M/snapshots"
if snap.is_dir() and any((s / "voices" / f"{voice}.pt").exists() for s in snap.iterdir()):
    os.environ["HF_HUB_OFFLINE"] = "1"
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
import numpy as np, soundfile as sf
from kokoro import KPipeline

SR = 24000
text = src.read_text()
text = re.sub(r"\s*\{[^}]*\}", "", text)          # drop translator's footnote
text = text.replace("[", "").replace("]", "")     # editorial insertions: keep words
sections = [s.strip() for s in text.split("\n\n") if s.strip()]
outdir.mkdir(parents=True, exist_ok=True)
pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
gap = np.zeros(int(SR * 0.25), dtype=np.float32)
t0 = time.time()
for i, sec in enumerate(sections):
    if only is not None and i >= only:
        break
    f = outdir / f"{i:03d}.wav"
    if f.exists():
        continue
    parts = []
    for line in sec.split("\n"):                   # "Chapter N." then body
        for _, _, audio in pipe(line, voice=voice, speed=speed):
            parts += [np.asarray(audio, dtype=np.float32), gap]
        parts.append(np.zeros(int(SR * 0.5), dtype=np.float32))
    sf.write(f, np.concatenate(parts), SR)
    dur = sf.info(f).duration
    print(f"[{i+1}/{len(sections)}] {dur:6.1f}s audio, {time.time()-t0:7.1f}s elapsed", flush=True)
