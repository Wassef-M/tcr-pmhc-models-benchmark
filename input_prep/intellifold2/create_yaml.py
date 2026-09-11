import os
import json

# Input and output directories
input_dir = "classI_jsons"
output_dir = "classI_yamls"

# Create output directory if it does not exist
os.makedirs(output_dir, exist_ok=True)

# Loop through all JSON files in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith(".json"):
        json_path = os.path.join(input_dir, filename)

        # Read JSON file
        with open(json_path, "r") as f:
            data = json.load(f)

        # Prepare YAML output filename
        yaml_filename = filename.replace(".json", ".yaml")
        yaml_path = os.path.join(output_dir, yaml_filename)

        # Write YAML manually
        with open(yaml_path, "w") as out:
            out.write(f"version: {data['version']}\n")
            out.write(f"name: {data['name']}\n")
            out.write("modelSeeds:\n")
            for seed in data["modelSeeds"]:
                out.write(f"  - {seed}\n")

            out.write("\nsequences:\n")

            for seq_entry in data["sequences"]:
                protein = seq_entry["protein"]
                out.write("  - protein:\n")
                out.write(f"      id: {protein['id']}\n")
                out.write(f"      sequence: {protein['sequence']}\n\n")

print(f"YAML files written to: {output_dir}")
