#!/bin/sh
# Real-time TTS demo: rt_send.py streams a text a few words at a time, rt_tts.py speaks it.
#
# usage: sh tools/rt_demo.sh [ws|poll] [rt_tts.py options, e.g. --save out.wav --no-play]
#        SEND="--stop-at 6" sh tools/rt_demo.sh     # also test interrupting
cd "$(dirname "$0")/.." || exit 1
mode=${1:-ws}
[ $# -gt 0 ] && shift
.venv-mlx/bin/python tools/rt_send.py $SEND > /dev/null 2>&1 &
sender=$!
trap 'kill $sender 2>/dev/null' EXIT
sleep 1
if [ "$mode" = poll ]; then
  .venv-mlx/bin/python tools/rt_tts.py --poll http://localhost:8766/text "$@"
else
  .venv-mlx/bin/python tools/rt_tts.py --ws ws://localhost:8765 "$@"
fi
