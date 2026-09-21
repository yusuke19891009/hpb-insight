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
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

VERSION = "v2.5.2"

MAIN_COLOR = colors.HexColor("#992854")
SUB_COLOR = colors.HexColor("#c18096")
TITLE_COLOR = colors.HexColor("#d5728d")
LIGHT_BG = colors.HexColor("#F8F1F4")
GRID_COLOR = colors.HexColor("#D9C3CC")
TEXT_COLOR = colors.HexColor("#333333")
MUTED_COLOR = colors.HexColor("#777777")
WHITE = colors.white
ROW_BG = colors.HexColor("#FCF8FA")


pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

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


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return escape(str(value).replace("\n", "<br/>"))


def _plain(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ").strip()


def _first(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def _customer_text(value: Any) -> str:
    """
    顧客向けPDFでは専門用語をそのまま表示しない。
    """
    text = _plain(value)

    replacements = {
        "IQR上限を上回っています":
            "同じカテゴリの他のクーポンと比べて、価格の差が大きいため確認候補です。",
        "IQR下限を下回っています":
            "同じカテゴリの他のクーポンと比べて、価格の差が大きいため確認候補です。",
        "IQR上限": "価格のばらつき",
        "IQR下限": "価格のばらつき",
        "統計的外れ値": "価格の差が大きい確認候補",
        "統計的な外れ値": "価格の差が大きい確認候補",
        "ファネル": "予約まで進む流れ",
        "相対的": "他の店舗と比べて",
        "定量的特徴": "数字から分かる特徴",
        "定量分析": "数字から見る分析",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def _styles():
    getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle", fontName=FONT, fontSize=24, leading=31,
            textColor=MAIN_COLOR, alignment=TA_CENTER, spaceAfter=5 * mm
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle", fontName=FONT, fontSize=20, leading=28,
            textColor=TITLE_COLOR, alignment=TA_CENTER, spaceAfter=10 * mm
        ),
        "cover_label": ParagraphStyle(
            "CoverLabel", fontName=FONT, fontSize=10, leading=14,
            textColor=SUB_COLOR, alignment=TA_LEFT
        ),
        "body": ParagraphStyle(
            "Body", fontName=MINCHO, fontSize=10.5, leading=17,
            textColor=TEXT_COLOR, spaceAfter=2.5 * mm
        ),
        "small": ParagraphStyle(
            "Small", fontName=MINCHO, fontSize=9.5, leading=14,
            textColor=TEXT_COLOR
        ),
        "small_muted": ParagraphStyle(
            "SmallMuted", fontName=MINCHO, fontSize=9.5, leading=14,
            textColor=MUTED_COLOR
        ),
        "h1": ParagraphStyle(
            "H1", fontName=FONT, fontSize=17, leading=23,
            textColor=MAIN_COLOR, spaceBefore=2 * mm, spaceAfter=5 * mm
        ),
        "h2": ParagraphStyle(
            "H2", fontName=FONT, fontSize=12, leading=17,
            textColor=MAIN_COLOR, spaceBefore=3 * mm, spaceAfter=3 * mm
        ),
        "metric_value": ParagraphStyle(
            "MetricValue", fontName=MINCHO, fontSize=16, leading=21,
            textColor=MAIN_COLOR, alignment=TA_CENTER
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel", fontName=FONT, fontSize=10, leading=13,
            textColor=MUTED_COLOR, alignment=TA_CENTER
        ),
        "table_header": ParagraphStyle(
            "TableHeader", fontName=FONT, fontSize=9.5, leading=13,
            textColor=WHITE, alignment=TA_CENTER
        ),
        "table_cell": ParagraphStyle(
            "TableCell", fontName=MINCHO, fontSize=9.5, leading=14,
            textColor=TEXT_COLOR
        ),
        "table_center": ParagraphStyle(
            "TableCenter", fontName=MINCHO, fontSize=9.5, leading=14,
            textColor=TEXT_COLOR, alignment=TA_CENTER
        ),
        "note": ParagraphStyle(
            "Note", fontName=MINCHO, fontSize=9.5, leading=14,
            textColor=MUTED_COLOR, backColor=LIGHT_BG,
            borderColor=GRID_COLOR, borderWidth=.5, borderPadding=6,
            spaceBefore=2 * mm, spaceAfter=4 * mm
        ),
        "card_title": ParagraphStyle(
            "CardTitle", fontName=FONT, fontSize=11.5, leading=16,
            textColor=MAIN_COLOR
        ),
        "card_label": ParagraphStyle(
            "CardLabel", fontName=FONT, fontSize=9.2, leading=13,
            textColor=SUB_COLOR
        ),
        "card_body": ParagraphStyle(
            "CardBody", fontName=MINCHO, fontSize=9.5, leading=14,
            textColor=TEXT_COLOR
        ),
    }


STYLES = _styles()


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
        self.addPageTemplates([
            PageTemplate(
                id="hpb",
                frames=frame,
                onPage=self._draw_page,
            )
        ])

    def _draw_page(self, canvas, doc):
        canvas.saveState()
        width, height = A4
        canvas.setFillColor(MAIN_COLOR)
        canvas.rect(0, height - 4 * mm, width, 4 * mm, stroke=0, fill=1)
        canvas.setFont(FONT, 6.5)
        canvas.setFillColor(MUTED_COLOR)
        canvas.drawString(15 * mm, 8 * mm, "ちゃぴおHPB Toolkit")
        canvas.drawRightString(
            width - 15 * mm, 8 * mm, f"{doc.page} ページ"
        )
        canvas.restoreState()


def _section_title(text: str):
    return Paragraph(_safe_text(text), STYLES["h1"])


def _sub_title(text: str):
    return Paragraph(_safe_text(text), STYLES["h2"])


def _note(text: str):
    return Paragraph(_safe_text(text), STYLES["note"])


def _metric_table(items: List[tuple]) -> Table:
    cells = []
    for label, value in items:
        cells.append([
            Paragraph(_safe_text(value), STYLES["metric_value"]),
            Paragraph(_safe_text(label), STYLES["metric_label"]),
        ])

    table = Table(
        [cells],
        colWidths=[44 * mm for _ in cells],
        rowHeights=[26 * mm],
        hAlign="CENTER",
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), .5, GRID_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), .5, GRID_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def _make_table(
    data: List[List[Any]],
    widths: List[float],
    header: bool = True,
    center_columns: Optional[List[int]] = None,
) -> Table:
    center_columns = center_columns or []
    converted = []

    for row_index, row in enumerate(data):
        converted_row = []
        for col_index, value in enumerate(row):
            if isinstance(value, Paragraph):
                converted_row.append(value)
                continue

            if header and row_index == 0:
                style = STYLES["table_header"]
            elif col_index in center_columns:
                style = STYLES["table_center"]
            else:
                style = STYLES["table_cell"]

            converted_row.append(
                Paragraph(_safe_text(value), style)
            )
        converted.append(converted_row)

    available = 180 * mm
    total = sum(widths)
    if total > available:
        scale = available / total
        widths = [x * scale for x in widths]

    table = Table(
        converted,
        colWidths=widths,
        repeatRows=1 if header else 0,
        hAlign="CENTER",
    )

    commands = [
        ("GRID", (0, 0), (-1, -1), .35, GRID_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]

    if header:
        commands.append(
            ("BACKGROUND", (0, 0), (-1, 0), MAIN_COLOR)
        )
        for i in range(1, len(converted)):
            if i % 2 == 0:
                commands.append(
                    ("BACKGROUND", (0, i), (-1, i), ROW_BG)
                )

    table.setStyle(TableStyle(commands))
    return table


def _card(
    title: str,
    fact: str,
    meaning: str,
    check: str,
) -> Table:
    rows = [
        [Paragraph(_safe_text(title), STYLES["card_title"])],
        [Paragraph("数字上の事実", STYLES["card_label"])],
        [Paragraph(_safe_text(_customer_text(fact)), STYLES["card_body"])],
        [Paragraph("分かること", STYLES["card_label"])],
        [Paragraph(_safe_text(_customer_text(meaning)), STYLES["card_body"])],
        [Paragraph("次に確認すること", STYLES["card_label"])],
        [Paragraph(_safe_text(_customer_text(check)), STYLES["card_body"])],
    ]

    table = Table(rows, colWidths=[176 * mm], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), .6, GRID_COLOR),
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
        ("BACKGROUND", (0, 1), (-1, 1), ROW_BG),
        ("BACKGROUND", (0, 3), (-1, 3), ROW_BG),
        ("BACKGROUND", (0, 5), (-1, 5), ROW_BG),
        ("LINEBELOW", (0, 0), (-1, 0), .4, GRID_COLOR),
        ("LINEBELOW", (0, 2), (-1, 2), .35, GRID_COLOR),
        ("LINEBELOW", (0, 4), (-1, 4), .35, GRID_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _primary(report_data):
    return report_data.get("primary_shop", {}) or {}


def _summary(report_data):
    return _primary(report_data).get("summary", {}) or {}


def _quantitative(report_data):
    p = _primary(report_data)
    return report_data.get("quantitative") or p.get("quantitative")


def _improvement(report_data):
    p = _primary(report_data)
    return report_data.get("improvement") or p.get("improvement") or {}


def _integrated(report_data):
    return (
        report_data.get("integrated_analysis")
        or report_data.get("integrated")
        or report_data.get("total_analysis")
        or {}
    )


# =============================================================
# 1. 表紙
# =============================================================

def _build_cover(report_data):
    primary = _primary(report_data)
    summary = primary.get("summary", {}) or {}
    shop_name = _plain(_first(summary, "name", "shop_name", default="自店舗"))

    comparisons = []
    for shop in report_data.get("comparison_shops", []) or []:
        if isinstance(shop, dict):
            name = _plain(_first(shop, "name", "shop_name", default=""))
            if name:
                comparisons.append(name)

    comparison_text = (
        "<br/>".join("・" + _safe_text(x) for x in comparisons)
        if comparisons else "・比較対象店舗なし"
    )

    target_table = Table(
        [
            [
                Paragraph("分析対象店舗", STYLES["cover_label"]),
                Paragraph(_safe_text(shop_name), STYLES["table_cell"]),
            ],
            [
                Paragraph("比較対象店舗", STYLES["cover_label"]),
                Paragraph(comparison_text, STYLES["table_cell"]),
            ],
        ],
        colWidths=[42 * mm, 118 * mm],
        hAlign="CENTER",
    )
    target_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), .35, GRID_COLOR),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    return [
        Spacer(1, 23 * mm),
        Paragraph(_safe_text(f"{shop_name} 様"), STYLES["cover_title"]),
        Paragraph("HOTPEPPER Beauty分析レポート", STYLES["cover_subtitle"]),
        Spacer(1, 5 * mm),
        target_table,
        Spacer(1, 12 * mm),
        Paragraph(
            f"作成日時：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
            STYLES["small_muted"],
        ),
        Paragraph(
            f"レポートバージョン：{VERSION}",
            STYLES["small_muted"],
        ),
        Spacer(1, 10 * mm),
        _note(
            "本レポートは「自店舗」を主対象とし、比較対象店舗は市場・参考情報として扱います。"
            "比較対象店舗そのものを評価することを目的とせず、自店舗の現状把握と価格検討に利用します。"
        ),
        PageBreak(),
    ]


