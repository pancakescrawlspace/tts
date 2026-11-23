# Real-time text-to-speech pipeline: log

Written 2026-11-23. The question: given a model fast enough for real time, how would a
pipeline work that (1) gets text by polling an HTTP endpoint or listening on a websocket,
(2) turns it into audio as it arrives, and (3) plays the audio? First the design, then a
working demo.

## Design

Three stages, each running independently, connected by queues:

```
 text source ──► [ text queue ] ──► synthesis ──► [ audio queue ] ──► playback ──► speakers
 (HTTP poll /     (sentences)        (model,        (audio chunks)     (output
  websocket)                          loaded once)                      stream)
```

Each stage waits on something different: the network, the model, the sound card.
Decoupled by queues, they overlap. While sentence 1 plays, sentence 2 is being
synthesised and sentence 3 is arriving.

**1. Input.**
- **Websocket:** the sender pushes text the moment it exists, so nothing is added to the
  delay. That suits e.g. an LLM streaming its reply word by word.
- **HTTP polling:** adds up to one poll interval of delay. It also needs a way to fetch
  only what's new (an ID, offset or timestamp), so nothing is spoken twice.
- **Either way, text is cut into sentences before synthesis.** TTS models sound right with
  whole sentences, so fragments are buffered until a sentence ends. A short timeout
  flushes a fragment that never gets a full stop.

**2. Synthesis.**
- **The model is loaded once and kept warm.** Loading takes seconds, and the first call is
  slow.
- **All model calls happen on one worker thread.**
- **What "real time" means, from the measurements in
  [licensed-voices-2026-11.md](licensed-voices-2026-11.md), step 3:**
  - Phonon 31M starts producing audio after about 0.2 s and generates 11–15x faster than
    playback, so it keeps up easily.
  - VoxCPM2 needs about 3 s per sentence (mlx-audio doesn't stream it) but generates 2x
    faster than playback. After the first sentence it stays ahead.
  - Voxtral TTS (measured later, [voxtral-2026-11.md](voxtral-2026-11.md)) streams. It
    starts after about 0.4 s and generates 2x faster than playback. It only has preset
    voices and a non-commercial licence.

**3. Playback.**
- **One audio output stream** at the model's sample rate (24 kHz for Phonon), written to
  chunk by chunk. A blocking write waits until the sound card can take more, so chunks join
  without gaps or overlap.
- **`sounddevice`**, already in `.venv-mlx` (installed with mlx-audio), provides it.

**What a real version needs on top:**
- **Flush on silence:** speak a trailing fragment if no sentence end arrives within about 1 s.
- **Interruption:** a "stop" message that empties both queues, so new text doesn't wait
  behind old audio.
- **Backpressure:** if text arrives faster than it can be spoken, the queues grow. The
  choice is to wait, skip ahead, or interrupt.
- **Optional decoupling:** instead of loading the model in-process, the synthesis stage can
  call mlx-audio's local server (`mlx_audio.server`, an OpenAI-compatible
  `/v1/audio/speech` endpoint). That's slightly slower, but any program can then use the
  TTS.

### Other input schemes

Polling and websockets aren't the only options. Only the input stage changes; it calls the
same "here's some text" function whatever the source (`handle()` in the demo).

| Scheme | Direction | Delay | Typical source | Notes |
|---|---|---|---|---|
| Server-Sent Events (SSE) | Server pushes over one long HTTP response | None | LLM APIs: OpenAI's and Anthropic's streaming responses are SSE | Simpler than websockets, one-way only. The natural choice for text from an LLM |
| Streamed HTTP response (chunked, NDJSON) | Server pushes | None | APIs that return JSON lines | Basically SSE without the event format |
| HTTP long polling | Client asks; the server holds the request until there's news | Small | Older chat systems | Polling without the interval delay |
| Webhook / HTTP POST | The sender pushes to the pipeline's own server | None | Scripts, `curl`, Apple Shortcuts, home automation, other services | The reverse of polling, and the easiest to integrate with |
| Message broker (MQTT, Redis pub/sub, NATS, RabbitMQ, Kafka) | Publish / subscribe | None | IoT and home automation (MQTT, e.g. Home Assistant), several producers, durable queues | Decouples senders from the speaker; messages can wait while it's offline |
| gRPC streaming | One way or both | None | Service-to-service | Typed and efficient, more set-up |
| Local pipes and sockets (stdin, named pipe, Unix or TCP socket) | Push | None | Programs on the same machine: `echo "hello" \| speak`, `tail -f log \| speak` | The simplest; no network stack |
| Watching a file or folder | The pipeline watches | Small | A log file being written, a drop folder | |
| OS hooks (clipboard, macOS Shortcuts or Services, a keyboard shortcut) | User-triggered | None | "Speak the selected text" | Desktop use |
| WebRTC data channel | Peer to peer | None | Browser apps | Usually paired with audio going back to the browser |
| OSC (Open Sound Control) | Push, over UDP | None | Music and audio software | |

