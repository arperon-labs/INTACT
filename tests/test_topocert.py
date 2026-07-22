"""topocert tests (CPU, fast). The planted-unsound test is the important
one: the soundness harness MUST catch a certificate that can break."""
import sys
from pathlib import Path

import numpy as np
import pytest

# RELEASE ADAPTATION - tests/ and experiments/ are siblings here; do not
# sync this file by wholesale copy or every import breaks.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

from sandwich import cert_sets, reachable_fg  # noqa: E402
from topo import certified_topology, soundness_check  # noqa: E402
from persistence import certified_cycle_count, HAVE_GUDHI  # noqa: E402
from connectivity import connectivity_certificate, segments, skeleton  # noqa: E402


def _roi(shape):
    return np.ones(shape, bool)


class TestSandwich:
    def test_containment_exhaustive(self):
        # CERT_FG subset-of any in-band threshold subset-of ~CERT_BG
        rng = np.random.default_rng(0)
        p = rng.random((16, 16)).astype(np.float32)
        eps = 0.15
        s = cert_sets(p, eps)
        for _ in range(200):
            choice = rng.random(p.shape) < rng.uniform(0, 1)
            M = reachable_fg(s, choice)
            assert (s["CERT_FG"] & ~M).sum() == 0        # CERT_FG in M
            assert (M & s["CERT_BG"]).sum() == 0         # M avoids CERT_BG

    def test_monotone_nesting(self):
        rng = np.random.default_rng(1)
        p = rng.random((32, 32)).astype(np.float32)
        s_small = cert_sets(p, 0.05)
        s_big = cert_sets(p, 0.2)
        # smaller eps -> MORE certified (nested)
        assert s_small["CERT_FG"].sum() >= s_big["CERT_FG"].sum()
        assert (s_big["CERT_FG"] & ~s_small["CERT_FG"]).sum() == 0


class TestCertifiedTopology:
    def test_ring_cycle(self):
        # a thick ring (one robust 1-cycle) with confident p
        H = 64
        yy, xx = np.mgrid[:H, :H]
        r = np.sqrt((yy - 32) ** 2 + (xx - 32) ** 2)
        ring = (r > 18) & (r < 26)                        # grout ring
        p = np.where(ring, 0.95, 0.05).astype(np.float32)
        ct = certified_topology(p, 0.1, _roi((H, H)), 3.0)
        assert ct["n_certified_cycles"] >= 1              # loop certified
        assert ct["n_certified_components"] >= 1