# =============================================================
# 2. 自店舗の現状
# =============================================================

def _build_primary_overview(report_data):
    primary = _primary(report_data)
    summary = primary.get("summary", {}) or {}
    pricing = primary.get("pricing", {}) or {}

    reference = _first(
        pricing,
        "market_reference_price",
        "comparison_median",
    )

    story = [
        _section_title("1. 自店舗の現状"),
        Paragraph(
            f"分析対象：<b>{_safe_text(summary.get('name', '自店舗'))}</b>",
            STYLES["body"],
        ),
        _metric_table([
            ("取得クーポン数", f"{summary.get('coupon_count', '—')}件"),
            ("有効価格データ", f"{summary.get('valid_price_count', '—')}件"),
            ("平均価格", _money(summary.get("average"))),
            ("中央値", _money(summary.get("median"))),
        ]),
        Spacer(1, 5 * mm),
    ]

    ratio = pricing.get("ratio")
    position = "—"
    if ratio is not None:
        try:
            ratio_f = float(ratio)
            if ratio_f > 100:
                position = f"市場参考価格より{ratio_f - 100:.1f}%高い位置"
            elif ratio_f < 100:
                position = f"市場参考価格より{100 - ratio_f:.1f}%低い位置"
            else:
                position = "市場参考価格と同じ水準"
        except (TypeError, ValueError):
            pass

    data = [
        ["項目", "自店舗", "市場・比較基準"],
        ["市場参考価格", _money(reference), "比較店舗の中央値を基準"],
        ["自店舗の中央値", _money(summary.get("median")), position],
        [
            "参考価格帯",
            (
                f"{_money(pricing.get('reference_price_min'))} ～ "
                f"{_money(pricing.get('reference_price_max'))}"
            ),
            "市場参考価格の±5%を目安",
        ],
        [
            "市場との比較",
            f"{ratio_f:.1f}%" if "ratio_f" in locals() else "—",
            "100%より大きい＝自店舗の中央値が高い",
        ],
    ]

    story += [
        _make_table(data, [48 * mm, 55 * mm, 73 * mm], center_columns=[1]),
        _note(
            "市場参考価格は比較対象店舗ごとの価格中央値を同じ重みで比較して算出しています。"
            "比較店舗数や有効価格データが少ない場合は、参考として確認してください。"
        ),
        PageBreak(),
    ]
    return story


