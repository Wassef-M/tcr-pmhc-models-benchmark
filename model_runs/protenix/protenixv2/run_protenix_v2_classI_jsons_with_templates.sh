#!/bin/bash

set -euo pipefail

PROJECT_DIR="/vol/benchmark_data/projects/protenixv1"
ENV_DIR="$PROJECT_DIR/env/protenix_env_py311"

INPUT_DIR="$PROJECT_DIR/inputs/classI_jsons_protenix_v2_with_templates"

RESULTS_DIR="$PROJECT_DIR/results/classI_protenix_v2_with_template"
LOG_DIR="$PROJECT_DIR/logs/classI_protenix_v2_with_template"

MODEL_NAME="protenix-v2"
SEED="42"

mkdir -p "$RESULTS_DIR"
mkdir -p "$LOG_DIR"

source "$ENV_DIR/bin/activate"

export CUDA_HOME=/usr/local/cuda-12.6
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}"

export MAX_JOBS=2
export TORCH_EXTENSIONS_DIR=/vol/benchmark_data/cache/torch_extensions

KALIGN_BIN=$(which kalign)
HMMSEARCH_BIN=$(which hmmsearch)
HMMBUILD_BIN=$(which hmmbuild)

echo "Kalign path: $KALIGN_BIN"
echo "hmmsearch path: $HMMSEARCH_BIN"
echo "hmmbuild path: $HMMBUILD_BIN"

for JSON in "$INPUT_DIR"/*.json; do

    BASENAME=$(basename "$JSON" .json)
    OUTPUT_DIR="$RESULTS_DIR/$BASENAME"

    OUT_LOG="$LOG_DIR/${BASENAME}.out"
    ERR_LOG="$LOG_DIR/${BASENAME}.err"

    mkdir -p "$OUTPUT_DIR"

    echo "========================================" | tee "$OUT_LOG"
    echo "Running Protenix WITH TEMPLATE for: $BASENAME" | tee -a "$OUT_LOG"
    echo "Input JSON: $JSON" | tee -a "$OUT_LOG"
    echo "Output Dir: $OUTPUT_DIR" | tee -a "$OUT_LOG"
    echo "Kalign path: $KALIGN_BIN" | tee -a "$OUT_LOG"
    echo "hmmsearch path: $HMMSEARCH_BIN" | tee -a "$OUT_LOG"
    echo "hmmbuild path: $HMMBUILD_BIN" | tee -a "$OUT_LOG"
    echo "Start Time: $(date)" | tee -a "$OUT_LOG"
    echo "========================================" | tee -a "$OUT_LOG"

    protenix pred \
        -i "$JSON" \
        -o "$OUTPUT_DIR" \
        -s "$SEED" \
        -n "$MODEL_NAME" \
        --use_msa true \
        --use_template true \
        > >(tee -a "$OUT_LOG") \
        2> >(tee "$ERR_LOG" >&2)

    echo "" | tee -a "$OUT_LOG"
    echo "Finished: $BASENAME" | tee -a "$OUT_LOG"
    echo "End Time: $(date)" | tee -a "$OUT_LOG"
    echo "" | tee -a "$OUT_LOG"

done

echo "All Protenix predictions with templates completed."