class TestCycleSoundness:
    """Regression for the unsoundness caught by adversarial review: betti1
    (CERT_FG) certified a ring around POSSIBLE that the adversary can fill."""

    def _ring(self, interior_p):
        H = 40
        yy, xx = np.mgrid[:H, :H]
        r = np.sqrt((yy - 20) ** 2 + (xx - 20) ** 2)
        ring = (r > 8) & (r < 14)
        p = np.full((H, H), 0.05, np.float32)      # outside = CERT_BG
        p[ring] = 0.95                             # wall = CERT_FG
        p[r <= 8] = interior_p                     # interior
        return p

    def test_hole_over_CERTBG_is_certified_and_sound(self):
        p = self._ring(0.05)                       # interior CERT_BG -> unfillable
        ct = certified_topology(p, 0.1, _roi(p.shape), 2.0)
        assert ct["n_certified_cycles"] >= 1
        cy = [{**c, "kind": "cycle"} for c in ct["cycles"]]
        v, ch = soundness_check(p, 0.1, cy, n_samples=16)
        assert v == 0 and ch > 0                   # sound

    def test_hole_over_POSSIBLE_is_NOT_certified(self):
        # the exact adversarial counterexample: ring around POSSIBLE interior.
        p = self._ring(0.5)                        # interior POSSIBLE (fillable)
        ct = certified_topology(p, 0.1, _roi(p.shape), 2.0)
        assert ct["n_certified_cycles"] == 0       # correctly NOT certified now

    def test_planted_unsound_cycle_is_caught(self):
        # force a 'cycle' whose interior is POSSIBLE -> adversary fills it.
        p = self._ring(0.5)
        H = p.shape[0]
        yy, xx = np.mgrid[:H, :H]
        core = np.sqrt((yy - 20) ** 2 + (xx - 20) ** 2) <= 6   # POSSIBLE interior
        v, ch = soundness_check(p, 0.1, [{"support": core, "kind": "cycle"}],
                                n_samples=8)
        assert v > 0                               # caught

    def test_two_cores_one_wall_enclosure_exceeds_persistence(self):
        """H-C4 (registered as an equivalence) is REFUTED here, and the case is
        pinned so it cannot regress back into an identity claim.

        One CERT_FG annulus whose interior holds TWO CERT_BG squares split by a
        POSSIBLE channel: the enclosure form counts two guaranteed-background
        regions, while the image rank is 1 because beta1(CERT_FG) = 1 and the
        annulus generator maps to the SUM of the two blob classes. No ROI or
        scale-floor filtering is involved -- the two forms simply answer
        different questions. See REGISTRY.md Correction Addendum 2.

        BOTH counts are sound; only their identification was wrong."""
        H = 40
        p = np.full((H, H), 0.5, np.float32)       # default POSSIBLE at eps=0.1
        p[5:35, 5:35] = 0.95                       # solid block -> wall...
        p[8:32, 8:32] = 0.5                        # ...hollowed to an annulus
        p[8:32, 8:19] = 0.05                       # CERT_BG square A
        p[8:32, 21:32] = 0.05                      # CERT_BG square B
        # cols 19-20 stay 0.5 -> a 2 px POSSIBLE channel between A and B

        s = cert_sets(p, 0.1)
        ct = certified_topology(p, 0.1, _roi(p.shape), 3.0)
        n_encl = ct["n_certified_cycles"]
        n_pers, avail = certified_cycle_count(s["CERT_FG"], s["CERT_BG"])

        assert n_encl == 2, f"enclosure should see two regions, got {n_encl}"
        if avail:                                  # gudhi present
            assert n_pers == 1, f"image rank should be 1, got {n_pers}"
            assert n_encl > n_pers                 # the refuting direction

        # Both remain SOUND: the enclosure regions survive both extremes.
        cy = [{**c, "kind": "cycle"} for c in ct["cycles"]]
        v, ch = soundness_check(p, 0.1, cy, n_samples=16)
        assert v == 0 and ch > 0


class TestSoundness:
    def test_genuine_certificate_zero_violations(self):
        # a confident grid: grout lines every 12 px -> certified grout comps
        # + certified tessera cores.
        H = 72
        grout = np.zeros((H, H), bool)
        grout[::12, :] = True; grout[:, ::12] = True
        grout[3:5, :] = True                              # thick lines
        grout[:, 3:5] = True
        p = np.where(grout, 0.95, 0.05).astype(np.float32)
        ct = certified_topology(p, 0.1, _roi((H, H)), 2.0)
        assert (ct["n_certified_components"] >= 1
                or ct["n_certified_tesserae"] >= 1)
        classes = ([{**c, "kind": "fg"} for c in ct["components"]]
                   + [{**t, "kind": "bg"} for t in ct["tesserae"]])
        v, ch = soundness_check(p, 0.1, classes, n_samples=32)
        assert v == 0 and ch > 0                          # genuine -> sound

    def test_planted_unsound_is_caught(self):
        # a 'certified' FG class whose support intrudes into POSSIBLE ->
        # the adversary (all-POSSIBLE-bg) breaks it -> MUST be flagged.
        H = 40
        p = np.full((H, H), 0.5, np.float32)              # all POSSIBLE
        p[10:14, 5:35] = 0.95                             # a confident bar
        s = cert_sets(p, 0.1)
        bar = np.zeros((H, H), bool); bar[10:14, 5:35] = True
        intrude = bar.copy(); intrude[10:14, 35:38] = True  # into POSSIBLE
        classes = [{"support": intrude, "kind": "fg"}]
        v, ch = soundness_check(p, 0.1, classes, n_samples=8)
        assert v > 0                                      # caught, as required

    def test_planted_bg_unsound_caught(self):
        H = 40
        p = np.full((H, H), 0.5, np.float32)
        p[5:35, 5:9] = 0.05                               # confident bg strip
        core = np.zeros((H, H), bool); core[5:35, 5:9] = True
        core[5:35, 9:12] = True                           # intrude POSSIBLE
        classes = [{"support": core, "kind": "bg"}]
        v, ch = soundness_check(p, 0.1, classes, n_samples=8)
        assert v > 0


