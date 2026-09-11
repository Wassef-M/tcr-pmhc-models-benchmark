#!/bin/bash
#SBATCH --job-name=AF3_classI
#SBATCH --output=array_%A_%a.out
#SBATCH --error=array_%A_%a.err
#SBATCH --time=24:00:00
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=500G
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu_p
#SBATCH --qos=gpu_normal
#SBATCH --array=1-56

CONTAINER_IMAGE=/lustre/boost_ai/apps/alphafold3/alphafold3_28jan2025.sif
DB_DIR=/lustre/boost_ai/apps/alphafold3/db
MODEL_PARAMETERS_DIR=/lustre/boost_ai/apps/alphafold3/model_parm

INPUT_DIR=$(pwd)
JSON_LIST="$INPUT_DIR/classI_jsons_list.txt"
JSON=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$JSON_LIST")
JSON_BASENAME=$(basename "$JSON")

OUTPUT_DIR="$INPUT_DIR/results_$(basename "$JSON" .json)"
mkdir -p "$OUTPUT_DIR"

echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "JSON: $JSON"
echo "Output: $OUTPUT_DIR"

apptainer exec --nv \
    --env JAX_PLATFORMS=cuda \
    --env XLA_FLAGS=--xla_disable_hlo_passes=custom-kernel-fusion-rewriter \
    --bind $INPUT_DIR:/work \
    --bind $OUTPUT_DIR:/output \
    --bind $MODEL_PARAMETERS_DIR:/models \
    --bind $DB_DIR:/public_databases \
    $CONTAINER_IMAGE \
    python /work/run_alphafold.py \
    --json_path=/work/${JSON#"$INPUT_DIR"/} \
    --model_dir=/models \
    --db_dir=/public_databases \
    --output_dir=/output \
    --flash_attention_implementation=xla
