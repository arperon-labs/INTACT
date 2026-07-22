"""Generate the paper's figures (CPU, matplotlib only; read-only over
experiments/). Colors: Okabe-Ito colorblind-safe subset, validated; line
styles + markers differ per series so grayscale print stays legible; mask
grids encode by LIGHTNESS (dark wall / hatched mid / near-white bg) with
direct labels, so they survive grayscale and CVD.

  python make_figs.py     # writes figs/*.png + figs/*.pdf
"""
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent

# RELEASE ADAPTATION - do not overwrite by wholesale copy from the source
# tree. Optional source imagery is NOT shipped here; only the frozen score
# maps in experiments/p_maps are. The source version walks above the repo
# root (parents[3]), which raises IndexError for any cloner.
_EXTERNAL = Path(os.environ.get("INTACT_EXTERNAL_DATA",
                                HERE.parents[0] / "external-data"))
EXP = HERE.parents[1] / "experiments" / "topocert"
FIGS = HERE / "figs"
EPS = [0.02, 0.05, 0.1, 0.15, 0.25, 0.4]

BLUE, GREEN, VERM = "#0072B2", "#009E73", "#D55E00"   # Okabe-Ito, validated
C_FG, C_POSS, C_BG = "#0072B2", "#F0E442", "#F7F7F5"  # lightness-separated

plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "grid.alpha": 0.25})


def _save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(FIGS / f"{name}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote figs/{name}.png/.pdf")


# ---- Fig 1: certified fractions vs eps (two panels, one y-scale) ---------
def fig_sweep():
    real = json.loads(
        (EXP / "results_real_hardened.json").read_text())["sweep"]
    toy = json.loads((EXP / "results_toy_hardened.json").read_text())["sweep"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)

    # LEFT: T-real (30 crops) — coverage vs connectivity is a MODEST 1.7x gap
    ax = axes[0]
    cov = [real[f"{e}"]["grout_len_certainly_fg_frac"] for e in EPS]
    conn = [real[f"{e}"]["certified_connected_len_frac"] for e in EPS]
    ab = [real[f"{e}"]["abstain_frac"] for e in EPS]
    ax.plot(EPS, cov, "o-", color=BLUE, label="coverage (certainly-fg length)")
    ax.plot(EPS, conn, "D-", color=GREEN, label="certified-connected length")
    ax.plot(EPS, ab, "^--", color=VERM, label="abstain area")
    ax.annotate(f"coverage {cov[-1]:.3f}", xy=(0.4, cov[-1]), xytext=(0.22, 0.74),
                fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.6))
    ax.annotate(f"connected {conn[-1]:.3f}", xy=(0.4, conn[-1]),
                xytext=(0.20, 0.20), fontsize=7.5,
                arrowprops=dict(arrowstyle="-", lw=0.6))
    ax.annotate(r"$1.7\times$ gap", xy=(0.40, 0.47), fontsize=8,
                color="0.30", ha="center", fontweight="bold")
    ax.set_title("T-real (30 crops, frozen zero-shot model)", fontsize=9)

    # RIGHT: T-toy — the ~14x collapse is a blurred-mask artifact, not real
    ax = axes[1]
    cov = [toy[f"{e}"]["grout_len_certainly_fg_frac"] for e in EPS]
    conn = [toy[f"{e}"]["certified_connected_len_frac"] for e in EPS]
    ab = [toy[f"{e}"]["abstain_frac"] for e in EPS]
    ax.plot(EPS, cov, "o-", color=BLUE, label="coverage (certainly-fg length)")
    ax.plot(EPS, conn, "D-", color=GREEN, label="certified-connected length")
    ax.plot(EPS, ab, "^--", color=VERM, label="abstain area")
    ax.annotate("coverage 0.500", xy=(0.4, 0.50), xytext=(0.27, 0.62),
                fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.6))
    ax.annotate("connected 0.036", xy=(0.4, 0.036), xytext=(0.27, 0.16),
                fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.6))
    ax.annotate(r"$\sim\!14\times$ gap", xy=(0.40, 0.26), fontsize=8,
                color="0.30", ha="center", fontweight="bold")
    ax.set_title("Toy track (blurred-mask validation)", fontsize=9)

    for ax in axes:
        ax.set_xlabel(r"$\ell_\infty$ budget $\varepsilon$")
        ax.grid(True)
        ax.set_ylim(0, 1.02)
    axes[0].set_ylabel("absolute fraction")
    # single shared legend UNDER the panels (the right panel carries all series)
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8,
               frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.subplots_adjust(bottom=0.30)
    _save(fig, "fig_sweep")


# ---- Fig 2: the beta1 counterexample (regression-test constructions) -----
def ring(interior_p, H=40):
    """Exact construction from tests/test_topocert.py::TestCycleSoundness."""
    yy, xx = np.mgrid[:H, :H]
    r = np.sqrt((yy - 20) ** 2 + (xx - 20) ** 2)
    p = np.full((H, H), 0.05, np.float32)
    p[(r > 8) & (r < 14)] = 0.95
    p[r <= 8] = interior_p
    return p


