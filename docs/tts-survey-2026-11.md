# Free TTS models: survey, November 2026

A new search for free, locally runnable text-to-speech models, done on 2026-11-23.
The repo was set up on 2026-09-10 with Piper, Kokoro and Coqui XTTS-v2. The candidates
that were compared back then weren't recorded, so this survey looks at everything and
marks what was released after 2026-09-10.

**Goal:** audiobooks (long-form English narration, Dutch as a second wish), rendered
locally on this machine: Apple M3 Max, 48 GB unified memory.

**Outcome:** three models were shortlisted for a pilot: Phonon 31M, Fish Audio Drama 3
and VoxCPM2. See [pilot-2026-11.md](pilot-2026-11.md).

## Method

- Web searches for 2026 open-weights TTS releases, leaderboards, Apple Silicon support
  and Dutch support.
- Then each candidate's primary source was read: the Hugging Face model card or GitHub
  README, the Artificial Analysis leaderboard, and the mlx-audio and mlx-speech READMEs.
  Third-party roundups were used only to find names.
- Licence, size and speed figures below come from the model cards. They are the
  publishers' own claims, and several cards contradict themselves (noted where it
  matters).

## Leaderboard snapshot

Artificial Analysis Speech Arena, open-weights tab, read 2026-11-23. Scores come from
blind A/B votes on short clips, so they say nothing about long-form stability. The page
shows no update date. The Hugging Face TTS Arena V2 Space wouldn't render its table.

| # | Model | Creator | Elo | Released |
|---|---|---|---|---|
| 1 | Fish Audio Drama 3 | Fish Audio | 1277 | Oct 2026 |
| 2 | Fish Audio Drama 3 Preview | Fish Audio | 1237 | Oct 2026 |
| 2 | Breeze TTS 2 | BreezeBlue | 1228 | Aug 2026 |
| 4 | Ming-3.0-tts | Ant Group | 1179 | Oct 2026 |
| 5 | Phonon 31M (English) | Gradium | 1108 | Oct 2026 |
| 6 | Fish Audio S2 Pro | Fish Audio | 1101 | Mar 2026 |
| 7 | Step Audio EditX | StepFun | 1100 | Feb 2026 |
| 8 | Voxtral TTS | Mistral | 1094 | Mar 2026 |
| 9 | Magpie-Multilingual 357M | NVIDIA | 1064 | Feb 2026 |
| **10** | **Kokoro 82M v1.0** | hexgrad | **1060** | Jan 2025 |
| 11 | Maya1 | Maya Research | 1047 | Jun 2025 |
| 12 | OpenAudio S1 Mini | Fish Audio | 1042 | Jun 2025 |
| 13 | Higgs Audio V3 TTS | Boson AI | 1035 | Jun 2026 |
| 14 | Chatterbox | Resemble AI | 1019 | May 2025 |
| 15 | Zonos-v0.1 | Zyphra | 1000 (anchor) | Feb 2025 |
| 16 | OpenVoice v2 | MyShell | 954 | Apr 2024 |
| 16 | VibeVoice 1.5B | Microsoft | 954 | Aug 2025 |
| **18** | **XTTS v2** | Coqui | **914** | Nov 2023 |
| 19 | StyleTTS 2 | yl4579 | 887 | Jun 2023 |
| 20 | MetaVoice v1 | MetaVoice | 845 | Feb 2024 |

Ranks follow the page, which ties models whose confidence intervals overlap.

## Candidates

### Released after 2026-09-10

