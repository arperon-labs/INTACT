"""TOPOCERT certified topology from the sandwich. gudhi-free: beta0 image-
persistence is exact via connected components (superset preserves
connectivity); beta1 via the campaign's Euler-characteristic method
(topo_metrics). ROI + physical scale floor applied. The soundness check is
the correctness gate (H-C1), not a metric.
"""
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from skimage.morphology import skeletonize

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]                      # repository root
# Optional datasets that are NOT shipped (source crops, DRIVE/CHASE
# archives, model checkpoints). Repo-relative by default; point
# INTACT_EXTERNAL_DATA at your own tree to use data held elsewhere.
EXTERNAL = Path(os.environ.get("INTACT_EXTERNAL_DATA",
                               ROOT / "external-data"))
sys.path.insert(0, str(EXTERNAL))
sys.path.insert(0, str(ROOT / "h2_domain"))
from sandwich import cert_sets, reachable_fg  # noqa: E402
from persistence import certified_cycle_count, HAVE_GUDHI  # noqa: E402
from connectivity import connectivity_certificate  # noqa: E402

try:
    from domain import region_below_floor, region_outside_roi
except Exception:
    def region_below_floor(reg, fl):
        r = max(1, round(fl / 2))
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        return not cv2.morphologyEx(reg.astype(np.uint8), cv2.MORPH_OPEN, k).any()

    def region_outside_roi(reg, roi):
        return float(roi[reg].mean()) < 0.5 if reg.any() else True

MIN_AREA = 15


def _components(field, conn, roi, floor_px):
    n, lbl = cv2.connectedComponents(field.astype(np.uint8), connectivity=conn)
    out = []
    for i in range(1, n):
        reg = lbl == i
        if reg.sum() < MIN_AREA or region_outside_roi(reg, roi) \
                or region_below_floor(reg, floor_px):
            continue
        ys, xs = np.nonzero(reg)
        out.append({"support": reg, "area": int(reg.sum()),
                    "bbox": [int(ys.min()), int(xs.min()),
                             int(ys.max()), int(xs.max())]})
    return out


def certified_cycles(cert_fg, cert_bg, roi, floor_px):
    """SOUND certified 1-cycles (image-persistence, corrected after
    adversarial review 2026-07-12): a robust hole requires an UNFILLABLE
    interior. betti1(CERT_FG) is UNSOUND — H1 is not monotone under
    foreground growth, so a CERT_FG ring around POSSIBLE pixels can be
    filled (interior set to fg within eps), dropping the cycle. A cycle
    persists in EVERY reachable mask iff its enclosed region is CERT_BG
    (guaranteed background) walled by CERT_FG (guaranteed foreground): the
    core cannot leak out (only path is through the always-fg wall) and
    cannot be filled (it is always background). So certified cycles =
    CERT_BG components not reachable from the image border through the
    can-be-background region ~CERT_FG."""
    canbg = (~cert_fg).astype(np.uint8)                 # POSSIBLE | CERT_BG
    n, lbl = cv2.connectedComponents(canbg, connectivity=4)
    border = np.unique(np.concatenate([lbl[0], lbl[-1], lbl[:, 0], lbl[:, -1]]))
    outside = np.isin(lbl, list(set(border.tolist()) - {0}))
    enclosed = cert_bg & ~outside                        # walled by CERT_FG
    return _components(enclosed, 4, roi, floor_px)