def cert_grid(p, eps=0.1):
    """0=CERT_BG, 1=POSSIBLE, 2=CERT_FG (plain thresholds suffice for the
    illustration; PEDANTIC widening moves nothing at these values)."""
    g = np.ones(p.shape, np.int8)
    g[p - eps > 0.5] = 2
    g[p + eps < 0.5] = 0
    return g


def draw_grid(ax, g, title):
    cmap = ListedColormap([C_BG, C_POSS, C_FG])
    ax.imshow(g, cmap=cmap, vmin=0, vmax=2, interpolation="nearest")
    poss = g == 1                       # hatch POSSIBLE for print/CVD safety
    if poss.any():
        ax.contourf(poss.astype(float), levels=[0.5, 1.5], colors="none",
                    hatches=["///"])
        ax.contour(poss.astype(float), levels=[0.5], colors="0.3",
                   linewidths=0.6)
    ax.set_title(title, fontsize=8.5)
    ax.set_xticks([]), ax.set_yticks([])


def fig_counterexample():
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.7))
    g_bad = cert_grid(ring(0.5))
    draw_grid(axes[0], g_bad,
              "(a) ring over POSSIBLE\n$\\beta_1(\\mathrm{CERT\\_FG})=1$ "
              "— but fillable")
    filled = np.where(g_bad == 1, 2, g_bad)   # adversary: all-POSSIBLE -> fg
    draw_grid(axes[1], filled,
              "(b) in-budget adversary fills\nthe interior — cycle destroyed")
    draw_grid(axes[2], cert_grid(ring(0.05)),
              "(c) ring over CERT_BG\nunfillable — certified")
    handles = [Patch(facecolor=C_FG, label="CERT_FG (certainly grout)"),
               Patch(facecolor=C_POSS, hatch="///", edgecolor="0.3",
                     label="POSSIBLE (adversary's)"),
               Patch(facecolor=C_BG, edgecolor="0.6",
                     label="CERT_BG (certainly bg)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8,
               frameon=False, bbox_to_anchor=(0.5, -0.06))
    _save(fig, "fig_counterexample")


# ---- Fig 3 (appendix): pinched-bar connectivity counterexample -----------
def fig_pinch():
    """Construction from TestConnectivityCertificate: coverage stays high but
    the spanning segment is disqualified by a 2-px POSSIBLE pinch."""
    H, W = 30, 60
    p = np.full((H, W), 0.05, np.float32)
    p[13:17, 5:55] = 0.95
    p[13:17, 29:31] = 0.55
    fig, ax = plt.subplots(figsize=(4.6, 1.9))
    draw_grid(ax, cert_grid(p),
              "pinched bar: 48 of 50 bar columns stay CERT_FG (high "
              "coverage),\nbut certified-connected length is 0 — a single "
              "POSSIBLE pinch\ndisqualifies the spanning segment")
    _save(fig, "fig_pinch")


# ---- Fig T (§3.6): tightness 2x2 — each violation at exactly one extreme --
def draw_mask(ax, M, former_poss, title, ok):
    """Binary extreme mask (lightness-coded) + dashed outline of the former
    POSSIBLE region so the adversary's move stays visible."""
    cmap = ListedColormap([C_BG, C_FG])
    ax.imshow(M.astype(int), cmap=cmap, vmin=0, vmax=1,
              interpolation="nearest")
    if former_poss.any():
        ax.contour(former_poss.astype(float), levels=[0.5], colors="0.25",
                   linewidths=0.9, linestyles="--")
    ax.set_title(title, fontsize=8, color=GREEN if ok else VERM)
    ax.set_xticks([]), ax.set_yticks([])


def fig_tightness():
    """{fillable ring, pinched bar} x {M_min, M_max}: the ring certificate
    passes at M_min and fails only at M_max; the bar segment passes at M_max
    and fails only at M_min — both extremes individually necessary, and each
    failure localizes at exactly one extreme (Lemma 1)."""
    g_ring = cert_grid(ring(0.5))                       # fillable ring
    H, W = 30, 60                                       # pinched bar (Fig 3)
    p_bar = np.full((H, W), 0.05, np.float32)
    p_bar[13:17, 5:55] = 0.95
    p_bar[13:17, 29:31] = 0.55
    g_bar = cert_grid(p_bar)

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.6),
                             gridspec_kw={"height_ratios": [1.5, 1]})
    for row, (g, name) in enumerate(
            [(g_ring, "fillable ring (cycle)"),
             (g_bar, "pinched bar (connectivity)")]):
        M_min, M_max, poss = g == 2, g >= 1, g == 1
        if row == 0:
            draw_mask(axes[0, 0], M_min, poss,
                      "ring at $M_{\\min}$ — hole open:\npasses ✓", True)
            draw_mask(axes[0, 1], M_max, poss,
                      "ring at $M_{\\max}$ — interior filled:\nFAILS ✗ "
                      "($M_{\\max}$ necessary)", False)
        else:
            draw_mask(axes[1, 0], M_min, poss,
                      "bar at $M_{\\min}$ — pinch cut:\nFAILS ✗ "
                      "($M_{\\min}$ necessary)", False)
            draw_mask(axes[1, 1], M_max, poss,
                      "bar at $M_{\\max}$ — spans:\npasses ✓", True)
    fig.suptitle("Both extremes are individually necessary — each planted "
                 "violation is caught at exactly one extreme",
                 fontsize=9, y=0.99)
    handles = [Patch(facecolor=C_FG, label="foreground in the extreme mask"),
               Patch(facecolor=C_BG, edgecolor="0.6", label="background"),
               plt.Line2D([], [], color="0.25", ls="--", lw=0.9,
                          label="former POSSIBLE region")]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8,
               frameon=False, bbox_to_anchor=(0.5, -0.02))
    _save(fig, "fig_tightness")


