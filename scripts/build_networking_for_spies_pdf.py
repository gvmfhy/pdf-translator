#!/usr/bin/env python3
"""Build a polished English PDF from the reviewed translation chunks."""

from __future__ import annotations

import argparse
import html
import math
import re
from pathlib import Path

from reportlab.graphics.shapes import Circle, Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

PAGE_SIZE = (6 * inch, 9 * inch)
BOOK_TITLE = "Networking for Spies"
BOOK_SUBTITLE = "How to Benefit from Any Acquaintance"
AUTHORS = "Elena Vavilova and Andrey Bezrukov"
FULL_AUTHORS = "Elena Stanislavovna Vavilova and Andrey Olegovich Bezrukov"

INK = colors.HexColor("#20242A")
RED = colors.HexColor("#BB1024")
DEEP_RED = colors.HexColor("#8E0D1C")
GOLD = colors.HexColor("#E2B93B")
PALE_GOLD = colors.HexColor("#F5EDD4")
MID_GREY = colors.HexColor("#69717A")
LIGHT_GREY = colors.HexColor("#DDE1E5")

SANS = "BookSans"
SANS_BOLD = "BookSans-Bold"
SANS_ITALIC = "BookSans-Italic"
SANS_BOLD_ITALIC = "BookSans-BoldItalic"
SERIF = "BookSerif"
SERIF_BOLD = "BookSerif-Bold"
SERIF_ITALIC = "BookSerif-Italic"
SERIF_BOLD_ITALIC = "BookSerif-BoldItalic"


FONT_FILENAMES = {
    SANS: ("Arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf", "arial.ttf"),
    SANS_BOLD: ("Arial Bold.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "arialbd.ttf"),
    SANS_ITALIC: ("Arial Italic.ttf", "DejaVuSans-Oblique.ttf", "LiberationSans-Italic.ttf", "ariali.ttf"),
    SANS_BOLD_ITALIC: (
        "Arial Bold Italic.ttf",
        "DejaVuSans-BoldOblique.ttf",
        "LiberationSans-BoldItalic.ttf",
        "arialbi.ttf",
    ),
    SERIF: ("Times New Roman.ttf", "DejaVuSerif.ttf", "LiberationSerif-Regular.ttf", "times.ttf"),
    SERIF_BOLD: ("Times New Roman Bold.ttf", "DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf", "timesbd.ttf"),
    SERIF_ITALIC: (
        "Times New Roman Italic.ttf",
        "DejaVuSerif-Italic.ttf",
        "LiberationSerif-Italic.ttf",
        "timesi.ttf",
    ),
    SERIF_BOLD_ITALIC: (
        "Times New Roman Bold Italic.ttf",
        "DejaVuSerif-BoldItalic.ttf",
        "LiberationSerif-BoldItalic.ttf",
        "timesbi.ttf",
    ),
}

SYSTEM_FONT_DIRS = (
    Path("/System/Library/Fonts/Supplemental"),
    Path("/Library/Fonts"),
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/truetype/liberation2"),
    Path("C:/Windows/Fonts"),
)


def register_book_fonts(font_dir=None):
    """Register a Unicode sans/serif pair available on macOS, Linux, or Windows."""
    search_dirs = ([font_dir.resolve()] if font_dir else []) + list(SYSTEM_FONT_DIRS)
    resolved = {}
    for font_name, filenames in FONT_FILENAMES.items():
        for directory in search_dirs:
            match = next((directory / filename for filename in filenames if (directory / filename).is_file()), None)
            if match:
                resolved[font_name] = match
                break
        if font_name not in resolved:
            searched = ", ".join(str(path) for path in search_dirs)
            raise FileNotFoundError(
                f"Could not find a Unicode font for {font_name}. "
                f"Searched: {searched}. Pass --font-dir with Arial, DejaVu, or Liberation font files."
            )
    for font_name, path in resolved.items():
        pdfmetrics.registerFont(TTFont(font_name, str(path)))
    pdfmetrics.registerFontFamily(
        SANS,
        normal=SANS,
        bold=SANS_BOLD,
        italic=SANS_ITALIC,
        boldItalic=SANS_BOLD_ITALIC,
    )
    pdfmetrics.registerFontFamily(
        SERIF,
        normal=SERIF,
        bold=SERIF_BOLD,
        italic=SERIF_ITALIC,
        boldItalic=SERIF_BOLD_ITALIC,
    )

def ascii_hyphens(value: str) -> str:
    """Comply with the PDF workflow's ASCII-hyphen requirement."""
    value = value.replace("\u2011", "-").replace("\u2012", "-")
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    value = value.replace("\u2212", "-")
    return value


def inline_markup(text: str) -> str:
    text = ascii_hyphens(text.strip())
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(
        r"(?<![\"'=])(https?://[^\s<]+)",
        r'<link href="\1" color="#8E0D1C">\1</link>',
        text,
    )
    return text


class BookDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, **kwargs)
        self._bookmark_counter = 0

    def beforeDocument(self):
        # multiBuild may make several passes while resolving the TOC. Stable
        # bookmark names are essential for convergence.
        self._bookmark_counter = 0

    def afterFlowable(self, flowable):
        level = getattr(flowable, "toc_level", None)
        if level is None:
            return
        title = getattr(flowable, "plain_title", "")
        key = f"heading-{self._bookmark_counter}"
        self._bookmark_counter += 1
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(title, key, level=level, closed=False)
        self.notify("TOCEntry", (level, title, self.page, key))


