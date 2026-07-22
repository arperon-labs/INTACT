"""Second cross-domain track: CHASE_DB1 V2 decoupling (registered 2026-07-16,
REGISTRY 'CHASE_DB1 REGISTRATION'). Identical protocol P and H-V2 analysis to
drive_v2.py, on the 20 CHASE training images (960x999). Doubles the V2
evidence across a second retinal dataset; H-C1 soundness re-run gates.

  python chase_v2.py    # CPU-only; writes results_chase.json
"""
import io
import json
import os
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion
from scipy.stats import spearmanr
from skimage.filters import frangi, threshold_otsu

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sandwich import cert_sets, useful_eps  # noqa: E402
from topo import certified_topology, soundness_check  # noqa: E402

ZIP = (EXTERNAL / "data" / "external"
       / "chasedb1" / "chasedb1.zip")
BASE = "chase/training/training"
EPS_SWEEP = [0.02, 0.05, 0.1, 0.15, 0.25, 0.4]
FOV_ERODE, K = 6, 12.0
TRANSFORMS = {"cbrt": lambda x: np.cbrt(x),
              "sqrt": lambda x: np.sqrt(x),
              "log": lambda x: np.log1p(x / (x[x > 0].mean() + 1e-12))
              if (x > 0).any() else x}


def _bin2d(a):
    if a.ndim > 2:
        a = a[..., 0]
    return a > (a.max() / 2)


def frangi_p(green, fov, tf):
    resp = np.where(fov, frangi(green, sigmas=range(1, 6), black_ridges=True),
                    0.0).astype(np.float32)
    r = tf(resp)
    sel = r[fov & (resp > 1e-7)]
    t = threshold_otsu(sel) if sel.size else 1.0
    return np.where(fov, 1 / (1 + np.exp(-K * (r - t))), 0.0).astype(np.float32)


def dice_iou(pred, gt, fov):
    pred, gt = pred & fov, gt & fov
    inter = float((pred & gt).sum())
    return (2 * inter / (pred.sum() + gt.sum() + 1e-9),
            inter / ((pred | gt).sum() + 1e-9))


def main():
    z = zipfile.ZipFile(ZIP)
    load = lambda n: np.asarray(Image.open(io.BytesIO(z.read(n))))
    g = lambda sub: sorted(n for n in z.namelist()
                           if n.startswith(f"{BASE}/{sub}/") and not n.endswith("/"))
    imgs = [n for n in g("images") if n.endswith(".tif")]
    m1, msk = g("1st_manual"), g("mask")
    assert len(imgs) == len(m1) == len(msk) == 20
    data = []
    for i in range(20):
        green = load(imgs[i])[..., 1].astype(np.float32) / 255.0
        gt = _bin2d(load(m1[i]))
        fov = binary_erosion(_bin2d(load(msk[i])), iterations=FOV_ERODE)
        data.append((imgs[i].split("/")[-1], green, gt & fov, fov))

    out = {"transforms": list(TRANSFORMS), "primary": "cbrt",
           "eps_sweep": EPS_SWEEP, "H_C1_violations": 0, "H_C1_checks": 0,
           "per_transform": {}}
    for tname, tf in TRANSFORMS.items():
        pmaps = [frangi_p(g_, f, tf) for _, g_, _, f in data]
        viol = checks = 0
        for (name, green, gt, fov), p in zip(data, pmaps):
            for eps in EPS_SWEEP:
                ct = certified_topology(p, eps, fov, 1.0)
                classes = (
                    [{**c, "kind": "fg"} for c in ct["components"]]
                    + [{**t, "kind": "bg"} for t in ct["tesserae"]]
                    + [{**cy, "kind": "cycle"} for cy in ct["cycles"]]
                    + [{"support": s, "kind": "connectivity"}
                       for s in ct["connectivity_segments"]])
                v, ch = soundness_check(p, eps, classes, n_samples=16)
                viol += v
                checks += ch
        out["H_C1_violations"] += viol
        out["H_C1_checks"] += checks
        if viol:
            out["HALT"] = f"H-C1 UNSOUND on CHASE/{tname}: {viol}"
            (HERE / "results_chase.json").write_text(json.dumps(out, indent=1))
            raise SystemExit(out["HALT"])
        print(f"[{tname}] H-C1 PASS: 0/{checks}", flush=True)

        ue = float(np.median([useful_eps(p) for p in pmaps]))
        eps_u = min(EPS_SWEEP, key=lambda e: abs(e - ue))
        per = []
        for (name, green, gt, fov), p in zip(data, pmaps):
            dice, iou = dice_iou(p > 0.5, gt, fov)
            ct = certified_topology(p, eps_u, fov, 1.0)
            per.append({"name": name, "dice": dice, "iou": iou,
                        "n_components": ct["n_certified_components"],
                        "conn_seg_frac": ct["certified_connected_seg_frac"],
                        "n_cycles": ct["n_certified_cycles"],
                        "coverage": ct["grout_len_certainly_fg_frac"]})
        dv = [r["dice"] for r in per]
        rho = {q: {"rho": float(spearmanr(dv, [r[q] for r in per])[0]),
                   "p_value": float(spearmanr(dv, [r[q] for r in per])[1])}
               for q in ("n_components", "conn_seg_frac", "n_cycles", "coverage")}
        out["per_transform"][tname] = {
            "useful_eps": ue, "eps_used": eps_u,
            "dice_mean": float(np.mean(dv)), "dice_min": float(np.min(dv)),
            "dice_max": float(np.max(dv)), "spearman_dice_vs": rho,
            "per_image": per}
        print(f"[{tname}] eps_u={eps_u} Dice {np.mean(dv):.3f} | "
              + " ".join(f"rho({q})={rho[q]['rho']:+.2f}" for q in rho),
              flush=True)

    (HERE / "results_chase.json").write_text(json.dumps(out, indent=1))
    print("wrote results_chase.json", flush=True)


if __name__ == "__main__":
    main()