# =============================================================
# 3. 市場・カテゴリ比較
# =============================================================

def _build_comparison_section(report_data):
    comparisons = report_data.get("comparison_shops", []) or []

    story = [
        _section_title("2. 市場・比較対象の位置づけ"),
        Paragraph(
            "比較対象店舗は、自店舗の価格水準を確認するための市場・参考情報として整理しています。",
            STYLES["body"],
        ),
    ]

    if not comparisons:
        story += [
            _note("比較対象店舗が設定されていないため、市場比較は実施していません。"),
            PageBreak(),
        ]
        return story

    data = [["比較対象店舗", "クーポン数", "有効価格", "平均", "中央値", "カテゴリ数"]]
    for shop in comparisons:
        data.append([
            shop.get("name", "—"),
            f"{shop.get('coupon_count', '—')}件",
            f"{shop.get('valid_price_count', '—')}件",
            _money(shop.get("average")),
            _money(shop.get("median")),
            f"{shop.get('category_count', '—')}",
        ])

    story += [
        _make_table(
            data,
            [58 * mm, 23 * mm, 23 * mm, 27 * mm, 27 * mm, 22 * mm],
            center_columns=[1, 2, 3, 4, 5],
        ),
        _note(
            "上表は比較対象店舗の観測値です。比較対象店舗は自店舗の分析基準として利用し、"
            "各店舗を個別の主分析対象として評価する構成にはしていません。"
        ),
        PageBreak(),
    ]
    return story


