#!/usr/bin/env python3
"""Join per-section WAVs (from render.py) into one WAV, with 1 s of silence
after each section, and write an ffmpeg metadata file with tags and one
chapter per section: "Title", "Greeting", "Chapter 1"... Chapter boundaries
are in samples (TIMEBASE=1/24000) so they land exactly on the joins.

Tags and chapter names are specific to 1 Clement.

usage: .venv/bin/python -I tools/join.py WAVDIR OUT.wav META.txt
"""
import sys
from pathlib import Path
import numpy as np, soundfile as sf
wavdir, out_wav, meta = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
files = sorted(wavdir.glob("*.wav"))
SR = 24000
pause = np.zeros(int(SR * 1.0), dtype=np.float32)
names = ["Title", "Greeting"] + [f"Chapter {n}" for n in range(1, len(files) - 1)]
lines = [";FFMETADATA1", "title=The First Epistle of Clement to the Corinthians",
         "artist=Clement of Rome", "album=1 Clement (tr. J. B. Lightfoot)", "genre=Audiobook"]
chunks, t = [], 0
for name, f in zip(names, files):
    a, sr = sf.read(f, dtype="float32"); assert sr == SR
    a = np.concatenate([a, pause])
    start, t = t, t + len(a)
    lines += ["[CHAPTER]", "TIMEBASE=1/24000", f"START={start}", f"END={t}", f"title={name}"]
    chunks.append(a)
sf.write(out_wav, np.concatenate(chunks), SR)
Path(meta).write_text("\n".join(lines) + "\n")
print(f"{len(files)} sections, {t/SR/60:.1f} min")
