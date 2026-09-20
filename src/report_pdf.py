from __future__ import annotations
from xml.sax.saxutils import escape

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


VERSION = "v2.1.0"

# -------------------------------------------------------------
# HPBブランドカラー
# -------------------------------------------------------------
MAIN_COLOR = colors.HexColor("#992854")
SUB_COLOR = colors.HexColor("#c18096")
TITLE_COLOR = colors.HexColor("#d5728d")
LIGHT_BG = colors.HexColor("#F8F1F4")
GRID_COLOR = colors.HexColor("#D9C3CC")
TEXT_COLOR = colors.HexColor("#333333")
MUTED_COLOR = colors.HexColor("#777777")
WHITE = colors.white


def _register_fonts():
    """
    ReportLab標準の日本語CIDフォントを使用する。
    外部フォントファイル不要。
    """
    pdfmetrics.registerFont(
        UnicodeCIDFont("HeiseiKakuGo-W5")
    )
    pdfmetrics.registerFont(
        UnicodeCIDFont("HeiseiMin-W3")
    )


_register_fonts()

FONT = "HeiseiKakuGo-W5"
FONT_BOLD = "Helvetica-Bold"
MINCHO = "HeiseiMin-W3"


def _money(value: Any) -> str:
    if value is None:
        return "—"

    try:
        return f"{float(value):,.0f}円"
    except (TypeError, ValueError):
        return "—"


def _percent(value: Any) -> str:
    if value is None:
        return "—"

    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "—"


def _sign_money(value: Any) -> str:
    if value is None:
        return "—"

    try:
        number = float(value)
        sign = "+" if number > 0 else ""
        return f"{sign}{number:,.0f}円"
    except (TypeError, ValueError):
        return "—"


def _safe_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).replace("\n", "<br/>")


def _build_styles():
    """
    v2.0.2 typography:
      - Titles / headings / labels: Gothic
      - Body / explanatory text / table content: Mincho
      - Main readable text: approximately 10–11pt
    """
    styles = getSampleStyleSheet()

    return {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            fontName=FONT,
            fontSize=25,
            leading=34,
            textColor=MAIN_COLOR,
            alignment=TA_CENTER,
            spaceAfter=8 * mm,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            fontName=FONT,
            fontSize=19,
            leading=27,
            textColor=TITLE_COLOR,
            alignment=TA_CENTER,
            spaceAfter=12 * mm,
        ),
        "cover_label": ParagraphStyle(
            "CoverLabel",
            fontName=FONT,
            fontSize=10,
            leading=14,
            textColor=SUB_COLOR,
            alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "H1",
            fontName=FONT,
            fontSize=17,
            leading=23,
            textColor=MAIN_COLOR,
            spaceBefore=2 * mm,
            spaceAfter=5 * mm,
        ),
        "h2": ParagraphStyle(
            "H2",
            fontName=FONT,
            fontSize=12,
            leading=17,
            textColor=MAIN_COLOR,
            spaceBefore=3 * mm,
            spaceAfter=3 * mm,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName=MINCHO,
            fontSize=10.5,
            leading=17,
            textColor=TEXT_COLOR,
            spaceAfter=2.5 * mm,
        ),
        "small": ParagraphStyle(
            "Small",
            fontName=MINCHO,
            fontSize=10,
            leading=15,
            textColor=TEXT_COLOR,
        ),
        "small_muted": ParagraphStyle(
            "SmallMuted",
            fontName=MINCHO,
            fontSize=9.5,
            leading=14,
            textColor=MUTED_COLOR,
        ),
        "metric_value": ParagraphStyle(
            "MetricValue",
            fontName=MINCHO,
            fontSize=16,
            leading=21,
            textColor=MAIN_COLOR,
            alignment=TA_CENTER,
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel",
            fontName=FONT,
            fontSize=10,
            leading=13,
            textColor=MUTED_COLOR,
            alignment=TA_CENTER,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            fontName=FONT,
            fontSize=10,
            leading=13,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            fontName=MINCHO,
            fontSize=10,
            leading=14,
            textColor=TEXT_COLOR,
        ),
        "table_cell_center": ParagraphStyle(
            "TableCellCenter",
            fontName=MINCHO,
            fontSize=10,
            leading=14,
            textColor=TEXT_COLOR,
            alignment=TA_CENTER,
        ),
        "note": ParagraphStyle(
            "Note",
            fontName=MINCHO,
            fontSize=10,
            leading=15,
            textColor=MUTED_COLOR,
            backColor=LIGHT_BG,
            borderColor=GRID_COLOR,
            borderWidth=0.5,
            borderPadding=6,
            spaceBefore=2 * mm,
            spaceAfter=4 * mm,
        ),
        "candidate": ParagraphStyle(
            "Candidate",
            fontName=MINCHO,
            fontSize=10,
            leading=14,
            textColor=TEXT_COLOR,
        ),
        "improvement_title": ParagraphStyle(
            "ImprovementTitle",
            fontName=FONT,
            fontSize=12,
            leading=17,
            textColor=MAIN_COLOR,
            spaceBefore=2 * mm,
            spaceAfter=2 * mm,
        ),
        "improvement_body": ParagraphStyle(
            "ImprovementBody",
            fontName=MINCHO,
            fontSize=10,
            leading=15,
            textColor=TEXT_COLOR,
        ),
        "improvement_label": ParagraphStyle(
            "ImprovementLabel",
            fontName=FONT,
            fontSize=9.5,
            leading=13,
            textColor=SUB_COLOR,
        ),
    }


