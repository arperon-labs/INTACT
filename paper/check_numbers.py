"""Every numeral in paper.md traced to a source or an explicit
justification. Exit 0 = clean; exit 1 = untraced numerals (printed with
context). Sources are the committed results files, the real-run log, and
code constants (read-only over experiments/).

  python check_numbers.py
"""
import json
import re
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# NOTE: these anchors are specific to the RELEASE layout (paper/, experiments/,
# docs/, results/ as siblings) and differ from the source repo's. Do not sync
# this file by wholesale copy from the source tree - port changes by hand, or
# the paths break and every ledger check fails on a missing results JSON.
HERE = Path(__file__).resolve().parent
EXTERNAL = Path(os.environ.get("INTACT_EXTERNAL_DATA",
                               HERE.parents[0] / "external-data"))
EXP = HERE.parents[0] / "experiments"
DOC = HERE.parents[0] / "docs"
RES = HERE.parents[0] / "results"
PAPER = HERE / "paper.md"

real = json.loads((RES / "results_real_hardened.json").read_text())
real24 = json.loads((RES / "results.json").read_text())  # committed baseline
toy = json.loads((RES / "results_toy_hardened.json").read_text())
rb = json.loads((RES / "results_random_baseline.json").read_text())
es = json.loads((RES / "results_eps_stability.json").read_text())
dw = json.loads((RES / "results_diagram_window.json").read_text())
drive = json.loads((RES / "results_drive.json").read_text())      # V2
chase = json.loads((RES / "results_chase.json").read_text())      # V2
chase_ir = json.loads((RES / "results_chase_interrater.json").read_text())  # V3
run_py = (EXP / "run.py").read_text()
results_md = (DOC / "RESULTS.md").read_text(encoding="utf-8")


def _validate_first24():
    """The parallel re-emit's first-24-crop means must equal the committed
    24-crop results.json exactly — proves run_parallel.py reproduced the
    serial computation byte-for-byte (the numbers the paper stood on)."""
    pairs = [("coverage", "grout_len_certainly_fg_frac"),
             ("n_components", "n_certified_components"),
             ("n_tessera_cores", "n_certified_tessera_cores"),
             ("n_cycles_enclosure", "n_certified_cycles"),
             ("abstain", "abstain_frac")]
    for e in real["sweep"]:
        pc = real["sweep"][e]["per_crop"]
        b = real24["sweep"][e]
        for pk, bk in pairs:
            if abs(sum(pc[pk][:24]) / 24 - b[bk]) > 1e-9:
                return False
    return True

# ---------------------------------------------------------------- ledger
# Assertions FIRST: the key statistics equal their sources exactly.
led = []


def check(name, cond):
    led.append((name, bool(cond)))


rs, ts = real["sweep"], toy["sweep"]
check("real H-C1 violations == 0", real["H_C1_soundness_violations"] == 0)
check("toy  H-C1 violations == 0", toy["H_C1_soundness_violations"] == 0)
check("real H-C3 nesting pass", real["H_C3_nesting_monotone_pass"] is True)
check("toy  H-C3 nesting pass", toy["H_C3_nesting_monotone_pass"] is True)
check("real H-C2 pass", real["H_C2_nonvacuity_at_useful_eps"]["pass"] is True)
check("toy  H-C2 fail (0.4998 < 0.5)",
      toy["H_C2_nonvacuity_at_useful_eps"]["pass"] is False)
check("real KILL not triggered", real["KILL_abstain_floods"] is False)
check("94% = coverage@0.10", round(rs["0.1"]["grout_len_certainly_fg_frac"]
                                   * 100) == 94)
check("60% = coverage@0.40", round(rs["0.4"]["grout_len_certainly_fg_frac"]
                                   * 100) == 60)
check("useful eps real 0.425", f"{real['useful_eps_calibrated']:.3f}"
      == "0.425" and real["useful_eps_used"] == 0.4)
check("useful eps toy 0.361", f"{toy['useful_eps_calibrated']:.3f}"
      == "0.361" and toy["useful_eps_used"] == 0.4)
