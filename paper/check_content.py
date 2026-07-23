"""Do paper.md and paper.tex carry the same CLAIMS?

check_sync.py compares paper.md against the built PDF by 6-gram fingerprint. It
catches a sentence that is MISSING from one side, but not one that is PRESENT in
both with altered wording — so a corrected number, a flipped inequality, or a
dropped qualifier in one master slips past it. That happened repeatedly (the
abstract's `<` vs `≤`; a §10 sentence; three §3–§5 clauses).

This guard closes that gap. It normalises both masters to a canonical token
stream — LaTeX macros and markdown markup stripped, math mapped to a common
ASCII form (\\CBG→certbg, \\le/≤→leq, \\eps/ε→eps, ½→half, …) — matches each md
sentence to its best tex counterpart, and reports pairs that are clearly the
same sentence yet differ in a MEANINGFUL token: a number, an inequality, a
negation, or a quantifier. Notation and cross-reference differences are
normalised away; only claim-level differences remain.

  python check_content.py            # report
  python check_content.py --quiet    # exit code only (0 = no claim differs)

ACCEPTED lists the residual structural artefacts (subscript indices, a
markdown URL autolink) with the reason each is benign. Anything not listed is a
real divergence until shown otherwise.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = Path(__file__).resolve().parent
QUIET = "--quiet" in sys.argv

# ordered: multi-char / macro forms first
NOTATION = [
    (r"\\CFG\b|CERT_FG", " certfg "), (r"\\CBG\b|CERT_BG", " certbg "),
    (r"\\POSS\b|POSSIBLE", " poss "),
    (r"\\tfrac12|\\tfrac\{1\}\{2\}|\\frac\{1\}\{2\}|½", " half "),
    (r"\\varepsilon|\\eps\b|ε", " eps "),
    (r"\\leq\b|\\le\b|≤", " leq "), (r"\\geq\b|\\ge\b|≥", " geq "),
    (r"<=", " leq "), (r">=", " geq "), (r"<", " lt "), (r">", " gt "),
    (r"\\neq\b|≠", " neq "),
    (r"\\hookrightarrow|\\to\b|→|↪", " to "),
    (r"\\beta_?\{?0\}?|β₀", " beta0 "), (r"\\beta_?\{?1\}?|β₁", " beta1 "),
    (r"\\ell_?\\?infty|ℓ∞|ℓ_∞", " linf "),
    (r"\\rho\b|ρ", " rho "), (r"\\sigma\b|σ", " sigma "), (r"\\alpha\b|α", " alpha "),
    (r"\\times\b|×", " times "), (r"\\approx\b|≈", " approx "),
    (r"\\subseteq\b|⊆", " subset "), (r"\\lnot\b|¬", " not "),
    (r"M_?\{?\\?min\}?|Mmin", " mmin "), (r"M_?\{?\\?max\}?|Mmax", " mmax "),
    (r"H_?\{?1\}?\b|H₁", " hone "), (r"H_?\{?0\}?\b|H₀", " hzero "),
]

# cross-references: \ref in tex (vanishes), literals in md. Cover ranges and
# 'N and M' forms, since a leftover number reads as a false claim difference.
XREF = re.compile(
    r"§+\s*\d[\d.]*(\s*(and|to|[–—-])\s*\d[\d.]*)?"
    r"|\b(sections?|secs?|tables?|figures?|figs?|propositions?|props?|lemmas?|"
    r"appendix|appendices|contributions?|equations?|eqs?|quantity|item|row)"
    r"\.?~?\s*\d[\d.]*(\s*(and|to|[–—-])\s*\d[\d.]*)?"
    r"|\b(appendix|appendices)\s+[a-e]\b",
    re.I)
SUBSCRIPT = re.compile(r"(?<=[a-z])_\{?\d\}?|[₀₁₂₃₄₅₆₇₈₉]", re.I)

# structural residue verified benign — each with its reason.
ACCEPTED = [
    ("survives to eps , that component to eps", "graded-cert subscripts eps_1/eps_2"),
    ("closed superlevel filtration", "F_{1/2} subscript fraction in the rank formula"),
    ("sources of this paper are at", "md wraps the URL in <> (autolink); tex uses \\url"),
    ("synthetic 256", "toy-score formula in display math; sigma=1.3 and 0.07 "
                       "verified identical in both masters, tex parser truncates at \\!"),
]


def apply_notation(t):
    for pat, rep in NOTATION:
        t = re.sub(pat, rep, t)
    return t


def md_plain(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"^\s*\|.*$", " ", t, flags=re.M)               # table rows
    t = re.sub(r"^#+.*$", " ", t, flags=re.M)                  # headings
    t = re.sub(r"^\s*\d+\.\s+", " ", t, flags=re.M)            # ordered-list markers
    t = XREF.sub(" ", t)                                       # refs, before dash strip
    t = re.sub(r"\*\(.*?\)\*", " ", t, flags=re.S)             # caption asides
    t = re.sub(r"<https?://[^>]+>", " urltoken ", t)           # autolinked URL
    t = re.sub(r"`([^`]*)`", r" \1 ", t)                       # code spans
    t = re.sub(r"\[[a-z][\w:.-]*\d{4}[\w]*\]|\[cite[^\]]*\]", " ", t)  # cite keys
    t = t.replace("*", " ").replace("—", " ").replace("–", " ")
    t = re.sub(r"~\s*(?=CERT|\\CBG|\\CFG)", " not ", t)        # md complement
    t = apply_notation(t)
    t = SUBSCRIPT.sub("", t)
    t = XREF.sub(" ", t)
    return t


def tex_plain(t):
    t = re.sub(r"(?<!\\)%.*$", " ", t, flags=re.M)
    if "\\maketitle" in t:
        t = t[t.index("\\maketitle"):]
    t = re.sub(r"\\begin\{(figure|table)\*?\}.*?\\end\{(figure|table)\*?\}", " ", t, flags=re.S)
    t = re.sub(r"\\(sub)*section\*?\{[^{}]*\}", " ", t)        # section headings
    t = re.sub(r"\\paragraph\{[^{}]*\}", " ", t)              # run-in headings kept? no: they are labels
    t = re.sub(r"\\(label|ref|eqref|cite[a-z]*|citep|citet|url|includegraphics|input|thanks)\s*\{[^{}]*\}", " ", t)
    t = re.sub(r"\\S~?\\?ref\{[^{}]*\}", " ", t)
    for _ in range(4):
        t = re.sub(r"\\(emph|textbf|texttt|textit|textsc|mathrm|operatorname|text)\{([^{}]*)\}", r" \2 ", t)
    t = apply_notation(t)
    t = re.sub(r"\\(begin|end)\{[^}]*\}", " ", t)
    t = re.sub(r"\\[a-zA-Z]+\b", " ", t)
    t = t.replace("$", " ").replace("{", " ").replace("}", " ").replace("&", " ").replace("\\", " ")
    t = SUBSCRIPT.sub("", t)
    t = XREF.sub(" ", t)
    return t


def toks(t):
    return [w for w in re.sub(r"[^a-z0-9]+", " ", t.lower()).split()
            if len(w) > 1 or w.isdigit()]


def sents(plain):
    plain = re.sub(r"\s+", " ", plain)
    out = []
    for s in re.split(r"(?<=[.!?])\s+", plain):
        tk = toks(s)
        if len(tk) >= 6:
            out.append((s.strip(), tk))
    return out


def accepted(s):
    flat = " ".join(s.split()).lower()
    return any(frag.lower() in flat for frag, _ in ACCEPTED)


MEANINGFUL = re.compile(r"^(leq|lt|geq|gt|eq|neq|\d[\d.,]*|not|no|never|cannot|"
                        r"neither|only|every|all|exactly|refuted|unsound|sound|"
                        r"monotone|equal|equivalent)$")


def main():
    md = sents(md_plain((P / "paper.md").read_text(encoding="utf-8")))
    tex = sents(tex_plain((P / "paper.tex").read_text(encoding="utf-8")))
    tex_sets = [(s, set(tk)) for s, tk in tex]

    hits = []
    for ms, mt in md:
        ma = set(mt)
        best_s, best_set, best_j = None, None, -1.0
        for ts, tset in tex_sets:
            j = len(ma & tset) / max(1, len(ma | tset))
            if j > best_j:
                best_s, best_set, best_j = ts, tset, j
        if best_j < 0.5 or best_j >= 0.995:
            continue
        fmd = {w for w in (ma - best_set) if MEANINGFUL.match(w)}
        ftex = {w for w in (best_set - ma) if MEANINGFUL.match(w)}
        if (fmd or ftex) and not accepted(ms) and not accepted(best_s):
            hits.append((best_j, ms, best_s, sorted(fmd), sorted(ftex)))

    if not QUIET:
        for j, ms, ts, fmd, ftex in hits:
            print(f"### CLAIM DIFFERS (jaccard {j:.2f})")
            print(f"  MD : {' '.join(ms.split())[:190]}")
            print(f"  TEX: {' '.join(ts.split())[:190]}")
            print(f"  only MD: {fmd}   only TEX: {ftex}\n")
        print("IN SYNC: no claim-level difference between paper.md and paper.tex."
              if not hits else f"---- {len(hits)} claim-level divergence(s) ----")
    return 1 if hits else 0


sys.exit(main())