STYLES = _build_styles()


class HPBReportDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(
            filename,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=17 * mm,
            bottomMargin=16 * mm,
            **kwargs,
        )

        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
        )

        self.addPageTemplates(
            [
                PageTemplate(
                    id="hpb",
                    frames=frame,
                    onPage=self._draw_page,
                )
            ]
        )

    def _draw_page(self, canvas, doc):
        canvas.saveState()

        width, height = A4

        canvas.setFillColor(MAIN_COLOR)
        canvas.rect(
            0,
            height - 4 * mm,
            width,
            4 * mm,
            stroke=0,
            fill=1,
        )

        canvas.setFont(FONT, 6.5)
        canvas.setFillColor(MUTED_COLOR)

        canvas.drawString(
            15 * mm,
            8 * mm,
            "ちゃぴおHPB Toolkit",
        )

        canvas.drawRightString(
            width - 15 * mm,
            8 * mm,
            f"{doc.page} ページ",
        )

        canvas.restoreState()


def _section_title(text: str):
    return Paragraph(
        text,
        STYLES["h1"],
    )


def _sub_title(text: str):
    return Paragraph(
        text,
        STYLES["h2"],
    )


def _note(text: str):
    return Paragraph(
        _safe_text(text),
        STYLES["note"],
    )


def _metric_table(items: List[tuple]) -> Table:
    cells = []

    for label, value in items:
        cells.append(
            [
                Paragraph(
                    str(value),
                    STYLES["metric_value"],
                ),
                Paragraph(
                    str(label),
                    STYLES["metric_label"],
                ),
            ]
        )

    table = Table(
        [cells],
        colWidths=[
            44 * mm
            for _ in cells
        ],
        rowHeights=[26 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_BG,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    GRID_COLOR,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    GRID_COLOR,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    return table


def _make_table(
    data: List[List[Any]],
    widths: List[float],
    header: bool = True,
    small: bool = False,
) -> Table:
    converted = []

    for row_index, row in enumerate(data):
        converted_row = []

        for value in row:
            if isinstance(value, Paragraph):
                converted_row.append(value)
                continue

            style = (
                STYLES["table_header"]
                if header and row_index == 0
                else (
                    STYLES["table_cell"]
                    if small
                    else STYLES["table_cell"]
                )
            )

            converted_row.append(
                Paragraph(
                    _safe_text(value),
                    style,
                )
            )

        converted.append(converted_row)

    # A4本文フレームは左右15mmマージンのため幅180mm。
    # 指定幅の合計がこれを超える表は比例縮小して右端のはみ出しを防ぐ。
    available_width = 180 * mm
    total_width = sum(widths)

    if total_width > available_width:
        scale = available_width / total_width
        widths = [
            width * scale
            for width in widths
        ]

    table = Table(
        converted,
        colWidths=widths,
        repeatRows=1 if header else 0,
        hAlign="LEFT",
    )

    style_commands = [
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.35,
            GRID_COLOR,
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
    ]

    if header:
        style_commands.extend(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    MAIN_COLOR,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    WHITE,
                ),
            ]
        )

        for row_index in range(1, len(converted)):
            if row_index % 2 == 0:
                style_commands.append(
                    (
                        "BACKGROUND",
                        (0, row_index),
                        (-1, row_index),
                        colors.HexColor("#FCF8FA"),
                    )
                )

    table.setStyle(
        TableStyle(style_commands)
    )

    return table


