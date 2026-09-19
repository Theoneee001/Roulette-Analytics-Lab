# Application Materials

**Portfolio evidence:** [GitHub repository](https://github.com/Theoneee001/Roulette-Analytics-Lab) | [verified public Streamlit deployment](https://roulette-analytics-lab.streamlit.app/), confirmed with a fresh anonymous cookie jar that retained server-issued session and CSRF cookies and received HTTP 200 at the canonical URL

## CV Bullets

- Independently rebuilt a University of Manchester roulette mathematics project as a tested Python package and Streamlit analytics product, with exact casino-rule modelling, fixed-horizon inference, and constrained bankroll simulation.
- Corrected a post-selection error in the hottest-pocket claim and added maximum-count simulation, sequential likelihood-ratio evidence, CUSUM diagnostics, posterior uncertainty, and a CVaR risk frontier.
- Built a deterministic publication pipeline in which generated CSV evidence feeds an executed notebook, a long-form PDF report, figures, and reproducibility checks.
- Translated probability and statistical reasoning into adjustable product controls, while labelling synthetic scenarios, hypothetical inputs, and the limits of Kelly sizing.
- Documented AI-assisted drafting and review with explicit attribution, test, provenance, and visual-verification boundaries.

## Personal Statement Material

Manchester mathematics taught me to move from a clean model to the assumptions that make it useful. I developed that habit by rebuilding our MATH20062 roulette investigation as an independent Python analytics product. I modelled wheel rules, calculated exact returns, implemented chi-squared and Monte Carlo tests, and simulated constrained bankroll paths. The result I value most was a correction: the hottest pocket had been selected after the data were inspected, so a naive one-pocket p-value was too optimistic. I added a family-wise simulation, sequential evidence, and a dashboard that keeps assumptions visible. Programming with Python, where I received 70, gave me a base that I have extended through tested modules, reproducible outputs, and product design. I want postgraduate study to deepen that bridge between mathematics, AI-assisted programming, and decisions that people can inspect. This project is evidence of that direction, not a claim that it cancels weaker parts of my transcript.

## Two-Minute Interview Answer

I took a group mathematics report on casino roulette and asked what would make it credible individual portfolio evidence. The original MATLAB files were unavailable, so I built an independent Python reimplementation with separate modules for wheel rules, bets, inference, and bankroll state.

The main analytical correction concerns selection. If I inspect all pockets, choose the hottest one, and then use a binomial tail as though I chose it in advance, the result is too optimistic. I kept that naive comparison as a teaching contrast, then added a maximum-count simulation that repeats the search under the fair null. I also separated fixed-horizon evidence from a pre-specified sequential likelihood-ratio monitor and a targeted CUSUM diagnostic.

The dashboard lets a user inspect the wheel contract, data assumptions, posterior uncertainty, Kelly fractions, and risk frontier. It does not claim to beat casinos. The project shows how I combine Manchester mathematics, Programming with Python 70, AI-assisted engineering, and product thinking: I make assumptions executable, test them, and present their limits alongside the result.

## Technical Walkthrough

`wheels.py` defines immutable European and American sample spaces. `bets.py` maps legal table bets to winning pockets and calculates exact expectation under Standard, La Partage, or En Prison. `statistics.py` handles global fairness tests and selection correction. `bankroll.py` implements constraints and path simulation. The V2 modules add likelihood-ratio and CUSUM paths, posterior edge summaries, conditional value at risk, and common-random-number risk frontiers.

`analysis.py` composes the production functions into deterministic outputs. `scripts/run_analysis.py` writes the named CSV tables and figures. `scripts/build_notebook.py` imports those production functions and presents generated evidence rather than defining its own formulas. The PDF builder resolves report headline markers from named CSV files. Streamlit calls the same validated package, so the interactive product is connected to the research artefacts.

## Personal Contribution Answer

The 2024/25 report was group work by five named authors, and I do not claim sole ownership of its original discussion. My individual portfolio contribution is the independent Python reimplementation and extension: software structure, complete bet validation, stateful special rules, post-selection correction, sequential and change-point methods, posterior decision summaries, constrained risk simulation, tests, dashboard, notebook, report pipeline, and public documentation. I recorded the source checksum and did not republish the group PDF because coauthor publication consent was unknown. That boundary is important to me because it makes the later individual work inspectable without overstating the starting point.

## CityU DTT Mapping

For a digital transformation and technology programme, the project shows how a static analysis can become a governed digital workflow. Inputs, tested models, generated evidence, user controls, and documentation are connected. The dashboard makes technical assumptions visible to a non-specialist user rather than leaving them in a private script.

## PolyU KTM Mapping

For knowledge and technology management, the strongest connection is turning analytical judgement into a reusable asset. Tests, data contracts, documentation, and interface constraints preserve decisions that would otherwise remain implicit. The AI-use record shows how assisted work can remain attributable and reviewable.

## HKUST BDT Mapping

For a data and technology programme, the project demonstrates a small but complete analytical pipeline: validated input, probability modelling, simulation, inference, machine-readable output, visual explanation, and reproducibility. Its central data-science lesson is equally important: more computation cannot repair a question that ignored selection or uncertainty.