check("toy coverage@0.40 = 0.500 / 0.4998",
      f"{ts['0.4']['grout_len_certainly_fg_frac']:.3f}" == "0.500"
      and f"{ts['0.4']['grout_len_certainly_fg_frac']:.4f}" == "0.4998")
check("toy conn-len@0.40 = 0.036",
      f"{ts['0.4']['certified_connected_len_frac']:.3f}" == "0.036")
check("toy conn-seg@0.40 = 0.062",
      f"{ts['0.4']['certified_connected_seg_frac']:.3f}" == "0.062")
check("~14x gap (13.5 <= ratio < 14.5; RESULTS.md quotes ~14x)",
      13.5 <= (ts["0.4"]["grout_len_certainly_fg_frac"]
               / ts["0.4"]["certified_connected_len_frac"]) < 14.5
      and "~14" in results_md)
check("toy pers/encl@0.40 = 1.38 / 0.04",
      f"{ts['0.4']['n_certified_cycles_persistence']:.2f}" == "1.38"
      and f"{ts['0.4']['n_certified_cycles_enclosure']:.2f}" == "0.04")
check("16,675,936 checks (JSON H_C1_checks, hardened 30-crop re-emit)",
      real["H_C1_checks"] == 16675936)
check("16,675,936 = 32 x sum of the FOUR hardened classes "
      "(components+tesserae+enclosure-cycles+connectivity-segments, "
      "x30 crops, x6 eps)",
      int(32 * sum(rs[e]["per_crop"]["n_components"][i]
                   + rs[e]["per_crop"]["n_tessera_cores"][i]
                   + rs[e]["per_crop"]["n_cycles_enclosure"][i]
                   + rs[e]["per_crop"]["n_certified_segments"][i]
                   for e in rs for i in range(30))) == 16675936)
check("n_samples INCLUDES the two extremes (masks k=0,1 in topo.py)",
      "if k == 0" in (EXP / "topo.py").read_text(encoding="utf-8"))
check("real study n_maps == 30 (full frozen set; parallel re-emit)",
      real["n_maps"] == 30)
check("parallel re-emit's first-24 means == committed results.json exactly "
      "(run_parallel.py validated byte-identical)", _validate_first24())
check("real means have denominator 30 (30 crops)",
      all(abs(rs[e]["n_certified_components"] * 30
              - round(rs[e]["n_certified_components"] * 30)) < 1e-6
          for e in rs))
check("real coverage-vs-connectivity gap ~1.2x @0.10, ~1.7x @0.40 "
      "(modest on real p; the ~14x is toy-only)",
      abs(rs["0.1"]["grout_len_certainly_fg_frac"]
          / rs["0.1"]["certified_connected_len_frac"] - 1.23) < 0.05
      and abs(rs["0.4"]["grout_len_certainly_fg_frac"]
              / rs["0.4"]["certified_connected_len_frac"] - 1.74) < 0.05)
check("real worst-crop @0.40: coverage 0.187, conn-len 0.028 (min over 30)",
      f'{min(rs["0.4"]["per_crop"]["coverage"]):.3f}' == "0.187"
      and f'{min(rs["0.4"]["per_crop"]["conn_len_frac"]):.3f}' == "0.028")
check("suite 21/21 per RESULTS.md (pytest verified 2026-07-22)",
      "21/21" in results_md)
check("regression cycle counts 0/1/9 per RESULTS.md",
      "ring-over-POSSIBLE → 0; ring-over-CERT_BG → 1;" in results_md
      and "grid-of-holes → 9" in results_md)
check("interval exactness gap 1.000 (registry)",
      "gap 1.000" in (DOC / "REGISTRY.md").read_text(encoding="utf-8"))
def _m(eps, key):
    import numpy as _np
    return float(_np.mean(rs[eps]["per_crop"][key]))


# Table 2 caption denominators/numerators (Sec 2: "ratios never stand alone").
check("Table 2 caption: skeleton length 24,728.9 px/crop and 2,739.8 segments, "
      "both eps-INDEPENDENT (same at every swept eps)",
      f'{_m("0.1", "skeleton_len_px"):.1f}' == "24728.9"
      and f'{_m("0.1", "n_segments"):.1f}' == "2739.8"
      and len({round(_m(e, "skeleton_len_px"), 4) for e in rs}) == 1
      and len({round(_m(e, "n_segments"), 4) for e in rs}) == 1)