def _candidate_items(
    candidates: Dict[str, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    seen = set()
    items = []

    groups = [
        ("店舗全体の統計的外れ値候補", candidates.get("outliers", [])),
        ("カテゴリ別の統計的外れ値候補", candidates.get("category_outliers", [])),
        ("低価格要確認", candidates.get("low_price_attention", [])),
        ("高価格要確認", candidates.get("high_price_attention", [])),
    ]

    for label, group in groups:
        for item in group:
            coupon_name = item.get(
                "coupon_name",
                "クーポン名不明",
            )
            price = item.get("price")

            key = (
                coupon_name,
                price,
                item.get("category", ""),
            )

            if key in seen:
                continue

            seen.add(key)

            items.append(
                {
                    "group": label,
                    **item,
                }
            )

    return items


def _split_cover_shop_name(shop_name: str) -> tuple[str, str]:
    """
    表紙店舗名を英字ブランド部分と日本語/その他部分に分離する。
    1行表示を前提とし、英字部分だけゴシック、日本語部分は明朝で描画する。
    """
    import re

    text = _safe_text(shop_name).strip()

    # 英字ブランド部分が先頭にあるケースを優先。
    match = re.match(
        r"^([A-Za-z][A-Za-z0-9&' .\-]*?)(?=\s*[ぁ-んァ-ヶ一-龯]|[（(])",
        text,
    )

    if match:
        english = match.group(1).strip()
        japanese = text[match.end():].strip()
        return english, japanese

    # 先頭が英字だけで終わる名称にも対応。
    match = re.match(
        r"^([A-Za-z][A-Za-z0-9&' .\-]+)(?:\s+)(.+)$",
        text,
    )

    if match:
        english = match.group(1).strip()
        japanese = match.group(2).strip()
        return english, japanese

    return "", text


def _cover_shop_name_paragraph(shop_name: str) -> Paragraph:
    """
    店舗名を1行のまま、英字=ゴシック、日本語=明朝で描画する。
    """
    english, japanese = _split_cover_shop_name(shop_name)

    # 英字・日本語を同じベースサイズで組み、
    # 英字だけ太めのゴシックにする。
    if english:
        markup = (
            f'<font name="{FONT_BOLD}">{escape(english)}</font>'
            f' <font name="{MINCHO}">{escape(japanese)}</font>'
            ' <font name="HeiseiMin-W3">様</font>'
        )
    else:
        markup = (
            f'<font name="{MINCHO}">{escape(japanese)}</font>'
            ' <font name="HeiseiMin-W3">様</font>'
        )

    style = ParagraphStyle(
        "CoverShopMixedV206",
        parent=STYLES["cover_title"],
        fontName=MINCHO,
        fontSize=24,
        leading=31,
        textColor=MAIN_COLOR,
        alignment=TA_CENTER,
        spaceAfter=5 * mm,
        wordWrap="CJK",
    )

    return Paragraph(markup, style)


def _build_cover(report_data: Dict[str, Any]) -> List[Any]:
    """
    v2.0.1 表紙。
    店舗名を最も大きく表示し、その下に
    HOTPEPPER Beauty分析レポートを配置する。
    """
    primary = report_data["primary_shop"]
    summary = primary["summary"]

    shop_name = _safe_text(summary["name"])
    comparison_shops = report_data.get(
        "comparison_shops",
        [],
    )

    comparison_names = [
        _safe_text(shop["name"])
        for shop in comparison_shops
    ]

    # ---------------------------------------------------------
    # 表紙用の専用スタイル
    # ---------------------------------------------------------
    cover_shop_style = ParagraphStyle(
        "CoverShopNameV201",
        parent=STYLES["cover_title"],
        fontName=FONT,
        fontSize=27,
        leading=35,
        textColor=MAIN_COLOR,
        alignment=TA_CENTER,
        spaceAfter=5 * mm,
    )

    cover_report_style = ParagraphStyle(
        "CoverReportTitleV201",
        parent=STYLES["cover_title"],
        fontName=FONT,
        fontSize=20,
        leading=28,
        textColor=TITLE_COLOR,
        alignment=TA_CENTER,
        spaceAfter=10 * mm,
    )

    cover_section_label = ParagraphStyle(
        "CoverSectionLabelV201",
        fontName=FONT,
        fontSize=10,
        leading=14,
        textColor=SUB_COLOR,
        alignment=TA_LEFT,
    )

    cover_shop_cell = ParagraphStyle(
        "CoverShopCellV201",
        fontName=MINCHO,
        fontSize=10.5,
        leading=16,
        textColor=TEXT_COLOR,
        alignment=TA_LEFT,
    )

    cover_meta = ParagraphStyle(
        "CoverMetaV201",
        fontName=MINCHO,
        fontSize=7.5,
        leading=11,
        textColor=MUTED_COLOR,
        alignment=TA_CENTER,
    )

    # ---------------------------------------------------------
    # 店舗情報パネル
    # ---------------------------------------------------------
    comparison_text = (
        "<br/>".join(
            f"・{name}"
            for name in comparison_names
        )
        if comparison_names
        else "・比較対象店舗なし"
    )

    target_table = Table(
        [
            [
                Paragraph(
                    "分析対象店舗",
                    cover_section_label,
                ),
                Paragraph(
                    shop_name,
                    cover_shop_cell,
                ),
            ],
            [
                Paragraph(
                    "比較対象店舗",
                    cover_section_label,
                ),
                Paragraph(
                    comparison_text,
                    cover_shop_cell,
                ),
            ],
        ],
        colWidths=[
            42 * mm,
            118 * mm,
        ],
        hAlign="CENTER",
    )

    target_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#FCF8FA"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    GRID_COLOR,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    GRID_COLOR,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    LIGHT_BG,
                ),
            ]
        )
    )

    story = [
        Spacer(1, 23 * mm),

        # 主タイトル：店舗名
        _cover_shop_name_paragraph(shop_name),

        # レポートタイトル
        Paragraph(
            "HOTPEPPER Beauty分析レポート",
            cover_report_style,
        ),

        Spacer(1, 5 * mm),

        # 対象店舗情報
        target_table,

        Spacer(1, 14 * mm),

        Paragraph(
            f"作成日時："
            f"{report_data['created_at'].strftime('%Y年%m月%d日 %H:%M')}",
            cover_meta,
        ),
        Paragraph(
            f"レポートバージョン：{report_data['version']}",
            cover_meta,
        ),

        Spacer(1, 12 * mm),

        _note(
            "本レポートは「自店舗」を主対象とし、比較対象店舗は市場・参考情報として扱います。"
            "比較対象店舗そのものを評価することを目的とせず、"
            "自店舗の現状把握と価格検討に利用する構成です。"
        ),

        PageBreak(),
    ]

    return story


