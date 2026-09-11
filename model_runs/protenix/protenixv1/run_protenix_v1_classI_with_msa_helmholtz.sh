#!/bin/bash
#SBATCH --job-name=protenix_array
#SBATCH --output=array_%A_%a.out
#SBATCH --error=array_%A_%a.err
#SBATCH --time=24:00:00
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu_p
#SBATCH --qos=gpu_normal
#SBATCH --array=1-56

set -euo pipefail

PROJECT_DIR=/ictstr01/groups/imm01/workspace/mustafa.wassef/projects/protenix_base_default_v1
INPUT_LIST="$PROJECT_DIR/json_list_re_run_with_msa.txt"

cd "$PROJECT_DIR"
source .protenix_env/bin/activate

JSON=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$INPUT_LIST")

if [ -z "$JSON" ]; then
    echo "No JSON found for task ${SLURM_ARRAY_TASK_ID}"
    exit 1
fi

if [ ! -f "$JSON" ]; then
    echo "JSON file does not exist: $JSON"
    exit 1
fi

JSON_BASENAME=$(basename "$JSON" .json)
OUTPUT_DIR="$PROJECT_DIR/results_protenixv1/$JSON_BASENAME"
mkdir -p "$OUTPUT_DIR"

echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "JSON: $JSON"
echo "Output: $OUTPUT_DIR"
echo "Host: $(hostname)"
echo "Start time: $(date)"
echo "GPU info:"
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader || true

protenix pred \
    -i "$JSON" \
    -o "$OUTPUT_DIR" \
    -s 42 \
    -n protenix_base_default_v1.0.0 \
    --use_msa true

echo "Finished at $(date)"