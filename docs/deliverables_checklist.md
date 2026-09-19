# Project 1 Deliverables Checklist

This manual matrix is limited to **Project 1: Roulette Analytics Lab**. Later portfolio projects are explicitly out of scope for this release and do not supply evidence for any row below.

Existing seven tables and six figures remain. The final release contains eleven tables and ten figures.

| Requirement | Code | Test | Output | Report | Dashboard | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Python reimplementation | [package](../src/roulette_lab) | [test suite](../tests) | [tables](../outputs/tables) | [research report](../report/technical_report.pdf) | [Methods](../app.py) | Complete |
| Contribution boundary | [provenance](provenance.md) | [publication test](../tests/test_publication.py) | [provenance checksum](provenance.md) | [research question](../report/technical_report.pdf) | [Methods](../app.py) | Complete |
| Kelly Criterion | [bets](../src/roulette_lab/bets.py) | [bet tests](../tests/test_bets.py) | [kelly sensitivity](../outputs/tables/kelly_sensitivity.csv) | [posterior decisions](../report/technical_report.pdf) | [Decision Risk](../app.py) | Complete |
| Chi-squared testing | [statistics](../src/roulette_lab/statistics.py) | [statistics tests](../tests/test_statistics.py) | [bias tests](../outputs/tables/bias_tests.csv) | [fixed-horizon inference](../report/technical_report.pdf) | [Evidence](../app.py) | Complete |
| Selection correction | [dashboard](../src/roulette_lab/dashboard.py) | [dashboard tests](../tests/test_dashboard.py) | [bias tests](../outputs/tables/bias_tests.csv) | [selection correction](../report/technical_report.pdf) | [Evidence](../app.py) | Complete |
| Random-walk and LLN simulation | [simulation](../src/roulette_lab/simulation.py) | [simulation tests](../tests/test_simulation.py) | [LLN figure](../outputs/figures/03_lln_convergence.png) | [probability contract](../report/technical_report.pdf) | [Live Experiment](../app.py) | Complete |
| Sequential evidence and CUSUM | [sequential](../src/roulette_lab/sequential.py) | [sequential tests](../tests/test_sequential.py) | [sequential evidence](../outputs/tables/sequential_evidence.csv) | [sequential evidence](../report/technical_report.pdf) | [Evidence](../app.py) | Complete |
| Posterior decision and CVaR | [decision](../src/roulette_lab/decision.py) | [decision tests](../tests/test_decision.py) | [posterior edge](../outputs/tables/posterior_edge.csv) | [posterior decisions](../report/technical_report.pdf) | [Decision Risk](../app.py) | Complete |
| Adjustable controls | [app controls](../app.py) | [app tests](../tests/test_app.py) | [risk frontier](../outputs/tables/risk_frontier.csv) | [software design](../report/technical_report.pdf) | [live controls](assets/live-experiment.png) | Complete |
| Live experiment and wheel | [experiment](../src/roulette_lab/experiment.py) | [component tests](../tests/test_roulette_component.py) | [history CSV](../data/example_unbiased_spins.csv) | [software design](../report/technical_report.pdf) | [settled wheel](assets/live-experiment.png) | Complete |
| Real-time charts and downloads | [dashboard figures](../app.py) | [dashboard tests](../tests/test_dashboard.py) | [figures](../outputs/figures) | [risk frontier](../report/technical_report.pdf) | [desktop QA](assets/dashboard-desktop.png) | Complete |
| Responsive design | [responsive CSS](../app.py) | [app tests](../tests/test_app.py) | [mobile capture](assets/dashboard-mobile.png) | [software design](../report/technical_report.pdf) | [visual QA](visual_qa.md) | Complete |
| Teaching data | [strict CSV IO](../src/roulette_lab/io.py) | [IO tests](../tests/test_io_and_power.py) | [fair CSV](../data/example_unbiased_spins.csv) | [experimental design](../report/technical_report.pdf) | [CSV import](app.py) | Complete |
| Notebook and report | [builders](../scripts) | [publication tests](../tests/test_publication.py) | [notebook](../notebooks/roulette_analytics.ipynb) | [PDF](../report/technical_report.pdf) | [Methods](../app.py) | Complete |
| Reproducibility | [analysis runner](../scripts/run_analysis.py) | [artifact verifier](../scripts/verify_artifacts.py) | [all outputs](../outputs) | [methods](../report/technical_report.pdf) | [Methods](../app.py) | Complete |
| Responsible framing | [dashboard copy](../app.py) | [publication tests](../tests/test_publication.py) | [methods output](../outputs/tables/posterior_edge.csv) | [limitations](../report/technical_report.pdf) | [Methods](../app.py) | Complete |
| AI workflow | [workflow record](ai_workflow.md) | [publication tests](../tests/test_publication.py) | [review evidence](ai_workflow.md) | [provenance](../report/technical_report.pdf) | [Methods](../app.py) | Complete |
| Application value | [application materials](application_materials.md) | [publication tests](../tests/test_publication.py) | [portfolio evidence](application_materials.md) | [application value](../report/technical_report.pdf) | [Methods](../app.py) | Complete |
| Online demonstration | [deployment configuration](../.streamlit) | [publication test](../tests/test_publication.py) | [QA screenshots](assets) | [software design](../report/technical_report.pdf) | [verified public deployment](https://roulette-analytics-lab.streamlit.app/) | Verified public deployment: fresh anonymous cookie jar retained server-issued session and CSRF cookies, received HTTP 200, and kept the canonical URL |

## Release gate

Task 7 requires a clean deterministic rebuild, rendered PDF inspection, exact desktop and mobile captures, an anonymous public deployment check, and a `unzip -t` validated V2 archive. The external manifest remains outside the archive so its checksum is not circular.
