"""Parallel chase_v2. Same computation and OUTPUT FORMAT as chase_v2.py, but
the heavy per-(transform, image, eps) cells run in a process pool. The serial
chase_v2 was on track for ~31h (3 transforms x 20 images x 6 eps of
certified_topology + soundness on 960x999 vessel maps, ~270s/cell, one core);
parallelized -> ~1-2h with progress. Deterministic (fixed seeds, independent
cells; float32 .npy round-trip is exact) => byte-identical to the serial run.

Reuses chase_v2's frangi_p / dice_iou / TRANSFORMS / constants verbatim, so
the p-maps and metrics are identical. The sweep record piggybacks on the
eps==eps_u soundness cell (chase_v2 recomputes certified_topology there; we
compute it once per cell).

  python chase_parallel.py --jobs 20               # full run
  python chase_parallel.py --n-img 3 --eps 0.1,0.4 --transforms cbrt  # smoke
"""
import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import chase_v2 as cv  # noqa: E402  (frangi_p, dice_iou, TRANSFORMS, _bin2d, consts)
from topo import certified_topology, soundness_check  # noqa: E402
from sandwich import useful_eps  # noqa: E402

PMAP_DIR = HERE / "chase_pmaps"
_DATA = None            # per-worker: [(name, green, gt, fov)]
_PMAPS = None           # per-worker: {(tname, idx): p}
_N_IMG = 20             # per-worker copy (set via initargs)
_N_SAMPLES = 16         # per-worker soundness masks (set via initargs)


def load_data(n_img):
    """Byte-identical to chase_v2.main()'s loader (same crops, order, FOV)."""
    z = zipfile.ZipFile(cv.ZIP)
    load = lambda n: np.asarray(Image.open(io.BytesIO(z.read(n))))
    g = lambda sub: sorted(n for n in z.namelist()
                           if n.startswith(f"{cv.BASE}/{sub}/")
                           and not n.endswith("/"))
    imgs = [n for n in g("images") if n.endswith(".tif")]
    m1, msk = g("1st_manual"), g("mask")
    assert len(imgs) == len(m1) == len(msk) == 20
    data = []
    for i in range(n_img):
        green = load(imgs[i])[..., 1].astype(np.float32) / 255.0
        gt = cv._bin2d(load(m1[i]))
        fov = binary_erosion(cv._bin2d(load(msk[i])), iterations=cv.FOV_ERODE)
        data.append((imgs[i].split("/")[-1], green, gt & fov, fov))
    return data


def _init_pmap(n_img):
    global _DATA, _N_IMG
    _N_IMG = n_img
    _DATA = load_data(n_img)


def _pmap_task(task):
    tname, idx = task
    _, green, _, fov = _DATA[idx]
    p = cv.frangi_p(green, fov, cv.TRANSFORMS[tname])
    np.save(PMAP_DIR / f"{tname}__{idx:02d}.npy", p)
    return tname, idx, float(useful_eps(p))


def _init_heavy(n_img, tnames, n_samples):
    global _DATA, _PMAPS, _N_IMG, _N_SAMPLES
    _N_IMG = n_img
    _N_SAMPLES = n_samples
    _DATA = load_data(n_img)
    _PMAPS = {(t, i): np.load(PMAP_DIR / f"{t}__{i:02d}.npy")
              for t in tnames for i in range(n_img)}


def _cell(task):
    """One (transform, image, eps) cell: certified_topology once, soundness
    (H-C1), plus the sweep record when eps == this transform's eps_u."""
    tname, idx, eps, eps_u = task
    name, _, gt, fov = _DATA[idx]
    p = _PMAPS[(tname, idx)]
    ct = certified_topology(p, eps, fov, 1.0)
    classes = ([{**c, "kind": "fg"} for c in ct["components"]]
               + [{**t, "kind": "bg"} for t in ct["tesserae"]]
               + [{**cy, "kind": "cycle"} for cy in ct["cycles"]]
               + [{"support": s, "kind": "connectivity"}
                  for s in ct["connectivity_segments"]])
    v, ch = soundness_check(p, eps, classes, n_samples=_N_SAMPLES)
    rec = None
    if abs(eps - eps_u) < 1e-12:
        dice, iou = cv.dice_iou(p > 0.5, gt, fov)
        rec = {"name": name, "dice": dice, "iou": iou,
               "n_components": ct["n_certified_components"],
               "conn_seg_frac": ct["certified_connected_seg_frac"],
               "n_cycles": ct["n_certified_cycles"],
               "coverage": ct["grout_len_certainly_fg_frac"]}
    return tname, idx, int(v), int(ch), rec


