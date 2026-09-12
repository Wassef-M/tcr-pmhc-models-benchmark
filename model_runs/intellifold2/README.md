# IntelliFold v2 run scripts (Helmholtz SLURM cluster)

All IntelliFold v2 predictions for this study were generated on a SLURM
cluster (Helmholtz), using these two array jobs (`#SBATCH --array=1-56`):

| Script | Condition |
|---|---|
| `run_intellifold2_v2_with_template.sh` | MSA + template (`--use_template`) |
| `run_intellifold2_v2.sh` | MSA only |

The no-MSA condition was produced with the same `run_intellifold2_v2.sh`
script, pointed at the no-MSA YAML inputs instead (per-chain `msa: empty`,
see `input_prep/intellifold2/add_empty_msa_to_yamls.py`) - there is no
separate no-MSA script.

Both scripts use `--use_msa_server` (a remote MSA server, not a local
database) and are otherwise SLURM/Helmholtz-specific (`PROJECT_DIR`, module
environment); adjust for any other cluster.

CIF→PDB conversion is cluster-agnostic and is included under
`pdb_conversion/intellifold2/`.
