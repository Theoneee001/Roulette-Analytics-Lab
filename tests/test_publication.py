from pathlib import Path
import re

from PIL import Image


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


def test_public_dashboard_is_linked_across_release_documents():
    live_url = "https://roulette-analytics-lab.streamlit.app/"
    for relative in [
        "README.md",
        "docs/deliverables_checklist.md",
        "docs/visual_qa.md",
    ]:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert live_url in text, f"Missing public dashboard URL in {relative}"

    checklist = (ROOT / "docs/deliverables_checklist.md").read_text(encoding="utf-8")
    assert "| Online demonstration |" in checklist
    assert "Post-acceptance only" not in checklist


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
        "Wheel & Bets",
        "Fairness Lab",
        "Bankroll Simulator",
        "Methods & Limits",
        "390x844",
        "11 pages",
        "WebSocket",
    ]:
        assert phrase in record
