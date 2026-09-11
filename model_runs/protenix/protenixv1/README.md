# Protenix v1 run scripts — mixed cluster origin

The three input conditions for Protenix v1 were run on two different
machines:

| Script | Condition | Ran on |
|---|---|---|
| `run_protenix_v1_classI_with_msa_helmholtz.sh` | MSA only | Helmholtz (SLURM) |
| `run_protenix_v1_classI_with_msa_with_template_helmholtz.sh` | MSA + template | Helmholtz (SLURM) |
| `run_protenix_v1_classI_jsons_no_msa.sh` | No MSA | deNBI (local GPU box) |

The two Helmholtz scripts are renamed from their originals (`run_protenix.sh`,
`run_protenix_with_template.sh`) for clarity alongside the deNBI naming
convention; their contents are otherwise unchanged and still contain
Helmholtz-specific SLURM/`/lustre` paths that will need adjusting for any
other cluster. The deNBI script uses a local Python venv and
`CUDA_HOME=/usr/local/cuda-12.6` instead.
