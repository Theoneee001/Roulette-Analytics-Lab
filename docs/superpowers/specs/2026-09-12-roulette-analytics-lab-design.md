# Roulette Analytics Lab: Design Specification

**Status:** Approved direction, implementation pending  
**Owner:** Jialiang Gong  
**Source study:** *The Mathematics of Roulette: Analysing Probability and Wheel Bias*, MATH20062 Group 40  
**Portfolio role:** Applied Math & AI Portfolio, Project 1: Optimal Betting Strategy Simulator

## 1. Purpose

This project turns a 19-page university group paper into an individual, reproducible Python product. It will preserve the paper's full mathematical scope while correcting its statistical and financial errors. The result must demonstrate applied probability, software engineering, interactive visualisation, responsible AI use, and the ability to explain a model to both technical and non-technical readers.

The public-facing title will follow the execution manual:

> **Optimal Betting Strategy Simulator**  
> *A Statistical Laboratory for Roulette Bias, Bankroll Risk and Decision-Making*

The word "optimal" will always be qualified. Kelly betting is optimal only for long-run expected logarithmic growth under a correctly specified probability and payout model. The application must not imply that roulette offers a guaranteed profit.

## 2. Provenance and Academic Integrity

The original report was written by Jialiang Gong, Joseph Myatt, Jessica Sathiyanathan, Jacob Tinker, and Chenyue Wang. It provides the conceptual starting point: roulette rules and history, the law of large numbers, uniform and multinomial models, conditional probability, streaks, random walks, betting systems, wheel-bias detection, and the Kelly criterion.

The original MATLAB source is no longer available. The portfolio must therefore describe the new code as an **independent Python reimplementation from the paper's mathematical specification**, not as a line-by-line MATLAB migration. The repository will contain a provenance statement that distinguishes the group paper from Jialiang's later individual work: Python architecture, statistical corrections, simulations, tests, dashboard, technical writing, and product design.

The group PDF will not be committed to the public repository without the co-authors' permission. The repository will instead record its title, authors, course context, local source filename, and SHA-256 checksum in `docs/provenance.md`. The local development copy remains outside Git.

## 3. Success Criteria

The project is successful when a reviewer can:

1. clone the repository and reproduce the published numerical results with documented commands;
2. run a Streamlit dashboard and explore wheel type, bet type, bankroll, stop-loss, strategy, sample size, bias strength, and random seed;
3. upload a valid spin-history CSV and receive an auditable fairness analysis;
4. trace each important mathematical claim from formula to Python function, regression test, visual output, and interpretation;
5. understand why a fair wheel has negative expected return and why apparent winning systems do not remove the house edge;
6. see how global bias detection differs from post-selection testing of the most frequent pocket;
7. inspect a truthful AI-use statement and a clear list of model limitations;
8. use the README, technical article, PDF report, screenshots, CV bullets, personal-statement paragraph, and interview notes without further reconstruction.

## 4. Scope

### 4.1 Included

- European roulette, American roulette, La Partage, and En Prison comparisons.
- Straight-up, split, street, corner, six-line, dozen, column, and even-money bet definitions.
- Exact win probabilities, expected net returns, variance, and house edge.
- Single-spin discrete distributions and multiple-spin multinomial distributions.
- Law of large numbers experiments with confidence bands.
- Independence, streak probabilities, gambler's fallacy, and random-walk demonstrations.
- Global chi-squared goodness-of-fit testing for wheel fairness.
- Selection-aware testing for the most frequent pocket.
- Synthetic unbiased and biased wheels with reproducible random seeds.
- Detection-power experiments over sample size and bias strength.
- Flat betting, Martingale, reverse Martingale, Kelly, and fractional Kelly simulations.
- Risk metrics: expected terminal bankroll, median terminal bankroll, loss probability, ruin probability, maximum drawdown, volatility, and selected quantiles.
- Streamlit dashboard, executable notebook, English technical report, shorter technical blog, application materials, tests, figures, example data, and AI-use documentation.

