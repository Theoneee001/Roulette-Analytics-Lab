"""Build the Chinese A4 translation of the technical report."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re
import sys

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.fonts import addMapping
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
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
sys.path.insert(0, str(ROOT))

from scripts.build_report_pdf import load_headline_results, resolve_csv_markers  # noqa: E402


SOURCE = ROOT / "report" / "technical_report_zh-CN.md"
TARGET = ROOT / "report" / "technical_report_zh-CN.pdf"
FONT_PATH = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
ACTIVE_FONT = "CJK"
GREEN = colors.HexColor("#24342F")
RED = colors.HexColor("#A33C35")
GOLD = colors.HexColor("#B78A3E")
INK = colors.HexColor("#26332F")
MUTED = colors.HexColor("#5C6964")


def _register_fonts() -> str:
    """Register a local embedded font or ReportLab's portable CJK fallback."""

    global ACTIVE_FONT
    if FONT_PATH.exists():
        ACTIVE_FONT = "CJK"
        if ACTIVE_FONT not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(ACTIVE_FONT, str(FONT_PATH)))
    else:
        ACTIVE_FONT = "STSong-Light"
        if ACTIVE_FONT not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(UnicodeCIDFont(ACTIVE_FONT))
    pdfmetrics.registerFontFamily(
        ACTIVE_FONT,
        normal=ACTIVE_FONT,
        bold=ACTIVE_FONT,
        italic=ACTIVE_FONT,
        boldItalic=ACTIVE_FONT,
    )
    addMapping(ACTIVE_FONT, 0, 0, ACTIVE_FONT)
    addMapping(ACTIVE_FONT, 1, 0, ACTIVE_FONT)
    addMapping(ACTIVE_FONT, 0, 1, ACTIVE_FONT)
    addMapping(ACTIVE_FONT, 1, 1, ACTIVE_FONT)
    return ACTIVE_FONT


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
            "ChineseTitle",
            parent=sample["Title"],
            fontName=ACTIVE_FONT,
            fontSize=25,
            leading=31,
            textColor=GREEN,
            alignment=TA_LEFT,
            spaceAfter=6 * mm,
        ),
        "subtitle": ParagraphStyle(
            "ChineseSubtitle",
            parent=sample["Heading2"],
            fontName=ACTIVE_FONT,
            fontSize=12.5,
            leading=19,
            textColor=MUTED,
            spaceAfter=4 * mm,
        ),
        "h2": ParagraphStyle(
            "ChineseHeading2",
            parent=sample["Heading2"],
            fontName=ACTIVE_FONT,
            fontSize=15,
            leading=22,
            textColor=GREEN,
            spaceBefore=7 * mm,
            spaceAfter=3 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "ChineseBody",
            parent=sample["BodyText"],
            fontName=ACTIVE_FONT,
            fontSize=9.1,
            leading=14.1,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=3.2 * mm,
            allowWidows=0,
            allowOrphans=0,
            wordWrap="CJK",
        ),
        "meta": ParagraphStyle(
            "ChineseMeta",
            parent=sample["BodyText"],
            fontName=ACTIVE_FONT,
            fontSize=8.7,
            leading=14,
            textColor=MUTED,
            spaceAfter=1.5 * mm,
            wordWrap="CJK",
        ),
        "code": ParagraphStyle(
            "ChineseCode",
            parent=sample["Code"],
            fontName="Courier",
            fontSize=8.2,
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
            "ChineseCaption",
            parent=sample["BodyText"],
            fontName=ACTIVE_FONT,
            fontSize=8,
            leading=12,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
            wordWrap="CJK",
        ),
        "metric_label": ParagraphStyle(
            "ChineseMetricLabel",
            parent=sample["BodyText"],
            fontName=ACTIVE_FONT,
            fontSize=7.5,
            leading=11,
            textColor=MUTED,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
        "metric_value": ParagraphStyle(
            "ChineseMetricValue",
            parent=sample["BodyText"],
            fontName=ACTIVE_FONT,
            fontSize=13,
            leading=16,
            textColor=GREEN,
            alignment=TA_CENTER,
        ),
        "metric_source": ParagraphStyle(
            "ChineseMetricSource",
            parent=sample["BodyText"],
            fontName="Courier",
            fontSize=6.3,
            leading=7.8,
            textColor=MUTED,
            alignment=TA_LEFT,
        ),
    }