check("Table 2 caption: certified length 23,408.1 / 14,969.8 px at eps 0.10/0.40",
      f'{_m("0.1", "certified_len_px"):.1f}' == "23408.1"
      and f'{_m("0.4", "certified_len_px"):.1f}' == "14969.8")
check("Table 2 caption: certified segments 2,173.2 / 1,003.5 at eps 0.10/0.40",
      f'{_m("0.1", "n_certified_segments"):.1f}' == "2173.2"
      and f'{_m("0.4", "n_certified_segments"):.1f}' == "1003.5")
check("scale floor: 0.5 x fallback tessera width 6.0 px = 3.0 px (run.py)",
      "FLOOR_F = 0.5" in run_py and "6.0" in run_py)
check("all 30 real crops are 512x512 (paper Setup; Appendix E runtime unit)",
      {__import__("numpy").load(f).shape for f in (EXP / "p_maps").glob("*.npy")}
      == {(512, 512)})
realset = EXTERNAL / "data" / "realset" / "crops"
if realset.exists():
    check("realset holds 30 crops", len(list(realset.glob("*.png"))) == 30)
# N8 miss-rate baseline (Appendix C 'Random-mask baseline' + §3.6 sentence)
check("miss-rate: ring fair-coin detection == 2^-c exactly",
      all(abs(r["det_fair_exact"] - 2.0 ** -r["c"]) < 1e-12
          for r in rb["ring"]))
check("miss-rate: bar max-flow min-cut == pinch height",
      all(b["mincut_c"] == b["h"] for b in rb["bar"]))
check("miss-rate: every planted violation caught at exactly the predicted "
      "extreme (rings M_max only, bars M_min only)",
      all(r["extremes"]["caught_at_M_max"]
          and not r["extremes"]["caught_at_M_min"] for r in rb["ring"])
      and all(b["extremes"]["caught_at_M_min"]
              and not b["extremes"]["caught_at_M_max"] for b in rb["bar"]))
check("miss-rate: MC within 3-sigma binomial CI of the exact law "
      "(both samplers, all constructions)",
      all(abs(x[f"det_{s}_mc"] - x[f"det_{s}_exact"])
          <= 3 * (max(x[f"det_{s}_exact"], 1e-9)
                  * (1 - x[f"det_{s}_exact"]) / rb["K_MC"]) ** 0.5 + 1e-5
          for x in rb["ring"] + rb["bar"] for s in ("fair", "harness")))
# S3 split-half eps-stability (§5.6)
check("eps-stability: 200/200 grid agreement (R=200, 30 crops)",
      es["R"] == 200 and es["grid_agreement_rate"] == 1.0
      and es["n_crops"] == 30)
check("eps-stability: drift median 0.016 / max 0.071 at 3 decimals",
      f"{es['drift_median']:.3f}" == "0.016"
      and f"{es['drift_max']:.3f}" == "0.071")
check("eps-stability: 0.15 = adjacent grid gap at the operating budget "
      "(0.4 - 0.25)",
      abs(es["grid_spacing_at_cohort"] - 0.15) < 1e-12
      and es["cohort_snapped"] == 0.4)
# N4 R-EQ diagram-window identity (§5.5 sentence, §8 eps* rider)
check("R-EQ H-R1: window count == persistence-form count on every "
      "(crop, eps): 30 crops x 6 eps, 0 mismatches",
      dw["H_R1_pass"] is True and dw["n_mismatch"] == 0
      and len(dw["crops"]) == 30
      and all(len(v) == 6 for v in dw["crops"].values()))

# V2 cross-domain (DRIVE + CHASE_DB1) + V3 inter-rater (§5.7, §5.8)
_dc = lambda res, q: res["per_transform"]["cbrt"]["spearman_dice_vs"][q]["rho"]
check("V2 DRIVE: 0 viol / 2,963,152 checks, 20 imgs",
      drive["H_C1_violations"] == 0 and drive["H_C1_checks"] == 2963152
      and len(drive["per_transform"]["cbrt"]["per_image"]) == 20)
