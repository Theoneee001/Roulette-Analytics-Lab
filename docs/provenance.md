# Provenance and Contribution Boundary

## Source work

The academic starting point is **MATH20062 2024/25 Group 40 Main Project**, a University of Manchester group report about probability, roulette rules, expected return, simulation, and statistical testing. The authors named on the report are:

- Jialiang Gong
- Joseph Myatt
- Jessica Sathiyanathan
- Jacob Tinker
- Chenyue Wang

The local source file used during development is `MATH20062_2024_25_Group_40_main_project.pdf`. Its SHA-256 checksum is:

```text
0364398a2cdcc91b1653604a9ca1b7adfaac529d99bc8e115f53475fa49c40e5
```

The PDF itself is not included in the public repository because permission from every coauthor to republish it has not been established. The checksum allows the analysis source to be identified without redistributing the document.

## Individual extension

This repository is Jialiang Gong's independent Python reimplementation from the paper's mathematical specification. The original MATLAB source files were not available for this build. Consequently, the project does not claim a direct MATLAB-to-Python code migration.

The individual extension covers:

- a tested Python package for wheels, bets, rule variants, inference, and bankroll simulation;
- complete roulette-table bet geometry and validation;
- exact expected-return calculations for Standard, La Partage, and En Prison rules;
- correction of post-selection bias when the hottest pocket is chosen after observing the data;
- Monte Carlo calibration, detection-power analysis, and Dirichlet uncertainty estimates;
- a reproducible notebook, deterministic output pipeline, Streamlit dashboard, technical report, and portfolio materials;
- automated verification for mathematics, data contracts, publication files, and repeatability.

## Corrections and extensions to the source argument

Two points receive special treatment. First, a straight bet on a fair European wheel has expected net return `35/37 - 36/37 = -1/37`; it is not zero. Second, the most frequent observed pocket cannot be tested as if it had been chosen before data collection. The repository reports a global chi-squared test and a family-wise maximum-count Monte Carlo test alongside the naive value so the selection effect remains visible.

## Attribution policy

Descriptions of the group report use collective attribution. Claims about the package, tests, dashboard, notebook, corrected inference, and portfolio narrative refer to the individual extension. This boundary should remain intact in CVs, interviews, applications, and future publications.

