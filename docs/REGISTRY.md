# TOPOCERT — adversarial topological certificates ("Benson move")
# (registration, committed BEFORE run.py). Additive. SPEC + CPU tests run
# now; the GPU real-p path is behind --gpu-real (default OFF) and MUST NOT
# launch while [internal track] holds the GPU — until then all real
# numbers are PROVISIONAL and the toy track is authoritative. No training.

> **Publication note.** This is the original pre-registration, preserved as
> committed. For public release, references to unrelated internal projects
> have been replaced by `[internal track]`; nothing else — no hypothesis,
> threshold, kill condition, or result — has been altered.

## Concept

Benson (1976) certifies a Go group unconditionally alive under ANY
opponent play via a monotone fixpoint — adversarial, not statistical.
[internal track] died because per-step STATISTICAL certificates break under
adaptive conditioning; the fix is adversarial quantification. Given a soft
grout map p and an l-infinity budget eps, endpoint-exact monotone
interval propagation (PROVEN exact: [internal track] H-A1b, thresholding is a
monotone op, gap 1.000) yields a SANDWICH:
  CERT_FG = {p - eps > 0.5}  (certainly grout under ANY eps-perturbation)
  CERT_BG = {p + eps < 0.5}  (certainly background)
  POSSIBLE = complement (perturbation-sensitive)
and CERT_FG subset-of  every reachable binary mask  subset-of  ~CERT_BG.
Topology present in EVERY reachable mask is certified ROBUST to the whole
eps-band: "no l-inf-eps perturbation can disconnect this grout line or
change this certified tessera count."

## Certified statements (exact, gudhi-free; image-persistence by inclusion)

- **Certified grout components / connectivity** = connected components of
  CERT_FG. Sound BY CONSTRUCTION: CERT_FG subset-of every reachable mask,
  and connectivity is preserved under superset -> a component connected in
  CERT_FG is connected in every reachable mask.
- **Certified tessera cores** = connected components of CERT_BG. Sound:
  CERT_BG subset-of the background of every reachable mask.
- **Certified separations** = two CERT_BG cores separated by a CERT_FG
  grout path -> separated in every reachable mask.
- **Certified 1-cycles** = beta1(CERT_FG) (Euler-characteristic method,
  campaign topo_metrics; a loop in the minimal foreground persists in all
  larger foregrounds). Full cubical persistence would refine localisation
  -> flagged, not implemented (gudhi absent).
- **Abstain set** = POSSIBLE = ~CERT_FG & ~CERT_BG (perturbation-sensitive,
  honestly reported as uncertain).
All statements pass ROI mask + physical scale floor (reuse
experiments/h2_domain/domain.py) so certificates concern meaningful
structure only (H2 lesson). Float-soundness: optional PEDANTIC nextafter
outward widening (mirrors [internal track]); default on for CERT sets.

## Hypotheses

**H-C1 (SOUNDNESS — gating, the teeth):** for a sample of certified-robust
classes, a bounded random + PGD-style eps-search over reachable
binarisations (CERT_FG subset-of M subset-of ~CERT_BG) finds ZERO
violations (a certified class never breaks), across all eps. A single
violation = certificate UNSOUND -> HALT and fix. Checked and reported
BEFORE any non-vacuity number. A deliberately-unsound planted certificate
MUST fail this check (test).

**H-C2 (non-vacuity — the positive claim):** at a "useful" eps defined
from p's own calibration (eps = one temperature-scaled confidence quantile
of |p-0.5|, stated in RESULTS), >= 50% of in-domain certified tessera
cores AND >= 50% of grout-line length are certified-robust.

**H-C3 (graded nesting):** certificates over DECREASING eps are
monotone-nested (more survives at smaller eps); nesting asserted EXACT
(mirrors [internal track] B1).

**KILL:** abstain floods (< 10% certified) at EVERY useful eps -> certified
topology needs eps below practical relevance -> report the clean boundary
"certified-topology threshold is eps < X", not a rescue.

## Tracks

- **T-toy (authoritative now):** synthetic masks with analytic topology GT
  + simulated p (soft-blurred GT + calibrated noise). Runs on CPU now;
  validates SOUNDNESS.