def _build_category_section(report_data):
    primary = _primary(report_data)
    rows = primary.get("category_rows", []) or []

    story = [
        _section_title("3. カテゴリ別価格比較"),
        Paragraph(
            "自店舗のカテゴリ別価格を中心に、比較対象店舗と市場参考価格を横並びで確認します。",
            STYLES["body"],
        ),
    ]

    if not rows:
        story += [
            _note("カテゴリ別価格分析データがありません。"),
            PageBreak(),
        ]
        return story

    data = [[
        "カテゴリ", "自店舗件数", "自店舗中央値",
        "市場参考", "ポジション", "参考度"
    ]]

    for row in rows:
        data.append([
            row.get("category", "—"),
            f"{row.get('primary_coupon_count', row.get('primary_count', '—'))}件",
            _money(row.get("primary_median")),
            _money(row.get("market_reference_price")),
            row.get("position", "—"),
            row.get("reference_level", "—"),
        ])

    story += [
        _make_table(
            data,
            [63 * mm, 22 * mm, 31 * mm, 29 * mm, 32 * mm, 18 * mm],
            center_columns=[1, 2, 3, 4, 5],
        ),
        Spacer(1, 5 * mm),
        _sub_title("カテゴリ別の比較店舗内訳"),
    ]

    for row in rows:
        stores = row.get("comparison_stores", []) or []
        if not stores:
            continue

        detail = [["カテゴリ", "比較対象店舗", "件数", "中央値"]]
        for item in stores:
            detail.append([
                row.get("category", "—"),
                item.get("shop_name", "—"),
                f"{item.get('coupon_count', '—')}件",
                _money(item.get("median")),
            ])

        story += [
            _make_table(
                detail,
                [58 * mm, 63 * mm, 22 * mm, 32 * mm],
                center_columns=[2, 3],
            ),
            Spacer(1, 3 * mm),
        ]

    story += [
        _note(
            "カテゴリは比較時に正規化し、カテゴリ順の違いや「その他」の付加による表記差を整理しています。"
            "比較可能なカテゴリだけを市場参考価格の算出対象としています。"
        ),
        PageBreak(),
    ]
    return story


# =============================================================
# 4. 営業確認候補
# =============================================================

def _candidate_items(candidates):
    candidates = candidates or {}
    seen = set()
    result = []

    groups = [
        ("価格のばらつきから見た確認候補", candidates.get("outliers", [])),
        ("カテゴリ別の確認候補", candidates.get("category_outliers", [])),
        ("低価格の確認候補", candidates.get("low_price_attention", [])),
        ("高価格の確認候補", candidates.get("high_price_attention", [])),
    ]

    for label, items in groups:
        for item in items or []:
            key = (
                item.get("coupon_name"),
                item.get("price"),
                item.get("category"),
                label,
            )
            if key in seen:
                continue
            seen.add(key)
            result.append({"group": label, **item})

    return result


def _build_review_section(report_data):
    primary = _primary(report_data)
    candidates = primary.get("review_candidates", {}) or {}
    items = _candidate_items(candidates)

    story = [
        _section_title("4. 営業確認候補"),
        _note(
            "以下は価格の差や価格帯などから機械的に抽出した確認候補です。"
            "異常価格と断定するものではなく、クーポン内容・利用条件・対象者条件などを"
            "営業担当者が確認するための一覧です。"
        ),
    ]

    if not items:
        story += [
            Paragraph("営業確認候補はありません。", STYLES["body"]),
            PageBreak(),
        ]
        return story

    data = [["区分", "価格", "クーポン名", "カテゴリ", "判定理由"]]
    for item in items:
        data.append([
            _customer_text(item.get("group", "—")),
            _money(item.get("price")),
            _customer_text(item.get("coupon_name", "クーポン名不明")),
            _customer_text(item.get("category", "")),
            _customer_text(item.get("reason", "")),
        ])

    story += [
        _make_table(
            data,
            [36 * mm, 23 * mm, 57 * mm, 28 * mm, 36 * mm],
            center_columns=[1],
        ),
        _note(
            "確認候補が出たことだけを理由に、価格変更やクーポン変更を行うものではありません。"
        ),
        PageBreak(),
    ]
    return story


# =============================================================
# 5. 比較対象店舗の観測特徴
# =============================================================

def _build_comparison_characteristics(report_data):
    comparisons = report_data.get("comparison_shops", []) or []

    story = [
        _section_title("5. 比較対象店舗の観測特徴"),
        Paragraph(
            "ここでは比較対象店舗について、取得データから確認できる事実を整理します。",
            STYLES["body"],
        ),
    ]

    if not comparisons:
        story += [
            _note("比較対象店舗が設定されていません。"),
            PageBreak(),
        ]
        return story

    for shop in comparisons:
        categories = shop.get("categories", {}) or {}
        category_items = []

        for category, item in categories.items():
            if not isinstance(item, dict):
                continue
            category_items.append((
                category,
                item.get("coupon_count", 0),
                item.get("median"),
            ))

        category_items.sort(
            key=lambda x: (-int(x[1] or 0), str(x[0]))
        )

        story += [
            _sub_title(shop.get("name", "比較対象店舗")),
            _make_table(
                [
                    ["項目", "観測値"],
                    ["クーポン数", f"{shop.get('coupon_count', '—')}件"],
                    ["有効価格データ", f"{shop.get('valid_price_count', '—')}件"],
                    ["平均価格", _money(shop.get("average"))],
                    ["中央値", _money(shop.get("median"))],
                ],
                [55 * mm, 125 * mm],
            ),
            Spacer(1, 3 * mm),
        ]

        # ここを必ず表にする
        if category_items:
            story.append(
                Paragraph("確認できた主なカテゴリ", STYLES["card_title"])
            )

            category_data = [["カテゴリ", "件数", "中央値"]]
            for category, count, median in category_items[:6]:
                category_data.append([
                    category,
                    f"{count}件",
                    _money(median),
                ])

            story.append(
                _make_table(
                    category_data,
                    [110 * mm, 30 * mm, 30 * mm],
                    center_columns=[1, 2],
                )
            )
        else:
            story.append(_note("確認できたカテゴリはありません。"))

        story.append(Spacer(1, 5 * mm))

    story += [
        _note(
            "この章は比較対象店舗の特徴を観測情報として整理したものです。"
            "比較対象店舗の施策を、そのまま自店舗に適用すべきという意味ではありません。"
        ),
        PageBreak(),
    ]
    return story


