import json
import re
from pathlib import Path
from Bio.PDB import MMCIFParser, PDBIO

BASE = Path(__file__).resolve().parent
INPUT_ROOT = BASE / "results"
OUTPUT_ROOT = (
    BASE.parent
    / "TCR-pMHC-folding-benchmark-main"
    / "benchmark"
    / "pred_pdb"
    / "protenix"
    / "pmhc_tcr"
)
RESULTS_DIRS = sorted([p for p in INPUT_ROOT.iterdir() if p.is_dir()])

parser = MMCIFParser(QUIET=True)


def convert_cif_to_pdb(cif_path: Path, pdb_path: Path):
    structure = parser.get_structure(pdb_path.stem, str(cif_path))
    io = PDBIO()
    io.set_structure(structure)
    io.save(str(pdb_path))


def get_class_name(result_dir: Path) -> str:
    if "classI" in result_dir.name:
        return "classI"
    if "classII" in result_dir.name:
        return "classII"
    raise ValueError(f"Cannot determine class for {result_dir}")


def get_sample_number(path: Path):
    match = re.search(r"sample_(\d+)", path.name)
    if match is None:
        return None
    return int(match.group(1))


def main():
    n_done = 0
    n_skipped = 0

    for result_dir in RESULTS_DIRS:
        class_name = get_class_name(result_dir)
        out_base = OUTPUT_ROOT / class_name / result_dir.name

        target_dirs = sorted([p for p in result_dir.iterdir() if p.is_dir()])
        if not target_dirs:
            print(f"SKIP {result_dir.name}: no target directories found")
            n_skipped += 1
            continue

        for target_outer in target_dirs:
            target_name = target_outer.name
            pred_dir = target_outer / target_name / "seed_42" / "predictions"

            if not pred_dir.exists():
                print(f"SKIP {target_name}: missing prediction directory {pred_dir}")
                n_skipped += 1
                continue

            summary_files = sorted(pred_dir.glob(f"{target_name}_summary_confidence_sample_*.json"))
            if len(summary_files) != 5:
                print(f"SKIP {target_name}: expected 5 summary files, found {len(summary_files)}")
                n_skipped += 1
                continue

            rows = []
            failed = False
            for summary_file in summary_files:
                sample = get_sample_number(summary_file)
                if sample is None:
                    print(f"SKIP {target_name}: could not read sample number from {summary_file.name}")
                    failed = True
                    break

                with open(summary_file) as f:
                    data = json.load(f)

                if "ranking_score" not in data:
                    print(f"SKIP {target_name}: missing ranking_score in {summary_file.name}")
                    failed = True
                    break

                cif_path = pred_dir / f"{target_name}_sample_{sample}.cif"
                if not cif_path.exists():
                    print(f"SKIP {target_name}: missing CIF file {cif_path}")
                    failed = True
                    break

                rows.append({
                    "sample": sample,
                    "ranking_score": float(data["ranking_score"]),
                    "cif_path": cif_path,
                })

            if failed:
                n_skipped += 1
                continue

            rows_sorted = sorted(rows, key=lambda x: x["ranking_score"], reverse=True)
            if len(rows_sorted) != 5:
                print(f"SKIP {target_name}: expected 5 ranked models, found {len(rows_sorted)}")
                n_skipped += 1
                continue

            for rank, row in enumerate(rows_sorted):
                out_pdb = out_base / f"ranked_{rank}" / f"{target_name}.pdb"
                out_pdb.parent.mkdir(parents=True, exist_ok=True)
                convert_cif_to_pdb(row["cif_path"], out_pdb)

            print(f"DONE {target_name} ({result_dir.name})")
            n_done += 1

    print()
    print(f"Completed targets: {n_done}")
    print(f"Skipped targets:   {n_skipped}")
    print(f"Output root:       {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
