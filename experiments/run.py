"""TOPOCERT experiment: is the certified band non-vacuous at useful eps?
SOUNDNESS (H-C1) is checked and reported FIRST (correctness gate). Then
non-vacuity (H-C2) + nesting (H-C3), all ABSOLUTE metrics.

  python run.py               # T-toy (simulated p) — authoritative now
  python run.py --gpu-real    # T-real (frozen GROUT p) — needs the model
Default (no flag) prints 'PROVISIONAL: simulated p' and uses the toy track.
"""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]                      # repository root
# Optional datasets that are NOT shipped (source crops, DRIVE/CHASE
# archives, model checkpoints). Repo-relative by default; point
# INTACT_EXTERNAL_DATA at your own tree to use data held elsewhere.
EXTERNAL = Path(os.environ.get("INTACT_EXTERNAL_DATA",
                               ROOT / "external-data"))
sys.path.insert(0, str(EXTERNAL))
sys.path.insert(0, str(HERE))
from sandwich import useful_eps  # noqa: E402
from topo import certified_topology, soundness_check  # noqa: E402

EPS_SWEEP = [0.02, 0.05, 0.1, 0.15, 0.25, 0.4]
N_MASKS = 24
FLOOR_F = 0.5


def toy_masks(n, seed=0):
    """Clean generator masks + simulated p (blur GT + calibrated noise).
    Analytic topology GT = the mask itself. Returns (name, p) pairs."""
    from grout_topo.generator import generate_mosaic
    rng = np.random.default_rng(seed)
    tmp = Path(tempfile.mkdtemp())
    out = []
    for i in range(n):
        for s in ("masks", "images", "topo"):
            import shutil
            shutil.rmtree(tmp / s, ignore_errors=True)
        generate_mosaic(i, str(tmp), img_size=256)
        mp = sorted((tmp / "masks").glob("*.png"))
        if not mp:
            continue
        m = cv2.imread(str(mp[-1]), cv2.IMREAD_GRAYSCALE) > 127
        p = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.3)
        p = np.clip(p + rng.normal(0, 0.07, p.shape).astype(np.float32), 0, 1)
        out.append((f"toy_{i:02d}", p))
    return out


def real_masks(n):
    """T-real: frozen GROUT p on real crops (GPU). Only via --gpu-real.
    Returns (crop_name, p) pairs."""
    from grout_topo.core import device_auto, infer_patch_logits, load_model
    from tools.prepare_real_crops import imread_unicode
    crops = sorted((EXTERNAL / "data" / "realset" / "crops").glob("*.png"))[:n]
    dev = device_auto()
    model = load_model(EXTERNAL / "checkpoints" /
                       "grout_b3_zeroshot_v1.pth", dev)
    out = []
    for c in crops:
        img = cv2.cvtColor(imread_unicode(c), cv2.COLOR_BGR2RGB)
        p = 1 / (1 + np.exp(-infer_patch_logits(model, img, dev)))
        out.append((c.stem, p.astype(np.float32)))
    return out


def crop_names(n):
    """The first n real-crop stems, in the exact order real_masks() uses.
    No GPU/model — just the crop-directory listing.

    Falls back to the committed p_maps/ when the source crops are absent:
    this release ships the frozen score maps so the real track reproduces
    without the model checkpoint. P-map files are named <stem>.npy, so the
    stems and their sort order are identical either way."""
    crops = sorted((EXTERNAL / "data" / "realset" / "crops").glob("*.png"))
    if crops:
        return [c.stem for c in crops[:n]]
    return [f.stem for f in sorted((HERE / "p_maps").glob("*.npy"))[:n]]


def _load_pmaps_from(pdir, names):
    """Load [(name, p)] from pdir/{name}.npy in the requested order, raising
    SystemExit if any is missing (a silent under-run would fake a smaller
    study). Testable core of load_pmaps()."""
    pdir = Path(pdir)
    out, missing = [], []
    for name in names:
        f = pdir / f"{name}.npy"
        if f.exists():
            out.append((name, np.load(f).astype(np.float32)))
        else:
            missing.append(name)
    if missing:
        raise SystemExit(
            f"--from-pmaps: {len(missing)} p-map(s) missing from {pdir} "
            f"(e.g. {missing[0]}.npy). Run once without --from-pmaps "
            f"(with --save-pmaps) to generate them.")
    return out


