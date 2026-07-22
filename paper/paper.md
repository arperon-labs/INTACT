# INTACT: Sound Worst-Case Topological Certificates for Segmentation Score Maps

**Radoslav Lovecký**  ·  Arperon
`info@arperon.com`

*Preprint v1. Every citation key in brackets resolves in
`refs.bib`, and every entry there was identity-verified against a primary
source before inclusion — no fabricated references, and no pending
placeholders.*

## Abstract

Consumers of segmentation rarely ask about pixel accuracy; they ask
topological questions — how many connected structures are there, does this
line stay unbroken, how many enclosed regions does it bound. Topology-aware
training methods (the clDice and Betti-matching lineage) improve such
properties on average but guarantee nothing about any particular output. We
present INTACT (INference-Time Adversarial Certificates for Topology):
sound, worst-case topological certificates for thresholded segmentation
score maps. An ℓ∞ uncertainty band of radius `ε` around a
frozen score map `p` determines — exactly — a lattice interval of reachable
binary masks, between
the certainly-foreground core `CERT_FG = {p−ε > ½}` and the complement of
the certainly-background core `CERT_BG = {p+ε ≤ ½}`. Over this interval
we prove a two-mask certification principle: a finite conjunction of
monotone predicates holds on every reachable mask iff it holds at the
interval's two extremes — and both extremes are individually necessary, a
minimal check that no fixed budget of random sampling can replace.
Instantiating the principle yields five certified quantities —
certainly-foreground coverage, certified connected components, certified
enclosed regions (tesserae), a strict certified-connectivity fraction,
and certified 1-cycles — holes whose wall is certainly foreground and whose
interior is certainly background, so no in-budget perturbation can fill or
breach them — each stated with its
worst-case adversary and its scope caveat. The certificate operates on
perturbations of the score map; it is **not** an end-to-end input-space
certificate (composition with input-space methods is an interface we
state, not a result we claim).

The instantiation is not mechanical: our first cycle certificate, β₁ of
the certified foreground, was genuinely unsound (H₁ is not monotone under
foreground growth), and we report the counterexample, the catch, and the
fix as a section of the method, not a footnote. A worst-case-exhaustive
soundness harness attacks all four class-valued quantities — coverage, the
fifth, is a pixel fraction with no per-instance support — at the two
deterministic extremes; on real model outputs it reports **0 violations in
16,675,936 checks**. On 30 real mosaic
crops through a frozen zero-shot grout-segmentation model the certificate
is non-vacuous: at ε = 0.10, 94% of predicted grout length is
certainly-foreground; at the calibration-defined ε = 0.40, 60%. Coverage,
however, is not connectivity — the strict certified-connected fraction is
always smaller: 0.766 at ε = 0.10 and 0.343 at ε = 0.40, a modest 1.2–1.7×
gap on real outputs (the order-of-magnitude gap appears only on the
near-tautological toy track, where the blurred maps fragment). We report
the two numbers separately rather than blur them into one.

*(Hero/teaser figure, page 1 — **the certificate is not a confidence map**:
a real score map `p`; the per-pixel margin `|p − ½|` (entropy-equivalent,
§7), which calls almost every pixel confident; and what is actually
certified — each enclosed tessera painted by `ε*`, the largest budget at
which it provably stays an unfillable hole. The budgets are graded, because
a hole dies when its *wall* erodes as readily as when its interior does — a
topological fact no per-pixel confidence map contains. Read off the
exactly-nested sweep (§5.4); crop closest to the 30-crop cohort mean.
`figs/fig_graded`.)*

---

## 1. Introduction

A segmentation map is usually consumed through its topology. A radiologist
asks whether a vessel is interrupted; a conservator asks whether a mosaic's
grout network still separates every tile from its neighbours; an inspector
asks whether a crack
network is one connected system or several. Pixelwise scores answer none of
these questions directly, and a model that is 99% accurate per pixel can
still be topologically wrong everywhere it matters.

A substantial literature addresses this at *training time*: topology-aware
losses and metrics — clDice for tubular structures [shit2021cldice],
persistent-homology losses [hu2019topo; clough2020topological], Betti
matching [stucki2023betti] — shape the learned map so that its topology is
better *on average*. What they do not provide is a guarantee about any
given output: after training, nothing tells the consumer which components
of *this* prediction survive *this* much uncertainty.

This paper takes the complementary, inference-time view. Given a frozen
score map `p` and an ℓ∞ budget `ε` on perturbations of `p`, we compute
topological statements that **hold on every mask reachable within the
budget**, and we prove and
then *test* that claim adversarially. The name is the guarantee: INTACT
certifies what remains *intact* — which components stay connected, which
lines stay unbroken, which holes stay unfillable — under any in-budget
perturbation. The conceptual ancestor is fifty
years old: Benson's algorithm for unconditional life in the game of Go
[benson1976] certifies a group alive under *any* sequence of opponent
moves via a monotone fixpoint — an adversarial certificate, not a
statistical one. Our certificate is the same move for segmentation
topology: a monotone construction (thresholding an interval-bounded map)
whose conclusions hold against the entire perturbation band.

Contributions, each with its qualifier:

1. **The sandwich is exact** (§2). `CERT_FG / POSSIBLE / CERT_BG`
   partitions the image so that the reachable set of binary masks under any
   ℓ∞-ε perturbation is *exactly* `{M : CERT_FG ⊆ M ⊆ ~CERT_BG}`
   (Proposition 1) — thresholding is monotone and interval propagation
   through it is endpoint-exact, so the abstraction loses nothing.

2. **Two masks suffice, and both are needed** (§3.6). Over that interval a
   finite conjunction of monotone predicates is certified by checking
   exactly the two extreme masks (Lemma 1); each extreme is individually
   necessary, and no fixed budget of random masks substitutes for either —
   the image-topology instance of a classical three-valued duality (§6),
   made exact and tight.

3. **Five certified quantities, each with adversary and caveat** (§3):
   certainly-foreground coverage; certified β₀ components; certified
   enclosed tesserae; a strict certified-connectivity fraction; and
   certified 1-cycles as *unfillable holes* — the rank of the image
   `H1(CERT_FG ↪ ~CERT_BG)` computed by cubical persistence. We keep
   coverage and connectivity as two separate reported numbers, because
   they are different quantities — a modest 1.2–1.7× apart on real outputs,
   an order of magnitude only on the near-tautological toy track (§5.2).

4. **Adversarial self-verification as part of the method** (§4). A
   soundness harness exercises every certified class at the deterministic
   worst-case extremes of the reachable set (plus random reachable masks)
   and must also catch deliberately planted unsound certificates. An
   adversarial-verification pass over the registered
   claims caught a real unsoundness that the harness, as then configured,
   had missed — our originally registered cycle certificate,
   `β₁(CERT_FG)`, is *false* as a robustness claim — before any real-model
   number was reported. We present the counterexample, why the original
   check missed it, and the corrected certificate.

5. **Non-vacuity on real model outputs** (§5). On 30 real mosaic crops
   through a frozen zero-shot grout segmenter, the certificate holds with
   0 violations in 16,675,936 checks and is far from empty: 94% of
   predicted grout length is certainly-foreground at ε = 0.10, and 60%
   survives even at the calibration-defined budget ε = 0.40, with dozens
   of certified components and hundreds of certified enclosed tesserae;
   the strict certified-connectivity fraction, now measured on real `p`,
   is 0.766 and 0.343 at those two budgets.

**Threat-model statement (read first).** The certificate as built operates
on perturbations of the *score map* `p`: the adversary may replace `p` by
any `p'` with `‖p' − p‖∞ ≤ ε`. It is **not** an end-to-end input-space
certificate — nothing here bounds how far `p` can move when the *input
image* is perturbed. The two compose cleanly in principle: any input-space
method that yields per-pixel bounds on the score map (randomized smoothing
[cohen2019smoothing; fischer2021segcert], interval bound propagation
[gowal2018ibp]) supplies exactly the interval field our machinery consumes.
We state this as an interface in §8; we have not built it, and no claim in
this paper depends on it.

**Domain.** Our primary testbed is GROUT [lovecky2026grout], a zero-shot
(synthetic-only trained) EfficientNet-B3 U-Net segmentation model for the
grout lines of stone mosaics; the enclosed tiles are *tesserae*. Nothing in
§§2–4 is specific to mosaics — the machinery consumes any soft map
thresholded at ½ — and we exercise that generality off-domain in §5.7 with
a cross-domain stress-test on two retinal-vessel datasets (DRIVE
[staal2004drive] and CHASE_DB1 [fraz2012chase], model-free Frangi maps),
where the soundness harness holds across a second modality. The *headline
non-vacuity* numbers, however, are about the single mosaic task and one
frozen checkpoint, and we say so wherever it matters.

## 2. Setting and threat model

*(Pipeline figure: image → frozen model → `p` → ±ε sandwich → five
certified quantities, four of which carry a per-instance support that the
harness attacks at both extremes; coverage is a pixel fraction with no such
support — nothing to attack instance-wise — and is sound directly by
CERT_FG-containment;
`figs/fig_pipeline`.)*