- **T-real (PROVISIONAL, GPU-gated):** frozen-checkpoint p on real crops;
  behind --gpu-real (default OFF -> prints "PROVISIONAL: simulated p").
  Runs only after [internal track] frees the GPU.

## Fixed conditions

eps sweep: {0.02, 0.05, 0.1, 0.15, 0.25, 0.4} (tiny -> clearly too large).
Metrics ABSOLUTE (standing rule): fraction of certified-robust components,
fraction of grout-line length certified-connected, abstain-area fraction,
each vs eps. 8-connectivity foreground, 4-connectivity background (dual
pairing, campaign convention). Seeds fixed.

## Deliverables & acceptance

sandwich.py, topo.py, run.py, REGISTRY.md, RESULTS.md,
plots/certified_vs_epsilon.png, gallery/. Suite green immediately; NO GPU
while hybrid runs (--gpu-real default off); REGISTRY precedes run.py in
git; H-C1 soundness checked + reported before any non-vacuity number;
interval-exactness and topo utilities reused, not reimplemented. Note the
graded / alpha-cut interval-valued-image extension as a possible future
direction -- flag, do not implement.

## CORRECTION ADDENDUM (2026-07-12, after adversarial verification; the
## original claims above are preserved verbatim; this records what was
## found unsound and the fix)

Adversarial verification (two independent
soundness reviewers) found the **β1 certified-cycle statement UNSOUND as
originally registered**: "Certified 1-cycles = betti1(CERT_FG) (a loop in
the minimal foreground persists in all larger foregrounds)" is FALSE — H1
is not monotone under foreground growth. Counterexample: a CERT_FG ring
around a POSSIBLE interior has betti1(CERT_FG)=1, but an in-budget
perturbation setting the interior to foreground fills the hole. The
original in-code H-C1 check did not test cycles, so it did not catch this.

**Corrected certified-cycle definition (sound):** a 1-cycle is certified
robust iff its enclosed region is CERT_BG (guaranteed background in every
reachable mask) walled by CERT_FG (guaranteed foreground) — an UNFILLABLE
hole. Computed as CERT_BG components not reachable from the image border
through ~CERT_FG. H-C1 extended to test cycle persistence. The β0
statements (components, tessera cores, separations) were and remain sound.

**Metric-semantics correction:** the reported `certified_component_frac`
(p-component ≥50%-covered by CERT_FG) and grout-length fraction are
COVERAGE proxies, NOT connectivity certificates (a ≥50%-covered component
pinched through POSSIBLE can be split). Renamed to
`component_covg_proxy_frac` / `grout_len_certainly_fg_frac`; the H-C2
headline and RESULTS verdict softened to "certainly-foreground coverage,"
with the genuinely certified-connected objects reported as the CERT_FG
connected-component count. The registered H-C2 threshold is unchanged; its
INTERPRETATION is corrected to what the metric actually guarantees.

These corrections were made before the T-real (GPU) run; no real-p number
was ever reported under the unsound version.

## HARDENING REGISTRATION (Track 1, 2026-07-12, committed BEFORE new numbers)

Soundness + non-vacuity on real p are ALREADY PROVEN (above). This does not
re-open them. It closes the two self-flagged gaps and locks wording. **No
new KILL can fire** — but if 1a or 1b surfaces an unsoundness in a NEW
predicate, HALT and report it as a finding (like the β1 correction), do not
paper over it.