check("V2 CHASE: 0 viol / 7,615,236 checks, n_samples=4, 20 imgs",
      chase["H_C1_violations"] == 0 and chase["H_C1_checks"] == 7615236
      and chase.get("n_samples") == 4
      and len(chase["per_transform"]["cbrt"]["per_image"]) == 20)
check("V2 combined 10,578,388 = DRIVE + CHASE checks",
      drive["H_C1_checks"] + chase["H_C1_checks"] == 10578388)
check("V2 rho(coverage,Dice) cbrt: +0.65 DRIVE / +0.60 CHASE",
      f"{_dc(drive, 'coverage'):+.2f}" == "+0.65"
      and f"{_dc(chase, 'coverage'):+.2f}" == "+0.60")
check("V2 DRIVE topology DECOUPLED: conn_seg +0.15, beta0 -0.42",
      f"{_dc(drive, 'conn_seg_frac'):+.2f}" == "+0.15"
      and f"{_dc(drive, 'n_components'):+.2f}" == "-0.42")
check("V2 CHASE topology COUPLED (degenerate): conn_seg +0.57, beta0 +0.51",
      f"{_dc(chase, 'conn_seg_frac'):+.2f}" == "+0.57"
      and f"{_dc(chase, 'n_components'):+.2f}" == "+0.51")
check("V2 CHASE cbrt Dice 0.30 (over-segmented regime)",
      f"{chase['per_transform']['cbrt']['dice_mean']:.2f}" == "0.30")
check("V3 inter-rater eps 0.246 -> 0.25; inter-obs Dice 0.773; 20 imgs",
      f"{chase_ir['eps_inter']:.3f}" == "0.246"
      and chase_ir["eps_inter_snapped"] == 0.25
      and f"{chase_ir['interobserver_dice_mean']:.3f}" == "0.773"
      and chase_ir["n_images"] == 20)

# ------------------------------------------------- allowed numeral tokens
allowed = set()


def add(x):
    allowed.add(str(x))


# every table cell at the paper's rounding (real is now hardened: coverage,
# abstain, AND connectivity fractions at 3 dp, like toy)
_cols13 = ["grout_len_certainly_fg_frac", "abstain_frac",
           "certified_connected_len_frac", "certified_connected_seg_frac"]
for sweep, cols13 in ((rs, _cols13), (ts, _cols13)):
    for e, row in sweep.items():
        for k, v in row.items():
            if v is None or isinstance(v, bool):
                continue
            add(f"{v:.3f}") if k in cols13 else None
            if k.startswith("n_"):
                add(f"{v:.1f}"), add(f"{v:.2f}")
add(f"{real['useful_eps_calibrated']:.3f}")   # 0.425
add(f"{toy['useful_eps_calibrated']:.3f}")    # 0.361
add(f"{ts['0.4']['grout_len_certainly_fg_frac']:.4f}")  # 0.4998
add("16,675,936"), add("16675936")
add("10,578,388"), add("10578388")      # V2 combined checks
add("2,963,152"), add("2963152")        # V2 DRIVE checks
add("7,615,236"), add("7615236")        # V2 CHASE checks

