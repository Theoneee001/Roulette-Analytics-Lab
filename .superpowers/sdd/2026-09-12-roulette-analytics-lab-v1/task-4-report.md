# Task 4 Report: Detection Power and Reproducible Spin Data

## Delivered

- Added immutable `SpinDataset` CSV input/output with exact required columns,
  path/bytes/file-object support, strict consecutive indices, missing-value
  rejection, and literal pocket-label validation.
- Added `wheel_with_single_pocket_probability`, seeded count simulation, and a
  vectorized global Pearson chi-square power estimator. Power results include
  the estimate, Monte Carlo standard error, sample and experiment counts,
  alpha, decision rule, and serialised starting generator state.
- Added the minimal `scripts/run_analysis.py` entry point and generated the
  tracked 1,000-row unbiased and biased European-wheel CSV examples. Seeds and
  schema are documented in `data/README.md`.
- Exported the Task 4 public interfaces from `roulette_lab`.

## TDD Evidence

- Initial red: `roulette_lab.io` was missing during test collection.
- Added strict CSV, rebiasing, seeded simulation, global-decision-rule,
  false-positive calibration, stronger-bias monotonicity, generator, and
  alternate-bit-generator metadata tests before their production changes.

## Verification

- `.venv/bin/python -m pytest tests/test_io_and_power.py -v`: 32 passed.
- `.venv/bin/python -m pytest -q`: 121 passed.
- `.venv/bin/python -m compileall -q src scripts`: passed.
- `.venv/bin/python -m pip check`: `No broken requirements found.`
- `.venv/bin/python scripts/run_analysis.py`: regenerated both tracked CSVs.

## Fix Round 1

- `wheel_with_single_pocket_probability` now accepts finite endpoint values
  `0` and `1`, preserves the existing impossible-base-wheel guard, preserves
  immutable output probabilities, and produces exact unit probability mass.
- `estimate_detection_power` now rejects any experiment whose null expected
  count is below five, including the exact fair-European 184/185-spin boundary.
- `SpinDataset` now requires canonical wheel labels for its declared kind while
  retaining support for arbitrary valid probability snapshots. CSV reads now
  reject direct contradictory `WheelSpec` inputs through this invariant.
- Added endpoint, asymptotic-boundary, canonical-label, contradictory-wheel,
  and valid-biased-snapshot regression coverage.

## Fix Round 1 Verification

- `.venv/bin/python -m pytest tests/test_io_and_power.py -v`: 39 passed.
- `.venv/bin/python -m pytest -q`: 128 passed.
- `.venv/bin/python -m compileall -q src scripts`: passed.
- `.venv/bin/python -m pip check`: `No broken requirements found.`