# ---- Fig anatomy (§5.1): the certificate on the worst-coverage real crop --
TRICOLOR = ListedColormap([C_BG, C_POSS, C_FG])


def draw_flat(ax, g, title):
    """Color-only tricolor (no hatch/outline) — the hatched draw_grid is for
    small test arrays; at 512^2 per-island outlines read as gray mush."""
    ax.imshow(g, cmap=TRICOLOR, vmin=0, vmax=2, interpolation="nearest")
    if title:
        ax.set_title(title, fontsize=8)
    ax.set_xticks([]), ax.set_yticks([])


def voronoi_mosaic_p(H=216, W=216, cell=36, seed=7):
    """Deterministic jittered-grid Voronoi ridge = grout lattice (Python port
    of the live demo's mosaicP; the interactive companion's score map)."""
    from scipy.ndimage import gaussian_filter
    rng = np.random.default_rng(seed)
    gx, gy = int(np.ceil(W / cell)) + 2, int(np.ceil(H / cell)) + 2
    sx = (np.arange(gx)[None, :] - 1 + 0.5) * cell
    sy = (np.arange(gy)[:, None] - 1 + 0.5) * cell
    seeds = np.stack([(sx + (rng.random((gy, gx)) - 0.5) * 0.8 * cell).ravel(),
                      (sy + (rng.random((gy, gx)) - 0.5) * 0.8 * cell).ravel()],
                     axis=1)                                   # (S,2) as (x,y)
    yy, xx = np.mgrid[:H, :W]
    d = np.sqrt((xx[..., None] - seeds[:, 0]) ** 2
                + (yy[..., None] - seeds[:, 1]) ** 2)          # (H,W,S)
    d.sort(axis=2)
    hard = ((d[..., 1] - d[..., 0]) < 2.6).astype(np.float32)  # grout ridge
    p = np.minimum(1.0, gaussian_filter(hard, 1.6) * 1.9)
    rng2 = np.random.default_rng(11)
    coarse = gaussian_filter(rng2.standard_normal((H, W)), 3.0)  # correlated texture
    coarse = coarse / (coarse.std() + 1e-9) * 0.055
    fine = (rng2.random((H, W)) - 0.5) * 0.07
    # texture only bites where it cannot flip a confident label past eps<=0.4:
    # grout (~1) and tile cores (~0) keep their side; mid-tones get the most.
    amp = 0.5 + 0.5 * np.cos(np.pi * np.clip(p, 0, 1))      # 1 at p=0.5, 0 at 0/1
    return np.clip(p + (coarse + fine) * (0.4 + 0.6 * amp),
                   0, 1).astype(np.float32)


def hole_kinds(p, eps, min_area=20):
    """Classify enclosed holes exactly as the demo/topo do: a hole is CERTIFIED
    (unfillable) iff it holds a CERT_BG core walled off from the border through
    ~CERT_FG; enclosed regions with no such core are FILLABLE — REFUSED (what
    the unsound beta1(CERT_FG) would still have certified). Returns
    (certified_core_mask, refused_region_mask)."""
    import cv2
    import sys
    sys.path.insert(0, str(EXP))
    from sandwich import cert_sets
    s = cert_sets(p, eps)
    fg, bg = s["CERT_FG"], s["CERT_BG"]
    nB, labB, statsB, _ = cv2.connectedComponentsWithStats(bg.astype(np.uint8), 4)
    nC, labC = cv2.connectedComponents((~fg).astype(np.uint8), 4)  # ~CERT_FG regions
    border = (set(labC[0]) | set(labC[-1]) | set(labC[:, 0]) | set(labC[:, -1]))
    border.discard(0)
    cert = np.zeros(p.shape, bool)
    has_core = set()
    for i in range(1, nB):
        if statsB[i, cv2.CC_STAT_AREA] < min_area:
            continue
        comp = labB == i
        reg = int(labC[comp][0])
        if reg in border:                        # reachable from border -> leaks
            continue
        cert |= comp
        has_core.add(reg)
    refused = np.zeros(p.shape, bool)
    for l in range(1, nC):
        if l in border:
            continue
        reg = labC == l
        if int(reg.sum()) >= min_area and l not in has_core:
            refused |= reg
    return cert, refused


