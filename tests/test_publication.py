from pathlib import Path
import re

from PIL import Image
import pandas as pd
from pypdf import PdfReader
from reportlab.platypus import KeepTogether, PageBreak, Paragraph

from scripts.build_report_pdf import (
    _styles,
    load_headline_results,
    markdown_story,
    resolve_csv_markers,
)


ROOT = Path(__file__).resolve().parents[1]


def count_report_prose(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    kept = []
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or line.startswith("#") or line.startswith("|") or line.startswith("!["):
            continue
        kept.append(line)
    return len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*|[0-9]+(?:\.[0-9]+)?%?", "\n".join(kept)))


def extract_named_section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, f"Missing section: {heading}"
    return match.group("body")


def count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*|[0-9]+(?:\.[0-9]+)?%?", text))


def test_report_prose_word_count_is_in_v2_range():
    assert 4_500 <= count_report_prose(ROOT / "report/technical_report.md") <= 5_000


def test_report_has_v2_research_sections_in_order():
    text = (ROOT / "report/technical_report.md").read_text(encoding="utf-8")
    headings = [
        "Executive Summary",
        "Research Question and Provenance",
        "Probability Contract",
        "Fixed-Horizon Inference",
        "Sequential Evidence",
        "Change-Point Diagnostics",
        "Posterior Decisions",
        "Risk Frontier",
        "Software and Product Design",
        "Application Value",
        "Limitations",
        "Conclusion",
        "References",
    ]
    positions = [text.index(f"## {heading}") for heading in headings]
    assert positions == sorted(positions)


def test_report_headline_evidence_names_generated_csv_tables():
    report = (ROOT / "report/technical_report.md").read_text(encoding="utf-8")
    for table in [
        "house_edges.csv",
        "bias_tests.csv",
        "sequential_evidence.csv",
        "change_point_results.csv",
        "posterior_edge.csv",
        "risk_frontier.csv",
    ]:
        assert table in report


def test_report_describes_the_generated_sequential_scenarios_accurately():
    sequential = pd.read_csv(ROOT / "outputs/tables/sequential_evidence.csv")
    assert sequential["scenario"].unique().tolist() == ["fair_null"]

    section = extract_named_section(ROOT / "report/technical_report.md", "Sequential Evidence")
    assert "contains only the generated fair-null example" in section
    assert "changed scenario shows the same evidence process" not in section.lower()

    change_section = extract_named_section(
        ROOT / "report/technical_report.md", "Change-Point Diagnostics"
    )
    assert "`change_point_results.csv` contains two generated scenarios" in change_section


def test_table_one_names_the_exact_source_for_every_metric():
    assert [result.source for result in load_headline_results()] == [
        "house_edges.csv | rule=european | house_edge",
        "house_edges.csv | rule=american | house_edge",
        "bias_tests.csv | dataset=unbiased | familywise_p_value",
        "bias_tests.csv | dataset=biased | monte_carlo_global_p_value",
        "strategy_risk.csv | strategy=martingale | probability_of_loss",
        "strategy_risk.csv | strategy=quarter_kelly | probability_of_loss",
    ]


def test_report_explains_the_two_quarter_kelly_samples_without_overclaiming():
    section = extract_named_section(ROOT / "report/technical_report.md", "Risk Frontier")
    for table in ("strategy_risk.csv", "risk_frontier.csv"):
        assert table in section
    for marker in (
        "{{strategy_risk.csv|strategy=quarter_kelly|probability_of_loss|.2%}}",
        "{{risk_frontier.csv|kelly_fraction_multiplier=0.25|probability_of_loss|.2%}}",
        "{{strategy_risk.csv|strategy=quarter_kelly|seed|.0f}}",
        "{{risk_frontier.csv|kelly_fraction_multiplier=0.25|seed|.0f}}",
    ):
        assert marker in section
    assert "Both use the same 3,000 paths and 300-spin horizon" in section
    assert "separate Monte Carlo samples" in section


def test_report_figure_numbers_are_unique_monotone_and_captions_match_plots():
    report = (ROOT / "report/technical_report.md").read_text(encoding="utf-8")
    figures = re.findall(r"^!\[Figure (\d+)\. ([^]]+)]\(([^)]+)\)$", report, re.MULTILINE)
    assert [int(number) for number, _, _ in figures] == list(range(1, len(figures) + 1))
    assert [path for _, _, path in figures] == [
        "../outputs/figures/01_wheel_layout.png",
        "../outputs/figures/03_lln_convergence.png",
        "../outputs/figures/02_house_edge_comparison.png",
        "../outputs/figures/05_detection_power.png",
        "../outputs/figures/04_bias_residuals.png",
        "../outputs/figures/07_sequential_evidence.png",
        "../outputs/figures/08_change_point_cusum.png",
        "../outputs/figures/09_posterior_edge.png",
        "../outputs/figures/10_risk_frontier.png",
    ]
    assert figures[-1][1] == (
        "Expected log growth by Kelly fraction multiplier under common random outcomes."
    )


def test_personal_statement_material_is_in_range():
    section = extract_named_section(
        ROOT / "docs/application_materials.md", "Personal Statement Material"
    )
    assert 150 <= count_words(section) <= 200


def test_readme_contains_manual_requirements():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for phrase in [
        "Kelly",
        "chi-squared",
        "random walk",
        "Streamlit",
        "Reproducibility",
        "AI use",
        "Group 40",
    ]:
        assert phrase.lower() in readme.lower()
    for heading in [
        "Project background",
        "Architecture",
        "Installation",
        "Published results",
        "Responsible gambling",
        "Citation",
    ]:
        assert f"## {heading}" in readme


def test_canonical_deployment_is_linked_and_verified_public():
    live_url = "https://roulette-analytics-lab.streamlit.app/"
    for relative in [
        "README.md",
        "docs/application_materials.md",
        "docs/deliverables_checklist.md",
        "docs/visual_qa.md",
    ]:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert live_url in text, f"Missing deployment target URL in {relative}"
        assert "verified public" in text.lower(), relative
        assert "fresh anonymous cookie jar" in text.lower(), relative
        assert "http 200" in text.lower(), relative
        assert "pending public-access verification" not in text.lower(), relative

    checklist = (ROOT / "docs/deliverables_checklist.md").read_text(encoding="utf-8")
    assert "| Online demonstration |" in checklist
    assert "Verified public deployment" in checklist


def test_provenance_credits_every_author_and_records_source_checksum():
    text = (ROOT / "docs/provenance.md").read_text(encoding="utf-8")
    for author in [
        "Jialiang Gong",
        "Joseph Myatt",
        "Jessica Sathiyanathan",
        "Jacob Tinker",
        "Chenyue Wang",
    ]:
        assert author in text
    assert "0364398a2cdcc91b1653604a9ca1b7adfaac529d99bc8e115f53475fa49c40e5" in text
    assert "independent Python reimplementation" in text


def test_blog_and_application_materials_cover_required_content():
    blog = (ROOT / "docs/technical_blog.md").read_text(encoding="utf-8").lower()
    for phrase in ["negative drift", "post-selection", "probability uncertainty"]:
        assert phrase in blog
    application = (ROOT / "docs/application_materials.md").read_text(encoding="utf-8")
    for heading in [
        "CV Bullets",
        "Personal Statement Material",
        "Two-Minute Interview Answer",
        "Technical Walkthrough",
        "Personal Contribution Answer",
        "CityU DTT Mapping",
        "PolyU KTM Mapping",
        "HKUST BDT Mapping",
    ]:
        assert f"## {heading}" in application


def test_pdf_and_manual_facing_docs_exist():
    pdf = ROOT / "report/technical_report.pdf"
    assert pdf.exists() and pdf.stat().st_size > 50_000
    for path in [
        ROOT / "docs/ai_workflow.md",
        ROOT / "docs/deliverables_checklist.md",
        ROOT / "docs/methodology_map.md",
    ]:
        assert path.exists() and path.stat().st_size > 500


def _pdf_body_lines(page, page_number: int) -> list[str]:
    ignored = {
        "Roulette Analytics Lab | Jialiang Gong",
        f"Page {page_number}",
        "Roulette Analytics Lab V2 | Research report",
    }
    return [
        line.strip()
        for line in page.extract_text().splitlines()
        if line.strip() and line.strip() not in ignored
    ]


def _source_block_starts() -> tuple[str, ...]:
    starts = ["European edge"]
    for line in (ROOT / "report/technical_report.md").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            starts.append(stripped[3:])
        elif stripped.startswith("![Figure "):
            starts.append(stripped[2:].split("]", 1)[0])
        elif stripped and not stripped.startswith(("#", "```", "|")):
            plain = re.sub(r"[`*_]", "", stripped)
            starts.append(plain[:45])
    return tuple(starts)


def test_pdf_is_a4_in_range_and_starts_pages_with_complete_source_blocks():
    reader = PdfReader(ROOT / "report/technical_report.pdf")
    assert 13 <= len(reader.pages) <= 16
    assert "Probability Contract" in reader.pages[3].extract_text()

    starts = _source_block_starts()
    for page_number, page in enumerate(reader.pages[1:], start=2):
        body = _pdf_body_lines(page, page_number)
        assert body, f"Page {page_number} is blank"
        first = body[0]
        assert any(start.startswith(first[: min(25, len(first))]) for start in starts), (
            page_number,
            first,
        )


def test_pdf_story_keeps_headings_with_content_and_only_breaks_after_cover():
    styles = _styles()
    assert styles["h2"].keepWithNext
    source = resolve_csv_markers(
        (ROOT / "report/technical_report.md").read_text(encoding="utf-8")
    )
    story = markdown_story(source, styles)
    assert sum(isinstance(flowable, PageBreak) for flowable in story) == 1
    probability = next(
        index
        for index, flowable in enumerate(story)
        if isinstance(flowable, Paragraph) and flowable.getPlainText() == "Probability Contract"
    )
    first_content = story[probability + 1]
    assert isinstance(first_content, KeepTogether)
    assert first_content._content[0].getPlainText().startswith("The first contract is exact.")


def test_targeted_publication_files_contain_no_em_dash():
    for relative in [
        "README.md",
        "report/technical_report.md",
        "docs/technical_blog.md",
        "docs/application_materials.md",
    ]:
        assert "—" not in (ROOT / relative).read_text(encoding="utf-8")


def test_release_visual_evidence_has_expected_dimensions_and_scope():
    expected = {
        "dashboard-desktop.png": (1440, 1000),
        "dashboard-mobile.png": (390, 844),
    }
    for filename, dimensions in expected.items():
        with Image.open(ROOT / "docs" / "assets" / filename) as screenshot:
            assert screenshot.format == "PNG"
            assert screenshot.size == dimensions

    record = (ROOT / "docs" / "visual_qa.md").read_text(encoding="utf-8")
    for phrase in [
        "Live Experiment",
        "Evidence",
        "Decision Risk",
        "Wheel Mechanics",
        "Methods",
        "390x844",
        "14 pages",
        "console",
    ]:
        assert phrase in record
