#!/usr/bin/env bash
set -uo pipefail
IFS=$'\t' read -r pdb model cls cond rank mtype <<< "$1"
res=$(python "$REPO/angle_one.py" -i "$pdb" --repo "$REPO" --mhc_type "$mtype" 2>/dev/null | grep -m1 '^RESULT' || true)
IFS=$'\t' read -r _ pid mhcc pepc ac bc dock inc dist warn status <<< "${res:-}"
[ -z "${pid:-}" ] && { pid=$(basename "$pdb" | cut -d_ -f1); status="FAIL:no_result"; }
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  "$pid" "$model" "$cls" "$cond" "$rank" "${dock:--}" "${inc:--}" "${dist:--}" "${warn:--}" "${status:-FAIL}"
