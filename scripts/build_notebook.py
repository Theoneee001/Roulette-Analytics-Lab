"""Build and execute the deterministic portfolio notebook."""

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


def build_notebook():
    notebook = nbformat.v4.new_notebook(
        metadata={
            "kernelspec": {
                "display_name": "Python 3.12",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.12",
                "mimetype": "text/x-python",
                "codemirror_mode": {"name": "ipython", "version": 3},
                "pygments_lexer": "ipython3",
                "nbconvert_exporter": "python",
                "file_extension": ".py",
            },
        }
    )
    notebook.cells = [
        nbformat.v4.new_markdown_cell(
            """# Roulette Analytics Lab

An independent Python reimplementation and extension of the mathematical specification in the MATH20062 Group 40 roulette report. The notebook uses the same tested domain functions as the dashboard and published tables."""
        ),
        nbformat.v4.new_code_cell(
            """from pathlib import Path
import sys
import pandas as pd

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "src"))

from roulette_lab.analysis import AnalysisConfig, run_full_analysis
from roulette_lab.bets import expected_net_return
from roulette_lab.statistics import max_count_test

pd.options.display.float_format = "{:.6f}".format
print("Python 3.12 | shared package interfaces loaded")"""
        ),
        nbformat.v4.new_code_cell(
            """config = AnalysisConfig.fast_test()
bundle = run_full_analysis(config)
print(f"Seed: {config.seed}; tables: {len(bundle.table_names())}")"""
        ),
        nbformat.v4.new_markdown_cell(
            r"""## House Edge

For a stake of one unit, exact expected net return is $E[X]=pb-(1-p)$. The typed bet fixes the casino payout. A fair European straight-up bet therefore returns $-1/37$ in expectation, rather than zero."""
        ),
        nbformat.v4.new_code_cell(
            "bundle.house_edges[[\"rule\", \"bet\", \"expected_net_return\", \"house_edge\"]]"
        ),
        nbformat.v4.new_markdown_cell(
            r"""## Law of Large Numbers

The cumulative frequency of pocket 17 fluctuates at small samples and approaches the model probability as the number of spins grows."""
        ),
        nbformat.v4.new_code_cell(
            "bundle.lln_convergence.iloc[[0, 9, 99, -1]][[\"spin\", \"empirical_probability\", \"theoretical_probability\", \"absolute_error\"]]"
        ),
        nbformat.v4.new_markdown_cell(
            """## Bias Detection

A global Pearson test asks whether the whole wheel departs from fairness. The maximum-count test then corrects for choosing the hottest pocket after seeing the same data. The family-wise value is the relevant measure for that selected claim."""
        ),
        nbformat.v4.new_code_cell(
            "bundle.bias_tests[[\"dataset\", \"hottest_label\", \"asymptotic_p_value\", \"monte_carlo_global_p_value\", \"naive_p_value\", \"bonferroni_p_value\", \"familywise_p_value\"]]"
        ),
        nbformat.v4.new_markdown_cell(
            r"""## Kelly Criterion

For net odds $b$ and estimated win probability $p$, full Kelly is $f^* = \max(0,(bp-(1-p))/b)$. A straight-up 35:1 bet needs $p>1/36$ for a positive allocation. Fractional Kelly reduces model and path risk but does not create an edge."""
        ),
        nbformat.v4.new_code_cell(
            "bundle.kelly_sensitivity.loc[bundle.kelly_sensitivity[\"pocket_probability\"].between(1/37, 0.04)].head(8)"
        ),
        nbformat.v4.new_markdown_cell(
            """## Bankroll Risk

Terminal averages alone hide dispersion. The comparison reports medians, simulation intervals, loss probability, ruin probability and maximum drawdown under one declared biased-wheel scenario with table constraints."""
        ),
        nbformat.v4.new_code_cell(
            "bundle.strategy_risk[[\"strategy\", \"terminal_mean\", \"terminal_median\", \"probability_of_loss\", \"probability_of_ruin\", \"expected_maximum_drawdown\"]]"
        ),
        nbformat.v4.new_markdown_cell(
            """## Limitations

- The biased CSV is synthetic and demonstrates workflow, not a claim about a live casino wheel.
- Bias selection and evaluation should use disjoint samples.
- Chi-square asymptotics require adequate expected counts; the project also reports a multinomial Monte Carlo result.
- Kelly is conditional log-growth optimisation under a correct probability and payout model. It is not guaranteed profit.
- Finite simulation summaries carry Monte Carlo error and depend on stop rules, table limits and the random seed."""
        ),
    ]
    for index, cell in enumerate(notebook.cells, start=1):
        cell["id"] = f"roulette-cell-{index:02d}"
    client = NotebookClient(
        notebook,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    )
    client.execute()
    for cell in notebook.cells:
        cell.metadata.pop("execution", None)
    notebook.metadata = nbformat.from_dict(
        {
            "kernelspec": {
                "display_name": "Python 3.12",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.12",
                "mimetype": "text/x-python",
                "codemirror_mode": {"name": "ipython", "version": 3},
                "pygments_lexer": "ipython3",
                "nbconvert_exporter": "python",
                "file_extension": ".py",
            },
        }
    )
    return notebook


def main() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    notebook = build_notebook()
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=TARGET.parent, suffix=".ipynb", delete=False
    ) as temporary:
        nbformat.write(notebook, temporary)
        temporary_path = Path(temporary.name)
    temporary_path.replace(TARGET)


if __name__ == "__main__":
    main()