def certified_topology(p, eps, roi, floor_px, pedantic=True):
    s = cert_sets(p, eps, pedantic)
    comps = _components(s["CERT_FG"], 8, roi, floor_px)        # grout comps
    tess = _components(s["CERT_BG"], 4, roi, floor_px)         # tessera cores
    cycles = certified_cycles(s["CERT_FG"], s["CERT_BG"], roi, floor_px)
    n_cycles = len(cycles)                                    # enclosure proxy
    cyc_pers, pers_avail = certified_cycle_count(              # 1a: true persistence
        s["CERT_FG"], s["CERT_BG"])
    conn = connectivity_certificate(p, s["CERT_FG"], roi)     # 1b: connectivity
    total = float(roi.sum()) if roi.any() else float(p.size)
    abstain = float((s["POSSIBLE"] & roi).sum()) / total
    # certified grout-line length fraction (skeleton of p_bin that lies in
    # CERT_FG -> COVERAGE, not connectivity; see connectivity.py for the
    # honest connectivity number)
    p_bin = p > 0.5
    sk = skeletonize(p_bin & roi)
    sk_len = float(sk.sum())
    cert_len = float((sk & s["CERT_FG"]).sum())
    return {"sets": s, "components": comps, "tesserae": tess,
            "cycles": cycles,
            "n_certified_components": len(comps),
            "n_certified_tesserae": len(tess),
            "n_certified_cycles": n_cycles,                   # enclosure (proxy)
            "n_certified_cycles_persistence": cyc_pers,       # 1a gudhi (None if absent)
            "persistence_available": pers_avail,
            "abstain_fraction": abstain,
            "grout_len_certainly_fg_frac": cert_len / sk_len if sk_len else 1.0,
            "sk_len_px": int(sk_len),                         # absolute companions
            "cert_len_px": int(cert_len),
            "certified_connected_seg_frac": conn["certified_seg_frac"],
            "certified_connected_len_frac": conn["certified_len_frac"],
            "n_segments": conn["n_segments"],
            "n_certified_segments": conn["n_certified_segments"],
            "connectivity_segments": conn["segments"]}


def soundness_check(p, eps, classes, n_samples=64, seed=0, pedantic=True):
    """H-C1 teeth: sample reachable masks M (CERT_FG subset-of M subset-of
    ~CERT_BG) via random + adversarial choice fields; verify EVERY claimed
    class holds in EVERY M. FG class = its support stays fully-fg AND
    connected in M; BG(tessera) class = its support stays fully background.
    Returns (violations, n_checked). A genuine certificate (support in
    CERT_FG / CERT_BG) yields 0 by construction; a planted-unsound one
    (support intruding into POSSIBLE) is caught."""
    s = cert_sets(p, eps, pedantic)
    rng = np.random.default_rng(seed)
    viol = 0
    checked = 0
    for k in range(n_samples):
        if k == 0:
            choice = np.zeros_like(s["POSSIBLE"])          # adversary: all bg
        elif k == 1:
            choice = np.ones_like(s["POSSIBLE"])           # all fg
        else:
            choice = rng.random(s["POSSIBLE"].shape) < rng.uniform(0.1, 0.9)
        M = reachable_fg(s, choice)                        # foreground mask
        for c in classes:
            checked += 1
            sup = c["support"]
            kind = c.get("kind", "fg")
            if kind in ("fg", "connectivity"):
                # fg component OR certified-connected segment: support must
                # stay fully foreground AND connected in every reachable M.
                # Worst case for disconnection = all-POSSIBLE→bg (k==0).
                if not M[sup].all():                       # a support px went bg
                    viol += 1; continue
                lab_n, lab = cv2.connectedComponents(
                    (M & _bbox_mask(sup)).astype(np.uint8), 8)
                if len(np.unique(lab[sup])) > 1:           # split -> broken
                    viol += 1
            elif kind == "bg":                             # tessera core
                if M[sup].any():                           # a core px went fg
                    viol += 1
            else:                                          # kind == 'cycle'
                if M[sup].any():                           # core must stay bg
                    viol += 1; continue
                # the hole must NOT connect to the border background of M
                bg = (~M).astype(np.uint8)
                nb, lblb = cv2.connectedComponents(bg, connectivity=4)
                border = set(np.concatenate([lblb[0], lblb[-1], lblb[:, 0],
                                             lblb[:, -1]]).tolist()) - {0}
                if len(set(lblb[sup].tolist()) & border):  # hole leaked out
                    viol += 1
    return viol, checked


def _bbox_mask(sup):
    ys, xs = np.nonzero(sup)
    m = np.zeros_like(sup)
    m[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = True
    return m
