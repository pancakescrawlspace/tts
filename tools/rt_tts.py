#!/usr/bin/env python3
"""Real-time TTS pipeline: text in over a websocket or HTTP polling, speech out.

Three stages, connected by queues (see docs/realtime-pipeline-2026-11.md):

  input      websocket messages or HTTP polls, cut into whole sentences
  synthesis  Phonon 31M, streaming; one thread owns the model, loaded once and warmed up
  playback   one sounddevice output stream at 24 kHz, written to chunk by chunk

Text may arrive in fragments and is spoken per sentence. A fragment without a
sentence end is spoken after --flush seconds without new text. The message
"<stop>" interrupts: queued text and audio are dropped. When the source ends,
what's left is spoken and the program exits.

For each sentence it logs when its text was complete, when the model had its
first audio ready, and when that audio went to the speakers, with a summary at
the end. --no-play skips the sound card (playback is then simulated at real
speed); --save writes everything that was played to a WAV file.

usage: .venv-mlx/bin/python tools/rt_tts.py (--ws URL | --poll URL) [--interval 0.5]
           [--flush 1.0] [--voice us_russell] [--save OUT.wav] [--no-play]
"""
import argparse, asyncio, json, queue, re, threading, time, urllib.request, warnings

warnings.filterwarnings("ignore")
import numpy as np

ap = argparse.ArgumentParser()
source = ap.add_mutually_exclusive_group(required=True)
source.add_argument("--ws", help="websocket URL to listen to")
source.add_argument("--poll", help="HTTP URL to poll (?offset=N is appended)")
ap.add_argument("--interval", type=float, default=0.5, help="seconds between polls")
ap.add_argument("--flush", type=float, default=1.0, help="speak an unfinished sentence after this many quiet seconds")
ap.add_argument("--voice", default="us_russell", help="Phonon voice: a name below, 'default', or an hf:// path")
ap.add_argument("--save")
ap.add_argument("--no-play", action="store_true")
args = ap.parse_args()

VOICES = {"us_russell": "_6Aslh2DxfmnRLmP", "us_easton": "LMDIYE0Oa377Qh6Z", "uk_hugh": "YyKcxPG7iIgS3jsK",
          "uk_spencer": "JOW0vchyswkQUMDS"}
VOICE = (f"hf://gradium/phonon-voices/voices/{VOICES[args.voice]}.safetensors"
         if args.voice in VOICES else args.voice)
SR = 24000
T0 = time.perf_counter()
text_q, audio_q = queue.Queue(), queue.Queue(maxsize=64)
epoch = [0]                       # bumped by <stop>; older text and audio are then dropped
ready = threading.Event()
stats = {}                        # sentence id -> {"text": t, "ready": t, "play": t}


def now():
    return time.perf_counter() - T0


def log(msg):
    print(f"[{now():6.2f} s] {msg}", flush=True)


class Sentences:
    """Collects fragments and hands whole sentences to the synthesis queue."""

    def __init__(self):
        self.buf, self.n, self.last = "", 0, time.perf_counter()

    def feed(self, text):
        self.buf += text
        self.last = time.perf_counter()
        *done, self.buf = re.split(r"(?<=[.!?;])\s+", self.buf)
        for s in done:
            self.emit(s)

    def emit(self, s):
        if s.strip():
            self.n += 1
            stats[self.n] = {"text": now()}
            text_q.put((self.n, epoch[0], s.strip()))
            log(f"text  #{self.n}: {s.strip()[:70]!r}")

    def flush_if_quiet(self):
        if self.buf.strip() and time.perf_counter() - self.last > args.flush:
            self.flush("(flushed after a pause)")

    def flush(self, why=""):
        s, self.buf = self.buf, ""
        if s.strip() and why:
            log(why)
        self.emit(s)


sentences = Sentences()


def handle(msg):
    if msg.strip() == "<stop>":
        epoch[0] += 1
        sentences.buf = ""
        for q in (text_q, audio_q):
            while not q.empty():
                q.get_nowait()
        log("<stop>: queued text and audio dropped")
    else:
        sentences.feed(msg)


def synthesise():
    from mlx_audio.tts.utils import load
    model = load("gradium/phonon-31m-en")
    for _ in model.generate(text="Ready.", voice=VOICE):   # warm-up: the first call is slow
        pass
    log("model loaded and warm")
    ready.set()
    while True:
        item = text_q.get()
        if item is None:
            audio_q.put(None)
            return
        sid, ep, text = item
        if ep != epoch[0]:
            continue
        for r in model.generate(text=text, voice=VOICE, stream=True, streaming_interval=0.3):
            if ep != epoch[0]:
                break
            stats[sid].setdefault("ready", now())
            audio_q.put((sid, ep, np.asarray(r.audio, dtype=np.float32).reshape(-1, 1)))


def play():
    out = None
    if not args.no_play:
        import sounddevice as sd
        out = sd.OutputStream(samplerate=SR, channels=1, dtype="float32")
        out.start()
    played = []
    while True:
        item = audio_q.get()
        if item is None:
            break
        sid, ep, chunk = item
        if ep != epoch[0]:
            continue
        if "play" not in stats[sid]:
            stats[sid]["play"] = now()
            s = stats[sid]
            log(f"audio #{sid}: model ready +{(s['ready'] - s['text']) * 1000:.0f} ms, "
                f"playing +{(s['play'] - s['text']) * 1000:.0f} ms after its text was complete")
        if out:
            out.write(chunk)
        else:
            time.sleep(len(chunk) / SR)
        played.append(chunk)
    if out:
        out.stop()                # returns once the last buffers have been played
        out.close()
    if args.save and played:
        import soundfile as sf
        sf.write(args.save, np.concatenate(played), SR)
        log(f"saved {sum(len(c) for c in played) / SR:.1f} s of audio to {args.save}")


async def listen_ws():
    from websockets.asyncio.client import connect
    from websockets.exceptions import ConnectionClosed
    async with connect(args.ws) as ws:
        log(f"connected to {args.ws}")
        while True:
            try:
                handle(await asyncio.wait_for(ws.recv(), timeout=0.2))
            except asyncio.TimeoutError:
                sentences.flush_if_quiet()
            except ConnectionClosed:
                break


def listen_poll():
    offset = 0
    log(f"polling {args.poll} every {args.interval} s")
    while True:
        with urllib.request.urlopen(f"{args.poll}?offset={offset}") as r:
            d = json.load(r)
        if d["text"]:
            handle(d["text"])
        offset = d["offset"]
        sentences.flush_if_quiet()
        if d.get("done"):
            break
        time.sleep(args.interval)


synth = threading.Thread(target=synthesise, daemon=True)
player = threading.Thread(target=play)
synth.start()
player.start()
ready.wait()
if args.ws:
    asyncio.run(listen_ws())
else:
    listen_poll()
sentences.flush("(source ended)")
text_q.put(None)
player.join()

done = [s for s in stats.values() if "play" in s]
if done:
    r = sorted(s["ready"] - s["text"] for s in done)
    p = sorted(s["play"] - s["text"] for s in done)
    log(f"{len(done)} sentences spoken, {len(stats) - len(done)} dropped. Text complete -> model ready: "
        f"median {r[len(r) // 2] * 1000:.0f} ms, max {r[-1] * 1000:.0f} ms. "
        f"Text complete -> playing: median {p[len(p) // 2] * 1000:.0f} ms, max {p[-1] * 1000:.0f} ms")
