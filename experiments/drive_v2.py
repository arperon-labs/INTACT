"""DRIVE V2 decoupling study (registered 2026-07-16, REGISTRY
'DRIVE V2 REGISTRATION' — committed before this file).

Model-free p (classical Frangi vesselness, no training/checkpoint) on 20
GT-annotated DRIVE training images; the INTACT harness certifies its
topology; we show per-image pixel accuracy (Dice/IoU vs GT) and certified
topology quantities are INDEPENDENT (Spearman rho), with the registered
honesty clause: rho is reported whatever it is. H-C1 soundness re-run on
the domain gates everything.

  python drive_v2.py    # CPU-only; writes results_drive.json
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion
from scipy.stats import spearmanr
from skimage.filters import frangi, threshold_otsu

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]                      # repository root
# Optional datasets that are NOT shipped. Repo-relative by default;
# point INTACT_EXTERNAL_DATA at your own tree to use data held elsewhere.
EXTERNAL = Path(os.environ.get("INTACT_EXTERNAL_DATA",
                               ROOT / "external-data"))
sys.path.insert(0, str(HERE))
from sandwich import cert_sets, useful_eps  # noqa: E402
from topo import certified_topology, soundness_check  # noqa: E402

DRIVE = (EXTERNAL / "data" / "external"
         / "drive" / "DRIVE" / "training")
EPS_SWEEP = [0.02, 0.05, 0.1, 0.15, 0.25, 0.4]
FOV_ERODE = 6
K = 12.0
TRANSFORMS = {                                    # registered: cbrt PRIMARY
    "cbrt": lambda x: np.cbrt(x),
    "sqrt": lambda x: np.sqrt(x),
    "log": lambda x: np.log1p(x / (x[x > 0].mean() + 1e-12))
    if (x > 0).any() else x,
}


def load(p):
    return np.asarray(Image.open(p))


def frangi_p(green, fov, transform):
    """Registered protocol P: green-channel Frangi, FOV-eroded, skew-corrected
    Otsu-logistic. p := 0 outside FOV."""
    resp = np.where(fov, frangi(green, sigmas=range(1, 6), black_ridges=True),
                    0.0).astype(np.float32)
    r = transform(resp)
    sel = r[fov & (resp > 1e-7)]
    t = threshold_otsu(sel) if sel.size else 1.0
    p = (1.0 / (1.0 + np.exp(-K * (r - t)))).astype(np.float32)
    return np.where(fov, p, 0.0).astype(np.float32)


def dice_iou(pred, gt, fov):
    pred, gt = pred & fov, gt & fov
    inter = float((pred & gt).sum())
    dice = 2 * inter / (pred.sum() + gt.sum() + 1e-9)
    iou = inter / ((pred | gt).sum() + 1e-9)
    return float(dice), float(iou)


def main():
    imgs = sorted(DRIVE.glob("images/*.tif"))
    assert len(imgs) == 20, f"expected 20 DRIVE training images, got {len(imgs)}"
    names = [ip.stem.split("_")[0] for ip in imgs]
    data = []                                     # (name, green, gt, fov)
    for ip, n in zip(imgs, names):
        green = load(ip)[..., 1].astype(np.float32) / 255.0
        gt = load(DRIVE / "1st_manual" / f"{n}_manual1.gif") > 0
        fov = binary_erosion(load(DRIVE / "mask" / f"{n}_training_mask.gif") > 0,
                             iterations=FOV_ERODE)
        data.append((n, green, gt, fov))

    out = {"transforms": list(TRANSFORMS), "primary": "cbrt",
           "eps_sweep": EPS_SWEEP, "fov_erode": FOV_ERODE,
           "H_C1_violations": 0, "H_C1_checks": 0, "per_transform": {}}

    for tname, tf in TRANSFORMS.items():
        pmaps = {n: frangi_p(g, f, tf) for n, g, f in
                 [(n, g, f) for n, g, _, f in data]}
        # ---- H-C1 soundness gate on the domain (all eps) ----------------
        viol = checks = 0
        for n, green, gt, fov in data:
            p = pmaps[n]
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
            out["HALT"] = f"H-C1 UNSOUND on DRIVE/{tname}: {viol} violations"
            (HERE / "results_drive.json").write_text(json.dumps(out, indent=1))
            raise SystemExit(out["HALT"])
        print(f"[{tname}] H-C1 PASS: 0/{checks} violations", flush=True)

        # ---- calibration eps (cohort), then per-image metrics -----------
        ue = float(np.median([useful_eps(pmaps[n]) for n in names]))
        eps_u = min(EPS_SWEEP, key=lambda e: abs(e - ue))
        per_img = []
        for n, green, gt, fov in data:
            p = pmaps[n]
            dice, iou = dice_iou(p > 0.5, gt, fov)
            ct = certified_topology(p, eps_u, fov, 1.0)
            per_img.append({
                "name": n, "dice": dice, "iou": iou,
                "n_components": ct["n_certified_components"],
                "conn_seg_frac": ct["certified_connected_seg_frac"],
                "n_cycles": ct["n_certified_cycles"],
                "coverage": ct["grout_len_certainly_fg_frac"],
                "n_segments": ct["n_segments"],
                "n_cert_segments": ct["n_certified_segments"]})
        # ---- Spearman rho: Dice vs each certified quantity (HONEST) ------
        dice_v = [r["dice"] for r in per_img]
        rho = {}
        for q in ("n_components", "conn_seg_frac", "n_cycles", "coverage"):
            qs = [r[q] for r in per_img]
            rr, pp = spearmanr(dice_v, qs)
            rho[q] = {"rho": float(rr), "p_value": float(pp)}
        out["per_transform"][tname] = {
            "useful_eps": ue, "eps_used": eps_u,
            "dice_mean": float(np.mean(dice_v)),
            "dice_min": float(np.min(dice_v)),
            "dice_max": float(np.max(dice_v)),
            "spearman_dice_vs": rho, "per_image": per_img}
        print(f"[{tname}] eps_u={eps_u} Dice {np.mean(dice_v):.3f} "
              f"[{np.min(dice_v):.3f},{np.max(dice_v):.3f}] | "
              + " ".join(f"rho({q})={rho[q]['rho']:+.2f}" for q in rho),
              flush=True)

    (HERE / "results_drive.json").write_text(json.dumps(out, indent=1))
    print("wrote results_drive.json", flush=True)


if __name__ == "__main__":
    main()
