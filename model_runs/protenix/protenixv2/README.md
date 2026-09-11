# Protenix v2 run scripts (deNBI local GPU box)

All Protenix v2 predictions for this study were run locally (deNBI), using
a Python 3.11 venv (`env/protenix_env_py311/`) with `CUDA_HOME=/usr/local/cuda-12.6`
and `TORCH_EXTENSIONS_DIR` set for its JIT-compiled CUDA kernels — see the
top-level README's [Setup §2](../../../README.md#2-model-environments-protenix-intellifold2).

| Script | Condition |
|---|---|
| `run_protenix_v2_classI_jsons_with_templates.sh` | MSA + template |
| `run_protenix_v2_classI_jsons_default_with_msa.sh` | MSA only |
| `run_protenix_v2_classI_jsons_no_msa.sh` | No MSA |
