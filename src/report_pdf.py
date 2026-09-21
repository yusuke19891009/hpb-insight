from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from html import escape

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
    KeepTogether,
)

VERSION = "v2.4.2"

MAIN_COLOR = colors.HexColor("#992854")
SUB_COLOR = colors.HexColor("#c18096")
TITLE_COLOR = colors.HexColor("#d5728d")
LIGHT_BG = colors.HexColor("#F8F1F4")
GRID_COLOR = colors.HexColor("#D9C3CC")
TEXT_COLOR = colors.HexColor("#333333")
MUTED_COLOR = colors.HexColor("#777777")
WHITE = colors.white
PALE_BG = colors.HexColor("#FCF8FA")

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

FONT = "HeiseiKakuGo-W5"
MINCHO = "HeiseiMin-W3"


def _safe(value: Any) -> str:
    """ReportLab Paragraph用に安全に文字列化する。"""
    if value is None:
        return ""
    return escape(str(value)).replace("\n", "<br/>")


def _money(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):,.0f}円"
    except (TypeError, ValueError):
        return "—"


def _money100(value: Any) -> str:
    if value is None:
        return "—"
    try:
        number = float(value)
        rounded = round(number / 100.0) * 100
        return f"{rounded:,.0f}円"
    except (TypeError, ValueError):
        return "—"


def _pct(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "—"


def _num(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(
            str(value)
            .replace(",", "")
            .replace("円", "")
            .replace("￥", "")
            .replace("¥", "")
            .replace("%", "")
            .strip()
        )
    except (TypeError, ValueError):
        return None


def _display_price(value: Any) -> str:
    number = _num(value)
    return "—" if number is None else _money(number)


def _styles():
    getSampleStyleSheet()
    return {
        "cover": ParagraphStyle(
            "cover",
            fontName=FONT,
            fontSize=25,
            leading=34,
            textColor=MAIN_COLOR,
            alignment=TA_CENTER,
            spaceAfter=8 * mm,
        ),
        "cover2": ParagraphStyle(
            "cover2",
            fontName=FONT,
            fontSize=19,
            leading=27,
            textColor=TITLE_COLOR,
            alignment=TA_CENTER,
            spaceAfter=12 * mm,
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName=FONT,
            fontSize=17,
            leading=23,
            textColor=MAIN_COLOR,
            spaceBefore=2 * mm,
            spaceAfter=5 * mm,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName=FONT,
            fontSize=12,
            leading=17,
            textColor=MAIN_COLOR,
            spaceBefore=3 * mm,
            spaceAfter=3 * mm,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=MINCHO,
            fontSize=10.5,
            leading=17,
            textColor=TEXT_COLOR,
            spaceAfter=2.5 * mm,
        ),
        "small": ParagraphStyle(
            "small",
            fontName=MINCHO,
            fontSize=9.5,
            leading=14,
            textColor=TEXT_COLOR,
        ),
        "muted": ParagraphStyle(
            "muted",
            fontName=MINCHO,
            fontSize=9,
            leading=13,
            textColor=MUTED_COLOR,
        ),
        "th": ParagraphStyle(
            "th",
            fontName=FONT,
            fontSize=9.5,
            leading=13,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
        "td": ParagraphStyle(
            "td",
            fontName=MINCHO,
            fontSize=9.3,
            leading=13.5,
            textColor=TEXT_COLOR,
        ),
        "tdc": ParagraphStyle(
            "tdc",
            fontName=MINCHO,
            fontSize=9.3,
            leading=13.5,
            textColor=TEXT_COLOR,
            alignment=TA_CENTER,
        ),
        "cardtitle": ParagraphStyle(
            "cardtitle",
            fontName=FONT,
            fontSize=11.5,
            leading=16,
            textColor=MAIN_COLOR,
        ),
        "cardlabel": ParagraphStyle(
            "cardlabel",
            fontName=FONT,
            fontSize=9.2,
            leading=13,
            textColor=SUB_COLOR,
        ),
        "cardbody": ParagraphStyle(
            "cardbody",
            fontName=MINCHO,
            fontSize=9.4,
            leading=14,
            textColor=TEXT_COLOR,
        ),
        "metric": ParagraphStyle(
            "metric",
            fontName=FONT,
            fontSize=16,
            leading=21,
            textColor=MAIN_COLOR,
            alignment=TA_CENTER,
        ),
        "label": ParagraphStyle(
            "label",
            fontName=FONT,
            fontSize=9.5,
            leading=13,
            textColor=MUTED_COLOR,
            alignment=TA_CENTER,
        ),
    }


S = _styles()


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
            [PageTemplate(id="hpb", frames=frame, onPage=self._page)]
        )

    def _page(self, canvas, doc):
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
        canvas.drawString(15 * mm, 8 * mm, "ちゃぴおHPB Toolkit")
        canvas.drawRightString(
            width - 15 * mm,
            8 * mm,
            f"{doc.page} ページ",
        )
        canvas.restoreState()


def _h(text: str) -> Paragraph:
    return Paragraph(_safe(text), S["h1"])


def _h2(text: str) -> Paragraph:
    return Paragraph(_safe(text), S["h2"])


def _p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(_safe(text), S[style])


def _note(text: str):
    table = Table(
        [[Paragraph(_safe(text), S["small"])]],
        colWidths=[180 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, GRID_COLOR),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _table(rows: List[List[Any]], widths: List[float], center=()) -> Table:
    converted = []
    for row_index, row in enumerate(rows):
        converted_row = []
        for col_index, value in enumerate(row):
            if isinstance(value, Paragraph):
                converted_row.append(value)
                continue
            if row_index == 0:
                style = S["th"]
            elif col_index in center:
                style = S["tdc"]
            else:
                style = S["td"]
            converted_row.append(Paragraph(_safe(value), style))
        converted.append(converted_row)

    total = sum(widths)
    if total > 180 * mm:
        scale = 180 * mm / total
        widths = [width * scale for width in widths]

    table = Table(
        converted,
        colWidths=widths,
        repeatRows=1 if len(converted) > 1 else 0,
        hAlign="LEFT",
    )
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.35, GRID_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if len(converted) > 1:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), MAIN_COLOR))
        for row_index in range(2, len(converted), 2):
            commands.append(
                ("BACKGROUND", (0, row_index), (-1, row_index), PALE_BG)
            )
    table.setStyle(TableStyle(commands))
    return table


