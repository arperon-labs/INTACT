"""Does paper.md actually agree with the built PDF?

Run alongside check_numbers.py: that one guards the NUMBERS in paper.md, this
one guards prose agreement between the two hand-maintained masters. Four
divergences reached the built PDF before this existed, including a claim the
paper.md correction had already retracted.

The two masters are maintained by hand, so this compares them by CONTENT rather
than by string: every sentence of paper.md is reduced to a distinctive shingle
of alphabetic word-stems and looked up in the normalised PDF text. A sentence
whose shingle is missing is a candidate divergence -- prose that exists in one
master and not the other.

False positives are expected where notation renders differently (math, symbols,
code spans); those are filtered by requiring a run of ordinary words.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = Path(__file__).resolve().parent

# ---------------------------------------------------------------- PDF side
pdf = subprocess.run(["pdftotext", str(P / "paper.pdf"), "-"],
                     capture_output=True).stdout.decode("utf-8", "replace")
pdf = pdf.replace("-\n", "")                      # de-hyphenate line breaks


def norm(t):
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())


def sig(t):
    """Reduce text to its sequence of significant word-stems. BOTH sides must
    go through this - filtering the query but not the haystack was the bug in
    the first version of this check, and it reported 91 false divergences."""
    return [w for w in norm(t).split() if w.isalpha() and len(w) > 2]


PDFN = " ".join(sig(pdf))

# ---------------------------------------------------------------- md side
md = (P / "paper.md").read_text(encoding="utf-8")
md = re.sub(r"```.*?```", " ", md, flags=re.S)     # code fences
md = re.sub(r"^\|.*$", " ", md, flags=re.M)       # tables
md = re.sub(r"^#+.*$", " ", md, flags=re.M)       # headings
md = re.sub(r"\*\(.*?\)\*", " ", md, flags=re.S)  # figure-caption asides
md = re.sub(r"`[^`]*`", " X ", md)                # code spans -> placeholder
md = re.sub(r"\[[^\]]*\]", " ", md)               # citation keys
md = md.replace("*", " ").replace("—", " ").replace("–", " ")

sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", md) if s.strip()]

missing = []
for s in sentences:
    words = sig(s)
    if len(words) < 10:                            # too short to fingerprint
        continue
    # try several shingles; the sentence counts as PRESENT if any 6-gram hits
    hit = False
    for i in range(0, max(1, len(words) - 6), 3):
        if " ".join(words[i:i + 6]) in PDFN:
            hit = True
            break
    if not hit:
        missing.append(s)

print(f"paper.md sentences fingerprinted : {len(sentences)}")
print(f"NOT found in the built PDF       : {len(missing)}")
print()
for m in missing:
    flat = " ".join(m.split())
    print(f"  - {flat[:180]}")
    print()