Let `p ∈ [0,1]^{H×W}` be a frozen score map ("grout probability" per
pixel), binarised at threshold ½: the predicted foreground is
`{p > ½}`. The adversary picks any `p'` with `‖p' − p‖∞ ≤ ε` and the
consumer sees the mask `M(p') = {p' > ½}`.

**The sandwich.** Define

```
CERT_FG  = { x : p(x) − ε > ½ }     (certainly foreground)
CERT_BG  = { x : p(x) + ε ≤ ½ }     (certainly background)
POSSIBLE = the complement            (the adversary's territory)
```

The asymmetry between the two tests is forced by the strict threshold rule
`M = {p' > ½}`, and is not a blemish: a pixel is certainly foreground iff
its lower endpoint clears the threshold strictly, and certainly background
iff its upper endpoint fails to — which is the *non-strict* `p + ε ≤ ½`.
With a strict test on the background side, a pixel at the exact tie
`p + ε = ½` would be called POSSIBLE despite being unable to cross the
threshold, and the proposition below would hold only up to such ties.

**Proposition 1 (reachable set, exact).** The set of masks obtainable by
in-budget perturbation is exactly the lattice interval

> `{ M(p') : ‖p'−p‖∞ ≤ ε } = { M : CERT_FG ⊆ M ⊆ ~CERT_BG }`.

*Proof.* (⊆) For any admissible `p'` and any `x ∈ CERT_FG`,
`p'(x) ≥ p(x) − ε > ½`, so `x ∈ M(p')`; symmetrically no `x ∈ CERT_BG`
enters `M(p')`. (⊇) Given any `M` with `CERT_FG ⊆ M ⊆ ~CERT_BG`, set
`p'(x) = min(p(x)+ε, 1)` where `x ∈ M` and `p'(x) = max(p(x)−ε, 0)`
otherwise. Then `p'` is admissible, and exactly two implications are
needed: if `x ∈ M` then `x ∉ CERT_BG`, so `p(x)+ε > ½` and hence
`p'(x) > ½`; if `x ∉ M` then `x ∉ CERT_FG`, so `p(x)−ε ≤ ½` and hence
`p'(x) ≤ ½`. Therefore `M(p') = M`. ∎

**Floating point.** In the implementation the interval `[p−ε, p+ε]` is
widened outward by one ulp per endpoint (`np.nextafter`; enabled by default) before the comparisons, so rounding can only *shrink* the
certified sets, never grow them. One consequence: an exact tie `p + ε = ½`
has its endpoint widened above ½ and is recorded as POSSIBLE rather than
CERT_BG. The computed sets are therefore the exact sets of Proposition 1
minus a measure-zero tie set, always in the direction of abstention — the
behaviour a safety-critical consumer needs, since a pixel the budget could
push either way is treated as uncertain rather than silently certified.

Thresholding is a monotone operation and interval propagation through it
is endpoint-exact: the propagated interval is attained, which is what
Proposition 1 states set-theoretically. In abstract-interpretation terms [cousot1977]: the
interval abstraction of the threshold operator is *exact* here, not merely
sound — the abstraction loses nothing for this operator.

Everything certified below is a statement quantified over the reachable
set of Proposition 1 — equivalently, over every admissible perturbation.

**Structured adversaries.** Any perturbation class contained in the ℓ∞
ball inherits soundness by containment: every certificate holds a
fortiori against smooth fields, low-frequency noise, or any other
structured subset of the ball. What is surrendered is exactness — the
reachable set of a structured class is generally not a lattice interval,
so Proposition 1's equality becomes containment and the two-extreme check
certifies against a superset of what is strictly reachable: sound but
conservative, with the conservatism concentrated at POSSIBLE features
smaller than the adversary's correlation length. The tightness measure
argument of §3.6 says why this direction is the right one to be
conservative in: correlated noise makes coordinated `c`-pixel flips
*likely* rather than measure `2^{-c}`, so a structured adversary is more
dangerous per unit budget, never less. Exact certification under
structured classes is open (§8).

**Where ε comes from.** So that ε is not an invented number, the "useful"
budget is calibration-defined: the median of the confidence margin
`|p − ½|` over uncertain pixels (`0 < margin < ½`), per map, median across
maps, snapped to the *nearest* point of the swept grid. On the real track
this gives 0.425 → ε = 0.40; the sweep is
ε ∈ {0.02, 0.05, 0.10, 0.15, 0.25, 0.40}. Snapping to the nearest point can
move ε down, which weakens the adversary and so makes certificates easier —
the one step in the pipeline that does not err toward abstention. It is
guarded by the split-half stability of the estimator (§5.6), which selects
the same grid point in 200 of 200 resamples, and by the exactly-nested
sweep (§5.4), which shows what any mis-estimate would cost.

**Conventions (part of the certificate's definition, not post-hoc
filters).** Certificates take a region-of-interest mask and a physical
scale floor. The ROI is the whole frame on the mosaic tracks — so the
abstain denominator there is the whole image — and, on the retinal tracks,
the dataset's field-of-view mask eroded by six binary-erosion iterations.
The floor is a *local-thickness* test rather than an area or diameter test:
a component survives iff it is non-empty after a morphological opening with
an elliptical structuring element of radius `max(1, round(floor/2))` px,
i.e. iff it contains an inscribed disc of that radius. On the mosaic tracks
the floor is half the tessera-width scale, tessera width being the square
root of the median area of the 4-connected background components of the
ε-*independent* prediction `{p > ½}` (components of area ≥ 9 px; fallback
width 6.0 px, hence a 3.0 px floor); on the retinal tracks it is a fixed
1.0 px, since vessel calibre rather than tessera size sets the scale.
Foreground uses 8-connectivity, background 4-connectivity (the
standard dual pairing, so that curves separate). Certificates pass a
region-of-interest mask and a physical scale floor — floor = 0.5 × the
tessera-width scale, where tessera width is the square root of the median
tessera area (areas ≥ 9 px; fallback 6.0 px) — so that certified counts
concern meaningful structure rather than single-pixel debris. All metrics
are reported as absolute counts alongside any fraction; ratios never stand
alone. The proofs are per-pixel or lattice-theoretic throughout, so
Proposition 1 and the coverage, component, tessera-core and per-segment
connectivity certificates carry to a cubical grid of any dimension, with
dimension entering only through the choice of dual adjacency pairing (in
3D, 26/6 or 18/6 rather than 8/4). The cycle certificate is the one
exception, and we flag it rather than gloss it: its persistence form
generalises degreewise — the image-rank construction applies to `H_k` for
any `k` — but its *enclosure* form does not. By Alexander duality,
background components that cannot reach the border realise `H_{d−1}`,
which is `H_1` only when `d = 2`; in three dimensions the same computation
counts enclosed voids, and `H_1` tunnels have no enclosure form at all
(§3.7, §8).

**What is *not* claimed.** (i) Nothing about the input→`p` pipeline (see
the threat-model statement above). (ii) Nothing about correctness of `p`
against ground truth: the certificate concerns robustness of *this map's*
topology to ε, not whether that topology is right. (iii) Nothing about
POSSIBLE pixels — they are reported as the abstain fraction. (iv) No claim that "the whole grout network certainly stays
connected"; the connectivity certificate is per-segment (§3.4).

## 3. Certified quantities and their soundness

Table 1 itemises the five certified quantities. Each row is a worst-case
claim over the entire reachable set, and each carries the caveat that
bounds what it means. This table is the paper's claim surface: nothing
stronger is asserted anywhere.

**Table 1 — the five certified quantities.**

| # | Quantity | Certified claim (∀ reachable masks) | Worst-case adversary | Caveat |
|---|---|---|---|---|
| 1 | Coverage: certainly-foreground fraction of predicted grout length | every CERT_FG pixel is foreground in every reachable mask | per-pixel ℓ∞-ε | a **coverage** statement, NOT connectivity: a covered line pinched through POSSIBLE can still split; reported as fraction and absolute length |
| 2 | Certified β₀ components: connected components of CERT_FG (8-conn) | each is connected in every reachable mask (supersets preserve connectivity) | any reachable mask (all are supersets) | these are CERT_FG's *own* components (absolute count), not the components of `{p>½}` |
| 3 | Certified enclosed tesserae: components of CERT_BG (4-conn), ROI + scale-floor filtered | each stays fully background in every reachable mask | any reachable mask | certifies a tessera **core**, not the whole tile |
| 4 | Certified-connected grout fraction: skeleton segments lying entirely in CERT_FG | such a segment's endpoints stay connected under any ε-perturbation | all-POSSIBLE→background | strictly ≤ coverage; a single POSSIBLE pinch disqualifies a segment; strictly ≤ coverage; modest on real outputs (1.2–1.7×), order-of-magnitude on toy |
| 5 | Certified 1-cycles, reported two ways: **enclosed regions** (CERT_BG components walled by CERT_FG, ROI + scale-floor filtered — the headline count) and the **image rank** `rank H1(CERT_FG ↪ ~CERT_BG)` (cubical persistence, unfiltered) | each enclosed region is an unfillable, unleakable hole — wall guaranteed foreground, interior guaranteed background — in every reachable mask; the rank additionally lower-bounds `β₁(M)` for every reachable `M` | both deterministic extremes | the two are **not** equal in general (§3.5): the rank is smaller when one cavity holds several CERT_BG components split by POSSIBLE, and larger where the enclosure count applies its ROI/scale floor. Only the rank is a Betti bound; only the enclosure form localises |

