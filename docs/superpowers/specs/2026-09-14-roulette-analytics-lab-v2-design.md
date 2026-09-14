# Roulette Analytics Lab V2: Design Specification

**Status:** Approved direction, implementation pending  
**Owner:** Jialiang Gong  
**Primary audience:** Postgraduate admissions reviewers  
**Research direction:** Statistical inference under selection, sequential observation, and model uncertainty  
**Interface direction:** Evidence Cockpit, revision C2

## 1. Purpose

V2 will turn the existing roulette portfolio into a stronger piece of applied statistical research. The central question is no longer only whether a wheel looks biased or which staking rule produces the largest simulated bankroll. It is:

> What conclusions remain defensible when the pocket is selected after inspection, the sample is observed sequentially, the data-generating process may change, and the probability used for betting is uncertain?

Roulette remains a compact teaching system. Its outcome space and contractual payouts are exact, while its observed probabilities must be inferred from finite data. That separation allows the project to demonstrate probability theory, statistical testing, Bayesian updating, stochastic processes, risk analysis, software engineering, and responsible communication without claiming a method for beating casinos.

The upgrade must improve depth and presentation together. Advanced methods will be exposed through an interactive experiment rather than added as disconnected equations. Every headline result must remain traceable from mathematical definition to tested Python, generated output, report interpretation, and dashboard state.

## 2. Success Criteria

V2 is successful when an admissions reviewer can:

1. identify a clear research question and understand why it is harder than a standard chi-squared exercise;
2. distinguish fixed-horizon testing from repeated observation and post-selection inference;
3. see how Bayesian uncertainty changes the decision to bet, including the probability that an apparent edge is actually below break-even;
4. inspect a time-varying simulation and understand what a change-point diagnostic can and cannot establish;
5. compare strategies through log growth, probability of loss, drawdown, and conditional value at risk rather than one average bankroll;
6. interact with a polished European roulette experiment whose spins update the statistical record in real time;
7. reproduce every publication table, figure, notebook output, and PDF from the repository;
8. separate the original group report from Jialiang Gong's individual Python, statistical, product, and writing contributions.

## 3. Research Scope

### 3.1 Fixed-Horizon Fairness Analysis

The existing Pearson chi-squared test, multinomial Monte Carlo calibration, maximum-count family-wise correction, Bonferroni reference, Dirichlet posterior, and train-validation split remain. V2 will make their experimental roles more explicit:

- The global test asks whether the complete count vector is compatible with the fair-wheel null.
- The maximum-count test repeats the search for the hottest pocket inside each null simulation.
- A pre-specified pocket can be analysed directly, but a data-selected pocket must use corrected or held-out evidence.
- Effect size and power accompany p-values so that non-rejection is not described as proof of fairness.

### 3.2 Sequential Evidence

Repeatedly recomputing an ordinary fixed-horizon p-value after every spin inflates the chance of a false discovery. V2 will therefore add a pre-specified one-pocket likelihood-ratio process for a simple null `p0` and simple alternative `p1`.

For indicator `X_t` showing whether spin `t` lands on the target pocket, the cumulative log likelihood ratio is

```text
log LR_t = sum[X_s log(p1/p0) + (1-X_s) log((1-p1)/(1-p0))].
```

The corresponding likelihood ratio is a non-negative martingale under the simple null. A threshold of `1/alpha` supplies a time-uniform rejection rule through Ville's inequality. The dashboard will show this evidence process beside the ordinary fixed-horizon p-value, explicitly explaining why their interpretations differ.

This is not an unrestricted bias detector. The pocket and alternative probability must be specified before monitoring. Data-driven selection still requires multiplicity control or a fresh validation stream.

### 3.3 Change-Point Diagnostics

The i.i.d. assumption will be challenged with a one-pocket Bernoulli change scenario. A Page-style CUSUM accumulates positive log-likelihood increments for movement from `p0` to `p1` and resets when the cumulative evidence becomes negative. The output includes the score path, threshold, first alarm time, and detection delay when the simulated change time is known.

Published experiments will compare a stationary fair stream with a synthetic stream that changes at a recorded spin. Monte Carlo results will estimate false-alarm frequency and detection delay for the chosen threshold. The report will call this a targeted diagnostic, not proof of a mechanical wheel defect.

