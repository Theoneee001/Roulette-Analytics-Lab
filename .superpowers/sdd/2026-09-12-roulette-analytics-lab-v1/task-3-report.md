# Task 3 Report: Global Fairness and Selection-Aware Bias Tests

## Scope Delivered

- Added `roulette_lab.statistics` with global Pearson chi-square fairness
  analysis, a multinomial Monte Carlo global p-value, and a selection-aware
  max-count test.
- Added immutable, tuple-backed `FairnessResult`, `MaxCountResult`, and
  `PosteriorEstimate` dataclasses so seeded result objects compare safely and
  reproducibly.
- Added symmetric-Dirichlet posterior means and marginal Beta credible
  intervals, plus deterministic disjoint estimation/validation history splits.
- Exported the Task 3 public API from `roulette_lab` without changing prior
  wheel or bet interfaces.

## Statistical and Validation Details

- All count analyses reject non-one-dimensional, non-integer, negative,
  empty-total, and wheel-shape-mismatched count data where a wheel is supplied.
- The global null is uniform across the wheel's pockets. Its Monte Carlo test
  uses complete multinomial samples and the add-one p-value correction.
- Chi-square output includes expected counts, Pearson residuals, Cramer's V,
  and an explicit Monte Carlo warning whenever any expected count is below
  five.
- The max-count test reports the observed maximum, a naive binomial tail,
  Bonferroni reference, and a family-wise multinomial Monte Carlo p-value.
- The Dirichlet prior uses `prior_strength` as the shared concentration for
  each pocket. Each marginal interval is Beta(alpha_i, alpha_total - alpha_i).
- Simulation counts, RNG instances, prior strength, credible level, and split
  fraction are validated explicitly. All simulation APIs require an explicit
  `numpy.random.Generator`.

## TDD Evidence

1. Added `tests/test_statistics.py` before `roulette_lab.statistics` existed.
2. Ran `.venv/bin/python -m pytest tests/test_statistics.py -x -vv`; collection
   failed as intended with `ModuleNotFoundError: No module named
   'roulette_lab.statistics'`.
3. Implemented the narrow Task 3 production API and public exports.
4. Ran the focused suite after implementation; it passed with 33 tests.

## Verification

- `.venv/bin/python -m pytest tests/test_statistics.py -v`: **33 passed in
  0.84s**.
- `.venv/bin/python -m pytest -v`: **89 passed in 1.71s**.
- `.venv/bin/python -m compileall -q src tests`: **passed** (exit 0).
- `.venv/bin/python -m pip check`: **No broken requirements found**.
- Fallback Git `diff --check`: **passed** with no whitespace errors.
