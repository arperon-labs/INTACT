# INTACT — Sound Worst-Case Topological Certificates for Segmentation Score Maps

**INTACT** (INference-Time Adversarial Certificates for Topology) certifies what
stays *intact* in a segmentation under **any** in-budget perturbation of its
score map: which components stay connected, which lines stay unbroken, which
holes stay unfillable.

Given a frozen score map `p` and an ℓ∞ budget `ε`, the `±ε` band splits the
image into `CERT_FG` (certainly foreground), `CERT_BG` (certainly background),
and a `POSSIBLE` band the adversary controls. The reachable binary masks are
then *exactly* a lattice interval (Proposition 1), and over that interval a
finite conjunction of monotone predicates is settled by checking just its **two
extremes** — both individually necessary, and not replaceable by any fixed
budget of random masks (Lemma 1).

Guarantees are **checked against the worst case, not sampled.**

---

## Headline results

| | |
|---|---|
| Soundness, real mosaic track | **0 violations in 16,675,936 checks** (30 crops × 4 certified classes × 6 ε) |
| Soundness, cross-domain | **0 violations in 10,578,388 checks** (DRIVE + CHASE_DB1, 3 normalizations each) |
| Non-vacuity (mosaic, ε=0.10) | 94% of grout length certainly-foreground; 0.766 certified-connected |
| Coverage **is not** connectivity | 1.2–1.7× apart on real maps (an order of magnitude only on blurred toy maps) |

The certificate held on maps degenerate enough that it had every excuse to
break (CHASE's over-segmented normalization: Dice 0.30, hundreds of certified
components per image).

**It is not a confidence map.** A feature's budget is the minimum over its
*wall* and its *interior* — an aggregate no per-pixel margin contains. See
`paper/figs/fig_graded.pdf`.

---

## Layout

```
paper/         paper.tex / paper.md / paper.pdf, refs.bib, figures,
               and the tooling that regenerates them:
                 make_figs.py      all figures
                 tables.py         Tables 2-3 from the committed results
                 check_numbers.py  traces EVERY numeral in the paper to a source
                 check_sync.py     paper.md prose vs. the built PDF
                 check_content.py  paper.md vs paper.tex, claim by claim
experiments/   the certification library + experiment runners
                 sandwich.py       the ±ε sandwich (Proposition 1)
                 topo.py           certified quantities + soundness harness
                 connectivity.py   certified-connectivity (segment graph)
                 persistence.py    cubical image-persistence cycle count
                 p_maps/           frozen score maps (see Reproducing, below)
results/       committed result JSONs — the source of every number in the paper
tests/         21 regression tests, incl. the planted-unsound cases
docs/          REGISTRY.md (pre-registration), RESULTS.md, GUARANTEE_STATEMENT.md,
               CLAIMS_INVENTORY.md, BUILD.md
```

## Install

```bash
pip install -r requirements.txt
```

Needs Python 3.10+. `gudhi` supplies cubical persistence; everything else is
NumPy/OpenCV/scikit-image/SciPy. All certification is **CPU-only**.

## Quickstart

```bash
pytest tests/ -q                       # 21 tests, ~2s
python paper/check_numbers.py          # every numeral in the paper -> its source
python paper/check_sync.py             # paper.md prose agrees with the built PDF
python paper/check_content.py          # paper.md and paper.tex agree claim-by-claim
```

`check_numbers.py` is the honesty gate: it re-derives the paper's statistics
from the committed JSONs and fails if any numeral in `paper.md` is untraceable.

## Reproducing the real track without the model

The frozen score maps are committed (`experiments/p_maps/`, 30 crops), so the
**entire real-track certification reproduces with no checkpoint and no GPU**:

```bash
cd experiments
python run_parallel.py --n-masks 30 --out ../results/results_real_hardened.json --jobs 8
```

Verified: certifying `crop_byzantine_00` at ε=0.10 straight from the shipped
p-maps returns coverage `0.889659`, connectivity `0.565624`, 10 components and
74 enclosure cycles — matching `results/results_real_hardened.json` exactly.

## What is *not* in this repository

- **The GROUT checkpoint and source crops.** Not redistributed. The committed
  p-maps make the certification reproducible without them.
- **DRIVE / CHASE_DB1.** Standard public retinal benchmarks, used under their
  own terms; obtain them from their maintainers. We ship the code that reads
  them and the per-image result JSONs, not the images. The cross-domain track
  is **model-free** (classical Frangi vesselness — no third-party weights).
- **Intermediate caches** (e.g. CHASE p-maps) — regenerable.

If you hold any of the above, put it under `external-data/` at the repository
root (`external-data/data/realset/crops`, `external-data/data/external`,
`external-data/checkpoints`), or point `INTACT_EXTERNAL_DATA` at your own tree.
Nothing in this repository reads outside its own directory, and every code path
that touches external data degrades gracefully when it is absent — the results
in the paper reproduce without any of it.

## Building the paper

```bash
cd paper
python make_figs.py && python tables.py && python check_numbers.py
tectonic paper.tex
```

## A note on the name

Some filenames, code comments and historical records use **TOPOCERT**, the
project's original working name. It refers to the same work as INTACT.

## Citation

Preprint **v1**. If you use this work, please cite it:

```bibtex
@misc{lovecky2026intact,
  author       = {Loveck{\'y}, Radoslav},
  title        = {{INTACT}: Sound Worst-Case Topological Certificates for
                  Segmentation Score Maps},
  year         = {2026},
  publisher    = {Zenodo},
  version      = {v1},
  doi          = {PENDING},
  url          = {https://github.com/arperon-labs/INTACT}
}
```

## License

Licensed under the **Apache License 2.0** — see [LICENSE](LICENSE) and
[NOTICE](NOTICE). Apache-2.0 includes an express patent grant; no patent is
being filed on this work.

The paper itself (`paper/paper.{md,tex,pdf}` and `paper/figs/`) is covered by
the same licence here; the Zenodo record carries its own licence field, and a
Creative Commons licence is the usual choice for the document there.

Third-party datasets (DRIVE, CHASE_DB1) and the mosaic source imagery are
**not** redistributed — see [NOTICE](NOTICE) for their terms.

Radoslav Lovecký  ·  Arperon
`info@arperon.com`  ·  ORCID [0009-0000-5669-920X](https://orcid.org/0009-0000-5669-920X)