JUSTIFIED = {
    # numeral: justification (source or derivation)
    "0.02": "eps sweep (REGISTRY/run.py)", "0.05": "eps sweep + toy bg score",
    "0.10": "eps sweep", "0.15": "eps sweep", "0.25": "eps sweep",
    "0.40": "eps sweep", "0.1": "eps sweep / test eps", "0.4": "eps sweep",
    "94": "round(coverage@0.10*100), ledger", "60": "round(coverage@0.40*100)",
    "50": "H-C2 threshold >=50% (REGISTRY); pinch bar 50 columns",
    "10": "KILL threshold <10% (REGISTRY)",
    "99": "rhetorical illustration ('99% accurate per pixel'), not a result",
    "14": "~14x gap (ledger; RESULTS.md '~14x'); ring outer radius 14 (tests)",
    "0.036": "toy conn-len@0.40 (ledger)", "0.500": "toy coverage@0.40",
    "0.062": "toy conn-seg@0.40 (ledger)", "0.4998": "toy coverage 4-dec",
    "1.38": "toy cycles-persistence@0.40, 2-dec (ledger)",
    "0.04": "toy cycles-enclosure@0.40, 2-dec (ledger)",
    "0.425": "real useful-eps calibrated 0.4252 (ledger)",
    "0.361": "toy useful-eps calibrated (ledger)",
    "24": "T-toy: 24 synthetic maps; committed-baseline 24-crop set (ledger)",
    "30": "T-real: 30 crops (realset; ledger); 30 random masks = 32 - 2 extremes",
    "16": "16 masks (DRIVE soundness); pinch bar rows 13-16 (tests); 16 GB RAM",
    "32": "soundness_check n_samples=32 incl. the 2 extremes (run.py/topo.py)",
    "521,123": "16,675,936 / 32 class instances (ledger, recomputed)",
    "521123": "16,675,936 / 32 class instances (ledger, recomputed)",
    "54": "pinch bar cols 5-54 (tests, inclusive rendering of 5:55)",
    "0": "zero violations / regression count 0 / connectivity 0",
    "1": "regression count 1 / >=1 component / one ulp",
    "9": "grid-of-holes regression count (RESULTS.md); min tessera area 9px (run.py)",
    "3": "3x3 grid-of-holes (tests); junction degree >=3",
    "2": "two reviewers (REGISTRY addendum); 2-px pinch; 2 deterministic extremes",
    "5": "five certified quantities (GUARANTEE_STATEMENT)",
    "1.000": "interval exactness gap (REGISTRY, ledger)",
    "0.95": "test construction score (tests)", "0.55": "pinch score (tests)",
    "0.9": "harness sampler q~U(0.1,0.9) (topo.py soundness_check)",
    "0.45": "ring superlevel bar persistence = 0.95 - 0.5 (App B "
            "construction; §6 folklore callout)",
    "0.2": "2×eps at eps=0.1 (§6/§4.2 folklore callout)",
    "200": "R=200 split-half resamples (eps_stability.py, ledger)",
    "15": "15/15 split of 30 crops (eps_stability.py)",
    "0.016": "split-half drift median (ledger, results_eps_stability.json)",
    "0.071": "split-half drift max (ledger, results_eps_stability.json)",
    "1.3": "toy blur sigma (run.py)", "0.07": "toy noise sigma (run.py)",
    "256": "toy image size (run.py generate img_size=256)",
    "512": "real crop size (all 30 p_maps/*.npy are 512x512; asserted above)",
    "26": "3D adjacency pairing 26/6 (standard digital topology, not a result)",
    "18": "3D adjacency pairing 18/6 (standard digital topology, not a result)",
    "3.0": "scale floor from the 6.0 px fallback tessera width (asserted)",
    "1.0": "retinal-track scale floor, fixed 1.0 px (topo/vessel runners)",
    "24,728.9": "mean skeleton length px/crop (asserted from real JSON)",
    "23,408.1": "mean certified length px/crop @eps=0.10 (asserted)",
    "14,969.8": "mean certified length px/crop @eps=0.40 (asserted)",
    "21": "regression suite size 21/21 (asserted against RESULTS.md)",
    "0.5": "threshold 1/2; FLOOR_F=0.5 (run.py); interior score 0.5",
    "6.0": "tessera-width fallback (run.py)",
    "8": "8-connectivity; ring inner radius 8 (tests)",
    "4": "4-connectivity",
    "48": "pinch bar: 50-2 columns CERT_FG (derived from test construction)",
    "96": "48/50 = 96% (derived from test construction)",
    "40": "counterexample field 40x40 (tests)",
    "60": "pinch field 30x60 (tests)",
    "13": "pinch bar rows 13-16 (tests, inclusive)",
    "29": "pinch cols 29-30 (tests, inclusive rendering of 29:31)",
    "2026-07-12": "correction date (RESULTS.md/REGISTRY.md)",
    "2026": "correction date year (2026-07-12)",
    "1.5": "persistence filtration death threshold >1.5 (RESULTS.md Track-1a)",
    "1.2": "real coverage/conn-len gap @0.10 ~1.23x (ledger)",
    "1.7": "real coverage/conn-len gap @0.40 ~1.74x (ledger)",
    "0.187": "real worst-crop coverage @0.40, min over 30 (ledger)",
    "0.028": "real worst-crop conn-len @0.40, min over 30 (ledger)",
    # V2 cross-domain (DRIVE + CHASE) + V3 inter-rater (ledger-checked)
    "0.65": "V2 rho(coverage,Dice) DRIVE cbrt (ledger)",
    "0.60": "V2 rho(coverage,Dice) CHASE cbrt (ledger)",
    "0.57": "V2 rho(conn_seg,Dice) CHASE cbrt (ledger)",
    "0.51": "V2 rho(beta0,Dice) CHASE cbrt (ledger)",
    "0.42": "V2 rho(beta0,Dice) DRIVE cbrt = -0.42 (ledger)",
    "0.30": "V2 CHASE cbrt Dice mean, degenerate over-seg (ledger)",
    "29": "V2 CHASE cbrt median foreground ~29% FOV (over-seg diagnostic)",
    "0.246": "V3 inter-rater eps unsnapped (ledger)",
    "0.773": "V3 inter-observer Dice (ledger)",
    "20": "V2 DRIVE/CHASE 20 images each (ledger)",
    # S4 compute/runtime (Appendix E; measured uncontended, runtime_s4.py)
    "51": "S4 mosaic cell ~51s @32 masks (measured)",
    "104": "S4 retinal cell ~104s @16 masks (measured)",
    "36": "S4 retinal cell ~36s @4 masks (measured)",
    "14": "S4 certification proper up to ~14s / connectivity ~14s (measured)",
    "4080": "RTX 4080 GPU (hardware)",
    "24": "24-thread machine (hardware)",
    "64": "64 GB RAM (hardware)",
    "0.1.": "draft version v0.1", "7": "target page count 7-9 (meta)",
    "2007": "citation year", "2009": "citation year", "1976": "citation year",
    "1977": "citation year", "2019": "citation year", "2021": "citation year",
    "2023": "citation year", "2018": "citation year", "2022": "citation year",
    "2006": "citation year", "2014": "citation year",
    "12": "date part of 2026-07-12",
    "6": "six-point eps sweep",
}
allowed |= set(JUSTIFIED)