# =============================================================
# 6. 自店舗への改善検討候補
# =============================================================

def _build_improvement_section(report_data):
    improvement = _improvement(report_data)
    proposals = improvement.get("proposals", []) or []
    summary = improvement.get("summary", "")
    limitations = improvement.get("limitations", []) or []

    story = [
        _section_title("6. 自店舗への改善検討候補"),
        Paragraph(
            "価格分析・カテゴリ比較・価格データの確認結果をもとに、"
            "自店舗で確認しておきたいポイントを整理します。",
            STYLES["body"],
        ),
    ]

    if summary:
        story.append(_note(_customer_text(summary)))

    if not proposals:
        story += [
            _note("今回の分析データから明確な改善検討候補は抽出されませんでした。"),
            PageBreak(),
        ]
        return story

    for index, proposal in enumerate(proposals, start=1):
        title = _first(
            proposal,
            "title",
            "name",
            default=f"改善検討候補{index}",
        )

        # v2.5.0 IntegratedAnalyzer形式を優先
        fact = _first(proposal, "fact", "numeric_fact", "evidence")
        meaning = _first(proposal, "meaning", "reason", "analysis_reason")
        check = _first(
            proposal,
            "check",
            "next_check",
            "action",
            "confirmation",
        )

        # ImprovementAnalyzer旧形式への互換
        if not fact:
            price = proposal.get("price")
            current = proposal.get("current_price")
            reference = proposal.get("reference_price")

            if current is not None or reference is not None:
                parts = []
                if current is not None:
                    parts.append(f"自店舗 {float(current):,.0f}円")
                if reference is not None:
                    parts.append(f"市場参考価格 {float(reference):,.0f}円")
                fact = " / ".join(parts) + "です。"
            elif price is not None:
                fact = f"対象クーポンの価格は{float(price):,.0f}円です。"
            else:
                fact = "価格分析から確認候補として抽出されています。"

        if not meaning:
            meaning = proposal.get("detail") or (
                "価格差や価格のばらつきを確認する入口として整理されています。"
            )

        if not check:
            check = proposal.get("action") or (
                "クーポン名・施術内容・所要時間・利用条件・対象者条件を確認します。"
            )

        story += [
            _card(
                _plain(title),
                _customer_text(fact),
                _customer_text(meaning),
                _customer_text(check),
            ),
            Spacer(1, 4 * mm),
        ]

    if limitations:
        story.append(_sub_title("この章を見るときの注意"))
        for item in limitations:
            story.append(
                Paragraph(
                    "・" + _safe_text(_customer_text(item)),
                    STYLES["small_muted"],
                )
            )

    story += [
        _note(
            "ここで挙げた内容は、変更を決めるためのものではなく、まず確認しておきたいポイントです。"
        ),
        PageBreak(),
    ]
    return story


# =============================================================
# 7. 自店舗の数字から分かる特徴
# =============================================================

def _comparison_word(current, reference):
    if current is None or reference is None:
        return "比較基準がないため、今回の数字だけでは比較できません。"
    try:
        c = float(current)
        r = float(reference)
    except (TypeError, ValueError):
        return "比較基準がないため、今回の数字だけでは比較できません。"

    if c > r:
        return "比較基準より高い数字です。"
    if c < r:
        return "比較基準より低い数字です。"
    return "比較基準と同程度です。"


