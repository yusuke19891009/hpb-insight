from __future__ import annotations

from xml.sax.saxutils import escape

from pathlib import Path
from typing import Any, Dict, List

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
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


VERSION = "v2.3.1"

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
    タイポグラフィ設定。
      - タイトル / 見出し / ラベル：ゴシック
      - 本文 / 説明文 / 表：明朝
      - 本文は10～11pt程度
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
                else STYLES["table_cell"]
            )

            converted_row.append(
                Paragraph(
                    _safe_text(value),
                    style,
                )
            )

        converted.append(converted_row)

    # A4本文フレームは左右15mmマージンのため幅180mm。
    # 指定幅の合計がこれを超える場合は比例縮小。
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
        (
            "店舗全体の統計的外れ値候補",
            candidates.get("outliers", []),
        ),
        (
            "カテゴリ別の統計的外れ値候補",
            candidates.get("category_outliers", []),
        ),
        (
            "低価格要確認",
            candidates.get("low_price_attention", []),
        ),
        (
            "高価格要確認",
            candidates.get("high_price_attention", []),
        ),
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
    """

    import re

    text = _safe_text(shop_name).strip()

    match = re.match(
        r"^([A-Za-z][A-Za-z0-9&' .\-]*?)(?=\s*[ぁ-んァ-ヶ一-龯]|[（(])",
        text,
    )

    if match:
        english = match.group(1).strip()
        japanese = text[match.end():].strip()
        return english, japanese

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
    店舗名を1行のまま、
    英字＝ゴシック、日本語＝明朝で描画する。
    """

    english, japanese = _split_cover_shop_name(shop_name)

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
        "CoverShopMixedV231",
        parent=STYLES["cover_title"],
        fontName=MINCHO,
        fontSize=24,
        leading=31,
        textColor=MAIN_COLOR,
        alignment=TA_CENTER,
        spaceAfter=5 * mm,
        wordWrap="CJK",
    )

    return Paragraph(
        markup,
        style,
    )


def _build_cover(
    report_data: Dict[str, Any]
) -> List[Any]:
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

    cover_report_style = ParagraphStyle(
        "CoverReportTitleV231",
        parent=STYLES["cover_title"],
        fontName=FONT,
        fontSize=20,
        leading=28,
        textColor=TITLE_COLOR,
        alignment=TA_CENTER,
        spaceAfter=10 * mm,
    )

    cover_section_label = ParagraphStyle(
        "CoverSectionLabelV231",
        fontName=FONT,
        fontSize=10,
        leading=14,
        textColor=SUB_COLOR,
        alignment=TA_LEFT,
    )

    cover_shop_cell = ParagraphStyle(
        "CoverShopCellV231",
        fontName=MINCHO,
        fontSize=10.5,
        leading=16,
        textColor=TEXT_COLOR,
        alignment=TA_LEFT,
    )

    cover_meta = ParagraphStyle(
        "CoverMetaV231",
        fontName=MINCHO,
        fontSize=7.5,
        leading=11,
        textColor=MUTED_COLOR,
        alignment=TA_CENTER,
    )

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

        _cover_shop_name_paragraph(
            shop_name
        ),

        Paragraph(
            "HOTPEPPER Beauty分析レポート",
            cover_report_style,
        ),

        Spacer(1, 5 * mm),

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


