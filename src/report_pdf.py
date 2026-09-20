from __future__ import annotations

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


VERSION = "v2.0.0"

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
            fontSize=13,
            leading=20,
            textColor=TITLE_COLOR,
            alignment=TA_CENTER,
            spaceAfter=14 * mm,
        ),
        "cover_label": ParagraphStyle(
            "CoverLabel",
            fontName=FONT,
            fontSize=9,
            leading=13,
            textColor=MUTED_COLOR,
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
            fontName=FONT,
            fontSize=9,
            leading=15,
            textColor=TEXT_COLOR,
            spaceAfter=2 * mm,
        ),
        "small": ParagraphStyle(
            "Small",
            fontName=FONT,
            fontSize=7.5,
            leading=11,
            textColor=TEXT_COLOR,
        ),
        "small_muted": ParagraphStyle(
            "SmallMuted",
            fontName=FONT,
            fontSize=7,
            leading=10,
            textColor=MUTED_COLOR,
        ),
        "metric_value": ParagraphStyle(
            "MetricValue",
            fontName=FONT,
            fontSize=17,
            leading=22,
            textColor=MAIN_COLOR,
            alignment=TA_CENTER,
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel",
            fontName=FONT,
            fontSize=7.5,
            leading=10,
            textColor=MUTED_COLOR,
            alignment=TA_CENTER,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            fontName=FONT,
            fontSize=7.5,
            leading=10,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            fontName=FONT,
            fontSize=7,
            leading=10,
            textColor=TEXT_COLOR,
        ),
        "table_cell_center": ParagraphStyle(
            "TableCellCenter",
            fontName=FONT,
            fontSize=7,
            leading=10,
            textColor=TEXT_COLOR,
            alignment=TA_CENTER,
        ),
        "note": ParagraphStyle(
            "Note",
            fontName=FONT,
            fontSize=7.5,
            leading=11,
            textColor=MUTED_COLOR,
            backColor=LIGHT_BG,
            borderColor=GRID_COLOR,
            borderWidth=0.5,
            borderPadding=5,
            spaceBefore=2 * mm,
            spaceAfter=4 * mm,
        ),
        "candidate": ParagraphStyle(
            "Candidate",
            fontName=FONT,
            fontSize=7.2,
            leading=10.5,
            textColor=TEXT_COLOR,
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


def _build_cover(report_data: Dict[str, Any]) -> List[Any]:
    primary = report_data["primary_shop"]
    summary = primary["summary"]

    story = [
        Spacer(1, 25 * mm),
        Paragraph(
            "ちゃぴおHPB Toolkit",
            STYLES["cover_title"],
        ),
        Paragraph(
            "自店舗クーポン分析レポート",
            STYLES["cover_subtitle"],
        ),
        Paragraph(
            "市場参考価格・カテゴリ比較・営業確認候補",
            STYLES["cover_subtitle"],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "分析対象店舗",
            STYLES["cover_label"],
        ),
        Spacer(1, 2 * mm),
        Paragraph(
            _safe_text(summary["name"]),
            ParagraphStyle(
                "CoverShop",
                parent=STYLES["cover_title"],
                fontSize=18,
                leading=25,
            ),
        ),
        Spacer(1, 6 * mm),
        Paragraph(
            "比較対象店舗",
            STYLES["cover_label"],
        ),
    ]

    comparison_shops = report_data.get(
        "comparison_shops",
        [],
    )

    if comparison_shops:
        comparison_names = "<br/>".join(
            _safe_text(shop["name"])
            for shop in comparison_shops
        )
    else:
        comparison_names = "なし"

    story.extend(
        [
            Paragraph(
                comparison_names,
                ParagraphStyle(
                    "CoverComparisons",
                    parent=STYLES["body"],
                    alignment=TA_CENTER,
                    fontSize=9,
                    leading=14,
                ),
            ),
            Spacer(1, 14 * mm),
            Paragraph(
                f"作成日時："
                f"{report_data['created_at'].strftime('%Y年%m月%d日 %H:%M')}",
                STYLES["cover_label"],
            ),
            Paragraph(
                f"レポートバージョン：{report_data['version']}",
                STYLES["cover_label"],
            ),
            Spacer(1, 14 * mm),
            _note(
                "本レポートは「自店舗」を主対象とし、比較対象店舗は市場・参考情報として扱います。"
                "比較対象店舗そのものを評価することを目的とせず、自店舗の現状把握と価格検討に利用する構成です。"
            ),
            PageBreak(),
        ]
    )

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
    primary = report_data["primary_shop"]
    pricing = primary["pricing"]
    rows = primary.get(
        "category_rows",
        [],
    )
    candidates = primary.get(
        "review_candidates",
        {},
    )

    story = [
        _section_title(
            "6. 自店舗の改善検討ポイント"
        ),
        Paragraph(
            "現時点では、取得データから確認できる価格面の改善検討ポイントを整理します。",
            STYLES["body"],
        ),
    ]

    position = pricing.get(
        "position",
        "比較不可",
    )

    reference = pricing.get(
        "market_reference_price"
    )

    if reference is None:
        reference = pricing.get(
            "comparison_median"
        )

    if reference is not None:
        story.append(
            _note(
                f"店舗全体では、自店舗中央値 {_money(pricing.get('shop_median'))} に対して、"
                f"市場参考価格は {_money(reference)} です。"
                f"現在の価格ポジションは「{position}」です。"
            )
        )

    lower_categories = [
        row
        for row in rows
        if row.get("position") == "中央値より安い"
        and row.get("market_reference_price") is not None
    ]

    higher_categories = [
        row
        for row in rows
        if row.get("position") == "中央値より高い"
        and row.get("market_reference_price") is not None
    ]

    if lower_categories:
        story.append(
            _sub_title(
                "価格差が確認できるカテゴリ"
            )
        )

        data = [
            [
                "カテゴリ",
                "自店舗中央値",
                "市場参考",
                "差額",
                "参考度",
            ]
        ]

        for row in lower_categories[:10]:
            data.append(
                [
                    row["category"],
                    _money(row["primary_median"]),
                    _money(row["market_reference_price"]),
                    _sign_money(row.get("difference")),
                    row["reference_level"],
                ]
            )

        story.append(
            _make_table(
                data,
                [
                    72 * mm,
                    30 * mm,
                    30 * mm,
                    30 * mm,
                    23 * mm,
                ],
                small=True,
            )
        )
        story.append(Spacer(1, 5 * mm))

    if higher_categories:
        story.append(
            _sub_title(
                "市場参考価格を上回っているカテゴリ"
            )
        )

        data = [
            [
                "カテゴリ",
                "自店舗中央値",
                "市場参考",
                "差額",
                "参考度",
            ]
        ]

        for row in higher_categories[:10]:
            data.append(
                [
                    row["category"],
                    _money(row["primary_median"]),
                    _money(row["market_reference_price"]),
                    _sign_money(row.get("difference")),
                    row["reference_level"],
                ]
            )

        story.append(
            _make_table(
                data,
                [
                    72 * mm,
                    30 * mm,
                    30 * mm,
                    30 * mm,
                    23 * mm,
                ],
                small=True,
            )
        )
        story.append(Spacer(1, 5 * mm))

    candidate_count = sum(
        len(value)
        for value in candidates.values()
    )

    if candidate_count:
        story.append(
            _note(
                f"価格データ品質分析では営業確認候補が{candidate_count}件抽出されています。"
                "まずはクーポン内容・利用条件を確認し、価格データそのものの妥当性を確認することが前提です。"
            )
        )

    story.extend(
        [
            _note(
                "今後のバージョンでは、この章をHPB運用ノウハウの知識ベースとAI分析に接続し、"
                "『現状 → 根拠 → 改善案 → 掲載文面案』まで一連で出力できる構成へ拡張します。"
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
    v2.0.0 自店舗主役型PDFレポートを生成する。

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