def _build_primary_overview(report_data: Dict[str, Any]) -> List[Any]:
    primary = report_data["primary_shop"]
    summary = primary["summary"]
    pricing = primary["pricing"]

    reference_price = pricing.get(
        "market_reference_price"
    )

    if reference_price is None:
        reference_price = pricing.get(
            "comparison_median"
        )

    story = [
        _section_title(
            "1. 自店舗の現状"
        ),
        Paragraph(
            f"分析対象：<b>{_safe_text(summary['name'])}</b>",
            STYLES["body"],
        ),
        _metric_table(
            [
                (
                    "取得クーポン数",
                    f"{summary['coupon_count']}件",
                ),
                (
                    "有効価格データ",
                    f"{summary['valid_price_count']}件",
                ),
                (
                    "自店舗中央値",
                    _money(summary["median"]),
                ),
                (
                    "市場参考価格",
                    _money(reference_price),
                ),
            ]
        ),
        Spacer(1, 6 * mm),
    ]

    position = pricing.get(
        "position",
        "比較不可",
    )

    ratio = pricing.get("ratio")
    difference = pricing.get("difference")

    overview_data = [
        ["項目", "自店舗", "市場・比較基準"],
        [
            "平均価格",
            _money(summary["average"]),
            _money(pricing.get("comparison_average")),
        ],
        [
            "中央値",
            _money(summary["median"]),
            _money(pricing.get("comparison_median")),
        ],
        [
            "価格差",
            _sign_money(difference),
            "自店舗中央値 − 比較店舗中央値",
        ],
        [
            "価格対比率",
            _percent(ratio),
            "比較店舗中央値を100%とした場合",
        ],
        [
            "価格ポジション",
            position,
            pricing.get(
                "comparison_method",
                "",
            ),
        ],
        [
            "参考度",
            pricing.get(
                "reference_level",
                "比較不可",
            ),
            pricing.get(
                "reference_reason",
                "",
            ),
        ],
    ]

    story.extend(
        [
            _make_table(
                overview_data,
                [
                    38 * mm,
                    45 * mm,
                    92 * mm,
                ],
            ),
            Spacer(1, 5 * mm),
            _note(
                "市場参考価格は比較対象店舗ごとの価格中央値を同じ重みで比較して算出しています。"
                "比較店舗数や有効クーポン数が少ない場合は、参考度が低くなる設計です。"
            ),
            PageBreak(),
        ]
    )

    return story