# --------------------------------------------------------- scan the paper
text = PAPER.read_text(encoding="utf-8")
# strip citation keys, headers/anchors, file paths, code spans
text = re.sub(r"\[cite[^\]]*\]|\[[a-z][\w]*\d{4}[\w]*\]", " ", text)
text = re.sub(r"`[^`]*`", " ", text)
# author metadata: an ORCID iD is an identifier, not a claim about results.
# Matches both the displayed id and the orcid.org URL it links to.
text = re.sub(r"(?:https?://orcid\.org/)?\d{4}-\d{4}-\d{4}-\d{3}[\dX]", " ", text)
# section cross-references, headings, table/figure numbering are structural
text = re.sub(r"(§+\s*|\bTable\s+|\bFigure\s+|\bProposition\s+|\bv)\d+(\.\d+)*",
              " ", text)
text = re.sub(r"^#+\s*\d+(\.\d+)*", "#", text, flags=re.M)
text = re.sub(r"σ=1\.3", " 1.3 ", text)

unknown = []
for m in re.finditer(r"(?<![\w./-])(\d[\d,]*(?:\.\d+)?)", text):
    tok = m.group(1).rstrip(".,")
    if tok in allowed or tok.replace(",", "") in allowed:
        continue
    # ranges like 13-17 / 5-55 split by the regex already; ratios 0/1/9 too
    ctx = text[max(0, m.start() - 60):m.end() + 40].replace("\n", " ")
    unknown.append((tok, ctx))

# ------------------------------------------------------------------ report
bad = [n for n, ok in led if not ok]
print("LEDGER:")
for name, ok in led:
    print(f"  [{'OK' if ok else 'FAIL'}] {name}")
if unknown:
    print("\nUNTRACED NUMERALS in paper.md:")
    for tok, ctx in unknown:
        print(f"  {tok!r}  …{ctx}…")
if bad or unknown:
    sys.exit(1)
print(f"\nCLEAN: all ledger checks pass; every numeral in paper.md traced "
      f"({len(allowed)} allowed tokens, {len(JUSTIFIED)} justified).")
