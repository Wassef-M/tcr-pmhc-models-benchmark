from pathlib import Path
import yaml

input_dir = Path("inputs/classI_yamls")
output_dir = Path("inputs/classI_yamls_no_msa")

output_dir.mkdir(parents=True, exist_ok=True)

for yaml_file in sorted(input_dir.glob("*.yaml")):
    with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)

    for item in data.get("sequences", []):
        if "protein" in item:
            item["protein"]["msa"] = "empty"

    output_file = output_dir / yaml_file.name

    with open(output_file, "w") as f:
        yaml.dump(data, f, sort_keys=False)

    print(f"Created: {output_file}")

print("Done.")
