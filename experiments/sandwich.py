"""INTACT sandwich: from soft grout map p and l-inf budget eps, the
certified interval field and the CERT_FG / CERT_BG / POSSIBLE partition.

Soundness rests on thresholding being a MONOTONE operation whose interval
propagation is ENDPOINT-EXACT (exactness gap 1.000, i.e. the propagated
interval is attained): the reachable set of binary masks under an
l-inf-eps perturbation of p is exactly
{ M : CERT_FG subset-of M subset-of ~CERT_BG }.

The [lo,hi] field is computed directly in numpy. Float error is handled by
optional PEDANTIC outward rounding (one ulp each way), so rounding can only
WIDEN the interval - never shrink a certified set, which would be unsound.
"""
import numpy as np

THRESH = 0.5


def interval_field(p, eps, pedantic=True):
    """lo=clip(p-eps), hi=clip(p+eps). PEDANTIC widens outward by one ulp
    so float rounding can only widen, never shrink, the certified sets."""
    lo = np.clip(p - eps, 0.0, 1.0).astype(np.float64)
    hi = np.clip(p + eps, 0.0, 1.0).astype(np.float64)
    if pedantic:
        lo = np.nextafter(lo, -np.inf)
        hi = np.nextafter(hi, np.inf)
    return lo, hi


def cert_sets(p, eps, pedantic=True):
    """Returns dict with boolean CERT_FG, CERT_BG, POSSIBLE (grout=fg)."""
    lo, hi = interval_field(p, eps, pedantic)
    # The asymmetry (> vs <=) is FORCED by the mask rule M = {p' > THRESH} and
    # is not a blemish to "fix": a pixel is certainly foreground iff its lower
    # endpoint clears the strict threshold, and certainly background iff its
    # upper endpoint p+eps fails to, i.e. p+eps <= THRESH. With < instead, a
    # pixel at the exact tie p+eps == THRESH would be called POSSIBLE despite
    # being unable to cross the threshold, which is what made Proposition 1
    # exact only up to ties. Reverting either comparison breaks that exactness.
    cert_fg = lo > THRESH          # certainly grout under any perturbation
    cert_bg = hi <= THRESH         # certainly background (sup p' = p+eps <= 1/2)
    possible = ~cert_fg & ~cert_bg
    return {"CERT_FG": cert_fg, "CERT_BG": cert_bg, "POSSIBLE": possible,
            "lo": lo, "hi": hi}


def reachable_fg(sets, choice):
    """A reachable foreground mask M: CERT_FG forced fg, CERT_BG forced bg,
    POSSIBLE pixels set by `choice` (a bool field, adversary's move).
    CERT_FG subset-of M subset-of ~CERT_BG holds by construction."""
    return sets["CERT_FG"] | (sets["POSSIBLE"] & choice)


def useful_eps(p, quantile=0.5):
    """Calibration-defined 'useful' eps = a quantile of the confidence
    margin |p-0.5| over uncertain pixels (temperature-free proxy). Stated
    in RESULTS so eps is not invented."""
    margin = np.abs(p - 0.5)
    m = margin[(margin > 0) & (margin < 0.5)]
    return float(np.quantile(m, quantile)) if m.size else 0.1