### 4.2 Excluded from V1

- Claims about identifying or beating a real casino wheel.
- Live casino data collection, scraping, or automated wagering.
- Physical wheel modelling from ball speed, rotor speed, dealer signature, or camera footage.
- Personalised gambling recommendations.
- A claim that the new implementation is the work of the original group.

## 5. Mathematical Design

### 5.1 Wheel and Bet Model

Each wheel is a finite probability vector over labelled pockets. A fair European wheel has 37 pockets with probability `1/37`; a fair American wheel has 38 pockets with probability `1/38`. A biased wheel accepts a validated probability vector whose entries are non-negative and sum to one.

For stake `w`, win probability `p`, and net payout multiple `b`, one-round net profit is `bw` after a win and `-w` after a loss. The expected net profit is

`E[X] = w(pb - (1-p))`.

For a European straight-up bet, `p=1/37` and `b=35`, so expected net profit is `-w/37`, not zero. The implementation will calculate probabilities and payouts from typed bet definitions instead of duplicating constants across the codebase.

La Partage will return half the even-money stake when zero occurs. En Prison will be represented as a small state model because a zero can defer settlement to the next spin. Closed-form expectations will be compared with simulation.

### 5.2 Fairness Testing

The global null hypothesis is that all pocket probabilities are equal. For sufficiently large expected cell counts, the Pearson statistic is

`chi2 = sum((observed_i - expected_i)^2 / expected_i)`.

The application will report the statistic, degrees of freedom, p-value, effect size, expected counts, assumptions, and a plain-language interpretation. It will refuse or warn against an asymptotic chi-squared conclusion when expected counts are too small and will offer a Monte Carlo null p-value instead.

The original paper treats the observed maximum count as if it were a pre-selected binomial count. That is not valid because the pocket is chosen after viewing all 37 counts. V1 will provide two auditable corrections:

- a family-wise Monte Carlo max-count test under the full multinomial null;
- a Bonferroni-adjusted one-pocket binomial tail as a conservative reference.

The selected pocket's probability will not be estimated and evaluated on the same spins without a warning. The analysis will support an estimation/validation split and a Dirichlet posterior estimate so that Kelly calculations do not blindly use the largest raw frequency.

### 5.3 Kelly and Risk

For a straight-up European bet with net odds `b=35`, the full-Kelly fraction is

`f* = (p(b+1)-1)/b = (36p-1)/35`.

A positive fraction requires `p > 1/36`, not merely `p > 1/37`. V1 will show zero allocation when the estimate does not clear the break-even probability. It will also offer half- and quarter-Kelly settings, stake caps, minimum chip sizes, and a conservative probability input based on a lower credible or confidence bound.

"Optimal" refers to expected log growth under the specified model. The dashboard must display the assumptions and show drawdown and ruin behaviour alongside growth. A strategy ranking based only on average terminal wealth is not acceptable.

### 5.4 Simulation and Validation

Vectorised Monte Carlo simulations will use explicit `numpy.random.Generator` instances and recorded seeds. Common random numbers will be used when strategies are compared under the same wheel so that differences are less noisy. Published outputs will state the number of paths and spins.

Analytical results will be validated against simulation for fair-wheel probabilities, expected returns, streak probabilities, and special-rule house edges. Every published Monte Carlo mean, probability, or quantile will state its simulation size and uncertainty measure; deterministic closed-form quantities will be labelled as exact under the stated model rather than given artificial confidence intervals.

## 6. Product and Dashboard Design

The dashboard is the product, not a marketing landing page. It opens directly into an analytical workspace with four views:

1. **Wheel and Bets:** wheel layout, selectable rules, exact probabilities, payouts, expected returns, and house-edge comparisons.
2. **Fairness Lab:** generated or uploaded spin records, observed-versus-expected chart, chi-squared test, max-count correction, residuals, and power analysis.
3. **Bankroll Simulator:** initial bankroll, bet type, strategy, stake rule, odds, stop-loss, take-profit, path count, spin count, and seed controls; output includes paths and risk distributions.
4. **Methods and Limits:** equations, assumptions, provenance, AI-use summary, responsible-gambling statement, and links to the full report.

The visual language will be an analytical laboratory rather than a casino advertisement. The base palette will use off-white, near-black, roulette green, outcome red, and restrained gold for emphasis. Typography will be compact and readable. Charts must remain distinguishable without relying on red versus green alone. Cards will be limited to repeated metric summaries; sections will not be nested inside decorative containers.

The dashboard will include useful empty, loading, invalid-file, infeasible-strategy, and no-edge states. Every unfamiliar control will have concise help text. Uploaded data will be validated for schema, wheel type, pocket labels, missing values, and sample size before analysis.

## 7. Software Architecture

```text
roulette_analytics_lab/
  app.py
  src/roulette_lab/
    wheels.py
    bets.py
    statistics.py
    bankroll.py
    simulation.py
    validation.py
    reporting.py
  notebooks/
    roulette_analytics.ipynb
  data/
    README.md
    example_unbiased_spins.csv
    example_biased_spins.csv
  outputs/
    figures/
    tables/
    analysis_summary.md
  report/
    technical_report.md
    technical_report.pdf
  docs/
    technical_blog.md
    methodology_map.md
    ai_workflow.md
    application_materials.md
    deliverables_checklist.md
    provenance.md
  tests/
  scripts/
    run_analysis.py
    build_notebook.py
    build_report_pdf.py
    verify_artifacts.py
  .github/workflows/reproducibility.yml
  README.md
  requirements.txt
  requirements-lock.txt
  LICENSE
```

Domain logic will not depend on Streamlit. The application layer calls tested functions in `src/roulette_lab`, and the notebook and report generator use the same functions. This prevents the dashboard, notebook, and PDF from drifting into separate implementations.

The data flow is:

`validated configuration/data -> mathematical model -> deterministic analysis or seeded simulation -> tidy result tables -> charts -> dashboard/notebook/report`.

## 8. Reproducibility and Testing

The test suite will cover:

- probability vectors and wheel labels;
- bet coverage and exact expected-value identities;
- known European and American house edges;
- La Partage and En Prison analytical-versus-simulation agreement;
- multinomial simulation reproducibility;
- chi-squared statistic and p-value against trusted SciPy calculations;
- small-sample fallback behaviour;
- max-count correction calibration under a fair wheel;
- power increasing with sample size or bias strength within simulation tolerance;
- Kelly break-even and stake constraints;
- stop-loss, table limit, zero-bankroll, and minimum-chip edge cases;
- deterministic published tables and notebook execution;
- required README, report, screenshots, and AI disclosure content.

GitHub Actions will install pinned dependencies, run tests, regenerate outputs, execute the notebook, build the PDF, and fail if tracked deterministic artifacts change.

## 9. Written Deliverables

The English technical report will contain 3,000-5,000 words of prose even though this word limit belongs to the manual's academic-project standard rather than its Roulette portfolio subsection. Applying the stricter standard strengthens the submission. It will include problem definition, mathematical model, implementation, visual results, interpretation, limitations, provenance, and references.

The technical blog will be shorter and reader-oriented. It will focus on three ideas: why fair roulette has negative drift, why the hottest observed number needs a selection correction, and why Kelly depends on reliable probability estimation.

Application material will include:

- a concise CV entry with quantified technical scope;
- a 150-200 word personal-statement paragraph;
- a two-minute interview explanation;
- a longer technical interview walkthrough;
- a direct answer to "What did you personally add after the group project?";
- a mapping to CityU Digital Transformation, PolyU Knowledge and Technology Management, and HKUST Big Data Technology.

All public prose will receive a professional Humanizer pass without removing mathematical terminology, numerical results, caveats, or source attribution.

