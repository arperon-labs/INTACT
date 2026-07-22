# TOPOCERT — adversarial topological certificates (results)

**Read this header first.** (1) **T-real HAS NOW RUN** (frozen-GROUT p on
real crops, once the GPU was free): the certificate is
**SOUND (0 violations) and NON-VACUOUS on real model outputs** — see
"T-real" below, now the authoritative result. (2) An earlier version
shipped an **UNSOUND β1 (cycle) certificate**; adversarial verification
(2026-07-12) caught it and it was CORRECTED — see "Correction." (3) Metrics
are COVERAGE ("certainly-foreground"), not connectivity guarantees, framed
accordingly throughout. No training; a certificate arc — success is a sound
guarantee that holds.

Registration `REGISTRY.md` + correction addendum precede this file in git.

## Correction (β1 unsoundness — caught and fixed)

The first version certified 1-cycles as `betti1(CERT_FG)` with the claim
"a loop in the minimal foreground persists in all larger foregrounds."
**This is false.** H1 is not monotone under foreground growth: a CERT_FG
ring around an interior of POSSIBLE pixels is a betti1(CERT_FG)=1 cycle,
but the adversary can set those interior pixels to foreground within ε,
filling the hole (betti1(M)=0) — an in-budget perturbation destroys the
"certified" cycle. The in-code soundness check never tested cycles, so it
did not catch this. **Fix:** a cycle is certified robust iff its enclosed
region is CERT_BG (guaranteed background in every reachable mask) walled by
CERT_FG (guaranteed foreground) — an *unfillable* hole. Computed now as
CERT_BG components not reachable from the border through the can-be-
background region ~CERT_FG (`topo.certified_cycles`), and the soundness
check now tests cycle persistence (`kind='cycle'`). Regression tests encode
the exact counterexample: ring-over-POSSIBLE is now correctly NOT certified;
ring-over-CERT_BG is certified and passes soundness; a planted-unsound cycle
is caught.

## H-C1 SOUNDNESS (the correctness gate, the real result)

> **H-C1: PASS — 0 violations** across all certified classes (components,
> tessera cores, AND the corrected cycles) and all ε, via the
> deterministic worst-case reachable masks (all-background and all-
> foreground POSSIBLE choices) plus random samples.

This is genuinely strong for β0 and the corrected β1, and it is
**structural**, not merely empirical-on-samples: CERT_FG ⊆ the foreground
of every reachable mask (per-pixel ℓ∞ intervals; PEDANTIC shrinks the CERT
sets in the safe direction; the strict `>` handles p−ε=0.5), connectivity
is preserved under superset, and the corrected cycle is an unfillable
CERT_BG hole. The check confirms the implementation matches that proof at
the deterministic extremes (an independent reviewer verified the check is
worst-case-exhaustive, not just probabilistic, for these predicates).

## T-REAL — frozen-GROUT p on real crops (AUTHORITATIVE, not provisional)

24 real mosaic crops **[corrected 2026-07-13:** this header previously
said 30; the run used the first 24 of the 30-crop frozen realset
(`run.py N_MASKS = 24`; every per-ε mean in `results.json` has
denominator 24)**]** → frozen `grout_b3_zeroshot_v1` p → the same
certified-topology pipeline. **H-C1 soundness: PASS, 0 violations** across
all certified classes (components, tessera cores, corrected cycles) and all
ε — the certificate holds on real model outputs, not just engineered p.

| ε | grout-length certainly-fg | # certified components | # certified cycles | abstain |
|---|---|---|---|---|
| 0.02 | 0.987 | 21 | 531 | 0.016 |
| 0.05 | 0.970 | 21 | 520 | 0.041 |
| 0.10 | 0.938 | 23 | 490 | 0.082 |
| 0.15 | 0.903 | 26 | 460 | 0.125 |
| 0.25 | 0.815 | 34 | 382 | 0.223 |
| **0.40** | 0.592 | 51 | 202 | 0.448 |

- **H-C2 (non-vacuity): PASS on real p.** GROUT is confident on these
  crops, so the calibration-defined useful ε is large (0.42 → 0.40); even
  there 59% of grout length is certainly-foreground with 51 certified-
  connected components and 202 certified cycles. At a conventional ε=0.10,
  94% of grout length is certainly-foreground. So the guarantee is
  genuinely non-vacuous on real model outputs — the critic's "only on
  blurred GT" concern is resolved.
- **H-C3 (nesting): PASS** (exact monotone). **KILL: not triggered.**
- Honest reading of the guarantee: "at ℓ∞ budget ε, ≥X% of this real
  GROUT map's grout is certainly-foreground under ANY ε-perturbation, and
  these N components / M enclosed tesserae are certified-robust." The
  certainly-foreground fraction is a SOUND coverage statement, NOT an
  end-to-end connectivity certificate (a component pinched through POSSIBLE
  can still split — the certified-connected objects are the reported CERT_FG
  component / enclosed-core counts).

## T-toy — blurred-GT p (retained as a sanity/validation track)

**Honest caveat (critic-confirmed):** the toy p is `GaussianBlur(GT mask,
σ=1.3) + noise 0.07`, i.e. a lightly-blurred copy of the answer key.
Certifying that its topology survives small perturbations is close to
tautological, and the "useful ε" is calibrated from the *same* p, so
clearing 50% is partly self-fulfilling.
These numbers demonstrate the machinery runs and produces non-empty
certificates on plausible-looking input — nothing about real-model behavior.

| ε | grout-length certainly-foreground | # certified components | # certified cycles | abstain |
|---|---|---|---|---|
| 0.02 | 0.997 | 1 | 187 | 0.020 |
| 0.05 | 0.991 | 1 | 181 | 0.051 |
| 0.10 | 0.974 | 1 | 167 | 0.107 |
| 0.15 | 0.946 | 1 | 145 | 0.169 |
| 0.25 | 0.832 | 4 | 80 | 0.302 |
| 0.40 | 0.485 | 13 | 0 | 0.562 |