def _scale_floor(mask, min_area):
    """Drop connected pieces < min_area and fill interior holes < min_area
    (the paper's scale floor; cv2-based, warning-free)."""
    import cv2
    if not mask.any():
        return mask
    keep = np.zeros(mask.shape, bool)
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= min_area:
            keep[lab == i] = True
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(
        (~keep).astype(np.uint8), 8)
    bord = set(lab2[0]) | set(lab2[-1]) | set(lab2[:, 0]) | set(lab2[:, -1])
    for i in range(1, n2):
        if i not in bord and st2[i, cv2.CC_STAT_AREA] < min_area:
            keep[lab2 == i] = True
    return keep


def _draw_sandwich(ax, p, eps, title, min_area=20):
    """Demo-style panel: tricolor sandwich + green outline on certified
    unfillable holes, dashed vermilion outline on fillable-refused holes."""
    ax.imshow(cert_grid(p, eps), cmap=TRICOLOR, vmin=0, vmax=2,
              interpolation="nearest")
    cert, refused = hole_kinds(p, eps, min_area)
    # scale floor (as the paper applies): drop sub-scale certified debris and
    # fill sub-scale interior speckles so outlines trace whole holes, not noise
    cert, refused = _scale_floor(cert, min_area), _scale_floor(refused, min_area)
    if cert.any():
        ax.contour(cert.astype(float), levels=[0.5], colors=[GREEN],
                   linewidths=1.3)
    if refused.any():
        ax.contour(refused.astype(float), levels=[0.5], colors=[VERM],
                   linewidths=1.8, linestyles="--")
    if title:
        ax.set_title(title, fontsize=8)
    ax.set_xticks([]), ax.set_yticks([])


_SANDWICH_LEGEND = [
    Patch(facecolor=C_FG, label="CERT_FG (certainly grout)"),
    Patch(facecolor=C_POSS, label="POSSIBLE (adversary's)"),
    Patch(facecolor=C_BG, edgecolor="0.6", label="CERT_BG (certainly bg)"),
    plt.Line2D([], [], color=GREEN, lw=1.4, label="unfillable hole — certified"),
    plt.Line2D([], [], color=VERM, ls="--", lw=1.2, label="fillable — refused"),
]


