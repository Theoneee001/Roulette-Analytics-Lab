# Reproducible analysis summary

## Selection-aware bias evidence

The biased example's hottest pocket was `17`. Its naive p-value was 0.0000, while the selection-aware family-wise p-value was 0.0001. The latter is the relevant result after choosing the hottest pocket from the same sample.

## Detection power

At pocket probability 0.080, the global test's estimated power was 1.000 (Monte Carlo SE 0.000).

## Bankroll and Kelly interpretation

Kelly sizing is conditional on a correct probability and payout model. It is an expected log-growth rule, not guaranteed profit. Strategy tables report simulated terminal dispersion, loss risk, ruin risk, and maximum drawdown under a declared biased-wheel scenario.

## Sequential and posterior extensions

The changed-stream CUSUM showcase uses a true change at spin 500 with a Monte Carlo median detection delay of 153.0 spins. The biased teaching sample posterior mean is 0.0598; its lower-quantile Kelly value is labelled a heuristic rather than a betting recommendation.
