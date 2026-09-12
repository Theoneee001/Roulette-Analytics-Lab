from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[1]


def test_notebook_is_executed_and_contains_required_sections():
    notebook = nbformat.read(ROOT / "notebooks/roulette_analytics.ipynb", as_version=4)
    headings = "\n".join(
        cell.source for cell in notebook.cells if cell.cell_type == "markdown"
    )

    for title in [
        "House Edge",
        "Law of Large Numbers",
        "Bias Detection",
        "Kelly Criterion",
        "Bankroll Risk",
        "Limitations",
    ]:
        assert title in headings
    assert all(
        cell.get("execution_count") is not None
        for cell in notebook.cells
        if cell.cell_type == "code"
    )


def test_notebook_calls_shared_analysis_instead_of_reimplementing_formulas():
    notebook = nbformat.read(ROOT / "notebooks/roulette_analytics.ipynb", as_version=4)
    code = "\n".join(cell.source for cell in notebook.cells if cell.cell_type == "code")

    assert "run_full_analysis" in code
    assert "expected_net_return" in code
    assert "max_count_test" in code
    assert "def expected" not in code
    assert "def kelly" not in code


def test_methodology_map_has_traceability_columns_and_two_source_corrections():
    text = (ROOT / "docs/methodology_map.md").read_text(encoding="utf-8")

    for heading in [
        "Concept",
        "Equation",
        "Python interface",
        "Test",
        "Figure",
        "Interpretation",
    ]:
        assert heading in text
    assert "-w/37" in text
    assert "selected after observing" in text
    assert "source report" in text.lower()


def test_notebook_metadata_is_stable_and_contains_no_execution_timing():
    notebook = nbformat.read(ROOT / "notebooks/roulette_analytics.ipynb", as_version=4)

    assert notebook.metadata.kernelspec.name == "python3"
    assert notebook.metadata.language_info.version == "3.12"
    assert all("execution" not in cell.metadata for cell in notebook.cells)

