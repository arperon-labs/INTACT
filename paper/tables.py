"""Regenerate the paper's eps-sweep tables from the committed results JSONs.

Read-only over experiments/; writes Markdown + LaTeX tables to generated/.
Rounding convention (stated in the paper): fractions to 3 decimals, per-crop
mean counts to 1 decimal. Every printed numeral is thereby traced to a JSON
key (check_numbers.py re-verifies the paper text against the same sources).

  python tables.py          # writes generated/table_{real,toy}.{md,tex}
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1] / "experiments" / "topocert"
OUT = HERE / "generated"
EPS = ["0.02", "0.05", "0.1", "0.15", "0.25", "0.4"]

# T-real (results_real_hardened.json): full hardened column set on 30 real
# crops. The parallel re-emit (run_parallel.py) resolved the former
# [real-p re-emit pending] connectivity + persistence columns; validated
# byte-identical to the committed 24-crop results.json on the shared crops.
REAL_COLS = [
    ("grout_len_certainly_fg_frac", "coverage", 3),
    ("certified_connected_len_frac", "conn-len", 3),
    ("certified_connected_seg_frac", "conn-seg", 3),
    ("n_certified_components", r"\#comp", 1),
    ("n_certified_tessera_cores", r"\#tess", 1),
    ("n_certified_cycles_enclosure", r"\#cyc-encl", 1),
    ("n_certified_cycles_persistence", r"\#cyc-pers", 1),
    ("abstain_frac", "abstain", 3),
]
TOY_COLS = [
    ("grout_len_certainly_fg_frac", "coverage", 3),
    ("certified_connected_len_frac", "conn-len", 3),
    ("certified_connected_seg_frac", "conn-seg", 3),
    ("n_certified_components", r"\#comp", 1),
    ("n_certified_tessera_cores", r"\#tess", 1),
    ("n_certified_cycles_enclosure", r"\#cyc-encl", 2),
    ("n_certified_cycles_persistence", r"\#cyc-pers", 2),
    ("abstain_frac", "abstain", 3),
]


def fmt(v, nd):
    return f"{v:.{nd}f}"


def build(sweep, cols):
    head = ["eps"] + [label for _, label, _ in cols]
    rows = []
    for e in EPS:
        rows.append([f"{float(e):.2f}"] +
                    [fmt(sweep[e][key], nd) for key, _, nd in cols])
    return head, rows


def to_md(head, rows):
    h = [c.replace("\\#", "#") for c in head]
    lines = ["| " + " | ".join(h) + " |",
             "|" + "|".join("---" for _ in h) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def to_tex(head, rows, caption, label):
    align = "l" + "r" * (len(head) - 1)
    body = " \\\\\n".join(" & ".join(r) for r in rows)
    heads = " & ".join(f"\\textbf{{{c}}}" for c in head)
    return (f"\\begin{{table}}[t]\n\\centering\n\\caption{{{caption}}}\n"
            f"\\label{{{label}}}\n\\small\n\\begin{{tabular}}{{{align}}}\n"
            f"\\toprule\n{heads} \\\\\n\\midrule\n{body} \\\\\n"
            f"\\bottomrule\n\\end{{tabular}}\n\\end{{table}}\n")


def main():
    OUT.mkdir(exist_ok=True)
    real = json.loads((EXP / "results_real_hardened.json").read_text())
    toy = json.loads((EXP / "results_toy_hardened.json").read_text())
    assert real["track"] == "T-real" and real["H_C1_soundness_violations"] == 0
    assert toy["track"] == "T-toy" and toy["H_C1_soundness_violations"] == 0

    h, r = build(real["sweep"], REAL_COLS)
    (OUT / "table_real.md").write_text(to_md(h, r))
    (OUT / "table_real.tex").write_text(to_tex(
        h, r,
        "T-real: certified quantities vs.\\ $\\varepsilon$ (frozen zero-shot "
        "model on 30 real $512\\times512$ crops; per-crop means). No ratio "
        "stands alone: the denominators are $\\eps$-independent --- coverage "
        "and conn-len over a mean skeleton length of $24{,}728.9$\\,px per "
        "crop, conn-seg over $2{,}739.8$ segments, abstain over the ROI (here "
        "the whole crop). Numerators at $\\eps=0.10/0.40$: certified length "
        "$23{,}408.1/14{,}969.8$\\,px, certified segments $2{,}173.2/1{,}003.5$. "
        "Each fraction is the mean of the per-crop ratios, not the ratio of "
        "the means.",
        "tab:real"))

    h, r = build(toy["sweep"], TOY_COLS)
    (OUT / "table_toy.md").write_text(to_md(h, r))
    (OUT / "table_toy.tex").write_text(to_tex(
        h, r,
        "T-toy (hardened re-emit, 24 synthetic maps): all columns incl.\\ "
        "certified-connected fractions (1b) and persistence cycles (1a). "
        "Toy $p$ is a blurred copy of the ground truth --- validation of "
        "the machinery, not evidence about real-model behaviour.",
        "tab:toy"))
    for f in sorted(OUT.glob("table_*")):
        print(f"wrote {f.name}")
    print(to_md(*build(real["sweep"], REAL_COLS)))


if __name__ == "__main__":
    main()