def fig_anatomy():
    """Real-crop anatomy in the demo's clean encoding: score map -> sandwich
    at the calibration budget -> sandwich at eps=0.40, with certified (green)
    vs fillable-refused (dashed) holes outlined. Crop is the WORST-coverage
    crop at eps=0.10 by the registered metric (crop_byzantine_01), not curated."""
    p = np.load(EXP / "p_maps" / "crop_byzantine_01.npy")
    fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.0))
    im = axes[0].imshow(p, cmap="Blues", vmin=0, vmax=1,
                        interpolation="nearest")
    axes[0].set_title("(a) score map $p$", fontsize=8)
    axes[0].set_xticks([]), axes[0].set_yticks([])
    fig.colorbar(im, ax=axes[0], fraction=0.046, pad=0.02)
    _draw_sandwich(axes[1], p, 0.1, "(b) sandwich, $\\varepsilon=0.10$", 15)
    _draw_sandwich(axes[2], p, 0.4,
                   "(c) $\\varepsilon=0.40$ — abstention floods", 15)
    fig.legend(handles=_SANDWICH_LEGEND, loc="lower center", ncol=5,
               fontsize=6.6, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(bottom=0.14, wspace=0.24)
    _save(fig, "fig_anatomy")


def fig_gallery():
    """The live-demo view recreated for print: a clean synthetic Voronoi mosaic
    where confident tiles are certified unfillable holes (green) while ONE tile
    with a model-uncertain interior is refused as fillable (dashed) — the beta1
    correction visible on realistic structure, with erosion of the guarantee
    as eps grows."""
    import cv2
    from scipy.ndimage import binary_dilation
    p = voronoi_mosaic_p()
    # inject ONE uncertain-interior tile -> a fillable (refused) hole beside the
    # certified ones (illustrative; a real model unsure about one tile's fill).
    # Blank the WHOLE CERT_BG core (dilate 1 to eat any residual bg ring), so
    # the enclosed region holds no certain-background core.
    cert, _ = hole_kinds(p, 0.1, 20)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(cert.astype("uint8"), 4)
    H, W = p.shape
    pick, best = None, 1e18
    for i in range(1, n):
        a = stats[i, cv2.CC_STAT_AREA]
        if 200 < a < 700:
            dc = (cent[i][1] - H / 2) ** 2 + (cent[i][0] - W / 2) ** 2
            if dc < best:
                best, pick = dc, i
    p = p.copy()
    if pick is not None:
        reg = binary_dilation(lab == pick, iterations=1)
        rngc = np.random.default_rng(23)                      # noisy, uncertain
        p[reg] = np.clip(0.5 + (rngc.random(int(reg.sum())) - 0.5) * 0.16,
                         0, 1)                                # ~[0.42, 0.58]

    fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.0))
    im = axes[0].imshow(p, cmap="Blues", vmin=0, vmax=1,
                        interpolation="nearest")
    axes[0].set_title("(a) synthetic mosaic $p$\n(one tile's fill uncertain)",
                      fontsize=8)
    axes[0].set_xticks([]), axes[0].set_yticks([])
    fig.colorbar(im, ax=axes[0], fraction=0.046, pad=0.02)
    _draw_sandwich(axes[1], p, 0.10, "(b) $\\varepsilon=0.10$", 80)
    _draw_sandwich(axes[2], p, 0.315, "(c) $\\varepsilon=0.315$", 80)
    fig.legend(handles=_SANDWICH_LEGEND, loc="lower center", ncol=5,
               fontsize=6.6, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(bottom=0.14, wspace=0.24)
    _save(fig, "fig_gallery")


# ---- Fig pipeline (§2): method schematic with real thumbnails -------------
def fig_pipeline():
    """image -> frozen model -> p -> eps-band sandwich -> five certificates,
    attacked at the two extremes by the soundness harness. All geometry in
    figure-fraction coordinates via one overlay axes (no frame mixing)."""
    import matplotlib.image as mpimg
    p = np.load(EXP / "p_maps" / "crop_byzantine_01.npy")
    crop_png = (_EXTERNAL / "data" / "realset"
                / "crops" / "crop_byzantine_01.png")

    fig = plt.figure(figsize=(7.2, 2.7))
    ov = fig.add_axes([0, 0, 1, 1])               # overlay frame, 0..1
    ov.set_xlim(0, 1), ov.set_ylim(0, 1)
    ov.axis("off")

    TY, TH, TW = 0.30, 0.52, 0.145                # thumb row geometry
    xs = [0.03, 0.245, 0.46]

    def thumb(x, img, label, cmap=None, grid=False):
        a = fig.add_axes([x, TY, TW, TH])
        if grid:
            a.imshow(img, cmap=TRICOLOR, vmin=0, vmax=2,
                     interpolation="nearest")
        else:
            a.imshow(img, cmap=cmap, interpolation="nearest")
        a.set_xticks([]), a.set_yticks([])
        for sp in a.spines.values():
            sp.set_color("0.6"), sp.set_linewidth(0.6)
        a.set_title(label, fontsize=7.5)

    if crop_png.exists():
        thumb(xs[0], mpimg.imread(str(crop_png)), "image crop")
    thumb(xs[1], p, "score map $p$", cmap="Blues")
    thumb(xs[2], cert_grid(p, 0.1), "sandwich", grid=True)

    mid = TY + TH / 2
    for x_from, x_to in [(xs[0] + TW, xs[1]), (xs[1] + TW, xs[2])]:
        ov.annotate("", xy=(x_to - 0.004, mid), xytext=(x_from + 0.004, mid),
                    arrowprops=dict(arrowstyle="->", lw=1.1, color="0.1"))
    # gap labels on a TOP overlay (added after the thumbs, so thumbnail axes
    # cannot occlude them); white boxes make the slight overlap clean.
    top_ov = fig.add_axes([0, 0, 1, 1])
    top_ov.set_xlim(0, 1), top_ov.set_ylim(0, 1)
    top_ov.axis("off")
    for x_from, x_to, label in [
            (xs[0] + TW, xs[1], "frozen model"),
            (xs[1] + TW, xs[2], "$\\pm\\varepsilon$ band, threshold ½")]:
        top_ov.text((x_from + x_to) / 2, mid + 0.13, label, fontsize=6.8,
                    ha="center", va="bottom", color="0.1",
                    bbox=dict(boxstyle="round,pad=0.22", fc="white",
                              ec="0.5", lw=0.5, alpha=0.92))

    certs = ["coverage", "$\\beta_0$ components", "tessera cores",
             "connectivity", "unfillable cycles"]
    chip_x, top, step = 0.76, 0.86, 0.135
    for i, c in enumerate(certs):
        y = top - i * step
        ov.text(chip_x, y, c, fontsize=7.5, ha="left", va="center",
                bbox=dict(boxstyle="round,pad=0.28", fc="white", ec=BLUE,
                          lw=0.8))
        ov.annotate("", xy=(chip_x - 0.008, y),
                    xytext=(xs[2] + TW + 0.004, mid),
                    arrowprops=dict(arrowstyle="->", lw=0.7, color="0.45"))
    ov.text(0.845, 0.075,
            "soundness harness: attack every class at $M_{\\min}$ and "
            "$M_{\\max}$;\nplanted faults must be caught",
            fontsize=6.6, ha="center", va="center", color=VERM,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=VERM, lw=0.8))
    ov.annotate("", xy=(0.845, 0.19), xytext=(0.845, 0.135),
                arrowprops=dict(arrowstyle="->", lw=0.9, color=VERM))
    _save(fig, "fig_pipeline")


