# Task 5 Report: Bankroll Strategies and Risk Metrics

## Delivered

- Added `roulette_lab.bankroll` with immutable `BankrollConfig`,
  `BankrollSimulation`, `RiskSummary`, `StrategyKind`, seeded
  `simulate_bankroll`, and `summarize_bankroll`.
- Added flat, Martingale, reverse Martingale, full/half/quarter Kelly sizing.
  `StrategyKind.KELLY` is the public alias for full Kelly. Kelly is documented
  as conditional log-growth optimisation, not guaranteed profit.
- Enforced finite non-boolean inputs, positive bankroll/stake/chip values,
  valid thresholds, feasible chip/table combinations, mandatory Kelly
  probabilities in `[0, 1]`, explicit RNGs, and simulation-only positive
  custom odds.
- Paths include initial capital in column zero. Frozen paths carry their exact
  prior balance forward. Stakes are capped by bankroll and table limit, then
  deterministically rounded down to the nearest whole chip.
- Implemented Standard, La Partage, and a true per-path En Prison state: zero
  reserves the full stake, repeated zero keeps it imprisoned, a later covered
  pocket returns it, and the settling spin cannot also start a new wager.
- Added terminal-risk and running-peak maximum-drawdown summaries, public
  exports, and 34 focused Task 5 tests including an analytical one-spin mean
  checked against a fixed-seed simulation within five Monte Carlo standard
  errors.

## TDD Evidence

1. Created `tests/test_bankroll.py` before `roulette_lab.bankroll` existed.
2. Ran `.venv/bin/python -m pytest tests/test_bankroll.py -x -vv`; collection
   failed as intended with `ModuleNotFoundError: roulette_lab.bankroll`.
3. Added the implementation and observed the first Kelly test fail against an
   incomplete payout handoff, then passed after supplying the selected odds.
4. Added a package-export test; it failed on the missing `BankrollConfig`
   import from `roulette_lab` and passed after exporting the Task 5 API.
5. During the En Prison state review, strengthened the deferred-settlement
   test. It failed with impossible `80` and `110` balances, proving that a
   prison settlement was followed by a second wager on the same outcome. The
   fix retains a per-spin `was_imprisoned` mask; the regression now passes.

## Verification

- `.venv/bin/python -m pytest tests/test_bankroll.py -v`: 34 passed.
- `.venv/bin/python -m pytest -q`: 162 passed.
- `.venv/bin/python -m compileall -q src tests scripts`: passed.
- `.venv/bin/python -m pip check`: `No broken requirements found.`
- Fallback Git `diff --check`: passed with no whitespace errors.

## Fix Round 1

- En Prison now preserves the actual imprisoned stake through repeated zeroes.
  A covered settlement advances progression as a win and a non-zero settlement
  advances it as a loss: Martingale resets/doubles respectively, while reverse
  Martingale doubles/resets respectively. Kelly re-enters on the next eligible
  spin using current liquid cash.
- `BankrollSimulation` now records immutable `equity_paths` and horizon
  `unresolved_stakes` alongside the backward-compatible liquid-cash `paths`.
  An active En Prison stake is marked as liquid cash plus
  `stake * p_win / (p_win + p_nonzero_loss)`; all other equity equals cash.
  Risk summaries now use that equity for terminal wealth, loss, ruin, and
  running-peak drawdown, so a recoverable stake is not automatically ruin.
- Added value-safe NumPy equality for simulation results, including explicit
  `NotImplemented` handling for other types.
- Kelly configurations may carry a base stake above the table limit because
  Kelly computes its own bankroll-based request; fixed and progression
  strategies still reject that infeasible configuration.
- Added deterministic controlled-wheel tests for zero-to-win/loss progression,
  repeated zeroes, liquid-cash Kelly re-entry, horizon equity/unresolved stake,
  equity-based risk, equality, new immutable arrays, and Kelly/table caps.

## Fix Round 1 Verification

- `.venv/bin/python -m pytest tests/test_bankroll.py -v`: 41 passed.
- `.venv/bin/python -m pytest -q`: 169 passed.
- `.venv/bin/python -m compileall -q src tests scripts`: passed.
- `.venv/bin/python -m pip check`: `No broken requirements found.`
