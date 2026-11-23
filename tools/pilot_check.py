#!/usr/bin/env python3
"""Check pilot renders for the things that break audiobooks.

DIR holds the section WAVs from pilot_render.py or render.py. Each DIR gets:

1. Speed: audio seconds per wall-clock second, from DIR/timings.jsonl when present.
2. Words: each WAV is transcribed by two different recognisers (cached in
   DIR/asr_parakeet/ and DIR/asr_whisper/) and each transcript is aligned with
   the cleaned source text. Reported:
   - WER: per section the lower of the two, so an upper bound on the TTS's errors.
   - Errors: runs of 3+ words that differ from the source.
     Dropped or replaced: listed only when both transcripts have such a run at
     that spot. Each recogniser sometimes loses text that was spoken, each in
     its own way, but text the TTS really skipped is missing for both. (A
     two-word spelling difference such as "round about"/"roundabout" doesn't
     count as agreeing.)
     Added (repeats, made-up text, fillers like "uh"): Parakeet alone. Whisper
     writes tidy transcripts: in a self-test it left out a 4 s repeat that
     Parakeet reported, and it sometimes invents sentences of its own.
   Both recognisers stumble on archaic words and names, so compare against the
   Kokoro baseline.
3. Voice: ECAPA speaker embeddings of 6 s windows. "ref" is the cosine
   similarity with REF_WAV (how well the clone matches the reference).
   "self" is the similarity with the DIR's own average voice (whether the voice
   stays the same all the way through). The windows with the lowest "self"
   score are listed with their position.
4. Level: loudness spread across sections (dB), clipped samples, words/minute.

The recognisers (--asr both, the default; or just one of them):
  parakeet  mlx-community/parakeet-tdt-0.6b-v3, in pieces of at most 30 s cut
            at pauses. Detects the language itself (25 European languages,
            Dutch included). Dropped the last sentence of a 102 s section
            when given the whole section at once.
  whisper   mlx-community/whisper-large-v3-turbo, in pieces of at most 15 s cut
            at pauses, language from --lang (default en). Now and then returns
            a piece cut short ("Chapter 1." for 13 s of speech).
Numbers are only spelled out in English, so for other languages keep digits
out of the text.

--chunk-starts (for VoxCPM2 runs): also checks every chunk that starts
mid-sentence (see textchunks.py), and lists those whose first words both
recognisers mishear. That's where a cloned voice garbled or prefixed the
opening ("Dot who, with lowliness"): one wrong word, too small for the
3-word rule, but audible.

usage: .venv-mlx/bin/python tools/pilot_check.py [--asr both|parakeet|whisper] [--lang nl]
           [--chunk-starts] TEXT REF_WAV DIR [DIR ...]
"""
import difflib, json, re, sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np, soundfile as sf
from scipy.signal import resample_poly

argv = sys.argv[1:]
chunk_starts = "--chunk-starts" in argv
argv = [x for x in argv if x != "--chunk-starts"]
opts = {"--asr": "both", "--lang": "en"}
while argv[:1] and argv[0] in opts:
    opts[argv[0]], argv = argv[1], argv[2:]
asr, lang = opts["--asr"], opts["--lang"]
text_path, ref_wav, dirs = Path(argv[0]), argv[1], [Path(d) for d in argv[2:]]
text = re.sub(r"\s*\{[^}]*\}", "", text_path.read_text()).replace("[", "").replace("]", "")
secs = [s.strip() for s in text.split("\n\n") if s.strip()]

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def num(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + num(n % 100))


def words(s):
    s = re.sub(r"\d+", lambda m: num(int(m.group())) if int(m.group()) < 1000 else m.group(), s)
    return re.sub(r"[^\w']+", " ", s.lower().replace("’", "'")).split()   # keeps é, ë, ...


def wer(ref, hyp):
    prev = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        cur = [i] + [0] * len(hyp)
        for j, h in enumerate(hyp, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (r != h))
        prev = cur
    return prev[-1]


def to16k(a, sr):
    return resample_poly(a, 16000, sr).astype(np.float32) if sr != 16000 else a


