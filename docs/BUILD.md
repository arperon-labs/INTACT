# Building the INTACT paper

Everything regenerates from committed sources; nothing is hand-copied.

## Pipeline (order matters)

Run these from `paper/`:

```
python tables.py          # generated/table_{real,toy}.{md,tex}  <- ../results/*.json
python make_figs.py       # figs/*.{png,pdf}                     <- JSONs + regression constructions
python check_numbers.py   # gate: every numeral in paper.md traced; exits 1 on any untraced numeral
tectonic paper.tex        # paper.pdf (runs BibTeX on refs.bib automatically)
```

Verified toolchain: Python 3.13 (numpy, matplotlib), Tectonic 0.16.9. Any
TeX Live works too:

```
pdflatex paper && bibtex paper && pdflatex paper && pdflatex paper
```

## Inputs (read-only; never edited from here)

- `../results/results_real_hardened.json` — T-real, 30 crops (authoritative)
- `../results/results_toy_hardened.json` — T-toy re-emit (the toy table
  printed in the paper; carries persistence + connectivity columns)
- `../docs/RESULTS.md` and `../docs/REGISTRY.md` — claim licenses;
  `check_numbers.py` greps both and fails if the wording it depends on moved
- The counterexample figures replicate the constructions in
  `../tests/test_topocert.py` exactly (small arrays; regenerated rather than
  imported, so `experiments/` stays untouched by the paper build)

## Outputs

- `paper.pdf` (includes appendices and references) and `paper.md` — the
  same content, with `paper.md` as the markdown master that `check_numbers.py`
  traces
- `generated/` tables and `figs/` are build products, but are committed so the
  repository is inspectable without running anything

## Notes

- `refs.bib` contains only identity-verified entries. Citation placeholders
  are fully resolved: none remain, and the `\citeph` macro that used to render
  them is retired.
- `check_numbers.py` is the honesty gate. It re-derives the paper's statistics
  from the committed JSONs and fails if any numeral in `paper.md` cannot be
  traced to a source. Run it before any commit that touches numbers.
- Figures are colorblind-safe (Okabe-Ito) and encode by lightness as well as
  hue, so they survive grayscale printing.