### 3.4 Bayesian Edge Uncertainty

For a pre-specified pocket, a Beta marginal from the Dirichlet model will produce:

- posterior mean and credible interval for the pocket probability;
- posterior probability that `p` exceeds the break-even value `1/(b+1)`;
- posterior distribution of expected net return;
- posterior predictive interval for the number of hits in a future sample.

The decision layer will compare three stake fractions:

1. plug-in Kelly using the posterior mean;
2. fractional Kelly using one-half or one-quarter of that fraction;
3. posterior-quantile Kelly using a lower posterior quantile as a conservative probability input.

Posterior-quantile Kelly will be labelled as a robust heuristic, not a universal optimum. Its purpose is to show how uncertainty can eliminate a nominal positive stake even when the point estimate clears break-even.

### 3.5 Risk Frontier

Strategy summaries will add expected log return and lower-tail risk. Conditional value at risk will be defined on terminal loss at a stated tail level, with the sign convention documented in code and report. A risk frontier will compare growth against drawdown and CVaR across stake fractions.

The project will not rank strategies with one universal score. The report will explain that the preferred point depends on horizon, constraints, model confidence, and risk tolerance. Standard fair-wheel scenarios must continue to produce no positive Kelly allocation.

## 4. Software Architecture

New research code will remain independent of Streamlit:

```text
src/roulette_lab/
  sequential.py      likelihood-ratio paths, time-uniform thresholds, CUSUM
  decision.py        posterior edge summaries, predictive checks, robust Kelly
  risk.py            CVaR, expected log growth, and risk-frontier summaries
```

Existing modules retain their current ownership:

- `wheels.py` owns probability spaces and simulated wheel definitions.
- `bets.py` owns legal roulette geometry, payouts, exact return, and base Kelly calculations.
- `statistics.py` owns fixed-horizon goodness-of-fit and posterior estimation.
- `bankroll.py` owns path simulation, constraints, stopping rules, and bankroll state.
- `analysis.py` composes deterministic publication outputs.
- `dashboard.py` converts validated inputs into presentation-ready view models.

The Streamlit app will not contain duplicate statistical formulas. It will call typed functions through view models. Live experiment state will use a small tested session model containing spin history, chosen wheel, target pocket, bankroll state, last result, and deterministic random generator seed.

## 5. Evidence Cockpit Interface

### 5.1 Information Architecture

The dashboard will open as an analytical workspace with five views:

1. **Live Experiment:** animated European or American wheel, single-spin and batch controls, experiment history, and immediate evidence updates.
2. **Evidence:** global fairness, selection-aware tests, sequential likelihood ratio, Bayesian intervals, and change-point diagnostics.
3. **Decision Risk:** posterior edge probability, Kelly sensitivity, wealth paths, fan chart, drawdown, and CVaR frontier.
4. **Wheel Mechanics:** exact bet economics, table geometry, special European rules, and standard versus hypothetical payouts.
5. **Methods:** assumptions, equations, provenance, AI-use boundary, glossary, and responsible interpretation.

The sidebar will hold experimental inputs only. Results will remain in the main workspace. Expensive simulations will run after an explicit apply action; lightweight spin and chart updates will feel immediate.

### 5.2 Live Roulette Interaction

The roulette component will use the correct European or American wheel order, alternating pocket colours, a green zero sector, a metallic outer track, inner rotor, pointer, and ball. A Python-generated result remains the source of truth. The visual component receives that result and animates toward it; animation does not choose the outcome.

One spin appends one observation to session history. Batch actions append 10, 50, or 100 observations without pretending to animate each spin. Reset requires a deliberate control and restores the recorded seed. CSV download exposes the complete experiment history.

### 5.3 Motion and Responsiveness

The spin sequence follows three phases:

1. wheel and ball accelerate, then decelerate with separate easing curves;
2. the result settles and receives a short visual emphasis;
3. metrics and trend lines update over 300 to 500 milliseconds.

Animations must not resize containers or move controls. `prefers-reduced-motion` disables decorative movement and replaces the spin with a short state transition. Desktop and mobile layouts preserve controls, chart labels, and interpretation text without overlap. Mobile uses a stacked experiment and evidence layout with horizontally scrollable view tabs.