def _build_comparison_section(report_data: Dict[str, Any]) -> List[Any]:
    comparisons = report_data.get(
        "comparison_shops",
        [],
    )

    story = [
        _section_title(
            "2. 市場・比較対象の位置づけ"
        ),
        Paragraph(
            "比較対象店舗は、自店舗の価格水準を確認するための市場・参考情報として整理しています。",
            STYLES["body"],
        ),
    ]

    if not comparisons:
        story.extend(
            [
                _note(
                    "比較対象店舗が設定されていないため、市場比較は実施していません。"
                ),
                PageBreak(),
            ]
        )
        return story

    data = [
        [
            "比較対象店舗",
            "クーポン数",
            "有効価格",
            "平均",
            "中央値",
            "カテゴリ数",
        ]
    ]

    for shop in comparisons:
        data.append(
            [
                shop["name"],
                f"{shop['coupon_count']}件",
                f"{shop['valid_price_count']}件",
                _money(shop["average"]),
                _money(shop["median"]),
                f"{shop['category_count']}",
            ]
        )

    story.extend(
        [
            _make_table(
                data,
                [
                    58 * mm,
                    23 * mm,
                    23 * mm,
                    27 * mm,
                    27 * mm,
                    22 * mm,
                ],
                small=True,
            ),
            Spacer(1, 5 * mm),
            _note(
                "上表は比較対象店舗の観測値です。比較対象店舗は自店舗の分析基準として利用し、"
                "各店舗を個別の主分析対象として評価する構成にはしていません。"
            ),
            PageBreak(),
        ]
    )

    return story


