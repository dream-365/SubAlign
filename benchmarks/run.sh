#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: benchmarks/run.sh <video> <subtitle> [out.srt]" >&2
  exit 1
fi

VIDEO="$1"
SUBTITLE="$2"
OUT="${3:-benchmarks/out.${SUBTITLE##*.}}"
MODEL="${SUBALIGN_MODEL:-large-v3-turbo}"

mkdir -p benchmarks
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"

/usr/bin/time -l .venv/bin/python -m subalign align \
  --video "$VIDEO" --subtitle "$SUBTITLE" --out "$OUT" --force \
  --model "$MODEL" \
  2> benchmarks/time.txt

python3 - "$OUT" <<'PY'
import json, re, sys
from pathlib import Path

text = Path("benchmarks/time.txt").read_text()
real = re.search(r"([0-9.]+) real", text)
rss = re.search(r"(\d+)  maximum resident set size", text)
payload = {
    "output": sys.argv[1],
    "real_seconds": float(real.group(1)) if real else None,
    "max_rss_bytes": int(rss.group(1)) if rss else None,
}
Path("benchmarks/latest.json").write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps(payload, indent=2))
PY
