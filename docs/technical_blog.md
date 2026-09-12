# The Hottest Number Is Not Necessarily Hot

Roulette looks simple enough to fit in one line of probability: a European wheel has 37 possible pockets, so a straight bet wins with probability `1/37`. Yet that small model opens several questions that appear in real analytical work. How do rules determine expected value? When does an unusual count become evidence of bias? What happens when we search the data before choosing what to test? How should a decision model respond when its probability estimate is uncertain?

I rebuilt a university group project around those questions as a tested Python package and interactive dashboard. The purpose is not to beat roulette. The purpose is to make mathematical assumptions visible, then follow their consequences through inference, simulation, and product design.

## Start with the contract, not the streak

A standard straight bet pays 35 units of net profit after a win and loses one unit otherwise. On a fair European wheel,

```text
expected net return = (1/37) x 35 - (36/37) x 1 = -1/37.
```

That is about `-2.70%` per unit staked. On an American wheel, the extra `00` pocket changes the denominator to 38, so the edge becomes about `5.26%`. The advertised 35:1 payout has not changed, but the sample space has.

This produces negative drift. Individual paths can rise sharply, sometimes for a long time, but the average increment remains below zero under the fair-wheel model. A random walk plot makes the distinction tangible: short-run variation can hide the direction of the expectation without changing it.

European rules such as La Partage and En Prison modify even-money bets when zero appears. The package treats their state transitions exactly. Both reduce the implemented long-run edge on red, black, odd, even, high, or low bets to about `1.35%`. They reduce a disadvantage; they do not turn it into an advantage.

## A suspicious pocket

Consider a reproducible fair sample of 1,000 European spins. Pocket 32 appears 39 times, more than any other pocket. If I now test pocket 32 with a binomial tail calculation, I obtain a naive p-value near `0.0164`. Read without context, that sounds like evidence against fairness.

The context changes the test. Pocket 32 was not written into a protocol before the experiment. It was chosen because it had the largest count among 37 candidates. Even fair data will usually have a winner. Testing that winner with a one-pocket null distribution ignores the search that produced it.

This is post-selection bias. The same pattern appears in feature screening, anomaly detection, subgroup analysis, and investment backtests. Search many possibilities, report only the best one, and an ordinary p-value no longer describes the full procedure.

I kept the naive value in the dashboard because it is a useful warning, then added two appropriate comparisons. A global chi-squared test asks whether the whole 37-category count vector differs from uniformity. A maximum-count Monte Carlo test repeatedly simulates fair 1,000-spin datasets and asks how often their hottest pocket is at least as hot as the observed one. For this fair sample, the global asymptotic p-value is about `0.3978` and the family-wise maximum-count value is about `0.4837`. The apparent discovery disappears.

## Detecting a known synthetic bias

The second sample is deliberately synthetic. Pocket 17 is assigned probability `0.060`; the remaining probability mass is shared by the other 36 pockets. In 1,000 generated spins, pocket 17 appears 61 times. The global chi-squared asymptotic p-value is about `0.0029`, the Monte Carlo global value is about `0.0044`, and the family-wise maximum-count value is about `0.0001`.

That result checks whether the methods can distinguish an intentionally strong departure from a fair sample. It does not establish that a casino wheel has such a bias. Labels matter here. Without the word "synthetic," a technically correct simulation can easily become a misleading real-world claim.

Detection also depends on effect size and sample size. A power experiment holds 1,000 spins fixed and gradually raises the probability of pocket 17. Near the fair value, rejection occurs at roughly the nominal 5% rate. At probability `0.050`, estimated power is about `0.590`; at `0.065`, it is about `0.975`. This curve answers a practical question that one p-value cannot: what departures is the experiment capable of finding?

## Probability uncertainty changes the decision

Suppose an analyst accepts `p = 0.060` for pocket 17 and considers standard 35:1 odds. The break-even probability is `1/36`, about `0.02778`, and the full Kelly fraction is positive. Kelly's formula maximises expected logarithmic growth when its inputs are correct and repeated opportunities follow the model.

The phrase "when its inputs are correct" does most of the work. A frequent pocket in a short training sample may regress towards the mean. A wheel may be repaired. Spins may not share one stationary probability. Estimation error can turn a positive Kelly fraction into aggressive overbetting.

The project therefore reports full, half, and quarter Kelly, adds a Dirichlet posterior view, and provides a train/validation split. Fractional Kelly is not magic. It is a sensitivity control that reduces exposure to probability uncertainty. Holdout data asks whether a pattern survives contact with observations that did not select it.

## Why Martingale is not an optimal solution

Martingale doubles the next stake after a loss, subject to available cash and the table limit. It can produce many small recoveries, which makes it psychologically persuasive. But it does not alter the expected return of the underlying bet. It concentrates losses into paths that encounter a long run of failures or a binding constraint.

In the repository's synthetic favourable scenario, 3,000 paths each start at 1,000 and run for up to 300 spins with a stop-loss at 500, take-profit at 2,000, and table limit of 100. Martingale's median terminal bankroll is 450 and its probability of ending below the start is about `65.57%`. Quarter Kelly's median is 2,198 and its loss probability is about `1.67%` under the same assumed pocket probability.

That comparison is conditional, not a universal ranking. It shows how position sizing and constraints reshape a distribution when an advantage has been supplied to the model. It does not prove that the advantage exists. The dashboard separates standard casino odds from hypothetical custom odds for the same reason.

## Building the analytical product

The implementation uses immutable wheel specifications and explicit winning-pocket sets for each bet. Tests check that European and American probability vectors sum to one, all legal geometries resolve correctly, zero and `00` are handled by the right wheel, and special rules return exact expectations.

The statistical layer returns structured results instead of formatted strings. This allows the notebook, report, and Streamlit app to share one source of calculation. Fixed random seeds make examples reproducible. CSV tables form the contract between analysis and publication, so headline values in the PDF can be regenerated rather than copied manually.

The interface follows the analytical sequence. First choose the wheel and bet. Then inspect data and fairness evidence. Finally explore bankroll paths and methods. Controls expose starting capital, stake, odds, stop-loss, take-profit, table limit, and strategy. The visual design stays quiet because the job is comparison, not casino atmosphere.

## What the project demonstrates

The central lesson is not that roulette is complicated. It is that a complete analysis must connect the question, data-generating process, test, decision rule, and communication.

Expectation answers what the contract implies. A chi-squared test asks whether a categorical distribution is compatible with fairness. Monte Carlo calibration follows the actual selection procedure. Power measures what the experiment could detect. Bayesian updating displays probability uncertainty. Random walk simulation shows the range and path dependence that an average hides. Product controls let a reader challenge assumptions instead of accepting a single screenshot.

The hottest number looked significant only when the search step was omitted. Once the full procedure was modelled, the conclusion changed. That correction is the most useful output of the project because it travels far beyond roulette.

## Responsible interpretation

No staking system removes the house edge from a fair wheel. Stop-loss and take-profit settings bound exposure or change the timing of exits, but they do not create positive expectation. The synthetic biased wheel is a teaching instrument, and custom odds are scenario inputs. Probability estimates from finite samples remain uncertain.

The code can help a student understand statistical inference and risk. It should not be read as profit advice or as encouragement to gamble. A good analytical product does more than calculate quickly; it also makes misuse harder.

