"""
Build the base classI_jsons/ directory: one bare AF3-schema input JSON per
target (chain IDs + sequences only, no MSA/template fields) from Lu et al.'s
per-target sequence file (class-i-seqs.json).

With unpairedMsa/pairedMsa/templates absent entirely (not just set empty),
AF3's own data pipeline computes them at runtime — this is the input consumed
directly by the MSA+template condition (../../model_runs/af3/alphafold3_array_classI.sh).
The MSA-only and no-MSA condition JSONs are derived from this base by
create_jsons_no_templates_classI.py and create_jsons_no_msa_no_template_classI.py,
which explicitly set those fields to ""/[] to disable AF3's own MSA/template search.
"""

import json
import os

input_json = "TCR-pMHC-folding-benchmark-main/benchmark_data/class-i-seqs.json"
output_dir = "classI_jsons"

os.makedirs(output_dir, exist_ok=True)

with open(input_json) as f:
    data = json.load(f)

chain_ids = ["A", "B", "C", "D", "E", "F", "G", "H"]

for entry in data:
    name = entry["name"]
    seqs = entry["sequences"]

    out = {
        "name": name,
        "sequences": [],
        "modelSeeds": [1],
        "dialect": "alphafold3",
        "version": 1,
    }

    for i, seq_block in enumerate(seqs):
        seq = seq_block["proteinChain"]["sequence"]
        out["sequences"].append({
            "protein": {
                "id": chain_ids[i],
                "sequence": seq,
            }
        })

    out_path = os.path.join(output_dir, f"{name}.json")
    with open(out_path, "w") as g:
        json.dump(out, g, indent=2)

print(f"Wrote {len(data)} JSON files to {output_dir}")
