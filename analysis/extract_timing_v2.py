"""
Extract wall-clock runtime for each complex from model log files.

Models: af3, intellifold2, protenix_v1, protenix_v2
Output: analysis/timing_v2.csv

Timing sources per model:
  AF3        (.out): sum of per-chain pipeline times + featurising + inference
  Protenix   (.err): "Job completed in X.XXs"
  IntelliFold2 (.out): "Elapsed seconds: N" when present, else Finished - Start time

Fixed vs v1: strip_tz now preserves AM/PM when removing timezone codes,
  then collapses multiple spaces before parsing.
"""

import csv
import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT_DIR = BASE / "analysis"
OUT_CSV = OUT_DIR / "timing_v2.csv"

FIELDNAMES = [
    "model", "mhc_class", "condition", "target",
    "total_seconds", "total_minutes", "timing_source",
]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def read(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except FileNotFoundError:
        return ""


def strip_tz(s: str) -> str:
    """Remove timezone abbreviations (e.g. CEST, UTC) but keep AM / PM."""
    # Remove all-caps 2-5 letter words that are NOT AM or PM
    s = re.sub(r'\b(?!(?:AM|PM)\b)[A-Z]{2,5}\b', '', s)
    # Collapse runs of whitespace to a single space
    return re.sub(r'\s+', ' ', s).strip()


def parse_datetime(s: str) -> datetime | None:
    """Try common date formats; return None on failure."""
    s = strip_tz(s)
    fmts = [
        "%a %b %d %I:%M:%S %p %Y",   # Wed Apr 22 02:14:04 PM 2026  (12h)
        "%a %b  %d %I:%M:%S %p %Y",  # double-space day padding
        "%a %b %d %H:%M:%S %Y",      # Wed Apr 22 14:14:04 2026     (24h)
        "%a %b  %d %H:%M:%S %Y",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# AF3
# ---------------------------------------------------------------------------

AF3_LOG_BASE = BASE / "af3" / "logs"

AF3_LOG_DIRS = [
    ("classI",  "with_msa_with_template",  AF3_LOG_BASE / "out_err_with_msa_with_template_classI"),
    ("classI",  "with_msa_no_template",    AF3_LOG_BASE / "out_err_with_msa_no_template_classI"),
    ("classI",  "no_msa_no_template",      AF3_LOG_BASE / "out_err_no_msa_no_template_classI"),
    ("classII", "with_msa_with_template",  AF3_LOG_BASE / "out_err_with_msa_with_template_classII"),
    ("classII", "with_msa_no_template",    AF3_LOG_BASE / "out_err_with_msa_no_template_classII"),
    ("classII", "no_msa_no_template",      AF3_LOG_BASE / "out_err_no_msa_no_template_classII"),
]


def parse_af3_out(content: str):
    """Return (target, total_seconds) from an AF3 .out file, or (None, None)."""
    m = re.search(r'JSON:\s+\S*/([^/\s]+)\.json', content)
    if not m:
        return None, None
    target = m.group(1)

    # Per-chain pipeline times (chains run sequentially, so sum them)
    chain_times = [float(x) for x in re.findall(
        r'Processing chain \w+ took ([\d.]+) seconds', content)]
    pipeline_s = sum(chain_times)

    fm = re.search(r'Featurising data with \d+ seed\(s\) took ([\d.]+) seconds', content)
    featurise_s = float(fm.group(1)) if fm else 0.0

    im = re.search(
        r'Running model inference and extracting output structures with \d+ seed\(s\) took ([\d.]+) seconds',
        content)
    inference_s = float(im.group(1)) if im else 0.0

    if featurise_s == 0.0 and inference_s == 0.0:
        return target, None   # incomplete log

    total = pipeline_s + featurise_s + inference_s
    return target, total


def iter_af3(rows):
    for mhc_class, condition, log_dir in AF3_LOG_DIRS:
        if not log_dir.exists():
            print(f"  MISSING {log_dir}")
            continue

        for out_path in sorted(log_dir.glob("*.out")):
            content = read(out_path)
            target, total_s = parse_af3_out(content)
            if target is None:
                print(f"  SKIP af3/{mhc_class}/{condition}/{out_path.name}: no JSON line")
                continue
            if total_s is None:
                print(f"  SKIP af3/{mhc_class}/{condition}/{target}: incomplete log")
                continue

            rows.append({
                "model": "af3",
                "mhc_class": mhc_class,
                "condition": condition,
                "target": target,
                "total_seconds": round(total_s, 2),
                "total_minutes": round(total_s / 60, 3),
                "timing_source": "sum_of_steps_from_out",
            })


# ---------------------------------------------------------------------------
# Protenix
# ---------------------------------------------------------------------------

PROTENIX_LOG_BASE = BASE / "protenix" / "logs"

PROTENIX_LOG_DIRS = [
    ("classI",  "v1", "with_msa_with_template",  PROTENIX_LOG_BASE / "classI_protenix_v1_with_msa_with_template"),
    ("classI",  "v1", "with_msa_no_template",    PROTENIX_LOG_BASE / "classI_protenix_v1_with_msa_no_template"),
    ("classI",  "v1", "no_msa_no_template",      PROTENIX_LOG_BASE / "classI_protenix_v1_no_msa_no_template"),
    ("classII", "v1", "with_msa_with_template",  PROTENIX_LOG_BASE / "classII_protenix_v1_with_msa_with_template"),
    ("classII", "v1", "with_msa_no_template",    PROTENIX_LOG_BASE / "classII_protenix_v1_with_msa_no_template"),
    ("classII", "v1", "no_msa_no_template",      PROTENIX_LOG_BASE / "classII_protenix_v1_no_msa_no_template"),
    ("classI",  "v2", "with_msa_with_template",  PROTENIX_LOG_BASE / "classI_protenix_v2_with_msa_with_template"),
    ("classI",  "v2", "with_msa_no_template",    PROTENIX_LOG_BASE / "classI_protenix_v2_with_msa_no_template"),
    ("classI",  "v2", "no_msa_no_template",      PROTENIX_LOG_BASE / "classI_protenix_v2_no_msa_no_template"),
    ("classII", "v2", "with_msa_with_template",  PROTENIX_LOG_BASE / "classII_protenix_v2_with_msa_with_template"),
    ("classII", "v2", "with_msa_no_template",    PROTENIX_LOG_BASE / "classII_protenix_v2_with_msa_no_template"),
    ("classII", "v2", "no_msa_no_template",      PROTENIX_LOG_BASE / "classII_protenix_v2_no_msa_no_template"),
]


def parse_protenix_target(out_content: str, stem: str) -> str:
    m = re.search(r'JSON:\s+\S*/([^/\s]+)\.json', out_content)
    if m:
        return m.group(1)
    return re.sub(r'(-update-msa)+$', '', stem)


def iter_protenix(rows):
    for mhc_class, version, condition, log_dir in PROTENIX_LOG_DIRS:
        if not log_dir.exists():
            print(f"  MISSING {log_dir}")
            continue

        for out_path in sorted(log_dir.glob("*.out")):
            err_path = out_path.with_suffix(".err")
            out_content = read(out_path)
            err_content = read(err_path)

            target = parse_protenix_target(out_content, out_path.stem)

            m = re.search(r'Job completed in ([\d.]+)s', err_content)
            if not m:
                print(f"  SKIP protenix_{version}/{mhc_class}/{condition}/{out_path.stem}: "
                      f"no 'Job completed' in .err")
                continue

            total_s = float(m.group(1))
            rows.append({
                "model": f"protenix_{version}",
                "mhc_class": mhc_class,
                "condition": condition,
                "target": target,
                "total_seconds": round(total_s, 2),
                "total_minutes": round(total_s / 60, 3),
                "timing_source": "job_completed_from_err",
            })


# ---------------------------------------------------------------------------
# IntelliFold2
# ---------------------------------------------------------------------------

IF2_LOG_BASE = BASE / "intellifold2" / "logs"

IF2_LOG_DIRS = [
    ("classI",  "with_msa_with_template",  IF2_LOG_BASE / "classI_v2_with_msa_with_template"),
    ("classI",  "with_msa_no_template",    IF2_LOG_BASE / "classI_v2_with_msa_no_template"),
    ("classI",  "no_msa_no_template",      IF2_LOG_BASE / "classI_v2_no_msa_no_template"),
    ("classII", "with_msa_with_template",  IF2_LOG_BASE / "classII_v2_with_msa_with_template"),
    ("classII", "with_msa_no_template",    IF2_LOG_BASE / "classII_v2_with_msa_no_template"),
    ("classII", "no_msa_no_template",      IF2_LOG_BASE / "classII_v2_no_msa_no_template"),
]


def parse_if2_out(content: str):
    """Return (target, total_seconds, source) from an IntelliFold2 .out file."""
    m = re.search(r'YAML:\s+\S*/([^/\s]+)\.yaml', content)
    if not m:
        return None, None, None
    target = m.group(1)

    # Best: explicit elapsed seconds
    em = re.search(r'Elapsed seconds:\s*([\d.]+)', content)
    if em:
        return target, float(em.group(1)), "elapsed_seconds_from_out"

    # Fallback: parse Start time / Finished at
    sm = re.search(r'Start time:\s*(.+)', content)
    fm = re.search(r'Finished at:?\s*(.+)', content)
    if sm and fm:
        t_start = parse_datetime(sm.group(1).strip())
        t_end   = parse_datetime(fm.group(1).strip())
        if t_start and t_end:
            delta = (t_end - t_start).total_seconds()
            if delta > 0:
                return target, delta, "start_finish_diff_from_out"

    return target, None, None


def iter_intellifold2(rows):
    for mhc_class, condition, log_dir in IF2_LOG_DIRS:
        if not log_dir.exists():
            print(f"  MISSING {log_dir}")
            continue

        for out_path in sorted(log_dir.glob("*.out")):
            content = read(out_path)
            target, total_s, source = parse_if2_out(content)

            if target is None:
                print(f"  SKIP intellifold2/{mhc_class}/{condition}/{out_path.name}: no YAML line")
                continue
            if total_s is None:
                print(f"  SKIP intellifold2/{mhc_class}/{condition}/{target}: could not parse time")
                continue

            rows.append({
                "model": "intellifold2",
                "mhc_class": mhc_class,
                "condition": condition,
                "target": target,
                "total_seconds": round(total_s, 2),
                "total_minutes": round(total_s / 60, 3),
                "timing_source": source,
            })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUT_DIR.mkdir(exist_ok=True)
    rows = []

    print("=== AF3 ===")
    iter_af3(rows)
    print(f"  -> {sum(1 for r in rows if r['model'] == 'af3')} rows")

    print("=== Protenix ===")
    iter_protenix(rows)
    print(f"  -> {sum(1 for r in rows if r['model'].startswith('protenix'))} rows")

    print("=== IntelliFold2 ===")
    iter_intellifold2(rows)
    print(f"  -> {sum(1 for r in rows if r['model'] == 'intellifold2')} rows")

    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nTotal rows : {len(rows)}")
    print(f"Written to : {OUT_CSV}")

    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["mhc_class"], r["condition"])].append(r["total_seconds"])

    print("\nMean time (seconds) per (model, mhc_class, condition):")
    for key in sorted(groups):
        vals = groups[key]
        print(f"  {key[0]:20s}  {key[1]:8s}  {key[2]:25s}  "
              f"n={len(vals):3d}  mean={sum(vals)/len(vals):8.1f}s  "
              f"min={min(vals):7.1f}s  max={max(vals):7.1f}s")

    sources = defaultdict(int)
    for r in rows:
        sources[(r["model"], r["timing_source"])] += 1
    print("\nTiming sources:")
    for k, n in sorted(sources.items()):
        print(f"  {k[0]:20s}  {k[1]:35s}  {n} rows")


if __name__ == "__main__":
    main()
