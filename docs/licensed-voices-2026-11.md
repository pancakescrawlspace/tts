# Voices licensed for online use, and real-time speed: log

Written 2026-11-23. It answers two questions that came up after the cloned-voice
audiobooks:

1. Which voices can be used for audio that's published online, unlike the Jay Dyer and
   Tim Dillon clones, which are for personal listening only?
2. Can those voices also generate speech in real time?

It also records the voice auditions made for a publishable 1 Clement audiobook. The
voice choice and the audiobook itself are still to come.

## 1. What "licensed for online use" requires

Two things must both be true.

**The model's licence must allow publishing its output**, including commercially:

| Model | Licence | Publishing output |
|---|---|---|
| Kokoro 82M | Apache 2.0 | Yes |
| Phonon 31M (`gradium/phonon-31m-en`) | Apache 2.0, covering "the weights, tokenizer and voices", "which allows commercial use" | Yes |
| Phonon 40M (all languages) | CC BY-NC 4.0 | No: non-commercial |
| VoxCPM2 | Apache 2.0, "free for commercial use" | Yes |
| Fish Audio Drama 3 | Fish Audio Community License | Allowed below USD 500k revenue a year; no hosted TTS service; may not imitate a real person without consent |
| Voxtral TTS, Breeze TTS 2, Reverb-TTS | Non-commercial | No |

**The voice must not belong to a real person who hasn't consented.** That rules out the
Jay Dyer and Tim Dillon clones, whatever the model's licence says. These are fine:

- **Preset voices shipped with an Apache 2.0 model:** Kokoro's `am_onyx` and the others,
  and the 102 voices in `gradium/phonon-voices`.
- **Voices VoxCPM2 designs from a text description.** These are invented by the model;
  no recording of a person goes in.
- **The user's own voice**, cloned from their own recording.

So the existing Kokoro `am_onyx` audiobook (`out/1clement_am_onyx.m4b`) already qualifies.

**The text:** J. B. Lightfoot's translation (1891) is in the public domain.

**When publishing:**
- Phonon's model card asks: "Tell listeners when speech is synthetic where that matters
  to them." A line in the description does that.
- It also forbids using Phonon "to impersonate a real person… or to clone a voice without
  the speaker's consent".
- Some audiobook stores don't accept synthetic narration, so the destination's rules
  decide where this can go.

### The user's actual use: a non-monetised YouTube channel

The user later explained that they won't publish commercially. At most, a video goes on
their YouTube channel, which isn't monetised, and most videos there are unlisted. That
changes the picture as follows:

- **Non-commercial licences become usable.** That covers Voxtral (CC BY-NC 4.0) and
  Drama 3 (its licence allows non-commercial use).
  - Voxtral's licence requires attribution, e.g. "Voxtral TTS by Mistral AI, CC BY-NC 4.0"
    in the video description.
  - YouTube may place ads on videos from non-monetised channels too, but the uploader
    doesn't earn from them, so this is generally treated as non-commercial use.
  - The 40M Phonon models (CC BY-NC) would qualify on the same basis.
- **Cloned real voices still don't qualify.** For the Jay Dyer and Tim Dillon clones, the
  issue is consent, not money. An unlisted video can still be watched by anyone with the
  link. Every model card consulted rules out imitating a real person without consent,
  regardless of licence. Those audiobooks stay private.
- **Disclosure:** YouTube asks creators to label realistic synthetic content. For an
  invented narrator that's probably not required, but "AI narration" in the description
  is good practice anyway.

## 2. Auditions

