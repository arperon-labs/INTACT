"""Parallel --from-pmaps re-emit. Same computation and OUTPUT FORMAT as
`run.py --from-pmaps`, parallelized across (crop, eps) cells: the serial run
is ~28h because certified_topology is ~128s/call on the dense mosaic maps
(1200 cycles + 3500 segments/crop) and the box is a 24-core machine idling
at 25%. Two speedups: (1) one certified_topology per cell (serial computes
it twice — once for H-C1, once for the sweep); (2) a process pool.

Deterministic and byte-identical to the serial values: certified_topology
and soundness_check are pure functions of (p, eps) with fixed seeds; cells
are independent. Validated against the committed results.json (first-24
crops) before use.

  python run_parallel.py --n-masks 30 --out results_real_hardened.json --jobs 18
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run  # noqa: E402  (crop_names, load_pmaps, tessera_w, EPS_SWEEP, FLOOR_F)
from topo import certified_topology, soundness_check  # noqa: E402

EPS_SWEEP = run.EPS_SWEEP
FLOOR_F = run.FLOOR_F
N_SAMPLES = 32                      # matches run.py's H-C1
_DATA = None                        # per-worker global: list of (name, p)


def _init(n):
    global _DATA
    _DATA = run.load_pmaps(n)


def _cell(task):
    """One (crop, eps) cell: certified_topology ONCE, then H-C1 soundness +
    every sweep metric run.py collects. Returns scalars only (no masks)."""
    idx, eps = task
    _, p = _DATA[idx]
    p_bin = p > 0.5
    roi = np.ones_like(p_bin)
    tw = run.tessera_w(p_bin)
    ct = certified_topology(p, eps, roi, FLOOR_F * tw)
    classes = ([{**c, "kind": "fg"} for c in ct["components"]]
               + [{**t, "kind": "bg"} for t in ct["tesserae"]]
               + [{**cy, "kind": "cycle"} for cy in ct["cycles"]]
               + [{"support": sup, "kind": "connectivity"}
                  for sup in ct["connectivity_segments"]])
    v, ch = soundness_check(p, eps, classes, n_samples=N_SAMPLES)
    # component coverage proxy (run.py's inner block)
    nlab, lab = cv2.connectedComponents(p_bin.astype(np.uint8), 8)
    cfg = ct["sets"]["CERT_FG"]
    n_p = n_cert = 0
    for i in range(1, nlab):
        comp = lab == i
        if comp.sum() < 15:
            continue
        n_p += 1
        if (comp & cfg).sum() >= 0.5 * comp.sum():
            n_cert += 1
    return idx, eps, {
        "v": int(v), "ch": int(ch), "comp_proxy": n_cert / max(n_p, 1),
        "len": ct["grout_len_certainly_fg_frac"],
        "abstain": ct["abstain_fraction"],
        "n_tess": ct["n_certified_tesserae"],
        "n_comp": ct["n_certified_components"],
        "n_cyc": ct["n_certified_cycles"],
        "cyc_pers": ct["n_certified_cycles_persistence"],
        "conn_len": ct["certified_connected_len_frac"],
        "conn_seg": ct["certified_connected_seg_frac"],
        "sk_px": ct["sk_len_px"], "cert_px": ct["cert_len_px"],
        "nseg": ct["n_segments"], "ncseg": ct["n_certified_segments"]}


def main():
    import multiprocessing as mp
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-masks", type=int, default=30)
    ap.add_argument("--out", default="results_real_hardened.json")
    ap.add_argument("--jobs", type=int, default=max(1, mp.cpu_count() - 4))
    a = ap.parse_args()

    names = run.crop_names(a.n_masks)
    n = len(names)
    data = run.load_pmaps(a.n_masks)      # parent copy, for useful_eps
    tasks = [(idx, eps) for idx in range(n) for eps in EPS_SWEEP]
    print(f"parallel re-emit: {n} crops x {len(EPS_SWEEP)} eps = {len(tasks)} "
          f"cells on {a.jobs} workers", flush=True)

    results = {}
    with mp.Pool(a.jobs, initializer=_init, initargs=(a.n_masks,)) as pool:
        done = 0
        for idx, eps, rec in pool.imap_unordered(_cell, tasks):
            results[(idx, eps)] = rec
            done += 1
            if done % 15 == 0 or done == len(tasks):
                print(f"  {done}/{len(tasks)} cells", flush=True)

    total_viol = sum(r["v"] for r in results.values())
    total_checked = sum(r["ch"] for r in results.values())
    hc1_pass = total_viol == 0
    print(f"H-C1 SOUNDNESS: {total_viol} violations / {total_checked} checks "
          f"-> {'PASS' if hc1_pass else 'UNSOUND — HALT'}", flush=True)
    out_path = HERE / a.out
    if not hc1_pass:
        out_path.write_text(json.dumps(
            {"track": "T-real", "H_C1_soundness_violations": total_viol,
             "H_C1_pass": False, "HALT": True}, indent=1))
        raise SystemExit("H-C1 UNSOUND: HALT.")

    sweep = {}
    for eps in EPS_SWEEP:
        c = [results[(idx, eps)] for idx in range(n)]
        col = lambda k: [x[k] for x in c]
        n_cyc_pers = [x["cyc_pers"] for x in c if x["cyc_pers"] is not None]
        sk_px, cert_px, nseg, ncseg = (col("sk_px"), col("cert_px"),
                                       col("nseg"), col("ncseg"))
        sweep[f"{eps}"] = {
            "grout_len_certainly_fg_frac": float(np.mean(col("len"))),
            "certified_connected_len_frac": float(np.mean(col("conn_len"))),
            "certified_connected_seg_frac": float(np.mean(col("conn_seg"))),
            "component_covg_proxy_frac": float(np.mean(col("comp_proxy"))),
            "abstain_frac": float(np.mean(col("abstain"))),
            "n_certified_components": float(np.mean(col("n_comp"))),
            "n_certified_tessera_cores": float(np.mean(col("n_tess"))),
            "n_certified_cycles_enclosure": float(np.mean(col("n_cyc"))),
            "n_certified_cycles_persistence": (float(np.mean(n_cyc_pers))
                                               if n_cyc_pers else None),
            "skeleton_len_px_mean": float(np.mean(sk_px)),
            "certified_len_px_mean": float(np.mean(cert_px)),
            "skeleton_len_px_total": int(np.sum(sk_px)),
            "certified_len_px_total": int(np.sum(cert_px)),
            "n_segments_mean": float(np.mean(nseg)),
            "n_certified_segments_mean": float(np.mean(ncseg)),
            "per_crop": {
                "coverage": [float(x) for x in col("len")],
                "conn_len_frac": [float(x) for x in col("conn_len")],
                "conn_seg_frac": [float(x) for x in col("conn_seg")],
                "abstain": [float(x) for x in col("abstain")],
                "n_components": [float(x) for x in col("n_comp")],
                "n_tessera_cores": [float(x) for x in col("n_tess")],
                "n_cycles_enclosure": [float(x) for x in col("n_cyc")],
                "n_cycles_persistence": [float(x) for x in n_cyc_pers],
                "skeleton_len_px": [int(x) for x in sk_px],
                "certified_len_px": [int(x) for x in cert_px],
                "n_segments": [int(x) for x in nseg],
                "n_certified_segments": [int(x) for x in ncseg]}}
        print(f"eps={eps}: cover-len={sweep[f'{eps}']['grout_len_certainly_fg_frac']:.3f} "
              f"conn-len={sweep[f'{eps}']['certified_connected_len_frac']:.3f} "
              f"n_cyc_encl={sweep[f'{eps}']['n_certified_cycles_enclosure']:.1f} "
              f"abstain={sweep[f'{eps}']['abstain_frac']:.3f}", flush=True)

    ue = float(np.median([run.useful_eps(p) for _, p in data]))
    eps_u = min(EPS_SWEEP, key=lambda e: abs(e - ue))
    su = sweep[f"{eps_u}"]
    hc2 = bool(su["grout_len_certainly_fg_frac"] >= 0.5
               and su["n_certified_components"] >= 1)
    kill = all(v["grout_len_certainly_fg_frac"] < 0.10 for v in sweep.values())
    lens = [sweep[f"{e}"]["grout_len_certainly_fg_frac"] for e in EPS_SWEEP]
    hc3 = all(lens[i] >= lens[i + 1] - 1e-9 for i in range(len(lens) - 1))
    out = {"track": "T-real", "PROVISIONAL": False,
           "n_maps": n, "names": names,
           "H_C1_soundness_violations": 0, "H_C1_pass": True,
           "H_C1_checks": total_checked, "sweep": sweep,
           "useful_eps_calibrated": ue, "useful_eps_used": eps_u,
           "H_C2_nonvacuity_at_useful_eps": {
               **{k: v for k, v in su.items() if k != "per_crop"}, "pass": hc2},
           "H_C3_nesting_monotone_pass": hc3, "KILL_abstain_floods": kill}
    out_path.write_text(json.dumps(out, indent=1))
    print(f"wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
