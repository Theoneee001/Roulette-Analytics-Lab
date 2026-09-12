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
    )
    tables = {name: _table(root, name) for name in names}
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


def _verify_public_text(root: Path, tables: dict[str, pd.DataFrame]) -> None:
    readme = _read(root / "README.md", "README")
    report = _read(root / "report" / "technical_report.md", "technical report")
    blog = _read(root / "docs" / "technical_blog.md", "technical blog")
    application = _read(root / "docs" / "application_materials.md", "application materials")
    _read(root / "docs" / "provenance.md", "provenance record")
    _read(root / "docs" / "ai_workflow.md", "AI workflow")
    _read(root / "docs" / "methodology_map.md", "methodology map")
    _read(root / "docs" / "deliverables_checklist.md", "deliverables checklist")

    report_words = _count_report_prose(report)
    _require(3_000 <= report_words <= 5_000, f"Technical report word count is {report_words}")
    ps_words = _word_count(_section(application, "Personal Statement Material"))
    _require(150 <= ps_words <= 200, f"Personal Statement word count is {ps_words}")

    for text, label in ((readme, "README"), (report, "report"), (blog, "technical blog")):
        _require("synthetic" in text.lower(), f"{label} does not label synthetic evidence")
        _require("not" in text.lower() and "profit" in text.lower(), f"{label} lacks profit disclaimer")
        _require("—" not in text, f"{label} contains an em dash")

    edges = tables["house_edges"]
    european = float(_unique(edges, "rule", "european")["house_edge"])
    american = float(_unique(edges, "rule", "american")["house_edge"])
    fair = _unique(tables["bias_tests"], "dataset", "unbiased")
    biased = _unique(tables["bias_tests"], "dataset", "biased")
    required_readme = (
        f"{european:.2%} on a European wheel",
        f"{american:.2%} on an American wheel",
        f"`p = {float(fair['naive_p_value']):.4f}`",
        f"`p = {float(fair['familywise_p_value']):.4f}`",
        f"`p = {float(biased['asymptotic_p_value']):.4f}`",
    )
    for headline in required_readme:
        _require(headline in readme, f"README headline mismatch: {headline}")

    required_report = (
        f"approximately {european:.2%}",
        f"approximately {american:.2%}",
        f"`p = {float(fair['naive_p_value']):.4f}`",
        f"`p = {float(fair['familywise_p_value']):.4f}`",
        f"`p = {float(biased['monte_carlo_global_p_value']):.4f}`",
    )
    for headline in required_report:
        _require(headline in report, f"Report headline mismatch: {headline}")


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
    _require(len(figures) == 6, f"Expected six publication figures, found {len(figures)}")
    for path in figures:
        with Image.open(path) as image:
            width, height = image.size
        _require(width >= 1_000 and height >= 700, f"Figure dimensions too small: {path.name}")
    pdf = root / "report" / "technical_report.pdf"
    _require(pdf.is_file() and pdf.stat().st_size > 50_000, "Missing or undersized report PDF")


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