**1a — true cubical persistence for cycles (gudhi).** Add gudhi (installed
3.13.0). Replace the connected-component enclosure proxy for certified
cycles with genuine cubical IMAGE-persistence. Filtration f over pixels of
the foreground-growth order: CERT_FG=0, POSSIBLE=1, CERT_BG=2. Certified
cycles = H1 persistence intervals with birth==0 AND death>1 (death==2),
i.e. the rank of the image H1(CERT_FG ↪ ~CERT_BG): a hole whose wall is
guaranteed-foreground (born in CERT_FG) and whose interior is guaranteed-
background (survives to ~CERT_BG, unfillable). **Registered equivalence
claim H-C4:** the persistence count EQUALS the corrected enclosure count on
the three regression cases (ring-over-POSSIBLE → 0; ring-over-CERT_BG → 1;
planted-unsound → not certified) and on T-real up to border/scale-floor
handling. Disagreement ⇒ one of the two is wrong ⇒ investigate before
reporting (not a KILL, a correctness check). If gudhi import fails in-env:
fall back to the enclosure proxy WITH A PROMINENT FLAG in RESULTS (never
silently). Re-emit the T-real table with the persistence column; keep the
enclosure column alongside for one release as cross-check.

**1b — connectivity certificate (coverage → connectivity, honest).** New
predicate distinct from the coverage fraction. Skeletonise p_bin&ROI; reduce
to a segment graph (nodes = junctions deg≥3 and endpoints deg 1; edges =
skeleton segments between nodes). A segment is CERTIFIED-CONNECTED iff EVERY
pixel on it lies in CERT_FG (⇒ foreground in every reachable mask ⇒ its two
endpoints stay connected under any ε-perturbation; a single POSSIBLE pinch
breaks it). Report, per real crop, BOTH: (i) `grout_len_certainly_fg_frac`
(coverage, unchanged) and (ii) NEW `certified_connected_seg_frac` and its
length-weighted form — expected LOWER than coverage. Do not overwrite (i).
**Soundness (add to H-C1, kind='connectivity'):** the worst-case reachable
mask for disconnection is all-POSSIBLE→background (M_min=CERT_FG); verify no
certified-connected segment's endpoints disconnect under it, and a planted
pinch (segment with a POSSIBLE gap) is NOT certified. Zero violations
required; a violation is a finding → HALT.

**1c — wording lock → GUARANTEE_STATEMENT.md.** The single exact sentence
the paper may claim, itemising (i) coverage fraction, (ii) certified β0
components, (iii) certified enclosed tesserae, (iv) NEW certified-connected
segment fraction, (v) certified cycles via persistence — each with its
worst-case adversary and scope caveat. Anti-overclaim contract.

Fixed conditions unchanged (eps sweep, ROI, scale floor, PEDANTIC, seeds).
Absolute companion to every new ratio (standing rule): connectivity reported
as both a fraction AND absolute segment/length counts.

## RE-EMIT REGISTRATION (2026-07-13, paper-queue item 6; committed BEFORE
## the run; GPU now free — no training co-resident, verified)

The GPU-deferred T-real re-emit, maximal scope, one run:

- **All 30 realset crops** (the prior run used the first 24 via
  `N_MASKS = 24`; RESULTS.md header corrected in this commit — the
  committed 24-crop numbers in `results.json` remain valid and untouched
  as the historical cross-check).
- **Emits on real p:** everything the prior run emitted PLUS the Track-1
  columns (`certified_connected_{len,seg}_frac`,
  `n_certified_cycles_persistence`) and the ABSOLUTE companions
  (skeleton length px + certainly-fg length px; segment counts
  total/certified) — closing the standing-rule debt flagged as paper
  limitation 7.
- **PER-CROP records** for every metric at every eps (not only means), so
  the paper can report worst-crop numbers — the honest headline shape for
  a worst-case certificate — and distributions.
- **p maps saved** per crop (`p_maps/*.npy`) for the real-image overlay
  figure (paper-queue item 7).
- **Output: `results_real_hardened.json`.** `results.json` is NOT
  overwritten (it is the committed source of the current paper's
  numbers). Once the new run's gate passes, the paper's next revision
  supersedes its T-real table with the new file and keeps the old as
  cross-check.
- **Gate unchanged:** H-C1 with ALL FOUR kinds (components, tessera
  cores, cycles, connectivity) at 0 violations BEFORE any non-vacuity
  number is read; a violation is a finding → HALT (as with the β1
  correction, report it, do not paper over).
- **Registered expectations (not claims):** real-p connectivity ≪
  coverage (as on toy); persistence count ≥ floored enclosure count with
  discrepancies attributable to sub-scale-floor holes only (H-C4 scope);
  30-crop means within the same regime as the 24-crop means.
