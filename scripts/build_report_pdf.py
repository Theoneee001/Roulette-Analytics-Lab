"""Build the deterministic A4 technical report from Markdown and CSV outputs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from html import escape
from pathlib import Path
import re
import sys

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    CondPageBreak,
    HRFlowable,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "report" / "technical_report.md"
TARGET = ROOT / "report" / "technical_report.pdf"
GREEN = colors.HexColor("#24342F")
RED = colors.HexColor("#A33C35")
GOLD = colors.HexColor("#B78A3E")
INK = colors.HexColor("#26332F")
MUTED = colors.HexColor("#5C6964")
PAPER = colors.HexColor("#FAF8F2")


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


_MARKER = re.compile(
    r"\{\{(?P<table>[a-z_]+\.csv)\|(?P<filter>[a-z_]+=[^|]+)\|(?P<column>[a-z_]+)\|(?P<format>[^}]+)\}\}"
)


def resolve_csv_markers(text: str) -> str:
    """Resolve report headline markers from named generated CSV evidence."""

    def replace(match: re.Match[str]) -> str:
        table = ROOT / "outputs" / "tables" / match.group("table")
        field, expected = match.group("filter").split("=", 1)
        rows = _rows(table)
        selected = [row for row in rows if row.get(field) == expected]
        values = {row[match.group("column")] for row in selected}
        if len(values) != 1:
            raise ValueError(
                f"Expected one evidence value for {match.group(0)}, found {len(values)}."
            )
        return format(float(values.pop()), match.group("format"))

    return _MARKER.sub(replace, text)


@dataclass(frozen=True, slots=True)
class HeadlineResult:
    label: str
    value: str
    source: str


def load_headline_results() -> list[HeadlineResult]:
    """Load report headline values from generated machine-readable outputs."""

    edges = _rows(ROOT / "outputs" / "tables" / "house_edges.csv")
    tests = _rows(ROOT / "outputs" / "tables" / "bias_tests.csv")
    risk = _rows(ROOT / "outputs" / "tables" / "strategy_risk.csv")

    edge_by_rule = {row["rule"]: float(row["house_edge"]) for row in edges}
    test_by_dataset = {row["dataset"]: row for row in tests}
    risk_by_strategy = {row["strategy"]: row for row in risk}

    return [
        HeadlineResult(
            "European edge",
            f"{edge_by_rule['european']:.2%}",
            "house_edges.csv | rule=european | house_edge",
        ),
        HeadlineResult(
            "American edge",
            f"{edge_by_rule['american']:.2%}",
            "house_edges.csv | rule=american | house_edge",
        ),
        HeadlineResult(
            "Fair sample corrected p",
            f"{float(test_by_dataset['unbiased']['familywise_p_value']):.4f}",
            "bias_tests.csv | dataset=unbiased | familywise_p_value",
        ),
        HeadlineResult(
            "Biased sample global p",
            f"{float(test_by_dataset['biased']['monte_carlo_global_p_value']):.4f}",
            "bias_tests.csv | dataset=biased | monte_carlo_global_p_value",
        ),
        HeadlineResult(
            "Martingale loss chance",
            f"{float(risk_by_strategy['martingale']['probability_of_loss']):.2%}",
            "strategy_risk.csv | strategy=martingale | probability_of_loss",
        ),
        HeadlineResult(
            "Quarter Kelly loss chance",
            f"{float(risk_by_strategy['quarter_kelly']['probability_of_loss']):.2%}",
            "strategy_risk.csv | strategy=quarter_kelly | probability_of_loss",
        ),
    ]


def _inline(text: str) -> str:
    safe = escape(text)
    safe = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", safe)
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", safe)
    return safe


def _styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=sample["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=29,
            textColor=GREEN,
            alignment=TA_LEFT,
            spaceAfter=6 * mm,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=sample["Heading2"],
            fontName="Helvetica",
            fontSize=13,
            leading=17,
            textColor=MUTED,
            spaceAfter=8 * mm,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=GREEN,
            spaceBefore=7 * mm,
            spaceAfter=3 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=9.3,
            leading=13.2,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=3.2 * mm,
            allowWidows=0,
            allowOrphans=0,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=MUTED,
            spaceAfter=1.5 * mm,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=sample["Code"],
            fontName="Courier",
            fontSize=8.5,
            leading=12,
            textColor=INK,
            leftIndent=5 * mm,
            rightIndent=5 * mm,
            borderColor=colors.HexColor("#D4D8D3"),
            borderWidth=0.5,
            borderPadding=4 * mm,
            backColor=colors.HexColor("#F1F2EE"),
            spaceBefore=2 * mm,
            spaceAfter=4 * mm,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=sample["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "metric_value": ParagraphStyle(
            "MetricValue",
            parent=sample["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=15,
            textColor=GREEN,
            alignment=TA_CENTER,
        ),
        "metric_source": ParagraphStyle(
            "MetricSource",
            parent=sample["BodyText"],
            fontName="Courier",
            fontSize=6.3,
            leading=7.8,
            textColor=MUTED,
            alignment=TA_LEFT,
        ),
    }


def _metrics_table(styles: dict[str, ParagraphStyle]) -> Table:
    results = load_headline_results()
    cells = [
        [
            Paragraph(_inline(result.label), styles["metric_label"]),
            Paragraph(_inline(result.value), styles["metric_value"]),
            Paragraph(_inline(result.source), styles["metric_source"]),
        ]
        for result in results
    ]
    table = Table(cells, colWidths=[47 * mm, 25 * mm, 92 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF1EC")),
                ("BOX", (0, 0), (-1, -1), 0.7, GOLD),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2 * mm),
            ]
        )
    )
    return table


def _footer(canvas, document) -> None:
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#D8D7D1"))
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setStrokeColor(RED)
    canvas.line(18 * mm, A4[1] - 14 * mm, width - 18 * mm, A4[1] - 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 9 * mm, "Roulette Analytics Lab | Jialiang Gong")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"Page {document.page}")
    if document.page > 1:
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(18 * mm, A4[1] - 11 * mm, "Roulette Analytics Lab V2 | Research report")
    canvas.restoreState()


def _image_flowable(markdown_path: str, caption: str, styles) -> KeepTogether:
    image_path = (SOURCE.parent / markdown_path).resolve()
    image = Image(str(image_path))
    max_width = 168 * mm
    max_height = 93 * mm
    scale = min(max_width / image.imageWidth, max_height / image.imageHeight)
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    return KeepTogether(
        [
            Spacer(1, 2 * mm),
            image,
            Paragraph(_inline(caption), styles["caption"]),
        ]
    )


def markdown_story(text: str, styles: dict[str, ParagraphStyle]):
    story = []
    lines = text.splitlines()
    paragraph_lines: list[str] = []
    list_items: list[str] = []
    code_lines: list[str] = []
    in_code = False
    seen_title = False
    inserted_metrics = False
    cover_closed = False

    def flush_paragraph() -> None:
        if paragraph_lines:
            paragraph = Paragraph(_inline(" ".join(paragraph_lines)), styles["body"])
            story.append(KeepTogether([paragraph]))
            paragraph_lines.clear()

    def flush_list() -> None:
        if list_items:
            items = [
                ListItem(Paragraph(_inline(item), styles["body"]), leftIndent=4 * mm)
                for item in list_items
            ]
            story.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    start="circle",
                    leftIndent=7 * mm,
                    bulletFontName="Helvetica",
                    bulletFontSize=7,
                    spaceAfter=3 * mm,
                )
            )
            list_items.clear()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            if in_code:
                story.append(
                    Paragraph("<br/>".join(escape(item) for item in code_lines), styles["code"])
                )
                code_lines.clear()
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue
        image_match = re.match(r"!\[(.+)]\((.+)\)", stripped)
        if image_match:
            flush_paragraph()
            flush_list()
            story.append(_image_flowable(image_match.group(2), image_match.group(1), styles))
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            flush_list()
            if not seen_title:
                story.append(Spacer(1, 8 * mm))
                story.append(Paragraph(_inline(stripped[2:]), styles["title"]))
                seen_title = True
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            flush_list()
            heading = stripped[3:]
            if heading == "A Statistical Laboratory for Roulette Bias, Bankroll Risk and Decision-Making":
                story.append(Paragraph(_inline(heading), styles["subtitle"]))
                continue
            if not cover_closed:
                story.append(Spacer(1, 58 * mm))
                story.append(Paragraph("Independent Python research extension", styles["subtitle"]))
                story.append(Paragraph("University of Manchester mathematics provenance recorded in docs/provenance.md", styles["meta"]))
                story.append(PageBreak())
                cover_closed = True
            if not inserted_metrics:
                story.append(_metrics_table(styles))
                story.append(Spacer(1, 4 * mm))
                story.append(
                    Paragraph(
                        "Table 1. Headline values with exact generated CSV, row filter, and column source",
                        styles["caption"],
                    )
                )
                story.append(HRFlowable(width="100%", thickness=0.7, color=GOLD))
                inserted_metrics = True
            story.append(CondPageBreak(72 * mm))
            story.append(Paragraph(_inline(heading), styles["h2"]))
            continue
        if stripped.startswith("**") and line.endswith("  "):
            flush_paragraph()
            flush_list()
            story.append(Paragraph(_inline(stripped), styles["meta"]))
            continue
        bullet_match = re.match(r"(?:[-*]|\d+\.)\s+(.+)", stripped)
        if bullet_match:
            flush_paragraph()
            list_items.append(bullet_match.group(1))
            continue
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        paragraph_lines.append(stripped)

    flush_paragraph()
    flush_list()
    return story


def build() -> Path:
    rl_config.invariant = 1
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(TARGET),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=19 * mm,
        title="Optimal Betting Strategy Simulator",
        author="Jialiang Gong",
        subject="Roulette probability, statistical inference, and bankroll risk",
        creator="Roulette Analytics Lab deterministic report builder",
        pageCompression=1,
    )
    styles = _styles()
    story = markdown_story(resolve_csv_markers(SOURCE.read_text(encoding="utf-8")), styles)
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return TARGET


def main() -> None:
    target = build()
    print(target.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
