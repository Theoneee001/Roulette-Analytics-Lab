# Project 1 Deliverables Checklist

This checklist maps the execution manual's Project 1 expectations to repository evidence.

| Requirement | Deliverable | Evidence | Status |
| --- | --- | --- | --- |
| Python programming evidence | Tested package and scripts | `src/roulette_lab`, `scripts`, `tests` | Complete |
| Roulette project reconstruction | Independent implementation from mathematical specification | `docs/provenance.md`, package modules | Complete |
| Kelly Criterion | Conditional full, half, and quarter Kelly | `bets.py`, `bankroll.py`, dashboard | Complete |
| Chi-squared testing | Asymptotic and Monte Carlo global tests | `statistics.py`, notebook, report | Complete |
| Random walk simulation | Bankroll paths and drawdown analysis | `bankroll.py`, figure 06 | Complete |
| Interactive dashboard | Adjustable assumptions and live charts | `app.py`, `dashboard.py` | Complete |
| Technical blog | Mathematics, implementation, results, and limits | `docs/technical_blog.md` | Complete |
| Full technical report | 3,000 to 5,000 words plus figures | `report/technical_report.md`, PDF | Complete after build |
| GitHub-ready repository | README, licence, lock file, commands | repository root | Complete |
| Code reproducibility | Fixed seeds and deterministic outputs | `scripts/run_analysis.py`, tests | Complete |
| Data | Fair and biased teaching datasets | `data/*.csv` | Complete |
| Correct interpretation | Negative expectation and selection correction | report, blog, README | Complete |
| AI capability evidence | Documented assisted workflow and checks | `docs/ai_workflow.md` | Complete |
| Application value | CV, PS, interview, contribution, programme maps | `docs/application_materials.md` | Complete |
| Personal portfolio boundary | Group credit and individual extension | `docs/provenance.md` | Complete |
| Responsible framing | No profit promise; limitations stated | README, report, dashboard | Complete |

## Release gate

The release is ready only when all automated tests pass, the notebook executes, publication outputs regenerate without drift, the PDF renders cleanly, desktop and mobile dashboard views are checked, and the final ZIP passes `unzip -t`. The external manifest records the archive checksum without creating a circular checksum inside the ZIP.

