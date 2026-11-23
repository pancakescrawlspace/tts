#!/usr/bin/env python3
"""Render REF_TXT with Phonon's default voice and each English male voice from
gradium/phonon-voices, and rank them by ECAPA speaker similarity to REF_WAV.

Phonon's open checkpoint can't clone from audio, so this is how the pilot
picked the preset voice closest to the reference. Writes OUTDIR/<voice>.wav.

usage: .venv-mlx/bin/python tools/phonon_voices.py REF_WAV REF_TXT OUTDIR
"""
import sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, soundfile as sf, mlx.core as mx
from scipy.signal import resample_poly
from mlx_audio.tts.utils import load
from mlx_audio.codec.models.ecapa_tdnn.speaker import EcapaSpeakerEmbeddingExtractor

ref_wav, ref_txt, outdir = sys.argv[1], Path(sys.argv[2]).read_text().strip(), Path(sys.argv[3])
outdir.mkdir(parents=True, exist_ok=True)
V = {"us_easton": "LMDIYE0Oa377Qh6Z", "us_micah": "40QrMVgAxFiUnP9f", "us_trevor": "0zLApsZfVLLNaEGl",
     "us_russell": "_6Aslh2DxfmnRLmP", "us_preston": "qIxlZ7Ei8KvWlyQH", "us_miles": "d9XCyhjo4JhkHF1d",
     "uk_alfie": "X6NceqF285Gr04gb", "uk_hugh": "YyKcxPG7iIgS3jsK", "uk_edwin": "zUCxzrOrugTSis03",
     "uk_spencer": "JOW0vchyswkQUMDS", "uk_toby": "dME3IWyZBvmh1n1q", "uk_teddy": "Zn7g6NxLqXlJb7Qi"}
spk = EcapaSpeakerEmbeddingExtractor.from_pretrained()
def emb(a, sr):
    a = resample_poly(a, 16000, sr).astype(np.float32)
    return np.array(spk.encode(a))
r, rsr = sf.read(ref_wav, dtype="float32"); e0 = emb(r, rsr)
model = load("gradium/phonon-31m-en")
rows = []
for name, vid in [("default", "default")] + list(V.items()):
    voice = vid if vid == "default" else f"hf://gradium/phonon-voices/voices/{vid}.safetensors"
    mx.random.seed(0)
    a = np.concatenate([np.asarray(x.audio, dtype=np.float32).reshape(-1) for x in model.generate(text=ref_txt, voice=voice)])
    sf.write(outdir / f"{name}.wav", a, model.sample_rate)
    rows.append((float(e0 @ emb(a, model.sample_rate)), name, len(a) / model.sample_rate))
for s, n, d in sorted(rows, reverse=True):
    print(f"{n:12s} sim {s:.3f}  {d:5.2f}s")
