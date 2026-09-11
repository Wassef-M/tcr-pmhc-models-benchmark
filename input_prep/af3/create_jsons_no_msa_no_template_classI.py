import json
from pathlib import Path

input_dir = Path("classI_jsons")
output_dir = Path("classI_jsons_no_msa")
output_dir.mkdir(exist_ok=True)

for json_file in input_dir.glob("*.json"):
    with open(json_file) as f:
        data = json.load(f)

    for item in data["sequences"]:
        protein = item["protein"]
        protein["unpairedMsa"] = ""
        protein["pairedMsa"] = ""
        protein["templates"] = []

    out_file = output_dir / json_file.name
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)

print(f"Wrote MSA-free JSONs to {output_dir}")