def load_pmaps(n):
    """T-real crash-recovery: load the frozen p maps saved by an earlier
    --gpu-real --save-pmaps run instead of re-inferring on the GPU. The p
    values are identical, so H-C1 / sweep / JSON are byte-identical to a fresh
    run — but this path needs no model, no torch and no GPU, so a killed run
    resumes on CPU alone (immune to the GPU-contention kill)."""
    names = crop_names(n)
    if not names:
        raise SystemExit("--from-pmaps: no real crops found under "
                         f"{EXTERNAL / 'data' / 'realset' / 'crops'}")
    data = _load_pmaps_from(HERE / "p_maps", names)
    print(f"loaded {len(data)} p maps from p_maps/ (CPU-only resume)",
          flush=True)
    return data


def tessera_w(p_bin):
    tess = (~p_bin).astype(np.uint8)
    n, _, st, _ = cv2.connectedComponentsWithStats(tess, 4)
    a = [st[i, cv2.CC_STAT_AREA] for i in range(1, n)
         if st[i, cv2.CC_STAT_AREA] >= 9]
    return float(np.sqrt(np.median(a))) if a else 6.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu-real", action="store_true")
    ap.add_argument("--from-pmaps", action="store_true",
                    help="CPU-only crash-recovery: load frozen T-real p from "
                         "p_maps/*.npy instead of GPU inference (no model, no "
                         "torch); deterministic, identical to a --gpu-real run")
    ap.add_argument("--n-masks", type=int, default=N_MASKS,
                    help="crops/maps to process (re-emit registration: 30)")
    ap.add_argument("--out", default="results.json",
                    help="output JSON filename (re-emit: "
                         "results_real_hardened.json; never overwrite the "
                         "committed results.json with a new run)")
    ap.add_argument("--save-pmaps", action="store_true",
                    help="dump per-crop p maps to p_maps/*.npy (item 7)")
    a = ap.parse_args()
    out_path = HERE / a.out
    # crash-recovery idempotency: a completed resume target is a no-op, so a
    # watchdog relaunch after success neither recomputes nor clobbers it.
    if a.from_pmaps and out_path.exists():
        try:
            prev = json.loads(out_path.read_text())
            if (prev.get("H_C1_pass") is True
                    and set(prev.get("sweep", {}))
                    == {f"{e}" for e in EPS_SWEEP}):
                print(f"--from-pmaps: {a.out} already complete (H-C1 pass, "
                      f"{len(EPS_SWEEP)}-eps sweep); nothing to do.", flush=True)
                return
        except (ValueError, OSError):
            pass                                   # partial/malformed -> redo
    if a.from_pmaps:
        print("T-real: resuming from saved p maps (CPU-only, no GPU)",
              flush=True)
        data = load_pmaps(a.n_masks); track = "T-real"; prov = False
    elif a.gpu_real:
        print("T-real: frozen GROUT p (real numbers)", flush=True)
        data = real_masks(a.n_masks); track = "T-real"; prov = False
    else:
        print("PROVISIONAL: simulated p (T-toy authoritative; T-real needs "
              "the frozen model, run with --gpu-real)",
              flush=True)
        data = toy_masks(a.n_masks); track = "T-toy"; prov = True
    if a.save_pmaps and not a.from_pmaps:          # already on disk if resuming
        (HERE / "p_maps").mkdir(exist_ok=True)
        for name, p in data:
            np.save(HERE / "p_maps" / f"{name}.npy", p)
        print(f"saved {len(data)} p maps to p_maps/", flush=True)

    # ---- H-C1 SOUNDNESS FIRST (the gate) --------------------------------
    total_viol = total_checked = 0
    for m, p in data:
        p_bin = p > 0.5
        roi = np.ones_like(p_bin)
        tw = tessera_w(p_bin)
        for eps in EPS_SWEEP:
            ct = certified_topology(p, eps, roi, FLOOR_F * tw)
            classes = ([{**c, "kind": "fg"} for c in ct["components"]]
                       + [{**t, "kind": "bg"} for t in ct["tesserae"]]
                       + [{**cy, "kind": "cycle"} for cy in ct["cycles"]]
                       + [{"support": sup, "kind": "connectivity"}   # 1b
                          for sup in ct["connectivity_segments"]])
            v, ch = soundness_check(p, eps, classes, n_samples=32)
            total_viol += v; total_checked += ch
    hc1_pass = total_viol == 0
    print(f"H-C1 SOUNDNESS: {total_viol} violations / {total_checked} checks "
          f"-> {'PASS' if hc1_pass else 'UNSOUND — HALT'}", flush=True)
    if not hc1_pass:
        out_path.write_text(json.dumps(
            {"track": track, "H_C1_soundness_violations": total_viol,
             "H_C1_pass": False, "HALT": True}, indent=1))
        raise SystemExit("H-C1 UNSOUND: certificate broke. HALT (no non-"
                         "vacuity number reported).")

    # ---- sweep metrics (absolute) ---------------------------------------
    sweep = {}
    for eps in EPS_SWEEP:
        comp_fracs, len_fracs, abstains, n_tess = [], [], [], []
        n_comp, n_cyc, n_cyc_pers, conn_len, conn_seg = [], [], [], [], []
        sk_px, cert_px, nseg, ncseg = [], [], [], []       # absolutes (re-emit)
        for m, p in data:
            p_bin = p > 0.5
            roi = np.ones_like(p_bin)
            tw = tessera_w(p_bin)
            ct = certified_topology(p, eps, roi, FLOOR_F * tw)
            # fraction of p-foreground grout components that are certified-
            # robust (>=50% of the component's area lies in CERT_FG). Bounded
            # in [0,1] (an earlier fragment-ratio version could exceed 1 at
            # large eps — corrected pre-final; that column was INVALID).
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
            # NOTE (post-review): this is a COVERAGE proxy (p-component >=50%
            # in CERT_FG), NOT a connectivity certificate — a component can be
            # >=50% covered yet pinched through POSSIBLE and split. The genuine
            # connectivity certificate is n_certified_components (CERT_FG's own
            # connected components). Reported as coverage, framed honestly.
            comp_fracs.append(n_cert / max(n_p, 1))
            len_fracs.append(ct["grout_len_certainly_fg_frac"])
            abstains.append(ct["abstain_fraction"])
            n_tess.append(ct["n_certified_tesserae"])
            n_comp.append(ct["n_certified_components"])
            n_cyc.append(ct["n_certified_cycles"])                 # enclosure proxy
            cp = ct["n_certified_cycles_persistence"]             # 1a persistence
            if cp is not None:
                n_cyc_pers.append(cp)
            conn_len.append(ct["certified_connected_len_frac"])  # 1b connectivity
            conn_seg.append(ct["certified_connected_seg_frac"])
            sk_px.append(ct["sk_len_px"])                    # absolute companions
            cert_px.append(ct["cert_len_px"])
            nseg.append(ct["n_segments"])
            ncseg.append(ct["n_certified_segments"])
        sweep[f"{eps}"] = {
            "grout_len_certainly_fg_frac": float(np.mean(len_fracs)),
            "certified_connected_len_frac": float(np.mean(conn_len)),   # 1b (< coverage)
            "certified_connected_seg_frac": float(np.mean(conn_seg)),
            "component_covg_proxy_frac": float(np.mean(comp_fracs)),
            "abstain_frac": float(np.mean(abstains)),
            "n_certified_components": float(np.mean(n_comp)),
            "n_certified_tessera_cores": float(np.mean(n_tess)),
            "n_certified_cycles_enclosure": float(np.mean(n_cyc)),
            "n_certified_cycles_persistence": (float(np.mean(n_cyc_pers))
                                               if n_cyc_pers else None),
            # absolute companions (standing rule; re-emit registration)
            "skeleton_len_px_mean": float(np.mean(sk_px)),
            "certified_len_px_mean": float(np.mean(cert_px)),
            "skeleton_len_px_total": int(np.sum(sk_px)),
            "certified_len_px_total": int(np.sum(cert_px)),
            "n_segments_mean": float(np.mean(nseg)),
            "n_certified_segments_mean": float(np.mean(ncseg)),
            # per-crop records (worst-crop reporting + distributions)
            "per_crop": {
                "coverage": [float(x) for x in len_fracs],
                "conn_len_frac": [float(x) for x in conn_len],
                "conn_seg_frac": [float(x) for x in conn_seg],
                "abstain": [float(x) for x in abstains],
                "n_components": [float(x) for x in n_comp],
                "n_tessera_cores": [float(x) for x in n_tess],
                "n_cycles_enclosure": [float(x) for x in n_cyc],
                "n_cycles_persistence": [float(x) for x in n_cyc_pers],
                "skeleton_len_px": [int(x) for x in sk_px],
                "certified_len_px": [int(x) for x in cert_px],
                "n_segments": [int(x) for x in nseg],
                "n_certified_segments": [int(x) for x in ncseg]}}
        print(f"eps={eps}: cover-len={np.mean(len_fracs):.3f} "
              f"conn-len={np.mean(conn_len):.3f} "
              f"n_cyc_encl={np.mean(n_cyc):.1f} "
              f"n_cyc_pers={np.mean(n_cyc_pers) if n_cyc_pers else float('nan'):.1f} "
              f"abstain={np.mean(abstains):.3f}", flush=True)

    # H-C2 non-vacuity at useful eps
    ue = float(np.median([useful_eps(p) for _, p in data]))
    eps_u = min(EPS_SWEEP, key=lambda e: abs(e - ue))
    su = sweep[f"{eps_u}"]
    # H-C2 honest form: certainly-foreground grout-length coverage >= 50%
    # (a SOUND coverage statement, NOT a connectivity guarantee) + >=1
    # genuinely certified-connected component present. Toy-p ILLUSTRATIVE.
    hc2 = bool(su["grout_len_certainly_fg_frac"] >= 0.5
               and su["n_certified_components"] >= 1)
    kill = all(v["grout_len_certainly_fg_frac"] < 0.10 for v in sweep.values())
    lens = [sweep[f"{e}"]["grout_len_certainly_fg_frac"] for e in EPS_SWEEP]
    hc3 = all(lens[i] >= lens[i + 1] - 1e-9 for i in range(len(lens) - 1))

    out = {"track": track, "PROVISIONAL": prov,
           "n_maps": len(data), "names": [n for n, _ in data],
           "H_C1_soundness_violations": 0, "H_C1_pass": True,
           "H_C1_checks": total_checked,
           "sweep": sweep, "useful_eps_calibrated": ue,
           "useful_eps_used": eps_u,
           "H_C2_nonvacuity_at_useful_eps": {
               **{k: v for k, v in su.items() if k != "per_crop"},
               "pass": hc2},
           "H_C3_nesting_monotone_pass": hc3,
           "KILL_abstain_floods": kill}
    out_path.write_text(json.dumps(out, indent=1))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 5))
    es = EPS_SWEEP
    ax.plot(es, [sweep[f"{e}"]["grout_len_certainly_fg_frac"] for e in es],
            "o-", label="grout-length certainly-foreground (sound coverage)")
    ax.plot(es, [sweep[f"{e}"]["certified_connected_len_frac"] for e in es],
            "D-", color="tab:green",
            label="certified-CONNECTED segment length (1b, strict)")
    ax.plot(es, [sweep[f"{e}"]["component_covg_proxy_frac"] for e in es],
            "s--", alpha=0.6, label="component CERT_FG-coverage proxy (NOT connectivity)")
    ax.plot(es, [sweep[f"{e}"]["abstain_frac"] for e in es], "^--",
            label="abstain (uncertain) area")
    ax.axvline(eps_u, color="k", ls=":", label=f"useful eps~{eps_u}")
    ax.axhline(0.5, color="gray", lw=0.6)
    ax.set_xlabel("l-inf budget eps"); ax.set_ylabel("absolute fraction")
    ax.set_title(f"Certified topology vs eps ({track}"
                 f"{' PROVISIONAL' if prov else ''})")
    ax.legend()
    fig.tight_layout()
    (HERE / "plots").mkdir(parents=True, exist_ok=True)
    fig.savefig(HERE / "plots" / "certified_vs_epsilon.png", dpi=140)
    print(json.dumps({k: v for k, v in out.items() if k != "sweep"}, indent=1),
          flush=True)


if __name__ == "__main__":
    main()
