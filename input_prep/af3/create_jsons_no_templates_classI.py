import json
from pathlib import Path

input_dir = Path("classI_jsons")
output_dir = Path("classI_jsons_patched")
output_dir.mkdir(exist_ok=True)

for json_file in input_dir.glob("*.json"):
    with open(json_file) as f:
        data = json.load(f)

    for item in data["sequences"]:
        protein = item["protein"]
        protein["templates"] = []

    out_file = output_dir / json_file.name
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)

print(f"Patched JSON files written to: {output_dir}")
