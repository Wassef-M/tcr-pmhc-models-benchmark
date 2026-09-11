"""
Extract ipTM, pTM, chain-pair ipTM, and annotated interface ipTM for all 5 samples.

Models covered: af3, intellifold2, protenix_v1, protenix_v2
Output: analysis/iptm_extracted_v4.csv

Chain assignments:
  ClassI  (4 chains): A=MHC_heavy(0), B=peptide(1), C=TCR_alpha(2), D=TCR_beta(3)
  ClassII (5 chains): A=MHC_alpha(0), B=peptide(1), C=MHC_beta(2), D=TCR_alpha(3), E=TCR_beta(4)

Added vs v3: overall ptm + per-chain ptm columns (ptm_mhc, ptm_pep, ptm_mhcb, ptm_tcra, ptm_tcrb)
  ptm_mhcb is empty for classI rows (no MHC beta chain).
"""

import csv
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT_DIR = BASE / "analysis"
OUT_CSV = OUT_DIR / "iptm_extracted_v4.csv"

FIELDNAMES = [
    "model", "mhc_class", "condition", "target",
    "sample", "ranking_score", "is_best_ranked",
    # overall confidence scores
    "iptm", "ptm",
    "n_chains",
    # per-chain pTM
    "ptm_mhc",       # classI: chain A;  classII: MHCa (chain A)
    "ptm_pep",       # chain B both classes
    "ptm_mhcb",      # classII only: chain C
    "ptm_tcra",      # classI: chain C;  classII: chain D
    "ptm_tcrb",      # classI: chain D;  classII: chain E
    # within-pMHC chain-pair ipTM
    "cp_mhc_pep",
    "cp_mhca_mhcb",  # classII only
    "cp_mhcb_pep",   # classII only
    # pMHC–TCR interface chain-pair ipTM
    "cp_mhc_tcra",
    "cp_mhc_tcrb",
    "cp_pep_tcra",
    "cp_pep_tcrb",
    "cp_mhcb_tcra",  # classII only
    "cp_mhcb_tcrb",  # classII only
    # within-TCR chain-pair ipTM
    "cp_tcra_tcrb",
    # summary interface metric
    "mean_tcr_pmhc_iptm",
    # raw matrix kept for reference
    "chain_pair_iptm",
]


def annotate(row: dict, mat: list, chain_ptm: list) -> dict:
    """Add named pTM and chain-pair ipTM columns to a row dict."""

    def cp(i, j):
        return mat[i][j]

    mhc_class = row["mhc_class"]

    if mhc_class == "classI":
        # A=0 MHC_heavy, B=1 peptide, C=2 TCR_alpha, D=3 TCR_beta
        row["ptm_mhc"]   = chain_ptm[0]
        row["ptm_pep"]   = chain_ptm[1]
        row["ptm_mhcb"]  = ""
        row["ptm_tcra"]  = chain_ptm[2]
        row["ptm_tcrb"]  = chain_ptm[3]

        row["cp_mhc_pep"]    = cp(0, 1)
        row["cp_mhca_mhcb"]  = ""
        row["cp_mhcb_pep"]   = ""
        row["cp_mhc_tcra"]   = cp(0, 2)
        row["cp_mhc_tcrb"]   = cp(0, 3)
        row["cp_pep_tcra"]   = cp(1, 2)
        row["cp_pep_tcrb"]   = cp(1, 3)
        row["cp_mhcb_tcra"]  = ""
        row["cp_mhcb_tcrb"]  = ""
        row["cp_tcra_tcrb"]  = cp(2, 3)
        row["mean_tcr_pmhc_iptm"] = (cp(0, 2) + cp(0, 3) + cp(1, 2) + cp(1, 3)) / 4

    elif mhc_class == "classII":
        # A=0 MHC_alpha, B=1 peptide, C=2 MHC_beta, D=3 TCR_alpha, E=4 TCR_beta
        row["ptm_mhc"]   = chain_ptm[0]   # MHCa
        row["ptm_pep"]   = chain_ptm[1]
        row["ptm_mhcb"]  = chain_ptm[2]
        row["ptm_tcra"]  = chain_ptm[3]
        row["ptm_tcrb"]  = chain_ptm[4]

        row["cp_mhc_pep"]    = cp(0, 1)
        row["cp_mhca_mhcb"]  = cp(0, 2)
        row["cp_mhcb_pep"]   = cp(1, 2)
        row["cp_mhc_tcra"]   = cp(0, 3)
        row["cp_mhc_tcrb"]   = cp(0, 4)
        row["cp_pep_tcra"]   = cp(1, 3)
        row["cp_pep_tcrb"]   = cp(1, 4)
        row["cp_mhcb_tcra"]  = cp(2, 3)
        row["cp_mhcb_tcrb"]  = cp(2, 4)
        row["cp_tcra_tcrb"]  = cp(3, 4)
        row["mean_tcr_pmhc_iptm"] = (
            cp(0, 3) + cp(0, 4) + cp(1, 3) + cp(1, 4) + cp(2, 3) + cp(2, 4)
        ) / 6

    return row


