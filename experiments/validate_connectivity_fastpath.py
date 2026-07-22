"""Gate for the near-linear connectivity rewrite (2026-07-17): prove it is
byte-identical to the O(n^2) reference AND reproduces the committed mosaic
connectivity numbers. Exit 0 = safe to use.

  A) segment SET (new fast) == segment SET (_segments_ref) on mosaic maps
     and a dense CHASE crop (the case the old quadratic loop choked on).
  B) connectivity_certificate(new) reproduces results_real_hardened.json's
     per-crop conn_seg_frac / conn_len_frac / n_segments / n_certified_segments.
"""
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import connectivity as C
import run
from sandwich import cert_sets


def sig_set(masks):
    """Order-independent signature of a set of boolean supports."""
    return sorted(hash(np.flatnonzero(m).tobytes()) for m in masks)


def new_masks(sk):
    out = []
    for sl, loc in C.segments(sk):
        full = np.zeros_like(sk)
        full[sl] = loc
        out.append(full)
    return out


def check_equiv(name, p, roi):
    sk = C.skeleton((p > 0.5) & roi)
    ref = C._segments_ref(sk)
    new = new_masks(sk)
    ok = (len(ref) == len(new)) and (sig_set(ref) == sig_set(new))
    print(f"  [{'OK' if ok else 'FAIL'}] equiv {name}: "
          f"sk_len={int(sk.sum())} n_seg ref={len(ref)} new={len(new)}")
    return ok


def cert_ref(p, cert_fg, roi):
    """Reference connectivity_certificate using _segments_ref (full masks)."""
    sk = C.skeleton((p > 0.5) & roi)
    sk_len = int(sk.sum())
    if sk_len == 0:
        return dict(certified_seg_frac=1.0, certified_len_frac=1.0,
                    n_segments=0, n_certified_segments=0)
    segs = C._segments_ref(sk)
    n_cert = cert_len = tot = 0
    for s in segs:
        L = int(s.sum()); tot += L
        if cert_fg[s].all():
            n_cert += 1; cert_len += L
    return dict(certified_seg_frac=n_cert / len(segs) if segs else 1.0,
                certified_len_frac=cert_len / tot if tot else 1.0,
                n_segments=len(segs), n_certified_segments=n_cert)


def load_chase_crop(sz=300):
    """A dense CHASE sub-window: exercises the quadratic case the ref chokes
    on at full size but stays cheap when cropped."""
    import chase_parallel as cp
    name, green, gt, fov = cp.load_data(1)[0]
    p = cp.cv.frangi_p(green, fov, cp.cv.TRANSFORMS["cbrt"])
    y, x = 400, 400
    return p[y:y + sz, x:x + sz].copy(), fov[y:y + sz, x:x + sz].copy()


def main():
    fails = 0
    print("A) segment-set equivalence (new fast == _segments_ref):")
    data = run.load_pmaps(3)                     # 3 mosaic p-maps
    for name, p in data:
        roi = np.ones_like(p > 0.5)
        for eps in (0.1, 0.4):
            s = cert_sets(p, eps, True)
            # equivalence is a property of the skeleton, eps-independent, but
            # run at two eps anyway to be safe with roi handling
            if not check_equiv(f"{name}@{eps}", p, roi):
                fails += 1
                break
    cp_p, cp_fov = load_chase_crop()
    if not check_equiv("chase_crop_cbrt@0.1(dense)", cp_p, cp_fov):
        fails += 1

    print("B) committed-results regression (results_real_hardened.json):")
    real = json.loads((HERE / "results_real_hardened.json").read_text())
    EPS = ["0.02", "0.05", "0.1", "0.15", "0.25", "0.4"]
    for idx, (name, p) in enumerate(data):        # first 3 crops
        roi = np.ones_like(p > 0.5)
        for e in EPS:
            s = cert_sets(p, float(e), True)
            got = C.connectivity_certificate(p, s["CERT_FG"], roi)
            pc = real["sweep"][e]["per_crop"]
            exp = dict(certified_seg_frac=pc["conn_seg_frac"][idx],
                       certified_len_frac=pc["conn_len_frac"][idx],
                       n_segments=pc["n_segments"][idx],
                       n_certified_segments=pc["n_certified_segments"][idx])
            ok = (got["n_segments"] == exp["n_segments"]
                  and got["n_certified_segments"] == exp["n_certified_segments"]
                  and abs(got["certified_seg_frac"] - exp["certified_seg_frac"]) < 1e-9
                  and abs(got["certified_len_frac"] - exp["certified_len_frac"]) < 1e-9)
            if not ok:
                fails += 1
                print(f"  [FAIL] {name}@{e}: got {got} exp {exp}")
        print(f"  [{'OK' if not fails else '...'}] {name}: all 6 eps match committed")

    print("\n" + ("ALL CHECKS PASS — fast path is byte-identical + reproduces "
                  "committed." if not fails else f"{fails} FAILURES"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