### 3.1 Coverage (certainly-foreground fraction)

The fraction of the skeleton of the predicted foreground that lies in
CERT_FG. We report it alongside its absolute certified length in pixels, so
the fraction never stands alone (Table 2 caption). Sound by Proposition 1: a
CERT_FG pixel is foreground under every admissible perturbation. The point bears repeating because it is the most tempting overclaim in this
design space: high coverage does **not** mean
the structure stays connected (§3.4, §5.2).

### 3.2 Certified β₀ components

The connected components of CERT_FG itself (8-connectivity). Every
reachable mask `M` satisfies `CERT_FG ⊆ M`, and adding pixels never
disconnects an already-connected set, so each CERT_FG component remains
connected — as a set of foreground pixels — in every `M`. The count is
absolute and refers to CERT_FG's own components; it is *not* the number of
components of the prediction `{p > ½}` (at large ε, CERT_FG fragments and
this count *rises* — visible in Table 2 — precisely because it counts
certified fragments). A scope note a careful reader will want: this is a
certificate about the *named* components (each stays connected in every
reachable mask), not a lower bound on β₀ of every reachable mask — two
certified components can merge through POSSIBLE, which is exactly why the
count rises with ε. The quantity that would bound distinct structures
from below — the rank of the image `H0(CERT_FG → ~CERT_BG)`, the degree-0
analogue of §3.5's cycle certificate — is well-defined in the same
filtration; we leave its registration as a certified quantity to future
work.

### 3.3 Certified enclosed tesserae

The connected components of CERT_BG (4-connectivity), after ROI and scale
floor. Each lies in the background of every reachable mask. This certifies
the tessera *core* — the region that certainly remains background — not
the full extent of the tile as a human would outline it.

### 3.4 Certified connectivity (the strict number)

Skeletonise the predicted foreground within the ROI by Zhang–Suen thinning
(`skimage.morphology.skeletonize`) — the thinning rule fixes the node
degrees and hence the segment decomposition, so it is part of the
certificate's definition — and reduce it to a
segment graph: nodes are junctions (degree ≥ 3) and endpoints (degree 1);
edges are the junction-to-junction skeleton segments. A segment is
**certified-connected** iff *every* pixel of it lies in CERT_FG; then its
endpoints remain connected under any admissible perturbation, because the
whole segment is present in every reachable mask. A single POSSIBLE pixel
on the segment disqualifies it — that pixel is the adversary's, and the
worst-case mask (all POSSIBLE → background) cuts the segment there.

