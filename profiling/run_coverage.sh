#!/usr/bin/env bash
set -euo pipefail

if ! command -v coverage >/dev/null 2>&1; then
  echo "coverage.py not found; install it with pip install coverage" >&2
  exit 1
fi

export PYTHONPATH="$(pwd)"

coverage run -m pytest
coverage report -m