def _build_primary_overview(
    report_data: Dict[str, Any]
) -> List[Any]:

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

    ratio = pricing.get(
        "ratio"
    )

    difference = pricing.get(
        "difference"
    )

    overview_data = [
        [
            "項目",
            "自店舗",
            "市場・比較基準",
        ],
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


def _build_comparison_section(
    report_data: Dict[str, Any]
) -> List[Any]:

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


def _build_category_section(
    report_data: Dict[str, Any]
) -> List[Any]:

    primary = report_data["primary_shop"]

    rows = primary.get(
        "category_rows",
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

        story.append(
            Spacer(1, 3 * mm)
        )

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


def _build_review_section(
    report_data: Dict[str, Any]
) -> List[Any]:

    primary = report_data["primary_shop"]

    candidates = primary.get(
        "review_candidates",
        {},
    )

    items = _candidate_items(
        candidates
    )

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
    """
    第5章：比較対象店舗の観測特徴。

    比較対象店舗について、
    クーポン数・価格データ・平均価格・中央値に加えて、
    確認できたカテゴリを一覧表で整理する。

    v2.3.1:
      - カテゴリを1つの文章に連結しない
      - 「カテゴリ / 件数 / 中央値」の独立した表にする
      - 長いカテゴリ名はParagraphの自動折り返しを利用する
    """

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

        # -----------------------------------------------------
        # 店舗の基本情報
        # -----------------------------------------------------

        story.append(
            _sub_title(
                shop["name"]
            )
        )

        summary_data = [
            [
                "項目",
                "観測値",
            ],
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
        ]

        story.append(
            _make_table(
                summary_data,
                [
                    55 * mm,
                    140 * mm,
                ],
                small=True,
            )
        )

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

        # -----------------------------------------------------
        # カテゴリ別一覧
        # -----------------------------------------------------

        category_items = []

        for category, item in categories.items():

            if not isinstance(item, dict):
                continue

            count = item.get(
                "coupon_count",
                0,
            )

            median_price = item.get(
                "median"
            )

            category_items.append(
                (
                    category,
                    count,
                    median_price,
                )
            )

        # 件数が多いカテゴリを上に表示。
        # 同数の場合はカテゴリ名順。
        category_items.sort(
            key=lambda x: (
                -int(x[1] or 0),
                str(x[0]),
            )
        )

        if category_items:

            story.append(
                Paragraph(
                    "確認できた主なカテゴリ",
                    STYLES["improvement_title"],
                )
            )

            category_data = [
                [
                    "カテゴリ",
                    "件数",
                    "中央値",
                ]
            ]

            # 既存仕様に合わせて上位6カテゴリを表示。
            for category, count, median_price in category_items[:6]:

                category_data.append(
                    [
                        category,
                        f"{count}件",
                        _money(median_price),
                    ]
                )

            category_table = _make_table(
                category_data,
                [
                    113 * mm,
                    27 * mm,
                    40 * mm,
                ],
                small=True,
            )

            # 件数・中央値を中央寄せ。
            category_table.setStyle(
                TableStyle(
                    [
                        (
                            "ALIGN",
                            (1, 1),
                            (-1, -1),
                            "CENTER",
                        ),
                    ]
                )
            )

            story.append(
                category_table
            )

        else:

            story.append(
                _note(
                    "確認できたカテゴリはありません。"
                )
            )

        story.append(
            Spacer(
                1,
                5 * mm,
            )
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
    第6章。

    自店舗の価格・カテゴリ・クーポン内容から、
    「改善を断定する」のではなく、
    「確認するポイント」を整理する。
    """

    improvement = report_data.get(
        "improvement",
        {}
    )

    proposals = improvement.get(
        "proposals",
        []
    )

    summary = improvement.get(
        "summary",
        ""
    )

    limitations = improvement.get(
        "limitations",
        []
    )

    story: List[Any] = [
        _section_title(
            "6. 自店舗への改善検討候補"
        ),

        Paragraph(
            "価格やクーポン内容を見て、確認しておきたいポイントを整理しています。",
            STYLES["body"],
        ),
    ]

    if summary:
        story.append(
            _note(
                _safe_text(summary)
            )
        )

    if not proposals:
        story.extend(
            [
                Paragraph(
                    "今回の分析では、特に確認が必要な候補は抽出されませんでした。",
                    STYLES["body"],
                ),
                PageBreak(),
            ]
        )

        return story

    for index, proposal in enumerate(
        proposals,
        start=1,
    ):

        title = _safe_text(
            proposal.get(
                "title",
                f"確認候補 {index}",
            )
        )

        category = _safe_text(
            proposal.get(
                "category",
                "",
            )
        )

        reason = _safe_text(
            proposal.get(
                "reason",
                "",
            )
        )

        detail = _safe_text(
            proposal.get(
                "detail",
                "",
            )
        )

        action = _safe_text(
            proposal.get(
                "action",
                "",
            )
        )

        current = proposal.get(
            "current_price"
        )

        reference = proposal.get(
            "reference_price"
        )

        story.append(
            Paragraph(
                f"{index}. {title}",
                STYLES["h2"],
            )
        )

        if category:
            story.append(
                Paragraph(
                    f"<b>カテゴリ：</b>{category}",
                    STYLES["improvement_body"],
                )
            )

        if (
            current is not None
            or reference is not None
        ):

            price_text = ""

            if current is not None:
                price_text += (
                    f"自店舗 {current:,.0f}円"
                )

            if reference is not None:
                if price_text:
                    price_text += " / "

                price_text += (
                    f"比較店舗 {reference:,.0f}円"
                )

            story.append(
                Paragraph(
                    f"<b>価格：</b>{price_text}",
                    STYLES["improvement_body"],
                )
            )

        if reason:
            story.append(
                Paragraph(
                    f"<b>確認する理由：</b>{reason}",
                    STYLES["improvement_body"],
                )
            )

        if detail:
            story.append(
                Paragraph(
                    f"<b>内容：</b>{detail}",
                    STYLES["improvement_body"],
                )
            )

        if action:
            story.append(
                Paragraph(
                    f"<b>確認ポイント：</b>{action}",
                    STYLES["improvement_body"],
                )
            )

        story.append(
            Spacer(
                1,
                4 * mm
            )
        )

    if limitations:

        story.append(
            _sub_title(
                "この章を見るときの注意"
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
            Spacer(
                1,
                3 * mm
            ),

            _note(
                "ここで挙げた内容は、変更を決めるためのものではなく、"
                "まず確認しておきたいポイントです。"
            ),

            PageBreak(),
        ]
    )

    return story


def _build_quantitative_section(
    report_data: Dict[str, Any]
) -> List[Any]:
    """
    第7章。

    自店舗HPB詳細レポートの数字から、
    店舗の特徴を分かりやすく整理する。
    """

    quantitative = (
        report_data.get(
            "quantitative"
        )
        or report_data.get(
            "primary_shop",
            {}
        ).get(
            "quantitative"
        )
    )

    if not quantitative:

        return [
            _section_title(
                "7. 自店舗の数字から分かる特徴"
            ),

            Paragraph(
                "自店舗のHPB詳細レポートPDFが指定されていないため、この章は生成していません。",
                STYLES["body"],
            ),

            _note(
                "HPB詳細レポートPDFを指定すると、PV・CVR・ACR・予約・売上・口コミなどの数字を確認できます。"
            ),

            PageBreak(),
        ]

    metrics = quantitative.get(
        "metrics",
        {}
    )

    summary = metrics.get(
        "summary",
        {}
    )

    reviews = metrics.get(
        "reviews",
        {}
    )

    listing = metrics.get(
        "listing",
        {}
    )

    coupon = metrics.get(
        "coupon",
        {}
    )

    analysis = quantitative.get(
        "analysis",
        {}
    )

    ai = quantitative.get(
        "ai_analysis"
    )

    story: List[Any] = [
        _section_title(
            "7. 自店舗の数字から分かる特徴"
        ),

        Paragraph(
            "HPB詳細レポートの数字から、店舗ページを見てもらえているか、クーポンを見てもらえているか、予約まで進んでいるかを確認します。",
            STYLES["body"],
        ),

        _note(
            f"解析対象："
            f"{metrics.get('source_file', 'HPB詳細レポートPDF')}"
            f" ／ "
            f"{metrics.get('page_count', '—')}ページ"
        ),
    ]

    metric_rows = [
        [
            "指標",
            "自店舗",
            "比較・基準",
        ],
        [
            "前月売上",
            (
                f"{summary.get('sales_man_yen', '—')}万円"
            ),
            "—",
        ],
        [
            "前月予約数",
            (
                f"{summary.get('reservations', '—')}件"
            ),
            (
                f"新規 {summary.get('new_reservations', '—')} / "
                f"リピート {summary.get('repeat_reservations', '—')}"
            ),
        ],
        [
            "PV",
            (
                f"{summary.get('top_pv', '—'):,}"
                if isinstance(
                    summary.get("top_pv"),
                    int,
                )
                else "—"
            ),
            (
                f"エリア同プラン "
                f"{summary.get('area_plan_pv', '—'):,}"
                if isinstance(
                    summary.get(
                        "area_plan_pv"
                    ),
                    int,
                )
                else "—"
            ),
        ],
        [
            "CVR",
            _percent(
                summary.get(
                    "cvr"
                )
            ),
            (
                "エリア同プラン "
                + _percent(
                    summary.get(
                        "area_plan_cvr"
                    )
                )
            ),
        ],
        [
            "ACR",
            _percent(
                summary.get(
                    "acr"
                )
            ),
            (
                "エリア同プラン "
                + _percent(
                    summary.get(
                        "area_plan_acr"
                    )
                )
            ),
        ],
        [
            "口コミ",
            (
                f"{reviews.get('count', '—')}件"
            ),
            (
                f"比較サロン平均 "
                f"{reviews.get('comparison_count', '—')}件"
            ),
        ],
        [
            "総合評点",
            reviews.get(
                "overall_score",
                "—",
            ),
            (
                f"比較サロン平均 "
                f"{reviews.get('comparison_overall_score', '—')}"
            ),
        ],
        [
            "掲載クーポン",
            (
                f"{listing.get('coupons', coupon.get('coupon_count', '—'))}件"
            ),
            (
                f"新規 {coupon.get('new_label_count', '—')} / "
                f"再来 {coupon.get('repeat_label_count', '—')} / "
                f"全員 {coupon.get('all_label_count', '—')}"
            ),
        ],
        [
            "スタイル",
            (
                f"{listing.get('styles', '—')}件"
            ),
            "—",
        ],
    ]

    story.append(
        _make_table(
            metric_rows,
            [
                43 * mm,
                45 * mm,
                92 * mm,
            ],
            small=True,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    story.append(
        _sub_title(
            "7-1. 数字から分かる特徴"
        )
    )

    insights = analysis.get(
        "insights",
        []
    )

    if insights:

        for item in insights:

            title = _safe_text(
                item.get(
                    "title",
                    "数字から分かること",
                )
            )

            text = _safe_text(
                item.get(
                    "text",
                    "",
                )
            )

            evidence = _safe_text(
                item.get(
                    "evidence",
                    "",
                )
            )

            story.append(
                Paragraph(
                    title,
                    STYLES["h2"],
                )
            )

            if text:
                story.append(
                    Paragraph(
                        text,
                        STYLES["body"],
                    )
                )

            if evidence:
                story.append(
                    Paragraph(
                        f"<b>数字：</b>{evidence}",
                        STYLES["small_muted"],
                    )
                )

            story.append(
                Spacer(
                    1,
                    2 * mm
                )
            )

    else:

        story.append(
            Paragraph(
                "今回のPDFからは、十分な分析コメントを作成できませんでした。",
                STYLES["body"],
            )
        )

    story.append(
        _sub_title(
            "7-2. PV・CVR・ACRの見方"
        )
    )

    definitions = [
        (
            "<b>PV（発見）</b>："
            "Hot Pepper Beautyで検索したお客様が、"
            "検索結果から店舗ページを開いた回数です。"
        ),
        (
            "<b>CVR（興味喚起）</b>："
            "店舗ページを見たお客様のうち、"
            "「クーポン・メニュー」を見た割合です。"
        ),
        (
            "<b>ACR（アクション）</b>："
            "「クーポン・メニュー」を見たお客様のうち、"
            "予約完了ページまで進んだ割合です。"
        ),
    ]

    for definition in definitions:

        story.append(
            Paragraph(
                definition,
                STYLES["body"],
            )
        )

    if ai:

        ai_text = ai.get(
            "text"
        )

        if ai_text:

            story.append(
                _sub_title(
                    "7-3. AIによる補足分析"
                )
            )

            story.append(
                Paragraph(
                    _safe_text(
                        ai_text
                    ),
                    STYLES["body"],
                )
            )

        elif ai.get(
            "error"
        ):

            story.append(
                _note(
                    "AI分析は利用できなかったため、"
                    "数字から作成した分析のみを掲載しています。"
                )
            )

    story.extend(
        [
            Spacer(
                1,
                3 * mm
            ),

            _note(
                "数字は店舗の状況を確認するための材料です。"
                "数字だけで原因を断定せず、クーポン内容・掲載内容・予約状況などと合わせて確認します。"
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
            "8. 分析方法・注意事項"
        ),

        Paragraph(
            "本レポートで使用している価格分析の考え方を記載します。",
            STYLES["body"],
        ),
    ]

    methods = [
        "自店舗を主分析対象とし、比較対象店舗は市場・参考情報として扱います。",
        "比較店舗の価格は、店舗ごとの中央値を先に算出し、その店舗中央値を同じ重みで比較します。",
        "カテゴリ比較では、カテゴリ名の順番の違いを整理して比較しています。",
        "市場参考価格は比較店舗の中央値を基準に、100円単位で表示しています。",
        "参考価格帯は市場参考価格の±5%を目安として算出しています。",
        "価格の確認候補は、価格の差や価格帯から確認が必要と思われるものを抽出しています。",
        "確認候補が出たことだけを理由に、価格変更やクーポン変更を行うものではありません。",
    ]

    for item in methods:

        story.append(
            Paragraph(
                "・" + _safe_text(item),
                STYLES["body"],
            )
        )

    story.append(
        Spacer(
            1,
            4 * mm
        )
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
    自店舗主役型PDFレポートを生成する。

    Parameters
    ----------
    report_data:
        main.py が作成したレポートデータ。

    output_path:
        PDF保存先。
    """

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    doc = HPBReportDocTemplate(
        str(output_path)
    )

    story: List[Any] = []

    story.extend(
        _build_cover(
            report_data
        )
    )

    story.extend(
        _build_primary_overview(
            report_data
        )
    )

    story.extend(
        _build_comparison_section(
            report_data
        )
    )

    story.extend(
        _build_category_section(
            report_data
        )
    )

    story.extend(
        _build_review_section(
            report_data
        )
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
        _build_quantitative_section(
            report_data
        )
    )

    story.extend(
        _build_method_section(
            report_data
        )
    )

    doc.build(
        story
    )

    return output_path