def _build_category_section(report_data: Dict[str, Any]) -> List[Any]:
    primary = report_data["primary_shop"]
    rows = primary.get(
        "category_rows",
        [],
    )
    comparisons = report_data.get(
        "comparison_shops",
        [],
    )

    story = [
        _section_title(
            "3. カテゴリ別価格比較"
        ),
        Paragraph(
            "自店舗のカテゴリ別価格を中心に、比較対象店舗と市場参考価格を横並びで確認します。",
            STYLES["body"],
        ),
    ]

    if not rows:
        story.extend(
            [
                _note(
                    "カテゴリ別価格分析データがありません。"
                ),
                PageBreak(),
            ]
        )
        return story

    # 比較店舗名が多い場合でも、表が横に広がりすぎないよう
    # 比較店舗の中央値は別行でまとめる。
    header = [
        "カテゴリ",
        "自店舗件数",
        "自店舗中央値",
        "市場参考",
        "ポジション",
        "参考度",
    ]

    data = [header]

    for row in rows:
        data.append(
            [
                row["category"],
                f"{row['primary_coupon_count']}件",
                _money(row["primary_median"]),
                _money(row["market_reference_price"]),
                row["position"],
                row["reference_level"],
            ]
        )

    story.extend(
        [
            _make_table(
                data,
                [
                    63 * mm,
                    22 * mm,
                    31 * mm,
                    29 * mm,
                    32 * mm,
                    18 * mm,
                ],
                small=True,
            ),
            Spacer(1, 5 * mm),
        ]
    )

    # 詳細比較
    story.append(
        _sub_title(
            "カテゴリ別の比較店舗内訳"
        )
    )

    for row in rows:
        comparison_stores = row.get(
            "comparison_stores",
            [],
        )

        if not comparison_stores:
            continue

        detail = [
            [
                "カテゴリ",
                "比較対象店舗",
                "件数",
                "中央値",
            ]
        ]

        for item in comparison_stores:
            detail.append(
                [
                    row["category"],
                    item["shop_name"],
                    f"{item['coupon_count']}件",
                    _money(item["median"]),
                ]
            )

        story.append(
            _make_table(
                detail,
                [
                    58 * mm,
                    63 * mm,
                    22 * mm,
                    32 * mm,
                ],
                small=True,
            )
        )
        story.append(Spacer(1, 3 * mm))

    story.extend(
        [
            _note(
                "カテゴリは比較時に正規化し、カテゴリ順の違いや「その他」の付加による表記差を吸収しています。"
                "比較可能なカテゴリだけを市場参考価格の算出対象としています。"
            ),
            PageBreak(),
        ]
    )

    return story


def _build_review_section(report_data: Dict[str, Any]) -> List[Any]:
    primary = report_data["primary_shop"]
    candidates = primary.get(
        "review_candidates",
        {},
    )

    items = _candidate_items(candidates)

    story = [
        _section_title(
            "4. 営業確認候補"
        ),
        _note(
            "以下は価格の統計・閾値から機械的に抽出した候補です。"
            "異常価格と断定するものではなく、クーポン内容・利用条件・対象者条件などを"
            "営業担当者が確認するための一覧です。"
        ),
    ]

    if not items:
        story.extend(
            [
                Paragraph(
                    "営業確認候補はありません。",
                    STYLES["body"],
                ),
                PageBreak(),
            ]
        )
        return story

    data = [
        [
            "区分",
            "価格",
            "クーポン名",
            "カテゴリ",
            "判定理由",
        ]
    ]

    for item in items:
        data.append(
            [
                item["group"],
                _money(item.get("price")),
                item.get(
                    "coupon_name",
                    "クーポン名不明",
                ),
                item.get(
                    "category",
                    "",
                ),
                item.get(
                    "reason",
                    "",
                ),
            ]
        )

    story.extend(
        [
            _make_table(
                data,
                [
                    32 * mm,
                    22 * mm,
                    61 * mm,
                    48 * mm,
                    32 * mm,
                ],
                small=True,
            ),
            Spacer(1, 5 * mm),
            _note(
                "特に高価格・低価格の候補は、施術内容や利用条件によって正当な価格である可能性があります。"
                "候補抽出結果だけを理由に価格変更を行わない前提です。"
            ),
            PageBreak(),
        ]
    )

    return story