def pieces16(a, max_s=15):
    """Cut 16 kHz audio at pauses into pieces under max_s seconds (default 15).

    Whisper's own long-form decoding skips a whole 30 s window when a window
    ends right after a short phrase (here: "Chapter N." and its pause), which
    shows up as dropped text that was actually spoken. One window per piece
    avoids that. Pieces near 30 s still sometimes came back as only their last
    sentence; 15 s pieces didn't.
    """
    hop = 320
    rms = np.sqrt((a[: len(a) // hop * hop].reshape(-1, hop) ** 2).mean(axis=1))
    quiet = rms < rms.max() * 0.02
    cuts, run = [], 0
    for k, q in enumerate(quiet):            # middle of every pause of 160 ms or more
        run = run + 1 if q else 0
        if run == 8:
            cuts.append((k - 4) * hop)
    out, start = [], 0
    while len(a) - start > max_s * 16000:
        ok = [c for c in cuts if start + 5 * 16000 < c <= start + max_s * 16000]
        end = ok[-1] if ok else start + max_s * 16000
        out.append(a[start:end]); start = end
    return out + [a[start:]]


ENGINES = ["parakeet", "whisper"] if asr == "both" else [asr]
models, spk = {}, None


def transcribe(engine, a16):
    from mlx_audio.stt.utils import load as load_stt
    loud = lambda p: np.abs(p).max() > 0.1 * np.abs(a16).max()   # skip near-silence
    if engine == "parakeet":
        import mlx.core as mx
        m = models.get(engine) or models.setdefault(engine, load_stt("mlx-community/parakeet-tdt-0.6b-v3"))
        return " ".join(m.generate(mx.array(p)).text.strip() for p in pieces16(a16, 30) if loud(p))
    if engine not in models:
        m = models[engine] = load_stt("mlx-community/whisper-large-v3-turbo")
        if getattr(m, "_processor", None) is None:
            # this MLX conversion ships without tokenizer files
            from huggingface_hub import snapshot_download
            from transformers import WhisperProcessor
            m._processor = WhisperProcessor.from_pretrained(snapshot_download(
                "openai/whisper-large-v3-turbo", allow_patterns=["*.json", "*.txt"]))
    # Timestamps off: with them on, Whisper stops after "Chapter N." even inside
    # a single window. Near-silent pieces are skipped: Whisper invents sentences.
    return " ".join(models[engine].generate(p, language=lang, condition_on_previous_text=False,
                                            return_timestamps=False).text.strip()
                    for p in pieces16(a16) if loud(p))


def diffs(ref, hyp, min_len):
    """Differences from the source, as (op, ref_start, ref_end, hyp_text)."""
    sm = difflib.SequenceMatcher(None, ref, hyp, autojunk=False)
    return [(op, i1, max(i2, i1 + 1), " ".join(hyp[j1:j2])) for op, i1, i2, j1, j2 in sm.get_opcodes()
            if op != "equal" and max(i2 - i1, j2 - j1) >= min_len]


r, rsr = sf.read(ref_wav, dtype="float32")
summary = []
for d in dirs:
    files = sorted(d.glob("[0-9][0-9][0-9].wav"))
    if len(files) != len(secs):
        print(f"WARNING {d.name}: {len(secs)} sections in text, {len(files)} WAVs")
    errs = nref = starts_total = 0
    runs, wins, levels, rates, clip, total, dur = [], [], [], [], 0, 0, 0.0
    starts_bad = []
    for i, (sec, f) in enumerate(zip(secs, files)):
        a, sr = sf.read(f, dtype="float32")
        dur += len(a) / sr
        ref, hyps = words(sec), {}
        for e in ENGINES:
            cache = d / f"asr_{e}" / f"{i:03d}.txt"
            if not cache.exists():
                cache.parent.mkdir(exist_ok=True)
                cache.write_text(transcribe(e, to16k(a, sr)) + "\n")
            hyps[e] = words(cache.read_text())
        errs += min(wer(ref, h) for h in hyps.values()); nref += len(ref)
        big = {e: diffs(ref, h, 3) for e, h in hyps.items()}
        seen = []
        for e in ENGINES:
            other = [o for o in ENGINES if o != e]
            for op, s, t, said in big[e]:
                if op == "insert" and other:
                    if e != "parakeet":
                        continue                # Whisper drops repeats and invents text
                    hit = []
                else:
                    hit = [x for o in other for x in big[o] if x[1] < t and s < x[2]]
                    if other and not hit:
                        continue                # one recogniser lost it, not the TTS
                if any(s < t2 and s2 < t for s2, t2 in seen):
                    continue                    # one recogniser only, or already listed
                seen.append((s, t))
                runs.append((i, op, " ".join(ref[s:t]), " / ".join([said] + [x[3] for x in hit])))
        if chunk_starts:                        # openings of chunks cut mid-sentence
            from textchunks import chunks
            lines = sec.split("\n")
            pos = len(words(lines[0])) if len(lines) > 1 else 0
            for c in chunks(lines[-1]):
                if c[:1].islower():
                    heard = []
                    for h in hyps.values():
                        sm = difflib.SequenceMatcher(None, ref, h, autojunk=False)
                        bad = [o for o in sm.get_opcodes()
                               if o[0] != "equal" and o[1] <= pos + 2 and pos - 1 <= max(o[2] - 1, o[1])]
                        heard.append(" ".join(h[max(bad[0][3] - 1, 0):bad[-1][4] + 1]) if bad else None)
                    starts_total += 1
                    if all(heard):
                        starts_bad.append((i, " ".join(words(c)[:4]), " / ".join(heard)))
                pos += len(words(c))
        # level, clipping, rate
        clip += int((np.abs(a) >= 0.999).sum()); total += len(a)
        fr = a[: len(a) // 2400 * 2400].reshape(-1, 2400)  # 0.1 s frames at 24 kHz-ish
        rms = np.sqrt((fr ** 2).mean(axis=1) + 1e-12)
        act = rms[rms > rms.max() * 0.05]
        levels.append(20 * np.log10(np.sqrt((act ** 2).mean())))
        rates.append(len(sec.split()) / (len(a) / sr) * 60)
        # voice windows
        if spk is None:
            from mlx_audio.codec.models.ecapa_tdnn.speaker import EcapaSpeakerEmbeddingExtractor
            spk = EcapaSpeakerEmbeddingExtractor.from_pretrained()
            e_ref = np.array(spk.encode(to16k(r, rsr)))
        a16 = to16k(a, sr)
        for s in range(0, max(1, len(a16) - 16000 * 3), 16000 * 6):
            w = a16[s: s + 16000 * 6]
            if len(w) < 16000 * 3 or np.sqrt((w ** 2).mean()) < 0.01:
                continue
            wins.append((i, s / 16000, np.array(spk.encode(w))))
    E = np.stack([w[2] for w in wins])
    c = E.mean(axis=0); c /= np.linalg.norm(c)
    sim_ref, sim_self = E @ e_ref, E @ c
    t = [json.loads(x) for x in (d / "timings.jsonl").read_text().splitlines()] if (d / "timings.jsonl").exists() else []
    speed = sum(x["audio_s"] for x in t) / sum(x["wall_s"] for x in t) if t else None
    row = {"dir": d.name, "minutes": round(dur / 60, 1), "speed_x": round(speed, 2) if speed else None,
           "peak_gb": max((x["peak_gb"] for x in t if x["peak_gb"] is not None), default=None),
           "wer_pct": round(100 * errs / nref, 2), "runs3": len(runs),
           "ref_sim": round(float(sim_ref.mean()), 3), "self_sim": round(float(sim_self.mean()), 3),
           "self_p5": round(float(np.percentile(sim_self, 5)), 3), "self_min": round(float(sim_self.min()), 3),
           "level_sd_db": round(float(np.std(levels)), 2), "wpm_median": round(float(np.median(rates))),
           "clipped": clip}
    if chunk_starts:
        row["chunk_starts_misheard"] = f"{len(starts_bad)} of {starts_total}"
    summary.append(row)
    print(f"\n== {d.name}")
    for k, v in row.items():
        if k != "dir":
            print(f"  {k:12s} {v}")
    for i, op, rr, hh in runs:
        print(f"  [{op} s{i:02d}] src: {rr[:90]!r}\n               asr: {hh[:90]!r}")
    for i, first, hh in starts_bad:
        print(f"  [chunk start s{i:02d}] src: {first!r}\n               asr: {hh!r}")
    for k in np.argsort(sim_self)[:3]:
        i, s, _ = wins[k]
        print(f"  lowest self-sim: section {i:2d} at {int(s) // 60}:{int(s) % 60:02d}  self {sim_self[k]:.3f}  ref {sim_ref[k]:.3f}")
    (d / "check.json").write_text(json.dumps(row, indent=1) + "\n")

print("\n| run | min | speed x | peak GB | WER % | 3+ word errors | ref sim | self sim (mean / p5 / min) | level SD dB | wpm | clipped |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for r_ in summary:
    print(f"| {r_['dir']} | {r_['minutes']} | {r_['speed_x']} | {r_['peak_gb']} | {r_['wer_pct']} | {r_['runs3']} | "
          f"{r_['ref_sim']} | {r_['self_sim']} / {r_['self_p5']} / {r_['self_min']} | {r_['level_sd_db']} | {r_['wpm_median']} | {r_['clipped']} |")
