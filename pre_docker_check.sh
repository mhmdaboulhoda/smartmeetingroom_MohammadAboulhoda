#!/usr/bin/env bash
set -euo pipefail

if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

pytest -vv
coverage run -m pytest
coverage report -m

python profiling/demo_rooms_cache_timing.py || true
pytest tests/test_db_indexes.py || true