Rules of thumb:
- Text from an LLM API: SSE.
- Home automation: MQTT.
- Other programs on the same Mac: stdin or a local socket.
- Anything that should be able to call it: an HTTP POST endpoint.
- Polling: only when the source offers nothing else.

### Starting point for the demo

The sketch the demo starts from:

```python
import asyncio, queue, re, threading
import numpy as np, sounddevice as sd, websockets
from mlx_audio.tts.utils import load

text_q, audio_q = queue.Queue(), queue.Queue(maxsize=16)
VOICE = "hf://gradium/phonon-voices/voices/_6Aslh2DxfmnRLmP.safetensors"   # us_russell

def synthesise():                                  # one thread owns the model
    model = load("gradium/phonon-31m-en")
    while True:
        sentence = text_q.get()
        for r in model.generate(text=sentence, voice=VOICE, stream=True, streaming_interval=0.3):
            audio_q.put(np.asarray(r.audio, dtype=np.float32).reshape(-1, 1))

def play():
    with sd.OutputStream(samplerate=24000, channels=1, dtype="float32") as out:
        while True:
            out.write(audio_q.get())               # blocks until the sound card takes it

async def listen(url):
    buf = ""
    async with websockets.connect(url) as ws:
        async for msg in ws:                       # fragments arrive; speak whole sentences
            *done, buf = re.split(r"(?<=[.!?])\s+", buf + msg)
            for s in done:
                text_q.put(s)

threading.Thread(target=synthesise, daemon=True).start()
threading.Thread(target=play, daemon=True).start()
asyncio.run(listen("ws://localhost:8765"))
```

## Demo

Built and run on 2026-11-23, after the other jobs, with the GPU to itself.

### Files

| File | What |
|---|---|
| `tools/rt_tts.py` | The pipeline: websocket (`--ws URL`) or HTTP polling (`--poll URL`) in; Phonon 31M (voice `us_russell`) streaming; playback through `sounddevice`. It also flushes an unfinished sentence after 1 s of quiet, handles `<stop>` interruption (an "epoch" counter makes the synthesis and playback threads drop stale audio), and logs timing per sentence. `--no-play` simulates playback at real speed; `--save` writes what was played. |
| `tools/rt_send.py` | A demo text source. It releases a 99-word passage of 1 Clement (from chapter 7) at a set number of words per second, like an LLM streaming, over both `ws://localhost:8765` and `http://localhost:8766/text?offset=N`. `--stop-at S` sends `<stop>`. |
| `tools/rt_demo.sh` | Starts both with one command: `sh tools/rt_demo.sh [ws\|poll] [rt_tts options]`. Use `SEND="..."` to pass options to the sender. |

The websocket code uses the `websockets` package (17.4), added to `.venv-mlx` and
`requirements-mlx.txt`. The sentence splitter in `rt_tts.py` also cuts at semicolons, for
shorter units and lower latency.

### Results (silent runs, `--no-play`)

Two times were measured from the moment a sentence's text was complete: when the model
had its first audio ready, and when that audio reached the (simulated) speakers.

| Run | Sentences | Model ready (median / max) | Playing (median / max) | Notes |
|---|---|---|---|---|
| Websocket, 5 words/s | 5 | 174 / 216 ms | 10.0 / 12.1 s | Text arrives faster than speech (300 against ~200 words/min), so later sentences queue behind playback |
| HTTP polling (0.5 s), 5 words/s | 5 | 197 / 226 ms | 9.9 / 12.2 s | The same. Polling's own delay (up to 0.5 s) comes before "text complete" and isn't in these numbers |
| Websocket, 2.5 words/s (speaking pace) | 5 | 209 / 217 ms | 2.4 / 5.8 s | Sentences 1 and 2 start playing **0.22 s** after their text was complete. Later ones still wait when short sentences arrive during a long one |
| Websocket, `<stop>` at 10 s | 5 | 173 / 215 ms | 2.8 / 4.9 s | At 11.1 s the rest of sentence 1 was dropped (20.2 s of audio saved, against 30.4 s without the stop). The next text was spoken mid-sentence ("the Master has given…"), because the unfinished fragment was discarded with the queue |

- **Synthesis is never the bottleneck.** Phonon has the first audio ready 150–230 ms after
  a sentence's text is complete, in every run.
- **The delay you'd hear comes from playback queueing** whenever text arrives faster than it
  can be spoken. That's the "backpressure" choice from the design: this demo waits; a chat
  assistant might rather interrupt or skip ahead.
- **Word-perfect:** the saved audio of the first run, transcribed with Parakeet, matches the
  99 words sent exactly.

### With sound

The same commands without `--no-play` play through the default output device, here a JBL
Go 4 Bluetooth speaker. That adds the device's own latency on top, which these numbers
don't include; Bluetooth typically adds 0.1–0.3 s.

```bash
sh tools/rt_demo.sh                          # websocket, 5 words/s
SEND="--wps 2.5" sh tools/rt_demo.sh         # at speaking pace
SEND="--stop-at 10" sh tools/rt_demo.sh      # with an interruption
sh tools/rt_demo.sh poll                     # HTTP polling instead
```