def _metric_cards(items: List[tuple]) -> Table:
    cells = []
    for value, label in items:
        cells.append(
            [
                Paragraph(_safe(value), S["metric"]),
                Paragraph(_safe(label), S["label"]),
            ]
        )
    width = 180 * mm / len(cells)
    table = Table(
        [cells],
        colWidths=[width] * len(cells),
        rowHeights=[27 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, GRID_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, GRID_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _three_part_card(title: str, fact: str, meaning: str, check: str) -> Table:
    """「数字上の事実 / 分かること / 次に確認すること」を明確に分離したカード。"""
    rows = [
        [Paragraph(_safe(title), S["cardtitle"])],
        [
            Table(
                [[
                    Paragraph("数字上の事実", S["cardlabel"]),
                    Paragraph(_safe(fact), S["cardbody"]),
                ]],
                colWidths=[38 * mm, 136 * mm],
            )
        ],
        [
            Table(
                [[
                    Paragraph("分かること", S["cardlabel"]),
                    Paragraph(_safe(meaning), S["cardbody"]),
                ]],
                colWidths=[38 * mm, 136 * mm],
            )
        ],
        [
            Table(
                [[
                    Paragraph("次に確認すること", S["cardlabel"]),
                    Paragraph(_safe(check), S["cardbody"]),
                ]],
                colWidths=[38 * mm, 136 * mm],
            )
        ],
    ]
    table = Table(rows, colWidths=[180 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, GRID_COLOR),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, GRID_COLOR),
                ("LINEBELOW", (0, 1), (-1, 1), 0.25, GRID_COLOR),
                ("LINEBELOW", (0, 2), (-1, 2), 0.25, GRID_COLOR),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return KeepTogether([table])


def _cover(data: Dict[str, Any]) -> List[Any]:
    primary = data["primary_shop"]
    name = primary["summary"]["name"]
    comparisons = data.get("comparison_shops", [])
    comparison_text = "<br/>".join(
        f"・{_safe(shop.get('name', ''))}" for shop in comparisons
    ) or "・比較対象店舗なし"

    target = Table(
        [
            [Paragraph("分析対象店舗", S["small"]), Paragraph(_safe(name), S["small"])],
            [Paragraph("比較対象店舗", S["small"]), Paragraph(comparison_text, S["small"])],
        ],
        colWidths=[42 * mm, 118 * mm],
        hAlign="CENTER",
    )
    target.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BG),
                ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.7, GRID_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, GRID_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return [
        Spacer(1, 23 * mm),
        Paragraph(_safe(name) + " 様", S["cover"]),
        Paragraph("HOTPEPPER Beauty分析レポート", S["cover2"]),
        Spacer(1, 5 * mm),
        target,
        Spacer(1, 14 * mm),
        Paragraph(
            f"作成日時：{data['created_at'].strftime('%Y年%m月%d日 %H:%M')}",
            S["muted"],
        ),
        Paragraph(f"レポートバージョン：{data['version']}", S["muted"]),
        Spacer(1, 12 * mm),
        _note(
            "本レポートは「自店舗」を主対象とし、比較対象店舗は市場・参考情報として扱います。"
            "比較対象店舗そのものを評価することを目的とせず、自店舗の現状把握と価格検討に利用する構成です。"
        ),
        PageBreak(),
    ]


def _overview(data: Dict[str, Any]) -> List[Any]:
    primary = data["primary_shop"]
    summary = primary["summary"]
    pricing = primary["pricing"]
    reference = pricing.get("market_reference_price") or pricing.get("comparison_median")
    return [
        _h("1. 自店舗の現状"),
        _p(f"分析対象：{summary.get('name', '不明店舗')}"),
        _metric_cards(
            [
                (f"{summary.get('coupon_count', 0)}件", "取得クーポン数"),
                (f"{summary.get('valid_price_count', 0)}件", "有効価格データ"),
                (_money(summary.get("average")), "平均価格"),
                (_money(summary.get("median")), "中央値"),
            ]
        ),
        Spacer(1, 5 * mm),
        _table(
            [
                ["項目", "自店舗"],
                ["市場参考価格", _money100(reference)],
                ["価格ポジション", pricing.get("position", "比較不可")],
                ["価格対比率", _pct(pricing.get("ratio"))],
                ["参考度", pricing.get("reference_level", "比較不可")],
                [
                    "参考価格帯",
                    f"{_money100(pricing.get('reference_price_min'))} ～ {_money100(pricing.get('reference_price_max'))}",
                ],
            ],
            [60 * mm, 120 * mm],
            center=[1],
        ),
        _note(
            "市場参考価格は比較店舗ごとの中央値を同じ重みで比較して算出し、PDFでは100円単位に統一して表示しています。"
        ),
        PageBreak(),
    ]


def _comparison(data: Dict[str, Any]) -> List[Any]:
    pricing = data["primary_shop"]["pricing"]
    comparisons = data.get("comparison_shops", [])
    reference = pricing.get("market_reference_price") or pricing.get("comparison_median")
    rows = [["比較対象店舗", "クーポン数", "有効価格", "平均価格", "中央値"]]
    for shop in comparisons:
        rows.append(
            [
                shop.get("name"),
                f"{shop.get('coupon_count', 0)}件",
                f"{shop.get('valid_price_count', 0)}件",
                _money(shop.get("average")),
                _money(shop.get("median")),
            ]
        )
    return [
        _h("2. 市場との価格比較"),
        _p("自店舗の価格中央値を中心に、比較対象店舗から算出した市場参考価格を確認します。"),
        _metric_cards(
            [
                (_money(pricing.get("shop_median")), "自店舗中央値"),
                (_money100(reference), "市場参考価格"),
                (_pct(pricing.get("ratio")), "市場価格との比較"),
            ]
        ),
        Spacer(1, 5 * mm),
        _table(rows, [62 * mm, 25 * mm, 25 * mm, 34 * mm, 34 * mm], center=[1, 2, 3, 4])
        if len(rows) > 1
        else _note("比較対象店舗がありません。"),
        Spacer(1, 4 * mm),
        _note(
            "比較対象店舗は市場・参考情報として使用しています。個別店舗の優劣を評価するためのものではありません。"
        ),
        PageBreak(),
    ]


def _categories(data: Dict[str, Any]) -> List[Any]:
    rows = data["primary_shop"].get("category_rows", [])
    table_rows = [["カテゴリ", "自店舗件数", "自店舗中央値", "市場参考", "ポジション", "参考度"]]
    for row in rows:
        table_rows.append(
            [
                row.get("category"),
                f"{row.get('primary_coupon_count', 0)}件",
                _money(row.get("primary_median")),
                _money100(row.get("market_reference_price")),
                row.get("position", "比較不可"),
                row.get("reference_level", "比較不可"),
            ]
        )

    story = [
        _h("3. カテゴリ別価格比較"),
        _p("自店舗のカテゴリ別価格を中心に、比較対象店舗と市場参考価格を確認します。"),
    ]
    if not rows:
        story += [_note("比較できるカテゴリがありません。"), PageBreak()]
        return story

    story += [
        _table(
            table_rows,
            [61 * mm, 23 * mm, 31 * mm, 29 * mm, 25 * mm, 20 * mm],
            center=[1, 2, 3, 4, 5],
        ),
        Spacer(1, 5 * mm),
        _h2("カテゴリ別の比較店舗内訳"),
    ]

    for row in rows:
        stores = row.get("comparison_stores", [])
        if not stores:
            continue
        detail = [["カテゴリ", "比較対象店舗", "件数", "中央値"]]
        for store in stores:
            detail.append(
                [
                    row.get("category"),
                    store.get("shop_name"),
                    f"{store.get('coupon_count', 0)}件",
                    _money(store.get("median")),
                ]
            )
        story += [
            _table(detail, [58 * mm, 63 * mm, 24 * mm, 35 * mm], center=[2, 3]),
            Spacer(1, 3 * mm),
        ]

    story += [
        _note(
            "カテゴリは比較時に正規化し、カテゴリ順の違いや「その他」の付加による表記差を吸収しています。"
            "比較可能なカテゴリだけを市場参考価格の算出対象としています。"
        ),
        PageBreak(),
    ]
    return story


def _review(data: Dict[str, Any]) -> List[Any]:
    candidates = data["primary_shop"].get("review_candidates", {})
    groups = [
        ("価格のばらつきから見た確認候補", candidates.get("outliers", [])),
        ("カテゴリ別の確認候補", candidates.get("category_outliers", [])),
        ("低価格の確認候補", candidates.get("low_price_attention", [])),
        ("高価格の確認候補", candidates.get("high_price_attention", [])),
    ]
    seen = set()
    rows = [["区分", "クーポン名", "カテゴリ", "価格", "確認理由"]]
    for label, items in groups:
        for item in items:
            key = (
                item.get("coupon_name"),
                item.get("price"),
                item.get("category"),
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                [
                    label,
                    item.get("coupon_name", "—"),
                    item.get("category", "—"),
                    _money(item.get("price")),
                    _replace_customer_jargon(item.get("reason", "価格上の確認候補")),
                ]
            )
    return [
        _h("4. 営業確認候補"),
        _p("価格の差や価格のばらつきから、営業担当者が確認しておきたい候補を整理しています。"),
        _table(rows, [39 * mm, 59 * mm, 31 * mm, 24 * mm, 27 * mm], center=[3])
        if len(rows) > 1
        else _note("今回の価格分析では、特に確認が必要な候補は抽出されませんでした。"),
        Spacer(1, 4 * mm),
        _note(
            "確認候補が出たことだけを理由に、価格変更やクーポン変更を行うものではありません。"
            "クーポンの内容・利用条件・対象者条件を確認してください。"
        ),
        PageBreak(),
    ]


def _replace_customer_jargon(text: Any) -> str:
    """顧客向けPDFから統計用語を排除する。"""
    value = "" if text is None else str(text)
    replacements = {
        "IQR上限": "同じカテゴリの他のクーポンと比べて価格の差が大きい範囲",
        "IQR下限": "同じカテゴリの他のクーポンと比べて価格の差が大きい範囲",
        "IQR": "価格のばらつき",
        "統計的外れ値": "価格の差が大きい確認候補",
        "統計的な外れ値": "価格の差が大きい確認候補",
        "統計的": "数字上",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def _improvement(data: Dict[str, Any]) -> List[Any]:
    improvement = data["primary_shop"].get("improvement", {})
    proposals = improvement.get("proposals", [])
    story = [
        _h("6. 自店舗への改善検討候補"),
        _p(
            "価格・カテゴリ・クーポン確認候補をもとに、改善を検討する入口となるポイントを整理しています。"
        ),
    ]

    if improvement.get("source_note"):
        story.append(_note(improvement["source_note"]))

    if not proposals:
        story += [
            _note("今回の分析では、価格・カテゴリ・クーポン内容から特に改善を検討する候補は抽出されませんでした。"),
            PageBreak(),
        ]
        return story

    for index, proposal in enumerate(proposals, start=1):
        title = f"{index}. {proposal.get('title', '改善検討候補')}"
        reason = _replace_customer_jargon(proposal.get("reason", ""))
        detail = _replace_customer_jargon(proposal.get("detail", ""))
        action = _replace_customer_jargon(proposal.get("action", ""))

        # クーポン名はタイトルや事実欄に繰り返さず、必要な場合のみ別の対象行にする。
        coupon_name = proposal.get("coupon_name")
        fact_parts = []
        if reason:
            fact_parts.append(reason)
        if proposal.get("category"):
            fact_parts.append(f"対象カテゴリ：{proposal.get('category')}。")
        current_price = proposal.get("current_price_display")
        reference_price = proposal.get("reference_price_display")
        if current_price and current_price != "—":
            fact_parts.append(f"自店舗価格：{current_price}。")
        if reference_price and reference_price != "—":
            reference_number = _num(reference_price)
            fact_parts.append(f"市場参考価格：{_money100(reference_number)}。")

        fact = " ".join(part for part in fact_parts if part)
        if coupon_name:
            fact = f"対象クーポンあり。{fact}" if fact else "対象クーポンあり。"

        if not detail:
            detail = "価格・カテゴリ・クーポン内容から確認するポイントを整理しています。"
        if not action:
            action = "価格だけで判断せず、クーポン内容・利用条件・対象者条件を確認します。"

        story += [
            _three_part_card(title, fact, detail, action),
            Spacer(1, 3 * mm),
        ]

    story += [
        _note(
            "第4章の営業確認候補と重なる場合がありますが、第6章ではそれを改善を検討する入口として整理しています。"
            "候補だけで変更を決めず、実際のクーポン内容や利用条件を確認してください。"
        ),
        PageBreak(),
    ]
    return story


def _quantitative_card_from_insight(insight: Dict[str, Any], summary: Dict[str, Any]) -> tuple:
    title = insight.get("title", "数字から分かる特徴")
    text = insight.get("text", "")
    return (
        title,
        text,
        "HPB詳細レポートの数字から確認できる特徴です。",
        "この数字だけで原因を断定せず、掲載内容や予約状況と合わせて確認します。",
    )


def _quant(data: Dict[str, Any]) -> List[Any]:
    quantitative = data["primary_shop"].get("quantitative")
    story = [
        _h("7. 自店舗の数字から分かる特徴"),
        _p(
            "HPB詳細レポートの数字から、店舗ページを見てもらえているか、クーポンを見てもらえているか、予約まで進んでいるかを確認します。"
        ),
    ]
    if not quantitative:
        story += [
            _note("自店舗のHPB詳細レポートPDFが指定されていないため、この章の数値分析は生成していません。"),
            PageBreak(),
        ]
        return story

    metrics = quantitative.get("metrics", {})
    summary = metrics.get("summary", {})
    reviews = metrics.get("reviews", {})
    listing = metrics.get("listing", {})
    coupon = metrics.get("coupon", {})

    metric_rows = [
        ["指標", "自店舗", "比較・基準"],
        ["前月売上", f"{summary.get('sales_man_yen', '—')}万円", "—"],
        [
            "前月予約数",
            f"{summary.get('reservations', '—')}件",
            f"新規 {summary.get('new_reservations', '—')} / リピート {summary.get('repeat_reservations', '—')}",
        ],
        [
            "PV",
            f"{summary.get('top_pv'):,}" if isinstance(summary.get("top_pv"), int) else "—",
            f"エリア同プラン {summary.get('area_plan_pv'):,}" if isinstance(summary.get("area_plan_pv"), int) else "—",
        ],
        [
            "CVR",
            _pct(summary.get("cvr")),
            f"エリア同プラン {_pct(summary.get('area_plan_cvr'))}",
        ],
        [
            "ACR",
            _pct(summary.get("acr")),
            f"エリア同プラン {_pct(summary.get('area_plan_acr'))}",
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
            f"新規 {coupon.get('new_label_count', '—')} / 再来 {coupon.get('repeat_label_count', '—')} / 全員 {coupon.get('all_label_count', '—')}",
        ],
        ["スタイル", f"{listing.get('styles', '—')}件", "—"],
    ]

    story += [
        _note(
            f"解析対象：{metrics.get('source_file', 'HPB詳細レポートPDF')} ／ {metrics.get('page_count', '—')}ページ"
        ),
        _table(metric_rows, [38 * mm, 55 * mm, 87 * mm], center=[1]),
        Spacer(1, 5 * mm),
        _h2("7-1. 数字から分かる店舗の特徴"),
    ]

    insights = quantitative.get("analysis", {}).get("insights", [])
    if insights:
        for insight in insights:
            story += [
                _three_part_card(*_quantitative_card_from_insight(insight, summary)),
                Spacer(1, 3 * mm),
            ]
    else:
        story.append(_note("詳細レポートから自動生成できる特徴はありませんでした。"))

    story.append(_h2("7-2. PV・CVR・ACRの見方"))
    story.append(
        _note(
            "PV（発見）：Hot Pepper Beautyで検索したお客様が、検索結果から店舗ページを開いた回数。\n"
            "CVR（興味喚起）：店舗ページを見たお客様のうち、「クーポン・メニュー」を見た割合。\n"
            "ACR（アクション）：「クーポン・メニュー」を見たお客様のうち、予約完了ページまで進んだ割合。"
        )
    )

    traffic = summary
    pv = traffic.get("top_pv")
    pvb = traffic.get("area_plan_pv")
    cvr = traffic.get("cvr")
    cvrb = traffic.get("area_plan_cvr")
    acr = traffic.get("acr")
    acrb = traffic.get("area_plan_acr")

    traffic_cards = []
    if pv is not None:
        pv_meaning = "比較基準より高い" if pvb is not None and pv > pvb else "比較基準より低い" if pvb is not None and pv < pvb else "比較基準と近い"
        traffic_cards.append(
            _three_part_card(
                "発見（PV）",
                f"自店舗PVは{int(pv):,}です。" + (f"比較基準は{int(pvb):,}です。" if pvb is not None else ""),
                f"店舗ページを見てもらう機会は、{pv_meaning}数字です。" if pvb is not None else "店舗ページを見てもらった回数を確認できます。",
                "検索される条件や店舗ページの掲載内容と合わせて確認します。",
            )
        )
    if cvr is not None:
        cvr_meaning = "比較基準より高い" if cvrb is not None and cvr > cvrb else "比較基準より低い" if cvrb is not None and cvr < cvrb else "比較基準と近い"
        traffic_cards.append(
            _three_part_card(
                "興味喚起（CVR）",
                f"自店舗CVRは{float(cvr):.1f}%です。" + (f"比較基準は{float(cvrb):.1f}%です。" if cvrb is not None else ""),
                f"店舗ページを見た後に「クーポン・メニュー」へ進む割合は、{cvr_meaning}数字です。" if cvrb is not None else "店舗ページから「クーポン・メニュー」へ進んだ割合を確認できます。",
                "店舗ページの内容やクーポンの見せ方と合わせて確認します。",
            )
        )
    if acr is not None:
        acr_meaning = "比較基準より高い" if acrb is not None and acr > acrb else "比較基準より低い" if acrb is not None and acr < acrb else "比較基準と近い"
        traffic_cards.append(
            _three_part_card(
                "アクション（ACR）",
                f"自店舗ACRは{float(acr):.1f}%です。" + (f"比較基準は{float(acrb):.1f}%です。" if acrb is not None else ""),
                f"「クーポン・メニュー」から予約完了ページまで進む割合は、{acr_meaning}数字です。" if acrb is not None else "予約完了ページまで進んだ割合を確認できます。",
                "クーポン内容・利用条件・予約状況と合わせて確認します。",
            )
        )

    story.extend(traffic_cards)
    if pv is not None and cvr is not None and acr is not None:
        story += [
            Spacer(1, 2 * mm),
            _three_part_card(
                "3つの数字を合わせて確認",
                f"PV {int(pv):,}、CVR {float(cvr):.1f}%、ACR {float(acr):.1f}%です。",
                "店舗ページを見てもらう機会、クーポンを見てもらう割合、予約完了まで進む割合を順番に確認できます。",
                "3つの数字だけで原因を決めず、クーポン内容・掲載内容・予約状況と合わせて確認します。",
            ),
        ]

    story += [PageBreak()]
    return story


def _label_for_check_point(value: Any) -> str:
    mapping = {
        "quantitative": "HPB詳細レポート",
        "cross_analysis": "数字の組み合わせ",
        "price": "価格",
        "category": "カテゴリ",
        "quality": "確認候補",
        "improvement": "改善検討候補",
        "overall": "全体確認",
    }
    key = "" if value is None else str(value)
    return mapping.get(key, key or "確認ポイント")


def _integrated(data: Dict[str, Any]) -> List[Any]:
    integrated = data.get("integrated") or data["primary_shop"].get("integrated") or {}
    story = [
        _h("8. 総合分析"),
        _p(
            "価格・カテゴリ・クーポン確認候補・HPB詳細レポートを組み合わせ、自店舗の状態を一つの流れで整理します。"
        ),
    ]
    if not integrated:
        story += [_note("総合分析データがありません。"), PageBreak()]
        return story

    story += [
        _note(integrated.get("summary", "総合分析を実行しました。")),
        _h2("8-1. 自店舗の全体像"),
    ]

    overall = integrated.get("overall", [])
    for index, item in enumerate(overall, start=1):
        story += [
            _three_part_card(
                f"{index}. {item.get('title', '総合分析')}",
                _replace_customer_jargon(item.get("fact", "")),
                _replace_customer_jargon(item.get("meaning", "")),
                _replace_customer_jargon(item.get("check", "")),
            ),
            Spacer(1, 3 * mm),
        ]

    categories = integrated.get("category", [])
    if categories:
        story += [_h2("8-2. カテゴリごとの確認ポイント")]
        category_rows = [["カテゴリ", "数字上の事実", "分かること", "次に確認すること"]]
        for item in categories[:8]:
            category_rows.append(
                [
                    item.get("category", "—"),
                    _replace_customer_jargon(item.get("fact", "—")),
                    _replace_customer_jargon(item.get("meaning", "—")),
                    _replace_customer_jargon(item.get("check", "—")),
                ]
            )
        story.append(
            _table(category_rows, [34 * mm, 52 * mm, 45 * mm, 49 * mm])
        )

    checks = integrated.get("check_points", [])
    if checks:
        story += [_h2("8-3. 総合的に確認するポイント")]
        check_rows = [["項目", "確認ポイント"]]
        for item in checks[:10]:
            check_rows.append(
                [
                    _label_for_check_point(item.get("priority")),
                    _replace_customer_jargon(item.get("text", "—")),
                ]
            )
        story.append(_table(check_rows, [40 * mm, 140 * mm]))

    story += [
        _note(
            "総合分析は、複数の数字から確認すべきポイントを整理するためのものです。"
            "数字だけから原因を断定したり、価格変更・施策を自動的に決めたりするものではありません。"
        ),
        PageBreak(),
    ]
    return story


def _method(data: Dict[str, Any]) -> List[Any]:
    methods = [
        "自店舗を主分析対象とし、比較対象店舗は市場・参考情報として扱います。",
        "比較店舗の価格は、店舗ごとの中央値を先に算出し、その店舗中央値を同じ重みで比較します。",
        "カテゴリ比較では、カテゴリ名の順番の違いや「その他」の付加による表記差を整理しています。",
        "市場参考価格は比較店舗の中央値を基準に、100円単位で表示しています。",
        "参考価格帯は市場参考価格の±5%を目安として算出しています。",
        "価格の確認候補は、価格の差や価格のばらつきから確認が必要と思われるものを抽出しています。",
        "第6章は第4章の確認候補を、改善を検討するための入口として整理しています。",
        "確認候補が出たことだけを理由に、価格変更やクーポン変更を行うものではありません。",
        "HPB詳細レポートは自店舗のPDFのみを対象とし、比較店舗の詳細PDFは使用していません。",
    ]
    story = [_h("9. 分析方法・注意事項"), _p("本レポートで使用している分析方法と注意点を記載します。")]
    story.extend(_p("・" + item) for item in methods)
    notes = data.get("notes", [])
    if notes:
        story += [Spacer(1, 4 * mm), _h2("レポート上の注意")]
        story.extend(_p("・" + str(note), "muted") for note in notes)
    return story


def generate_pdf_report(report_data: Dict[str, Any], output_path: str | Path) -> Path:
    """自店舗主役型PDFレポートを生成する。"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = HPBReportDocTemplate(str(output_path))

    story: List[Any] = []
    for builder in (
        _cover,
        _overview,
        _comparison,
        _categories,
        _review,
        _comparison_features,
        _improvement,
        _quant,
        _integrated,
        _method,
    ):
        if builder is _comparison_features:
            story.extend(builder(report_data))
        else:
            story.extend(builder(report_data))

    doc.build(story)
    return output_path


# ------------------------------------------------------------------
# 第5章：比較対象店舗の観測特徴
# ------------------------------------------------------------------
def _comparison_features(data: Dict[str, Any]) -> List[Any]:
    story = [
        _h("5. 比較対象店舗の観測特徴"),
        _p("比較対象店舗について、取得データから確認できる事実を整理します。"),
    ]
    comparisons = data.get("comparison_shops", [])
    if not comparisons:
        story += [_note("比較対象店舗が設定されていません。"), PageBreak()]
        return story

    for shop in comparisons:
        categories = shop.get("categories", {}) or {}
        items = []
        for category, value in categories.items():
            if not isinstance(value, dict):
                continue
            items.append(
                (
                    category,
                    value.get("coupon_count", 0),
                    value.get("median"),
                )
            )
        items.sort(key=lambda item: (-int(item[1] or 0), str(item[0])))
        items = items[:6]

        story += [
            _h2(shop.get("name", "不明店舗")),
            _table(
                [
                    ["項目", "観測値"],
                    ["クーポン数", f"{shop.get('coupon_count', 0)}件"],
                    ["有効価格データ", f"{shop.get('valid_price_count', 0)}件"],
                    ["平均価格", _money(shop.get("average"))],
                    ["中央値", _money(shop.get("median"))],
                ],
                [55 * mm, 125 * mm],
            ),
            Spacer(1, 3 * mm),
        ]

        if items:
            category_rows = [["カテゴリ", "件数", "中央値"]]
            for category, count, median_price in items:
                category_rows.append(
                    [category, f"{count}件", _money(median_price)]
                )
            story += [
                Paragraph("確認できた主なカテゴリ", S["cardtitle"]),
                _table(category_rows, [113 * mm, 27 * mm, 40 * mm], center=[1, 2]),
                Spacer(1, 5 * mm),
            ]
        else:
            story += [
                Paragraph("確認できた主なカテゴリ", S["cardtitle"]),
                _note("確認できたカテゴリはありません。"),
                Spacer(1, 5 * mm),
            ]

    story += [
        _note(
            "この章は比較対象店舗の特徴を観測情報として整理したものです。"
            "比較対象店舗の施策を、そのまま自店舗に適用すべきという意味ではありません。"
        ),
        PageBreak(),
    ]
    return story