| Model | Size | Weights licence | Languages | Dutch | Cloning | Apple Silicon |
|---|---|---|---|---|---|---|
| **Fish Audio Drama 3** | 35B MoE, 3B active | Fish Audio Community License: free for non-commercial use, and commercial use under USD 500k/yr revenue. No hosted services. | "83" (not listed) | Not confirmed | Yes, plus up to 16 speakers | 4-bit build in mlx-audio |
| Ming-3.0-tts | 0.5B dense / 7.9B MoE | MIT | zh en de es fr ko ja | No | Yes, plus preset voices | Officially CUDA (H800). Community MLX builds exist. |
| **Phonon 31M** | 31M, ~65 MB | Apache 2.0 (the 40M multilingual model is CC BY-NC) | English | No | Yes, from a short sample | CPU, Metal, Core ML. In mlx-audio. |
| Reverb-TTS | ~300M | CC BY-NC 4.0 (fine-tune of OmniVoice) | en de fr es it pl pt | No | Yes, plus 16 presets | MLX via ExecuTorch, 12-21x realtime on M4 Pro (claimed) |

Drama 3's card says it is "built for multi-character scenes and long-form content" and
that "long text is chunked automatically". It's the only candidate that says anything
about long-form use.

### Released before 2026-09-10 (mostly in 2026)

| Model | Size | Weights licence | Dutch | Cloning | Apple Silicon | Note |
|---|---|---|---|---|---|---|
| Breeze TTS 2 | 3B | Non-commercial | No (en, zh) | Yes | No: Linux + CUDA only | #2 on the board |
| Fish Audio S2 Pro | 4.4B | Fish research licence (non-commercial) | ? | Yes | mlx-speech | Superseded by Drama 3 |
| Step Audio EditX | 3B | Apache 2.0 | No | Yes | mlx-speech | Clips under 30 s |
| Voxtral TTS (Mistral) | 4B | CC BY-NC 4.0 | **Yes** (9 langs) | Short reference | mlx-audio | 20 preset voices |
| **VoxCPM2** (OpenBMB) | 2B | Apache 2.0 | **Yes** (30 langs) | Yes, plus voice design | Community MLX builds, in mlx-audio | Card: "occasional instability with very long inputs" |
| MOSS-TTS v1.5 | 8B | Apache 2.0 (HF tag) | **Yes** (31 langs) | Yes | mlx-audio | |
| MOSS-TTS-Nano | 100M | Unclear (tag says Apache, card says not yet licensed) | No | Yes | CPU | |
| KugelAudio 0 | 7B | MIT | **Yes** (23 European) | No | mlx-audio, ~17 GB | Only 4 presets: 2 German, 2 English |
| Chatterbox Multilingual V3 | 0.5B | Code MIT, weights not stated | **Yes** (23 langs) | Yes | mlx-audio | Project retired Aug 2026 |
| Qwen3-TTS (Alibaba) | 0.6B / 1.7B | Apache 2.0 | No (10 langs) | Yes, plus voice design | mlx-audio | |
| Pocket TTS (Kyutai) | 100M | CC BY 4.0, gated | GitHub says yes, HF card says no | Yes, plus 26 presets | CPU, ~6x realtime on M4 Air | |
| Hume TADA | 1B / 3B | Llama 3.2 Community License | No | Yes | CUDA in examples | Gated behind Llama access |
| OmniVoice (k2-fsa) | 0.6B | CC BY-NC | "600+" (not listed) | Yes, plus voice design | Install path for Mac shown | |
| Magpie-Multilingual 357M | 357M | NVIDIA Open Model License | No | No (5 fixed speakers) | ? | 20 s cap per call |
| Higgs Audio V3 | 4B | Non-commercial | ? (100+) | Yes | mlx-audio | Ranks below Kokoro |
| VibeVoice 7B / 1.5B | | MIT, but Microsoft withdrew the weights | | | mlx-speech (Large) | 90 min multi-speaker |

### Dutch-only

Parkiet (github.com/pevers/parkiet): open-weights Dutch TTS, code MIT, weights RAIL-M.
Not checked further.

## Running these on a Mac

