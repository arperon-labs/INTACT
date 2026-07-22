"""TOPOCERT Track-1b: CONNECTIVITY certificate (honest upgrade of coverage).

Coverage ("certainly-foreground fraction") says grout pixels are certainly
grout under any ε-perturbation, but a CERT_FG-covered grout line PINCHED by a
POSSIBLE pixel can still be broken — coverage is NOT connectivity. This adds
the strict predicate:

  A grout skeleton SEGMENT (a path between two junction/endpoint nodes) is
  CERTIFIED-CONNECTED iff EVERY pixel on it lies in CERT_FG. Then in every
  reachable mask CERT_FG ⊆ M the whole segment is foreground, so its two
  endpoints stay connected under ANY ε-perturbation. A single POSSIBLE pixel
  anywhere on the segment disqualifies it (that pixel can go background,
  splitting the line).

Reported ALONGSIDE coverage (never replacing it); expected LOWER. Absolute
companion: both a fraction and absolute segment/length counts.
Soundness is enforced via topo.soundness_check(kind='connectivity') on the
certified segment supports (worst case = all-POSSIBLE→background).
"""
import numpy as np
from scipy import ndimage as ndi
from skimage.morphology import skeletonize

_S8 = np.ones((3, 3), np.uint8)


def skeleton(p_bin_roi):
    return skeletonize(p_bin_roi)


def _degree(sk):
    """8-neighbour count within the skeleton (excludes self)."""
    return (ndi.convolve(sk.astype(np.uint8), _S8, mode="constant") - sk) * sk


def _segments_ref(sk):
    """Reference (pre-2026-07-17) implementation: full-image masks and an
    O(n_seg * n_node) node-matching scan. Correct but quadratic — retained
    ONLY as the byte-identical oracle for the fast `segments()` below
    (validate_connectivity_fastpath.py). Do not call in production."""
    deg = _degree(sk)
    nodes = sk & (deg != 2)                       # junctions, endpoints, isolated
    interior = sk & (deg == 2)
    lbl, n = ndi.label(interior, structure=_S8)
    segs = []
    for i in range(1, n + 1):
        interi = lbl == i
        grown = ndi.binary_dilation(interi, _S8) & nodes
        segs.append(interi | grown)
    node_lbl, node_lbl_n = ndi.label(nodes, structure=_S8)
    for i in range(1, node_lbl_n + 1):
        comp = node_lbl == i
        if comp.sum() >= 2 and not any((s & comp).any() for s in segs):
            segs.append(comp)
    return segs


def segments(sk):
    """Split the skeleton graph into segments between nodes (junctions deg≥3
    / endpoints deg 1). Each segment = its degree-2 interior plus the node
    pixels it touches; degenerate node-to-node adjacencies (no interior) are
    recovered as isolated node pairs.

    Near-linear equivalent of `_segments_ref` (byte-identical support set,
    same order). Two changes that make it scale to dense skeletons without
    altering the result:
      * each interior segment is grown/emitted inside its bounding box
        (`find_objects`) instead of over the whole image;
      * the O(n_seg * n_node) "is this node cluster touched by any segment?"
        scan collapses to ONE dilation `touched = dilate(interior) & nodes`
        plus a per-node-label sum — because a node pixel joins segment i iff
        it is 8-adjacent to interior i, so a node cluster is untouched iff it
        meets no dilated-interior pixel.
    Returns a list of (bbox_slices, local_bool_mask) so callers can test/
    materialise each segment in its own window rather than full-frame."""
    deg = _degree(sk)
    nodes = sk & (deg != 2)
    interior = sk & (deg == 2)
    lbl, n = ndi.label(interior, structure=_S8)
    out = []
    if n:
        slices = ndi.find_objects(lbl)
        for i in range(1, n + 1):
            sl = slices[i - 1]
            if sl is None:
                continue
            # pad by 1 so the 8-dilation stays inside the sub-window
            sl2 = tuple(slice(max(0, s.start - 1), min(dim, s.stop + 1))
                        for s, dim in zip(sl, sk.shape))
            interi = lbl[sl2] == i
            grown = ndi.binary_dilation(interi, _S8) & nodes[sl2]
            out.append((sl2, interi | grown))
    # node-node segments: node clusters (size>=2) meeting no dilated interior
    node_lbl, node_lbl_n = ndi.label(nodes, structure=_S8)
    if node_lbl_n:
        touched = ndi.binary_dilation(interior, _S8) & nodes
        flat = node_lbl.ravel()
        sizes = np.bincount(flat, minlength=node_lbl_n + 1)
        touch = np.bincount(flat, weights=touched.ravel().astype(np.float64),
                            minlength=node_lbl_n + 1)
        nslices = ndi.find_objects(node_lbl)
        for i in range(1, node_lbl_n + 1):
            if sizes[i] >= 2 and touch[i] == 0:
                sl = nslices[i - 1]
                out.append((sl, node_lbl[sl] == i))
    return out


def connectivity_certificate(p, cert_fg, roi):
    """Both metrics on the p-skeleton restricted to ROI.

    coverage_frac        = |skeleton ∩ CERT_FG| / |skeleton|      (unchanged)
    certified_seg_frac   = #segments fully in CERT_FG / #segments
    certified_len_frac   = certified segment length / total segment length
    Returns dict incl. absolute counts and the certified segment supports
    (full-image masks, for the soundness check). Only certified segments are
    materialised full-frame — the (bbox, local-mask) form keeps the dense
    case from allocating thousands of full images."""
    sk = skeleton((p > 0.5) & roi)
    sk_len = int(sk.sum())
    if sk_len == 0:
        return {"coverage_frac": 1.0, "certified_seg_frac": 1.0,
                "certified_len_frac": 1.0, "n_segments": 0,
                "n_certified_segments": 0, "sk_len": 0,
                "cert_len": 0, "segments": []}
    cert_supports, n_seg, n_cert, cert_len, tot_len = [], 0, 0, 0, 0
    for sl, loc in segments(sk):
        L = int(loc.sum())
        tot_len += L
        n_seg += 1
        if cert_fg[sl][loc].all():                # every pixel guaranteed fg
            n_cert += 1
            cert_len += L
            full = np.zeros_like(sk)
            full[sl] = loc
            cert_supports.append(full)
    coverage = float((sk & cert_fg).sum()) / sk_len
    return {"coverage_frac": coverage,
            "certified_seg_frac": (n_cert / n_seg) if n_seg else 1.0,
            "certified_len_frac": (cert_len / tot_len) if tot_len else 1.0,
            "n_segments": n_seg, "n_certified_segments": n_cert,
            "sk_len": sk_len, "cert_len": cert_len,
            "segments": cert_supports}
