#!/usr/bin/env python3
"""Sanity-check rendered sections against the source text.

1. Coverage: re-runs Kokoro's text chunking (no audio) and compares the words
   it would speak with the source, section by section. Kokoro can drop text
   that doesn't fit in a chunk, so any mismatch here means missing words.
2. Speaking rate per section (words/min); an outlier that's much faster than
   the median also hints at dropped text.
3. Clipping: number of samples at or near full scale.

Applies the same clean-up as render.py before comparing.

usage: .venv/bin/python -I tools/check.py TEXT WAVDIR
"""
import os, re, sys, warnings
from pathlib import Path
os.environ["HF_HUB_OFFLINE"] = "1"
warnings.filterwarnings("ignore")
import numpy as np, soundfile as sf
from kokoro import KPipeline

text = Path(sys.argv[1]).read_text()
text = re.sub(r"\s*\{[^}]*\}", "", text).replace("[", "").replace("]", "")
secs = [s.strip() for s in text.split("\n\n") if s.strip()]
files = sorted(Path(sys.argv[2]).glob("*.wav"))
if len(files) != len(secs):
    print(f"WARNING: {len(secs)} sections in text, {len(files)} WAVs")

pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", model=False)
norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).split()
bad = 0
for i, sec in enumerate(secs):
    got = []
    for line in sec.split("\n"):
        for r in pipe(line):
            got += norm(r.graphemes)
    if got != norm(sec):
        bad += 1
        print(f"section {i}: source {len(norm(sec))} words, chunks {len(got)} words")
print("sections with text mismatch:", bad)

rates, clip, tot = [], 0, 0
for i, (s, f) in enumerate(zip(secs, files)):
    a, sr = sf.read(f, dtype="float32")
    clip += int((np.abs(a) >= 0.999).sum()); tot += len(a)
    w = len(s.split()); rates.append((w / (len(a) / sr) * 60, i, w, len(a) / sr))
r = np.array([x[0] for x in rates])
print(f"words/min: median {np.median(r):.0f}, min {r.min():.0f}, max {r.max():.0f}")
for wpm, i, w, d in sorted(rates)[:3] + sorted(rates)[-3:]:
    print(f"  section {i:3d}: {w:4d} words, {d:6.1f}s, {wpm:.0f} wpm")
print(f"near-full-scale samples: {clip} of {tot} ({clip/tot*100:.5f}%)")
