# AF3 run scripts (Helmholtz SLURM cluster)

All AF3 predictions for this study were generated on a SLURM cluster
(Helmholtz), using these three array jobs - one per input condition, each
looping over the 56 Class I targets (`#SBATCH --array=1-56`):

| Script | Condition |
|---|---|
| `alphafold3_array_classI.sh` | MSA + template |
| `alphafold3_array_no_template_classI.sh` | MSA only (no template) |
| `alphafold3_array_no_msa_no_template_classI.sh` | No MSA |

Each script runs `run_alphafold.py` inside an Apptainer container
(`alphafold3_28jan2025.sif`), bound to a database dir and a model-parameters
dir. **`run_alphafold.py` itself is not included in this repository** - it is
DeepMind's own AlphaFold3 source, released under a restricted, non-commercial
license with gated model-weight access. Obtain it from the
[official AlphaFold3 repository](https://github.com/google-deepmind/alphafold3)
and place it at the path these scripts expect (bound to `/work/run_alphafold.py`
inside the container, i.e. alongside the input JSONs on the host).

Paths (`CONTAINER_IMAGE`, `DB_DIR`, `MODEL_PARAMETERS_DIR`, the `/lustre/...`
input/output layout) are specific to the Helmholtz cluster this study ran on
and will need adjusting for any other SLURM cluster.

Input generation and CIF→PDB conversion, by contrast, are cluster-agnostic -
plain Python/Biopython with no SLURM or Helmholtz-specific paths - and are
included under `input_prep/af3/` and `pdb_conversion/af3/` respectively.
