#!/usr/bin/env python3
"""Extract 1 Clement (Lightfoot) from the earlychristianwritings.com page into
plain text: a spoken title line, the greeting, then one paragraph per chapter
headed "Chapter N.". Blocks are separated by blank lines.

Standard library only.

usage: python3 -I tools/extract.py lightfoot.html 1clement.txt
"""
import html, re, sys
src, dst = sys.argv[1], sys.argv[2]
raw = open(src, encoding="latin-1").read()
verses = re.findall(r"<p>\s*1Clem\s+(prologue|\d+):(\d+)\s*<br>(.*?)</p>", raw, re.S | re.I)
chapters = {}
for ch, v, body in verses:
    t = re.sub(r"<[^>]+>", "", body)
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    chapters.setdefault(ch, []).append(t)
out = ["The First Epistle of Clement to the Corinthians. Translated by J. B. Lightfoot."]
for ch, vs in chapters.items():
    head = "" if ch == "prologue" else f"Chapter {ch}."
    out.append((head + "\n" + " ".join(vs)).strip())
open(dst, "w").write("\n\n".join(out) + "\n")
print(len(verses), "verses,", len(chapters), "sections,", sum(len(x.split()) for x in out), "words")