# ---- Fig hero (page 1 teaser): the method in one glance -------------------
def fig_hero():
    """RETIRED from the paper (2026-07-17): fig_graded took the page-1 teaser
    slot — it is on real data and states the sharper claim (the certificate is
    not a confidence map). This figure's content is already covered by
    fig_pipeline (§2 schematic) and fig_gallery (§3.5, same Voronoi sandwich
    with certified/refused holes). Kept and still generated so it can be put
    back in one line if wanted.

    A frozen (grainy, realistic) score map, its +/-eps
    sandwich, and the same at a larger budget. TWO graded-uncertainty tiles
    make the progression legible: a VERY grainy tile is already POSSIBLE and
    refused at eps=0.10; a MODERATELY grainy tile is still certified at 0.10
    but flips to refused as the budget grows. Certified unfillable holes are
    solid green, refused fillable ones solid vermilion."""
    import cv2
    from scipy.ndimage import binary_dilation, gaussian_filter
    import sys as _sys
    _sys.path.insert(0, str(EXP))
    from sandwich import cert_sets
    H = W = 240
    p = voronoi_mosaic_p(H=H, W=W, cell=40, seed=7)
    # more overall grain for realism, modulated so confident regions (grout ~1,
    # cores ~0) keep their side while mid-tones and edges get visible texture
    rg = np.random.default_rng(31)
    fine = gaussian_filter(rg.standard_normal((H, W)), 0.6)
    fine = fine / (fine.std() + 1e-9)
    amp0 = 0.5 + 0.5 * np.cos(np.pi * np.clip(p, 0, 1))   # 1 at p=0.5, 0 at 0/1
    p = np.clip(p + fine * 0.048 * (0.35 + amp0), 0, 1)
    # two uncertain tiles, spatially apart
    s0 = cert_sets(p, 0.10)
    nB, labB, stB, ctB = cv2.connectedComponentsWithStats(
        s0["CERT_BG"].astype(np.uint8), 4)
    cores = [i for i in range(1, nB) if stB[i, cv2.CC_STAT_AREA] >= 260]
    p = p.copy()
    rc = np.random.default_rng(23)
    if cores:
        a = min(cores, key=lambda i: (ctB[i][1] - H * 0.5) ** 2
                + (ctB[i][0] - W * 0.40) ** 2)          # A near centre-left
        regA = binary_dilation(labB == a, iterations=2)  # VERY grainy ~0.5
        p[regA] = np.clip(0.5 + (rc.random(int(regA.sum())) - 0.5) * 0.19, 0, 1)
        ay, ax_ = ctB[a][1], ctB[a][0]
        rest = [i for i in cores if i != a                # central & apart from A
                and 0.20 * W < ctB[i][0] < 0.80 * W
                and 0.18 * H < ctB[i][1] < 0.80 * H]
        if rest:
            b = max(rest, key=lambda i: (ctB[i][1] - ay) ** 2
                    + (ctB[i][0] - ax_) ** 2)            # B farthest from A
            regB = binary_dilation(labB == b, iterations=2)  # MODERATE ~0.30
            p[regB] = np.clip(0.30 + (rc.random(int(regB.sum())) - 0.5) * 0.13,
                              0, 1)

    def panel(ax, eps, title, mn=60):
        ax.imshow(cert_grid(p, eps), cmap=TRICOLOR, vmin=0, vmax=2,
                  interpolation="nearest")
        cert, refused = hole_kinds(p, eps, mn)
        cert, refused = _scale_floor(cert, mn), _scale_floor(refused, mn)
        if cert.any():
            ax.contour(cert.astype(float), [0.5], colors=[GREEN], linewidths=1.3)
        if refused.any():                              # SOLID vermilion
            ax.contour(refused.astype(float), [0.5], colors=[VERM], linewidths=2.1)
        ax.set_title(title, fontsize=9)
        ax.set_xticks([]), ax.set_yticks([])

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.55))
    axes[0].imshow(p, cmap="gray_r", vmin=0, vmax=1, interpolation="nearest")
    axes[0].set_title(r"frozen score map $p$ (two tiles uncertain)", fontsize=9)
    axes[0].set_xticks([]), axes[0].set_yticks([])
    panel(axes[1], 0.10, r"$\pm\varepsilon$ sandwich ($\varepsilon{=}0.10$)")
    panel(axes[2], 0.30, r"larger budget ($\varepsilon{=}0.30$)")
    for x in (0.332, 0.668):                           # flow arrows in the gutters
        fig.text(x, 0.55, r"$\Rightarrow$", fontsize=15, ha="center",
                 va="center", color="0.45")
    hero_legend = [
        Patch(facecolor=C_FG, label="CERT_FG (certainly grout)"),
        Patch(facecolor=C_POSS, label="POSSIBLE (adversary's)"),
        Patch(facecolor=C_BG, edgecolor="0.6", label="CERT_BG (certainly bg)"),
        plt.Line2D([], [], color=GREEN, lw=1.6, label="unfillable hole — certified"),
        plt.Line2D([], [], color=VERM, lw=2.1, label="fillable — refused"),
    ]
    fig.legend(handles=hero_legend, loc="lower center", ncol=5, fontsize=6.6,
               frameon=False, bbox_to_anchor=(0.5, -0.05), handlelength=1.4,
               columnspacing=1.1)
    fig.subplots_adjust(bottom=0.15, wspace=0.10, left=0.01, right=0.99, top=0.9)
    _save(fig, "fig_hero")


