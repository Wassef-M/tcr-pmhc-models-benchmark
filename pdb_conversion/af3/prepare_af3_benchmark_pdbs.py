import csv
from pathlib import Path
from Bio.PDB import MMCIFParser, PDBIO

BASE = Path(__file__).resolve().parent

OUTPUT_ROOT = (
    BASE.parent
    / "TCR-pMHC-folding-benchmark-main"
    / "benchmark"
    / "pred_pdb"
    / "af3"
    / "pmhc_tcr"
)

RESULTS_DIRS = [
    BASE / "results_classI",
    BASE / "results_classII",
    BASE / "results_classI_no_msa_no_template",
    BASE / "results_classII_no_msa_no_template",
    BASE / "results_classI_no_template",
    BASE / "results_classII_no_template",
]
RESULTS_DIRS = [d for d in RESULTS_DIRS if d.exists()]

parser = MMCIFParser(QUIET=True)


def convert_cif_to_pdb(cif_path: Path, pdb_path: Path):
    structure = parser.get_structure(pdb_path.stem, str(cif_path))
    io = PDBIO()
    io.set_structure(structure)
    io.save(str(pdb_path))


def get_class_name(result_dir: Path) -> str:
    if "classII" in result_dir.name:
        return "classII"
    if "classI" in result_dir.name:
        return "classI"
    raise ValueError(f"Cannot determine class for {result_dir}")


def clean_target_name(name: str) -> str:
    if name.startswith("results_classII_"):
        return name.replace("results_classII_", "", 1)
    if name.startswith("results_classI_"):
        return name.replace("results_classI_", "", 1)
    if name.startswith("results_"):
        return name.replace("results_", "", 1)
    return name


def main():
    n_done = 0
    n_skipped = 0

    for result_dir in RESULTS_DIRS:
        class_name = get_class_name(result_dir)
        out_base = OUTPUT_ROOT / class_name / result_dir.name

        target_dirs = sorted([p for p in result_dir.iterdir() if p.is_dir()])

        for target_dir in target_dirs:
            outer_name = target_dir.name

            ranking_files = sorted(target_dir.rglob("ranking_scores.csv"))

            if len(ranking_files) != 1:
                print(f"SKIP {outer_name}: expected 1 ranking_scores.csv, found {len(ranking_files)}")
                n_skipped += 1
                continue

            ranking_csv = ranking_files[0]
            real_target_dir = ranking_csv.parent
            target_name = clean_target_name(outer_name) 

            rows = []
            with open(ranking_csv, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append({
                        "seed": int(row["seed"]),
                        "sample": int(row["sample"]),
                        "ranking_score": float(row["ranking_score"]),
                    })

            rows_sorted = sorted(rows, key=lambda x: x["ranking_score"], reverse=True)

            if len(rows_sorted) != 5:
                print(f"SKIP {target_name}: expected 5 ranked samples, found {len(rows_sorted)}")
                n_skipped += 1
                continue

            failed = False

            for rank, row in enumerate(rows_sorted):
                sample = row["sample"]
                cif_path = real_target_dir / f"seed-1_sample-{sample}" / "model.cif"

                if not cif_path.exists():
                    print(f"SKIP {target_name}: missing {cif_path}")
                    failed = True
                    break

                out_pdb = out_base / f"ranked_{rank}" / f"{target_name}.pdb"
                out_pdb.parent.mkdir(parents=True, exist_ok=True)
                convert_cif_to_pdb(cif_path, out_pdb)

            if failed:
                n_skipped += 1
                continue

            print(f"DONE {target_name} ({result_dir.name})")
            n_done += 1

    print()
    print(f"Completed targets: {n_done}")
    print(f"Skipped targets:   {n_skipped}")
    print(f"Output root:       {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()