`out/licensed/auditions/` holds 19 clips, each reading the same two sentences (the
opening of 1 Clement chapter 20, the text of the pilot's reference clip):

- **13 Phonon voices:** `phonon_default` and the 12 English male catalogue voices
  (`phonon_us_*`, `phonon_uk_*`), copied from the pilot's voice comparison
  (`tools/phonon_voices.py`, see [pilot-2026-11.md](pilot-2026-11.md), step 3). The
  catalogue also has 13 English female voices and 12 character voices, not auditioned.
- **6 VoxCPM2 designed voices:** three descriptions, two takes each (seeds 0 and 1),
  48 kHz:

  | Files | Description given to the model |
  |---|---|
  | `voxcpm2_warm_american_take1/2` | "A calm, warm, middle-aged American man with a deep, relaxed voice, reading slowly like an audiobook narrator" |
  | `voxcpm2_british_elder_take1/2` | "An older British man with a gentle, resonant voice, measured and reverent, like a narrator of classic literature" |
  | `voxcpm2_soft_low_take1/2` | "A mature American man with a soft, low, soothing voice, unhurried and steady" |

**Takes.** Voice design involves randomness, so every attempt (take) invents a different
voice that fits the description. The model card says so too: results "may vary between
runs; generating 1–3 times is recommended". The two takes of each description are
different voices:

| Description | Take 1 vs take 2 (ECAPA similarity) |
|---|---|
| warm_american | 0.575 |
| british_elder | 0.549 |
| soft_low | 0.571 |

The same voice typically scores above 0.8.

**Locking a designed voice for a whole book.** The chosen take becomes the reference clip,
with its transcript, for VoxCPM2's prompt mode, just as with the cloned voices. Designing
anew for every chunk would change the narrator from chunk to chunk.

**Every take says the text exactly** (checked with Parakeet). That matters because the
reference transcript has to match the audio.

Made with:

```python
from mlx_audio.tts.utils import load
import mlx.core as mx
tts = load("mlx-community/VoxCPM2-bf16")
mx.random.seed(0)                                   # seed 1 for take 2
audio = [r.audio for r in tts.generate(text=TEXT, instruct=DESCRIPTION)]
```

## 3. Real-time speed

Both models are equally licensed for live use, so it's a question of speed. Measured on
the M3 Max with mlx-audio 0.6.7, after one warm-up call (the first call is always slower).
The test text was the first sentences of 1 Clement chapter 7 ("Let us fix our eyes on the
blood of Christ…"). Times run from the call to the first audio returned.

| Engine, voice | Mode | Text | First audio after | Audio | Total time | Speed |
|---|---|---|---|---|---|---|
| Phonon 31M, `us_russell` | `stream=True`, 0.5 s pieces | 1 sentence | 200 ms | 4.9 s | 0.5 s | 10.7x |
| Phonon 31M, `us_russell` | `stream=True`, 0.5 s pieces | 3 sentences | 188 ms | 15.9 s | 1.1 s | 14.5x |
| VoxCPM2 bf16, `warm_american_take1` | prompt mode, per sentence | 1 sentence | 3,001 ms | 6.6 s | 3.0 s | 2.2x |

- **Phonon streams:** it hands over audio while still generating. It starts speaking in
  about 0.2 s, quick enough for conversation, e.g. a voice assistant. Gradium quotes 28 ms
  to first audio on a CPU with its own runtime (`ptts`), which wasn't tested here.
- **VoxCPM2 doesn't stream in mlx-audio.** Its `generate()` collects all audio features,
  decodes them at the end and yields once (`mlx_audio/tts/models/voxcpm2/voxcpm2.py`). The
  first sound comes only when the whole sentence is done. Fed sentence by sentence, it can
  still read a text aloud live: about 3 s of delay before the first sentence, then it
  stays ahead, because it generates twice as fast as playback. For conversation, 3 s
  before every reply is too slow.
  - Ways to bring that down (not tested): the 8-bit or 4-bit builds, a short first
    sentence, or the official PyTorch VoxCPM, which streams, though its fast path
    targets NVIDIA GPUs.
- **For use from other programs**, mlx-audio includes a local server (`mlx_audio.server`)
  with an OpenAI-compatible `/v1/audio/speech` endpoint.

**For choosing a voice:** if one voice should serve both a published audiobook and
real-time speech, that favours Phonon.

How such a model is wired into a live pipeline (text in over HTTP or a websocket, audio
out to the speakers) is in [realtime-pipeline-2026-11.md](realtime-pipeline-2026-11.md).

## Status

Exploration only so far. Next: choose a voice from the auditions and render the 1 Clement
audiobook in it, with its own log.