We report the certified fraction of segments and of skeleton length (the
absolute segment and length companions are in the Table 2 caption). By
construction this is
bounded above by coverage; that gap is measured, not hidden — modest on
real `p` (1.2–1.7×) and dramatic only on the toy track (§5.2). We
explicitly do not claim network-level connectivity ("the whole grout web
stays one piece") — only the per-segment guarantee.

### 3.5 Certified 1-cycles (unfillable holes) — the corrected certificate

A cycle of the prediction is worth certifying only if the adversary can
neither *fill* it (turn its interior to foreground) nor *leak* it (break
its wall). The certified object is therefore an **unfillable hole**: a
connected region of CERT_BG (guaranteed background everywhere, in every
reachable mask) enclosed by CERT_FG (guaranteed foreground). Two related
computations, which are **not** equivalent in general:

- **Enclosure form:** CERT_BG components not reachable from the image
  border through `~CERT_FG` (the can-be-background region); this form is
  ROI/scale-floor filtered and provides localisation.
- **Persistence form:** the rank of the image `H1(CERT_FG ↪ ~CERT_BG)`,
  computed by cubical persistent homology [cohensteiner2009image] with the
  three-level filtration CERT_FG = 0, POSSIBLE = 1, CERT_BG = 2 (gudhi
  [gudhi]; intervals with birth < 0.5 and death > 1.5).

The two forms count different things, and we separate them rather than
identify them. The enclosure form counts *enclosed guaranteed-background
regions*; the persistence form counts the *rank* of an inclusion-induced
map. They diverge whenever one enclosed cavity contains several CERT_BG
components split by POSSIBLE: a CERT_FG annulus whose interior holds two
CERT_BG squares separated by a POSSIBLE channel gives enclosure 2 but image
rank 1 — `β₁(CERT_FG) = 1` while `β₁(~CERT_BG) = 2`, and the annulus
generator maps to the *sum* of the two blob classes. Only the persistence
rank lower-bounds `β₁(M)` for every reachable mask `M` (at `M = CERT_FG` the
two squares merge into a single hole). The enclosure count stays sound as a
*per-region* statement — each region is guaranteed background and unleakable
in every reachable mask, which is exactly what the soundness harness
verifies — but it is not a Betti number and must not be read as one. This is
the degree-1 instance of the named-features-versus-rank-bound distinction
drawn for β₀ in §3.2.

The two counts agree **exactly** on the clean regression cases
(ring-over-POSSIBLE → 0; ring-over-CERT_BG → 1; a 3×3 grid of enclosed
cells → 9; the planted unsound cycle → not certified) — we pre-registered this
equivalence as a prediction before writing the persistence code. On noisy maps the raw persistence count exceeds the enclosure count by
the holes the enclosure count filters out — sub-scale-floor and outside the
ROI — since persistence is unfiltered; the decomposition is validated on the
toy track (§5.5). Localisation stays with the enclosure form:
persistence gives the certified *count*, not per-cycle generators.

This definition is the *corrected* one. It is not what we first built —
§4 reports what we first built, why it was wrong, and how it was caught.

*(Gallery figure: a synthetic Voronoi mosaic — confident tiles are
certified unfillable holes (green); one tile with a model-uncertain
interior is a fillable hole, refused (dashed), exactly what the unsound
β₁ would have certified; thin joints erode to POSSIBLE as ε grows.
`figs/fig_gallery`.)*

### 3.6 Soundness: the structural argument and the adversarial check

Soundness has two layers, and we state the strength of each precisely.

**The structural layer.** Each certificate is sound by construction on top
of Proposition 1: CERT_FG is contained in the foreground of every
reachable mask (quantities 1, 4); connectivity is preserved under superset
(quantity 2); CERT_BG is contained in the background of every reachable
mask (quantity 3); and an unfillable hole's wall and interior are pinned
by both containments at once (quantity 5). PEDANTIC widening only shrinks
CERT sets — the safe direction — and the strict inequalities settle exact
boundary ties conservatively.

**The adversarial layer.** An implementation can betray a proof, so every
certified class emitted by the pipeline is attacked by an explicit
soundness check: the *deterministic worst-case extremes* of the reachable
set — all POSSIBLE pixels to background (the minimal mask, the worst case
for anything foreground) and all POSSIBLE pixels to foreground (the
maximal mask, the worst case for anything background or for filling a
hole) — plus random reachable masks. That the two extremes suffice is not
an empirical observation; it is a consequence of the predicates'
monotonicity:

**Lemma 1 (two extremes are exhaustive).** Write the reachable set as the
lattice interval

> `𝕀 = {M : M_min ⊆ M ⊆ M_max}`,  with `M_min = CERT_FG`, `M_max = ~CERT_BG`

(Proposition 1). Call a predicate φ(M) *upward
monotone* if φ(M) and M ⊆ M′ imply φ(M′), *downward monotone* dually.
Then a finite conjunction of monotone predicates holds on all of 𝕀 iff
every upward-monotone conjunct holds at `M_min` and every
downward-monotone conjunct holds at `M_max`.

*Proof.* An upward-monotone conjunct that holds at `M_min` holds at every
`M ⊇ M_min`; if it fails, `M_min ∈ 𝕀` is itself the witness. Dually at
`M_max`. A conjunction fails somewhere on 𝕀 iff some conjunct does. ∎

Each harness predicate is such a conjunction: a foreground class asserts
`S ⊆ M` for its (already-connected) support — upward monotone, worst case
`M_min`; a background core asserts `S ∩ M = ∅` — downward monotone, worst
case `M_max`; a cycle asserts its wall is present (upward, `M_min`) *and*
its interior stays background (downward, `M_max`) — both extremes
together; a connectivity segment asserts a path exists — path existence
is upward monotone, worst case `M_min`. A violation counts as a broken
certificate; a single one halts the run before any headline number is
emitted.

**Tightness (both extremes necessary).** Lemma 1 makes the pair
*sufficient*; the certified classes make each extreme *individually
necessary* (all four extreme-mask cells are rendered in the tightness
figure). Drop `M_max` and the counterexample figure's fillable ring is falsely certified
— its cycle holds at `M_min` (wall present, interior open) yet is filled
at `M_max` once the POSSIBLE interior is forced to foreground (§3.5); drop
`M_min` and the pinch figure's pinched bar is falsely certified — its segment
spans at `M_max` yet is cut at `M_min` once the POSSIBLE pinch is forced
to background (§3.4). By Lemma 1 each failure localises at exactly one
extreme, never strictly interior; the foreground-support and
background-core classes only fix *which* extreme is worst (`M_min` and
`M_max` respectively, the direction in which the harness would reject a
support or core straying into POSSIBLE), and a cycle forces both at once.
Since `M_min` is the worst case of every upward-monotone conjunct and
`M_max` of every downward one, neither extreme dominates the other: the
neither can stand in for the other and the check is *minimal* at two masks — each
extreme is itself a reachable mask on which the dropped-extreme harness
fails, so omitting either forfeits worst-case certainty. Random sampling
cannot restore it: by monotonicity `M_min` lies in *every* non-empty
upward-violation region and `M_max` in every downward one, whereas a
random draw detects a violation only by landing in that region, of
measure `2^{-c}` in the number `c` of POSSIBLE pixels that must turn
adversarial in unison (an enclosure's whole interior, a segment's
separating cut). Taking `c` large — an enclosure of growing area — sends
the per-draw detection `2^{-c}` to zero, so for any fixed budget `N` the
miss probability `(1 − 2^{-c})^N → 1`; the two extremes drive all POSSIBLE
pixels at once and catch it with certainty. The random reachable masks
therefore add nothing to worst-case coverage; they are retained only as a
cross-check against implementation faults (an independent review of the
harness reached the same exhaustiveness conclusion before Lemma 1 was
written down). The measure argument is itself measured: a registered
baseline (Appendix C) plants fillable rings and pinched bars with
controlled in-unison count `c`, scores the semantic events, and finds
per-draw detection matching `2^{-c}` exactly under the uniform model —
polynomially better yet still vanishing under the harness's own sampler —
with every planted violation caught at exactly the predicted extreme and
never the other.

The harness must also be able to *fail*: deliberately planted unsound
certificates — a foreground class intruding into POSSIBLE, a background
core intruding into POSSIBLE, a "certified" cycle over a fillable
interior, a "certified-connected" segment spanning a pinch — are all
flagged by the same check (regression tests). A certificate system whose
alarm never rings is indistinguishable from one with no alarm; ours rings
on every planted fault. The one real fault (§4) was caught not by this
harness — which did not yet know cycles were a class — but by an external
adversarial-verification pass, after which the harness was extended so
that it would ring.

**Result:** 0 violations for every certified class emitted on each track
and all swept ε — all four classes (components, tessera cores, corrected
enclosure cycles, and connectivity segments) on both the toy track and the
real track (16,675,936 checks
over 30 crops).

### 3.7 Generality of the construction

**Interval fields (Proposition 1′).** Nothing in Proposition 1 uses the
uniformity of ε: the proof is per-pixel, so for any per-pixel interval
field `[l(x), u(x)]` on the score map the reachable set of masks is
exactly the lattice interval between `{l > ½}` and the complement of
`{u ≤ ½}`, and every certificate above applies unchanged to the resulting
(non-uniform) sandwich. Uniform ε is the corollary `l = p−ε, u = p+ε`,
and the composition interface of §8 is the corollary for bounds supplied
by input-space certification. The implementation is already field-ready —
a per-pixel ε array broadcasts through the identical code path
(regression-tested) — though the harness results of §5 exercise
only the uniform case.

**The lattice form, and what else is monotone.** More abstractly, the
ingredients are an interval in a complete lattice and monotone
predicates: the sandwich is a three-valued (Kleene) abstraction and the
two-extreme check is the classical optimistic/pessimistic-completion
duality (§6) — we claim the imaging instantiation, its exactness
(Proposition 1), and its tightness (§3.6), not the lattice principle.
The same two-mask check therefore extends beyond topology: morphological
erosion and dilation are monotone lattice maps, so certified minimum
thickness (survival of erosion at `M_min`), certified clearance (dually
at `M_max`), and certified area intervals follow with no new theory —
geometric certificates we flag but do not build here.

**What is not monotone.** The recipe has a boundary, and §4's correction
is its instance: perimeter, skeleton length, convexity (which fails in
both directions), curvature, and the Euler characteristic are *not*
monotone under foreground growth — and β₁ fails directly, since growth fills
holes, which
is exactly why the naive cycle certificate was unsound and the corrected
one decomposes into a wall conjunct (upward) and an interior conjunct
(downward), one per extreme. Non-monotone quantities require such a
decomposition or a different certificate; Lemma 1 as stated does not
cover them, and we do not claim it does.

## 4. The correction: an unsound cycle certificate, caught and fixed

We consider this section part of the method. Adversarial self-verification
is not an afterthought to the certificate; it is what makes the
certificate credible — a certificate system that cannot catch a planted
unsound certificate should not be trusted, and one that never had to
correct itself has probably not been attacked hard enough.

### 4.1 What we originally certified

As first registered, certified 1-cycles were computed as `β₁(CERT_FG)`,
with the justification: "a loop in the minimal foreground persists in all
larger foregrounds."

### 4.2 The counterexample

That justification is **false**: H₁ is not monotone under foreground
growth. Adding pixels can only merge or preserve components (which is why
quantity 2 *is* sound), but it can *destroy* holes by filling them.
Concretely (the counterexample figure): let CERT_FG be a ring whose interior is POSSIBLE.
Then `β₁(CERT_FG) = 1`, and the original certificate called this cycle
robust. But the adversary may, within budget, push every interior pixel
above threshold — a reachable mask by Proposition 1 — and the hole is
gone: `β₁(M) = 0`. An in-budget perturbation destroys the "certified"
cycle. The certificate was unsound. (In persistence terms the trap is
quantitative: this ring's superlevel bar has persistence 0.45 —
comfortably above 2ε = 0.2 — yet the hole dies, because a long bar need
not straddle the threshold window at ½; see §6.)

### 4.3 Why the in-code check missed it

The soundness harness of §3.6 existed at the time and passed — because it
tested only the component and tessera classes. Cycles were never attacked:
the check enumerated worst-case masks for the classes it knew about, and
nobody had told it a cycle was a class. The lesson we draw is specific:
*every* certified predicate needs its own adversary in the harness, and a
predicate without one should be treated as unverified.

### 4.4 The fix

The corrected certificate is the unfillable hole of §3.5: a cycle is
certified iff its enclosed region is CERT_BG (so it cannot be filled)
walled by CERT_FG (so it cannot leak). The harness gained a `cycle` class
attacked at both extremes, and the regression suite now encodes the exact
counterexample: ring-over-POSSIBLE is *not* certified;
ring-over-CERT_BG is certified and survives the attack; a planted unsound
cycle is caught. The equivalence of the enclosure computation with cubical
image-persistence (§3.5) was pre-registered and verified afterwards as
an independent cross-check on the fixed definition.

### 4.5 Provenance

The unsoundness was found on 2026-07-12 by an adversarial-verification
pass (two independent AI soundness reviewers attacking the registered claims;
the review record is preserved with the released code), *before* the real-model track ran:
no real-`p` number was ever reported under the unsound definition. In the
same pass, a metric-semantics overclaim was corrected: a "certified
component fraction" (predicted components ≥50%-covered by CERT_FG) was
renamed to a coverage proxy, because a ≥50%-covered component pinched
through POSSIBLE can still split — coverage is not connectivity, the
recurring theme of this paper. The registry preserves the original claims
verbatim alongside the correction addendum; the paper you are reading
states only the corrected forms.

## 5. Experiments

**Setup.** Real track (T-real): 30 real mosaic crops (the full frozen
evaluation set) through a frozen zero-shot GROUT checkpoint
(`grout_b3_zeroshot_v1`) [lovecky2026grout]; `p` is the sigmoid of the
model's patch logits. Crops are 512×512 px, which is the unit the runtimes
of Appendix E are quoted per.
Toy track (T-toy): 24 synthetic 256×256 mosaic masks from our own
generator with simulated scores

> `p = clip(GaussianBlur(mask, σ=1.3) + N(0, 0.07²))`

retained strictly as a validation track (§5.3). Sweep and
conventions as in §2; seeds fixed. Table 3 reports the toy run that carries
the persistence-cycle and connectivity columns. The regression suite — including the planted-unsound and
counterexample cases — passes (§10).

### 5.1 T-real: sound and non-vacuous on real model outputs

*(Anatomy figure: the worst-coverage crop at ε = 0.10,
`crop_byzantine_01` — score map, tricolor sandwich at ε = 0.10
with certified unfillable holes outlined in green, and ε = 0.40 where
abstention floods; `figs/fig_anatomy`.)*

Soundness first, because nothing else matters if it fails: the soundness
gate passes with **0 violations in 16,675,936 checks** across all four
certified classes this run emitted (components, tessera cores, corrected
cycles, and connectivity segments) and all ε (§3.6).
The certificate then turns out to be far from vacuous on real outputs:

**Table 2 — T-real sweep** (frozen zero-shot model, 30 crops; per-crop
means; `generated/table_real.md` regenerates this from the committed
results file). Per §2 no ratio stands alone, so the denominators, which are
ε-independent, are: coverage and conn-len are over a mean skeleton length of
24,728.9 px per crop; conn-seg is over 2,739.8 segments per crop; abstain is
over the ROI, here the whole 512×512 crop. The ε-varying numerators at
ε = 0.10 and 0.40 are certified length 23,408.1 and 14,969.8 px, and
certified segments 2,173.2 and 1,003.5. Each tabled fraction is the mean of
the per-crop ratios, not the ratio of the means.

| ε | coverage | conn-len | conn-seg | #comp | #tess | #cyc-encl | #cyc-pers | abstain |
|---|---|---|---|---|---|---|---|---|
| 0.02 | 0.988 | 0.921 | 0.916 | 17.9 | 530.5 | 471.5 | 740.6 | 0.016 |
| 0.05 | 0.971 | 0.848 | 0.841 | 18.1 | 533.2 | 462.9 | 684.9 | 0.040 |
| 0.10 | 0.942 | 0.766 | 0.761 | 20.3 | 537.3 | 439.0 | 606.6 | 0.080 |
| 0.15 | 0.908 | 0.700 | 0.696 | 22.5 | 540.2 | 411.4 | 532.0 | 0.123 |
| 0.25 | 0.823 | 0.577 | 0.575 | 30.2 | 536.4 | 342.7 | 398.4 | 0.219 |
| 0.40 | 0.598 | 0.343 | 0.348 | 41.7 | 474.6 | 171.4 | 186.7 | 0.438 |

Readings. At an illustrative mid-sweep ε = 0.10, **94%** of predicted grout length is
certainly-foreground with 20.3 certified components and 439.0 certified
enclosed cycles per crop on average — and, now measured on real `p`,
**0.766** of grout length is certified to stay *connected* (unbroken). The
model is confident on these crops, so the calibration-defined useful
budget is large (0.425, snapped to 0.40); even there **60%** of grout
length is certainly-foreground and **0.343** is certified-connected, with
41.7 certified components and 171.4 certified cycles (per-crop means).
Worst-case over the 30 crops — the right headline for a worst-case paper — the cohort floors hold: coverage 0.187 and certified connectivity 0.028
at ε = 0.40 (each the minimum over the 30 crops, on *different* crops; the
full per-crop distribution is in Appendix A). Our pre-registered non-vacuity criterion — at least 50% of grout length
certainly-foreground, with at least one certified component, at the useful ε —
passes; the registered kill
condition (<10% certified at every useful ε) is not triggered. The
component count *rises* with ε (17.9 → 41.7) — that is CERT_FG
fragmenting, counted as certified fragments, not evidence of more
structure.

### 5.2 Coverage is not connectivity — the headline pair

The largest number in this paper (94% coverage) is a coverage statement.
The corresponding *connectivity* certificate — grout that certainly stays
unbroken — is a different, strictly smaller number, and we report both
everywhere, never one for the other. We measure
it on real `p`: at the useful ε = 0.40, coverage is 0.598 while the strict
certified-connected length fraction is **0.343** — a **1.7×** gap (**1.2×**
at ε = 0.10). The gap is real — connectivity is always the smaller
number — but on real model outputs it is *modest*, because the confident
model keeps most segments entirely inside CERT_FG.

The order-of-magnitude gap lives only on the near-tautological toy track,
where at ε = 0.40 coverage is 0.500 versus certified-connected length
**0.036** (segment fraction 0.062) — a **~14×** collapse (the sweep figure,
right panel; the pinch figure shows the mechanism: one two-pixel POSSIBLE
pinch disqualifies a
segment whose coverage is 96%). That collapse is a property of the toy
maps, not the certificate: the toy scores are lightly-blurred masks whose
skeletons turn POSSIBLE *en masse* at large ε, whereas the real maps are
sharp enough that connectivity largely survives (0.343 of grout length
certified unbroken even at the largest calibrated budget). Reporting the
two numbers separately still matters — blurring them converts a sound
coverage statement into an unsound connectivity claim, the same failure
mode as §4 at the level of prose rather than code — but the real-track
headline is a 1.7× gap, not an order of magnitude.

### 5.3 T-toy: validation track, with its caveat stated verbatim

The toy scores are `GaussianBlur(GT mask, σ=1.3) + noise 0.07` — in the
words of the results file: "a lightly-blurred copy of the answer key.
Certifying that its topology survives small perturbations is close to
tautological, and the 'useful ε' is calibrated from the *same* `p`, so
clearing 50% is partly self-fulfilling. These numbers demonstrate the
machinery runs and produces non-empty certificates on plausible-looking
input — nothing about real-model behavior." We still print the toy table
because engineered maps are where soundness is easiest to attack and where
the persistence-cycle and connectivity columns were first
validated — not because it is the only track carrying them; the real track
now does too (Table 2, §5.1).

**Table 3 — toy-track sweep** (24 synthetic maps; per-map
means; `generated/table_toy.md` regenerates this).

| ε | coverage | conn-len | conn-seg | #comp | #tess | #cyc-encl | #cyc-pers | abstain |
|---|---|---|---|---|---|---|---|---|
| 0.02 | 0.996 | 0.971 | 0.969 | 0.7 | 185.8 | 151.71 | 214.58 | 0.019 |
| 0.05 | 0.990 | 0.925 | 0.926 | 0.6 | 180.4 | 146.38 | 203.08 | 0.048 |
| 0.10 | 0.974 | 0.842 | 0.854 | 0.6 | 169.4 | 135.12 | 183.96 | 0.101 |
| 0.15 | 0.945 | 0.752 | 0.773 | 0.8 | 157.0 | 117.67 | 152.04 | 0.159 |
| 0.25 | 0.841 | 0.572 | 0.598 | 3.5 | 134.6 | 71.12 | 73.25 | 0.284 |
| 0.40 | 0.500 | 0.036 | 0.062 | 18.1 | 28.2 | 0.04 | 1.38 | 0.536 |

On this run's own calibration (0.361 → ε = 0.40) the ≥50%-coverage
criterion narrowly fails (0.4998) — reported for completeness; per the
caveat above, toy non-vacuity is illustrative either way. Soundness on the
toy track: 0 violations, including the connectivity predicate.

### 5.4 Nesting

Certificates over decreasing ε are monotone-nested — `CERT_FG(ε′) ⊇
CERT_FG(ε)` for ε′ ≤ ε, exact set containment, so every certified quantity
that is a *measure* of the certified sets — coverage, certified length,
abstain fraction — is monotone along the sweep. Counts are not, and the
tables show it: component and cavity counts are not monotone functionals
of set inclusion (§3.7), so `#comp` and `#tess` move non-monotonically in
Tables 2 and 3 as CERT_FG fragments and CERT_BG merges. One topological
count *is* provably monotone: by the diagram identity of §5.5 the
persistence-form cycle count at ε
is the number of points of `p`'s fixed superlevel diagram straddling
`[½−ε, ½+ε]`, and widening ε can only shrink that set, so `#cyc-pers` is
non-increasing in ε — on every crop individually, not merely in the mean.
Exact set containment is asserted and unit-tested (a pre-registered
prediction; it holds on both
tracks, registering the induced monotonicity of the coverage column). This is the hook for the
graded extension of §8: the sandwich family over ε *is* a nested
(α-graded) structure already.

### 5.5 Persistence vs enclosure: an equivalence that holds only locally

We pre-registered the two computations of §3.5 as equivalent. That is
confirmed on the regression cases (0 / 1 / 9 on ring-over-POSSIBLE /
ring-over-CERT_BG / 3×3 grid of holes; planted-unsound not certified) and
**refuted as a general identity** — we record the refutation rather than
quietly narrowing the claim, as with §4. The two columns diverge in *both*
directions, for two distinct reasons. Persistence exceeds enclosure where
enclosure applies the ROI and scale floor: on noisy toy maps at ε = 0.40,
persistence 1.38 vs floored enclosure 0.04 (per-map means), the difference
being sub-floor debris the definition excludes. Enclosure exceeds
persistence where a POSSIBLE channel subdivides one cavity into several
guaranteed-background regions (§3.5); this occurs on real `p` at the larger
budgets. The equivalence therefore holds exactly when each enclosed cavity
contains a single CERT_BG component, and not otherwise. The enclosure
column remains the headline count — it is the localisable, per-region
certificate — and the persistence column is reported alongside it as the
rank bound, not as the same number measured twice.

The identity goes further, and we pre-registered it before running the
check: the persistence-form count
at *every* swept ε equals the number of points of `p`'s own superlevel
diagram straddling the window `[½−ε, ½+ε]` — verified exactly on every
crop and every ε (a registered check; §10), so the entire ε-sweep of
certified cycles is derivable from one diagram per crop, and §6's rank
identity is machine-checked rather than asserted.

### 5.6 The ε estimator is split-half stable

Because ε is estimated (median confidence margin, §2) rather than chosen,
its stability is an empirical question, and we register and measure it:
across 200 random 15/15 splits of the real crops, the calibration
estimator's split-half drift is median 0.016 (maximum 0.071) — small
against the 0.15 gap between adjacent sweep points at the operating
budget — and the two halves select the *same* grid point in 200 of 200
resamples, so the held-out certified quantities are identical by
construction. We do not *learn* ε against the certified quantities, and
would not: the band is the assumption the certificate is conditioned on,
and optimizing it against certified counts would invert the semantics (a
band chosen to flatter the model certifies nothing about the domain). The
estimator is certificate-blind by design — it reads only the score map's
margins — and the exactly-nested sweep (§5.4) already quantifies the
consequence of any mis-estimate.

### 5.7 Cross-domain replication: two retinal-vessel datasets

Nothing in §§2–4 is specific to mosaics (§3.7), so we stress-test the
certificate off the mosaic domain entirely, on retinal blood-vessel maps —
the setting where connectivity is the *clinical* question. We use DRIVE
[staal2004drive] (20 images) and CHASE_DB1 [fraz2012chase] (20 images) and,
with **no trained model**, build a score map `p` per image from multiscale
Frangi vesselness [frangi1998vessel] under three monotone normalizations
(cbrt, sqrt, log) with an Otsu-calibrated logistic, then run the identical
certificate.

*(Vessel montage: fundus green channel → Frangi `p` → the ε-sandwich at
ε = 0.10 (vessel tree certified blue) and the useful ε = 0.25 (abstention, more so on CHASE's over-segmented map), for DRIVE and CHASE_DB1.
`figs/fig_vessels`.)*

*(Decoupling figure: per-image Dice vs. each certified quantity, both
datasets, cbrt; Spearman ρ per dataset. `figs/fig_decoupling`.)*

**Soundness holds cross-domain — even on degenerate maps.** The headline is
negative space: across both datasets and all three normalizations the
soundness harness reports **0 violations in 10,578,388 checks** (DRIVE
2,963,152 at the full 16-mask setting; CHASE 7,615,236 at 4 masks — the two
deterministic extremes plus two cross-checks, exhaustive by Lemma 1, for
the denser vessel maps). This includes a genuinely adversarial regime for
the certificate: CHASE's cbrt normalization badly over-segments (median
foreground ≈ 29% of the field of view, per-image Dice against the manual
tracing only 0.30), so the certificate must reason about *hundreds* of
certified components and thousands of connectivity segments per image — and
it stays sound. A worst-case certificate that only held on well-behaved
maps would be far less useful; ours holds regardless of the underlying
prediction's quality.

**Coverage is accuracy-linked; the topological certificates are not simple
Dice proxies.** Correlating each per-image certified quantity with that
image's Dice (Spearman ρ, primary cbrt normalization): coverage tracks Dice
on both datasets (ρ = +0.65 on DRIVE, +0.60 on CHASE, both p < 0.05) —
expected, since coverage is essentially a confidence measure. The
topological invariants behave differently and *inconsistently*:
on DRIVE they decouple from Dice (certified-connected fraction ρ = +0.15,
β₀ ρ = −0.42, both n.s.), whereas on CHASE's degenerate cbrt maps they
correlate (ρ = +0.57, +0.51, both p < 0.05) — because in that
over-segmented regime more certified structure and less-bad accuracy
degrade together; under the better-behaved sqrt/log normalizations they
decouple on both datasets. The reading is not "topology is
orthogonal to accuracy": it is that the certified topological quantities
are **not reducible to Dice**, and their relationship to it is
regime-dependent — so they must be reported as their own numbers (the
recurring theme of §5.2), never inferred from an accuracy score. The full
per-transform ρ table lives in the committed results files.

### 5.8 An inter-rater budget: ε from annotation disagreement

Where two human tracings exist, ε need not come from the model's own
margins (§2) — it can be read from *inter-observer disagreement*, the
irreducible uncertainty of the task itself. On the CHASE images with two
independent manual tracings, the median confidence margin `|p − ½|` over
the pixels the two annotators label differently is 0.246, snapping to
ε = 0.25 (the two tracings agree at Dice 0.773). Certifying at this budget
answers a specifically clinical question — which topological features
survive perturbations no larger than the disagreement between two trained
human annotators — and grounds ε in a medical protocol rather than a model
statistic. The certificate machinery is unchanged.

## 6. Related work

**Certified segmentation via randomized smoothing.** Smoothing-based
certification [cohen2019smoothing], scaled to segmentation
[fischer2021segcert], certifies *pixelwise labels* under input-space
perturbations, typically with an abstain mechanism. This is the natural
*supplier* for our machinery, not a competitor: pixelwise certified label
bounds are an interval field on the score map, which is exactly what the
sandwich consumes (§8). What smoothing does not provide — and what we add
on the map level — is the topological layer: components, enclosures,
connectivity, cycles, quantified against the whole reachable set at once.
As of this writing no smoothing-based segmentation certifier — including
the hierarchical AdaptiveCertify [anani2024adaptive] — certifies any
topological invariant; all operate on per-pixel labels.

**Topology-aware training.** clDice [shit2021cldice], persistent-homology
losses [hu2019topo; clough2020topological], and Betti matching
[stucki2023betti] improve topological fidelity of the *learned* map. They
are complementary in the strongest sense: they change `p`, we certify a
given `p`. None of them yields a worst-case statement about a particular
output; that is not a criticism — it is a different problem, and it is the
problem this paper addresses.

**Persistence stability, image persistence, and well groups.** Our
certified-cycle count is a persistence quantity, and we say which one:
writing `F_t = {p ≥ t}` for the closed superlevel filtration of the score
map and `F°_t = {p > t}` for its open counterpart, the *persistence-form*
count of §3.5 is

> `rank H1(F°_{½+ε} → F_{½−ε})`

— by the standard rank formula, the number of points of `p`'s superlevel
persistence diagram with birth `> ½+ε` and death `< ½−ε`, i.e. alive across
the entire window `[½−ε, ½+ε]`. The strict inequality at the source end is
exactly `CERT_FG = {p−ε > ½}`, and the target end `F_{½−ε}` is exactly
`~CERT_BG` under the non-strict background test of §2; the headline
enclosure count is this rank only when each cavity holds a single CERT_BG
component (§3.5, §5.5). The stability theorem
[cohensteiner2007stability] recovers exactly this number as a lower bound:
`‖p′−p‖∞ ≤ ε` moves the diagram by at most ε in bottleneck distance, so
every window-straddling point yields a hole in every reachable mask. Three
things do not follow from stability. First, identity and localisation: a
bottleneck matching is existential and non-canonical — it preserves the
*count* of holes, not *which* holes; our certificate pins each feature by
containment, with per-feature pixel support from the enclosure form, and
its "same feature across masks" semantics is that of inclusion-induced
maps — image persistence [cohensteiner2009image], the machinery also
underlying Betti matching [stucki2023betti] — not a diagram metric. In
particular the folklore reading "persistence exceeding 2ε implies the
feature survives" is **false** at a fixed threshold: the counterexample
figure's fillable ring has superlevel persistence 0.45 > 2ε = 0.2, yet an ε = 0.1
perturbation destroys it — its bar, though long, does not straddle the
window at ½. Window-straddling, not persistence, is the correct
criterion, and it is what we compute; §4 is the story of what happens
when this distinction is missed. Second, completeness and witnesses:
stability is a one-way inequality, whereas Proposition 1 characterises
the reachable set exactly, so every hole failing the straddle criterion ships
with an explicit in-budget attack mask (features excluded by the ROI or the
scale floor are filtered out by definition, not defeated by an adversary) (filled at `M_max` or breached at
`M_min`). Third, scope: the connectivity class — designated endpoints
staying in one component — plus coverage and abstention are not
functionals of any persistence diagram (Appendix B gives two maps with
identical superlevel diagrams and opposite connectivity verdicts), so no
stability statement speaks to them. In the other direction stability is
strictly broader where it applies: all thresholds at once, arbitrary
filtrations, graceful degradation in Wasserstein distance; our
construction is the single-threshold instantiation made exact — an ℓ∞
ε-band *is* an ε-interleaving of superlevel filtrations. The closest
prior notion is the **well group** of a level set [emp2011wellgroups;
bendich2013levelsets]: homology classes surviving every ε-perturbation —
our universal quantifier. In this codimension-zero cubical setting the
ε-well group of the ½-superlevel set is exactly the image whose rank we
compute; well groups are incomplete and uncomputable in general
[franek2015wellgroups], while §3.5 is an operational,
implementation-verified instance with localisation, witnesses, and
non-homological companions.

**Uncertain-field topology and three-valued abstraction.** Mandatory
critical points of uncertain scalar fields [gunther2014mandatory]
compute, from per-vertex lower/upper bound fields, regions where critical
points must occur in every realization — interval-bound "must" topology,
shipped in TTK. They neither produce a thresholded-segmentation
certificate nor characterise the reachable mask set exactly (Proposition
1), and provide no per-feature attack witnesses or soundness harness.
More abstractly, the sandwich is a three-valued (Kleene) abstraction of
the thresholded image, and the two extremes are the
pessimistic/optimistic completions of three-valued model checking
[bruns1999threevalued]; Lemma 1 is the image-topology instance of that
classical duality — what this paper adds to it is the exactness of the
abstraction (Proposition 1), the tightness of the two-mask check (§3.6),
and the certified-class instantiation with its harness. A further
adjacent line certifies downstream *classifiers* via Lipschitz control of
persistence representations [agerberg2025certifying] — diagram-metric
robustness of a prediction, not set-level feature survival of the
segmentation; topology-*enforcing* segmentation [topoguarantee2026]
constrains the output's topology without certifying its robustness
(enforcement is not certification); and conformal morphological margins
[mossina2025conformal] give distribution-free *statistical* coverage of
the truth mask — complementary outer bounds to our worst-case machinery.
To our knowledge, ours is the only method that is simultaneously
worst-case, topological, about the segmentation output itself, and
verified by checked predicates with attack witnesses rather than sampling
(delta table, Appendix D).

**Abstract interpretation.** The sandwich is an interval abstract domain
for the thresholding operator, in the sense of [cousot1977]; Proposition 1
says the abstraction is exact for this (monotone) operator. The soundness
harness is then best understood as *testing the abstract transformer
against its concretisation* at the extremal points.

**Benson's unconditional life.** Benson [benson1976] computes Go groups
that are alive under any sequence of opponent moves, by a monotone
fixpoint over "vital regions" — an adversarially quantified, purely
combinatorial certificate. Our construction shares the shape: a monotone
operator, an adversary quantified over an explicit reachable set, and a
certificate that is checked, not sampled.

## 7. Limitations (the honest ledger)

1. **Coverage is the big number; connectivity is the honest one.** 94% /
   60% are coverage; the strict certified-connectivity fraction is always
   smaller and answers "does the grout certainly stay unbroken?" — on real
   `p` it is 0.766 / 0.343 at ε = 0.10 / 0.40 (a modest 1.2–1.7× gap),
   collapsing to an order of magnitude only on the near-tautological toy
   track (0.036 vs 0.500 at ε = 0.40), where the blurred maps fragment
   (§5.2).
2. **Score-map-level threat model.** Nothing here certifies the
   input→map pipeline (§1, §2); composition is an interface (§8), not a
   result.
3. **Small real study; non-vacuity is single-domain.** The *non-vacuity*
   headline rests on 30 crops, one task (mosaic grout), one frozen
   checkpoint; a larger real study would tighten that distribution.
   *Soundness* is validated more broadly — cross-domain on two
   retinal-vessel datasets (§5.7) — but we make no non-vacuity claim there
   (CHASE's cbrt maps are degenerate). The machinery itself is task-agnostic
   for binary maps thresholded at ½.
4. **Cycle localisation granularity.** Persistence supplies the certified
   count; localisation uses the enclosure form (per-cycle generators are
   not extracted). The raw persistence count is unfiltered by ROI/scale
   floor and is reported as a cross-check column, not the headline.
5. **Toy track is nearly tautological** — caveat quoted verbatim in §5.3;
   we rely on it only for machinery validation, never for evidence about
   real-model behaviour.

**Abstention is not the contribution.** For a scalar binary score, the
POSSIBLE band `|p − ½| ≤ ε` is a monotone transform of predictive
entropy, so the abstain map by itself is equivalent to entropy
thresholding and we claim no novelty for it. The contribution is what is
*extracted* from the band — worst-case topological guarantees; entropy
thresholding by itself certifies nothing about connectivity or holes. The
hero figure is the visual form of this distinction: the per-pixel margin
calls nearly every pixel confident, while the per-feature certified budgets
are graded and far sparser, because a feature's budget is the *minimum*
over its wall and its interior — an aggregate no per-pixel map contains.

## 8. Future work

**Composition with input-space certification.** Any method producing
per-pixel bounds `[l(x), u(x)]` on the score map under input-space
perturbations — randomized smoothing at segmentation scale
[fischer2021segcert], interval bound propagation [gowal2018ibp] — supplies
an interval field that replaces `[p−ε, p+ε]` pointwise; Proposition 1 and
every certificate in §3 apply unchanged to the resulting (per-pixel,
non-uniform) sandwich. That composition would yield end-to-end certified
topology. We state the interface and stop: it is not built, and nothing
above claims it.

**Graded certificates.** The exact nesting of §5.4 means the family
`{sandwich(ε)}` is a filtration in ε; equivalently, `(p, ε)` defines an
interval-valued image whose α-cuts are the sandwiches. A graded
certificate — "this cycle survives to ε₁, that component to ε₂" — is then
a persistence structure over the ε-axis itself. For cycles this is not
hypothetical: each certified cycle already carries its exact maximal
budget

> `ε* = min(p_birth − ½, ½ − p_death)`,

read off the same superlevel diagram as the identity of §5.5. The construction connects to the graded
fuzzy-partition representation lineage of the F-transform
[perfilieva2006ftransform]. The per-feature budgets themselves are
readable today and we visualise them (the hero figure); what is *not* built
is the graded object proper — a persistence structure over the ε-axis with
its own diagram, stability, and matching. That remains mathematical framing.

**Multi-class segmentation.** Per-class one-vs-rest score maps yield
exact per-class sandwiches (Proposition 1 applies to each map
separately); the joint labeling set embeds strictly into their product,
so cross-class predicates — certified adjacency of two named regions,
certified separation of class pairs — are sound but conservative when
read off the product. The certificate types this enables
(organ-touches-organ, phase contact) have no pixelwise analogue; we
develop them separately.

**Temporal.** Per-frame certificates lift through the product lattice to
certified topological *events* for free; certified *identity* of a
feature across frames does not, and is the open problem.

**Contingent topology.** Intervals of the §3.5 filtration born or dying
at the middle level flag holes present in *some but not all* reachable
masks — a certified / contingent / absent triple per homology degree at
zero extra compute; its per-mask quantifier semantics remain to be pinned
down, so we report nothing under it yet.

## 9. Conclusion

An ℓ∞ band around a frozen score map pins the reachable binary masks to a
lattice interval *exactly* (Proposition 1), and over that interval a
conjunction of monotone predicates is settled by its two extremes — both of
them necessary, and not replaceable by any fixed budget of random masks
(Lemma 1, §3.6). That is the whole engine; the certified components,
tessera cores, unfillable holes, and unbroken segments are instantiations
of it, each shipped with the adversary that would break it.

Two things we would ask a reader to carry away are corrections rather than
claims. First, the instantiation is not mechanical: our own first cycle
certificate was unsound, because H₁ is not monotone under foreground
growth, and it survived an existing harness that simply did not know cycles
were a class (§4). Second, coverage is not connectivity: they differ by
1.2–1.7× on real maps and by an order of magnitude on blurred ones, so we
report them as two numbers and never one (§5.2). The certificate is also
not a confidence map — a feature's budget is the minimum over its wall
*and* its interior, an aggregate no per-pixel margin contains (the hero
figure).

What we do not claim bounds what we do: nothing here certifies the
input→score-map pipeline, and the non-vacuity numbers are one mosaic task
and one frozen checkpoint. Soundness, though, held everywhere we attacked
it — 16,675,936 checks on real mosaic crops and 10,578,388 across two
retinal-vessel datasets, zero violations, including on maps degenerate
enough that a certificate had every excuse to break.

## 10. Reproducibility and disclosure

**Reproducibility.** The experiment directory is registration-first in git
history: the registry (hypotheses, adversaries, kill conditions, fixed
conditions including the ε sweep, connectivity conventions, scale floor,
and seeds) precedes the run code. Corrections are appended as addenda that
preserve the original claims verbatim rather than edited in place, and
there are now two: the unsound β₁ cycle certificate of §4, and the
refutation of the registered persistence/enclosure equivalence (§5.5).
Both were found the same way — a registered claim checked against a case
its own regression suite did not cover — and both are recorded with the
construction that breaks them. The wording of every guarantee in Table 1
is locked in a guarantee-statement file that this paper's claims are
checked against, and that file carries the same two revisions. Tables 2–3 are regenerated from the
committed result files by `tables.py`; figures by `make_figs.py`;
`check_numbers.py` traces every numeral in this paper to its source file
or derivation. Test suite: 21/21, including the planted-unsound and
counterexample regressions.

**AI involvement.** The experimental campaign was executed by an agentic
AI system under human adjudication, with pre-registration (registry before
code, claims locked before prose). The unsound cycle certificate of §4 was
caught by an adversarial-verification pass using two independent AI
reviewers; the finding, the halt, and the correction were adjudicated by
the human author.

---

## References

*(Keys resolve in `refs.bib`; entries appear only after identity
verification against primary sources. No pending placeholders remain.)*

- [benson1976] Benson — unconditional life in Go.
- [cohen2019smoothing] Cohen, Rosenfeld, Kolter — randomized smoothing.
- [fischer2021segcert] Fischer, Baader, Vechev — certified segmentation.
- [shit2021cldice] Shit et al. — clDice.
- [stucki2023betti] Stucki et al. — Betti matching.
- [hu2019topo] Hu et al. — topology-preserving segmentation.
- [clough2020topological] Clough et al. — persistent-homology loss.
- [cohensteiner2007stability] Cohen-Steiner, Edelsbrunner, Harer — stability.
- [cohensteiner2009image] Cohen-Steiner, Edelsbrunner, Harer, Morozov — image persistence.
- [cousot1977] Cousot & Cousot — abstract interpretation.
- [gowal2018ibp] Gowal et al. — interval bound propagation.
- [gudhi] The GUDHI library.
- [perfilieva2006ftransform] Perfilieva — F-transform.
- [lovecky2026grout] Lovecký — GROUT, zero-shot mosaic segmentation.
- [anani2024adaptive] Anani, Lorenz, Schiele, Fritz — adaptive hierarchical certification.
- [emp2011wellgroups] Edelsbrunner, Morozov, Patel — robustness of intersections (well groups).
- [bendich2013levelsets] Bendich, Edelsbrunner, Morozov, Patel — robustness of level and interlevel sets.
- [franek2015wellgroups] Franek & Krčál — computability and triviality of well groups.
- [gunther2014mandatory] Günther, Salmon, Tierny — mandatory critical points of uncertain fields.
- [bruns1999threevalued] Bruns & Godefroid — three-valued model checking.
- [agerberg2025certifying] Agerberg et al. — certifying robustness via topological representations.
- [topoguarantee2026] Li, Tai, Liu — topology-guaranteed image segmentation.
- [mossina2025conformal] Mossina & Friedrich — conformal morphological prediction sets.
- [staal2004drive] Staal et al. — DRIVE retinal vessel dataset.
- [fraz2012chase] Fraz et al. — CHASE_DB1 retinal vessel dataset.
- [frangi1998vessel] Frangi et al. — multiscale vessel enhancement filtering.

## Appendix A — Per-crop distributions, and how the tables are rounded

Tables 2 and 3 report per-crop *means*; this appendix gives the underlying
spread. Figure A.1 shows the per-crop distribution of coverage and
certified-connected length across the 30 real crops at each ε (box = IQR,
whiskers = range), with the cohort minimum marked — the worst-case floors
quoted in §5.1 are read off it, and they fall on *different* crops for the
two quantities.

*(`figs/fig_worstcrop`.)*

The tables themselves are complete for the swept grid; exact unrounded
values are in the released results files (`results_real_hardened.json`,
`results_toy_hardened.json`) and are regenerated by `tables.py`. Rounding
convention, applied per column rather than per value: fractions to 3
decimals; per-crop mean counts to 1 decimal, except Table 3's two cycle
columns, which carry 2 throughout because their values fall below 1 at the
largest budgets.

## Appendix B — The counterexample constructions

The counterexample figure's grids are the regression-test arrays: a 40×40 field, background
score 0.05, ring `8 < r < 14` at score 0.95, interior `r ≤ 8` at score 0.5
(fillable case) or 0.05 (unfillable case), ε = 0.1. Under the sandwich:
the ring is CERT_FG in both cases; the interior is POSSIBLE in the first
(0.5 ± 0.1 straddles ½) and CERT_BG in the second (0.05 + 0.1 < ½).
`β₁(CERT_FG) = 1` in both; only the second survives the all-POSSIBLE→
foreground extreme. The pinch figure's pinched bar: a 30×60 field, bar rows 13–16,
columns 5–54 (inclusive) at 0.95, with the two pinch columns 29–30 at
0.55 — above threshold (so the skeleton spans) but within ε = 0.1 of ½
(so the two pinch pixels per row are POSSIBLE, and the spanning segment
is not certified-connected).

**Connectivity is not a diagram functional.** Take three identical
CERT_FG squares X, Y, Z over CERT_BG background and one CERT_FG bridge of
fixed shape: joining X–Y (map A) or joining Y–Z (map B) produces
identical superlevel persistence diagrams in every degree — the diagram
is location-blind — yet with designated endpoints in X and Y, map A's
pair is certified-connected while map B's pair is certainly separated in
every reachable mask. No functional of the persistence diagram computes
the connectivity class; that certificate is not a persistence statement.

## Appendix C — Soundness-check accounting

Every emitted certified class is checked against 32 reachable masks: the
two deterministic extremes plus 30 random reachable masks. The real-track
total across 30 crops, the four certified classes (components,
tessera cores, corrected cycles, and connectivity
segments), and the six-point ε sweep is 16,675,936 individual checks —
exactly 32 × 521,123 class instances — with 0 violations. The check for a
foreground class asserts connectivity and presence in the minimal mask;
for a background core, absence from the maximal mask; for a cycle, hole
persistence at both extremes; for a connectivity segment, endpoint
connectedness in the minimal mask.

**Random-mask baseline (registered).** To measure §3.6's tightness claim,
`random_baseline.py` plants fillable square rings (interior area = `c`)
and pinched bars (min-cut `c` verified exactly by max-flow) and scores the
*semantic* violation events — hole destroyed, endpoints disconnected —
under two samplers: the uniform reachable-mask model of §3.6 and the
harness's own (per-mask `q ~ U(0.1, 0.9)`, iid per pixel). Detection
probabilities are computed exactly (closed form for the ring; full
pinch-block enumeration for the bar) and Monte-Carlo cross-checked; the
committed `results_random_baseline.json` shows fair-coin ring detection
equal to `2^{-c}` exactly, the harness sampler decaying exponentially with a
slower base (0.9 rather than ½, times a `1/(c+1)` factor)
rather than exponentially (an advantage of biased sampling that still
vanishes as `c` grows), and every planted violation caught at exactly one
extreme — rings at `M_max`, bars at `M_min` — never the other.

## Appendix D — Related-work delta table

Every cell verified against the primary source (staging notes committed in
the repo). Main-text one-sentence version at the end of §6.

| Method | Output certified | Threat model | Worst-case? | Topological? | Checked vs sampled |
|---|---|---|---|---|---|
| SegCertify [fischer2021segcert] / AdaptiveCertify [anani2024adaptive] | per-pixel labels | input-space (smoothing) | probabilistic | no | sampled |
| Betti matching [stucki2023betti] and topology-aware losses | training loss on the learned map | none | no | yes (loss) | n/a (training) |
| Well groups [emp2011wellgroups; bendich2013levelsets] | level-set homology rank of a fixed field | ℓ∞ on the field | yes | yes | diagram read; uncomputable in general [franek2015wellgroups] |
| Mandatory critical points [gunther2014mandatory] | guaranteed critical-point regions | per-vertex interval bounds | yes | yes | tree pairing / visualization |
| Topology-guaranteed segmentation [topoguarantee2026] | enforced connectivity/genus of the output | none | no (enforce ≠ certify) | yes | optimization |
| Conformal morphological sets [mossina2025conformal] | statistical coverage of the truth mask | calibration exchangeability | probabilistic | no | calibrated margin |
| PH-representation robustness [agerberg2025certifying] | downstream label via persistence features | input Lipschitz | yes (label) | diagram-metric | Lipschitz bound |
| **INTACT (this paper)** | **four topological classes of the segmentation itself** | **ℓ∞ on `p`** | **yes** | **yes** | **checked + adversarial harness with witnesses** |

## Appendix E — Compute and runtime

All certification is CPU-only; a single desktop GPU (RTX 4080, 16 GB) is
used once, for the frozen model's inference over the 30 crops. On one core,
uncontended, the full per-unit cost (certification *plus* the soundness
harness) is ≈ 51 s per mosaic (crop, ε) at the 32-mask setting and ≈ 104 s
per retinal (image, ε) at 16 masks (≈ 36 s at 4). Certification proper is
only 1–14 s of that; the soundness harness — thousands of certified classes
× the mask budget — is the bulk, which is exactly why the two-extreme
minimality of §3.6 matters in practice (the extremes are exhaustive, so a
mask budget above two buys only cross-checks). The per-(unit, ε) cells are
independent, so the whole study is embarrassingly parallel: the 30-crop real
mosaic run (`run_parallel.py`) and the retinal study (DRIVE via `drive_v2.py`
and CHASE's 20 images × 3 normalizations × 6 ε via `chase_parallel.py`) each
finish in minutes-to-a-couple-hours of wall
time on the 24-thread machine (64 GB RAM). A near-linear implementation of
the connectivity segment graph (§3.4) was load-bearing: it cut dense-vessel
certification from > 20 minutes to ≈ 14 s per (image, ε), without which the
retinal study was intractable.