- Fixed conditions unchanged (eps sweep, ROI, scale floor, PEDANTIC,
  seeds, 8/4 connectivity). Runner: project .venv (torch+cuda,
  gudhi 3.13). Command:
  `python run.py --gpu-real --n-masks 30 --out results_real_hardened.json --save-pmaps`.

## RANDOM-MASK MISS-RATE REGISTRATION (2026-07-15; committed
## BEFORE random_baseline.py exists — empirical companion to §3.6 Tightness)

Measured claim (not assumed): the two deterministic extremes catch every
planted SEMANTIC violation with certainty; N random reachable masks miss at
the law-predicted rates, which tend to 1 as the in-unison count c grows.

- **Constructions** (small grids, geometry mirrors tests/test_topocert.py):
  (a) fillable SQUARE ring — wall CERT_FG (0.95), rectangular interior
  POSSIBLE (0.5), bg CERT_BG (0.05), eps=0.1; interior area swept so
  c ∈ {1, 2, 4, 8, 12, 16} EXACTLY (c = interior pixel count; the fill
  event needs all c in unison). (b) pinched bar — bar CERT_FG (0.95),
  2-column POSSIBLE pinch (0.55), eps=0.1; bar/pinch height swept
  h ∈ {1, 2, 4, 8}; designated endpoint pixels at the bar's two ends.
- **Semantic predicates** (registered distinction: the H-C1 harness checks
  the stronger per-class SUPPORT predicate by design; the tightness claim
  concerns the semantic event, so that is what is scored here): ring
  violation = enclosed hole destroyed (⇔ every interior pixel foreground,
  since the CERT_FG wall encloses any remaining interior bg pixel); bar
  violation = endpoint pixels 8-disconnected in M.
- **Min-cut c for the bar computed EXACTLY** by vertex-capacitated max-flow
  (scipy.sparse.csgraph.maximum_flow, node splitting) on the POSSIBLE
  graph between the two CERT_FG sides; expected c = h (one pinch column).
  Enumeration cross-check: the violation event depends only on the 2h-pixel
  pinch block; all 2^(2h) patterns enumerated → EXACT detection probability
  per sampler (no closed form claimed for the bar; the union-bound
  approximation ≈ 2·2^{-h} may be quoted as approximation only).
- **Samplers, both registered:** (i) FAIR-COIN uniform reachable mask (each
  POSSIBLE pixel iid Bernoulli(1/2)) — the §3.6 tightness model; ring
  detection/draw = 2^-c exactly. (ii) HARNESS sampler (topo.py
  soundness_check: per mask q ~ U(0.1, 0.9), iid Bernoulli(q) per pixel);
  ring detection/draw = E_q[q^c] (numeric integral; polynomially larger
  than 2^-c yet still → 0 as c grows).
- **Method:** detection probabilities computed EXACTLY (ring closed form /
  numeric integral; bar enumeration weighted by the sampler's pattern
  probabilities), plus Monte-Carlo cross-check (K = 200,000 draws per
  construction × sampler; binomial CI; deviation beyond CI = FINDING to
  investigate, not hide). Miss probability for budget N is (1 − p_det)^N
  (draws iid), N ∈ {10, 30, 100, 1000}. Extremes M_min/M_max checked
  deterministically; expected: ring caught by M_max only, bar by M_min
  only (each violation lives at exactly one extreme, per Lemma 1).
- **Output:** results_random_baseline.json + plots/miss_rate.png. Any
  numeral entering paper.md gets a check_numbers.py ledger entry reading
  that JSON. Seed 0. CPU-only; runs while the re-emit occupies cores.

## SPLIT-HALF EPS-STABILITY REGISTRATION (2026-07-15 — the V5
## replacement; committed BEFORE eps_stability.py exists)

Replaces the retired V5 "learned-eps SVM" design (a constructed-to-fail
strawman; retired in the campaign plan). Question actually at issue: is the
calibration-defined eps estimator STABLE across data halves, and what
would any drift cost in certified quantities?

