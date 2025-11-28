# Profiling Toolkit

This directory centralizes lightweight performance tooling:

- `run_line_profile.sh` uses `kernprof`/`line_profiler` to measure execution time within `list_rooms` and `create_booking`. It spins up an in-memory SQLite DB and reuses the existing service-layer functions so results mirror production logic.
- `run_memory_profile.py` applies `memory_profiler` to the same code paths, highlighting allocations while listing rooms or creating bookings.
- `run_coverage.sh` runs the full pytest suite under `coverage.py` and prints a summary, making it easy to track test completeness.

## Usage

From the project root:

```bash
pip install line-profiler memory-profiler coverage
chmod +x profiling/run_line_profile.sh profiling/run_coverage.sh

# Line profiling
profiling/run_line_profile.sh

# Memory profiling
python profiling/run_memory_profile.py

# Coverage
profiling/run_coverage.sh
```

Each script assumes you have a virtualenv with the project dependencies installed and that you run it from the repo root so relative imports resolve correctly.
