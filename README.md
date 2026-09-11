# TCR–pMHC Model Benchmark

We compare three open-source structure prediction models — **IntelliFold v2**,
**Protenix v1**, **Protenix v2** — against **AlphaFold3** as a reference, on the
56 Class I TCR–pMHC complexes curated by
[Lu et al.](https://github.com/Jiadong001/TCR-pMHC-folding-benchmark), across
three input conditions (MSA+template, MSA only, no MSA), looking at DockQ/RMSD
accuracy, confidence-score reliability (iPTM, CDR3 pLDDT), native docking-angle
reproduction, and runtime.

## What's in this repo

This repository holds the code written for this study: the model run scripts,
the scripts that turn model outputs into ranked PDBs, the confidence/runtime
extraction scripts, the docking-angle wrapper, and the adapted evaluation
notebooks. It does **not** include:

- Raw model prediction outputs (CIF/JSON files — hundreds of GB across four
  models × three conditions × 56 targets × 5 samples).
- The reference PDB structures and metadata — these belong to the Lu et al.
  dataset (see [Setup](#setup) below).
- Model weights or model source code (AF3, Protenix, IntelliFold2) — obtain
  these from the model authors directly; AF3 weights in particular are
  restricted-access and not redistributable.

```
model_runs/              Per-model run scripts (.sh) only
  af3/                     Helmholtz SLURM array jobs, all 3 conditions
  intellifold2/            Helmholtz SLURM array jobs, 2 scripts cover all 3 conditions
  protenix/
    protenixv1/              mixed: 2 Helmholtz scripts + 1 deNBI script
    protenixv2/               deNBI, all 3 conditions
input_prep/              Scripts that build model-specific inputs before a run
  af3/                     Lu et al. sequences → classI_jsons → per-condition AF3 JSON
  intellifold2/            classI_jsons → IntelliFold YAML (+ no-MSA variant)
  protenix/                classI_jsons → Protenix JSON
pdb_conversion/           Scripts that rank + convert raw model outputs to PDB
  af3/  intellifold2/  protenix/
metrics_notebooks/       Per-model/condition notebooks computing DockQ/RMSD/pLDDT
  af3/  intellifold2/  protenixv1/  protenixv2/
analysis/                 Cross-model analysis, written for this study
  extract_iptm_v4.py       Confidence-score (iPTM/pTM) extraction, all models
  extract_timing_v2.py     Wall-clock runtime extraction, all models
  docking_angle/           Wrapper around the Pierce lab tcr_docking_angle tool
results/                  Final computed metrics and timings (CSV/TSV)
```

## Pipeline

1. **Generate inputs.** `input_prep/` (see its own
   [README](input_prep/README.md) for the full flow) starts from one base
   directory, `classI_jsons/` — one **bare** AF3-schema JSON per target
   (chain IDs + sequences only, no MSA/template fields), built by
   `af3/build_classI_jsons.py` from Lu et al.'s per-target sequence file
   (`benchmark_data/class-i-seqs.json`). Because those fields are absent
   rather than empty, this base JSON is what AF3's own data pipeline
   consumes directly for the MSA+template condition, computing the MSA and
   searching templates itself at runtime. From there:
   `af3/create_jsons_no_templates_classI.py` and
   `af3/create_jsons_no_msa_no_template_classI.py` derive AF3's MSA-only and
   no-MSA condition JSONs; `intellifold2/create_yaml.py` converts the base
   JSON to IntelliFold's YAML schema, and
   `intellifold2/add_empty_msa_to_yamls.py` derives its no-MSA variant;
   `protenix/make_protenix_jsons.py` converts the base JSON to Protenix's
   schema (Protenix's own `--use_msa`/`--use_template` flags then select the
   condition at run time, see [stage 2](#pipeline)).
2. **Run predictions.** AF3 and IntelliFold2 were run on a SLURM cluster
   (Helmholtz) — see `model_runs/af3/` and `model_runs/intellifold2/` (each
   has a README mapping script → condition). Protenix v2 (all conditions) and
   Protenix v1's no-MSA condition were run on this study's local GPU box
   (deNBI); Protenix v1's MSA and MSA+template conditions were also run on
   Helmholtz — see `model_runs/protenix/protenixv1/README.md` for exactly
   which script produced which condition. AF3's `run_alphafold.py` itself is
   not included (see `model_runs/af3/README.md` and [Known gaps](#known-gaps)).
3. **Convert to ranked PDBs.** `pdb_conversion/<model>/prepare_*_benchmark_pdbs.py`
   ranks the 5 sampled structures per target/condition by the model's own
   `ranking_score`, converts mmCIF→PDB with Biopython, and writes `ranked_0`
   … `ranked_4` into the directory layout expected by the Lu et al.
   evaluation pipeline.
4. **Evaluate metrics.** `metrics_notebooks/<model>/*.ipynb` — copies of Lu et
   al.'s `cal_metrics_i.ipynb`, adapted only in their input paths — compute
   DockQ, global/region/CDR-loop RMSD, and pLDDT for each model/condition.
   These notebooks import `Metrics.utils` and must be run from inside a
   checkout of the Lu et al. repository (see [Setup](#setup)).
5. **Extract confidence & timing.** `analysis/extract_iptm_v4.py` parses each
   model's own confidence JSON output (ipTM, pTM, per-chain-pair ipTM) into
   one CSV; `analysis/extract_timing_v2.py` parses wall-clock runtime from
   job logs. Both expect to be run from the top of the original prediction
   working directory (i.e. with `af3/`, `protenix/`, `intellifold2/`
   subdirectories of raw results alongside them), not from inside this repo.
6. **Docking-angle analysis.** `analysis/docking_angle/` wraps the Pierce lab
   `tcr_docking_angle` tool: `batch_angles.sh` finds every `ranked_*` PDB,
   `angle_worker.sh` + `angle_one.py` normalize chain naming/numbering (via
   ANARCI) and invoke the compiled `tcr_docking_angle` binary per structure,
   and `analyze_angles.py` aggregates docking-/incident-angle error against
   the native structures. `tcr_complex.cc.patch` is a one-line fix (init
   `IsClassII` in the constructor) applied on top of the upstream tool — see
   [Setup](#setup) for how to set this up.

## Setup

Nothing this pipeline depends on is vendored into this repo — it's all
referenced here so the repo stays small and each dependency keeps its own
license. This section is organized by *what you need before which pipeline
stage will run*; you don't need all of it unless you're reproducing the
whole study end to end.

### 1. Upstream repositories

Required for stages 1, 4, and 6 of the [Pipeline](#pipeline).

- **Lu et al. benchmark** — dataset, reference structures, metadata, and the
  DockQ/RMSD/pLDDT evaluation pipeline (`Metrics/`) that
  `metrics_notebooks/*.ipynb` import from, and the sequence file
  `input_prep/af3/build_classI_jsons.py` reads:
  ```bash
  git clone https://github.com/Jiadong001/TCR-pMHC-folding-benchmark.git
  ```
  `metrics_notebooks/*.ipynb` here are already-adapted copies of Lu et al.'s
  `cal_metrics_i.ipynb` (adapted only in their input paths) — they still
  import `Metrics.utils` via `sys.path.append("..")`, so to actually run one,
  copy it into `TCR-pMHC-folding-benchmark/benchmark/<model>/` first; that's
  the only way `..` resolves to a directory containing `Metrics/`.

- **Pierce lab docking-angle tool** — computes TCR–pMHC docking/incident
  angle; requires the GNU Scientific Library (GSL) to compile. See
  [`analysis/docking_angle/README.md`](analysis/docking_angle/README.md) for
  the full, verified build recipe (including a no-sudo/conda path and a
  Linux-specific FAST-library gotcha) and how to run the batch analysis.

### 2. Model environments (Protenix, IntelliFold2)

Required for stage 2. This repo doesn't ship a `requirements.txt` or
`environment.yml` — install each model from its own public repository,
in its own environment, following that repo's instructions:

| Model | Env used in this study | Notes |
|---|---|---|
| Protenix v1 / v2 | Python 3.11 venv at `env/protenix_env_py311/` | Needs `CUDA_HOME=/usr/local/cuda-12.6` and a writable `TORCH_EXTENSIONS_DIR` set before running — Protenix JIT-compiles custom CUDA kernels on first use (see any `run_protenix_v2_*.sh` script). |
| IntelliFold v2 | Python venv at `.venv/` | Run with `--use_msa_server`, i.e. it queries a remote MSA server rather than a local database — no genetic-database download needed for this model. |

Exact package versions were not pinned at the time; if reproducing the
paper's numbers matters (rather than just running the pipeline), install the
same model release / commit referenced in the report.

### 3. AlphaFold3: source, weights, databases, container

Required for stage 2, AF3 only. Getting AF3 running is the heaviest part of
this setup — four separate things, all outside this repo:

1. **`run_alphafold.py`** — DeepMind's own source, restricted non-commercial
   license. Get it from the
   [official AlphaFold3 repository](https://github.com/google-deepmind/alphafold3)
   and place it where `model_runs/af3/*.sh` expects it (bound to
   `/work/run_alphafold.py` inside the container, i.e. alongside the input
   JSONs on the host).
2. **Model weights** — gated; request access per the
   [AF3 weights terms of use](https://github.com/google-deepmind/alphafold3/blob/main/WEIGHTS_TERMS_OF_USE.md).
3. **Genetic sequence databases** — several hundred GB; fetched with the
   official repo's own `fetch_databases.sh` script, not by anything here.
4. **Container image** — the Helmholtz scripts run everything inside an
   Apptainer image (`CONTAINER_IMAGE=.../alphafold3_28jan2025.sif`). Build
   one from AF3's official Dockerfile (`docker build` then
   `apptainer build` / `singularity build` to convert), and update
   `CONTAINER_IMAGE`, `DB_DIR`, and `MODEL_PARAMETERS_DIR` in the `.sh`
   scripts to your own paths — the ones checked in are Helmholtz-specific.

### 4. Command-line tools (ANARCI, HMMER, Kalign)

Required for stage 2 ("with template" conditions) and stage 6. Install via
conda (recommended — these are standard bioconda packages):

```bash
conda install -c bioconda anarci hmmer kalign2
```

- **ANARCI** — antibody/TCR numbering. Used by `analysis/docking_angle/`
  (`angle_one.py`, `inspect_chains.py`) to type and AHo-renumber TCR chains,
  and internally by the upstream `tcr_docking_angle` tool's own
  `renumber_tcr.py`. Must be on `PATH` as the `ANARCI` command.
- **`hmmsearch` / `hmmbuild`** (from HMMER) **and `kalign`** — used for
  template search when running Protenix or IntelliFold2 under the "with
  template" condition. Some run scripts (e.g.
  `run_protenix_v2_classI_jsons_with_templates.sh`) explicitly prepend a
  separate `bio-tools` conda env's `bin/` to `PATH` to find these — adjust
  that to wherever you install them.

## Known gaps

Every run script that produced a published result, and every input-generation
script, is now included (see the per-model READMEs under `model_runs/` for
the script → condition mapping, and [`input_prep/README.md`](input_prep/README.md)
for the input-generation flow). The only thing deliberately excluded is
**AF3's `run_alphafold.py`** — DeepMind's own restricted-license source — see
[Setup §3](#3-alphafold3-source-weights-databases-container) for how to
obtain it and everything else AF3 needs.

The computed metrics, confidence/timing extraction, and docking-angle
analysis in `results/` and `analysis/` cover all models and conditions
regardless of which cluster generated the underlying predictions.

## Citation

If you use this code, please also cite the datasets/tools it builds on:

- Lu, J., Zhu, X., Hu, X., Zhang, C. & Feng, F. Benchmarking TCR–pMHC
  structure prediction: a unified evaluation and CDR3-based functional
  insights. *Briefings in Bioinformatics* 27, bbag289 (2026).
- Pierce lab `tcr_docking_angle` — https://github.com/piercelab/tcr_docking_angle
- AlphaFold3, Protenix (v1/v2), IntelliFold-2 — see the report's reference list.

## License

The code in this repository (excluding vendored/patched upstream files, which
retain their original licenses) is released under the MIT License — see
[`LICENSE`](LICENSE).
