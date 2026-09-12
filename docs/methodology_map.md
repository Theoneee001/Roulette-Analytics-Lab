# Formula-to-code methodology map

This map connects the mathematics to executable code, tests, tracked evidence and interpretation. It also records two corrections made while extending the source report.

| Concept | Equation | Python interface | Test | Figure | Interpretation |
|---|---|---|---|---|---|
| Fair wheel | $P(X=i)=1/m$ | `make_fair_wheel` | `test_wheels.py` | `01_wheel_layout.png` | European and American wheels have 37 and 38 mutually exclusive pockets. |
| Exact net return | $E[X]=pb-(1-p)$ | `expected_net_return`, `house_edge` | `test_bets.py::test_straight_up_house_edge` | `02_house_edge_comparison.png` | A fair European straight-up stake $w$ has expected net return $-w/37$, not zero. |
| La Partage | $E[X]=p_w-p_l-z/2$ | `expected_net_return` | `test_bets.py::test_european_la_partage_halves_even_money_edge` | `02_house_edge_comparison.png` | Returning half the stake on zero halves the standard European even-money edge. |
| En Prison | $V_I=-p_l/(p_w+p_l)$ | `expected_net_return`, `simulate_bankroll` | `test_bets.py`, `test_bankroll.py` | `02_house_edge_comparison.png` | An explicit deferred state handles repeated zero and eventual settlement. |
| Law of large numbers | $\hat p_n=N_i(n)/n\to p_i$ | `run_full_analysis` | `test_analysis.py` | `03_lln_convergence.png` | Cumulative frequency stabilises with sample size but does not remove house edge. |
| Pearson goodness of fit | $X^2=\sum_i(O_i-E_i)^2/E_i$ | `chi_square_fairness` | `test_statistics.py::test_chi_square_matches_scipy` | `04_bias_residuals.png` | The global test asks whether the complete count vector fits a fair wheel. |
| Pearson residual | $r_i=(O_i-E_i)/\sqrt{E_i}$ | `chi_square_fairness` | `test_statistics.py` | `04_bias_residuals.png` | Signed residuals locate pockets contributing to the global discrepancy. |
| Cramer's V | $V=\sqrt{X^2/[n(m-1)]}$ | `chi_square_fairness` | `test_statistics.py` | `04_bias_residuals.png` | Effect size supplements the sample-size-sensitive p-value. |
| Monte Carlo global test | $(1+\#\{T^*\ge T\})/(B+1)$ | `monte_carlo_global_pvalue` | `test_statistics.py` | `04_bias_residuals.png` | Full multinomial null samples provide a finite-simulation global reference. |
| Selected maximum | $M=\max_i O_i$ | `max_count_test` | `test_statistics.py::test_max_count_test_is_reproducible` | `04_bias_residuals.png` | The hottest pocket was selected after observing all pockets, so its naive binomial tail is not the final evidence. |
| Bonferroni reference | $p_B=\min(1,mp_{naive})$ | `max_count_test` | `test_statistics.py` | `04_bias_residuals.png` | The correction bounds family-wise error across pocket-level searches. |
| Dirichlet posterior | $p\mid O\sim Dirichlet(O_i+\alpha)$ | `dirichlet_posterior` | `test_statistics.py` | Published table | Posterior means and marginal Beta intervals regularise sparse pocket estimates. |
| Detection power | $P_{H_1}(X^2>c_\alpha)$ | `estimate_detection_power` | `test_io_and_power.py` | `05_detection_power.png` | Power links sample size and bias strength to the probability of detection. |
| Kelly fraction | $f^*=\max(0,[bp-(1-p)]/b)$ | `kelly_fraction` | `test_bets.py::test_kelly_requires_probability_above_break_even` | Kelly sensitivity table | Positive straight-up allocation requires $p>1/36$ at 35:1 net odds. |
| Bankroll recursion | $W_{t+1}=W_t+s_tR_{t+1}$ | `simulate_bankroll` | `test_bankroll.py` | `06_bankroll_risk.png` | Strategy rules change path risk, not the underlying casino payout. |
| Maximum drawdown | $\max_t(P_t-W_t)/P_t$ | `summarize_bankroll` | `test_bankroll.py` | `06_bankroll_risk.png` | Running-peak loss captures path pain hidden by terminal averages. |

## Source-report corrections

The source report supplied the mathematical and conceptual starting point. During the independent Python reimplementation, two statements were tightened:

1. The source report treated a fair European straight-up bet as break-even. With a 35:1 net payout and 37 pockets, the exact expected net return is $-w/37$. Unit tests compare this identity on both European and American wheels.
2. The source report used a binomial tail for the largest observed count. Because that pocket was selected after observing the sample, the portfolio reports the naive tail as a reference and uses a full multinomial maximum-count simulation for the selected claim.

