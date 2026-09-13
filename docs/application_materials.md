# Application Materials

**Portfolio evidence:** [GitHub repository](https://github.com/Theoneee001/Roulette-Analytics-Lab) | [Live interactive dashboard](https://roulette-analytics-lab.streamlit.app/)

## CV Bullets

- Reimplemented a University of Manchester roulette probability project as a tested Python package and Streamlit product, covering exact expectation, chi-squared inference, Monte Carlo calibration, Bayesian uncertainty, and constrained bankroll simulation.
- Identified and corrected a post-selection error in testing the hottest observed pocket; added family-wise simulation, reproducible power analysis, and 180+ automated tests to support defensible conclusions.
- Built a deterministic analytics pipeline that produces seven CSV tables, six publication figures, an executed notebook, and a 3,000+ word technical report from version-controlled assumptions and seeds.
- Translated undergraduate mathematics into an interactive decision tool with European and American wheels, La Partage and En Prison rules, complete bet geometry, Kelly sensitivity, drawdown, stop-loss, take-profit, and table-limit controls.
- Used AI-assisted engineering for test ideation, code review, and editing while documenting attribution, verification boundaries, and reproducibility rather than presenting generated output as evidence.

## Personal Statement Material

My mathematics degree taught me to move between an abstract model and the assumptions that make it valid. I developed that habit further by rebuilding our MATH20062 roulette investigation as an independent Python analytics product. I encoded European and American wheels, derived exact expected returns, implemented chi-squared and Monte Carlo tests, and simulated constrained bankroll paths. The result I value most was a correction, not a betting strategy. The apparently significant hottest pocket had been selected after observing the data. I corrected the analysis with a family-wise maximum-count test and exposed the difference in an interactive dashboard. This project changed how I use programming: code makes calculations faster, assumptions testable, and conclusions reproducible. I also documented how AI assisted with review and drafting while keeping mathematical checks, attribution, and final judgement explicit. I now want to study digital transformation and technology management so I can apply the same discipline to operational data: connect rigorous quantitative reasoning with usable products, responsible automation, and decisions that non-specialists can inspect.

## Two-Minute Interview Answer

I took a group mathematics report on roulette and asked what would be required to turn it into credible portfolio evidence. I rebuilt the model independently in Python because the original MATLAB files were unavailable. The package represents wheels, valid table bets, payout rules, statistical tests, and bankroll strategies as separate tested components.

The key analytical lesson came from the fairness analysis. If I look at 37 pockets, choose the most frequent one, and then apply a binomial test as if I had chosen it beforehand, the p-value is too optimistic. In the fair 1,000-spin sample, the naive value is about 0.016, but a family-wise simulation gives about 0.484. That changes the conclusion. In a separate synthetic sample where pocket 17 truly has probability 0.060, global and corrected tests do detect the departure.

I then built a Streamlit dashboard so a user can change the wheel, rules, bankroll constraints, and probability assumptions while seeing the result immediately. The project demonstrates mathematics, Python, statistical judgement, product design, and responsible AI use. More importantly, it shows that I can challenge an attractive result, correct it, and communicate why the correction matters.

## Technical Walkthrough

Start with `wheels.py`, which defines immutable European and American sample spaces. `bets.py` maps each legal bet to winning pockets and calculates exact expectation under Standard, La Partage, or En Prison rules. `statistics.py` implements global fairness tests, maximum-count selection correction, posterior updating, and holdout splitting. `bankroll.py` models the state transitions of flat, progression, and conditional Kelly strategies while enforcing minimum chips, table limits, and stopping rules.

`analysis.py` composes these modules into one deterministic bundle. `scripts/run_analysis.py` writes the example datasets, seven result tables, and six figures. `scripts/build_notebook.py` creates and executes the notebook with stable cell identifiers. The Streamlit app calls the same tested functions instead of maintaining a second set of formulas. Finally, the report builder reads the CSV outputs so published headline values remain tied to executable evidence.

## Personal Contribution Answer

The 2024/25 report was group work by five named authors, so I do not claim sole ownership of its original discussion. My individual contribution in this portfolio is the independent Python reimplementation and extension: software architecture, complete bet validation, special-rule expectation, corrected post-selection inference, power analysis, Bayesian uncertainty, bankroll engine, automated testing, dashboard, notebook, report pipeline, visual design, and public documentation. I also recorded the source checksum and withheld the group PDF from publication because consent from all coauthors was not established. This distinction lets me discuss the shared academic origin honestly while providing concrete, inspectable evidence of what I built afterwards.

## CityU DTT Mapping

The project fits a digital transformation and technology track because it converts a static analytical report into a governed digital workflow. Inputs, models, tests, outputs, and user controls are connected through one reproducible system. The dashboard demonstrates how technical assumptions can be exposed to decision-makers instead of being hidden in a spreadsheet or one-off script. Provenance, responsible AI use, and release checks also show attention to technology governance.

## PolyU KTM Mapping

For knowledge and technology management, the strongest connection is the movement from mathematical knowledge to a reusable product. The repository captures tacit analytical decisions as tests, documentation, data contracts, and interface constraints. It also shows how AI-assisted work can be managed through verification and attribution. The result is not merely code; it is a structured knowledge asset that another person can inspect, reproduce, and extend.

## HKUST BDT Mapping

For a big data technology programme, the project demonstrates a complete small-data version of a larger analytical pipeline: validated ingestion, probabilistic modelling, simulation, statistical inference, machine-readable outputs, visual analytics, and reproducibility. Monte Carlo experiments create and process large collections of paths, while vectorised NumPy and pandas operations keep computation practical. The analysis also proves a central data-science point: more computation cannot rescue a biased question, so selection effects and uncertainty must be designed into the method.
