"""Cross-check the mathematics and public artifacts for a release build."""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import re
import sys

import nbformat
import numpy as np
import pandas as pd
from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
sys.path.insert(0, str(ROOT / "src"))

from roulette_lab.wheels import WheelKind, make_fair_wheel  # noqa: E402


class VerificationError(RuntimeError):
    """Raised when a public artifact conflicts with the validated analysis."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def _read(path: Path, label: str) -> str:
    _require(path.is_file(), f"Missing {label}: {path.relative_to(path.parents[1])}")
    text = path.read_text(encoding="utf-8")
    _require(bool(text.strip()), f"Empty {label}")
    return text


def _table(root: Path, name: str) -> pd.DataFrame:
    path = root / "outputs" / "tables" / f"{name}.csv"
    _require(path.is_file(), f"Missing result table: {name}")
    table = pd.read_csv(path)
    _require(not table.empty, f"Empty result table: {name}")
    _require(not table.isna().any().any(), f"Missing values in result table: {name}")
    return table


def _unique(table: pd.DataFrame, column: str, value: str) -> pd.Series:
    rows = table.loc[table[column] == value]
    _require(len(rows) == 1, f"Expected one {column}={value} row")
    return rows.iloc[0]


def _close(actual: float, expected: float, tolerance: float, label: str) -> None:
    _require(
        math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance),
        f"{label} mismatch: expected {expected:.12g}, found {float(actual):.12g}",
    )


def _count_report_prose(text: str) -> int:
    kept: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or line.startswith("#") or line.startswith("|") or line.startswith("!["):
            continue
        kept.append(line)
    return len(
        re.findall(
            r"[A-Za-z]+(?:['-][A-Za-z]+)*|[0-9]+(?:\.[0-9]+)?%?",
            "\n".join(kept),
        )
    )


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    _require(match is not None, f"Missing section: {heading}")
    return match.group("body")


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*|[0-9]+(?:\.[0-9]+)?%?", text))


def _verify_wheels() -> None:
    for kind, count in ((WheelKind.EUROPEAN, 37), (WheelKind.AMERICAN, 38)):
        wheel = make_fair_wheel(kind)
        _require(len(wheel.labels) == count, f"{kind.value} wheel pocket count mismatch")
        _close(np.sum(wheel.probabilities), 1.0, 1e-12, f"{kind.value} probability sum")
        _require(np.all(wheel.probabilities >= 0), f"{kind.value} has negative probability")


def _verify_tables(root: Path) -> dict[str, pd.DataFrame]:
    names = (
        "house_edges",
        "lln_convergence",
        "bias_tests",
        "observed_residuals",
        "detection_power",
        "kelly_sensitivity",
        "strategy_risk",
        "sequential_evidence",
        "change_point_results",
        "posterior_edge",
        "risk_frontier",
    )
    tables = {name: _table(root, name) for name in names}
    actual_names = {path.stem for path in (root / "outputs" / "tables").glob("*.csv")}
    _require(actual_names == set(names), f"Expected eleven named result tables, found {sorted(actual_names)}")
    _verify_v2_table_schemas(tables)
    _verify_numeric_table_values(tables)
    edges = tables["house_edges"]
    expected_edges = {
        "european": 1 / 37,
        "american": 2 / 38,
        "european_standard": 1 / 37,
        "la_partage": 1 / 74,
        "en_prison": 1 / 74,
    }
    labels = {
        "european": "European house edge",
        "american": "American house edge",
        "european_standard": "European even-money house edge",
        "la_partage": "La Partage house edge",
        "en_prison": "En Prison house edge",
    }
    for rule, expected in expected_edges.items():
        row = _unique(edges, "rule", rule)
        _close(row["house_edge"], expected, 1e-12, labels[rule])
        _close(row["expected_net_return"], -expected, 1e-12, f"{rule} expected return")
    _require(
        float(_unique(edges, "rule", "european")["expected_net_return"]) <= 0.0,
        "A fair European wheel must not report a positive player edge",
    )

    lln = tables["lln_convergence"]
    final = lln.sort_values("spin").iloc[-1]
    _close(final["theoretical_probability"], 1 / 37, 1e-12, "LLN target probability")
    _require(
        abs(float(final["empirical_probability"]) - 1 / 37) < 0.01,
        "LLN simulation is outside its publication tolerance",
    )

    bias = tables["bias_tests"]
    for dataset in ("unbiased", "biased"):
        row = _unique(bias, "dataset", dataset)
        for column in (
            "asymptotic_p_value",
            "monte_carlo_global_p_value",
            "naive_p_value",
            "bonferroni_p_value",
            "familywise_p_value",
        ):
            _require(0 <= float(row[column]) <= 1, f"Invalid {dataset} {column}")
        _require(
            float(row["familywise_p_value"]) >= float(row["naive_p_value"]),
            f"Selection adjustment ordering failed for {dataset}",
        )
        _require(
            float(row["bonferroni_p_value"]) >= float(row["naive_p_value"]),
            f"Bonferroni ordering failed for {dataset}",
        )
        _require(
            abs(float(row["asymptotic_p_value"]) - float(row["monte_carlo_global_p_value"]))
            < 0.02,
            f"Analytical and simulation p-values disagree for {dataset}",
        )
    _require(float(_unique(bias, "dataset", "unbiased")["asymptotic_p_value"]) > 0.05,
             "Unbiased teaching sample should not reject fairness")
    _require(float(_unique(bias, "dataset", "biased")["asymptotic_p_value"]) < 0.05,
             "Biased teaching sample should reject fairness")

    power = tables["detection_power"]
    _require(power["estimated_power"].between(0, 1).all(), "Power estimate outside [0, 1]")
    _require(
        power.sort_values("pocket_probability")["estimated_power"].is_monotonic_increasing,
        "Published detection power is not monotone",
    )

    risk = tables["strategy_risk"]
    for column in ("probability_of_loss", "probability_of_ruin", "expected_maximum_drawdown"):
        _require(risk[column].between(0, 1).all(), f"Invalid strategy risk column: {column}")
    return tables


def _verify_v2_table_schemas(tables: dict[str, pd.DataFrame]) -> None:
    required_columns = {
        "sequential_evidence": {
            "scenario", "spin", "target_hit", "e_value", "e_value_threshold",
            "fixed_horizon_p_value", "null_probability", "alternative_probability",
            "alpha", "seed", "evidence_contract",
        },
        "change_point_results": {
            "scenario", "spin", "target_hit", "cusum_score", "cusum_threshold",
            "null_probability", "alternative_probability", "seed", "showcase_paths",
            "monte_carlo_experiments", "monte_carlo_experiment_count",
            "true_change_spin", "first_alarm", "detection_delay", "false_alarm_rate",
            "median_detection_delay", "false_alarm_definition", "no_alarm_sentinel",
        },
        "posterior_edge": {
            "dataset", "label", "hits", "trials", "dataset_seed", "prior_alpha",
            "prior_beta", "posterior_mean", "credible_interval_lower",
            "credible_interval_upper", "break_even_probability", "probability_positive_edge",
            "plugin_kelly", "quantile_kelly", "quantile_kelly_interpretation",
            "posterior_lower_quantile",
        },
        "risk_frontier": {
            "kelly_fraction_multiplier", "strategy", "terminal_mean", "terminal_median",
            "probability_of_loss", "expected_maximum_drawdown", "expected_log_growth",
            "terminal_cvar_shortfall", "seed", "paths", "spins", "common_random_numbers",
            "expected_log_growth_convention",
        },
    }
    for name, required in required_columns.items():
        missing = required - set(tables[name].columns)
        _require(not missing, f"{name} schema is missing columns: {sorted(missing)}")

    sequential = tables["sequential_evidence"]
    _require(set(sequential["scenario"]) == {"fair_null"}, "Sequential evidence must use a fair_null path")
    _require(len(sequential) == 1_000, "Sequential evidence must contain 1,000 path rows")
    _require(
        sequential["spin"].tolist() == list(range(1, 1_001)),
        "Sequential evidence spins must run from 1 to 1,000",
    )
    _require(
        (sequential["alternative_probability"] > sequential["null_probability"]).all(),
        "Sequential evidence must retain its simple-null/simple-alternative ordering",
    )
    _require(
        (sequential["evidence_contract"] == "simple_null_vs_simple_alternative").all(),
        "Sequential evidence contract is not simple-null/simple-alternative",
    )

    change = tables["change_point_results"]
    _require(len(change) == 2_000, "Change-point results must contain both 1,000-spin paths")
    _require(set(change["scenario"]) == {"fair_null", "changed_at_500"}, "Change-point scenarios are incorrect")
    repeated = (
        "false_alarm_rate", "median_detection_delay", "monte_carlo_experiments",
        "monte_carlo_experiment_count", "true_change_spin", "first_alarm", "detection_delay",
    )
    for scenario, subset in change.groupby("scenario"):
        _require(len(subset) == 1_000, f"{scenario} must contain 1,000 per-spin rows")
        _require(subset["spin"].tolist() == list(range(1, 1_001)), f"{scenario} spin path is incomplete")
        _require(
            (subset[list(repeated)].nunique() == 1).all(),
            f"{scenario} must repeat scenario-level reliability fields on every path row",
        )
    _require(
        change.loc[change["scenario"] == "fair_null", "true_change_spin"].eq(0).all(),
        "Fair CUSUM path must have no true change",
    )
    _require(
        change.loc[change["scenario"] == "changed_at_500", "true_change_spin"].eq(500).all(),
        "Changed CUSUM path must record the true change at spin 500",
    )

    posterior = tables["posterior_edge"]
    _require(len(posterior) == 1, "Posterior edge table must have one teaching-sample row")
    _require(
        posterior["quantile_kelly_interpretation"].eq("heuristic_lower_posterior_quantile").all(),
        "Posterior quantile Kelly must be labelled heuristic",
    )

    frontier = tables["risk_frontier"]
    _require(
        frontier["kelly_fraction_multiplier"].tolist() == [0.25, 0.5, 1.0],
        "Risk frontier must contain ordered quarter, half, and full Kelly rows",
    )
    _require(frontier["common_random_numbers"].all(), "Risk frontier must use common random numbers")


def _verify_numeric_table_values(tables: dict[str, pd.DataFrame]) -> None:
    """Require finite numeric output except the documented -inf log-growth case."""

    for name, table in tables.items():
        numeric = table.select_dtypes(include=[np.number])
        for column in numeric:
            values = numeric[column].to_numpy(dtype=float)
            allowed_negative_infinity = (
                name == "risk_frontier"
                and column == "expected_log_growth"
                and np.isneginf(values)
            )
            valid = np.isfinite(values) | allowed_negative_infinity
            _require(valid.all(), f"Invalid numeric values in {name}.{column}")

    probability_columns = {
        "sequential_evidence": ("target_hit", "fixed_horizon_p_value", "null_probability", "alternative_probability", "alpha"),
        "change_point_results": ("target_hit", "null_probability", "alternative_probability", "false_alarm_rate"),
        "posterior_edge": (
            "posterior_mean", "credible_interval_lower", "credible_interval_upper",
            "break_even_probability", "probability_positive_edge", "plugin_kelly",
            "quantile_probability", "quantile_kelly", "posterior_lower_quantile",
        ),
        "risk_frontier": ("kelly_fraction_multiplier", "probability_of_loss", "expected_maximum_drawdown"),
    }
    for name, columns in probability_columns.items():
        for column in columns:
            _require(
                tables[name][column].between(0.0, 1.0).all(),
                f"Invalid probability bounds in {name}.{column}",
            )

    change = tables["change_point_results"]
    _require((change["cusum_score"] >= 0.0).all(), "CUSUM scores must be non-negative")
    _require((change["cusum_threshold"] > 0.0).all(), "CUSUM threshold must be positive")
    _require(change["first_alarm"].between(0, 1_000).all(), "Invalid first alarm spin")
    _require(
        ((change["detection_delay"] >= 0) | (change["detection_delay"] == -1)).all(),
        "Detection delay must be non-negative or use the explicit -1 no-alarm sentinel",
    )
    _require(
        (change["monte_carlo_experiments"] > 0).all(),
        "Change-point Monte Carlo experiment count must be positive",
    )
    _require(
        change["monte_carlo_experiments"].eq(change["monte_carlo_experiment_count"]).all(),
        "Change-point Monte Carlo experiment count columns disagree",
    )
    posterior = tables["posterior_edge"]
    _require(
        (posterior["credible_interval_lower"] <= posterior["credible_interval_upper"]).all(),
        "Posterior credible interval endpoints are out of order",
    )
    _require(
        (posterior["quantile_kelly"] <= posterior["plugin_kelly"]).all(),
        "Heuristic quantile Kelly must not exceed plug-in Kelly",
    )
    _require(
        (tables["risk_frontier"]["terminal_cvar_shortfall"] >= 0.0).all(),
        "Risk-frontier terminal CVaR shortfall must be non-negative",
    )


def _verify_public_text(root: Path, tables: dict[str, pd.DataFrame]) -> None:
    readme = _read(root / "README.md", "README")
    report = _read(root / "report" / "technical_report.md", "technical report")
    blog = _read(root / "docs" / "technical_blog.md", "technical blog")
    application = _read(root / "docs" / "application_materials.md", "application materials")
    _read(root / "docs" / "provenance.md", "provenance record")
    _read(root / "docs" / "ai_workflow.md", "AI workflow")
    _read(root / "docs" / "methodology_map.md", "methodology map")
    checklist = _read(root / "docs" / "deliverables_checklist.md", "deliverables checklist")
    visual_qa = _read(root / "docs" / "visual_qa.md", "visual QA record")

    report_words = _count_report_prose(report)
    _require(4_500 <= report_words <= 5_000, f"Technical report word count is {report_words}")
    ps_words = _word_count(_section(application, "Personal Statement Material"))
    _require(150 <= ps_words <= 200, f"Personal Statement word count is {ps_words}")

    for text, label in ((readme, "README"), (report, "report"), (blog, "technical blog")):
        _require("synthetic" in text.lower(), f"{label} does not label synthetic evidence")
        _require("not" in text.lower() and "profit" in text.lower(), f"{label} lacks profit disclaimer")
        _require("—" not in text, f"{label} contains an em dash")

    named_evidence = (
        "house_edges.csv",
        "bias_tests.csv",
        "sequential_evidence.csv",
        "change_point_results.csv",
        "posterior_edge.csv",
        "risk_frontier.csv",
    )
    for table in named_evidence:
        _require(
            f"](outputs/tables/{table})" in readme,
            f"README evidence reference missing: {table}",
        )
        _require(
            table in report,
            f"Report evidence reference missing: {table}",
        )

    manual_baseline_phrases = (
        "Existing seven tables and six figures remain.",
        "The final release contains eleven tables and ten figures.",
    )
    for phrase in manual_baseline_phrases:
        _require(phrase in readme, f"README baseline phrase mismatch: {phrase}")
        _require(phrase in checklist, f"Deliverables checklist baseline phrase mismatch: {phrase}")

    deployment_documents = (readme, application, checklist, visual_qa)
    deployment_url = "https://roulette-analytics-lab.streamlit.app/"
    for text in deployment_documents:
        _require(deployment_url in text, "Deployment target URL is missing")
        _require(
            "pending public-access verification" in text.lower(),
            "Unverified deployment status is not labelled pending",
        )
    forbidden_public_claims = (
        "open the live streamlit dashboard",
        "the public dashboard is available",
        "live interactive dashboard",
        "public streamlit url",
        "sharing settings identify the app as public and searchable",
    )
    combined = "\n".join(deployment_documents).lower()
    _require(
        not any(claim in combined for claim in forbidden_public_claims),
        "Unverified public deployment status is overstated",
    )


def _verify_notebook(root: Path) -> None:
    path = root / "notebooks" / "roulette_analytics.ipynb"
    _require(path.is_file(), "Missing executed notebook")
    notebook = nbformat.read(path, as_version=4)
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    _require(bool(code_cells), "Executed notebook has no code cells")
    _require(
        all(cell.get("execution_count") is not None for cell in code_cells),
        "The notebook is not fully executed",
    )
    _require(
        all(not output.get("ename") for cell in code_cells for output in cell.get("outputs", [])),
        "The notebook contains an execution error",
    )


def _verify_figures_and_pdf(root: Path) -> None:
    figures = sorted((root / "outputs" / "figures").glob("*.png"))
    expected = {
        "01_wheel_layout.png",
        "02_house_edge_comparison.png",
        "03_lln_convergence.png",
        "04_bias_residuals.png",
        "05_detection_power.png",
        "06_bankroll_risk.png",
        "07_sequential_evidence.png",
        "08_change_point_cusum.png",
        "09_posterior_edge.png",
        "10_risk_frontier.png",
    }
    _require(
        {path.name for path in figures} == expected,
        f"Expected ten named publication figures, found {[path.name for path in figures]}",
    )
    for path in figures:
        with Image.open(path) as image:
            width, height = image.size
            extrema = image.convert("RGB").getextrema()
        _require(width >= 1_000 and height >= 700, f"Figure dimensions too small: {path.name}")
        _require(any(low < high for low, high in extrema), f"Figure is blank: {path.name}")
    pdf = root / "report" / "technical_report.pdf"
    _require(pdf.is_file() and pdf.stat().st_size > 50_000, "Missing or undersized report PDF")
    reader = PdfReader(pdf)
    _require(13 <= len(reader.pages) <= 16, f"Report PDF has {len(reader.pages)} pages")
    _require(
        "Probability Contract" in reader.pages[3].extract_text(),
        "Probability Contract is missing from PDF page 4",
    )


def verify_artifacts(root: Path) -> None:
    """Raise VerificationError unless every release-facing artifact agrees."""

    root = Path(root).resolve()
    _verify_wheels()
    tables = _verify_tables(root)
    _verify_public_text(root, tables)
    _verify_notebook(root)
    _verify_figures_and_pdf(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        verify_artifacts(args.root)
    except VerificationError as error:
        print(f"VERIFICATION FAILED: {error}", file=sys.stderr)
        return 1
    print("Artifact verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
