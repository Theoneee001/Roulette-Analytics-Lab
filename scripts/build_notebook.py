"""Build and execute the deterministic V2 research notebook."""

import os
from pathlib import Path
import tempfile

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "notebooks" / "roulette_analytics.ipynb"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("IPYTHONDIR", str(ROOT / ".ipython"))


def _markdown(title: str, body: str):
    return nbformat.v4.new_markdown_cell(f"## {title}\n\n{body}")


def _table(name: str, expression: str):
    return nbformat.v4.new_code_cell(
        f"# Generated evidence: outputs/tables/{name}.csv\n{expression}"
    )


def build_notebook():
    notebook = nbformat.v4.new_notebook(
        metadata={
            "kernelspec": {"display_name": "Python 3.12", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12", "mimetype": "text/x-python", "codemirror_mode": {"name": "ipython", "version": 3}, "pygments_lexer": "ipython3", "nbconvert_exporter": "python", "file_extension": ".py"},
        }
    )
    notebook.cells = [
        nbformat.v4.new_markdown_cell(
            "# Roulette Analytics Lab V2\n\n"
            "A reproducible research notebook for **casino roulette**. It imports the "
            "tested production package and presents named generated CSV outputs rather "
            "than maintaining notebook-only formulas."
        ),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "import pandas as pd\n\n"
            "ROOT = Path.cwd()\n"
            "sys.path.insert(0, str(ROOT / 'src'))\n\n"
            "from roulette_lab.analysis import AnalysisConfig, run_full_analysis\n"
            "from roulette_lab.bets import expected_net_return\n"
            "from roulette_lab.decision import posterior_edge_summary\n"
            "from roulette_lab.risk import build_risk_frontier\n"
            "from roulette_lab.sequential import cusum_change_detection, likelihood_ratio_path\n"
            "from roulette_lab.statistics import max_count_test\n\n"
            "TABLES = ROOT / 'outputs' / 'tables'\n"
            "tables = {path.stem: pd.read_csv(path) for path in TABLES.glob('*.csv')}\n"
            "pd.options.display.float_format = '{:.6f}'.format\n"
            "production_interfaces = (run_full_analysis, expected_net_return, max_count_test, "
            "likelihood_ratio_path, cusum_change_detection, posterior_edge_summary, build_risk_frontier)\n"
            "print(f'Loaded {len(tables)} generated CSV tables and {len(production_interfaces)} production interfaces.')"
        ),
        _markdown(
            "Exact Wheel Economics",
            "The casino contract comes first. `house_edges.csv` reports exact expected "
            "net returns and house edges for European and American wheels, plus the two "
            "implemented European special rules. A fair wheel is not the same as a fair wager.",
        ),
        _table("house_edges", "tables['house_edges'][['rule', 'bet', 'expected_net_return', 'house_edge']]"),
        _markdown(
            "Random Walk and Law of Large Numbers",
            "The cumulative frequency table makes the convergence claim concrete. A finite "
            "random walk can rise while the fair-wheel expected return remains negative; "
            "long-run frequency convergence is not a promise about a single path.",
        ),
        _table("lln_convergence", "tables['lln_convergence'].iloc[[0, 9, 99, -1]][['spin', 'empirical_probability', 'theoretical_probability', 'absolute_error']]"),
        _markdown(
            "Fixed-Horizon Fairness",
            "A global chi-square test examines the complete pre-defined count vector. "
            "The Monte Carlo column provides a multinomial calibration for the same "
            "fixed-horizon question.",
        ),
        _table("bias_tests", "tables['bias_tests'][['dataset', 'spins', 'chi_square_statistic', 'asymptotic_p_value', 'monte_carlo_global_p_value']]"),
        _markdown(
            "Selection Correction",
            "The hottest pocket was chosen after inspecting all pockets. `bias_tests.csv` "
            "therefore keeps the naive one-pocket tail beside Bonferroni and maximum-count "
            "family-wise values. The latter represents the actual search procedure.",
        ),
        _table("bias_tests", "tables['bias_tests'][['dataset', 'hottest_label', 'observed_max', 'naive_p_value', 'bonferroni_p_value', 'familywise_p_value']]"),
        _markdown(
            "Sequential Evidence",
            "Repeated fixed-horizon peeking changes its calibration. The production "
            "likelihood-ratio process uses a pre-specified simple null, simple alternative, "
            "and threshold. The displayed table is generated evidence, not a notebook calculation.",
        ),
        _table("sequential_evidence", "tables['sequential_evidence'].groupby('scenario', as_index=False).tail(1)[['scenario', 'spin', 'cumulative_hits', 'e_value', 'e_value_threshold', 'first_crossing', 'fixed_horizon_p_value']]"),
        _markdown(
            "CUSUM Change-Point Diagnostic",
            "CUSUM is a targeted diagnostic for a declared upward change. It reports alarms "
            "and simulated delay for the synthetic scenario, but it cannot establish the physical "
            "cause or exact timing of a real change.",
        ),
        _table("change_point_results", "tables['change_point_results'].groupby('scenario', as_index=False).tail(1)[['scenario', 'cusum_threshold', 'first_alarm', 'detection_delay', 'false_alarm_rate', 'median_detection_delay']]"),
        _markdown(
            "Posterior Edge Uncertainty",
            "The Beta posterior summary separates a point estimate from uncertainty. The target "
            "is a labelled synthetic teaching case; it does not establish a live casino probability.",
        ),
        _table("posterior_edge", "tables['posterior_edge'][['dataset', 'label', 'posterior_mean', 'credible_interval_lower', 'credible_interval_upper', 'break_even_probability', 'probability_positive_edge']]"),
        _markdown(
            "Robust Kelly Decisions",
            "Kelly is constrained expected-log-growth optimisation under an assumed edge, odds, "
            "and repeated-trial model. Fair roulette has zero Kelly. The lower posterior-quantile "
            "version is explicitly a conservative heuristic, not a guaranteed or universal optimum.",
        ),
        _table("posterior_edge", "tables['posterior_edge'][['plugin_kelly', 'quantile_probability', 'quantile_kelly', 'quantile_kelly_interpretation']]"),
        _markdown(
            "CVaR Risk Frontier",
            "The frontier uses common random numbers to compare stake fractions. CVaR is the mean "
            "of the worst non-negative terminal shortfalls `max(initial bankroll - terminal equity, 0)` "
            "at the recorded tail probability, so larger values are worse.",
        ),
        _table("risk_frontier", "tables['risk_frontier'][['kelly_fraction_multiplier', 'expected_log_growth', 'probability_of_loss', 'expected_maximum_drawdown', 'terminal_cvar_shortfall', 'cvar_tail_probability']]"),
        _markdown(
            "Limitations",
            "The simulations are conditional on named synthetic scenarios, probabilities, seed, horizon, "
            "and table constraints. Fixed-horizon, post-selection, sequential, and change-point questions "
            "need different procedures. None of these outputs is gambling advice or a claim about a live wheel.",
        ),
    ]
    for index, cell in enumerate(notebook.cells, start=1):
        cell["id"] = f"roulette-v2-cell-{index:02d}"
    client = NotebookClient(notebook, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}})
    client.execute()
    for cell in notebook.cells:
        cell.metadata.pop("execution", None)
    notebook.metadata = nbformat.from_dict(
        {
            "kernelspec": {"display_name": "Python 3.12", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12", "mimetype": "text/x-python", "codemirror_mode": {"name": "ipython", "version": 3}, "pygments_lexer": "ipython3", "nbconvert_exporter": "python", "file_extension": ".py"},
        }
    )
    return notebook


def main() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    notebook = build_notebook()
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=TARGET.parent, suffix=".ipynb", delete=False) as temporary:
        nbformat.write(notebook, temporary)
        temporary_path = Path(temporary.name)
    temporary_path.replace(TARGET)


if __name__ == "__main__":
    main()
