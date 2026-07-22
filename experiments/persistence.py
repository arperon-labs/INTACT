"""TOPOCERT Track-1a: TRUE cubical image-persistence for certified 1-cycles
(replaces the connected-component enclosure proxy; gudhi 3.13).

The certified-cycle count is the rank of the image of
    H1(CERT_FG)  --inclusion-->  H1(~CERT_BG)
i.e. 1-cycles whose WALL is guaranteed foreground (the loop already exists
when only CERT_FG is foreground) AND whose INTERIOR is guaranteed background
(the loop is NOT filled when every POSSIBLE pixel becomes foreground). Such a
hole is present in EVERY reachable mask CERT_FG ⊆ M ⊆ ~CERT_BG — exactly the
sound certified cycle from the β1 correction.

Computed as sublevel cubical persistence of the foreground-growth filtration
    f = 0 on CERT_FG,  1 on POSSIBLE,  2 on CERT_BG
so {f≤0}=CERT_FG, {f≤1}=~CERT_BG, {f≤2}=all. A certified cycle is an H1
interval born at 0 (wall in CERT_FG) that dies at 2 (interior is CERT_BG,
filled only when CERT_BG becomes fg — which never happens in a reachable
mask) — i.e. birth<0.5 and death>1.5. Holes filled by POSSIBLE die at 1
(death<1.5 → not certified); holes needing a POSSIBLE wall are born at 1
(birth>0.5 → not certified).

Registered equivalence H-C4: this count matches the corrected enclosure
count (topo.certified_cycles) on the three regression cases.
"""
import numpy as np

try:
    import gudhi
    HAVE_GUDHI = True
    GUDHI_VERSION = gudhi.__version__
except Exception:                                     # pragma: no cover
    HAVE_GUDHI = False
    GUDHI_VERSION = None


def foreground_filtration(cert_fg, cert_bg):
    """f: CERT_FG=0 (fg from the start), POSSIBLE=1, CERT_BG=2 (never fg in
    any reachable mask). Sublevel sets are the foreground-growth sequence."""
    f = np.ones(cert_fg.shape, dtype=np.float64)      # POSSIBLE = 1
    f[cert_fg] = 0.0
    f[cert_bg] = 2.0
    return f


def certified_cycle_count(cert_fg, cert_bg):
    """Rank of image H1(CERT_FG ↪ ~CERT_BG) = # H1 intervals born in CERT_FG
    (birth<0.5) that survive to ~CERT_BG (death>1.5).

    Returns (count, available). If gudhi is absent → (None, False); callers
    MUST fall back to the enclosure proxy WITH A PROMINENT FLAG."""
    if not HAVE_GUDHI:
        return None, False
    f = foreground_filtration(cert_fg, cert_bg)
    cc = gudhi.CubicalComplex(top_dimensional_cells=f)
    cc.persistence(homology_coeff_field=2, min_persistence=0.0)
    iv = cc.persistence_intervals_in_dimension(1)     # (N,2) birth,death
    if iv.size == 0:
        return 0, True
    births, deaths = iv[:, 0], iv[:, 1]
    certified = int(np.sum((births < 0.5) & (deaths > 1.5)))
    return certified, True
