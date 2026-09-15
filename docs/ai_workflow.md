# AI-Assisted Engineering Workflow

## Purpose

AI tools were used as engineering assistants during the portfolio extension. They helped decompose requirements, propose tests, inspect implementation details, review visual layouts, and edit prose. They did not replace mathematical verification or establish factual truth by themselves.

## Workflow

1. Requirements from the execution manual and source report were converted into explicit deliverables and acceptance tests.
2. Mathematical behavior was expressed in unit tests before or alongside implementation.
3. Domain modules were kept separate so wheel rules, betting geometry, inference, and simulation could be checked independently.
4. Deterministic scripts generated CSV tables and figures from fixed seeds.
5. Report headline markers were resolved from named generated CSV files instead of being typed or recomputed in publication code.
6. The notebook was rebuilt and executed in a clean kernel.
7. The Streamlit interface was checked at desktop and mobile widths, including browser console output.
8. Public prose was scanned for formula errors, unsupported certainty, missing attribution, repetitive AI-style wording, and em dashes. The requested Rust humanizer detector was attempted before and after publication editing; this workstation could not link it because the active macOS Command Line Tools path is missing. The build failure and equivalent transparent checks are recorded in `task-6-report.md`.

## Verification boundary

An AI suggestion was accepted only after one or more of the following checks: an exact analytical calculation, an automated test, a comparison with a deterministic CSV output, a rendered visual inspection, or a source-provenance check. This matters because fluent text can conceal a wrong denominator, an invalid hypothesis test, or an exaggerated personal contribution.

## Examples of human judgement

- The hottest pocket required a post-selection correction. A naive binomial result was retained only as a teaching contrast.
- Kelly staking was framed as conditional on an assumed probability, not as proof of a profitable opportunity.
- The unavailable MATLAB code prevented a direct migration claim, so the project uses the more accurate phrase "independent Python reimplementation."
- The group PDF was not copied into the repository because coauthor publication consent was unknown.
- Visual design choices were checked against the dashboard's analytical purpose, with compact controls and readable plots taking priority over casino decoration.

## Reproducible evidence

The strongest evidence in this repository is executable. Tests check wheel probability mass, bet coverage, special rules, inference, bankroll state transitions, notebook structure, and publication requirements. Seeds, package versions, source checksums, and generated artifacts are recorded. This workflow makes AI use visible and auditable while keeping responsibility for the final claims with the author.