def _build_comparison_characteristics(
    report_data: Dict[str, Any]
) -> List[Any]:
    comparisons = report_data.get(
        "comparison_shops",
        [],
    )

    story = [
        _section_title(
            "5. 比較対象店舗の観測特徴"
        ),
        Paragraph(
            "ここでは比較対象店舗について、取得データから確認できる事実を整理します。",
            STYLES["body"],
        ),
    ]

    if not comparisons:
        story.extend(
            [
                _note(
                    "比較対象店舗が設定されていません。"
                ),
                PageBreak(),
            ]
        )
        return story

    for shop in comparisons:
        categories = shop.get(
            "categories",
            {},
        )

        category_items = []

        for category, item in categories.items():
            category_items.append(
                (
                    category,
                    item.get("coupon_count", 0),
                    item.get("median"),
                )
            )

        category_items.sort(
            key=lambda x: (
                -x[1],
                x[0],
            )
        )

        category_text = " / ".join(
            f"{category} {count}件・中央値{_money(median_price)}"
            for category, count, median_price
            in category_items[:6]
        )

        story.extend(
            [
                _sub_title(
                    shop["name"]
                ),
                _make_table(
                    [
                        ["項目", "観測値"],
                        [
                            "クーポン数",
                            f"{shop['coupon_count']}件",
                        ],
                        [
                            "有効価格データ",
                            f"{shop['valid_price_count']}件",
                        ],
                        [
                            "平均価格",
                            _money(shop["average"]),
                        ],
                        [
                            "中央値",
                            _money(shop["median"]),
                        ],
                        [
                            "確認できた主なカテゴリ",
                            category_text or "なし",
                        ],
                    ],
                    [
                        55 * mm,
                        140 * mm,
                    ],
                    small=True,
                ),
                Spacer(1, 4 * mm),
            ]
        )

    story.extend(
        [
            _note(
                "この章は比較対象店舗の特徴を観測情報として整理したものです。"
                "比較対象店舗の施策を、そのまま自店舗に適用すべきという意味ではありません。"
            ),
            PageBreak(),
        ]
    )

    return story


def _build_improvement_section(
    report_data: Dict[str, Any]
) -> List[Any]:
    """
    v2.1.0 第6章。

    ImprovementAnalyzer が生成した「改善検討候補」をPDFへ整形する。
    現段階では具体的な変更を断定せず、
    「分析結果 → 確認ポイント → 次の確認行動」の順で表示する。
    """

    primary = report_data["primary_shop"]
    improvement = primary.get("improvement", {})

    proposals = improvement.get("proposals", [])
    summary = improvement.get(
        "summary",
        "改善検討候補を確認してください。",
    )
    limitations = improvement.get(
        "limitations",
        [],
    )

    story = [
        _section_title(
            "6. 自店舗への改善提案"
        ),
        Paragraph(
            "価格分析・カテゴリ比較・価格データ品質分析をもとに、"
            "自店舗で確認・改善を検討できるポイントを整理します。",
            STYLES["body"],
        ),
        _note(summary),
    ]

    if not proposals:
        story.extend(
            [
                _note(
                    "今回の分析データから明確な改善検討候補は抽出されませんでした。"
                    "比較店舗数や価格データの状況によっては、候補が出ない場合があります。"
                ),
            ]
        )
    else:
        for index, proposal in enumerate(proposals, start=1):
            title = proposal.get(
                "title",
                "改善検討候補",
            )
            category = proposal.get(
                "category",
                "—",
            )
            priority = proposal.get(
                "priority",
                "確認候補",
            )
            reason = proposal.get(
                "reason",
                "",
            )
            action = proposal.get(
                "action",
                "",
            )
            coupon_name = proposal.get(
                "coupon_name",
                "",
            )

            current_price = proposal.get(
                "current_price_display",
                _money(proposal.get("current_price")),
            )
            reference_price = proposal.get(
                "reference_price_display",
                _money(proposal.get("reference_price")),
            )

            title_text = f"{index}. {title}"

            story.append(
                Paragraph(
                    _safe_text(title_text),
                    STYLES["improvement_title"],
                )
            )

            meta = [
                [
                    "対象",
                    category,
                    "区分",
                    priority,
                ]
            ]

            if coupon_name:
                meta.append(
                    [
                        "クーポン",
                        coupon_name,
                        "価格",
                        current_price,
                    ]
                )
            else:
                meta.append(
                    [
                        "自店舗価格",
                        current_price,
                        "市場参考",
                        reference_price,
                    ]
                )

            converted = []
            for row in meta:
                converted.append(
                    [
                        Paragraph(
                            _safe_text(row[0]),
                            STYLES["improvement_label"],
                        ),
                        Paragraph(
                            _safe_text(row[1]),
                            STYLES["improvement_body"],
                        ),
                        Paragraph(
                            _safe_text(row[2]),
                            STYLES["improvement_label"],
                        ),
                        Paragraph(
                            _safe_text(row[3]),
                            STYLES["improvement_body"],
                        ),
                    ]
                )

            table = Table(
                converted,
                colWidths=[
                    22 * mm,
                    68 * mm,
                    22 * mm,
                    68 * mm,
                ],
                hAlign="LEFT",
            )

            table.setStyle(
                TableStyle(
                    [
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.35,
                            GRID_COLOR,
                        ),
                        (
                            "BACKGROUND",
                            (0, 0),
                            (0, -1),
                            LIGHT_BG,
                        ),
                        (
                            "BACKGROUND",
                            (2, 0),
                            (2, -1),
                            LIGHT_BG,
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP",
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),
                    ]
                )
            )

            story.extend(
                [
                    table,
                    Spacer(1, 2 * mm),
                ]
            )

            if reason:
                story.append(
                    Paragraph(
                        f"<b>分析理由：</b>{_safe_text(reason)}",
                        STYLES["improvement_body"],
                    )
                )

            if action:
                story.append(
                    Paragraph(
                        f"<b>確認ポイント：</b>{_safe_text(action)}",
                        STYLES["improvement_body"],
                    )
                )

            story.append(
                Spacer(1, 4 * mm)
            )

    if limitations:
        story.append(
            _sub_title(
                "本章の利用上の注意"
            )
        )

        for item in limitations:
            story.append(
                Paragraph(
                    "・" + _safe_text(item),
                    STYLES["small_muted"],
                )
            )

    story.extend(
        [
            Spacer(1, 3 * mm),
            _note(
                "今後はHPB運用ノウハウの知識ベースと接続し、"
                "ここで抽出した確認ポイントを、具体的なクーポン改善・"
                "掲載内容改善・ページ改善案へ発展させる予定です。"
            ),
            PageBreak(),
        ]
    )

    return story

