"""Split-half stability of the calibration-
defined eps estimator (registered 2026-07-15, REGISTRY 'SPLIT-HALF
EPS-STABILITY REGISTRATION' — committed before this file).

The estimator (sandwich.useful_eps, the paper's rule) is certificate-blind:
it reads only |p-1/2| margins. This script measures its split-half drift on
the 30 committed p maps and the grid-snap agreement rate; the certified-
quantity consequence of any drift is read off the committed H-C3-nested
sweep, which is the registered sensitivity ablation.

  python eps_stability.py    # seconds, CPU; writes results_eps_stability.json
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sandwich import useful_eps  # noqa: E402

EPS_GRID = [0.02, 0.05, 0.1, 0.15, 0.25, 0.4]
R = 200
SEED = 0


def snap(e):
    return min(EPS_GRID, key=lambda g: abs(g - e))


def main():
    pmaps = sorted((HERE / "p_maps").glob("*.npy"))
    assert len(pmaps) == 30, f"expected 30 p maps, found {len(pmaps)}"
    per_crop = {f.stem: useful_eps(np.load(f)) for f in pmaps}
    vals = np.array(list(per_crop.values()))
    cohort = float(np.median(vals))

    rng = np.random.default_rng(SEED)
    drifts, agree = [], 0
    splits = []
    for _ in range(R):
        idx = rng.permutation(30)
        a, b = vals[idx[:15]], vals[idx[15:]]
        ea, eb = float(np.median(a)), float(np.median(b))
        drifts.append(abs(ea - eb))
        same = snap(ea) == snap(eb)
        agree += same
        splits.append({"eps_A": ea, "eps_B": eb, "snap_A": snap(ea),
                       "snap_B": snap(eb), "same_grid_point": bool(same)})
    drifts = np.array(drifts)

    out = {"seed": SEED, "R": R, "n_crops": 30,
           "per_crop_useful_eps": {k: float(v) for k, v in per_crop.items()},
           "cohort_useful_eps": cohort,
           "cohort_snapped": snap(cohort),
           "drift_median": float(np.median(drifts)),
           "drift_max": float(drifts.max()),
           "drift_p95": float(np.quantile(drifts, 0.95)),
           "grid_agreement_rate": agree / R,
           "grid_spacing_at_cohort": 0.4 - 0.25,   # adjacent grid gap there
           "splits": splits}
    (HERE / "results_eps_stability.json").write_text(json.dumps(out, indent=1))
    print(f"cohort useful_eps {cohort:.3f} -> grid {snap(cohort)}")
    print(f"split-half drift: median {np.median(drifts):.4f}, "
          f"p95 {np.quantile(drifts, 0.95):.4f}, max {drifts.max():.4f} "
          f"(adjacent grid gap at cohort: {0.4 - 0.25})")
    print(f"grid agreement: {agree}/{R} = {agree / R:.3f}")


if __name__ == "__main__":
    main()
