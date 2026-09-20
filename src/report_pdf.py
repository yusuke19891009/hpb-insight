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
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)


class PDFReportGenerator:
    """
    ちゃぴおHPB Toolkit v1.9.1

    PDFレポートの見た目を改善するバージョン。

    デザインカラー:
      メイン  #992854
      サブ    #c18096
      題目    #d5728d

    - 日本語フォントを可能な限り実フォントで埋め込む
    - 表の日本語欠落を防ぐ
    - セクション見出し・表ヘッダー・罫線をブランドカラー化
    - 店舗ごとのレポートを読みやすく整理
    """

    VERSION = "v1.9.1"

    # ---------------------------------------------------------
    # ブランドカラー
    # ---------------------------------------------------------
    MAIN_COLOR = colors.HexColor("#992854")
    SUB_COLOR = colors.HexColor("#c18096")
    TITLE_COLOR = colors.HexColor("#d5728d")

    TEXT_COLOR = colors.HexColor("#333333")
    MUTED_COLOR = colors.HexColor("#777777")
    LIGHT_BG = colors.HexColor("#FBF7F9")
    TABLE_BG = colors.HexColor("#F7EEF2")
    BORDER_COLOR = colors.HexColor("#DDBBC8")
    WHITE = colors.white

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.FONT_NAME, self.FONT_BOLD = self._register_japanese_fonts()

        styles = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            "JPTitle191",
            parent=styles["Title"],
            fontName=self.FONT_BOLD,
            fontSize=22,
            leading=29,
            textColor=self.TITLE_COLOR,
            alignment=TA_CENTER,
            spaceAfter=3 * mm,
        )

        self.subtitle_style = ParagraphStyle(
            "JPSubtitle191",
            parent=styles["Normal"],
            fontName=self.FONT_NAME,
            fontSize=10,
            leading=15,
            textColor=self.MAIN_COLOR,
            alignment=TA_CENTER,
            spaceAfter=9 * mm,
        )

        self.cover_note_style = ParagraphStyle(
            "JPCoverNote191",
            parent=styles["BodyText"],
            fontName=self.FONT_NAME,
            fontSize=8.2,
            leading=13,
            textColor=self.TEXT_COLOR,
            alignment=TA_LEFT,
            spaceAfter=2.5 * mm,
        )

        self.h1_style = ParagraphStyle(
            "JPH1_191",
            parent=styles["Heading1"],
            fontName=self.FONT_BOLD,
            fontSize=15,
            leading=21,
            textColor=self.MAIN_COLOR,
            spaceBefore=2 * mm,
            spaceAfter=4 * mm,
        )

        self.h2_style = ParagraphStyle(
            "JPH2_191",
            parent=styles["Heading2"],
            fontName=self.FONT_BOLD,
            fontSize=10.5,
            leading=15,
            textColor=self.MAIN_COLOR,
            spaceBefore=3.5 * mm,
            spaceAfter=2 * mm,
        )

        self.body_style = ParagraphStyle(
            "JPBody191",
            parent=styles["BodyText"],
            fontName=self.FONT_NAME,
            fontSize=8.3,
            leading=13,
            textColor=self.TEXT_COLOR,
            spaceAfter=2 * mm,
        )

        self.small_style = ParagraphStyle(
            "JPSmall191",
            parent=styles["BodyText"],
            fontName=self.FONT_NAME,
            fontSize=7.1,
            leading=10.5,
            textColor=self.MUTED_COLOR,
        )

        self.table_style = ParagraphStyle(
            "JPTable191",
            parent=styles["BodyText"],
            fontName=self.FONT_NAME,
            fontSize=7.0,
            leading=9.5,
            textColor=self.TEXT_COLOR,
        )

        self.table_header_style = ParagraphStyle(
            "JPTableHeader191",
            parent=self.table_style,
            fontName=self.FONT_BOLD,
            fontSize=6.9,
            leading=9.2,
            textColor=self.WHITE,
            alignment=TA_CENTER,
        )

        self.metric_label_style = ParagraphStyle(
            "JPMetricsLabel191",
            parent=self.table_style,
            fontName=self.FONT_BOLD,
            textColor=self.MAIN_COLOR,
        )

        self.metric_value_style = ParagraphStyle(
            "JPMetricsValue191",
            parent=self.table_style,
            textColor=self.TEXT_COLOR,
        )

    # =========================================================
    # フォント
    # =========================================================

    def _register_japanese_fonts(self):
        """Windows日本語フォントを優先し、なければCIDフォントへフォールバックする。"""
        candidates = [
            ("Meiryo", r"C:\\Windows\\Fonts\\meiryo.ttc", 0),
            ("MeiryoBold", r"C:\\Windows\\Fonts\\meiryob.ttc", 0),
            ("YuGothic", r"C:\\Windows\\Fonts\\YuGothR.ttc", 0),
            ("YuGothicBold", r"C:\\Windows\\Fonts\\YuGothB.ttc", 0),
            ("MSGothic", r"C:\\Windows\\Fonts\\msgothic.ttc", 0),
        ]

        # 実フォントを優先。ReportLabでTTCが扱えない環境もあるため例外時は次へ。
        regular_registered = False
        bold_registered = False

        for name, path, subfont in candidates:
            if not Path(path).exists():
                continue
            try:
                if "Bold" in name:
                    if not bold_registered:
                        pdfmetrics.registerFont(TTFont(name, path, subfontIndex=subfont))
                        bold_registered = True
                else:
                    if not regular_registered:
                        pdfmetrics.registerFont(TTFont(name, path, subfontIndex=subfont))
                        regular_registered = True
            except Exception:
                continue

        if regular_registered:
            regular = "Meiryo" if "Meiryo" in pdfmetrics.getRegisteredFontNames() else (
                "YuGothic" if "YuGothic" in pdfmetrics.getRegisteredFontNames() else "MSGothic"
            )
            if bold_registered:
                bold = "MeiryoBold" if "MeiryoBold" in pdfmetrics.getRegisteredFontNames() else (
                    "YuGothicBold" if "YuGothicBold" in pdfmetrics.getRegisteredFontNames() else regular
                )
            else:
                bold = regular
            return regular, bold

        # Windows側で実フォントが登録できない場合の最終フォールバック。
        cid_name = "HeiseiKakuGo-W5"
        pdfmetrics.registerFont(UnicodeCIDFont(cid_name))
        return cid_name, cid_name

    # =========================================================
    # 共通
    # =========================================================

    def _p(self, text: Any, style=None) -> Paragraph:
        value = "" if text is None else str(text)
        value = (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )
        return Paragraph(value, style or self.body_style)

    def _yen(self, value: Any) -> str:
        if value is None:
            return "—"
        try:
            return f"{float(value):,.0f}円"
        except (TypeError, ValueError):
            return str(value)

    def _percent(self, value: Any) -> str:
        if value is None:
            return "—"
        try:
            return f"{float(value):.1f}%"
        except (TypeError, ValueError):
            return str(value)

    def _build_page_template(self) -> PageTemplate:
        frame = Frame(
            15 * mm,
            16 * mm,
            A4[0] - 30 * mm,
            A4[1] - 30 * mm,
            id="normal",
        )

        def draw_page(canvas, doc):
            canvas.saveState()

            # 上部アクセントライン
            canvas.setStrokeColor(self.SUB_COLOR)
            canvas.setLineWidth(1.0)
            canvas.line(15 * mm, A4[1] - 10 * mm, A4[0] - 15 * mm, A4[1] - 10 * mm)

            # フッター
            canvas.setFillColor(self.MUTED_COLOR)
            canvas.setFont(self.FONT_NAME, 6.8)
            canvas.drawString(15 * mm, 8 * mm, "ちゃぴおHPB Toolkit")
            canvas.drawRightString(
                A4[0] - 15 * mm,
                8 * mm,
                f"{doc.page} ページ",
            )

            canvas.restoreState()

        return PageTemplate(
            id="main",
            frames=[frame],
            onPage=draw_page,
        )

    def _section_bar(self, title: str) -> Table:
        table = Table(
            [[self._p(title, ParagraphStyle(
                "SectionBar191",
                parent=self.table_style,
                fontName=self.FONT_BOLD,
                fontSize=9,
                leading=12,
                textColor=self.WHITE,
            ))]],
            colWidths=[165 * mm],
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.MAIN_COLOR),
            ("BOX", (0, 0), (-1, -1), 0, self.MAIN_COLOR),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    def _metric_table(self, rows: List[List[str]]) -> Table:
        data = []
        for row in rows:
            data.append([
                self._p(row[0], self.metric_label_style),
                self._p(row[1], self.metric_value_style),
            ])

        table = Table(
            data,
            colWidths=[54 * mm, 111 * mm],
            repeatRows=0,
        )

        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.35, self.BORDER_COLOR),
            ("BACKGROUND", (0, 0), (0, -1), self.TABLE_BG),
            ("BACKGROUND", (1, 0), (1, -1), colors.white),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return table

    def _candidate_table(
        self,
        title: str,
        items: List[Dict[str, Any]],
    ) -> List[Any]:
        story = [self._p(title, self.h2_style)]

        if not items:
            story.append(self._p("該当なし", self.small_style))
            story.append(Spacer(1, 1.5 * mm))
            return story

        data = [[
            self._p("価格", self.table_header_style),
            self._p("クーポン名", self.table_header_style),
            self._p("カテゴリ", self.table_header_style),
            self._p("判定", self.table_header_style),
        ]]

        for item in items:
            data.append([
                self._p(self._yen(item.get("price")), self.table_style),
                self._p(item.get("coupon_name", ""), self.table_style),
                self._p(item.get("category", ""), self.table_style),
                self._p(
                    item.get("reason", item.get("direction", "要確認")),
                    self.table_style,
                ),
            ])

        table = Table(
            data,
            colWidths=[21 * mm, 67 * mm, 41 * mm, 36 * mm],
            repeatRows=1,
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.SUB_COLOR),
            ("GRID", (0, 0), (-1, -1), 0.35, self.BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 1), (0, -1), "RIGHT"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

        story.extend([table, Spacer(1, 2.5 * mm)])
        return story

    def _position_color(self, position: str):
        if position == "中央値より高い":
            return colors.HexColor("#F7E7ED")
        if position == "中央値より安い":
            return colors.HexColor("#F3EDF6")
        if position == "中央値付近":
            return colors.HexColor("#F9F3E8")
        return colors.white

    # =========================================================
    # 店舗別レポート
    # =========================================================

    def _build_shop_section(self, report: Dict[str, Any]) -> List[Any]:
        shop_name = report.get("shop_name", "不明店舗")
        coupon_count = report.get("coupon_count", 0)
        pricing = report.get("pricing_result", {}) or {}
        category_analysis = report.get("category_analysis", {}) or {}

        story: List[Any] = []

        # 店舗タイトル
        story.append(self._section_bar(f"【{shop_name}】"))
        story.append(Spacer(1, 3 * mm))

        reference_price = pricing.get("market_reference_price")
        reference_min = pricing.get("reference_price_min")
        reference_max = pricing.get("reference_price_max")

        reference_range = "—"
        if reference_min is not None and reference_max is not None:
            reference_range = f"{self._yen(reference_min)} ～ {self._yen(reference_max)}"

        rows = [
            ["取得クーポン数", f"{coupon_count}件"],
            ["有効価格データ数", f"{pricing.get('shop_price_count', 0)}件"],
            ["自店舗平均価格", self._yen(pricing.get("shop_average"))],
            ["自店舗中央値", self._yen(pricing.get("shop_median"))],
            ["比較対象店舗数", f"{pricing.get('comparison_shop_count', 0)}店舗"],
            ["比較対象クーポン数", f"{pricing.get('comparison_coupon_count', 0)}件"],
            ["比較店舗中央値", self._yen(pricing.get("comparison_median"))],
            ["比較店舗平均との差", self._yen(pricing.get("difference"))],
            ["価格対比率", self._percent(pricing.get("ratio"))],
            ["価格ポジション", pricing.get("position", "比較不可")],
            ["比較方法", pricing.get("comparison_method", "")],
            ["市場参考価格", self._yen(reference_price)],
            ["参考価格帯", reference_range],
            ["参考度", pricing.get("reference_level", "比較不可")],
            ["参考度の理由", pricing.get("reference_reason", "")],
        ]

        story.append(self._metric_table(rows))
        story.append(Spacer(1, 4 * mm))

        # 営業確認候補
        story.append(self._section_bar("営業確認候補"))
        story.append(Spacer(1, 2.5 * mm))
        story.append(self._p(
            "以下は価格の統計・閾値から機械的に抽出した候補です。"
            "異常価格と断定するものではなく、クーポン内容や利用条件を確認するための一覧です。",
            self.small_style,
        ))
        story.append(Spacer(1, 1 * mm))

        quality = pricing.get("price_quality", {}) or {}

        story.extend(self._candidate_table(
            "店舗全体の統計的外れ値候補",
            quality.get("outliers", []),
        ))
        story.extend(self._candidate_table(
            "カテゴリ別の統計的外れ値候補",
            quality.get("category_outliers", []),
        ))
        story.extend(self._candidate_table(
            "低価格要確認",
            quality.get("low_price_attention", []),
        ))
        story.extend(self._candidate_table(
            "高価格要確認",
            quality.get("high_price_attention", []),
        ))

        # 品質判定
        story.append(self._p("価格データ品質", self.h2_style))

        q1 = quality.get("q1")
        q3 = quality.get("q3")
        iqr = quality.get("iqr")
        lower = quality.get("lower_bound")
        upper = quality.get("upper_bound")

        quality_rows = [
            ["品質判定", quality.get("quality_status", "判定対象外")],
            ["品質判定理由", quality.get("quality_reason", "")],
            ["統計的外れ値候補", f"{quality.get('outlier_count', 0)}件"],
            ["カテゴリ別外れ値候補", f"{quality.get('category_outlier_count', 0)}件"],
            ["低価格要確認", f"{quality.get('low_price_attention_count', 0)}件"],
            ["高価格要確認", f"{quality.get('high_price_attention_count', 0)}件"],
        ]

        if q1 is not None:
            quality_rows.extend([
                ["店舗全体Q1", self._yen(q1)],
                ["店舗全体Q3", self._yen(q3)],
                ["店舗全体IQR", self._yen(iqr)],
                ["判定下限", self._yen(lower)],
                ["判定上限", self._yen(upper)],
            ])

        story.append(self._metric_table(quality_rows))
        story.append(Spacer(1, 5 * mm))

        # カテゴリ別価格分析
        story.append(self._section_bar("カテゴリ別価格分析"))
        story.append(Spacer(1, 3 * mm))

        if not category_analysis:
            story.append(self._p("カテゴリ別価格分析データがありません。", self.body_style))
            return story

        category_data = [[
            self._p("カテゴリ", self.table_header_style),
            self._p("自店舗件数", self.table_header_style),
            self._p("自店舗中央値", self.table_header_style),
            self._p("比較店舗数", self.table_header_style),
            self._p("比較件数", self.table_header_style),
            self._p("市場参考価格", self.table_header_style),
            self._p("ポジション", self.table_header_style),
            self._p("参考度", self.table_header_style),
        ]]

        row_positions: List[str] = []
        for category, data in category_analysis.items():
            position = data.get("position", "比較不可")
            row_positions.append(position)
            category_data.append([
                self._p(category, self.table_style),
                self._p(data.get("shop_coupon_count", 0), self.table_style),
                self._p(self._yen(data.get("shop_median")), self.table_style),
                self._p(data.get("comparison_shop_count", 0), self.table_style),
                self._p(data.get("comparison_coupon_count", 0), self.table_style),
                self._p(self._yen(data.get("market_reference_price")), self.table_style),
                self._p(position, self.table_style),
                self._p(data.get("reference_level", "比較不可"), self.table_style),
            ])

        category_table = Table(
            category_data,
            colWidths=[39 * mm, 15 * mm, 23 * mm, 16 * mm, 16 * mm, 24 * mm, 23 * mm, 9 * mm],
            repeatRows=1,
        )

        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), self.MAIN_COLOR),
            ("GRID", (0, 0), (-1, -1), 0.35, self.BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]

        for row_index, position in enumerate(row_positions, start=1):
            bg = self._position_color(position)
            if bg != colors.white:
                style_commands.append(("BACKGROUND", (6, row_index), (6, row_index), bg))

        category_table.setStyle(TableStyle(style_commands))

        story.append(category_table)
        story.append(Spacer(1, 4 * mm))

        return story

    # =========================================================
    # レポート生成
    # =========================================================

    def generate(
        self,
        analysis_reports: List[Dict[str, Any]],
        shop_count: int,
    ) -> str:
        timestamp = datetime.now()
        filename = f"HPB_分析レポート_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = self.output_dir / filename

        doc = BaseDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=16 * mm,
            title="ちゃぴおHPB Toolkit 分析レポート",
            author="ちゃぴおHPB Toolkit",
        )

        doc.addPageTemplates([self._build_page_template()])

        story: List[Any] = []

        # -----------------------------------------------------
        # 表紙
        # -----------------------------------------------------
        story.append(Spacer(1, 18 * mm))
        story.append(self._p("ちゃぴおHPB Toolkit", self.title_style))
        story.append(self._p("クーポン価格分析レポート", self.title_style))
        story.append(self._p(
            "市場参考価格・営業確認候補・カテゴリ別価格分析",
            self.subtitle_style,
        ))

        # ブランドアクセント
        accent = Table([[""]], colWidths=[165 * mm], rowHeights=[2.5 * mm])
        accent.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.MAIN_COLOR),
        ]))
        story.append(accent)
        story.append(Spacer(1, 7 * mm))

        total_coupons = sum(
            int(report.get("coupon_count", 0))
            for report in analysis_reports
        )

        overview_rows = [
            ["作成日時", timestamp.strftime("%Y年%m月%d日 %H:%M")],
            ["分析対象店舗数", f"{shop_count}店舗"],
            ["レポートバージョン", self.VERSION],
            ["総取得クーポン数", f"{total_coupons}件"],
        ]

        story.append(self._metric_table(overview_rows))
        story.append(Spacer(1, 9 * mm))

        story.append(self._p(
            "本レポートは、HotPepper Beautyから取得したクーポン情報をもとに、"
            "自店舗価格と比較店舗の価格を分析したものです。",
            self.cover_note_style,
        ))
        story.append(self._p(
            "「営業確認候補」は統計・価格閾値による機械的な抽出であり、"
            "クーポンの内容や利用条件を踏まえた人による確認を前提とします。",
            self.cover_note_style,
        ))

        # -----------------------------------------------------
        # 店舗別
        # -----------------------------------------------------
        for report in analysis_reports:
            story.append(PageBreak())
            story.extend(self._build_shop_section(report))

        doc.build(story)
        return str(output_path)
