# The Hottest Number Is Not Necessarily Hot

Roulette is a compact way to practise a habit that matters in larger analytical systems: ask what procedure produced a result before trusting the result itself. This project uses casino roulette, not because it offers a way around casino odds, but because the probability space and payout contract can be stated exactly. That makes it harder to hide a weak assumption behind a dramatic chart.

## Start with the casino contract

A fair European wheel gives every pocket the same chance. A fair wager is a different matter. A straight-up bet wins at standard net odds only when one named pocket occurs, and the payout does not compensate for the full set of possible pockets. `outputs/tables/house_edges.csv` contains the exact expected return and house edge for each implemented wheel and rule. The same table shows how La Partage and En Prison reduce the edge on qualifying even-money bets without reversing it.

That contract is the anchor for the rest of the lab. A bankroll path can jump upward. A run of outcomes can look persuasive. Neither changes negative drift under the fair-wheel model. The notebook pairs `lln_convergence.csv` with a random-walk explanation for this reason: the law of large numbers describes convergence in relative frequency under assumptions, not a promise that a finite sequence will behave politely.

## The search is part of the test

The first teaching dataset is fair by construction. One pocket still appears most often. A naive one-pocket tail probability looks at that pocket as though it had been written down before the data arrived. It was not. The analyst searched the wheel, found the most frequent label, then tested the winner.

That is post-selection bias. It appears in feature screening, anomaly detection, subgroup claims, and backtests as well as roulette. `bias_tests.csv` keeps the naive value on purpose, but puts it beside a global chi-square result and a maximum-count Monte Carlo result. The maximum-count simulation repeats the search inside each fair simulated dataset. Its family-wise result therefore answers the actual question: how surprising is the hottest observed pocket after looking across the whole wheel?

The synthetic biased dataset plays a different role. It gives one labelled pocket a documented elevated probability and checks whether the fixed-horizon procedure reacts. The resulting p-values and power curve are evidence about that generated experiment, not a claim about a real casino wheel. That label is doing serious work.

## Three questions, three tools

A fixed-horizon fairness test, a post-selection correction, and a sequential monitor are easy to confuse because all can produce a number that looks like evidence. They answer different questions.

The fixed-horizon global test asks whether the complete count vector at a planned endpoint is compatible with a fair wheel. The maximum-count correction asks whether a data-selected hottest pocket remains unusual after the selection search is included. The likelihood-ratio process in `sequential_evidence.csv` asks whether a pre-specified target has accumulated enough evidence against a pre-specified simple null while data are observed over time.

That last distinction matters. Repeatedly checking an ordinary fixed-horizon p-value and stopping when it becomes attractive changes its error rate. The sequential module instead records a likelihood ratio, a declared alternative, and a pre-specified threshold. It is not a general permission to search every pocket until something crosses. The target and alternative must be declared, or the multiplicity problem returns.

`change_point_results.csv` adds a Page-style CUSUM diagnostic. It asks whether a specific indicator has changed upward from one specified probability to another. It can report an alarm and, in a synthetic stream with a known inserted change, a detection delay. It cannot identify the mechanical cause of an alarm, certify the exact moment a real wheel changed, or replace a global fairness analysis. A diagnostic is more useful when its blind spots are written next to it.

## Kelly needs an edge, and an edge needs scrutiny

Kelly is often described too casually. In the usual model, it chooses the stake fraction that maximises expected logarithmic growth under an assumed win probability, net odds, repeated opportunities, and divisible capital. That is what optimal means here. It is a constrained mathematical objective, not a promise of the highest future bankroll.

Under standard fair European straight-up roulette, the assumed probability is below break-even. The correct Kelly fraction is therefore zero. `kelly_sensitivity.csv` makes this visible. Positive Kelly appears only after a favourable probability has been supplied to the model.

The synthetic posterior example in `posterior_edge.csv` goes further. It shows a posterior mean, credible interval, probability above break-even, plug-in Kelly, and lower-quantile Kelly. That probability uncertainty belongs in the decision, not in a footnote. The lower-quantile figure is explicitly a heuristic. It deliberately shrinks exposure by using a cautious probability input, but it is not a formal uncertainty-aware optimum and it cannot correct a target that was selected after inspecting the same sample.

## Risk belongs in the comparison

The risk frontier compares quarter, half, and full Kelly under one named synthetic scenario. Common random numbers give each fraction the same seeded simulated outcomes. `risk_frontier.csv` reports expected log growth alongside loss probability, expected drawdown, and terminal CVaR.

The CVaR sign convention is plain: terminal shortfall is `max(initial bankroll - terminal equity, 0)`, so larger values are worse. CVaR is the mean of the worst shortfalls at the stated tail probability. It is not an unstated return convention with a reversed sign. This matters when a chart is used to compare strategies, because otherwise a lower-tail metric can sound clearer than it is.

The lesson is not that one staking rule wins a contest. A full-Kelly choice can suit expected-log-growth assumptions while a lower fraction has a smaller finite-horizon drawdown or tail shortfall. A user with different constraints can make a different choice. On a fair casino contract, the edge disappears and so does the Kelly allocation.

## Why build a product around this?

The Streamlit dashboard turns assumptions into controls: wheel, rule, target, probability, bankroll, horizon, and stake fraction. The underlying production modules also feed the executed notebook and generated tables. That shared path is important. It prevents the dashboard from becoming a polished but separate set of formulas.

The project is a piece of applied mathematics and programming evidence, not a profit system or gambling recommendation. It is also a reminder that a result becomes more credible when the data source, selection step, stopping rule, and loss convention are easy to inspect. Roulette is only the teaching system. The habit travels well.
