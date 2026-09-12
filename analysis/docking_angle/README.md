# Docking-angle analysis

Measures how well each predicted structure reproduces the native TCR–pMHC
docking geometry (docking angle, incident angle, TCR–pMHC center distance),
using the Pierce lab's `tcr_docking_angle` tool. This directory holds the
wrapper written for this study; the tool itself is *not* included here - see
[Running it](#running-it) below for the full build recipe.

## What each file does

| File | Role |
|---|---|
| `angle_one.py` | Processes **one** PDB structure: runs ANARCI on every chain to identify the TCR α/β chains (by AHo numbering scheme), assigns the two remaining chains as MHC (longer) / peptide (shorter), relabels chains to the tool's required convention (A=MHC, C=peptide, D=TCRα, E=TCRβ), renumbers the TCR chains via the upstream `scripts/renumber_tcr.py`, and runs the compiled `tcr_docking_angle` binary. Prints one `RESULT\t...` line with the parsed angles, or a `FAIL:<reason>` line if any step raises. |
| `angle_worker.sh` | Processes **one job**: takes a tab-separated job description (`pdb\tmodel\tmhc_class\tcondition\trank\tmhc_type`), calls `angle_one.py` on it, and emits one formatted TSV row (falls back to a `FAIL:no_result` row if `angle_one.py` produced nothing usable). |
| `batch_angles.sh` | Drives the **whole batch**: finds every `ranked_*` predicted PDB under a `pred_pdb/` tree plus every native reference structure, builds the job list, and fans it out to `angle_worker.sh` in parallel via `xargs -P`. Writes the combined TSV. |
| `analyze_angles.py` | Aggregates the batch TSV against the native angles: computes per-target docking-/incident-angle error, then prints summary tables (mean/median/% within threshold) for rank-0 and for best-of-5, split by model and condition. |
| `inspect_chains.py` | Standalone debug helper - prints chain IDs, residue counts, and the first ~65 residues of each chain's sequence for one or more PDB files. Useful for sanity-checking a structure before/after running the pipeline above; not part of the batch itself. |
| `tcr_complex.cc.patch` | One-line fix to the upstream tool's `tcr_complex.cc` (initializes `IsClassII` in the constructor) - applied during the build below. |

## Running it

### 1. Environment and build

This is the recipe actually used to get the tool building and running on a
plain Linux box with no sudo and no pre-existing conda or module system -
one isolated conda env with everything needed (compiler, GSL, ANARCI, HMMER,
Biopython):

```bash
# Userspace conda (skip if you already have conda/mamba):
cd ~
wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
bash Miniforge3-Linux-x86_64.sh -b -p $HOME/miniforge3
source $HOME/miniforge3/bin/activate
conda init bash        # then reopen your shell, or `source ~/.bashrc`

# One env with build tools + runtime deps:
conda create -n tcrangle -c conda-forge -c bioconda \
    python=3.11 anarci hmmer biopython=1.85 \
    gsl gxx_linux-64 make -y
conda activate tcrangle

# Sanity check before building:
ANARCI --help 2>/dev/null | head -3 || echo "ANARCI MISSING"
python -c "import Bio; print('biopython', Bio.__version__)"
ls $CONDA_PREFIX/include/gsl/gsl_version.h && echo "GSL headers OK"
```

Clone and patch the upstream tool, then build against conda's GSL:

```bash
git clone https://github.com/piercelab/tcr_docking_angle.git
cd tcr_docking_angle
git apply /path/to/this/repo/analysis/docking_angle/tcr_complex.cc.patch
export REPO=$(pwd)

# 1) Build the FAST library. Its Makefile is macOS-named (produces a
#    .dylib) - rename it so the main build's -lfast can find it on Linux:
cd "$REPO/fast"
make clean
make libs CC="$CC -O3 -w -I."
cp libfast.dylib libfast.a

# 2) Build the main tool, pointing it at conda's GSL:
cd "$REPO"
rm -f tcr_docking_angle
make CXX="$CXX" \
     INCLUDES="-I$CONDA_PREFIX/include" \
     GSL_LIBS="-L$CONDA_PREFIX/lib -Wl,-rpath,$CONDA_PREFIX/lib -lgsl -lgslcblas"
```

Verify:

```bash
ls -l tcr_docking_angle               # binary should exist
ldd ./tcr_docking_angle | grep -i gsl # should resolve to your conda env's libgsl/libgslcblas
./tcr_docking_angle                   # no args -> prints usage/MHC-type help text
```

(If you have GSL installed system-wide instead - e.g. via `apt`, with sudo -
a plain `make` without the `INCLUDES`/`GSL_LIBS` overrides should also work;
the conda-based recipe above is for environments without root access.)

Finally, place this directory's `angle_one.py`, `angle_worker.sh`,
`batch_angles.sh`, and `analyze_angles.py` inside `$REPO` (alongside the
binary you just built).

### 2. Configure paths

Edit the paths hardcoded near the top of `batch_angles.sh`:
- `REPO` - your `$REPO` from above.
- `BENCH` / `PRED` / `TRUE_I` - your Lu et al. checkout, its
  `benchmark/pred_pdb/` tree (from [stage 3](../../README.md#pipeline) of
  this repo's pipeline), and its native Class I reference PDBs
  (`benchmark_data/class-i/pdb/`).
- `INCLUDE` - which model names under `pred_pdb/` to process (defaults to
  `af3 protenix_v1 protenix_v2 intellifold2`).

### 3. Run the batch

```bash
./batch_angles.sh              # optional args: [model_filter] [nproc]
```

Writes `$REPO/results/docking_angles_classI.tsv` and prints a job count +
pass/fail summary. The no-MSA condition is skipped by design (docking
geometry wasn't evaluated for it in the report).

### 4. Aggregate the errors

```bash
python analyze_angles.py $REPO/results/docking_angles_classI.tsv
```

Writes `results/angle_errors_classI.tsv` (per-target docking-/incident-angle
error against the native structure) and prints two summary tables to
stdout: rank-0 vs. native, and best-of-5 vs. native.

## Limitation: Class I only

As written, this batch pipeline only handles Class I complexes:
`angle_one.py`'s chain-role classifier (`classify_classI`) explicitly raises
if it finds more than the 4 expected chains (it would need Class-II-specific
handling - a second MHC chain - to go further), and `batch_angles.sh` only
looks under `.../classI/...` paths. There is no Class II equivalent in this
repository.
