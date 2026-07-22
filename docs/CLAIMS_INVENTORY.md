# TOPOCERT paper — CLAIMS INVENTORY (Phase 1; committed before any prose)

Every claim the paper will make, traced to its licensing source. The paper's
abstract and claim sentences may contain ONLY statements licensed here; each
guarantee is stated with its adversary and its caveat, verbatim-equivalent to
`docs/GUARANTEE_STATEMENT.md` (the anti-overclaim contract).

**Source keys**

| Key | File (repo-relative) |
|---|---|
| G | `docs/GUARANTEE_STATEMENT.md` (wording lock, Track-1c) |
| R | `docs/RESULTS.md` (incl. Correction + Track-1 hardening sections) |
| REG | `docs/REGISTRY.md` (registration + correction addendum + hardening registration) |
| J-real | `results/results_real_hardened.json` (T-real, 30 crops, authoritative) |
| J-toy | `results/results_toy.json` (original toy run) |
| J-toy-h | `results/results_toy_hardened.json` (Track-1 toy re-emit: persistence + connectivity columns) |
| CODE | `experiments/{sandwich,topo,persistence,connectivity,run}.py` (definitions; read-only) |
| TESTS | `tests/test_topocert.py` (regression constructions, 20/20 green) |

---

## A. Setting, threat model, sandwich

**A1 — Sandwich definition.** For a frozen soft map `p` and ℓ∞ budget `ε`:
`CERT_FG = {p−ε > ½}`, `CERT_BG = {p+ε < ½}` (PEDANTIC-widened by one ulp
outward so float rounding cannot shrink the certified sets; strict
inequalities handle `p−ε = 0.5`), `POSSIBLE` = complement.
*License:* G "single sentence"; CODE `sandwich.py` (`interval_field`,
`cert_sets`, `THRESH=0.5`).

**A2 — Exact reachable-set characterisation.** The set of binary masks
reachable by thresholding any `p'` with `‖p'−p‖∞ ≤ ε` is exactly
`{M : CERT_FG ⊆ M ⊆ ~CERT_BG}` — thresholding is a monotone op whose
interval propagation is endpoint-exact (exactness gap 1.000 — the
propagated interval is attained). The `[lo,hi]` field is computed directly
in numpy with outward rounding; see `experiments/sandwich.py`.
*License:* REG Concept; CODE `sandwich.py` docstring. The paper may restate
this with a short self-contained proof (both directions are elementary); the
proof adds no new claim.

**A3 — Threat model precision (HARD RULE).** The certificate operates on
perturbations of the SCORE MAP `p` (ℓ∞ at the map level). It is NOT an
end-to-end input-space certificate. Composition with pixelwise input-space
certification (randomized smoothing / IBP supplying per-pixel map-level
bounds) is an interface + future work — one paragraph, no implied completion.
*License:* G scope ("For a frozen GROUT soft map `p` and an ℓ∞ perturbation
budget `ε`"); session contract. The paper must state this exactly.

**A4 — Main guarantee sentence.** "No ℓ∞-ε perturbation of `p` can move a
CERT_FG pixel out of the grout foreground or a CERT_BG pixel out of the
background", and consequently the five itemised quantities are certified
robust to the entire ε-band — with the honest distinction that *coverage* is
NOT *connectivity*, reported separately, connectivity strictly smaller.
*License:* G "The single sentence the paper may claim" (verbatim-equivalent
only).

## B. The five certified quantities (each with adversary + caveat — G items 1–5)

**B1 — Coverage** (`grout_len_certainly_fg_frac`): fraction of the p-skeleton
lying in CERT_FG. Adversary: per-pixel ℓ∞-ε; a CERT_FG pixel is foreground in
every reachable mask. Caveat: a SOUND COVERAGE statement, NOT connectivity —
a covered line pinched through POSSIBLE can still split. Report fraction AND
absolute length. *License:* G item 1.

**B2 — Certified β0 components** (`n_certified_components`): connected
components of CERT_FG (8-conn); each is connected in EVERY reachable mask
(superset preserves connectivity). Caveat: CERT_FG's OWN components (absolute
count), not p's components. *License:* G item 2.

**B3 — Certified enclosed tesserae** (`n_certified_tessera_cores`): connected
components of CERT_BG (4-conn), ROI + scale-floor filtered; each stays fully
background in every reachable mask. Caveat: a tessera CORE, not the whole
tile. *License:* G item 3.

