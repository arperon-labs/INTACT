"""S4 compute-disclosure: clean uncontended per-unit runtimes for Appendix E.
certified_topology + soundness on one representative mosaic crop and one
retinal-vessel image, at each track's soundness setting. Measured 2026-07-17
on the paper's hardware (RTX 4080 / 64 GB / 24 threads), one core, idle box:

  mosaic (crop_byzantine_00) certify  1.0s | soundness(n=32)  49.9s | cell  51.0s
  vessel cbrt (n=16 DRIVE)   certify 13.6s | soundness(n=16)  90.8s | cell 104.4s
  vessel cbrt (n=4 CHASE)    certify 13.4s | soundness(n=4)   22.4s | cell  35.8s

Run:  python runtime_s4.py
"""
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run
import chase_parallel as cp
from topo import certified_topology, soundness_check


def _classes(ct):
    return ([{**c, "kind": "fg"} for c in ct["components"]]
            + [{**t, "kind": "bg"} for t in ct["tesserae"]]
            + [{**cy, "kind": "cycle"} for cy in ct["cycles"]]
            + [{"support": s, "kind": "connectivity"}
               for s in ct["connectivity_segments"]])


def bench(label, p, roi, floor, eps, n_samples):
    t = time.time(); ct = certified_topology(p, eps, roi, floor)
    t_ct = time.time() - t
    cls = _classes(ct)
    t = time.time(); v, ch = soundness_check(p, eps, cls, n_samples=n_samples)
    t_s = time.time() - t
    print(f"{label:28s} certify {t_ct:6.1f}s | soundness(n={n_samples}) "
          f"{t_s:6.1f}s | cell {t_ct + t_s:6.1f}s | classes {len(cls)} viol {v}",
          flush=True)


def main():
    name, p = run.load_pmaps(1)[0]
    pb = p > 0.5
    bench(f"mosaic {name}", p, np.ones_like(pb),
          0.5 * run.tessera_w(pb), 0.1, 32)
    _, green, gt, fov = cp.load_data(1)[0]
    pv = cp.cv.frangi_p(green, fov, cp.cv.TRANSFORMS["cbrt"])
    bench("vessel cbrt (n=16 DRIVE)", pv, fov, 1.0, 0.25, 16)
    bench("vessel cbrt (n=4 CHASE)", pv, fov, 1.0, 0.25, 4)


if __name__ == "__main__":
    main()