# ---- Fig worst-crop (§5.1): per-crop distribution, worst-case floor -------
def fig_worstcrop():
    """Per-crop distribution of coverage and certified-connected length across
    the 30 real crops at each eps (box = IQR, whiskers = full range). The
    worst crop (min) is marked: a worst-case paper's honest headline is the
    floor, not the mean, and it shows the result is not driven by outliers."""
    sw = json.loads((EXP / "results_real_hardened.json").read_text())["sweep"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1), sharex=True, sharey=True)
    panels = [("coverage", "coverage", BLUE),
              ("conn_len_frac", "certified-connected length", GREEN)]
    pos = list(range(len(EPS)))
    for ax, (key, title, color) in zip(axes, panels):
        data = [sw[f"{e}"]["per_crop"][key] for e in EPS]
        bp = ax.boxplot(data, positions=pos, widths=0.55, patch_artist=True,
                        medianprops=dict(color="0.15", lw=1.2),
                        flierprops=dict(marker=".", ms=3, mec="0.5", mfc="0.5"),
                        whiskerprops=dict(color="0.4"),
                        capprops=dict(color="0.4"))
        for b in bp["boxes"]:
            b.set(facecolor=color, alpha=0.35, edgecolor=color)
        mins = [min(d) for d in data]
        ax.plot(pos, mins, "v", color=VERM, ms=6, zorder=5,
                label="worst crop (min)")
        ax.annotate(f"{mins[-1]:.3f}", xy=(pos[-1], mins[-1]),
                    xytext=(pos[-1] - 0.9, mins[-1] + 0.05), fontsize=7.5,
                    color=VERM, arrowprops=dict(arrowstyle="-", lw=0.6, color=VERM))
        ax.set_title(title, fontsize=9)
        ax.set_xticks(pos)
        ax.set_xticklabels([str(e) for e in EPS], fontsize=7.5)
        ax.set_xlabel(r"$\ell_\infty$ budget $\varepsilon$", fontsize=8)
        ax.set_ylim(-0.02, 1.02)
        ax.legend(fontsize=7.5, frameon=False, loc="lower left")
    axes[0].set_ylabel("per-crop fraction (30 crops)", fontsize=8)
    fig.tight_layout()
    _save(fig, "fig_worstcrop")


# ---- Fig graded: per-FEATURE certified budget as a heatmap ----------------
def fig_graded():
    """The certificate as a heatmap. Each certified enclosed tessera is painted
    by the LARGEST eps at which it stays certified — its survival budget. This
    is NOT the per-pixel margin |p-1/2| (a monotone transform of entropy,
    disclaimed in §7): a hole can die because its WALL erodes rather than its
    own interior, so the budget is topological (eps* = min(wall, interior)).
    Exact nesting (§5.4) makes the map well-defined: certified sets shrink
    monotonically in eps."""
    import sys as _sys
    _sys.path.insert(0, str(EXP))
    import run
    # representative crop, not cherry-picked: the one whose certified-cycle
    # count at eps=0.02 is closest to the 30-crop cohort mean
    cyc = json.loads((EXP / "results_real_hardened.json").read_text())[
        "sweep"]["0.02"]["per_crop"]["n_cycles_enclosure"]
    idx = int(np.argmin(np.abs(np.asarray(cyc) - np.mean(cyc))))
    name, p = run.load_pmaps(idx + 1)[idx]
    grid = np.round(np.arange(0.02, 0.462, 0.02), 3)
    surv = np.zeros(p.shape, np.float32)          # 0 = never certified
    for eps in grid:                              # ascending -> last write = max
        cert, _ = hole_kinds(p, float(eps), 40)
        cert = _scale_floor(cert, 40)
        surv[cert] = eps
    pixel_margin = np.abs(p - 0.5)                # the entropy-equivalent map

    fig, axes = plt.subplots(1, 3, figsize=(7.6, 2.7))
    axes[0].imshow(p, cmap="gray_r", vmin=0, vmax=1, interpolation="nearest")
    axes[0].set_title(r"score map $p$", fontsize=9)
    im1 = axes[1].imshow(np.where(pixel_margin > 0, pixel_margin, np.nan),
                         cmap="magma", vmin=0, vmax=0.5, interpolation="nearest")
    axes[1].set_title(r"per-pixel margin $|p-\frac{1}{2}|$" "\n"
                      r"(entropy-equivalent, §7)", fontsize=8.5)
    fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.02)
    im2 = axes[2].imshow(np.where(surv > 0, surv, np.nan), cmap="viridis",
                         vmin=0.02, vmax=0.46, interpolation="nearest")
    axes[2].set_title("per-tessera certified budget $\\varepsilon^{*}$\n"
                      "(topological: wall OR interior)", fontsize=8.5)
    cb = fig.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.02)
    cb.set_label(r"certified up to $\varepsilon$", fontsize=7.5)
    for ax in axes:
        ax.set_xticks([]), ax.set_yticks([])
    fig.subplots_adjust(wspace=0.18, left=0.02, right=0.97, top=0.86,
                        bottom=0.03)
    _save(fig, "fig_graded")


