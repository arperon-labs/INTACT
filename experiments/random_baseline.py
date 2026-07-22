"""Random-mask miss-rate baseline (registered 2026-07-15,
REGISTRY 'RANDOM-MASK MISS-RATE REGISTRATION' — committed before this file).

Empirical companion to paper §3.6 Tightness: the two deterministic extremes
catch every planted SEMANTIC violation with certainty; N random reachable
masks miss at law-predicted rates that tend to 1 as the in-unison count c
grows. Detection probabilities are computed EXACTLY (ring: closed form; bar:
full pinch-block enumeration) with a Monte-Carlo cross-check; the miss
probability for a budget N is (1 - p_det)^N (draws iid).

  python random_baseline.py     # CPU-only, ~1 min; writes
                                # results_random_baseline.json + plots/miss_rate.png
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sandwich import cert_sets, reachable_fg  # noqa: E402

EPS = 0.1
RING_C = [1, 2, 4, 8, 12, 16]        # interior areas (1x1,1x2,2x2,2x4,3x4,4x4)
RING_HW = {1: (1, 1), 2: (1, 2), 4: (2, 2), 8: (2, 4), 12: (3, 4), 16: (4, 4)}
BAR_H = [1, 2, 4, 8]                 # pinch heights (min-cut c = h expected)
BUDGETS = [10, 30, 100, 1000]
K_MC = 200_000
SEED = 0


# ---------------------------------------------------------------- constructions
def build_ring(c):
    """Square ring: CERT_FG wall (0.95) around an h x w POSSIBLE interior
    (0.5), CERT_BG outside (0.05). Fill event needs ALL c interior pixels."""
    h, w = RING_HW[c]
    H, W = h + 8, w + 8                       # 2px wall + 2px bg margin
    p = np.full((H, W), 0.05, np.float32)
    p[2:h + 6, 2:w + 6] = 0.95                # wall block
    p[4:h + 4, 4:w + 4] = 0.5                 # POSSIBLE interior
    interior = np.zeros((H, W), bool)
    interior[4:h + 4, 4:w + 4] = True
    assert interior.sum() == c
    return p, interior


def build_bar(h):
    """Pinched bar: CERT_FG bar (0.95) h rows tall, 2-column POSSIBLE pinch
    (0.55) mid-span, CERT_BG elsewhere. Endpoints at the bar's two ends."""
    H, W = h + 8, 20
    p = np.full((H, W), 0.05, np.float32)
    r0 = 4
    p[r0:r0 + h, 2:18] = 0.95                 # bar
    p[r0:r0 + h, 9:11] = 0.55                 # pinch (POSSIBLE: 0.55 +/- 0.1)
    pinch = np.zeros((H, W), bool)
    pinch[r0:r0 + h, 9:11] = True
    ends = ((r0 + h // 2, 2), (r0 + h // 2, 17))
    return p, pinch, ends


# ---------------------------------------------------------------- semantics
def ring_violated(M, interior):
    """Hole destroyed <=> every interior pixel foreground (the CERT_FG wall
    encloses any remaining interior bg pixel)."""
    return bool(M[interior].all())


def bar_violated(M, ends):
    """Endpoints 8-disconnected in M."""
    n, lbl = cv2.connectedComponents(M.astype(np.uint8), connectivity=8)
    return lbl[ends[0]] != lbl[ends[1]]


# ---------------------------------------------------------------- exact laws
def harness_moment(k, m):
    """E_q[q^k (1-q)^m] for q ~ U(0.1, 0.9) (topo.py soundness_check
    sampler), by numeric quadrature."""
    q = np.linspace(0.1, 0.9, 20001)
    return float(np.trapezoid(q ** k * (1 - q) ** m, q) / 0.8)


def bar_enumerate(h):
    """EXACT per-draw detection for the bar: the violation event depends only
    on the 2h-pixel pinch block. Enumerate all 2^(2h) patterns; weight by
    the sampler's pattern probability (fair coin: 2^-2h each; harness:
    E_q[q^ones (1-q)^zeros], depends only on the ones-count)."""
    p, pinch, ends = build_bar(h)
    s = cert_sets(p, EPS)
    ys, xs = np.nonzero(pinch)
    n_pix = len(ys)
    det_fair = 0.0
    ones_hist = np.zeros(n_pix + 1)           # violating patterns by #ones
    for pat in range(1 << n_pix):
        bits = (pat >> np.arange(n_pix)) & 1
        choice = np.zeros_like(pinch)
        choice[ys, xs] = bits.astype(bool)
        M = reachable_fg(s, choice)
        if bar_violated(M, ends):
            det_fair += 2.0 ** (-n_pix)
            ones_hist[int(bits.sum())] += 1
    det_harness = sum(ones_hist[k] * harness_moment(k, n_pix - k)
                      for k in range(n_pix + 1))
    return det_fair, float(det_harness)


def bar_mincut(h):
    """Min vertex cut of POSSIBLE pixels separating the bar's two CERT_FG
    sides (8-adjacency), via max-flow with node splitting. Expected: h."""
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import maximum_flow
    p, pinch, ends = build_bar(h)
    s = cert_sets(p, EPS)
    ys, xs = np.nonzero(pinch)
    idx = {(y, x): i for i, (y, x) in enumerate(zip(ys, xs))}
    n = len(ys)
    BIG = 10 ** 6
    S, T = 2 * n, 2 * n + 1                   # in_i=2i, out_i=2i+1
    rows, cols, caps = [], [], []
    for (y, x), i in idx.items():
        rows.append(2 * i); cols.append(2 * i + 1); caps.append(1)   # vertex cap
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == dx == 0:
                    continue
                ny, nx_ = y + dy, x + dx
                if (ny, nx_) in idx:
                    j = idx[(ny, nx_)]
                    rows.append(2 * i + 1); cols.append(2 * j); caps.append(BIG)
                elif 0 <= ny < p.shape[0] and 0 <= nx_ < p.shape[1] \
                        and s["CERT_FG"][ny, nx_]:
                    if nx_ < x:                                       # left side
                        rows.append(S); cols.append(2 * i); caps.append(BIG)
                    elif nx_ > x:                                     # right side
                        rows.append(2 * i + 1); cols.append(T); caps.append(BIG)
    g = csr_matrix((caps, (rows, cols)), shape=(2 * n + 2, 2 * n + 2))
    return int(maximum_flow(g, S, T).flow_value)


# ---------------------------------------------------------------- MC cross-check
def mc_ring(c, rng):
    """Vectorized: violation <=> all c interior bits foreground."""
    fair = (rng.random((K_MC, c)) < 0.5).all(axis=1).mean()
    q = rng.uniform(0.1, 0.9, K_MC)
    harness = (rng.random((K_MC, c)) < q[:, None]).all(axis=1).mean()
    return float(fair), float(harness)


def mc_bar(h, rng):
    """Vectorized via the enumeration table (weights validated by sampling;
    per-pattern decisions come from the same cv2 labeling as the exact
    path, exercised through build/reachable in bar_enumerate)."""
    p, pinch, ends = build_bar(h)
    s = cert_sets(p, EPS)
    ys, xs = np.nonzero(pinch)
    n_pix = len(ys)
    table = np.zeros(1 << n_pix, bool)
    for pat in range(1 << n_pix):
        bits = (pat >> np.arange(n_pix)) & 1
        choice = np.zeros_like(pinch)
        choice[ys, xs] = bits.astype(bool)
        table[pat] = bar_violated(reachable_fg(s, choice), ends)
    pow2 = (1 << np.arange(n_pix)).astype(np.int64)
    fair_bits = rng.random((K_MC, n_pix)) < 0.5
    fair = table[(fair_bits @ pow2)].mean()
    q = rng.uniform(0.1, 0.9, K_MC)
    h_bits = rng.random((K_MC, n_pix)) < q[:, None]
    harness = table[(h_bits @ pow2)].mean()
    return float(fair), float(harness)


# ---------------------------------------------------------------- extremes
def extremes(p, mask_or_ends, violated):
    s = cert_sets(p, EPS)
    M_min = reachable_fg(s, np.zeros(p.shape, bool))
    M_max = reachable_fg(s, np.ones(p.shape, bool))
    return {"caught_at_M_min": bool(violated(M_min, mask_or_ends)),
            "caught_at_M_max": bool(violated(M_max, mask_or_ends))}


def main():
    rng = np.random.default_rng(SEED)
    out = {"seed": SEED, "eps": EPS, "K_MC": K_MC, "budgets": BUDGETS,
           "ring": [], "bar": []}

    for c in RING_C:
        p, interior = build_ring(c)
        exact_fair = 2.0 ** (-c)
        exact_harness = harness_moment(c, 0)
        mc_fair, mc_harness = mc_ring(c, rng)
        ext = extremes(p, interior, ring_violated)
        assert ext["caught_at_M_max"] and not ext["caught_at_M_min"], \
            f"ring c={c}: violation must localize at M_max exactly"
        out["ring"].append({
            "c": c, "det_fair_exact": exact_fair,
            "det_harness_exact": exact_harness,
            "det_fair_mc": mc_fair, "det_harness_mc": mc_harness,
            "extremes": ext,
            "miss_fair": {str(N): (1 - exact_fair) ** N for N in BUDGETS},
            "miss_harness": {str(N): (1 - exact_harness) ** N for N in BUDGETS}})
        print(f"ring c={c:2d}: fair {exact_fair:.3e} (mc {mc_fair:.3e}) "
              f"harness {exact_harness:.3e} (mc {mc_harness:.3e}) "
              f"extremes {ext}", flush=True)

    for h in BAR_H:
        p, pinch, ends = build_bar(h)
        cut = bar_mincut(h)
        det_fair, det_harness = bar_enumerate(h)
        mc_fair, mc_harness = mc_bar(h, rng)
        ext = extremes(p, ends, bar_violated)
        assert ext["caught_at_M_min"] and not ext["caught_at_M_max"], \
            f"bar h={h}: violation must localize at M_min exactly"
        assert cut == h, f"bar h={h}: max-flow min-cut {cut} != {h}"
        out["bar"].append({
            "h": h, "mincut_c": cut, "det_fair_exact": det_fair,
            "det_harness_exact": det_harness,
            "det_fair_mc": mc_fair, "det_harness_mc": mc_harness,
            "extremes": ext,
            "miss_fair": {str(N): (1 - det_fair) ** N for N in BUDGETS},
            "miss_harness": {str(N): (1 - det_harness) ** N for N in BUDGETS}})
        print(f"bar  h={h:2d}: mincut {cut} fair {det_fair:.3e} "
              f"(mc {mc_fair:.3e}) harness {det_harness:.3e} "
              f"(mc {mc_harness:.3e}) extremes {ext}", flush=True)

    (HERE / "results_random_baseline.json").write_text(json.dumps(out, indent=1))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    rc = [r["c"] for r in out["ring"]]
    ax1.semilogy(rc, [r["det_fair_exact"] for r in out["ring"]], "k-",
                 label=r"ring, fair coin: $2^{-c}$ (exact)")
    ax1.semilogy(rc, [r["det_fair_mc"] for r in out["ring"]], "ko",
                 fillstyle="none", label="ring, fair coin (MC)")
    ax1.semilogy(rc, [r["det_harness_exact"] for r in out["ring"]], "b-",
                 label=r"ring, harness $q{\sim}U(0.1,0.9)$: $E[q^c]$")
    ax1.semilogy(rc, [r["det_harness_mc"] for r in out["ring"]], "bs",
                 fillstyle="none", label="ring, harness (MC)")
    bc = [b["mincut_c"] for b in out["bar"]]
    ax1.semilogy(bc, [b["det_fair_exact"] for b in out["bar"]], "r^-",
                 label="bar, fair coin (enumerated)")
    ax1.semilogy(bc, [b["det_harness_exact"] for b in out["bar"]], "mv-",
                 label="bar, harness (enumerated)")
    ax1.set_xlabel("in-unison count $c$ (ring: interior area; bar: min-cut)")
    ax1.set_ylabel("per-draw detection probability")
    ax1.set_title("Random reachable masks: detection vs $c$")
    ax1.legend(fontsize=7)
    for N, ls in zip(BUDGETS, ["-", "--", "-.", ":"]):
        ax2.plot(rc, [r["miss_fair"][str(N)] for r in out["ring"]], "k" + ls,
                 label=f"fair coin, N={N}")
        ax2.plot(rc, [r["miss_harness"][str(N)] for r in out["ring"]],
                 "b" + ls, alpha=0.6, label=f"harness, N={N}")
    ax2.axhline(0.0, color="g", lw=1.5)
    ax2.annotate("two deterministic extremes: miss = 0 for every c",
                 (rc[0], 0.02), color="g", fontsize=8)
    ax2.set_xlabel("in-unison count $c$ (ring)")
    ax2.set_ylabel(r"miss probability $(1-p_{\rm det})^N$")
    ax2.set_title("Miss probability vs $c$ for fixed budgets")
    ax2.legend(fontsize=6, ncol=2)
    fig.tight_layout()
    (HERE / "plots").mkdir(exist_ok=True)
    fig.savefig(HERE / "plots" / "miss_rate.png", dpi=140)
    print("wrote results_random_baseline.json + plots/miss_rate.png", flush=True)


if __name__ == "__main__":
    main()