class TestPersistenceEquivalence:
    """Track-1a H-C4: gudhi image-persistence cycle count EQUALS the corrected
    enclosure count on the three regression cases (and a grid of holes)."""

    def _ring(self, interior_p, H=40):
        yy, xx = np.mgrid[:H, :H]
        r = np.sqrt((yy - 20) ** 2 + (xx - 20) ** 2)
        ring = (r > 8) & (r < 14)
        p = np.full((H, H), 0.05, np.float32)
        p[ring] = 0.95
        p[r <= 8] = interior_p
        return p

    def test_gudhi_available(self):
        assert HAVE_GUDHI, "gudhi must be installed (Track-1a); no silent proxy"

    def test_ring_over_CERTBG_persistence_eq_enclosure(self):
        p = self._ring(0.05)                              # unfillable hole
        s = cert_sets(p, 0.1)
        pers, ok = certified_cycle_count(s["CERT_FG"], s["CERT_BG"])
        ct = certified_topology(p, 0.1, np.ones(p.shape, bool), 1.0)
        assert ok and pers == 1 and ct["n_certified_cycles"] == 1

    def test_ring_over_POSSIBLE_persistence_zero(self):
        p = self._ring(0.5)                               # fillable -> not certified
        s = cert_sets(p, 0.1)
        pers, ok = certified_cycle_count(s["CERT_FG"], s["CERT_BG"])
        ct = certified_topology(p, 0.1, np.ones(p.shape, bool), 1.0)
        assert ok and pers == 0 and ct["n_certified_cycles"] == 0

    def test_grid_of_holes_persistence_eq_enclosure(self):
        # 3x3 confident tessera cells -> 9 unfillable holes (walls CERT_FG,
        # cores CERT_BG). persistence count must equal enclosure count.
        H = 84
        grout = np.zeros((H, H), bool)
        for k in range(0, H, 20):
            grout[k:k + 4, :] = True
            grout[:, k:k + 4] = True
        p = np.where(grout, 0.95, 0.05).astype(np.float32)
        s = cert_sets(p, 0.1)
        pers, ok = certified_cycle_count(s["CERT_FG"], s["CERT_BG"])
        ct = certified_topology(p, 0.1, np.ones(p.shape, bool), 1.0)
        assert ok and pers == ct["n_certified_cycles"] and pers >= 4


class TestConnectivityCertificate:
    """Track-1b: a segment fully in CERT_FG is certified-connected (sound); a
    POSSIBLE pinch breaks it (not certified, and a claim of it is caught)."""

    def _bar(self, pinch):
        H, W = 30, 60
        p = np.full((H, W), 0.05, np.float32)
        p[13:17, 5:55] = 0.95                             # confident grout bar
        if pinch:
            p[13:17, 29:31] = 0.55                        # grout (p>0.5) but
            # within eps of 0.5 -> POSSIBLE, not CERT_FG: a real pinch
        return p

    def test_full_bar_certified_and_sound(self):
        p = self._bar(pinch=False)
        roi = np.ones(p.shape, bool)
        s = cert_sets(p, 0.1)
        conn = connectivity_certificate(p, s["CERT_FG"], roi)
        assert conn["certified_len_frac"] == 1.0 and conn["n_certified_segments"] >= 1
        cls = [{"support": sup, "kind": "connectivity"} for sup in conn["segments"]]
        v, ch = soundness_check(p, 0.1, cls, n_samples=16)
        assert v == 0 and ch > 0

    def test_pinched_bar_not_certified(self):
        p = self._bar(pinch=True)
        roi = np.ones(p.shape, bool)
        s = cert_sets(p, 0.1)
        conn = connectivity_certificate(p, s["CERT_FG"], roi)
        # coverage stays high (only 2 px lost) but connectivity drops: the
        # spanning segment is disqualified by the pinch.
        assert conn["coverage_frac"] > conn["certified_len_frac"]
        assert conn["certified_len_frac"] < 1.0

    def test_pinch_claim_is_caught(self):
        # claim the WHOLE pinched bar skeleton as a certified-connected segment
        # -> soundness check (all-POSSIBLE->bg) must flag it.
        p = self._bar(pinch=True)
        sk = skeleton((p > 0.5) & np.ones(p.shape, bool))
        # skeleton of the pinched bar won't cross the gap; claim the full bar
        span = np.zeros(p.shape, bool); span[14, 5:55] = True
        v, ch = soundness_check(p, 0.1, [{"support": span, "kind": "connectivity"}],
                                n_samples=8)
        assert v > 0


