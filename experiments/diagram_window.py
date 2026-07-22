"""R-EQ diagram-window identity (registered 2026-07-15,
REGISTRY 'R-EQ DIAGRAM-WINDOW REGISTRATION' — committed before this file).

H-R1: the persistence-form certified-cycle count at every eps equals the
number of window-straddling points of p's OWN superlevel H1 diagram —
  certified(eps) = #{ intervals: p_birth > 1/2+eps and p_death < 1/2-eps }
computed from ONE gudhi diagram per crop (CubicalComplex on -p), against the
committed convention (persistence.certified_cycle_count on cert_sets).
Debugs on the three H-C4 regression constructions first. Also emits the
eps* rider: per-feature maximal certified budget
  eps*(feature) = min(p_birth - 1/2, 1/2 - p_death).

  python diagram_window.py    # CPU-only; writes results_diagram_window.json
"""
import json
import sys
from pathlib import Path

import gudhi
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sandwich import cert_sets  # noqa: E402
from persistence import certified_cycle_count  # noqa: E402

EPS_SWEEP = [0.02, 0.05, 0.1, 0.15, 0.25, 0.4]


def superlevel_h1(p):
    """H1 intervals of the superlevel filtration of p, in p-scale:
    (p_birth, p_death) with p_birth > p_death (feature exists for
    thresholds in between). One diagram per crop; all eps read off it."""
    cc = gudhi.CubicalComplex(top_dimensional_cells=(-p).astype(np.float64))
    cc.persistence(homology_coeff_field=2, min_persistence=0.0)
    iv = cc.persistence_intervals_in_dimension(1)
    if iv.size == 0:
        return np.zeros((0, 2))
    return np.column_stack([-iv[:, 0], -iv[:, 1]])   # (p_birth, p_death)


def window_count(intervals, eps):
    """Certified count at eps = window-straddling points (strict, mirroring
    CERT strictness)."""
    if not len(intervals):
        return 0
    b, d = intervals[:, 0], intervals[:, 1]
    return int(np.sum((b > 0.5 + eps) & (d < 0.5 - eps)))


def convention_count(p, eps):
    s = cert_sets(p, eps)
    n, ok = certified_cycle_count(s["CERT_FG"], s["CERT_BG"])
    assert ok, "gudhi required (registered: no silent fallback)"
    return n


# ---- H-C4 regression constructions (exact test-suite geometry) ------------
def ring(interior_p, H=40):
    yy, xx = np.mgrid[:H, :H]
    r = np.sqrt((yy - 20) ** 2 + (xx - 20) ** 2)
    p = np.full((H, H), 0.05, np.float32)
    p[(r > 8) & (r < 14)] = 0.95
    p[r <= 8] = interior_p
    return p


def grid_of_holes(H=64):
    """3x3 grid of enclosed cells (RESULTS.md regression count 9): lines at
    0/20/40/60 leave 3 gaps per axis. (H=84 would give a 4x4 grid = 16.)"""
    grout = np.zeros((H, H), bool)
    for k in range(0, H, 20):
        grout[k:k + 4, :] = True
        grout[:, k:k + 4] = True
    return np.where(grout, 0.95, 0.05).astype(np.float32)


def main():
    # ---- debug gate: the three H-C4 cases at eps=0.1 ----------------------
    cases = [("ring-over-POSSIBLE", ring(0.5), 0),
             ("ring-over-CERT_BG", ring(0.05), 1),
             ("grid-of-holes", grid_of_holes(), 9)]
    for name, p, expect in cases:
        w = window_count(superlevel_h1(p), 0.1)
        c = convention_count(p, 0.1)
        assert w == c == expect, \
            f"H-C4 debug gate FAILED on {name}: window {w}, convention {c}, " \
            f"expected {expect} — investigate before touching real maps"
        print(f"debug {name}: window {w} == convention {c} == {expect} OK",
              flush=True)

    # ---- H-R1 on the 30 committed p maps ----------------------------------
    out = {"eps_sweep": EPS_SWEEP, "crops": {}, "H_R1_pass": True,
           "n_mismatch": 0, "eps_star": {}}
    pmaps = sorted((HERE / "p_maps").glob("*.npy"))
    assert len(pmaps) == 30
    for f in pmaps:
        p = np.load(f)
        iv = superlevel_h1(p)
        rec = {}
        for eps in EPS_SWEEP:
            w = window_count(iv, eps)
            c = convention_count(p, eps)
            rec[f"{eps}"] = {"window": w, "convention": c, "match": w == c}
            if w != c:
                out["H_R1_pass"] = False
                out["n_mismatch"] += 1
        out["crops"][f.stem] = rec
        # eps* distribution of features certified at ANY swept eps
        if len(iv):
            eps_star = np.minimum(iv[:, 0] - 0.5, 0.5 - iv[:, 1])
            pos = eps_star[eps_star > 0]
            out["eps_star"][f.stem] = {
                "n_positive": int(pos.size),
                "median": float(np.median(pos)) if pos.size else None,
                "max": float(pos.max()) if pos.size else None}
        print(f"{f.stem}: " + " ".join(
            f"{e}:{rec[f'{e}']['window']}{'=' if rec[f'{e}']['match'] else '!'}"
            f"{rec[f'{e}']['convention']}" for e in EPS_SWEEP), flush=True)

    total = 30 * len(EPS_SWEEP)
    print(f"H-R1: {total - out['n_mismatch']}/{total} identities hold "
          f"-> {'PASS' if out['H_R1_pass'] else 'MISMATCH (investigate)'}",
          flush=True)
    (HERE / "results_diagram_window.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