def _build_method_section(
    report_data: Dict[str, Any]
) -> List[Any]:
    notes = report_data.get(
        "notes",
        [],
    )

    story = [
        _section_title(
            "7. 分析方法・注意事項"
        ),
        Paragraph(
            "本レポートで使用している価格分析の考え方を記載します。",
            STYLES["body"],
        ),
    ]

    methods = [
        "自店舗を主分析対象とし、比較対象店舗は市場・参考情報として扱います。",
        "比較店舗の価格は、店舗ごとの中央値を先に算出し、その店舗中央値を同じ重みで比較します。",
        "カテゴリ比較では、カテゴリ名の順序違いを正規化し、「その他」の付加による表記差を吸収します。",
        "市場参考価格は比較店舗の中央値を基準に、100円単位へ丸めて表示します。",
        "参考価格帯は市場参考価格の±5%を目安として算出します。",
        "価格データ品質分析のフラグは情報提供目的であり、該当価格を平均・中央値から自動除外しません。",
        "営業確認候補は統計的外れ値や価格閾値による機械的抽出であり、異常価格と断定しません。",
    ]

    for item in methods:
        story.append(
            Paragraph(
                "・" + _safe_text(item),
                STYLES["body"],
            )
        )

    story.append(
        Spacer(1, 4 * mm)
    )

    if notes:
        story.append(
            _sub_title(
                "レポート上の注意"
            )
        )

        for note in notes:
            story.append(
                Paragraph(
                    "・" + _safe_text(note),
                    STYLES["small_muted"],
                )
            )

    return story


def generate_pdf_report(
    report_data: Dict[str, Any],
    output_path: str | Path,
) -> Path:
    """
    v2.1.0 自店舗主役型PDFレポートを生成する。

    Parameters
    ----------
    report_data:
        main.py が作成したレポートデータ。
    output_path:
        PDF保存先。
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    doc = HPBReportDocTemplate(
        str(output_path)
    )

    story: List[Any] = []

    story.extend(
        _build_cover(report_data)
    )

    story.extend(
        _build_primary_overview(report_data)
    )

    story.extend(
        _build_comparison_section(report_data)
    )

    story.extend(
        _build_category_section(report_data)
    )

    story.extend(
        _build_review_section(report_data)
    )

    story.extend(
        _build_comparison_characteristics(
            report_data
        )
    )

    story.extend(
        _build_improvement_section(
            report_data
        )
    )

    story.extend(
        _build_method_section(
            report_data
        )
    )

    doc.build(story)

    return output_path