- **Data:** the 30 committed p_maps (frozen real p; the re-emit inputs).
- **Estimator under test** (verbatim the paper's rule, sandwich.useful_eps):
  per-crop useful_eps = median confidence margin |p−½| over uncertain
  pixels; cohort value = median across crops; snapped to the swept grid
  for use.
- **Protocol:** R = 200 seeded resamples (seed 0); each draws a random
  15/15 split (A, B) of the 30 crops. Record eps_A, eps_B (raw cohort
  medians), |eps_A − eps_B|, and whether both snap to the same grid point
  of {0.02, 0.05, 0.1, 0.15, 0.25, 0.4}.
- **Consequence metric:** when the snapped values agree (expected common
  case) the held-out certified quantities are IDENTICAL by construction;
  when they differ, the certified-quantity consequence is read off the
  committed H-C3-exactly-nested sweep (adjacent-grid deltas of coverage
  and counts) — no new heavy runs; the six-point sweep is the registered
  sensitivity ablation (registered in the campaign plan).
- **Design argument registered alongside:** optimizing eps against the
  certified quantities would invert the certificate's semantics (the band
  is the assumption, not a knob) — the estimator must be, and is,
  certificate-blind (it reads only |p−½| margins).
- **Report:** raw-drift distribution (median/max), grid agreement rate,
  per-crop useful_eps distribution. Output results_eps_stability.json;
  any numeral entering paper.md gets a check_numbers ledger entry.
- **Expectations (not claims):** raw drift small relative to grid spacing;
  agreement rate high. If NOT — that is the finding, reported as such,
  with the sweep quantifying its cost.

## R-EQ DIAGRAM-WINDOW REGISTRATION (2026-07-15; committed
## BEFORE diagram_window.py exists)

**H-R1 (identity):** for every committed p map (30) and every eps of the
sweep, the persistence-form certified-cycle count (persistence.py
certified_cycle_count on cert_sets(p, eps) — the paper's 1a column) EQUALS
the window count read off ONE superlevel H1 diagram of p per crop:
  #{ H1 intervals of gudhi CubicalComplex(top_dimensional_cells = -p):
     (-birth) > 1/2 + eps  AND  (-death) < 1/2 - eps }
(strict inequalities mirroring CERT strictness; Z/2 coefficients; same
cubical model as persistence.py). I.e., the certified count at every eps is
determined by window-straddling points of p's own superlevel diagram — the
§6 rank identity, machine-checked.
- Debug FIRST on the three H-C4 regression constructions (ring-over-
  POSSIBLE → 0; ring-over-CERT_BG → 1; 3×3 grid-of-holes → 9) at eps=0.1.
- Ties/pedantic widening: cert_sets applies one-ulp outward widening; if
  the identity fails ONLY at one-ulp threshold ties, the registered
  fallback is the tie-conservative direction (window count ≤ persistence-
  form count at ties), reported as such. Any OTHER disagreement is a
  finding → investigate before reporting (H-C4 style), not a KILL.
- **eps\* rider:** each certified cycle carries the closed-form maximal
  certified budget eps\*(feature) = min(p_birth − 1/2, 1/2 − p_death);
  one registered §8 sentence; NO figure this cycle (page budget).
- Output: results_diagram_window.json; any numeral entering paper.md gets
  a check_numbers ledger entry. CPU-only; one gudhi H1 diagram per crop +
  the 180 existing-convention cross-checks.

## H-F1 REGISTRATION (2026-07-15): interval-field feasibility

H-F1: cert_sets(p, eps_field) with a per-pixel eps ARRAY equals the
per-pixel scalar computation exactly (interval_field is elementwise;
broadcast regression test added to tests/test_topocert.py). A feasibility
test, not a number-emitting claim; it licenses the paper's Prop 1' remark
("the proof is per-pixel; uniformity is never used") with code truth. The
harness continues to exercise only the uniform-eps case — stated honestly
wherever the generalized form is claimed.

## DRIVE V2 REGISTRATION (2026-07-16; committed BEFORE
## drive_v2.py emits any number). The existential V2 deliverable:
## topology certificate is INDEPENDENT of per-pixel accuracy.