def _build_quantitative_section(report_data):
    quantitative = _quantitative(report_data)

    story = [
        _section_title("7. 自店舗の数字から分かる特徴"),
        Paragraph(
            "自店舗のHPB詳細レポートから、数字上の事実・分かること・次に確認することを整理します。",
            STYLES["body"],
        ),
    ]

    if not quantitative:
        story += [
            _note(
                "自店舗のHPB詳細レポートPDFが指定されていないため、この章の数字は作成していません。"
            ),
            PageBreak(),
        ]
        return story

    metrics = quantitative.get("metrics", {}) or {}
    summary = metrics.get("summary", {}) or {}
    reviews = metrics.get("reviews", {}) or {}
    listing = metrics.get("listing", {}) or {}
    coupon = metrics.get("coupon", {}) or {}
    analysis = quantitative.get("analysis", {}) or {}

    story.append(
        _note(
            f"解析対象：{_customer_text(metrics.get('source_file', 'HPB詳細レポートPDF'))}"
            f" ／ {metrics.get('page_count', '—')}ページ"
        )
    )

    # 7-1 数字一覧
    metric_rows = [
        ["指標", "自店舗", "比較・基準"],
        [
            "前月売上",
            f"{summary.get('sales_man_yen', '—')}万円",
            "—",
        ],
        [
            "前月予約数",
            f"{summary.get('reservations', '—')}件",
            f"新規 {summary.get('new_reservations', '—')} / "
            f"リピート {summary.get('repeat_reservations', '—')}",
        ],
        [
            "PV（発見）",
            (
                f"{summary.get('top_pv'):,}"
                if isinstance(summary.get("top_pv"), (int, float))
                else "—"
            ),
            (
                f"エリア同プラン {summary.get('area_plan_pv'):,}"
                if isinstance(summary.get("area_plan_pv"), (int, float))
                else "—"
            ),
        ],
        [
            "CVR（興味喚起）",
            _percent(summary.get("cvr")),
            f"エリア同プラン {_percent(summary.get('area_plan_cvr'))}",
        ],
        [
            "ACR（アクション）",
            _percent(summary.get("acr")),
            f"エリア同プラン {_percent(summary.get('area_plan_acr'))}",
        ],
        [
            "口コミ",
            f"{reviews.get('count', '—')}件",
            f"比較サロン平均 {reviews.get('comparison_count', '—')}件",
        ],
        [
            "総合評点",
            reviews.get("overall_score", "—"),
            f"比較サロン平均 {reviews.get('comparison_overall_score', '—')}",
        ],
        [
            "掲載クーポン",
            f"{listing.get('coupons', coupon.get('coupon_count', '—'))}件",
            (
                f"新規 {coupon.get('new_label_count', '—')} / "
                f"再来 {coupon.get('repeat_label_count', '—')} / "
                f"全員 {coupon.get('all_label_count', '—')}"
            ),
        ],
        [
            "スタイル",
            f"{listing.get('styles', '—')}件",
            (
                f"比較サロン {listing.get('comparison_styles', '—')}件 / "
                f"エリア同プラン {listing.get('area_plan_styles', '—')}件"
            ),
        ],
    ]

    story += [
        _make_table(
            metric_rows,
            [43 * mm, 45 * mm, 92 * mm],
            center_columns=[1],
        ),
        Spacer(1, 5 * mm),
        _sub_title("7-1. PV・CVR・ACRの見方"),
        Paragraph(
            "<b>PV（発見）</b>：Hot Pepper Beautyで検索したお客様が、検索結果から店舗ページを開いた回数です。",
            STYLES["body"],
        ),
        Paragraph(
            "<b>CVR（興味喚起）</b>：店舗ページを見たお客様のうち、「クーポン・メニュー」を見た割合です。",
            STYLES["body"],
        ),
        Paragraph(
            "<b>ACR（アクション）</b>：「クーポン・メニュー」を見たお客様のうち、予約完了ページまで進んだ割合です。",
            STYLES["body"],
        ),
    ]

    # 7-2 カード
    pv = summary.get("top_pv")
    pv_base = summary.get("area_plan_pv")
    cvr = summary.get("cvr")
    cvr_base = summary.get("area_plan_cvr")
    acr = summary.get("acr")
    acr_base = summary.get("area_plan_acr")

    cards = [
        (
            "発見（PV）",
            (
                f"自店舗PVは{int(pv):,}です。比較基準は{int(pv_base):,}です。"
                if pv is not None and pv_base is not None
                else f"自店舗PVは{int(pv):,}です。" if pv is not None
                else "PVの数字を確認できませんでした。"
            ),
            (
                "店舗ページを見てもらう機会は"
                + ("比較基準より高いです。" if pv is not None and pv_base is not None and pv > pv_base
                   else "比較基準より低いです。" if pv is not None and pv_base is not None and pv < pv_base
                   else "比較基準と同程度です。" if pv is not None and pv_base is not None
                   else "今回の数字だけでは比較できません。")
            ),
            "検索される条件や店舗ページの掲載内容と合わせて確認します。",
        ),
        (
            "興味喚起（CVR）",
            (
                f"自店舗CVRは{float(cvr):.1f}%です。比較基準は{float(cvr_base):.1f}%です。"
                if cvr is not None and cvr_base is not None
                else f"自店舗CVRは{float(cvr):.1f}%です。" if cvr is not None
                else "CVRの数字を確認できませんでした。"
            ),
            (
                "「クーポン・メニュー」へ進む割合は"
                + ("比較基準より高いです。" if cvr is not None and cvr_base is not None and cvr > cvr_base
                   else "比較基準より低いです。" if cvr is not None and cvr_base is not None and cvr < cvr_base
                   else "比較基準と同程度です。" if cvr is not None and cvr_base is not None
                   else "今回の数字だけでは比較できません。")
            ),
            "店舗ページの内容やクーポンの見せ方と合わせて確認します。",
        ),
        (
            "アクション（ACR）",
            (
                f"自店舗ACRは{float(acr):.1f}%です。比較基準は{float(acr_base):.1f}%です。"
                if acr is not None and acr_base is not None
                else f"自店舗ACRは{float(acr):.1f}%です。" if acr is not None
                else "ACRの数字を確認できませんでした。"
            ),
            (
                "予約完了まで進む割合は"
                + ("比較基準より高いです。" if acr is not None and acr_base is not None and acr > acr_base
                   else "比較基準より低いです。" if acr is not None and acr_base is not None and acr < acr_base
                   else "比較基準と同程度です。" if acr is not None and acr_base is not None
                   else "今回の数字だけでは比較できません。")
            ),
            "クーポン内容・利用条件・予約可能枠・予約状況と合わせて確認します。",
        ),
    ]

    for title, fact, meaning, check in cards:
        story += [_card(title, fact, meaning, check), Spacer(1, 4 * mm)]

    # 3指標まとめ
    flow_meaning = (
        "PV・CVR・ACRを個別に見るだけでなく、予約までの流れのどこを確認するかを整理できます。"
    )
    story += [
        _card(
            "3つの数字を合わせて確認",
            (
                f"PV {int(pv):,}、CVR {float(cvr):.1f}%、ACR {float(acr):.1f}%です。"
                if pv is not None and cvr is not None and acr is not None
                else "PV・CVR・ACRの一部を確認できませんでした。"
            ),
            flow_meaning,
            "3つの数字だけで原因を決めず、クーポン内容・掲載内容・予約状況を合わせて確認します。",
        ),
        Spacer(1, 4 * mm),
    ]

    # 売上・予約
    sales = summary.get("sales_man_yen")
    reservations = summary.get("reservations")
    ticket = None
    if sales is not None and reservations:
        try:
            ticket = float(sales) * 10000 / float(reservations)
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    if sales is not None or reservations is not None:
        fact = f"前月売上は{sales}万円、予約数は{reservations}件です。"
        if ticket is not None:
            fact += f" 1予約あたりの売上は約{ticket:,.0f}円です。"

        story += [
            _card(
                "売上・予約",
                fact,
                "売上と予約数を組み合わせることで、予約1件あたりの売上も確認できます。",
                "HPB上の客単価、新規・再来の予約構成、掲載クーポンと合わせて確認します。",
            ),
            Spacer(1, 4 * mm),
        ]

    # 口コミ
    if reviews.get("count") is not None:
        fact = f"口コミは{reviews.get('count')}件です。"
        if reviews.get("comparison_count") is not None:
            try:
                diff = float(reviews["count"]) - float(reviews["comparison_count"])
                fact += f" 比較サロン平均との差は{diff:+.0f}件です。"
            except (TypeError, ValueError):
                pass
        if reviews.get("reply_rate") is not None:
            fact += f" 口コミ返信率は{float(reviews['reply_rate']):.1f}%です。"
        if reviews.get("overall_score") is not None:
            fact += f" 総合評点は{float(reviews['overall_score']):.2f}です。"

        meaning = "口コミ数・評点・返信状況を予約状況と合わせて確認できます。"
        if reviews.get("overall_score") is not None and reviews.get("comparison_overall_score") is not None:
            try:
                if float(reviews["overall_score"]) < float(reviews["comparison_overall_score"]):
                    meaning = "総合評点は比較サロン平均より低い水準です。"
                elif float(reviews["overall_score"]) > float(reviews["comparison_overall_score"]):
                    meaning = "総合評点は比較サロン平均より高い水準です。"
                else:
                    meaning = "総合評点は比較サロン平均と同じ水準です。"
            except (TypeError, ValueError):
                pass

        story += [
            _card(
                "口コミ・評価",
                fact,
                meaning,
                "口コミ数だけで判断せず、評価・返信状況・予約数などと合わせて確認します。",
            ),
            Spacer(1, 4 * mm),
        ]

    # 掲載量
    if listing.get("styles") is not None or listing.get("coupons") is not None:
        styles = listing.get("styles", "—")
        coupons = listing.get("coupons", coupon.get("coupon_count", "—"))
        style_base = listing.get("comparison_styles")
        area_style_base = listing.get("area_plan_styles")

        fact = f"掲載スタイルは{styles}件、クーポンは{coupons}件です。"
        if style_base is not None or area_style_base is not None:
            fact += (
                f" スタイルの比較基準は"
                f"比較サロン {style_base if style_base is not None else '—'}件、"
                f"エリア同プラン {area_style_base if area_style_base is not None else '—'}件です。"
            )

        story += [
            _card(
                "掲載量",
                fact,
                "掲載量そのものだけでなく、PV・CVR・ACRと合わせて店舗ページの状態を確認できます。",
                "数量だけで判断せず、実際のスタイル・クーポンの内容と予約までの数字を合わせて確認します。",
            ),
            Spacer(1, 4 * mm),
        ]

    # QuantitativeAnalyzerの既存insightsも保持
    insights = analysis.get("insights", []) or []
    if insights:
        story.append(_sub_title("7-3. PDFの数字から補足できる特徴"))
        for item in insights:
            if not isinstance(item, dict):
                continue
            title = item.get("title", "数字から分かる特徴")
            text = item.get("text", "")
            evidence = item.get("evidence", "")
            story += [
                _card(
                    title,
                    evidence or "PDF内の数字から確認できます。",
                    text or "数字から確認できる店舗の特徴です。",
                    "この数字だけで原因を断定せず、掲載内容・クーポン内容・予約状況と合わせて確認します。",
                ),
                Spacer(1, 4 * mm),
            ]

    story += [
        _note(
            "数字は店舗の状態を確認するための材料です。"
            "数字だけで原因を断定せず、クーポン内容・掲載内容・予約状況などと合わせて確認します。"
        ),
        PageBreak(),
    ]
    return story


