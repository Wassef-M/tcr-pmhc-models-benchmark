#!/usr/bin/env python3

import json
from pathlib import Path

INPUT_DIR = Path("classI_jsons_af3")
OUTPUT_DIR = Path("classI_jsons_protenix_re_run_with_msa_and_template")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for infile in sorted(INPUT_DIR.glob("*.json")):
    with open(infile, "r") as f:
        af3 = json.load(f)

    protenix = [
        {
            "name": af3["name"],
            "sequences": []
        }
    ]

    for entry in af3["sequences"]:
        protein = entry["protein"]
        protenix[0]["sequences"].append(
            {
                "proteinChain": {
                    "id": [protein["id"]],
                    "sequence": protein["sequence"],
                    "count": 1
                }
            }
        )

    outfile = OUTPUT_DIR / infile.name
    with open(outfile, "w") as f:
        json.dump(protenix, f, indent=2)

    print(f"Converted {infile.name} -> {outfile}")
