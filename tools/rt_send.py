#!/usr/bin/env python3
"""Demo text source for rt_tts.py. It releases a text a few words at a time, the
way an LLM streams its answer, and offers it two ways at once:

  websocket  ws://localhost:8765                every new fragment is sent as a message
  HTTP       http://localhost:8766/text?offset=N
             -> {"text": <text released after character N>, "offset": <new N>, "done": bool}

The clock starts when the first client connects. --stop-at S also sends
"<stop>" over the websocket after S seconds, to test interrupting, and then
carries on with the rest of the text. Runs until killed.

usage: .venv-mlx/bin/python tools/rt_send.py [TEXTFILE] [--wps 5] [--stop-at S]
"""
import argparse, asyncio, json, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from websockets.asyncio.server import serve

DEMO = ("Let us fix our eyes on the blood of Christ and understand how precious it is "
        "unto His Father, because being shed for our salvation it won for the whole world "
        "the grace of repentance. Let us review all the generations in turn, and learn how "
        "from generation to generation the Master has given a place for repentance unto them "
        "that desire to turn to Him. Noah preached repentance, and they that obeyed were saved. "
        "Jonah preached destruction unto the men of Nineveh; but they, repenting of their sins, "
        "obtained pardon of God by their supplications and received salvation.")

ap = argparse.ArgumentParser()
ap.add_argument("textfile", nargs="?")
ap.add_argument("--wps", type=float, default=5.0, help="words released per second")
ap.add_argument("--stop-at", type=float, help="send <stop> after this many seconds")
args = ap.parse_args()
words = (open(args.textfile).read() if args.textfile else DEMO).split()
start = None


def begin():
    global start
    if start is None:
        start = time.monotonic()
        print("first client connected: releasing text", flush=True)


def released():
    """The text released so far, and whether that's all of it."""
    if start is None:
        return "", False
    n = min(len(words), int((time.monotonic() - start) * args.wps))
    return "".join(w + " " for w in words[:n]), n == len(words)


class Poll(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/text":
            self.send_error(404)
            return
        begin()
        offset = int(parse_qs(url.query).get("offset", ["0"])[0])
        text, done = released()
        body = json.dumps({"text": text[offset:], "offset": len(text), "done": done}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


async def stream(ws):
    begin()
    sent, stopped = 0, False
    while True:
        text, done = released()
        if len(text) > sent:
            await ws.send(text[sent:])
            sent = len(text)
        if args.stop_at and not stopped and time.monotonic() - start >= args.stop_at:
            await ws.send("<stop>")
            stopped = True
            print(f"sent <stop> at {args.stop_at:.1f} s", flush=True)
        if done:
            break
        await asyncio.sleep(0.05)
    await ws.close()


async def main():
    http = ThreadingHTTPServer(("localhost", 8766), Poll)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    async with serve(stream, "localhost", 8765):
        print("serving ws://localhost:8765 and http://localhost:8766/text", flush=True)
        await asyncio.Future()


asyncio.run(main())
