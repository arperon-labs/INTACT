# Zenodo deposit metadata

Fill the Zenodo form from this file. Fields are in the order the form presents
them. Anything marked **DECIDE** needs a choice from you.

---

## Upload type

**Publication → Preprint**

*(Not "Software". The deposit's primary object is the paper. If you also want a
citable software record, make it a second deposit of the repository — Zenodo's
GitHub integration will do it on a release tag — and cross-link the two with
the related identifiers below.)*

## Basic information

| Field | Value |
|---|---|
| **Digital Object Identifier** | leave blank — Zenodo mints it |
| **Publication date** | the day you publish |
| **Title** | `INTACT: Sound Worst-Case Topological Certificates for Segmentation Score Maps` |
| **Version** | `v1` |
| **Language** | `eng` |

## Authors

| Field | Value |
|---|---|
| Name | `Lovecký, Radoslav` |
| Affiliation | `Arperon` |
| ORCID | `0009-0000-5669-920X` |

*(Zenodo wants `Family, Given`. The ORCID belongs here, in the record metadata,
which is why it is not in the paper's title block — here it is machine-readable
and actually links your works together.)*

## Description

Zenodo renders basic HTML. Paste this:

```html
<p><strong>INTACT</strong> (INference-Time Adversarial Certificates for
Topology) computes sound, worst-case topological certificates for thresholded
segmentation score maps: statements that hold on <em>every</em> mask reachable
within a given perturbation budget, not on average and not by sampling.</p>

<p>Given a frozen score map <em>p</em> and an &#8467;<sub>&#8734;</sub> budget
&epsilon;, the &plusmn;&epsilon; band splits the image into a
certainly-foreground core, a certainly-background core, and a POSSIBLE band the
adversary controls. The reachable binary masks are then <em>exactly</em> a
lattice interval (Proposition 1), and over that interval a finite conjunction
of monotone predicates is settled by checking just its two extremes — both
individually necessary, and not replaceable by any fixed budget of random masks
(Lemma 1).</p>

<p>Instantiating the principle yields five certified quantities: certainly-
foreground coverage, certified connected components, certified enclosed
regions, a strict certified-connectivity fraction, and certified 1-cycles
(holes whose wall is certainly foreground and whose interior is certainly
background, so no in-budget perturbation can fill or breach them). Each is
stated with its worst-case adversary and its scope caveat.</p>

<p><strong>Results.</strong> A worst-case-exhaustive soundness harness reports
0 violations in 16,675,936 checks on 30 real mosaic crops through a frozen
zero-shot segmentation model, and 0 violations in 10,578,388 checks across two
retinal-vessel datasets (DRIVE and CHASE_DB1, model-free Frangi maps) — the
latter including a deliberately degenerate regime (Dice 0.30) where the
certificate had every excuse to break. At &epsilon;&nbsp;=&nbsp;0.10, 94% of
predicted grout length is certainly-foreground; the strict certified-connected
fraction is 0.766, and the two are reported separately throughout because
coverage is not connectivity.</p>

<p><strong>Method as reported.</strong> The paper reports two of its own
registered claims being refuted and corrected: an unsound &beta;<sub>1</sub>
cycle certificate (H<sub>1</sub> is not monotone under foreground growth) and a
registered equivalence between two cycle computations that holds only locally.
Both are recorded as addenda that preserve the original claims verbatim, with
the constructions that break them.</p>

<p><strong>Scope.</strong> The certificate operates on perturbations of the
score map. It is <em>not</em> an end-to-end input-space certificate;
composition with input-space methods is stated as an interface, not claimed as
a result.</p>

<p>Code, frozen score maps, committed result files and the pre-registration
record: <a href="https://github.com/arperon-labs/INTACT">github.com/arperon-labs/INTACT</a></p>
```

## Keywords

Paste one per line (Zenodo splits on newline or comma):

```
certified robustness
worst-case certification
topological data analysis
persistent homology
image segmentation
semantic segmentation
adversarial robustness
interval analysis
abstract interpretation
digital topology
connectivity certification
uncertainty quantification
retinal vessel segmentation
cultural heritage imaging
mosaic analysis
pre-registration
reproducible research
INTACT
```

**Note on discoverability.** `IntAct` is also an established EMBL-EBI
molecular-interaction database. Different field, but it dominates the search
term — the keywords above are what will actually surface this record, so keep
the topological and certification terms even if you trim the list.

## License

**DECIDE.** Two sensible options:

- **Creative Commons Attribution 4.0 (CC-BY-4.0)** — the standard choice for a
  preprint, and what most readers expect on a Zenodo document. *Recommended for
  this deposit.*
- **Apache License 2.0** — matches the GitHub repository, but it is a software
  licence and sits oddly on a PDF.

These do not conflict: the repository is Apache-2.0 (code, with its patent
grant), and the Zenodo record can be CC-BY-4.0 (the document). State whichever
you pick; the README already says the Zenodo record carries its own field.

## Related / alternate identifiers

| Relation | Identifier |
|---|---|
| `is supplemented by` | `https://github.com/arperon-labs/INTACT` |
| `cites` | `10.5281/zenodo.18187265` — GROUT, the model producing the real-track score maps |
| `is derived from` | *(leave empty)* |

*(If you later publish a separate software record for the repository, add
`is supplement to` / `is supplemented by` between the two DOIs.)*

## Communities

**DECIDE.** None are required. Candidates worth a look, if you want reach:
`Computer Vision`, `Machine Learning`, `Applied Topology`. Zenodo communities
are curated — submission is a request, not a guarantee, and rejection costs
nothing.

## Funding

None. Leave empty unless Arperon should be recorded as a funder.

## Files to upload

1. `paper.pdf` — the paper *(required)*
2. **DECIDE**: whether to attach a source archive. The repository is public and
   linked in the description, so a duplicate snapshot is optional. If you want
   the record self-contained, attach a zip of the repository at the tagged
   commit.

---

## After Zenodo mints the DOI

The DOI has to go back into the paper, which changes the PDF you uploaded.
Zenodo's versioning handles this: the **concept DOI** is reserved before
publishing, so the sequence is

1. In the deposit form, use **"Reserve DOI"** — this gives you the DOI *before*
   you publish.
2. Send that DOI back; it goes into `paper.tex` / `paper.md` (title block and
   the citation block), the PDF is rebuilt, and `check_numbers` + `check_sync`
   re-run.
3. Upload the rebuilt `paper.pdf`, then publish.

That way the published PDF carries its own DOI. If you publish first instead,
you would need a v2 to correct it.