def draw_cover(canvas, doc):
    width, height = PAGE_SIZE
    canvas.saveState()
    canvas.setFillColor(RED)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)

    canvas.setFillColor(colors.HexColor("#D51A30"))
    canvas.circle(width * 0.68, height * 0.48, width * 0.62, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.circle(width * 0.33, height * 0.47, width * 0.34, stroke=0, fill=1)
    canvas.setFillColor(GOLD)
    canvas.circle(width * 0.56, height * 0.47, width * 0.34, stroke=0, fill=1)

    canvas.setFillColor(colors.white)
    canvas.setFont(SANS_BOLD, 11)
    canvas.drawString(0.58 * inch, height - 0.58 * inch, "SVR COLONELS")
    canvas.setFont(SANS_BOLD, 31)
    canvas.drawString(0.56 * inch, height - 1.5 * inch, "NETWORKING")
    canvas.setFont(SANS_BOLD, 35)
    canvas.drawString(0.56 * inch, height - 2.05 * inch, "FOR SPIES")

    canvas.setFillColor(INK)
    canvas.setFont(SANS_BOLD, 15)
    y = 1.83 * inch
    for line in ("HOW TO BENEFIT FROM", "ANY ACQUAINTANCE"):
        canvas.drawString(0.56 * inch, y, line)
        y -= 0.27 * inch

    canvas.setFillColor(colors.white)
    canvas.setFont(SANS, 10.5)
    canvas.drawString(0.58 * inch, 0.68 * inch, "ELENA VAVILOVA  /  ANDREY BEZRUKOV")
    canvas.restoreState()


def draw_frontmatter_page(canvas, doc):
    width, _ = PAGE_SIZE
    canvas.saveState()
    canvas.setFillColor(MID_GREY)
    canvas.setFont(SANS, 8)
    canvas.drawCentredString(width / 2, 0.38 * inch, str(doc.page))
    canvas.restoreState()


def draw_body_page(canvas, doc):
    width, height = PAGE_SIZE
    canvas.saveState()
    canvas.setStrokeColor(LIGHT_GREY)
    canvas.setLineWidth(0.5)
    canvas.line(0.68 * inch, height - 0.48 * inch, width - 0.68 * inch, height - 0.48 * inch)
    canvas.setFillColor(MID_GREY)
    canvas.setFont(SANS, 7.6)
    canvas.drawString(0.72 * inch, height - 0.36 * inch, BOOK_TITLE.upper())
    canvas.drawRightString(width - 0.72 * inch, height - 0.36 * inch, AUTHORS.upper())
    canvas.setFont(SANS, 8)
    canvas.drawCentredString(width / 2, 0.38 * inch, str(doc.page))
    canvas.restoreState()


def make_styles():
    sample = getSampleStyleSheet()
    styles = {}
    styles["Body"] = ParagraphStyle(
        "Body",
        parent=sample["BodyText"],
        fontName=SERIF,
        fontSize=10.4,
        leading=14.6,
        textColor=INK,
        alignment=TA_JUSTIFY,
        spaceAfter=7.5,
        allowWidows=0,
        allowOrphans=0,
        splitLongWords=False,
    )
    styles["BodyNoJustify"] = ParagraphStyle(
        "BodyNoJustify",
        parent=styles["Body"],
        alignment=TA_LEFT,
    )
    styles["Chapter"] = ParagraphStyle(
        "Chapter",
        parent=sample["Heading1"],
        fontName=SANS_BOLD,
        fontSize=20,
        leading=24,
        textColor=DEEP_RED,
        spaceBefore=0,
        spaceAfter=13,
        keepWithNext=True,
    )
    styles["Section"] = ParagraphStyle(
        "Section",
        parent=sample["Heading2"],
        fontName=SANS_BOLD,
        fontSize=13.5,
        leading=17,
        textColor=INK,
        spaceBefore=12,
        spaceAfter=7,
        keepWithNext=True,
    )
    styles["Subsection"] = ParagraphStyle(
        "Subsection",
        parent=sample["Heading3"],
        fontName=SANS_BOLD,
        fontSize=11,
        leading=14,
        textColor=DEEP_RED,
        spaceBefore=9,
        spaceAfter=5,
        keepWithNext=True,
    )
    styles["Caption"] = ParagraphStyle(
        "Caption",
        parent=sample["BodyText"],
        fontName=SANS_ITALIC,
        fontSize=7.8,
        leading=10.2,
        textColor=MID_GREY,
        alignment=TA_CENTER,
        spaceBefore=4,
        spaceAfter=10,
    )
    styles["Small"] = ParagraphStyle(
        "Small",
        parent=sample["BodyText"],
        fontName=SANS,
        fontSize=8.3,
        leading=11.2,
        textColor=MID_GREY,
        alignment=TA_LEFT,
        spaceAfter=5,
    )
    styles["TableHeader"] = ParagraphStyle(
        "TableHeader",
        parent=styles["Small"],
        fontName=SANS_BOLD,
        textColor=colors.white,
        spaceAfter=0,
    )
    styles["TableTitle"] = ParagraphStyle(
        "TableTitle",
        parent=styles["BodyNoJustify"],
        fontName=SERIF_BOLD_ITALIC,
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=INK,
        spaceBefore=8,
        spaceAfter=8,
        keepWithNext=True,
    )
    styles["FrontTitle"] = ParagraphStyle(
        "FrontTitle",
        parent=sample["Title"],
        fontName=SANS_BOLD,
        fontSize=27,
        leading=31,
        textColor=DEEP_RED,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    styles["FrontSubtitle"] = ParagraphStyle(
        "FrontSubtitle",
        parent=sample["Heading2"],
        fontName=SANS,
        fontSize=15,
        leading=19,
        textColor=INK,
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    styles["FrontAuthor"] = ParagraphStyle(
        "FrontAuthor",
        parent=sample["BodyText"],
        fontName=SANS_BOLD,
        fontSize=11.5,
        leading=15,
        textColor=INK,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    return styles


def heading(text: str, level: int, styles):
    style_name = {0: "Chapter", 1: "Section", 2: "Subsection"}[level]
    p = Paragraph(inline_markup(text), styles[style_name])
    p.toc_level = level
    p.plain_title = ascii_hyphens(re.sub(r"[*_`]", "", text))
    return p


def scaled_image(path: Path, max_width=4.25 * inch, max_height=3.0 * inch):
    image = Image(str(path))
    scale = min(max_width / image.imageWidth, max_height / image.imageHeight)
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    image.hAlign = "CENTER"
    return image


def illustration(path: Path, caption: str, styles, max_height=3.0 * inch):
    return KeepTogether(
        [
            scaled_image(path, max_height=max_height),
            Paragraph(inline_markup(caption), styles["Caption"]),
        ]
    )


def diagram_caption(text: str, styles):
    return Paragraph(inline_markup(text), styles["Caption"])


def relationship_circles():
    d = Drawing(330, 245)
    cx, cy = 165, 116
    for radius, fill in [(102, colors.HexColor("#F7F1E1")), (70, colors.white), (38, PALE_GOLD)]:
        circle = Circle(cx, cy, radius, strokeColor=MID_GREY, fillColor=fill, strokeWidth=1.1)
        if radius == 102:
            circle.strokeDashArray = [4, 4]
        d.add(circle)
    d.add(String(cx, cy + 80, "Development Circle", textAnchor="middle", fontName=SANS_BOLD, fontSize=9, fillColor=INK))
    d.add(String(cx, cy + 48, "Productivity Circle", textAnchor="middle", fontName=SANS_BOLD, fontSize=9, fillColor=INK))
    d.add(String(cx, cy + 4, "Support", textAnchor="middle", fontName=SANS_BOLD, fontSize=8.5, fillColor=INK))
    d.add(String(cx, cy - 8, "Circle", textAnchor="middle", fontName=SANS_BOLD, fontSize=8.5, fillColor=INK))
    d.add(Circle(cx, cy, 2.4, strokeColor=MID_GREY, fillColor=MID_GREY))
    return d


def density_scale():
    d = Drawing(350, 145)
    groups = [70, 175, 280]
    diagrams = [
        (
            [(0, 0), (-25, 0), (-13, 22), (13, 22), (25, 0), (13, -22), (-13, -22)],
            [(0, i) for i in range(1, 7)],
        ),
        (
            [(-28, 15), (-5, 23), (13, 37), (18, 8), (43, 3), (26, -27), (55, -25)],
            [(0, 1), (1, 2), (1, 3), (3, 4), (3, 5), (4, 5), (4, 6)],
        ),
        (
            [(-28, 22), (28, 31), (0, 8), (17, -2), (-10, -15), (-28, -27), (23, -27)],
            [(0,1), (0,2), (0,4), (0,5), (1,2), (1,3), (1,6), (2,3), (2,4), (2,5), (3,4), (3,6), (4,5), (4,6), (5,6)],
        ),
    ]
    for idx, cx in enumerate(groups):
        cy = 76
        points, links = diagrams[idx]
        for a, b in links:
            ax, ay = points[a]
            bx, by = points[b]
            d.add(Line(cx + ax, cy + ay, cx + bx, cy + by, strokeColor=colors.HexColor("#A0A6AC"), strokeWidth=0.7))
        for x, y in points:
            d.add(Circle(cx + x, cy + y, 3.2, strokeColor=INK, fillColor=INK))
    d.add(Line(35, 10, 315, 10, strokeColor=MID_GREY, strokeWidth=1))
    d.add(String(30, 6, "0", textAnchor="end", fontName=SANS, fontSize=8, fillColor=MID_GREY))
    d.add(String(320, 6, "1", textAnchor="start", fontName=SANS, fontSize=8, fillColor=MID_GREY))
    return d


def network_map(with_links=False, rings=False):
    d = Drawing(350, 335)
    cx, cy, radius = 175, 165, 125
    if rings:
        for r in (42, 82, 125):
            d.add(Circle(cx, cy, r, strokeColor=MID_GREY, fillColor=None, strokeWidth=1))
    else:
        d.add(Circle(cx, cy, radius, strokeColor=MID_GREY, fillColor=colors.HexColor("#FBFAF6"), strokeWidth=1.2))
    angles = [90, 30, -20, -90, -135, 180]
    for angle in angles:
        a = math.radians(angle)
        d.add(Line(cx, cy, cx + radius * math.cos(a), cy + radius * math.sin(a), strokeColor=colors.HexColor("#BBC0C5"), strokeWidth=0.6))
    labels = [
        ("OFFICE", 132),
        ("CLIENTS", 48),
        ("ACQUAINTANCES" if with_links else "FRIENDS", -45),
        ("FAMILY", -105),
        ("GOLF", -135),
        ("NEIGHBORS", 180),
    ]
    for label, angle in labels:
        a = math.radians(angle)
        d.add(String(cx + (radius + 18) * math.cos(a), cy + (radius + 18) * math.sin(a), label, textAnchor="middle", fontName=SANS_BOLD, fontSize=7, fillColor=MID_GREY))
    if rings:
        d.add(String(cx, cy + 104, "DEVELOPMENT", textAnchor="middle", fontName=SANS, fontSize=7.2, fillColor=MID_GREY))
        d.add(String(cx, cy + 64, "PRODUCTIVITY", textAnchor="middle", fontName=SANS, fontSize=7.2, fillColor=MID_GREY))
        d.add(String(cx, cy + 24, "SUPPORT", textAnchor="middle", fontName=SANS, fontSize=7.2, fillColor=MID_GREY))
    source_small = [
        (374,42), (319,58), (189,68), (176,75), (396,82), (193,105), (250,109), (421,116),
        (97,125), (63,138), (367,138), (488,166), (169,182), (250,189), (160,196), (125,206),
        (396,216), (72,219), (421,260), (220,263), (469,270), (315,280), (147,290), (260,293),
        (132,297), (495,303), (246,309), (83,315), (363,322), (256,326), (147,336), (367,340),
        (406,340), (445,365), (249,379), (359,389), (209,393), (290,410), (342,461), (224,465),
    ]
    source_large = [(441,124), (180,151), (333,304), (205,358), (125,382), (326,382)]

    def source_to_drawing(point):
        x, y = point
        scale = radius / 249.0
        return cx + (x - 273) * scale, cy - (y - 251) * scale

    small_pts = [source_to_drawing(point) for point in source_small]
    large_pts = [source_to_drawing(point) for point in source_large]
    if with_links:
        solid_edges = [(2,1), (4,10), (9,15), (14,13), (18,20), (24,22), (26,29), (29,34), (35,33), (36,39)]
        dashed_edges = [(41,13), (13,21), (17,22), (27,22), (45,35)]
        combined = small_pts + large_pts
        for left, right in solid_edges:
            x1, y1 = combined[left]
            x2, y2 = combined[right]
            d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#9FA6AC"), strokeWidth=0.65))
        for left, right in dashed_edges:
            x1, y1 = combined[left]
            x2, y2 = combined[right]
            line = Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#9FA6AC"), strokeWidth=0.65)
            line.strokeDashArray = [2, 2]
            d.add(line)
    for x, y in small_pts:
        d.add(Circle(x, y, 2.15, strokeColor=INK, fillColor=INK))
    for x, y in large_pts:
        d.add(Circle(x, y, 4.7, strokeColor=INK, fillColor=INK))
    for label, source_point, dx, dy in [
        ("Sa", (189,68), -2, 8), ("V", (367,138), -6, 7), ("V", (125,206), -6, 7),
        ("Sa", (421,260), -3, 8), ("V", (125,382), -5, 7), ("So", (326,382), -6, 7),
    ]:
        x, y = source_to_drawing(source_point)
        d.add(String(x + dx, y + dy, label, textAnchor="middle", fontName=SANS, fontSize=6.3, fillColor=MID_GREY))
    d.add(Circle(cx, cy, 4, strokeColor=RED, fillColor=RED))
    return d


def thai_student_map(with_links=False):
    """Recreate the two-country example used in the source edition."""
    d = Drawing(350, 320)
    cx, cy, radius = 175, 155, 124
    d.add(Circle(cx, cy, radius, strokeColor=MID_GREY, fillColor=colors.HexColor("#FBFAF6"), strokeWidth=1.2))
    for angle, width in [(90, 0.7), (42, 1.5), (-7, 0.7), (-51, 0.7), (-90, 1.5), (-153, 0.7), (180, 0.7)]:
        a = math.radians(angle)
        d.add(Line(cx, cy, cx + radius * math.cos(a), cy + radius * math.sin(a), strokeColor=MID_GREY, strokeWidth=width))
    labels = [
        ("UNIVERSITY", 90, 230),
        ("WORK", 54, 153),
        ("FRIENDS", 94, 68),
        ("NEIGHBORS", 177, 274),
        ("FAMILY", 273, 220),
        ("CHILDHOOD FRIENDS", 281, 134),
        ("FRIENDS", 240, 58),
    ]
    for label, x, y in labels:
        d.add(String(x, y, label, textAnchor="middle", fontName=SANS_BOLD, fontSize=6.4, fillColor=MID_GREY))
    d.add(String(16, 159, "USA", textAnchor="start", fontName=SANS_BOLD, fontSize=9, fillColor=INK))
    d.add(String(334, 92, "THAILAND", textAnchor="end", fontName=SANS_BOLD, fontSize=9, fillColor=INK))
    source_points = [
        (253,50), (175,62), (315,69), (228,86), (160,104), (346,107), (183,120), (437,120),
        (275,129), (365,141), (296,142), (156,164), (249,164), (459,167), (325,184), (91,188),
        (214,192), (156,195), (401,199), (287,210), (432,229), (353,230), (276,233), (108,236),
        (231,240), (365,243), (491,248), (101,276), (167,279), (444,280), (329,284), (131,295),
        (491,295), (286,302), (394,309), (332,312), (447,323), (221,327), (289,331), (171,346),
        (117,360), (466,372), (179,373), (411,373), (356,376), (234,385), (329,425), (353,428),
        (217,429), (390,440), (283,449),
    ]

    def source_to_drawing(point):
        x, y = point
        scale = radius / 246.0
        return cx + (x - 310) * scale, cy - (y - 257) * scale

    pts = [source_to_drawing(point) for point in source_points]
    if with_links:
        source_edges = [
            (1,12), (8,10), (12,14), (11,24), (24,19), (24,22),
            (23,27), (31,28), (37,42), (42,45), (45,37), (45,50),
            (7,18), (18,20), (18,25), (20,25), (20,26), (21,25),
            (29,34), (29,32), (35,46), (44,49), (44,43), (46,44), (46,47),
        ]
        for left, right in source_edges:
            x1, y1 = pts[left]
            x2, y2 = pts[right]
            d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#AEB4BA"), strokeWidth=0.55))
    for x, y in pts:
        d.add(Circle(x, y, 2.1, strokeColor=INK, fillColor=INK))
    d.add(Circle(cx, cy, 4, strokeColor=RED, fillColor=RED))
    return d


def goal_circle():
    d = Drawing(350, 345)
    cx, cy = 175, 170
    for r in (55, 100, 145):
        d.add(Circle(cx, cy, r, strokeColor=colors.HexColor("#AEB4B9"), fillColor=None, strokeWidth=1))
    for angle in (0, 90, 180, 270):
        a = math.radians(angle)
        d.add(Line(cx, cy, cx + 145 * math.cos(a), cy + 145 * math.sin(a), strokeColor=MID_GREY, strokeWidth=0.8))
    for text, x, y in [("HEALTH", 42, 321), ("CAREER", 307, 321), ("TRAVEL", 42, 13), ("FAMILY", 307, 13)]:
        d.add(String(x, y, text, textAnchor="middle", fontName=SANS_BOLD, fontSize=9, fillColor=INK))
    for text, x, y in [("WHAT", 175, 153), ("WHO / WHERE", 245, 153), ("HOW", 317, 153)]:
        d.add(String(x, y, text, textAnchor="middle", fontName=SANS_BOLD, fontSize=8.5, fillColor=DEEP_RED))
    examples = [
        ("Lose weight", 141, 184),
        ("Tennis coach", 107, 205),
        ("Pavel (likes trips to the countryside)", 98, 235),
        ("Gourmet market", 132, 254),
        ("Invite him on an outing", 73, 266),
        ("Collect healthy-eating recipes", 145, 286),
        ("Create a tennis-practice schedule", 54, 190),
    ]
    for text, x, y in examples:
        d.add(String(x, y, text, textAnchor="middle", fontName=SANS, fontSize=6.5, fillColor=MID_GREY))
    return d


def formal_real_structure():
    d = Drawing(370, 235)
    line_color = colors.HexColor("#A9AFB4")
    node_fill = colors.HexColor("#E8ECEF")
    d.add(String(90, 220, "FORMAL STRUCTURE", textAnchor="middle", fontName=SANS_BOLD, fontSize=8, fillColor=INK))
    d.add(String(280, 220, "REAL STRUCTURE", textAnchor="middle", fontName=SANS_BOLD, fontSize=8, fillColor=INK))
    d.add(Line(185, 10, 185, 210, strokeColor=MID_GREY, strokeWidth=0.7))

    # The source diagram contains A-R in both views and highlights M. Keep the
    # same reporting chains on the left rather than substituting a generic tree.
    formal = {
        "A": (90, 188), "B": (22, 154), "C": (78, 154), "D": (145, 154),
        "E": (22, 123), "I": (22, 93), "M": (22, 63), "P": (22, 33), "R": (22, 8),
        "F": (78, 123), "J": (78, 93), "N": (78, 63), "Q": (78, 33),
        "G": (128, 123), "K": (128, 93), "O": (128, 63),
        "H": (162, 123), "L": (162, 93),
    }
    formal_edges = [
        ("A", "B"), ("A", "C"), ("A", "D"),
        ("B", "E"), ("E", "I"), ("I", "M"), ("M", "P"), ("P", "R"),
        ("C", "F"), ("F", "J"), ("J", "N"), ("N", "Q"),
        ("D", "G"), ("D", "H"), ("G", "K"), ("K", "O"), ("H", "L"),
    ]
    for parent, child in formal_edges:
        x1, y1 = formal[parent]
        x2, y2 = formal[child]
        d.add(Line(x1, y1 - 7, x2, y2 + 7, strokeColor=line_color, strokeWidth=0.55))

    # Approximate the original informal-power map while preserving every node
    # and the same highlighted center of influence.
    real = {
        "O": (280, 188), "D": (328, 163), "H": (253, 145), "G": (302, 145),
        "E": (214, 112), "M": (280, 112), "A": (350, 112), "R": (214, 78),
        "K": (250, 78), "J": (319, 78), "B": (350, 78), "L": (230, 46),
        "I": (256, 18), "Q": (280, 18), "N": (300, 46), "C": (334, 46),
        "P": (316, 14), "F": (356, 14),
    }
    real_edges = [
        ("O", "D"), ("O", "H"), ("D", "H"), ("D", "G"), ("H", "G"),
        ("H", "M"), ("G", "M"), ("E", "M"), ("M", "A"), ("A", "B"),
        ("B", "C"), ("C", "F"), ("C", "P"), ("P", "Q"), ("P", "F"),
        ("Q", "I"), ("I", "L"), ("L", "R"), ("R", "K"), ("K", "L"),
        ("K", "I"), ("K", "Q"), ("M", "K"), ("M", "Q"), ("M", "J"),
        ("M", "N"), ("M", "B"), ("M", "C"), ("J", "C"), ("N", "C"),
    ]
    for left, right in real_edges:
        x1, y1 = real[left]
        x2, y2 = real[right]
        d.add(Line(x1, y1, x2, y2, strokeColor=line_color, strokeWidth=0.5))

    def add_nodes(nodes):
        for label, (x, y) in nodes.items():
            highlighted = label == "M"
            fill = MID_GREY if highlighted else node_fill
            text_color = colors.white if highlighted else INK
            d.add(Rect(x - 9, y - 7, 18, 14, strokeColor=line_color, fillColor=fill, strokeWidth=0.55))
            d.add(String(x, y - 2.4, label, textAnchor="middle", fontName=SANS_BOLD, fontSize=6.5, fillColor=text_color))

    add_nodes(formal)
    add_nodes(real)
    return d


def vertical_networked():
    d = Drawing(370, 205)
    d.add(String(92, 190, "VERTICAL", textAnchor="middle", fontName=SANS_BOLD, fontSize=8, fillColor=INK))
    d.add(String(278, 190, "NETWORKED", textAnchor="middle", fontName=SANS_BOLD, fontSize=8, fillColor=INK))
    rows = [[92], [48, 92, 136], [22, 50, 78, 106, 134, 162]]
    coords = []
    for row_idx, xs in enumerate(rows):
        y = 155 - row_idx * 47
        row_coords = []
        for x in xs:
            d.add(Rect(x - 11, y - 7, 22, 14, strokeColor=colors.HexColor("#A9AFB4"), fillColor=PALE_GOLD, strokeWidth=0.6))
            row_coords.append((x, y))
        coords.append(row_coords)
    for parent in coords[0]:
        for child in coords[1]: d.add(Line(parent[0], parent[1]-7, child[0], child[1]+7, strokeColor=colors.HexColor("#A9AFB4"), strokeWidth=0.55))
    for idx, parent in enumerate(coords[1]):
        for child in coords[2][idx * 2:idx * 2 + 2]:
            d.add(Line(parent[0], parent[1]-7, child[0], child[1]+7, strokeColor=colors.HexColor("#A9AFB4"), strokeWidth=0.55))
    nodes = [(278 + 58*math.cos(i*2*math.pi/8), 108 + 58*math.sin(i*2*math.pi/8)) for i in range(8)]
    for i, (x1,y1) in enumerate(nodes):
        for j in range(i+1, len(nodes)):
            x2,y2=nodes[j]
            d.add(Line(x1,y1,x2,y2,strokeColor=colors.HexColor("#B5BAC0"),strokeWidth=0.42))
    for x,y in nodes:
        d.add(Rect(x-10,y-6,20,12,strokeColor=colors.HexColor("#A9AFB4"),fillColor=colors.HexColor("#E8ECEF"),strokeWidth=0.6))
    return d


def meeting_preparation_table(styles):
    data = [
        ["Problem", "Plan", "Result"],
        ["What should I do to develop the relationship?", "", ""],
        ["How can I learn more about this person?", "", ""],
        ["What can I give?", "", ""],
        ["What can I ask for?", "", ""],
        ["How can I secure the next meeting?", "", ""],
    ]
    wrapped = [
        [Paragraph(inline_markup(cell), styles["TableHeader"] if row_idx == 0 else styles["Small"]) for cell in row]
        for row_idx, row in enumerate(data)
    ]
    table = Table(wrapped, colWidths=[2.15 * inch, 1.35 * inch, 1.15 * inch], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), DEEP_RED),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), SANS_BOLD),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#B8BDC2")),
        ("BACKGROUND", (0,1), (-1,-1), colors.HexColor("#FBFAF6")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    return table


def relationship_dynamics_table(styles):
    data = [
        ["Human behavior", "Meeting results (0-3)", "", "", "", "", ""],
        ["", "1st", "2nd", "3rd", "4th", "5th", "6th"],
        ["Commitment and intensity", "1", "2", "", "", "", ""],
        ["Initiative and reciprocity", "2", "2", "", "", "", ""],
        ["Emotional engagement", "3", "3", "", "", "", ""],
        ["Openness and trust", "0", "1", "", "", "", ""],
    ]
    wrapped = [
        [Paragraph(inline_markup(cell), styles["TableHeader"] if row_idx < 2 else styles["Small"]) for cell in row]
        for row_idx, row in enumerate(data)
    ]
    table = Table(wrapped, colWidths=[2.25 * inch] + [0.4 * inch] * 6, repeatRows=1)
    table.setStyle(TableStyle([
        ("SPAN", (0,0), (0,1)),
        ("SPAN", (1,0), (6,0)),
        ("BACKGROUND", (0,0), (-1,1), DEEP_RED),
        ("TEXTCOLOR", (0,0), (-1,1), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#B8BDC2")),
        ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BACKGROUND", (0,2), (-1,-1), colors.HexColor("#FBFAF6")),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    return table


def special_elements(title: str, image_dir: Path, styles):
    title_key = ascii_hyphens(title).lower().replace("“", '"').replace("”", '"').replace("’", "'")
    aliases = {
        "organize dinners and parties": "organize lunches and parties",
        "host lunches and parties": "organize lunches and parties",
        'become a "gardener" of human relationships': 'becoming a "gardener" of human relationships',
        '"decoding" organizations': '"deciphering" organizations',
        "influence in networked and virtual organizations": "influence in network and virtual organizations",
        "how to forge a path into an organization": "how to pave a path into an organization",
        "how to map your network": "how to draw a map of your network",
        'riding the "social elevators"': 'riding "social elevators"',
    }
    title_key = aliases.get(title_key, title_key)
    if title_key.startswith("initial sorting") and "ois" in title_key:
        title_key = 'initial sorting - the "ois" method'
    cartoons = {
        "introduction. networking from a spy's perspective": [(1, "A bird's-eye view reveals routes and relationships that are hard to see from ground level.")],
        'your network as your "reflection"': [(2, "The people around us reflect the composition of our personal network.")],
        "three main rules of networking": [(7, "Gatekeepers control access; connectors and bridges help open routes to people and groups.")],
        "your information sources": [(11, "Useful information can come from many kinds of contacts.")],
        "first meeting scenarios": [(12, "A prepared introduction can create a natural opening for conversation.")],
        "how to prevent rejection": [(13, "A poorly judged approach can trigger an immediate defensive reaction.")],
        '"behavioral hygiene"': [(14, "Appearance and behavior shape first impressions before a word is spoken.")],
        'initial sorting - the "ois" method': [(15, "Assess risk before investing in a new contact.")],
        "how to manage a spontaneous conversation": [(17, "A conversation needs attentive management, not a hidden agenda.")],
        'becoming a "gardener" of human relationships': [(18, "Relationships develop through patient, repeated care.")],
        "remote networking": [(19, "Remote contact can maintain a relationship when face-to-face contact is impossible.")],
        "organize lunches and parties": [(20, "Shared meals and gatherings create opportunities for stronger ties.")],
        "do something interesting together": [(21, "Shared activities create memories and expand the basis of a relationship.")],
        "diagnosing problems in relationships": [(23, "When one party always pulls, the relationship is no longer reciprocal.")],
        "how to pave a path into an organization": [(26, "An additional bridge provides another route into an organization.")],
        "four problems in working with organizations": [(30, "Internal sponsorship can disappear unexpectedly.")],
        'riding "social elevators"': [(32, "Social elevators can move people between levels of status and opportunity.")],
    }
    result = []
    for idx, _caption in cartoons.get(title_key, []):
        result.append(illustration(image_dir / f"figure-{idx:03d}.png", "Original-edition illustration.", styles))

    if title_key in {"connection map", "a map of connections"}:
        result += [thai_student_map(with_links=False), diagram_caption("Translated recreation of the original diagram: the Thai student's map separates contacts in the United States and Thailand, then groups them by context.", styles)]
    elif title_key == "network density and its significance":
        result += [density_scale(), diagram_caption("Translated recreation of the original diagram: at density 0, contacts are unconnected to one another; at density 1, every contact is connected to every other contact.", styles), thai_student_map(with_links=True), diagram_caption("Translated recreation of the original diagram: relationship lines reveal clusters and the density of different parts of the Thai student's network.", styles)]
    elif title_key == "three levels of relationships":
        result += [relationship_circles(), diagram_caption("Translated recreation of the original diagram: the Support Circle lies inside the Productivity Circle, which lies inside the wider Development Circle.", styles)]
    elif title_key == "how to draw a map of your network":
        result += [network_map(with_links=False, rings=True), diagram_caption("Translated recreation of the original diagram - Stage 2: place contacts by relationship level and context.", styles), network_map(with_links=True, rings=True), diagram_caption("Translated recreation of the original diagram - Stage 3: add the most important relationship lines.", styles)]
    elif title_key == "circle of goals":
        result += [goal_circle(), diagram_caption("Translated recreation of the original diagram: the Circle of Goals connects what you want with who or where can help, and how to build the necessary relationships.", styles)]
    elif title_key == "table: preparation and evaluation of meetings" or (
        title_key.startswith("table:")
        and "meeting" in title_key
        and "prepar" in title_key
        and "evaluat" in title_key
    ):
        result += [meeting_preparation_table(styles), Spacer(1, 10)]
    elif title_key == '"deciphering" organizations':
        result += [formal_real_structure(), diagram_caption("Translated recreation of the original diagram: formal reporting lines can differ sharply from the real structure of influence.", styles)]
    elif title_key == "influence in network and virtual organizations":
        result += [vertical_networked(), diagram_caption("Translated recreation of the original diagram: vertical organizations concentrate authority in a hierarchy; networked organizations distribute relationships across many nodes.", styles)]
    return result


def load_clean_lines(translations_dir: Path):
    chunks = []
    for path in sorted(translations_dir.glob("chunk_*_translation.md")):
        cleaned = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if re.match(r"^\*\[(?:Continued from|End of Chunk|End of Book)", line.strip()):
                continue
            cleaned.append(line.rstrip())
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()
        if cleaned and cleaned[-1].strip() == "---":
            cleaned.pop()
            while cleaned and not cleaned[-1].strip():
                cleaned.pop()
        while cleaned and not cleaned[0].strip():
            cleaned.pop(0)
        chunks.append(cleaned)

    # The reviewed chunk files already carry every split sentence and paragraph
    # back to its originating chunk, so each boundary is now a true paragraph or
    # section break. Keep the generic join mechanism disabled as a safeguard.
    join_after = set()
    lines = list(chunks[0]) if chunks else []
    for chunk_num, next_chunk in enumerate(chunks[1:], start=1):
        if chunk_num in join_after and lines and next_chunk:
            while lines and not lines[-1].strip():
                lines.pop()
            previous = re.sub(r"(?:\.\.\.|…)$", "", lines[-1].rstrip())
            continuation = next_chunk.pop(0).lstrip()
            previous_word = re.findall(r"[A-Za-z']+", previous.lower())
            next_word = re.match(r"([A-Za-z']+)(.*)$", continuation)
            if previous_word and next_word and previous_word[-1] == next_word.group(1).lower():
                continuation = next_word.group(2).lstrip()
            separator = "" if continuation[:1] in ",.;:!?)]" else " "
            lines[-1] = (previous + separator + continuation).strip()
            lines.extend(next_chunk)
        else:
            lines.append("")
            lines.extend(next_chunk)
    return lines


def remove_repository_frontmatter(lines):
    """Keep book content but replace the repository's fixed-page TOC."""
    output = []
    in_toc = False
    skipped_title_block = False
    for line in lines:
        stripped = line.strip()
        if not skipped_title_block:
            if stripped == "## Synopsis":
                skipped_title_block = True
                output.append(line)
            continue
        if stripped == "## Table of Contents":
            in_toc = True
            continue
        if in_toc:
            if stripped == "## Dedication":
                in_toc = False
                output.append(line)
            continue
        output.append(line)
    return output


def parse_story(lines, styles, image_dir: Path):
    story = []
    paragraph_lines = []
    bullet_lines = []
    first_chapter = True

    def flush_paragraph():
        nonlocal paragraph_lines
        if paragraph_lines:
            text = " ".join(part.strip() for part in paragraph_lines if part.strip())
            if text:
                plain = re.sub(r"[*_`]", "", text).strip().lower()
                if plain.startswith("table:") and "relationship dynamics" in plain:
                    story.append(Paragraph("Table: Relationship Dynamics", styles["TableTitle"]))
                    story.append(relationship_dynamics_table(styles))
                else:
                    story.append(Paragraph(inline_markup(text), styles["Body"]))
                    deferred = []
                    if plain.startswith("for those who pass the o-test"):
                        deferred = [(16, "Original-edition illustration.")]
                    elif plain.startswith("regardless of the mechanisms of power at work"):
                        deferred = [(27, "Original-edition illustration.")]
                    elif plain.startswith("under the second style"):
                        deferred = [(28, "Original-edition illustration.")]
                    elif plain.startswith('the third, "bureaucratic," style'):
                        deferred = [(29, "Original-edition illustration.")]
                    for figure_idx, caption in deferred:
                        story.append(CondPageBreak(3.1 * inch))
                        story.append(illustration(image_dir / f"figure-{figure_idx:03d}.png", caption, styles))
            paragraph_lines = []

    def flush_bullets():
        nonlocal bullet_lines
        if bullet_lines:
            items = [ListItem(Paragraph(inline_markup(item), styles["BodyNoJustify"]), leftIndent=5) for item in bullet_lines]
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=18, bulletFontName=SANS, bulletFontSize=7, spaceAfter=7))
            bullet_lines = []

    for raw in lines:
        stripped = raw.strip()
        heading_match = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        is_bullet = re.match(r"^(?:[-*]|•)\s+(.+)$", stripped)
        if heading_match:
            flush_paragraph()
            flush_bullets()
            level = len(heading_match.group(1)) - 1
            title = heading_match.group(2).strip()
            if level == 0:
                if story:
                    # Start top-level sections on a fresh page, but do not emit
                    # an empty page when the previous section already ended at
                    # the bottom of a frame.
                    story.append(CondPageBreak(7.7 * inch))
                first_chapter = False
            extras = special_elements(title, image_dir, styles)
            if extras and level > 0:
                story.append(CondPageBreak(3.15 * inch))
            title_flowable = heading(title, level, styles)
            if first_chapter and level > 0:
                # Front-matter sections precede the first chapter and therefore
                # need to be top-level outline entries despite their Markdown level.
                title_flowable.toc_level = 0
            story.append(title_flowable)
            story.extend(extras)
        elif is_bullet:
            flush_paragraph()
            bullet_lines.append(is_bullet.group(1))
        elif stripped == "---":
            flush_paragraph()
            flush_bullets()
            story.append(Spacer(1, 3))
        elif not stripped:
            flush_paragraph()
            flush_bullets()
        else:
            if bullet_lines:
                flush_bullets()
            paragraph_lines.append(stripped)
    flush_paragraph()
    flush_bullets()
    story.append(PageBreak())
    story.append(Spacer(1, 1.0 * inch))
    story.append(illustration(image_dir / "figure-033.png", "Original-edition illustration.", styles, max_height=3.4 * inch))
    return story


def front_matter(styles):
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOC0", fontName=SANS_BOLD, fontSize=10, leading=13, textColor=INK, leftIndent=0, firstLineIndent=0, spaceBefore=5),
        ParagraphStyle("TOC1", fontName=SANS, fontSize=8.7, leading=11.5, textColor=INK, leftIndent=14, firstLineIndent=-5, spaceBefore=1),
        ParagraphStyle("TOC2", fontName=SANS, fontSize=8.2, leading=10.5, textColor=MID_GREY, leftIndent=26, firstLineIndent=-5, spaceBefore=0),
    ]
    return [
        NextPageTemplate("FrontMatter"),
        PageBreak(),
        Spacer(1, 0.72 * inch),
        Paragraph(BOOK_TITLE, styles["FrontTitle"]),
        Paragraph(BOOK_SUBTITLE, styles["FrontSubtitle"]),
        Spacer(1, 0.3 * inch),
        Paragraph(FULL_AUTHORS, styles["FrontAuthor"]),
        Paragraph("Series: <i>Woman Spy: My Life Undercover</i>", styles["FrontAuthor"]),
        Spacer(1, 0.55 * inch),
        HRFlowable(width="60%", color=GOLD, thickness=2, hAlign="CENTER", spaceBefore=4, spaceAfter=18),
        Paragraph("English translation reviewed against the complete 274-page Russian source edition.", styles["Small"]),
        Paragraph("Original publisher: Eksmo, Moscow, 2021. ISBN 978-5-04-160537-7.", styles["Small"]),
        Paragraph("Original edition record: <link href=\"https://www.litres.ru/pages/biblio_book/?art=66635352\" color=\"#8E0D1C\">litres.ru/pages/biblio_book/?art=66635352</link>.", styles["Small"]),
        Paragraph("This is a reader-created translation edition. Original text and illustrations remain copyright their respective rights holders.", styles["Small"]),
        NextPageTemplate("FrontMatter"),
        PageBreak(),
        Paragraph("Contents", styles["FrontTitle"]),
        Spacer(1, 6),
        toc,
        NextPageTemplate("Body"),
        PageBreak(),
    ]


def build_pdf(translations_dir: Path, image_dir: Path, output: Path, font_dir=None):
    translation_files = sorted(translations_dir.glob("chunk_*_translation.md"))
    expected_translation_names = {
        f"chunk_{index:03d}_translation.md" for index in range(1, 15)
    }
    actual_translation_names = {path.name for path in translation_files}
    if actual_translation_names != expected_translation_names:
        missing = sorted(expected_translation_names - actual_translation_names)
        unexpected = sorted(actual_translation_names - expected_translation_names)
        raise ValueError(
            "The reviewed PDF requires exactly translation chunks 001-014. "
            f"Missing: {missing or 'none'}; unexpected: {unexpected or 'none'}"
        )
    required_images = [
        1, 2, 7, 11, 12, 13, 14, 15, 16, 17, 18,
        19, 20, 21, 23, 26, 27, 28, 29, 30, 32, 33,
    ]
    missing_images = [image_dir / f"figure-{index:03d}.png" for index in required_images]
    missing_images = [path for path in missing_images if not path.is_file()]
    if missing_images:
        raise FileNotFoundError(
            "Missing original-edition images. Run scripts/extract_pdf_images.py first. "
            f"First missing file: {missing_images[0]}"
        )
    register_book_fonts(font_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = make_styles()
    margin_x = 0.7 * inch
    margin_top = 0.62 * inch
    margin_bottom = 0.62 * inch
    frame = Frame(
        margin_x,
        margin_bottom,
        PAGE_SIZE[0] - 2 * margin_x,
        PAGE_SIZE[1] - margin_top - margin_bottom,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="main",
    )
    cover_frame = Frame(0, 0, PAGE_SIZE[0], PAGE_SIZE[1], leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="cover")
    doc = BookDocTemplate(
        str(output),
        pagesize=PAGE_SIZE,
        leftMargin=margin_x,
        rightMargin=margin_x,
        topMargin=margin_top,
        bottomMargin=margin_bottom,
        title=f"{BOOK_TITLE}: {BOOK_SUBTITLE}",
        author=AUTHORS,
        subject="Reviewed English translation",
        creator="Codex / ReportLab",
    )
    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[cover_frame], onPage=draw_cover),
        PageTemplate(id="FrontMatter", frames=[frame], onPage=draw_frontmatter_page),
        PageTemplate(id="Body", frames=[frame], onPage=draw_body_page),
    ])
    lines = remove_repository_frontmatter(load_clean_lines(translations_dir))
    story = front_matter(styles) + parse_story(lines, styles, image_dir)
    doc.multiBuild(story)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--translations-dir", type=Path, default=Path("translations"))
    parser.add_argument("--image-dir", type=Path, default=Path("assets/source_images"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/Networking_for_Spies_Reviewed_English_Translation.pdf"),
    )
    parser.add_argument(
        "--font-dir",
        type=Path,
        help="Optional directory containing Arial, DejaVu, or Liberation Sans/Serif font files",
    )
    args = parser.parse_args()
    build_pdf(
        args.translations_dir.resolve(),
        args.image_dir.resolve(),
        args.output.resolve(),
        args.font_dir,
    )


if __name__ == "__main__":
    main()