# ---------------------------------------------------------------------------
# AF3
# ---------------------------------------------------------------------------

AF3_BASE = BASE / "af3"

AF3_RESULT_DIRS = [
    ("classI",  "with_msa_with_template",  AF3_BASE / "results_classI_with_msa_with_template"),
    ("classI",  "with_msa_no_template",    AF3_BASE / "results_classI_with_msa_no_template"),
    ("classI",  "no_msa_no_template",      AF3_BASE / "results_classI_no_msa_no_template"),
    ("classII", "with_msa_with_template",  AF3_BASE / "results_classII_with_msa_with_template"),
    ("classII", "with_msa_no_template",    AF3_BASE / "results_classII_with_msa_no_template"),
    ("classII", "no_msa_no_template",      AF3_BASE / "results_classII_no_msa_no_template"),
]


def iter_af3(rows):
    for mhc_class, condition, result_dir in AF3_RESULT_DIRS:
        if not result_dir.exists():
            print(f"  MISSING {result_dir}")
            continue

        for outer_dir in sorted(p for p in result_dir.iterdir() if p.is_dir()):
            ranking_files = sorted(outer_dir.rglob("ranking_scores.csv"))
            if len(ranking_files) != 1:
                print(f"  SKIP af3/{mhc_class}/{condition}/{outer_dir.name}: "
                      f"found {len(ranking_files)} ranking_scores.csv")
                continue

            ranking_csv = ranking_files[0]
            real_target_dir = ranking_csv.parent

            target_name = outer_dir.name
            for prefix in ("results_classII_", "results_classI_", "results_"):
                if target_name.startswith(prefix):
                    target_name = target_name[len(prefix):]
                    break

            with open(ranking_csv, newline="") as f:
                ranked = sorted(csv.DictReader(f),
                                key=lambda r: float(r["ranking_score"]), reverse=True)
            if not ranked:
                print(f"  SKIP af3/{mhc_class}/{condition}/{target_name}: empty ranking CSV")
                continue

            best_sample = int(ranked[0]["sample"])

            for csv_row in ranked:
                sample = int(csv_row["sample"])
                ranking_score = float(csv_row["ranking_score"])

                conf_path = real_target_dir / f"seed-1_sample-{sample}" / "summary_confidences.json"
                if not conf_path.exists():
                    print(f"  SKIP af3/{mhc_class}/{condition}/{target_name} "
                          f"sample-{sample}: missing {conf_path.name}")
                    continue

                conf = json.load(open(conf_path))
                mat = conf["chain_pair_iptm"]
                chain_ptm = conf["chain_ptm"]

                row = {
                    "model": "af3",
                    "mhc_class": mhc_class,
                    "condition": condition,
                    "target": target_name,
                    "sample": sample,
                    "ranking_score": ranking_score,
                    "is_best_ranked": sample == best_sample,
                    "iptm": conf["iptm"],
                    "ptm": conf["ptm"],
                    "n_chains": len(mat),
                    "chain_pair_iptm": json.dumps(mat),
                }
                rows.append(annotate(row, mat, chain_ptm))


# ---------------------------------------------------------------------------
# Protenix (v1 and v2)
# ---------------------------------------------------------------------------

PROTENIX_BASE = BASE / "protenix" / "results"
PROTENIX_CONDITIONS = ["with_msa_with_template", "with_msa_no_template", "no_msa_no_template"]
PROTENIX_VERSIONS  = ["v1", "v2"]
PROTENIX_CLASSES   = ["classI", "classII"]