### 5.4 Visual System

The selected C2 direction uses a continuous evidence workbench rather than a card grid:

- near-black `#171816` for the experiment stage and navigation;
- off-white `#F7F7F4` for analytical content;
- restrained crimson `#D32842` as the single interface accent;
- neutral silver greys for borders and wheel hardware;
- green only where roulette semantics require the zero pocket.

Sections use rules, spacing, and background shifts instead of floating cards. Metric blocks share one stable height. Controls use one small radius scale, while the roulette remains circular by definition. Typography is a compact system sans stack with tabular numerals and a monospace face for experiment state.

## 6. Publication Outputs

The deterministic pipeline will expand from seven tables and six figures. V2 must add at least:

- `sequential_evidence.csv` and a likelihood-ratio figure;
- `change_point_results.csv` and a CUSUM figure;
- `posterior_edge.csv` and a posterior edge-density figure;
- `risk_frontier.csv` and a growth-versus-tail-risk figure.

The executed notebook will follow the research argument in the same order as the report. It will derive the methods, call production functions, display generated tables, and explain one fair, one stationary biased, and one changing-bias scenario.

The technical report will remain within 4,500 to 5,000 English prose words. It will gain a sharper research question, sequential inference, change-point, posterior decision, and risk-frontier sections by compressing repeated background material. The PDF will target 13 to 16 A4 pages with a restrained cover, consistent running headers, readable equations, numbered figures and tables, page-safe section breaks, and no decorative filler.

The technical blog will focus on one argument: why an apparent edge can disappear after selection correction, sequential correction, and posterior uncertainty. README, methodology map, AI workflow, application materials, visual QA, and the deliverables checklist will be updated to reflect V2 without exaggerating individual contribution or research certainty.

## 7. Error Handling and Performance

- Invalid uploads fail with a concrete schema or label message.
- Incompatible wheel and dataset choices are blocked before analysis.
- Sequential methods reject invalid probabilities, thresholds, and empty streams.
- CUSUM output states when no alarm occurs.
- Kelly controls display zero allocation when the conservative probability does not clear break-even.
- Long simulations expose a bounded progress state and use deterministic caching where inputs are identical.
- The warm dashboard should respond to a single spin within one second on the deployment target. Batch simulation may take longer but must preserve layout and show progress.

## 8. Testing and Verification

Implementation will use test-driven development. New tests will cover:

- likelihood-ratio increments and time-uniform thresholds;
- deterministic sequential paths for all-hit and no-hit streams;
- CUSUM reset, alarm, no-alarm, and detection-delay behavior;
- posterior edge probability and predictive interval boundaries;
- plug-in, fractional, and posterior-quantile Kelly behavior around break-even;
- CVaR sign convention, monotonic tail selection, and risk-frontier schema;
- live experiment state, deterministic spin history, reset, and batch updates;
- dashboard view-model contracts and invalid states;
- publication file count, schema, report word range, figure dimensions, and cross-artifact headline consistency.

Full verification includes the Python test suite, deterministic analysis rebuild, notebook execution, PDF rebuild and rendering, artifact verifier, ZIP integrity, GitHub Actions, public deployment, desktop screenshots, mobile screenshots, interaction checks, browser console review, and nonblank wheel rendering.

## 9. Delivery and Migration

V2 will preserve the public repository and Streamlit URL. Work will be committed in reviewable stages: research engine, publication pipeline, dashboard experience, report and documentation, then release packaging. The final ZIP will be generated from the exact source commit and recorded in an external manifest to avoid a circular checksum.

The existing V1 release remains a recoverable Git history point. V2 will not include the original group PDF, private credentials, browser state, virtual environments, caches, or brainstorm mockups.

## 10. Non-Goals

- live casino scraping or automated wagering;
- personalised gambling advice or profit promises;
- physical wheel prediction from video, dealer motion, or hardware sensors;
- an unrestricted claim that sequential evidence identifies any possible bias;
- a claim that advanced mathematics compensates for poor sampling design;
- redistribution of the group report without coauthor permission.