# =============================================================
# 8. 総合分析
# =============================================================

def _build_integrated_section(report_data):
    integrated = _integrated(report_data)

    story = [
        _section_title("8. 総合分析"),
        Paragraph(
            "ここでは、価格・HPB上のお客様の行動・売上・口コミ・掲載状況などを組み合わせ、"
            "数字から確認しておきたいポイントを整理します。",
            STYLES["body"],
        ),
    ]

    cards = integrated.get("overall", []) or []

    if not cards:
        # IntegratedAnalyzerのカテゴリ別結果も拾う
        cards = (
            integrated.get("price", [])
            + integrated.get("cross_analysis", [])
            + integrated.get("quantitative", [])
        )[:8]

    story.append(_sub_title("8-1. 数字を組み合わせて見る"))

    if cards:
        for item in cards:
            if not isinstance(item, dict):
                continue
            story += [
                _card(
                    item.get("title", "総合確認項目"),
                    item.get("fact", ""),
                    item.get("meaning", ""),
                    item.get("check", "掲載内容・クーポン内容・予約状況と合わせて確認します。"),
                ),
                Spacer(1, 4 * mm),
            ]
    else:
        story.append(_note("今回の総合分析では表示できるカードがありませんでした。"))

    story.append(_sub_title("8-2. 総合的に確認するポイント"))

    check_points = integrated.get("check_points", []) or []

    if check_points:
        data = [["確認する領域", "次に確認すること"]]
        seen = set()

        aliases = {
            "価格 × HPB上の行動": "予約までの流れ",
            "予約までの流れ": "予約までの流れ",
            "掲載内容": "掲載内容",
            "価格": "価格",
            "カテゴリ": "カテゴリ",
            "確認候補": "確認候補",
            "売上・予約": "売上・予約",
            "口コミ・評価": "口コミ・評価",
        }

        for item in check_points:
            if not isinstance(item, dict):
                continue
            area = _plain(
                _first(item, "section", "area", "title", default="確認ポイント")
            )
            area = aliases.get(area, area)
            check = _customer_text(
                _first(
                    item,
                    "check",
                    "next_check",
                    "action",
                    "confirmation",
                    default="確認ポイントを整理してください。",
                )
            )
            key = (area, check)
            if key in seen:
                continue
            seen.add(key)
            data.append([area, check])

        if len(data) > 1:
            story.append(
                _make_table(data, [45 * mm, 115 * mm])
            )
        else:
            story.append(_note("追加の確認ポイントはありませんでした。"))
    else:
        # カードから重複しない確認ポイントを生成
        data = [["確認する領域", "次に確認すること"]]
        seen = set()
        for item in cards:
            if not isinstance(item, dict):
                continue
            area = _plain(
                _first(item, "section", "title", default="確認ポイント")
            )
            check = _customer_text(item.get("check", ""))
            if not check:
                continue
            key = (area, check)
            if key in seen:
                continue
            seen.add(key)
            data.append([area, check])

        if len(data) > 1:
            story.append(_make_table(data, [45 * mm, 115 * mm]))
        else:
            story.append(_note("追加の確認ポイントはありませんでした。"))

    story += [
        _note(
            "総合分析は、複数の数字から確認すべきポイントを整理するためのものです。"
            "数字だけから原因を断定したり、価格変更・クーポン変更を自動的に決めたりするものではありません。"
        ),
        PageBreak(),
    ]
    return story


