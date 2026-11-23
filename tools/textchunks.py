"""Cut text into chunks for TTS engines that don't split long text themselves.

Used by pilot_render.py (VoxCPM2) and pilot_check.py (to find where chunks
start). A chunk holds whole sentences up to LIMIT characters. A longer
sentence is cut at ; or :, then at commas, then at spaces, which leaves the
next chunk starting mid-sentence, usually in lowercase.
"""
import re

LIMIT = 300
SEPARATORS = (r"(?<=[.!?])\s+", r"(?<=[;:])\s+", r"(?<=,)\s+", r"\s+")


def pieces(s, seps=SEPARATORS):
    """Split s at the coarsest boundary that gets every piece under LIMIT."""
    if len(s) <= LIMIT or not seps:
        return [s]
    return [q for p in re.split(seps[0], s) for q in pieces(p, seps[1:])]


def chunks(s):
    """Pack the pieces of s into chunks of at most LIMIT characters."""
    out, cur = [], ""
    for p in pieces(s):
        if cur and len(cur) + 1 + len(p) > LIMIT:
            out.append(cur)
            cur = p
        else:
            cur = f"{cur} {p}".strip()
    return out + [cur] if cur else out