**mlx-audio** (github.com/Blaizzy/mlx-audio, now Neywa-Labs/mlx-audio, MIT) runs about 30
TTS models natively on Apple Silicon from a single `pip install mlx-audio`. Its list
includes Kokoro, Phonon, Drama 3, Voxtral, VoxCPM2, Qwen3-TTS, Chatterbox, Reverb,
OmniVoice, MOSS-TTS, KugelAudio and Ming-3.0. It also does speech-to-text. One venv for
all of them is simpler than one venv per engine, which is what the repo does now.

**mlx-speech** (github.com/appautomaton/mlx-speech) covers a different set: Fish S2 Pro,
VibeVoice Large, Step-Audio-EditX, MOSS-TTSD, LongCat AudioDiT, Breeze TTS 2 (convert it
yourself). It needs Python 3.13+.

## Shortlist for audiobooks

What matters for an audiobook, in order:

1. **Doesn't skip, repeat or invent words** over hours of text.
2. **Same voice from the first chunk to the last.** Voice design from a text prompt can
   give a different voice each time, so a fixed reference clip or preset voice is needed.
3. **Natural narration prosody.** This is what the arena measures, on short clips.
4. **Speed.** 1 Clement is 66 minutes of audio. At 0.3x realtime that's a 3.5-hour render.
5. Licence. For personal use, non-commercial is fine (the repo already uses XTTS on
   those terms).

Chosen for the pilot:

| Model | Why |
|---|---|
| Phonon 31M | Smallest possible step from Kokoro: tiny, Apache 2.0, ranks above Kokoro |
| Fish Audio Drama 3 | Highest-ranked open model by a wide margin. The only one that claims long-form support. |
| VoxCPM2 | The best-documented Dutch option with a permissive licence |

Not chosen:
- **Breeze TTS 2:** no Mac support.
- **Ming-3.0:** no Dutch, and only community Mac builds.
- **Voxtral:** non-commercial. It's the alternative if VoxCPM2's Dutch disappoints.
- **Fish S2 Pro:** superseded by Drama 3.
- **Step Audio EditX:** limited to clips under 30 s.
- **KugelAudio:** no Dutch voice to speak with.

## Unverified or conflicting

- Drama 3: the HF tag says "fish-audio-research-license", but the card and LICENSE file
  say "Fish Audio Community License". Its language list isn't published.
- Reverb-TTS: the card gives two parameter counts (297M and 319M) and two WER figures.
- KugelAudio: 7B on the card, 9B in the HF metadata.
- Pocket TTS: Dutch is listed on GitHub but not on the HF card.
- Chatterbox V3: the weights licence and the release date aren't on the GitHub page.
- Breeze TTS 2: one roundup calls its licence "NVIDIA Open Model License". The model card
  says "BreezeBlue Research and Non-Commercial License".

## Sources

- https://artificialanalysis.ai/text-to-speech/leaderboard/open-weights
- https://huggingface.co/fishaudio/drama-3
- https://huggingface.co/blog/phonon-tts
- https://huggingface.co/openbmb/VoxCPM2
- https://huggingface.co/inclusionAI/Ming-3.0-tts-0.5B, https://huggingface.co/inclusionAI/Ming-3.0-tts-tiny
- https://huggingface.co/software-mansion/Reverb-TTS
- https://huggingface.co/BreezeBlue/Breeze-TTS-2
- https://huggingface.co/mistralai/Voxtral-4B-TTS-2603
- https://huggingface.co/OpenMOSS-Team/MOSS-TTS-v1.5, https://huggingface.co/OpenMOSS-Team/MOSS-TTS-Nano-100M
- https://huggingface.co/kugelaudio/kugelaudio-0-open
- https://huggingface.co/k2-fsa/OmniVoice
- https://github.com/resemble-ai/chatterbox
- https://github.com/kyutai-labs/pocket-tts
- https://github.com/HumeAI/tada
- https://github.com/Blaizzy/mlx-audio
- https://github.com/appautomaton/mlx-speech
- https://pinggy.io/blog/best_open_source_self_hosted_text_to_speech_models/ (roundup, updated 2026-08-26)