# =============================================================
# 9. 分析方法
# =============================================================

def _build_method_section(report_data):
    notes = report_data.get("notes", []) or []

    story = [
        _section_title("9. 分析方法・注意事項"),
        Paragraph(
            "本レポートで使用している価格分析と総合分析の考え方を記載します。",
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
            Paragraph("・" + _safe_text(item), STYLES["body"])
        )

    if notes:
        story += [
            Spacer(1, 4 * mm),
            _sub_title("レポート上の注意"),
        ]
        for note in notes:
            story.append(
                Paragraph(
                    "・" + _safe_text(_customer_text(note)),
                    STYLES["small_muted"],
                )
            )

    return story


# =============================================================
# PDF生成
# =============================================================

def generate_pdf_report(
    report_data: Dict[str, Any],
    output_path: str | Path,
) -> Path:
    """
    v2.5.2
    既存の分析データを維持したまま、PDFの表示構造を修正。
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = HPBReportDocTemplate(str(output_path))

    story: List[Any] = []

    # 1～4：既存の主要データを必ず残す
    story.extend(_build_cover(report_data))
    story.extend(_build_primary_overview(report_data))
    story.extend(_build_comparison_section(report_data))
    story.extend(_build_category_section(report_data))
    story.extend(_build_review_section(report_data))

    # 5～9
    story.extend(_build_comparison_characteristics(report_data))
    story.extend(_build_improvement_section(report_data))
    story.extend(_build_quantitative_section(report_data))
    story.extend(_build_integrated_section(report_data))
    story.extend(_build_method_section(report_data))

    doc.build(story)
    return output_path