**B4 — Certified-connected grout fraction**
(`certified_connected_seg_frac` / `certified_connected_len_frac`): fraction
of skeleton segments (junction-to-junction) lying ENTIRELY in CERT_FG — such
a segment's endpoints stay connected under ANY ε-perturbation; a single
POSSIBLE pinch disqualifies it. Adversary: all-POSSIBLE→bg
(`kind='connectivity'`, 0 violations). Caveat: strictly ≤ coverage; the
HONEST connectivity number, expected much lower than coverage at large ε.
*License:* G item 4; R Track-1b.

**B5 — Certified 1-cycles** (`n_certified_cycles_persistence`): rank of the
image `H1(CERT_FG ↪ ~CERT_BG)` via cubical persistence (gudhi 3.13; 3-level
filtration CERT_FG=0, POSSIBLE=1, CERT_BG=2; intervals with birth<0.5 ∧
death>1.5). An enclosed hole whose wall is guaranteed foreground and interior
guaranteed background — unfillable and unleakable in every reachable mask.
Adversary: both deterministic extremes (`kind='cycle'`, 0 violations).
Caveat: the raw persistence count is NOT scale-floor/ROI filtered (the
enclosure count `n_certified_cycles_enclosure` is); the two agree EXACTLY on
the clean regression cases (H-C4) and differ on noisy `p` only by
sub-scale-floor holes; cycle LOCALISATION still uses component enclosure.
*License:* G item 5; R Track-1a; REG hardening 1a.

## C. Soundness

**C1 — H-C1: 0 violations.** Across all certified classes (components,
tessera cores, corrected cycles, connectivity segments) and all ε, via the
deterministic worst-case reachable masks (all-POSSIBLE→background and
all-POSSIBLE→foreground) plus random reachable masks. On T-real:
**0 violations / 4,798,656 checks** (LOG line 2). H-C1 remains 0 violations
WITH the Track-1b connectivity predicate added.
*License:* R H-C1 + Track-1 header; LOG; J-real (`H_C1_soundness_violations:
0`); J-toy-h (same).

**C2 — Strength of the check, stated at true strength.** The check is
worst-case-exhaustive at the deterministic extremes for these predicates
(an independent reviewer verified this), and the soundness argument is
STRUCTURAL: CERT_FG ⊆ foreground of every reachable mask; connectivity
preserved under superset; corrected cycle = unfillable CERT_BG hole; PEDANTIC
shrinks CERT sets in the safe direction; strict `>` handles `p−ε = 0.5`.
The check confirms the implementation matches the proof.
*License:* R H-C1 section; G preamble.

**C3 — A planted unsound certificate is caught.** The harness flags planted
unsound fg/bg/cycle/connectivity classes (TESTS: `test_planted_unsound_*`,
`test_pinch_claim_is_caught`). *License:* R Correction; TESTS.

## D. The correction (a section, not a footnote)

**D1 — Original β1 certificate UNSOUND.** As registered, certified 1-cycles
= `betti1(CERT_FG)` with the claim "a loop in the minimal foreground persists
in all larger foregrounds" — FALSE; H1 is not monotone under foreground
growth. Counterexample: a CERT_FG ring around a POSSIBLE interior has
betti1(CERT_FG)=1, but an in-budget perturbation sets the interior to
foreground and fills the hole. *License:* R Correction; REG Correction
addendum.