def iter_protenix(rows):
    for version in PROTENIX_VERSIONS:
        for mhc_class in PROTENIX_CLASSES:
            for condition in PROTENIX_CONDITIONS:
                result_dir = PROTENIX_BASE / f"{mhc_class}_protenix_{version}_{condition}"
                if not result_dir.exists():
                    print(f"  MISSING {result_dir}")
                    continue

                for target_outer in sorted(p for p in result_dir.iterdir() if p.is_dir()):
                    target_name = target_outer.name
                    pred_dir = target_outer / target_name / "seed_42" / "predictions"

                    if not pred_dir.exists():
                        print(f"  SKIP protenix_{version}/{mhc_class}/{condition}/{target_name}: "
                              f"missing predictions dir")
                        continue

                    conf_files = sorted(
                        pred_dir.glob(f"{target_name}_summary_confidence_sample_*.json")
                    )
                    if not conf_files:
                        print(f"  SKIP protenix_{version}/{mhc_class}/{condition}/{target_name}: "
                              f"no summary_confidence files")
                        continue

                    samples = []
                    for cf in conf_files:
                        m = re.search(r"sample_(\d+)\.json$", cf.name)
                        if not m:
                            continue
                        sample_num = int(m.group(1))
                        data = json.load(open(cf))
                        score = float(data.get("ranking_score", -1))
                        samples.append((sample_num, score, data))

                    if not samples:
                        continue

                    best_sample = max(samples, key=lambda t: t[1])[0]

                    for sample_num, score, data in sorted(samples, key=lambda t: t[0]):
                        mat = data["chain_pair_iptm"]
                        chain_ptm = data["chain_ptm"]
                        row = {
                            "model": f"protenix_{version}",
                            "mhc_class": mhc_class,
                            "condition": condition,
                            "target": target_name,
                            "sample": sample_num,
                            "ranking_score": score,
                            "is_best_ranked": sample_num == best_sample,
                            "iptm": data["iptm"],
                            "ptm": data["ptm"],
                            "n_chains": len(mat),
                            "chain_pair_iptm": json.dumps(mat),
                        }
                        rows.append(annotate(row, mat, chain_ptm))


# ---------------------------------------------------------------------------
# IntelliFold2
# ---------------------------------------------------------------------------

IF2_BASE = BASE / "intellifold2" / "results"
IF2_CONDITIONS = ["with_msa_with_template", "with_msa_no_template", "no_msa_no_template"]
IF2_CLASSES    = ["classI", "classII"]


def iter_intellifold2(rows):
    for mhc_class in IF2_CLASSES:
        for condition in IF2_CONDITIONS:
            result_dir = IF2_BASE / f"{mhc_class}_v2_{condition}"
            if not result_dir.exists():
                print(f"  MISSING {result_dir}")
                continue

            for target_outer in sorted(p for p in result_dir.iterdir() if p.is_dir()):
                target_name = target_outer.name
                pred_dir = target_outer / target_name / "predictions" / target_name

                if not pred_dir.exists():
                    print(f"  SKIP intellifold2/{mhc_class}/{condition}/{target_name}: "
                          f"missing predictions dir")
                    continue

                conf_files = sorted(
                    pred_dir.glob(f"{target_name}_seed-42_sample-*_summary_confidences.json")
                )
                if not conf_files:
                    print(f"  SKIP intellifold2/{mhc_class}/{condition}/{target_name}: "
                          f"no summary_confidences files")
                    continue

                samples = []
                for cf in conf_files:
                    m = re.search(r"sample-(\d+)_summary", cf.name)
                    if not m:
                        continue
                    sample_num = int(m.group(1))
                    data = json.load(open(cf))
                    score = float(data.get("ranking_score", -1))
                    samples.append((sample_num, score, data))

                if not samples:
                    continue

                best_sample = max(samples, key=lambda t: t[1])[0]

                for sample_num, score, data in sorted(samples, key=lambda t: t[0]):
                    mat = data["chain_pair_iptm"]
                    chain_ptm = data["chain_ptm"]
                    row = {
                        "model": "intellifold2",
                        "mhc_class": mhc_class,
                        "condition": condition,
                        "target": target_name,
                        "sample": sample_num,
                        "ranking_score": score,
                        "is_best_ranked": sample_num == best_sample,
                        "iptm": data["iptm"],
                        "ptm": data["ptm"],
                        "n_chains": len(mat),
                        "chain_pair_iptm": json.dumps(mat),
                    }
                    rows.append(annotate(row, mat, chain_ptm))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUT_DIR.mkdir(exist_ok=True)
    rows = []

    print("=== AF3 ===")
    iter_af3(rows)
    print(f"  -> {sum(1 for r in rows if r['model'] == 'af3')} rows")

    print("=== Protenix ===")
    iter_protenix(rows)
    print(f"  -> {sum(1 for r in rows if r['model'].startswith('protenix'))} rows")

    print("=== IntelliFold2 ===")
    iter_intellifold2(rows)
    print(f"  -> {sum(1 for r in rows if r['model'] == 'intellifold2')} rows")

    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nTotal rows : {len(rows)}")
    print(f"Best-ranked: {sum(1 for r in rows if r['is_best_ranked'] == True)}")
    print(f"Written to : {OUT_CSV}")

    # Spot-check one classI and one classII row
    print("\n--- Spot-check (best-ranked only) ---")
    for cls in ("classI", "classII"):
        r = next((x for x in rows if x["mhc_class"] == cls and x["is_best_ranked"] == True), None)
        if r:
            print(f"\n{cls}  model={r['model']}  target={r['target']}")
            for col in FIELDNAMES[7:]:
                if col != "chain_pair_iptm":
                    print(f"  {col:22s}: {r.get(col, '')}")


if __name__ == "__main__":
    main()
