#!/usr/bin/env python3
"""Join a pilot run's section WAVs into one WAV for listening, with 1 s of
silence after each section, at the run's own sample rate.

usage: .venv-mlx/bin/python -I tools/pilot_join.py RUNDIR OUT.wav
"""
import sys
from pathlib import Path
import numpy as np, soundfile as sf
files = sorted(Path(sys.argv[1]).glob("[0-9][0-9][0-9].wav"))
parts, sr0 = [], None
for f in files:
    a, sr = sf.read(f, dtype="float32"); sr0 = sr0 or sr; assert sr == sr0
    parts += [a, np.zeros(sr, dtype=np.float32)]
sf.write(sys.argv[2], np.concatenate(parts), sr0)
print(f"{Path(sys.argv[2]).name}: {len(files)} sections, {sum(map(len, parts))/sr0/60:.1f} min, {sr0} Hz")