## 10. AI Use and Human Oversight

The project will document the AI tools actually used. Codex may assist with architecture, test generation, implementation drafts, debugging, visual QA, and prose editing. The documentation will not claim use of Cursor, GitHub Copilot, Figma, or v0.dev unless those tools are genuinely used.

Human oversight will include checking equations against primary references, running analytical-versus-simulation tests, inspecting generated figures and PDF pages, reviewing claims about the original group work, and recording remaining limitations. AI-generated output is never treated as evidence by itself.

## 11. Manual Requirement Mapping

| Manual requirement for Roulette Project 1 | Planned evidence |
|---|---|
| Python reconstruction | Tested package under `src/roulette_lab` with provenance statement |
| Kelly Criterion | Exact and fractional Kelly module, break-even tests, uncertainty controls |
| Chi-squared test | Global test, assumption checks, Monte Carlo fallback, selection correction |
| Random Walk simulation | Analytical drift plus seeded bankroll-path experiments |
| Streamlit Dashboard | Four-view working application with complete control and error states |
| Initial bankroll control | Numeric input with validation |
| Odds/bet control | Wheel rule and typed bet selectors with derived payouts |
| Stop-loss control | Enforced per path with tests |
| Real-time win/risk curves | Cached recomputation of probability, path, and distribution charts |
| Detailed technical blog | `docs/technical_blog.md` |
| Mathematical explanation | Report, methods view, notebook, and formula-to-code map |
| Code implementation explanation | README architecture and technical blog |
| Results analysis | Versioned tables, figures, report, and dashboard interpretation |
| AI-enabled development | Truthful `docs/ai_workflow.md` with validation record |
| README + code + data + results | Root README and complete repository structure |
| Online demonstration | Local V1 first, then Streamlit deployment after acceptance |
| Result screenshots | Desktop and mobile screenshots after visual QA |

## 12. Matching Value for Applications

### Programming with Python (70)

The evidence will be the engineering depth: reusable modules, typed interfaces, vectorised simulation, statistical validation, automated tests, CI, notebook execution, and a deployed application. The claim is demonstrable rather than asserted.

### Mathematics, Programming, and Visualisation

The formula-to-code map will connect probability theory to implementation and charts. Corrections to post-selection inference and expected-return calculations will show development beyond the original group paper.

### CityU: Digital Transformation and Technological Innovation

The project converts a static academic report into a usable analytical product with validated uploads, interactive decisions, explainable outputs, and deployment. The application materials will emphasise product translation rather than casino subject matter.

### PolyU: Knowledge and Technology Management

The repository packages specialist knowledge into reusable code, documentation, model assumptions, provenance, and reproducible workflows. It demonstrates knowledge transfer and governance, not only numerical calculation.

### HKUST: Big Data Technology

The project uses scalable simulation patterns, tidy data pipelines, statistical testing, experiment configuration, and reproducibility. It will describe these honestly as data-intensive methods rather than claiming a genuinely large production dataset.

### EY Product-Design Narrative

The Streamlit application will demonstrate requirements thinking, information hierarchy, user controls, validation, explainability, and visual QA. This provides a concrete product counterpart to the Figma-demo experience described in the application plan without claiming that the Roulette dashboard was produced during EY work.

## 13. Acceptance Gate for V1

V1 is ready for review only when:

- all automated tests pass;
- the deterministic artifact verifier passes;
- the notebook executes from a clean environment;
- the PDF renders without clipping, missing glyphs, or unreadable tables;
- desktop and mobile dashboard screenshots show no overlap or blank charts;
- uploaded valid and invalid CSV examples behave correctly;
- analytical benchmarks agree with simulation within declared tolerances;
- all Project 1 manual requirements have concrete file or application evidence;
- the Humanizer detector passes the README, report, blog, and application materials;
- no text overstates personal authorship, real-world profitability, AI use, or data provenance.