def _metrics_table(styles: dict[str, ParagraphStyle]) -> Table:
    translations = {
        "European edge": "欧洲轮盘庄家优势",
        "American edge": "美国轮盘庄家优势",
        "Fair sample corrected p": "公平样本校正后 p 值",
        "Biased sample global p": "偏置样本全局 p 值",
        "Martingale loss chance": "马丁格尔亏损概率",
        "Quarter Kelly loss chance": "四分之一凯利亏损概率",
    }
    cells = [
        [
            Paragraph(_inline(translations[result.label]), styles["metric_label"]),
            Paragraph(_inline(result.value), styles["metric_value"]),
            Paragraph(_inline(result.source), styles["metric_source"]),
        ]
        for result in load_headline_results()
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
    canvas.setFont(ACTIVE_FONT, 7.5)
    canvas.drawString(18 * mm, 9 * mm, "轮盘分析实验室 | 龚嘉亮")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"第 {document.page} 页")
    if document.page > 1:
        canvas.drawString(18 * mm, A4[1] - 11 * mm, "轮盘分析实验室 V2 | 中文技术报告")
    canvas.restoreState()


def _image_flowable(markdown_path: str, caption: str, styles) -> KeepTogether:
    image_path = (SOURCE.parent / markdown_path).resolve()
    image = Image(str(image_path))
    scale = min(168 * mm / image.imageWidth, 93 * mm / image.imageHeight)
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    return KeepTogether(
        [Spacer(1, 2 * mm), image, Paragraph(_inline(caption), styles["caption"])]
    )


def markdown_story(text: str, styles: dict[str, ParagraphStyle]):
    story = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []
    code_lines: list[str] = []
    in_code = False
    seen_title = False
    inserted_metrics = False
    cover_closed = False

    def flush_paragraph() -> None:
        if paragraph_lines:
            story.append(
                KeepTogether(
                    [Paragraph(_inline(" ".join(paragraph_lines)), styles["body"])]
                )
            )
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
                    bulletType="1",
                    start="1",
                    leftIndent=7 * mm,
                    bulletFontName=ACTIVE_FONT,
                    bulletFontSize=7,
                    spaceAfter=3 * mm,
                )
            )
            list_items.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            if in_code:
                story.append(
                    Paragraph(
                        "<br/>".join(escape(item) for item in code_lines),
                        styles["code"],
                    )
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
            if not cover_closed:
                story.append(Spacer(1, 58 * mm))
                story.append(Paragraph("独立完成的 Python 研究扩展", styles["subtitle"]))
                story.append(
                    Paragraph(
                        "曼彻斯特大学数学项目来源与个人贡献边界记录于 docs/provenance.md",
                        styles["meta"],
                    )
                )
                story.append(PageBreak())
                cover_closed = True
            if not inserted_metrics:
                story.append(_metrics_table(styles))
                story.append(Spacer(1, 4 * mm))
                story.append(
                    Paragraph(
                        "表 1. 核心结果及其生成 CSV、行筛选条件和数据列来源",
                        styles["caption"],
                    )
                )
                story.append(HRFlowable(width="100%", thickness=0.7, color=GOLD))
                inserted_metrics = True
            story.append(CondPageBreak(72 * mm))
            story.append(Paragraph(_inline(heading), styles["h2"]))
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
    _register_fonts()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(TARGET),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=19 * mm,
        title="最优投注策略模拟器：中文技术报告",
        author="龚嘉亮",
        subject="轮盘概率、统计推断与资金风险",
        creator="Roulette Analytics Lab Chinese report builder",
        pageCompression=1,
    )
    story = markdown_story(
        resolve_csv_markers(SOURCE.read_text(encoding="utf-8")), _styles()
    )
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return TARGET


def main() -> None:
    print(build().relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