**D2 — Why the in-code check missed it.** The original H-C1 check never
tested cycles. *License:* R Correction ("The in-code soundness check never
tested cycles, so it did not catch this").

**D3 — The fix.** A cycle is certified robust iff its enclosed region is
CERT_BG walled by CERT_FG (an unfillable hole); computed as CERT_BG
components not reachable from the border through ~CERT_FG; H-C1 extended
with `kind='cycle'`. Regression tests encode the exact counterexample
(ring-over-POSSIBLE → NOT certified; ring-over-CERT_BG → certified + sound;
planted-unsound → caught). *License:* R Correction; TESTS.

**D4 — Provenance of the catch.** Found by adversarial verification
(2026-07-12; two independent soundness reviewers), corrected BEFORE any real-p number was reported.
*License:* REG Correction addendum; G Provenance.

**D5 — Metric-semantics correction.** `certified_component_frac` renamed
`component_covg_proxy_frac` (a p-component ≥50%-covered by CERT_FG is a
COVERAGE proxy, not a connectivity certificate); H-C2 headline softened to
"certainly-foreground coverage". *License:* REG Correction addendum; CODE
`run.py` NOTE.

**D6 — Framing.** Adversarial self-verification is part of the method: a
certificate system that cannot catch a planted unsound certificate should
not be trusted. *License:* session contract framing; supported by C3, D4
(the system did catch it, plus planted-unsound tests).

## E. Experimental results

**E1 — T-real (AUTHORITATIVE).** Frozen `grout_b3_zeroshot_v1` p on real
mosaic crops; the same certified-topology pipeline; H-C1 PASS (0
violations). **Crop count: 24** — `run.py N_MASKS = 24` slices the first 24
of the 30-crop frozen realset, and every J-real mean has denominator 24.
R's header says "30 real mosaic crops"; the paper uses the evidenced 24 and
logs the discrepancy. *License:* J-real; LOG; CODE `run.py`;
realset dir count (30 files).

**E2 — T-real eps-sweep table** (main table; ONLY the columns licensed by
the existing T-real run: coverage, certified components, enclosure-based
certified cycles, abstain — J-real key `n_certified_cycles` is the enclosure
count; the run predates Track-1a/1b):

| ε | coverage | # cert. components | # cert. cycles (enclosure) | abstain |
|---|---|---|---|---|
| 0.02 | 0.987 | 20.9 | 530.8 | 0.016 |
| 0.05 | 0.970 | 21.0 | 519.7 | 0.041 |
| 0.10 | 0.938 | 23.4 | 490.5 | 0.082 |
| 0.15 | 0.903 | 25.9 | 459.6 | 0.125 |
| 0.25 | 0.815 | 34.1 | 382.0 | 0.223 |
| 0.40 | 0.592 | 51.3 | 202.0 | 0.448 |

(Means over 24 crops; tessera-core column also available: 591.3 … 516.1.)
*License:* J-real sweep (exact values); LOG. NOTE: R's table rounds
components/cycles to integers (21/531 etc.); the paper reports one-decimal
means with "mean over 24 crops" stated, which is the exact J-real content.

**E3 — T-real headline readings.** At conventional ε=0.10, 94% of grout
length is certainly-foreground (0.938); at the calibration-defined useful
ε (calibrated 0.418 → swept 0.40), 59% (0.592) with 51.3 certified
components and 202.0 certified cycles (means/24). H-C2 pass: true. KILL
(abstain floods, <10% certified at every useful ε): not triggered.
*License:* J-real `H_C2_nonvacuity_at_useful_eps`, `useful_eps_*`,
`KILL_abstain_floods`; R T-real bullets.

**E4 — H-C3 nesting.** Certificates over decreasing ε are monotone-nested;
asserted exact (containment); PASS on T-real and T-toy(-hardened).
*License:* J-real / J-toy / J-toy-h `H_C3_nesting_monotone_pass: true`;
R; TESTS `test_monotone_nesting`.

**E5 — T-toy (validation track) + self-fulfilling-calibration caveat
VERBATIM.** Toy p = `GaussianBlur(GT mask, σ=1.3) + noise 0.07` — "a
lightly-blurred copy of the answer key. Certifying that its topology
survives small perturbations is close to tautological, and the 'useful ε'
is calibrated from the *same* p, so clearing 50% is partly self-fulfilling.
These numbers demonstrate the machinery runs and produces non-empty
certificates on plausible-looking input — nothing about real-model
behavior." *License:* R T-toy caveat (must appear verbatim-equivalent);
CODE `run.py` `toy_masks`.

**E6 — T-toy hardened table** (the toy table the paper prints — it carries
the Track-1 persistence + connectivity columns; means over 24 synthetic
maps, J-toy-h exact):

| ε | coverage | conn-len | conn-seg | # comp | # tesserae | cycles-encl | cycles-pers | abstain |
|---|---|---|---|---|---|---|---|---|
| 0.02 | 0.996 | 0.971 | 0.969 | 0.7 | 185.8 | 151.7 | 214.6 | 0.019 |
| 0.05 | 0.990 | 0.925 | 0.926 | 0.6 | 180.4 | 146.4 | 203.1 | 0.048 |
| 0.10 | 0.974 | 0.842 | 0.854 | 0.6 | 169.4 | 135.1 | 184.0 | 0.101 |
| 0.15 | 0.945 | 0.752 | 0.773 | 0.8 | 157.0 | 117.7 | 152.0 | 0.159 |
| 0.25 | 0.841 | 0.572 | 0.598 | 3.5 | 134.6 | 71.1 | 73.3 | 0.284 |
| 0.40 | 0.500 | 0.036 | 0.062 | 18.1 | 28.2 | 0.04 | 1.375 | 0.536 |

*License:* J-toy-h sweep (exact). NOTE: the original J-toy table printed in
R (0.485 at ε=0.4, cycles 187→0, useful ε 0.25 with 0.832 coverage and H-C2
illustrative pass) is a DIFFERENT run (pre-hardening, no gudhi/connectivity
columns; regenerated masks). The paper prints the hardened table only and
says so; it does not mix runs. J-toy-h's own `H_C2` at its useful ε (0.40)
is `pass: false` (coverage 0.4998 < 0.5) — if the paper mentions toy H-C2 at
all it reports THIS, framed per E5 as illustrative-only anyway. Deviation
logged in the issue ledger.

**E7 — Coverage vs connectivity contrast (goes in the paper as a feature of
honest reporting).** T-toy-hardened at ε=0.40: coverage 0.500 vs
certified-connected length 0.036 (seg 0.062) — coverage overstates
robustness ~14× at this large ε; the connectivity number is the honest
"grout certainly stays unbroken" figure, reported ALONGSIDE coverage, never
replacing it. **Attribution note:** this 0.500-vs-0.036 example is a TOY
number (J-toy-h; R Track-1b quotes it as "T-toy at ε=0.4"). An earlier internal
note mislabelled it a "real-p example"; the paper attributes it to T-toy.
The real-p connectivity column does not exist yet (E9). *License:* J-toy-h;
R Track-1b.

**E8 — H-C4 persistence≡enclosure.** The persistence count EQUALS the
corrected enclosure count EXACTLY on the regression cases
(ring-over-POSSIBLE → 0; ring-over-CERT_BG → 1; grid-of-holes → 9) and the
planted-unsound is not certified; on noisy p the two differ only by
sub-scale-floor holes (persistence raw, enclosure ROI+floor filtered): T-toy
ε=0.4 persistence 1.375 vs floored-enclosure 0.042 ("1.38 vs 0.04").
*License:* R Track-1a; TESTS `TestPersistenceEquivalence`; J-toy-h.
NOTE: R's prose "grid-of-holes → 9" vs TESTS assertion `pers >= 4` with
equality to enclosure — the 3×3-cell construction has 9 interior holes; the
paper says "a 3×3 grid of holes" and cites the test's exact-equality
assertion; the specific integer 9 is licensed by R.

**E9 — PENDING (hard rule).** The real-p re-emit of the persistence-cycle
and connectivity columns is GPU-deferred (frozen model needs the GPU,
currently on an unrelated workload). Main real-p table carries only
E2-licensed columns; persistence + connectivity appear with toy/engineered-p
validation plus an explicit "[real-p re-emit pending]" marker. No blank
promised numbers. Expected (not claimed): connectivity ≪ coverage on real p
too. *License:* R Track-1 final paragraph.

**E10 — Suite state.** Regression suite 20/20 green.
*License:* R Track-1 header.

## F. Fixed conditions / conventions (part of the certificate definition)

**F1 — ε sweep** {0.02, 0.05, 0.10, 0.15, 0.25, 0.40} (tiny → clearly too
large). *License:* REG Fixed conditions; CODE `run.py EPS_SWEEP`.

**F2 — Connectivity conventions.** 8-connectivity foreground,
4-connectivity background (dual pairing). *License:* REG; G items 2–3.

**F3 — Scale floor + ROI.** Certificates pass an ROI mask and a physical
scale floor (floor = 0.5 × tessera-width scale, tessera width = √median
tessera area, ≥9 px areas, fallback 6.0) so they concern meaningful
structure only; the floor is STATED AS PART OF THE CERTIFICATE DEFINITION.
*License:* REG; CODE `run.py` (`FLOOR_F`, `tessera_w`).

**F4 — Useful-ε calibration.** useful ε = median of the confidence margin
|p−0.5| over uncertain pixels (0 < margin < 0.5), per map, median across
maps, snapped to the nearest swept ε; stated so ε is not invented. T-real:
0.418 → 0.40. *License:* CODE `sandwich.py useful_eps`, `run.py`; J-real.

**F5 — Absolutes rule.** Metrics are ABSOLUTE with companions; ratios never
stand alone. *License:* G "not claimed" list; REG.

**F6 — PEDANTIC float handling.** One-ulp outward widening of [p−ε, p+ε]
(np.nextafter) so rounding cannot enlarge CERT sets; default ON.
*License:* CODE `sandwich.py`; R H-C1 section; G preamble ("PEDANTIC-widened").

## G. What is explicitly NOT claimed (must appear in the paper)

- No end-to-end "the whole grout network certainly stays connected" — only
  the per-segment certified-connected fraction (B4). *License:* G.
- No data-coverage / ground-truth claim — robustness of THIS p to ε, not
  correctness of p. *License:* G.
- No claim on POSSIBLE (abstain) pixels — reported honestly as uncertain.
  *License:* G.
- No end-to-end input-space certificate (A3). *License:* G scope; session
  contract.
- Cycle localisation granularity: persistence gives the count, not
  per-cycle generators; localisation via enclosure. *License:* G item 5
  caveat; R Track-1a.
- Small real study: 24 crops (E1); single task/domain (grout/mosaic
  segmentation, one frozen checkpoint). *License:* R honest ledger
  ("a larger real study would tighten the non-vacuity distribution").

## H. Positioning / related-work claims (position, don't pad)

**H1 — Lineage hook.** Benson (1976) certifies unconditional life in Go via
a monotone fixpoint — an adversarial (not statistical) certificate against
any continuation; TOPOCERT is the same move for segmentation topology.
*License:* REG Concept ("Benson move"); citation identity to be verified
before refs.bib entry (else \citeph).

**H2 — Certified segmentation via randomized smoothing** certifies pixelwise
labels; it is our composition interface (supplier of map-level bounds), not
our competitor. *License:* A3; positioning claim only — no empirical
comparison is claimed.

**H3 — Topology-aware losses/metrics (clDice, Betti matching lineage)** are
training-time objectives/metrics; they improve topology on average but give
no worst-case guarantee. *License:* positioning claim only (no empirical
comparison); citation identities to be verified.

**H4 — Persistence stability / interleaving** bounds diagram distances under
function perturbation — a different guarantee type (metric stability of
diagrams, not certified counts of reachable-mask topology). Image
persistence (Cohen-Steiner et al.) is the tool B5 instantiates on the
cubical pair. *License:* positioning; identity-verify before citing.

**H5 — Abstract-interpretation framing.** The sandwich is an interval
abstraction of the threshold operator, exact for this monotone op (A2).
*License:* framing of A2; cite Cousot & Cousot only if identity verified.

**H6 — α-graded / interval-valued extension** —
flagged future target, mathematical framing only, one paragraph.
*License:* R Verdict; REG deliverables note.

**H7 — AI-involvement disclosure.** Agentic executor + human adjudication +
pre-registration (REGISTRY precedes run.py in git; correction addendum
preserved verbatim); the β1 catch by independent adversarial review.
*License:* REG headers/addendum; D4.

---

## Anti-claims checklist for the abstract (each abstract sentence must map here)

1. Sandwich + exact reachable set → A1, A2.
2. Map-level ℓ∞ threat model, stated exactly → A3.
3. Five certified quantities with adversaries/caveats → B1–B5.
4. Soundness 0 violations incl. worst-case-exhaustive extremes → C1, C2.
5. Correction narrative (unsound β1 caught & fixed) → D1–D6.
6. Non-vacuous on real p: 94% @ ε=0.10, 59% @ ε=0.40, 24 crops → E1–E3.
7. Coverage ≠ connectivity, both reported, 0.500 vs 0.036 (TOY) → E7.
8. Pending real-p re-emit marked → E9.

## ADDENDUM (2026-07-15) — anti-claims

- **Abstention/entropy equivalence (barred as a finding):** for scalar
  binary p, the POSSIBLE band |p−½| ≤ ε is a monotone transform of
  predictive entropy. The abstain map is therefore NEVER to be claimed as
  a novel uncertainty quantifier or compared against entropy thresholding
  as if distinct (§7 states this explicitly). Claimable: only the
  worst-case topological guarantees extracted from the band.
- **β₀ scope (barred over-claim):** quantity 2 certifies the NAMED
  CERT_FG components stay connected; it is NOT a lower bound on β₀ of
  every reachable mask (components can merge through POSSIBLE). The
  image-H0 rank is named in §3.2/§8 as future work — not claimed.
- **Structured adversaries (scope):** sound-but-conservative by
  containment only (§2); exactness claims are confined to the full ℓ∞
  ball. Never claim exact certification for a structured subclass.
- **Generalized interval fields (scope):** Prop 1′ is claimed as theory +
  H-F1 code feasibility; ALL harness numbers exercise the uniform-ε case
  only, and every generalized-form claim must say so (§3.7 does).
