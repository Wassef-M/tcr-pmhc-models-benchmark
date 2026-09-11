#!/bin/bash
#SBATCH --job-name=intellifold_array
#SBATCH --output=array_%A_%a.out
#SBATCH --error=array_%A_%a.err
#SBATCH --time=24:00:00
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu_p
#SBATCH --qos=gpu_normal
#SBATCH --array=1-56

set -euo pipefail

PROJECT_DIR=/ictstr01/groups/imm01/workspace/mustafa.wassef/projects/intellifold2
INPUT_LIST="$PROJECT_DIR/yaml_list.txt"
CACHE_DIR="$PROJECT_DIR/cache_data"
TOOLS_BIN="$HOME/miniconda3/envs/bio-tools/bin"

cd "$PROJECT_DIR"

# Activate IntelliFold Python environment
source .venv/bin/activate

# Add HMMER and other bio-tools binaries from conda env to PATH
export PATH="$TOOLS_BIN:$PATH"

mkdir -p "$CACHE_DIR"

YAML=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$INPUT_LIST")

if [ -z "$YAML" ]; then
    echo "No YAML found for task ${SLURM_ARRAY_TASK_ID}"
    exit 1
fi

if [ ! -f "$YAML" ]; then
    echo "YAML file does not exist: $YAML"
    exit 1
fi

YAML_BASENAME=$(basename "$YAML" .yaml)
OUTPUT_DIR="$PROJECT_DIR/results_with_template/$YAML_BASENAME"
mkdir -p "$OUTPUT_DIR"

echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "YAML: $YAML"
echo "Output: $OUTPUT_DIR"
echo "Cache: $CACHE_DIR"
echo "Tools bin: $TOOLS_BIN"
echo "Host: $(hostname)"
echo "Start time: $(date)"
echo "Python: $(which python)"
echo "intellifold: $(which intellifold)"
echo "hmmsearch: $(which hmmsearch)"
echo "hmmbuild: $(which hmmbuild)"
echo "GPU info:"
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader || true

intellifold predict "$YAML" \
    --out_dir "$OUTPUT_DIR" \
    --cache "$CACHE_DIR" \
    --model v2 \
    --seed 42 \
    --use_msa_server \
    --msa_pairing_strategy greedy \
    --use_template

echo "Finished at $(date)"