#!/usr/bin/env bash
set -euo pipefail

if ! command -v kernprof >/dev/null 2>&1; then
  echo "kernprof not found; install line-profiler first (pip install line-profiler)" >&2
  exit 1
fi

export PYTHONPATH="$(pwd)"

echo "Running line profiler for rooms listing and booking creation"
kernprof -l -v profiling/targets/line_profile_targets.py