**Data.** DRIVE retinal vessels, Kaggle mirror
`andrewmvd/drive-digital-retinal-images-for-vessel-extraction` (downloaded
2026-07-16 via the Kaggle API; 29.4 MB). 20 training images (.tif, 565x584)
with 1st_manual vessel GT (.gif) + FOV masks. Test set + 2nd_manual are
NOT in this mirror → inter-rater eps (S2) deferred to official DRIVE.
License unspecified upstream (release-section flag). **p is MODEL-FREE**
(a classical Frangi filter, no training, no checkpoint) — which makes
"the certificate consumes only (p, eps)" literal and answers "single
checkpoint" more strongly than any second neural checkpoint.

**Frozen protocol P (pre-probe-established; NOT tuned to GT).** green
channel /255; `frangi(sigmas=range(1,6), black_ridges=True)`; FOV eroded
6 iterations (binary_erosion) to exclude the circular rim ridge (the
pre-probe found the rim is the strongest Frangi ridge and dominates Otsu
otherwise); response r within eroded FOV; skew-corrected Otsu-logistic
  p = sigma( 12 * ( T(r) - Otsu(T(r) over FOV & r>1e-7) ) ),  p:=0 outside FOV.
Transform T: **cbrt is PRIMARY** — the cube root is a standard
variance-stabilizer for a heavy-tailed nonnegative response and was chosen
A PRIORI on that ground, NOT because it maximized Dice (raw Otsu
under-segments ~5x; the pre-probe reported sqrt/log/cbrt all give Dice
0.59-0.62, so the certificate story is transform-robust). sqrt and
log1p-scaled are the REGISTERED ROBUSTNESS ABLATION, reported alongside.

**eps.** swept {0.02,0.05,0.1,0.15,0.25,0.4}; the V2 scatter is reported
at the calibration-defined useful_eps (cohort median of per-image
sandwich.useful_eps, snapped to the grid) — identical methodology to the
mosaic track. Absolute companions to every fraction.

**H-C1 (soundness gate, DOMAIN RE-RUN).** soundness_check on every emitted
DRIVE certified class (components, tessera/background cores, cycles,
connectivity) must find 0 violations at every eps BEFORE any V2 number is
read. A violation is a FINDING → HALT and report (as with the beta_1
correction), never papered over. (Pre-probe already saw 0 on 2 images.)

**H-V2 (the decoupling claim).** For the 20 images at the calibration eps,
compute per-image Dice(p>1/2, GT within FOV) and IoU, and per-image
certified quantities (n_certified_components, certified_connected_seg_frac,
n_certified_cycles, coverage). Report the SPEARMAN rho between Dice and
each certified quantity. **HONESTY CLAUSE (binding): rho is reported
whatever it is** — near-zero supports "topology certificate is orthogonal
to pixel accuracy" (V2); a strong positive rho would WEAKEN V2 and is
reported as such, not hidden. Deliverable: scatter (Dice vs certified
quantity) + a four-quadrant montage (a high-Dice / broken-certificate case
and a low-Dice / valid-certificate case, IF they exist in the 20).
Output: results_drive.json + figs. Seeds fixed. CPU-only, no GPU, no
training. Runner: project .venv (gudhi 3.13, skimage 0.26).

## CHASE_DB1 REGISTRATION (2026-07-16, second domain +
## inter-rater eps; committed BEFORE chase numbers). Unblocks S2 without the
## official-DRIVE email-verification wait: CHASE_DB1 ships TWO observers.

**Data.** CHASE_DB1 (Child Heart and Health Study), Kaggle mirror
`rashasarhanalharthi/chasedb1` (downloaded 2026-07-16 via the Kaggle API;
28.8 MB). 20 training + 8 test fundus images, 960x999, each with 1st_manual
AND 2nd_manual vessel GT (two independent human observers) + FOV masks.
Sorted-order pairing VERIFIED (inter-observer Dice 0.74-0.82 on 5 spot
images — the human-vs-human range; a mispairing would read ~0.1).
License: research dataset, unspecified on the mirror (release-section flag,
as with DRIVE); canonical source Kingston University Research Data Repo.

