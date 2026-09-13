# Roulette Analytics Lab

**Optimal Betting Strategy Simulator: A Statistical Laboratory for Roulette Bias, Bankroll Risk and Decision-Making**

[Open the live Streamlit dashboard](https://roulette-analytics-lab.streamlit.app/)

Roulette Analytics Lab is a reproducible Python portfolio project built from the mathematical questions studied in the University of Manchester MATH20062 Group 40 report. It turns a static academic investigation into a tested package, a deterministic analysis pipeline, an executable notebook, and a Streamlit dashboard. The project asks three linked questions: what the rules imply before any wheel is spun, what observed spins can tell us about fairness, and how uncertainty changes bankroll risk.

This is an educational probability project, not a system for making money from gambling. Under a fair wheel and standard casino payouts, every conventional bet has negative expected net return.

## Project background

The source report was written by Jialiang Gong, Joseph Myatt, Jessica Sathiyanathan, Jacob Tinker, and Chenyue Wang for MATH20062 in 2024/25. This repository credits that shared foundation and separates it from Jialiang Gong's subsequent individual work. The source PDF is not redistributed because coauthor publication consent has not been established. Its identity and SHA-256 checksum are recorded in [docs/provenance.md](docs/provenance.md).

The individual extension is an independent Python reimplementation from the paper's mathematical specification. The original MATLAB files were unavailable, so this repository does not claim line-by-line migration. New work includes a typed domain model, complete bet geometry, exact treatment of European special rules, corrected post-selection inference, Monte Carlo power analysis, risk-aware bankroll simulation, automated tests, an interactive product, and publication-ready outputs.

## Questions answered

1. What are the exact expected returns of European and American roulette bets?
2. How do La Partage and En Prison change the edge on even-money bets?
3. How quickly does a running frequency approach its theoretical probability?
4. Can a chi-squared test detect a wheel with one elevated pocket probability?
5. Why is testing the hottest observed pocket as though it were chosen in advance invalid?
6. How do flat betting, progression systems, and conditional Kelly staking alter the distribution of bankroll outcomes?

## Mathematical methods

The package combines finite probability spaces, expectation, variance, random walk simulation, categorical goodness-of-fit testing, Monte Carlo calibration, multiple-testing correction, Bayesian Dirichlet updating, and conditional Kelly optimization. Exact enumeration is used when the wheel rules are fully specified. Simulation is used for path-dependent quantities such as drawdown and for sampling distributions that are awkward to derive analytically.

For a unit stake with net payout odds `b` and win probability `p`, the expected net return is

```text
E[X] = p b - (1 - p).
```

The standard European straight bet has `p = 1/37` and `b = 35`, so `E[X] = -1/37`, a house edge of about 2.70%. The American wheel has 38 pockets and a house edge of about 5.26% for the same advertised payout. The full Kelly fraction, when the assumed `p` is known and greater than the break-even probability, is `(bp - (1-p))/b`. In this project it is treated as a conditional log-growth result, not a guarantee and not an estimate of a real casino advantage.

## Architecture

```text
app.py                          Streamlit entry point
src/roulette_lab/               Tested probability, inference, and simulation package
scripts/run_analysis.py         Deterministic data and publication-output pipeline
scripts/build_notebook.py       Rebuilds and executes the teaching notebook
scripts/build_report_pdf.py     Builds the A4 technical report from Markdown and CSV data
data/                           Reproducible synthetic spin samples
outputs/tables/                 Machine-readable headline results
outputs/figures/                Publication figures
notebooks/                      Executed end-to-end analysis notebook
report/                         Long-form report in Markdown and PDF
docs/                           Blog, provenance, methods, AI workflow, and application material
tests/                          Unit, integration, publication, and reproducibility tests
```

The package keeps wheel mechanics, bet definitions, statistical inference, bankroll rules, and presentation logic separate. This makes claims easier to test and prevents dashboard controls from silently changing the mathematical model.

## Installation

Python 3.12 is required.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
```

## Commands

Run the deterministic analysis:

```bash
.venv/bin/python scripts/run_analysis.py
```

Rebuild and execute the notebook:

```bash
.venv/bin/python scripts/build_notebook.py
```

Launch the dashboard:

```bash
.venv/bin/streamlit run app.py
```

Run the tests:

```bash
.venv/bin/python -m pytest -q
```

## Dashboard controls

The four tabs move from rules to evidence to decisions. **Wheel & Bets** compares wheel type, bet geometry, payout, and special European rules. **Fairness Lab** accepts generated examples or strict CSV input, displays residuals, and contrasts global and post-selection-aware tests. **Bankroll Simulator** exposes starting bankroll, stake, number of spins, path count, stop-loss, take-profit, table limit, payout assumptions, and staking strategy. **Methods & Limits** states the assumptions needed to interpret each output.

Custom payout odds are deliberately labelled hypothetical and simulation-only. They never overwrite the casino-standard analytical tables.

## Published results

The standard straight-bet house edge is 2.70% on a European wheel and 5.26% on an American wheel. For a European even-money bet, La Partage and En Prison reduce the exact edge to about 1.35% under the implemented rules.

In the reproducible fair sample of 1,000 spins, pocket 32 appeared 39 times. A naive one-pocket test gives `p = 0.0164`, but that pocket was selected because it was the hottest. The family-wise Monte Carlo value is `p = 0.4837`, and the global chi-squared asymptotic value is `p = 0.3978`; neither supports a fairness rejection.

In the synthetic biased sample, pocket 17 has true probability 0.060 and appears 61 times. The global chi-squared asymptotic value is `p = 0.0029`, while the Monte Carlo global value is `p = 0.0044`. The family-wise hottest-pocket value is about `0.0001`. This sample is labelled synthetic throughout.

The strategy comparison is a stress test under that favourable synthetic pocket, not evidence of a real-world edge. Across 3,000 paths of 300 spins, Martingale has a median terminal bankroll of 450 from a starting bankroll of 1,000 and a 65.57% probability of finishing below the start. Quarter Kelly has a median of 2,198 and a 1.67% probability of loss in this same assumed scenario. That contrast shows how sizing and constraints change risk; it does not validate the assumed probability.

## Screenshots

The screenshots below were generated from the tested V1 interface. The full interaction record is in [docs/visual_qa.md](docs/visual_qa.md).

### Desktop: bankroll paths and risk metrics

![Roulette Analytics Lab desktop dashboard](docs/assets/dashboard-desktop.png)

### Mobile: wheel economics and probability model

![Roulette Analytics Lab mobile dashboard](docs/assets/dashboard-mobile.png)

The repository also ships six deterministic publication figures in [outputs/figures](outputs/figures). The public dashboard is available at [roulette-analytics-lab.streamlit.app](https://roulette-analytics-lab.streamlit.app/), and the local launch command above runs the same app from source.

## Reproducibility

Every synthetic dataset and Monte Carlo procedure uses a recorded seed. Publication tables are CSV files, and the report builder reads headline values from those files rather than duplicating numbers by hand. The notebook is generated with stable cell identifiers and executed before release. Dependency versions are pinned in `requirements-lock.txt`. The final verifier checks tests, output freshness, notebook execution, report presence, and package contents.

Statistical reproducibility does not remove model uncertainty. A fixed seed reproduces a computation; it does not prove that an assumed pocket probability describes a real wheel.

## AI use

AI tools supported code review, test ideation, documentation structure, and prose editing. Mathematical claims, formulas, generated evidence, and file-level outputs were checked through executable tests and deterministic scripts. Details, boundaries, and verification practices are documented in [docs/ai_workflow.md](docs/ai_workflow.md). AI output is treated as a draft or hypothesis until it passes an independent check.

## Limitations

The supplied spin records are synthetic, not casino observations. The one-pocket alternative is intentionally simple. Spins are modelled as independent and identically distributed unless a specific wheel says otherwise. Results may not transfer to wheels with temporal drift, dealer signatures, measurement error, or changing operating conditions. A statistically detectable deviation is not automatically large enough, stable enough, or legal to exploit. Kelly calculations are highly sensitive to probability error.

## Responsible gambling

Roulette is a negative-expectation game under standard fair-wheel rules. Progression systems do not change the expected value of the underlying bet. Stop-loss and take-profit rules change exposure and the shape of outcomes, but do not create positive expectation. Anyone experiencing harm related to gambling should stop and seek qualified local support.

## Licence

Code is released under the MIT License. The source group report is not included and remains subject to its authors' rights. Generated portfolio prose and figures may be cited with attribution.

## Citation

```bibtex
@software{gong2026roulette,
  author  = {Jialiang Gong},
  title   = {Roulette Analytics Lab},
  year    = {2026},
  version = {0.1.0},
  note    = {Independent Python portfolio extension of the MATH20062 Group 40 report}
}
```