def main():
    import multiprocessing as mp
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=max(1, mp.cpu_count() - 4))
    ap.add_argument("--n-img", type=int, default=20)
    ap.add_argument("--eps", default=None, help="comma list; default full grid")
    ap.add_argument("--transforms", default=None, help="comma list; default all")
    ap.add_argument("--n-samples", type=int, default=16,
                    help="soundness masks per cell; 2 extremes are exhaustive "
                         "(Lemma 1), rest are cross-checks. 4 for dense CHASE.")
    ap.add_argument("--out", default="results_chase.json")
    a = ap.parse_args()

    eps_grid = ([float(x) for x in a.eps.split(",")] if a.eps
                else list(cv.EPS_SWEEP))
    tnames = (a.transforms.split(",") if a.transforms else list(cv.TRANSFORMS))
    n = a.n_img
    PMAP_DIR.mkdir(exist_ok=True)
    print(f"chase parallel: {len(tnames)} transforms x {n} imgs x "
          f"{len(eps_grid)} eps, n_samples={a.n_samples}, on {a.jobs} workers",
          flush=True)

    # ---- phase 1: p-maps (cheap frangi; save to disk, collect useful_eps) ----
    tasks1 = [(t, i) for t in tnames for i in range(n)]
    ueps = {t: {} for t in tnames}
    with mp.Pool(a.jobs, initializer=_init_pmap, initargs=(n,)) as pool:
        for tname, idx, ue in pool.imap_unordered(_pmap_task, tasks1):
            ueps[tname][idx] = ue
    epsu = {}
    for t in tnames:
        ue = float(np.median([ueps[t][i] for i in range(n)]))
        epsu[t] = (ue, min(eps_grid, key=lambda e: abs(e - ue)))
    print("p-maps done; eps_u = "
          + ", ".join(f"{t}:{epsu[t][1]}" for t in tnames), flush=True)

    # ---- phase 2: heavy cells (H-C1 soundness + sweep at eps_u) ----
    tasks2 = [(t, i, e, epsu[t][1])
              for t in tnames for i in range(n) for e in eps_grid]
    hc1 = {t: [0, 0] for t in tnames}
    sweep = {t: {} for t in tnames}
    with mp.Pool(a.jobs, initializer=_init_heavy,
                 initargs=(n, tnames, a.n_samples)) as pool:
        done = 0
        for tname, idx, v, ch, rec in pool.imap_unordered(_cell, tasks2):
            hc1[tname][0] += v
            hc1[tname][1] += ch
            if rec is not None:
                sweep[tname][idx] = rec
            done += 1
            if done % 10 == 0 or done == len(tasks2):
                print(f"  {done}/{len(tasks2)} cells", flush=True)

    # ---- assemble (matches chase_v2.main() output structure) ----
    out = {"transforms": tnames, "primary": "cbrt", "eps_sweep": eps_grid,
           "n_samples": a.n_samples,
           "H_C1_violations": 0, "H_C1_checks": 0, "per_transform": {}}
    for t in tnames:
        viol, checks = hc1[t]
        out["H_C1_violations"] += viol
        out["H_C1_checks"] += checks
        if viol:
            out["HALT"] = f"H-C1 UNSOUND on CHASE/{t}: {viol}"
            (HERE / a.out).write_text(json.dumps(out, indent=1))
            raise SystemExit(out["HALT"])
        ue, eps_u = epsu[t]
        per = [sweep[t][i] for i in range(n)]
        dv = [r["dice"] for r in per]
        rho = {q: {"rho": float(spearmanr(dv, [r[q] for r in per])[0]),
                   "p_value": float(spearmanr(dv, [r[q] for r in per])[1])}
               for q in ("n_components", "conn_seg_frac", "n_cycles", "coverage")}
        out["per_transform"][t] = {
            "useful_eps": ue, "eps_used": eps_u,
            "dice_mean": float(np.mean(dv)), "dice_min": float(np.min(dv)),
            "dice_max": float(np.max(dv)), "spearman_dice_vs": rho,
            "per_image": per}
        print(f"[{t}] H-C1 0/{checks} | eps_u={eps_u} Dice {np.mean(dv):.3f} | "
              + " ".join(f"rho({q})={rho[q]['rho']:+.2f}" for q in rho),
              flush=True)

    (HERE / a.out).write_text(json.dumps(out, indent=1))
    print(f"wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