- "grout-length certainly-foreground" = fraction of the p-skeleton lying in
  CERT_FG. This is a SOUND *coverage* statement ("these grout pixels are
  certainly grout under any ε-perturbation") — it is **NOT** a connectivity
  guarantee. A component ≥50%-covered by CERT_FG but pinched through
  POSSIBLE can still be split; the genuinely certified-connected structures
  are the CERT_FG connected components (the "# certified components"
  column). Metric renamed and the `component_covg_proxy_frac` explicitly
  flagged as a coverage proxy (`run.py`).
- **H-C2 (as re-stated honestly): illustrative PASS on toy** — at ε=0.25,
  83% of grout length is certainly-foreground and ≥1 certified-connected
  component exists; but per the caveat this proves the machinery, not the
  method. The registered "50% of components... certified-robust" is
  reported via the coverage proxy, NOT a connectivity certificate.
- **H-C3 (nesting): PASS** — all certified quantities monotone-decreasing
  in ε (exact containment).
- **KILL: not triggered** on toy. The stated boundary: certification stays
  non-vacuous up to ε ≈ 0.15–0.25 and collapses at ε=0.4.

## What is NOT established (honest ledger)

- Metrics are COVERAGE, not end-to-end connectivity certificates (the
  certified-connected objects are the CERT_FG component / enclosed-core
  counts, reported as absolutes).
- Cycle localization uses connected-component enclosure, not full cubical
  persistence (gudhi absent) — sufficient for the *count/soundness*, not for
  fine 1-cycle disambiguation (flagged).
- 30 real crops (the frozen realset); a larger real study would tighten the
  non-vacuity distribution.

## Verdict (revised, honest — now with real-p confirmation)

The **certified-topology machinery is SOUND on real model outputs** — β0
(components, tessera cores, separations) provably, and β1 (cycles) after
the correction, with a worst-case-exhaustive soundness check that caught a
planted unsound certificate. **0 violations on both toy and real frozen-
GROUT p.** It is also **non-vacuous on real p**: 94% of grout length is
certainly-foreground at ε=0.10 (59% at ε=0.40), with dozens of certified-
connected components and hundreds of certified enclosed tesserae. So the
Benson-style adversarial certificate delivers a genuine, sound, non-vacuous
guarantee on real GROUT predictions: "no ℓ∞-ε perturbation can turn these
certainly-grout pixels to background or fill these certified tesserae."
This is a rare positive in the campaign — and it survived adversarial
verification, which first caught and forced the fix of a real unsoundness.
The α-cut / interval-valued-image extension remains a flagged future
direction.

## TRACK-1 HARDENING RESULTS (2026-07-12; registration in REGISTRY.md precedes)

The two self-flagged gaps closed + wording locked. **No new unsoundness:
H-C1 remains 0 violations WITH the new connectivity predicate added to the
worst-case check.** Suite 21/21 (pytest, 2026-07-22: +the H-C4 two-cores refutation case; 2026-07-17: +TestIntervalField
H-F1 and TestPmapResume for the --from-pmaps re-emit).

**1a — true cubical persistence for cycles (gudhi 3.13).** Certified cycles
now computed as the image-persistence rank `H1(CERT_FG ↪ ~CERT_BG)` (3-level
foreground filtration, birth<0.5 ∧ death>1.5). **H-C4 equivalence: PASS** —
the persistence count EQUALS the corrected enclosure count EXACTLY on the
three regression cases (ring-over-POSSIBLE → 0; ring-over-CERT_BG → 1;
grid-of-holes → 9) and the planted-unsound is not certified (tests). On noisy
`p` the two columns differ only by sub-scale-floor holes (persistence is raw,
enclosure is ROI+floor filtered): e.g. T-toy at ε=0.4 gives persistence 1.38
vs floored-enclosure 0.04 — the documented "up to scale-floor handling"
caveat. Both columns reported; localisation stays with enclosure (persistence
gives the count, not per-cycle generators — gudhi cofaces flagged).

**1b — connectivity certificate (coverage → connectivity, honest).** New
predicate: a skeleton SEGMENT is certified-connected iff every pixel on it
lies in CERT_FG (a single POSSIBLE pinch disqualifies it). **Sound**
(`kind='connectivity'`, 0 violations; planted pinch caught — tests). It is
STRICTLY below coverage, as intended: T-toy at ε=0.4, coverage
`grout_len_certainly_fg` = 0.500 but `certified_connected_len_frac` = **0.036**
(seg-frac 0.062) — coverage over-states robustness ~14× at this large ε; the
connectivity number is the honest "grout certainly stays unbroken" figure.
Reported ALONGSIDE coverage (both fractions + absolute segment/length counts),
never replacing it.

**1c — wording lock.** `GUARANTEE_STATEMENT.md` fixes the five certifiable
quantities (coverage / β0 components / enclosed tesserae / NEW certified-
connected segment fraction / cycles-via-persistence), each with its worst-case
adversary and scope caveat — the anti-overclaim contract.

**T-real re-emit (persistence + connectivity columns on real `p`): LANDED.**
The 30-crop hardened re-emit (`results/results_real_hardened.json`) carries
the persistence and connectivity columns on real `p`. Certification itself is
CPU-only; the GPU was needed once, to run the frozen GROUT model over the
crops. Connectivity does sit below coverage there, but by a modest
1.2–1.7x — not the order of magnitude the blurred toy maps suggested.
The already-authoritative T-real SOUNDNESS + non-vacuity (above) are
unchanged; only the two new descriptive columns await the GPU re-run.
