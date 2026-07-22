# TOPOCERT — the guarantee statement (wording lock, Track-1c)

**Anti-overclaim contract.** These are the ONLY claims the paper may make from
this certificate. Each is itemised with the exact object certified, its
worst-case adversary, and its scope caveat. Nothing beyond this list is
claimed. Soundness (0 violations) is verified by the worst-case-exhaustive
`soundness_check` at the deterministic extremes (all-POSSIBLE→bg and →fg) plus
random reachable masks, for every predicate below.

## The single sentence the paper may claim

> For a frozen GROUT soft map `p` and an ℓ∞ perturbation budget `ε`, define the
> sandwich `CERT_FG = {p−ε > ½}`, `CERT_BG = {p+ε < ½}` (PEDANTIC-widened).
> Then **no ℓ∞-ε perturbation of `p` can move a CERT_FG pixel out of the grout
> foreground or a CERT_BG pixel out of the background**, and consequently the
> five itemised quantities below are certified robust to the entire ε-band —
> with the honest distinction that *coverage* (how much grout is certainly
> foreground) is NOT *connectivity* (whether a grout line certainly stays
> unbroken), which is reported separately and is strictly smaller.

## The five certified quantities (each with adversary + caveat)

1. **Coverage — certainly-foreground fraction** `grout_len_certainly_fg_frac`.
   *Claim:* fraction of the p-skeleton lying in CERT_FG. *Adversary:* per-pixel
   ℓ∞-ε; a CERT_FG pixel is foreground in every reachable mask. *Caveat:* a
   SOUND COVERAGE statement, **NOT** connectivity — a covered line pinched
   through POSSIBLE can still split. Report as a fraction AND absolute length.

2. **Certified β0 components** `n_certified_components` = connected components
   of CERT_FG (8-conn). *Claim:* each is connected in EVERY reachable mask.
   *Adversary:* superset preserves connectivity (CERT_FG ⊆ M), so worst case
   cannot disconnect. *Caveat:* these are CERT_FG's OWN components (absolute
   count), not p's components.

3. **Certified enclosed tesserae** `n_certified_tesserae` = connected
   components of CERT_BG (4-conn), ROI+scale-floor filtered. *Claim:* each stays
   fully background in every reachable mask. *Adversary:* CERT_BG ⊆ background
   of every M. *Caveat:* a tessera CORE, not the whole tile.

4. **Certified-CONNECTED grout fraction** (NEW, Track-1b)
   `certified_connected_seg_frac` / `certified_connected_len_frac`. *Claim:*
   fraction of skeleton SEGMENTS (junction-to-junction) lying ENTIRELY in
   CERT_FG — such a segment's endpoints stay connected under ANY ε-perturbation
   (a single POSSIBLE pinch disqualifies it). *Adversary:* all-POSSIBLE→bg
   (`kind='connectivity'`, 0 violations). *Caveat:* strictly ≤ coverage (1);
   this is the HONEST connectivity number and is expected much lower than
   coverage at large ε.

5. **Certified 1-cycles**, reported as TWO quantities with distinct semantics
   (revised 2026-07-22, Correction Addendum 2 in REGISTRY.md):
   `n_certified_cycles_enclosure` = CERT_BG regions walled by CERT_FG, ROI and
   scale-floor filtered — the headline count; and
   `n_certified_cycles_persistence` = rank of the image
   `H1(CERT_FG ↪ ~CERT_BG)` via cubical persistence (gudhi). *Claim:* each
   enclosed region is a hole whose wall is guaranteed foreground and whose
   interior is guaranteed background — unfillable and unleakable in every
   reachable mask; the rank additionally lower-bounds `β₁(M)` for every
   reachable `M`. *Adversary:* both extremes (`kind='cycle'`, 0 violations).
   *Caveat:* the two are NOT equal in general. They agree on the regression
   cases and whenever each cavity holds a single CERT_BG component; the rank is
   SMALLER when a POSSIBLE channel splits one cavity into several CERT_BG
   components, and LARGER where enclosure applies its ROI/scale floor. Only the
   rank is a Betti bound; only enclosure localises (persistence gives the count,
   not per-cycle generators).

## What is explicitly NOT claimed
- No end-to-end "the whole grout network certainly stays connected" — only the
  per-segment certified-connected fraction (item 4).
- No data-coverage / ground-truth claim — the certificate is about robustness
  of THIS `p` to ε, not about correctness of `p`.
- No claim on POSSIBLE (abstain) pixels — reported honestly as uncertain.
- Metrics are ABSOLUTE with companions (standing rule); ratios never stand
  alone.

## Provenance
Soundness proven (H-C1, 0 violations incl. the new connectivity predicate),
non-vacuous on real p (T-real, authoritative). The β1 unsoundness caught by
adversarial verification (2026-07-12) was corrected before any real number.
Track-1 hardening (1a persistence, 1b connectivity, 1c this file) added no new
unsoundness (H-C1 remains 0 violations).
