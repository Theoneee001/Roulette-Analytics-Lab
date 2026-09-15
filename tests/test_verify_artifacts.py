from pathlib import Path
import shutil
import sys

import pandas as pd
import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_artifacts import VerificationError, verify_artifacts


def copy_artifacts(tmp_path: Path) -> Path:
    destination = tmp_path / "project"
    shutil.copytree(
        ROOT,
        destination,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".worktrees",
            "__pycache__",
            ".pytest_cache",
            ".matplotlib",
            ".ipython",
        ),
    )
    return destination


def replace_csv_value(
    root: Path, relative: str, key_column: str, key: str, column: str, value
) -> None:
    path = root / relative
    table = pd.read_csv(path)
    selected = table[key_column] == key
    assert selected.sum() == 1
    table.loc[selected, column] = value
    table.to_csv(path, index=False, lineterminator="\n")


def test_verifier_accepts_current_publication():
    verify_artifacts(ROOT)


def test_verifier_rejects_an_incorrect_house_edge(tmp_path):
    copied = copy_artifacts(tmp_path)
    replace_csv_value(
        copied,
        "outputs/tables/house_edges.csv",
        "rule",
        "european",
        "house_edge",
        0.0,
    )
    with pytest.raises(VerificationError, match="European house edge"):
        verify_artifacts(copied)


def test_verifier_rejects_missing_manual_evidence(tmp_path):
    copied = copy_artifacts(tmp_path)
    (copied / "docs/technical_blog.md").unlink()
    with pytest.raises(VerificationError, match="technical blog"):
        verify_artifacts(copied)


def test_verifier_requires_the_v2_change_point_table(tmp_path):
    copied = copy_artifacts(tmp_path)
    (copied / "outputs/tables/change_point_results.csv").unlink()

    with pytest.raises(VerificationError, match="change_point_results"):
        verify_artifacts(copied)


def test_verifier_enforces_manual_baseline_phrases(tmp_path):
    copied = copy_artifacts(tmp_path)
    readme = copied / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "Existing seven tables and six figures remain.", "Baseline totals removed."
        ),
        encoding="utf-8",
    )

    with pytest.raises(VerificationError, match="baseline phrase"):
        verify_artifacts(copied)


def test_verifier_rejects_unverified_public_dashboard_wording(tmp_path):
    copied = copy_artifacts(tmp_path)
    readme = copied / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "Streamlit deployment target, pending public-access verification in Task 7",
            "Open the live Streamlit dashboard",
        ),
        encoding="utf-8",
    )

    with pytest.raises(VerificationError, match="deployment status"):
        verify_artifacts(copied)


def test_verifier_allows_negative_infinite_expected_log_growth(tmp_path):
    copied = copy_artifacts(tmp_path)
    path = copied / "outputs/tables/risk_frontier.csv"
    table = pd.read_csv(path)
    table.loc[0, "expected_log_growth"] = float("-inf")
    table.to_csv(path, index=False, lineterminator="\n")

    verify_artifacts(copied)


def test_verifier_rejects_positive_infinite_expected_log_growth(tmp_path):
    copied = copy_artifacts(tmp_path)
    path = copied / "outputs/tables/risk_frontier.csv"
    table = pd.read_csv(path)
    table.loc[0, "expected_log_growth"] = float("inf")
    table.to_csv(path, index=False, lineterminator="\n")

    with pytest.raises(VerificationError, match="expected_log_growth"):
        verify_artifacts(copied)


def test_verifier_rejects_blank_v2_figure(tmp_path):
    copied = copy_artifacts(tmp_path)
    image_path = copied / "outputs/figures/10_risk_frontier.png"
    Image.new("RGB", (1_800, 1_080), "white").save(image_path)

    with pytest.raises(VerificationError, match="blank"):
        verify_artifacts(copied)


def test_verifier_rejects_unexecuted_notebook(tmp_path):
    copied = copy_artifacts(tmp_path)
    notebook_path = copied / "notebooks/roulette_analytics.ipynb"
    text = notebook_path.read_text(encoding="utf-8")
    text = text.replace('"execution_count": 1', '"execution_count": null', 1)
    notebook_path.write_text(text, encoding="utf-8")
    with pytest.raises(VerificationError, match="notebook"):
        verify_artifacts(copied)


def test_verifier_rejects_missing_named_public_evidence(tmp_path):
    copied = copy_artifacts(tmp_path)
    readme = copied / "README.md"
    text = readme.read_text(encoding="utf-8").replace(
        "house_edges.csv", "incorrect_house_edges.csv"
    )
    readme.write_text(text, encoding="utf-8")
    with pytest.raises(VerificationError, match="evidence reference"):
        verify_artifacts(copied)


def test_ci_runs_the_complete_reproducibility_gate():
    workflow = (ROOT / ".github/workflows/reproducibility.yml").read_text(encoding="utf-8")
    for command in (
        "python -m pytest -q",
        "python scripts/run_analysis.py",
        "python scripts/build_notebook.py",
        "python scripts/build_report_pdf.py",
        "python scripts/verify_artifacts.py",
        "git diff --exit-code",
    ):
        assert command in workflow
    assert "python-version: '3.12'" in workflow
