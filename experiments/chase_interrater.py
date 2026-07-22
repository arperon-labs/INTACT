"""CHASE_DB1 inter-rater eps (registered 2026-07-16, REGISTRY
'CHASE_DB1 REGISTRATION' — committed before this number). The V3 medical
protocol INSTANTIATED: eps calibrated from where two human observers
disagree, not invented.

Registered rule (fixes the degenerate binary-percentile naive rule):
  D_i   = obs1_i XOR obs2_i  within the eroded FOV
  eps   = median_i  median_{x in D_i} |frangi_p_i(x) - 1/2|
i.e. the typical model-margin uncertainty exactly where the annotators
disagree — the score-map band that renders humanly-disputed pixels POSSIBLE.
Reported as a marked point on the swept grid, with the two-observer
lower-bound caveat. CPU-only, no gudhi.

  python chase_interrater.py    # writes results_chase_interrater.json
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
from skimage.filters import frangi, threshold_otsu

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ZIP = (EXTERNAL / "data" / "external"
       / "chasedb1" / "chasedb1.zip")
EPS_GRID = [0.02, 0.05, 0.1, 0.15, 0.25, 0.4]
BASE = "chase/training/training"


def _bin2d(a):
    if a.ndim > 2:
        a = a[..., 0]
    return a > (a.max() / 2)


def frangi_p(green, fov):
    """Registered protocol P (cbrt-primary), identical to the DRIVE run."""
    resp = np.where(fov, frangi(green, sigmas=range(1, 6), black_ridges=True),
                    0.0).astype(np.float32)
    r = np.cbrt(resp)
    sel = r[fov & (resp > 1e-7)]
    t = threshold_otsu(sel) if sel.size else 1.0
    return np.where(fov, 1 / (1 + np.exp(-12.0 * (r - t))), 0.0).astype(np.float32)


def main():
    z = zipfile.ZipFile(ZIP)
    load = lambda n: np.asarray(Image.open(io.BytesIO(z.read(n))))
    g = lambda sub: sorted(n for n in z.namelist()
                           if n.startswith(f"{BASE}/{sub}/") and not n.endswith("/"))
    imgs, m1, m2, msk = (g("images"), g("1st_manual"), g("2nd_manual"), g("mask"))
    imgs = [n for n in imgs if n.endswith(".tif")]
    assert len(imgs) == len(m1) == len(m2) == len(msk) == 20

    per, dices = [], []
    for i in range(len(imgs)):
        green = load(imgs[i])[..., 1].astype(np.float32) / 255.0
        fov = binary_erosion(_bin2d(load(msk[i])), iterations=6)
        o1, o2 = _bin2d(load(m1[i])) & fov, _bin2d(load(m2[i])) & fov
        D = (o1 ^ o2) & fov
        dices.append(float(2 * (o1 & o2).sum() / (o1.sum() + o2.sum() + 1e-9)))
        margin = np.abs(frangi_p(green, fov) - 0.5)[D]
        per.append(float(np.median(margin)) if margin.size else float("nan"))

    per = np.array(per)
    eps_inter = float(np.median(per))
    snap = min(EPS_GRID, key=lambda e: abs(e - eps_inter))
    out = {"rule": "median_i median_{x in obs1 XOR obs2} |frangi_p - 0.5|",
           "n_images": len(imgs), "eps_inter": eps_inter,
           "eps_inter_snapped": snap,
           "per_image_margin": per.tolist(),
           "interobserver_dice_mean": float(np.mean(dices)),
           "interobserver_dice_range": [float(min(dices)), float(max(dices))]}
    (HERE / "results_chase_interrater.json").write_text(json.dumps(out, indent=1))
    print(f"inter-observer Dice {np.mean(dices):.3f} "
          f"[{min(dices):.3f},{max(dices):.3f}] | eps_inter {eps_inter:.3f} "
          f"-> grid {snap}")


if __name__ == "__main__":
    main()