class TestIntervalField:
    """H-F1 (registered): cert_sets accepts a per-pixel eps FIELD with
    per-pixel semantics — the Prop 1' interval-field remark is code-true."""

    def test_eps_field_matches_per_pixel_scalar(self):
        rng = np.random.default_rng(7)
        p = rng.random((16, 16)).astype(np.float32)
        e = rng.uniform(0.02, 0.4, p.shape).astype(np.float32)
        s = cert_sets(p, e)
        for (i, j) in [(0, 0), (3, 7), (8, 2), (15, 15), (5, 11), (12, 4)]:
            sij = cert_sets(p[i:i + 1, j:j + 1], float(e[i, j]))
            assert s["CERT_FG"][i, j] == sij["CERT_FG"][0, 0]
            assert s["CERT_BG"][i, j] == sij["CERT_BG"][0, 0]
            assert s["POSSIBLE"][i, j] == sij["POSSIBLE"][0, 0]

    def test_eps_field_full_grid(self):
        rng = np.random.default_rng(8)
        p = rng.random((12, 12)).astype(np.float32)
        e = rng.uniform(0.02, 0.4, p.shape).astype(np.float32)
        s = cert_sets(p, e)
        ref_fg = np.zeros_like(p, bool)
        ref_bg = np.zeros_like(p, bool)
        for (i, j), eij in np.ndenumerate(e):
            sij = cert_sets(p[i:i + 1, j:j + 1], float(eij))
            ref_fg[i, j] = sij["CERT_FG"][0, 0]
            ref_bg[i, j] = sij["CERT_BG"][0, 0]
        assert np.array_equal(s["CERT_FG"], ref_fg)
        assert np.array_equal(s["CERT_BG"], ref_bg)


class TestPmapResume:
    """--from-pmaps crash-recovery (Piece 1): saved p maps round-trip
    byte-identically and in the requested order, and a missing map fails loudly
    instead of silently under-running the study."""

    def test_roundtrip_identical(self, tmp_path):
        import run
        rng = np.random.default_rng(3)
        saved = {}
        for name in ("crop_a", "crop_b"):
            p = rng.random((8, 8)).astype(np.float32)
            np.save(tmp_path / f"{name}.npy", p)
            saved[name] = p
        data = run._load_pmaps_from(tmp_path, ["crop_a", "crop_b"])
        assert [n for n, _ in data] == ["crop_a", "crop_b"]
        for name, p in data:
            assert p.dtype == np.float32
            assert np.array_equal(p, saved[name])          # byte-identical
        # order follows the requested names, not the directory listing
        rev = run._load_pmaps_from(tmp_path, ["crop_b", "crop_a"])
        assert [n for n, _ in rev] == ["crop_b", "crop_a"]

    def test_missing_pmap_raises(self, tmp_path):
        import run
        np.save(tmp_path / "crop_a.npy", np.zeros((4, 4), np.float32))
        with pytest.raises(SystemExit):
            run._load_pmaps_from(tmp_path, ["crop_a", "crop_b"])   # b missing