# ---- Fig vessels (V2): the certificate on real retinal images -------------
def fig_vessels():
    """Cross-domain (§5.7) VISUAL: the certificate on real retinal-vessel
    images from two datasets. One row per dataset — fundus green channel →
    Frangi score map p → the ±eps sandwich at the useful budget — so the
    machinery is shown running off-domain, not only as a decoupling scatter.
    Certainly-vessel (CERT_FG) is blue, the uncertain band POSSIBLE (yellow),
    certain background CERT_BG (white)."""
    import sys as _sys
    from scipy.ndimage import binary_erosion
    _sys.path.insert(0, str(EXP))
    import drive_v2
    import chase_parallel as cp
    # DRIVE image (first training image)
    d_imgs = sorted(drive_v2.DRIVE.glob("images/*.tif"))
    dn = d_imgs[0].name.split("_")[0]
    d_green = drive_v2.load(d_imgs[0])[..., 1].astype(np.float32) / 255.0
    d_fov = binary_erosion(
        drive_v2.load(drive_v2.DRIVE / "mask" / f"{dn}_training_mask.gif") > 0,
        iterations=drive_v2.FOV_ERODE)
    d_p = drive_v2.frangi_p(d_green, d_fov, drive_v2.TRANSFORMS["cbrt"])
    # CHASE image (first)
    _, c_green, _, c_fov = cp.load_data(1)[0]
    c_p = cp.cv.frangi_p(c_green, c_fov, cp.cv.TRANSFORMS["cbrt"])

    rows = [("DRIVE", d_green, d_p, d_fov),
            ("CHASE_DB1", c_green, c_p, c_fov)]
    col = ["fundus (green ch.)", r"Frangi $p$",
           r"sandwich $\varepsilon{=}0.10$",
           r"sandwich $\varepsilon{=}0.25$ (useful)"]
    fig, axes = plt.subplots(2, 4, figsize=(7.6, 4.2))
    for r, (name, green, p, fov) in enumerate(rows):
        axes[r, 0].imshow(np.where(fov, green, np.nan), cmap="gray")
        axes[r, 1].imshow(np.where(fov, p, np.nan), cmap="gray_r",
                          vmin=0, vmax=1)
        for cix, eps in ((2, 0.10), (3, 0.25)):
            grid = np.where(fov, cert_grid(p, eps), 0)  # outside FOV -> CERT_BG
            axes[r, cix].imshow(grid, cmap=TRICOLOR, vmin=0, vmax=2,
                                interpolation="nearest")
        axes[r, 0].set_ylabel(name.replace("_", r"\_"), fontsize=10)
        for cix in range(4):
            axes[r, cix].set_xticks([]), axes[r, cix].set_yticks([])
            if r == 0:
                axes[r, cix].set_title(col[cix], fontsize=8.5)
    vessel_legend = [
        Patch(facecolor=C_FG, label="CERT_FG (certainly vessel)"),
        Patch(facecolor=C_POSS, label="POSSIBLE (adversary's)"),
        Patch(facecolor=C_BG, edgecolor="0.6", label="CERT_BG (certainly bg)"),
    ]
    fig.legend(handles=vessel_legend, loc="lower center", ncol=3,
               fontsize=7.5, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(bottom=0.09, wspace=0.05, hspace=0.06,
                        left=0.05, right=0.99, top=0.93)
    _save(fig, "fig_vessels")


# ---- Fig decoupling (V2): per-image Dice vs certified quantities ----------
def fig_decoupling():
    """Cross-domain (DRIVE + CHASE_DB1) scatter of per-image Dice against each
    certified quantity, primary (cbrt) normalisation. The honest, mixed
    story: coverage tracks Dice on both sets; the topological invariants
    scatter on DRIVE but slope up on CHASE's degenerate over-segmented maps
    (Dice~0.30). Spearman rho annotated per dataset."""
    drive = json.loads((EXP / "results_drive.json").read_text())
    chase = json.loads((EXP / "results_chase.json").read_text())
    qu_keys = [("coverage", "coverage (accuracy-linked)"),
               ("conn_seg_frac", "certified-connected fraction"),
               ("n_components", "certified $\\beta_0$ components"),
               ("n_cycles", "certified $\\beta_1$ cycles")]
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.0))
    for ax, (k, title) in zip(axes.ravel(), qu_keys):
        for res, name, color, marker in (
                (drive, "DRIVE", BLUE, "o"), (chase, "CHASE", VERM, "D")):
            per = res["per_transform"]["cbrt"]["per_image"]
            x = [r["dice"] for r in per]
            y = [r[k] for r in per]
            rho = res["per_transform"]["cbrt"]["spearman_dice_vs"][k]
            sig = "*" if rho["p_value"] < 0.05 else ""
            ax.scatter(x, y, s=22, c=color, marker=marker, alpha=0.75,
                       edgecolors="white", linewidths=0.4,
                       label=f"{name}: $\\rho$={rho['rho']:+.2f}{sig}")
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("per-image Dice", fontsize=8)
        ax.legend(fontsize=7, frameon=False, loc="best")
        ax.tick_params(labelsize=7)
    fig.suptitle("Certified quantities vs.\\ Dice across two retinal datasets "
                 "(cbrt; $*$ = $p<0.05$)", fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    _save(fig, "fig_decoupling")


if __name__ == "__main__":
    FIGS.mkdir(exist_ok=True)
    fig_sweep()
    fig_counterexample()
    fig_pinch()
    fig_tightness()
    fig_anatomy()
    fig_gallery()
    fig_pipeline()
    fig_decoupling()
    fig_worstcrop()
    fig_hero()
    fig_vessels()
