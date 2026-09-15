# Project 1 Deliverables Checklist

This checklist maps the execution manual's Project 1 expectations to repository evidence.

| Requirement | Deliverable | Concrete evidence | Status |
| --- | --- | --- | --- |
| Python reimplementation | Tested package and scripts | [`src/roulette_lab`](../src/roulette_lab), [`scripts`](../scripts), [`tests`](../tests) | Complete |
| Source and personal contribution boundary | Independent implementation from the mathematical specification | [`provenance.md`](provenance.md) | Complete |
| Kelly Criterion | Conditional full, half, and quarter Kelly | [`bets.py`](../src/roulette_lab/bets.py), [`bankroll.py`](../src/roulette_lab/bankroll.py), [`app.py`](../app.py) | Complete |
| Chi-squared testing | Asymptotic and Monte Carlo global tests | [`statistics.py`](../src/roulette_lab/statistics.py), [`roulette_analytics.ipynb`](../notebooks/roulette_analytics.ipynb) | Complete |
| Selection correction | Naive, Bonferroni, and maximum-count family-wise results | [`bias_tests.csv`](../outputs/tables/bias_tests.csv), [`technical_blog.md`](technical_blog.md) | Complete |
| Random walk simulation | Running frequency and bankroll paths | [`03_lln_convergence.png`](../outputs/figures/03_lln_convergence.png), [`06_bankroll_risk.png`](../outputs/figures/06_bankroll_risk.png) | Complete |
| Adjustable dashboard controls | Bankroll, odds, stop-loss, take-profit, paths, spins, seed, and strategy | [`app.py`](../app.py), [`dashboard.py`](../src/roulette_lab/dashboard.py) | Complete |
| Real-time curves | Probability, residual, and bankroll charts | [`dashboard-desktop.png`](assets/dashboard-desktop.png), [`visual_qa.md`](visual_qa.md) | Complete |
| Responsive design | Desktop and 390x844 evidence | [`dashboard-desktop.png`](assets/dashboard-desktop.png), [`dashboard-mobile.png`](assets/dashboard-mobile.png) | Complete |
| Technical blog | Mathematics, implementation, results, and limits | [`technical_blog.md`](technical_blog.md) | Complete |
| Full technical report | 4,500-5,000 prose words and 13-16 page A4 PDF | [`technical_report.md`](../report/technical_report.md), [`technical_report.pdf`](../report/technical_report.pdf) | Complete |
| GitHub-ready repository | README, licence, lock file, commands, CI | [`README.md`](../README.md), [`LICENSE`](../LICENSE), [`requirements-lock.txt`](../requirements-lock.txt), [`reproducibility.yml`](../.github/workflows/reproducibility.yml) | Complete |
| Code reproducibility | Fixed seeds and permanent cross-artifact checks | [`run_analysis.py`](../scripts/run_analysis.py), [`verify_artifacts.py`](../scripts/verify_artifacts.py) | Complete |
| Data | Fair and biased teaching datasets with strict schema | [`example_unbiased_spins.csv`](../data/example_unbiased_spins.csv), [`example_biased_spins.csv`](../data/example_biased_spins.csv), [`README`](../data/README.md) | Complete |
| Machine-readable results | Existing seven tables and six figures remain. The final release contains eleven tables and ten figures. | [`outputs/tables`](../outputs/tables), [`outputs/figures`](../outputs/figures) | Complete |
| Correct interpretation | Negative expectation, post-selection bias, and probability uncertainty | [`technical_report.md`](../report/technical_report.md), [`technical_blog.md`](technical_blog.md) | Complete |
| AI capability evidence | Assisted workflow plus verification boundary | [`ai_workflow.md`](ai_workflow.md) | Complete |
| Application value | CV, PS, interview, contribution, and programme maps | [`application_materials.md`](application_materials.md) | Complete |
| Responsible framing | No profit promise and explicit limitations | [`README.md`](../README.md), [`technical_report.md`](../report/technical_report.md), [`app.py`](../app.py) | Complete |
| Online demonstration | Task 7 release checklist item | [Streamlit deployment target](https://roulette-analytics-lab.streamlit.app/) | Pending public-access verification |

## Release gate

The release is ready only when all automated tests pass, the notebook executes, publication outputs regenerate without drift, the PDF renders cleanly, desktop and mobile dashboard views are checked, the public dashboard is reachable, and the final ZIP passes `unzip -t`. The external manifest records the archive checksum without creating a circular checksum inside the ZIP. The online demonstration remains pending public-access verification in Task 7 and is therefore still a release checklist item.