**S1 (second V2 domain).** Identical frozen protocol P to DRIVE (green
channel /255, frangi sigmas 1-5 black_ridges, FOV erode 6, skew-corrected
Otsu-logistic, cbrt PRIMARY + sqrt/log robustness ablation), same H-C1
soundness gate (0 violations required), same H-V2 decoupling (per-image
Dice/IoU vs certified quantities, Spearman rho, BINDING honesty clause:
rho reported whatever it is). Pooled DRIVE+CHASE scatter strengthens V2
across two retinal datasets + the mosaic track.

**S2 (inter-rater eps, V3 medical protocol INSTANTIATED).** The naive
"95th percentile of per-pixel disagreement" is degenerate on binary masks
(values are 0/1). REGISTERED RULE:
  D_i = obs1_i XOR obs2_i  within FOV       (inter-observer disagreement)
  eps_inter := median over the 20 training images of
               median_{x in D_i} |Frangi_p_i(x) - 1/2|
i.e. the typical model-margin uncertainty exactly where the two human
observers disagree. Justification: eps is the score-map band that renders
humanly-disputed pixels POSSIBLE (abstained), tying eps to annotation
uncertainty, not an invented number. Report eps_inter as a MARKED POINT on
the swept eps grid (nearest grid point) + the explicit two-observer
lower-bound caveat (2 raters underestimate true inter-rater spread). No
KILL; this is a calibration instantiation, not a pass/fail claim.

Absolute companions to every fraction. Seeds fixed. CPU-only. Runner: the
project .venv. S2 (eps only, Frangi+disagreement, no gudhi) runs
now; the heavier S1 certificate sweep queues behind the DRIVE run.


## CORRECTION ADDENDUM 2 (2026-07-22, H-C4 refuted as a general identity;
## the original registration above is preserved verbatim)

**What was registered.** H-C4 claimed the persistence count EQUALS the
corrected enclosure count on the three regression cases "and on T-real up to
border/scale-floor handling".

**What is true.** The regression-case half is CONFIRMED (ring-over-POSSIBLE
-> 0; ring-over-CERT_BG -> 1; 3x3 grid -> 9; planted-unsound not certified).
The general half is REFUTED. The two computations answer different questions
and diverge in BOTH directions:

- Persistence > enclosure where enclosure applies its ROI and scale floor
  (the direction the original registration anticipated: sub-floor debris).
- Enclosure > persistence where a POSSIBLE channel subdivides ONE cavity into
  several CERT_BG components. Counterexample, executed against the shipped
  code: a CERT_FG annulus whose interior holds two CERT_BG squares separated
  by a 2 px POSSIBLE channel gives enclosure 2, image rank 1
  (beta1(CERT_FG)=1, beta1(~CERT_BG)=2; the annulus generator maps to the SUM
  of the two blob classes). No filtering is involved. On the committed real
  track this configuration occurs on 9 of 30 crops at eps=0.25 and 0.40.

**Why the registered check missed it.** The three regression constructions all
place a single CERT_BG component inside each cavity, which is exactly the
condition under which the two forms agree. The equivalence held on every case
that was tested, and the untested case is the one that breaks it -- the same
shape of failure as the beta1 unsoundness of Correction Addendum 1, where the
harness passed because it did not attack the class in question.

**Soundness impact: NONE.** Both quantities remain sound; neither over-claims.
The harness verifies per-region enclosure at both extremes and the
counterexample passes it legitimately. What was wrong was the IDENTIFICATION
of the two counts, not either count.

**Correction.** They are now reported as two quantities with distinct
semantics: the enclosure count is the localisable per-region certificate and
stays the headline; the image rank is the only one of the two that
lower-bounds beta1 of every reachable mask. The paper states the
non-equivalence, the counterexample, and the two-sided divergence
(Sec 3.5, Table 1 row 5, Sec 5.5).

**Registered follow-up.** Add the two-cores-one-wall construction to the
regression suite so the refuted case is covered going forward.
