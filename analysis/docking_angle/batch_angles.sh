#!/usr/bin/env bash
set -uo pipefail
export REPO=/vol/benchmark_data/projects/tcr_docking_angle
BENCH=/vol/benchmark_data/projects/TCR-pMHC-folding-benchmark-main
export PRED=$BENCH/benchmark/pred_pdb
TRUE_I=$BENCH/benchmark_data/class-i/pdb

INCLUDE="af3 protenix_v1 protenix_v2 intellifold2"   # boltz2 excluded
MODEL_FILTER="${1:-}"            # optional single model; empty = all in INCLUDE
NPROC="${2:-$(nproc)}"
OUT=$REPO/results/docking_angles_classI.tsv
mkdir -p "$REPO/results"

JOBS=$(mktemp)
find "$PRED" -path '*/classI/*/ranked_*/*_pmhc_tcr.pdb' | while read -r f; do
  rel=${f#$PRED/}; IFS=/ read -r model _ cls cond rank fname <<< "$rel"
  [[ " $INCLUDE " == *" $model "* ]] || continue
  [[ "$cond" == *no_msa* ]] && continue            # <-- skip no-MSA conditions
  [ -n "$MODEL_FILTER" ] && [ "$model" != "$MODEL_FILTER" ] && continue
  printf '%s\t%s\tclassI\t%s\t%s\t0\n' "$f" "$model" "$cond" "$rank"
done > "$JOBS"
if [ -z "$MODEL_FILTER" ] || [ "$MODEL_FILTER" = "true" ]; then
  for f in "$TRUE_I"/*_pmhc_tcr.pdb; do
    printf '%s\ttrue\tclassI\tnative\t-\t0\n' "$f"
  done >> "$JOBS"
fi

n=$(wc -l < "$JOBS"); echo "Jobs: $n   Parallelism: $NPROC"
TMP=$(mktemp)
sort -u "$JOBS" | xargs -P "$NPROC" -I LINE bash "$REPO/angle_worker.sh" "LINE" > "$TMP"
{ printf 'pdb\tmodel\tmhc_class\tcondition\trank\tdocking_angle\tincident_angle\tdistance\twarn\tstatus\n'
  sort -t$'\t' -k2,2 -k4,4 -k5,5 -k1,1 "$TMP"; } > "$OUT"
rm -f "$JOBS" "$TMP"
echo "Wrote $OUT"; echo "Status summary:"
awk -F'\t' 'NR>1{c[$10 ~ /^FAIL/ ? "FAIL" : $10]++} END{for(s in c) printf "  %-6s %d\n", s, c[s]}' "$OUT"
