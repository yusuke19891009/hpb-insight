from __future__ import annotations

import json
import os
import re
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen

from pypdf import PdfReader


VERSION = "v2.3.0"


def _to_number(value: str) -> Optional[float]:
    if value is None:
        return None

    value = (
        str(value)
        .replace(",", "")
        .replace("¥", "")
        .replace("￥", "")
        .replace("%", "")
        .strip()
    )

    if not value:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _percent(value: Optional[float]) -> Optional[float]:
    return value


def _ratio(
    a: Optional[float],
    b: Optional[float],
) -> Optional[float]:
    if a is None or b in (None, 0):
        return None

    return a / b * 100.0


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    return re.sub(r"[ \t]+", " ", text)


class HPBDetailReportParser:
    """HotPepper Beautyの自店舗詳細レポートPDFを構造化する。"""

    def parse(
        self,
        pdf_path: str | Path,
    ) -> Dict[str, Any]:

        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDFが見つかりません: {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                "PDFファイルを指定してください。"
            )

        reader = PdfReader(str(path))

        pages = [
            _clean_text(
                page.extract_text() or ""
            )
            for page in reader.pages
        ]

        full = "\n".join(pages)

        data: Dict[str, Any] = {
            "version": VERSION,
            "source_file": path.name,
            "page_count": len(pages),
            "shop": self._parse_shop_info(full),
            "summary": self._parse_summary(
                pages,
                full,
            ),
            "traffic": self._parse_traffic(
                pages
            ),
            "reviews": self._parse_reviews(
                pages
            ),
            "listing": self._parse_listing(
                pages
            ),
            "coupon": self._parse_coupon(
                pages
            ),
            "demographics": self._parse_demographics(
                pages
            ),
            "staff": self._parse_staff(
                pages
            ),
            "raw_sections": {
                "summary": (
                    pages[3]
                    if len(pages) >= 4
                    else ""
                ),
                "pv": (
                    pages[4]
                    if len(pages) >= 5
                    else ""
                ),
                "cvr": (
                    pages[10]
                    if len(pages) >= 11
                    else ""
                ),
                "acr": (
                    pages[13]
                    if len(pages) >= 14
                    else ""
                ),
                "coupon": (
                    pages[15]
                    if len(pages) >= 16
                    else ""
                ),
            },
        }

        data["data_quality"] = self._quality(
            data
        )

        return data

    def _parse_shop_info(
        self,
        full: str,
    ) -> Dict[str, Any]:

        hcode = re.search(
            r"H\s*コード\s*(H\d+)",
            full,
        )

        plan = re.search(
            r"プラン\s*([^\n]+)",
            full,
        )

        return {
            "h_code": (
                hcode.group(1)
                if hcode
                else None
            ),
            "plan": (
                plan.group(1).strip()
                if plan
                else None
            ),
        }

    def _parse_summary(
        self,
        pages: List[str],
        full: str,
    ) -> Dict[str, Any]:

        text = (
            pages[3]
            if len(pages) >= 4
            else full
        )

        result: Dict[str, Any] = {}

        m = re.search(
            r"売上.{0,40}?([\d.]+)万円",
            text,
            re.S,
        )

        if m:
            result["sales_man_yen"] = float(
                m.group(1)
            )
            result["sales_yen"] = (
                float(m.group(1)) * 10000
            )

        m = re.search(
            r"新規売上.*?([\d.]+)万円.*?([\d.]+)万円",
            text,
            re.S,
        )

        if m:
            result[
                "new_sales_man_yen"
            ] = float(m.group(1))

            result[
                "repeat_sales_man_yen"
            ] = float(m.group(2))

        m = re.search(
            r"HPB ネット予.*?(\d+)\s+(\d+)\s+(\d+)",
            text,
            re.S,
        )

        if m:
            result["reservations"] = int(
                m.group(1)
            )
            result[
                "new_reservations"
            ] = int(m.group(2))
            result[
                "repeat_reservations"
            ] = int(m.group(3))

        if (
            "reservations" not in result
            and pages
        ):
            reservation_text = pages[0]

            m = re.search(
                r"HPB ネット予.*?(\d+)\s+(\d+)\s+(\d+)",
                reservation_text,
                re.S,
            )

            if m:
                result[
                    "reservations"
                ] = int(m.group(1))

                result[
                    "new_reservations"
                ] = int(m.group(2))

                result[
                    "repeat_reservations"
                ] = int(m.group(3))

        m = re.search(
            r"TOP PV.*?(\d[\d,]*)\s+(\d[\d,]*)\s+(\d[\d,]*)",
            text,
            re.S,
        )

        if m:
            result["top_pv"] = int(
                m.group(1).replace(",", "")
            )

            result[
                "comparison_pv"
            ] = int(
                m.group(2).replace(",", "")
            )

            result[
                "area_plan_pv"
            ] = int(
                m.group(3).replace(",", "")
            )

        m = re.search(
            r"CVR.*?([\d.]+)%.*?([\d.]+)%.*?([\d.]+)%",
            text,
            re.S,
        )

        if m:
            result["cvr"] = float(
                m.group(1)
            )

            result[
                "comparison_cvr"
            ] = float(
                m.group(2)
            )

            result[
                "area_plan_cvr"
            ] = float(
                m.group(3)
            )

        m = re.search(
            r"ACR.*?([\d.]+)%.*?([\d.]+)%.*?([\d.]+)%",
            text,
            re.S,
        )

        if m:
            result["acr"] = float(
                m.group(1)
            )

            result[
                "comparison_acr"
            ] = float(
                m.group(2)
            )

            result[
                "area_plan_acr"
            ] = float(
                m.group(3)
            )

        return result

    def _parse_traffic(
        self,
        pages: List[str],
    ) -> Dict[str, Any]:

        result: Dict[str, Any] = {}

        if len(pages) >= 5:
            text = pages[4]

            m = re.search(
                r"TOP PV.*?(\d[\d,]*)",
                text,
                re.S,
            )

            if m:
                result["top_pv"] = int(
                    m.group(1).replace(
                        ",",
                        "",
                    )
                )

        return result

    def _parse_reviews(
        self,
        pages: List[str],
    ) -> Dict[str, Any]:

        if len(pages) < 13:
            return {}

        text = pages[12]

        result: Dict[str, Any] = {}

        m = re.search(
            r"サロン\s+(\d+)\s+([\d.]+)%.*?サロン平\s+(\d+)\s+([\d.]+)%",
            text,
            re.S,
        )

        if m:
            result.update(
                count=int(m.group(1)),
                reply_rate=float(
                    m.group(2)
                ),
                comparison_count=int(
                    m.group(3)
                ),
                comparison_reply_rate=float(
                    m.group(4)
                ),
            )

        m = re.search(
            r"サロン\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+).*?サロン平\s+([\d.]+)",
            text,
            re.S,
        )

        if m:
            result[
                "overall_score"
            ] = float(m.group(1))

            result[
                "atmosphere"
            ] = float(m.group(2))

            result[
                "service"
            ] = float(m.group(3))

            result[
                "technical"
            ] = float(m.group(4))

            result[
                "menu_price"
            ] = float(m.group(5))

            result[
                "comparison_overall_score"
            ] = float(m.group(6))

        return result

    def _parse_listing(
        self,
        pages: List[str],
    ) -> Dict[str, Any]:

        if len(pages) < 3:
            return {}

        text = pages[2]

        result: Dict[str, Any] = {}

        m = re.search(
            r"セット.*?(\d+)\s*席?\s*¥([\d,]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
            text,
        )

        if m:
            result.update(
                seats=int(m.group(1)),
                cut_price=int(
                    m.group(2).replace(
                        ",",
                        "",
                    )
                ),
                reviews=int(m.group(3)),
                blogs=int(m.group(4)),
                styles=int(m.group(5)),
                coupons=int(m.group(6)),
            )

        return result

    def _parse_coupon(
        self,
        pages: List[str],
    ) -> Dict[str, Any]:

        result: Dict[str, Any] = {}

        if len(pages) >= 16:

            text = pages[15]

            m = re.search(
                r"自サロン.*?([\d.]+)%\s+([\d.]+)%",
                text,
                re.S,
            )

            if m:
                result[
                    "new_repeat_new"
                ] = float(m.group(1))

                result[
                    "new_repeat_repeat"
                ] = float(m.group(2))

            m = re.search(
                r"現在.*?クーポン種別.*?\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
                text,
                re.S,
            )

            if m:
                result.update(
                    coupon_count=int(
                        m.group(1)
                    ),
                    new_label_count=int(
                        m.group(2)
                    ),
                    repeat_label_count=int(
                        m.group(3)
                    ),
                    all_label_count=int(
                        m.group(4)
                    ),
                )

            m = re.search(
                r"ネット平.*?¥([\d,]+).*?規.*?¥([\d,]+).*?リピート.*?¥([\d,]+)",
                text,
                re.S,
            )

            if m:
                result.update(
                    average_price=int(
                        m.group(1).replace(
                            ",",
                            "",
                        )
                    ),
                    new_average_price=int(
                        m.group(2).replace(
                            ",",
                            "",
                        )
                    ),
                    repeat_average_price=int(
                        m.group(3).replace(
                            ",",
                            "",
                        )
                    ),
                )

        return result

    def _parse_demographics(
        self,
        pages: List[str],
    ) -> Dict[str, Any]:

        if not pages:
            return {}

        text = pages[0]

        result: Dict[str, Any] = {}

        m = re.search(
            r"女性率\s+((?:\d+%\s+){12,}\d+%)\s+男性率\s+((?:\d+%\s+){12,}\d+%)",
            text,
        )

        if m:
            women = [
                int(x)
                for x in re.findall(
                    r"\d+",
                    m.group(1),
                )
            ]

            men = [
                int(x)
                for x in re.findall(
                    r"\d+",
                    m.group(2),
                )
            ]

            if women:
                result[
                    "latest_women_rate"
                ] = women[-1]

            if men:
                result[
                    "latest_men_rate"
                ] = men[-1]

        m = re.search(
            r"20代未満\s+((?:\d+%\s+){12,}\d+%)\s+20代\s+((?:\d+%\s+){12,}\d+%)\s+30代\s+((?:\d+%\s+){12,}\d+%)\s+40代\s+((?:\d+%\s+){12,}\d+%)\s+50代以上\s+((?:\d+%\s+){12,}\d+%)",
            text,
        )

        if m:
            labels = [
                "under20",
                "20s",
                "30s",
                "40s",
                "50plus",
            ]

            for label, group in zip(
                labels,
                m.groups(),
            ):
                values = [
                    int(x)
                    for x in re.findall(
                        r"\d+",
                        group,
                    )
                ]

                if values:
                    result[
                        label
                    ] = values[-1]

        return result

    def _parse_staff(
        self,
        pages: List[str],
    ) -> Dict[str, Any]:

        if len(pages) < 20:
            return {}

        text = pages[19]

        result: Dict[str, Any] = {}

        m = re.search(
            r"平均\s+([\d.]+)\s+([\d.]+)\s+¥([\d,]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)%\s+([\d.]+)%",
            text,
        )

        if m:
            result.update(
                average_sales_man_yen=float(
                    m.group(1)
                ),
                average_reservations=int(
                    float(m.group(2))
                ),
                average_ticket=int(
                    m.group(3).replace(
                        ",",
                        "",
                    )
                ),
                average_capacity=float(
                    m.group(4)
                ),
                average_weekend_capacity=float(
                    m.group(5)
                ),
                average_fill_rate=float(
                    m.group(6)
                ),
                average_weekend_fill_rate=float(
                    m.group(7)
                ),
            )

        return result

    def _quality(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        required = [
            (
                "PV",
                data.get(
                    "summary",
                    {},
                ).get(
                    "top_pv"
                ),
            ),
            (
                "CVR",
                data.get(
                    "summary",
                    {},
                ).get(
                    "cvr"
                ),
            ),
            (
                "ACR",
                data.get(
                    "summary",
                    {},
                ).get(
                    "acr"
                ),
            ),
            (
                "予約数",
                data.get(
                    "summary",
                    {},
                ).get(
                    "reservations"
                ),
            ),
        ]

        missing = [
            name
            for name, value
            in required
            if value is None
        ]

        return {
            "status": (
                "OK"
                if not missing
                else "一部不足"
            ),
            "missing": missing,
        }


class QuantitativeAnalyzer:
    """
    HPB詳細レポートの数字から、
    自店舗の特徴を分かりやすく整理する。
    """

    def _comparison_text(
        self,
        current: Optional[float],
        reference: Optional[float],
        label: str,
    ) -> str:

        if (
            current is None
            or reference is None
        ):
            return (
                f"{label}は比較できる基準値がないため、"
                "今回の数字だけでは判断できません。"
            )

        difference = current - reference

        if abs(difference) < 0.05:
            return (
                f"{label}は比較基準とほぼ同じ水準です。"
            )

        if difference > 0:
            return (
                f"{label}は比較基準より高い水準です。"
            )

        return (
            f"{label}は比較基準より低い水準です。"
        )

    def analyze(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        summary = data.get(
            "summary",
            {},
        )

        reviews = data.get(
            "reviews",
            {},
        )

        listing = data.get(
            "listing",
            {},
        )

        coupon = data.get(
            "coupon",
            {},
        )

        insights: List[
            Dict[str, Any]
        ] = []

        # -------------------------------------------------
        # 発見 = PV
        # -------------------------------------------------

        pv = summary.get(
            "top_pv"
        )

        area_pv = summary.get(
            "area_plan_pv"
        )

        if pv is not None:

            text = (
                "サロン情報PVは、Hot Pepper Beautyで検索したお客様が、"
                "検索結果からこの店舗ページを開いた回数です。"
            )

            if (
                area_pv is not None
            ):
                text += " "
                text += (
                    self._comparison_text(
                        pv,
                        area_pv,
                        "PV"
                    )
                )

            text += (
                " 数字が高い場合は、"
                "店舗ページを見てもらう機会が多い状態と考えられます。"
            )

            insights.append(
                {
                    "title": "発見（PV）",
                    "text": text,
                    "evidence": (
                        f"PV {pv:,}"
                        + (
                            f" / エリア同プラン {area_pv:,}"
                            if area_pv is not None
                            else ""
                        )
                    ),
                }
            )

        # -------------------------------------------------
        # 興味喚起 = CVR
        # -------------------------------------------------

        cvr = summary.get(
            "cvr"
        )

        area_cvr = summary.get(
            "area_plan_cvr"
        )

        if cvr is not None:

            text = (
                "CVRは、店舗ページを見たお客様のうち、"
                "「クーポン・メニュー」を見た割合です。"
            )

            if area_cvr is not None:
                text += " "
                text += (
                    self._comparison_text(
                        cvr,
                        area_cvr,
                        "CVR"
                    )
                )

            text += (
                " 店舗ページを見た後に、"
                "クーポンやメニューまで見てもらえているかを確認できます。"
            )

            insights.append(
                {
                    "title": "興味喚起（CVR）",
                    "text": text,
                    "evidence": (
                        f"CVR {cvr:.1f}%"
                        + (
                            f" / エリア同プラン {area_cvr:.1f}%"
                            if area_cvr is not None
                            else ""
                        )
                    ),
                }
            )

        # -------------------------------------------------
        # アクション = ACR
        # -------------------------------------------------

        acr = summary.get(
            "acr"
        )

        area_acr = summary.get(
            "area_plan_acr"
        )

        if acr is not None:

            text = (
                "ACRは、「クーポン・メニュー」を見たお客様のうち、"
                "予約完了ページまで進んだ割合です。"
            )

            if area_acr is not None:
                text += " "
                text += (
                    self._comparison_text(
                        acr,
                        area_acr,
                        "ACR"
                    )
                )

            text += (
                " クーポンを見た後に、"
                "予約まで進んでいるかを確認できます。"
            )

            insights.append(
                {
                    "title": "アクション（ACR）",
                    "text": text,
                    "evidence": (
                        f"ACR {acr:.1f}%"
                        + (
                            f" / エリア同プラン {area_acr:.1f}%"
                            if area_acr is not None
                            else ""
                        )
                    ),
                }
            )

        # -------------------------------------------------
        # 3指標の組み合わせ
        # -------------------------------------------------

        if (
            pv is not None
            and cvr is not None
            and acr is not None
        ):

            parts = []

            if (
                area_pv is not None
            ):
                parts.append(
                    "PVは"
                    + (
                        "比較基準より高い"
                        if pv > area_pv
                        else "比較基準以下"
                    )
                )

            if (
                area_cvr is not None
            ):
                parts.append(
                    "CVRは"
                    + (
                        "比較基準より高い"
                        if cvr > area_cvr
                        else "比較基準以下"
                    )
                )

            if (
                area_acr is not None
            ):
                parts.append(
                    "ACRは"
                    + (
                        "比較基準より高い"
                        if acr > area_acr
                        else "比較基準以下"
                    )
                )

            if parts:

                text = (
                    "今回の数字では、"
                    + "、".join(parts)
                    + "という結果です。"
                )

                text += (
                    " 3つの数字を合わせて見ることで、"
                    "店舗を見つけてもらえているか、"
                    "クーポンを見てもらえているか、"
                    "予約まで進んでいるかを順番に確認できます。"
                )

                insights.append(
                    {
                        "title": "PV・CVR・ACRを合わせて確認",
                        "text": text,
                        "evidence": (
                            f"PV {pv:,} / "
                            f"CVR {cvr:.1f}% / "
                            f"ACR {acr:.1f}%"
                        ),
                    }
                )

        # -------------------------------------------------
        # 売上・予約
        # -------------------------------------------------

        sales = summary.get(
            "sales_man_yen"
        )

        reservations = summary.get(
            "reservations"
        )

        if (
            sales is not None
            and reservations
        ):

            ticket = (
                sales
                * 10000
                / reservations
            )

            insights.append(
                {
                    "title": "売上・予約",
                    "text": (
                        f"前月売上は{sales:.1f}万円、"
                        f"予約数は{reservations}件です。"
                        f" 売上を予約数で割ると、"
                        f"1予約あたり約{ticket:,.0f}円です。"
                        " HPB上の客単価と合わせて確認します。"
                    ),
                    "evidence": (
                        f"売上 {sales:.1f}万円 / "
                        f"予約 {reservations}件"
                    ),
                }
            )

        # -------------------------------------------------
        # 口コミ
        # -------------------------------------------------

        review_count = reviews.get(
            "count"
        )

        comparison_review_count = reviews.get(
            "comparison_count"
        )

        if (
            review_count is not None
        ):

            text = (
                f"口コミは{review_count}件です。"
            )

            if comparison_review_count is not None:

                difference = (
                    review_count
                    - comparison_review_count
                )

                text += (
                    f" 比較サロン平均との差は"
                    f"{difference:+d}件です。"
                )

            reply_rate = reviews.get(
                "reply_rate"
            )

            if reply_rate is not None:
                text += (
                    f" 口コミ返信率は"
                    f"{reply_rate:.1f}%です。"
                )

            insights.append(
                {
                    "title": "口コミ・評価",
                    "text": text,
                    "evidence": (
                        f"口コミ {review_count}件"
                    ),
                }
            )

        # -------------------------------------------------
        # 掲載量
        # -------------------------------------------------

        styles = listing.get(
            "styles"
        )

        coupons = listing.get(
            "coupons"
        )

        if (
            styles is not None
            and coupons is not None
        ):

            insights.append(
                {
                    "title": "掲載量",
                    "text": (
                        f"掲載中のスタイルは{styles}件、"
                        f"クーポンは{coupons}件です。"
                        " 数量だけで判断せず、"
                        "PV・CVR・ACRと合わせて確認します。"
                    ),
                    "evidence": (
                        f"スタイル {styles}件 / "
                        f"クーポン {coupons}件"
                    ),
                }
            )

        # -------------------------------------------------
        # クーポン構成
        # -------------------------------------------------

        coupon_count = coupon.get(
            "coupon_count"
        )

        new_count = coupon.get(
            "new_label_count"
        )

        repeat_count = coupon.get(
            "repeat_label_count"
        )

        all_count = coupon.get(
            "all_label_count"
        )

        if (
            coupon_count is not None
            and new_count is not None
            and repeat_count is not None
        ):

            text = (
                f"掲載クーポンは{coupon_count}件です。"
                f" 新規向け{new_count}件、"
                f"再来向け{repeat_count}件"
            )

            if all_count is not None:
                text += (
                    f"、全員向け{all_count}件"
                )

            text += (
                "です。予約数や新規・再来の構成と"
                "合わせて確認できます。"
            )

            insights.append(
                {
                    "title": "クーポン構成",
                    "text": text,
                    "evidence": (
                        f"クーポン {coupon_count}件 / "
                        f"新規 {new_count} / "
                        f"再来 {repeat_count}"
                    ),
                }
            )

        return {
            "version": VERSION,
            "insights": insights,
            "summary": self._summary(
                insights
            ),
        }

    def _summary(
        self,
        insights: List[Dict[str, Any]],
    ) -> str:

        if not insights:
            return (
                "数字から特徴を確認するための"
                "主要データが不足しています。"
            )

        return (
            f"HPB詳細レポートから"
            f"{len(insights)}項目の"
            "数字から分かる特徴を整理しました。"
        )


class OptionalAIAnalyzer:
    """
    OpenAI Responses APIを任意で利用するAI分析層。

    APIキーがなければ実行しない。
    """

    def analyze(
        self,
        data: Dict[str, Any],
        base_analysis: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:

        api_key = os.getenv(
            "OPENAI_API_KEY"
        )

        if not api_key:
            return None

        model = os.getenv(
            "HPB_AI_MODEL",
            "gpt-5.6-luna",
        )

        payload = {
            "model": model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "あなたはHotPepper Beautyの"
                        "店舗分析を補助する分析AIです。"
                        "\n\n"
                        "与えられたHPB詳細レポートの"
                        "数字だけを根拠に、自店舗の特徴を"
                        "分かりやすい日本語で整理してください。"
                        "\n\n"
                        "重要な指標の定義："
                        "\n"
                        "発見 = サロン情報PV数。"
                        "Hot Pepper Beautyで検索したお客様が、"
                        "検索結果から店舗ページを開いた回数。"
                        "\n"
                        "興味喚起 = CVR。"
                        "店舗ページを見たお客様のうち、"
                        "「クーポン・メニュー」を見た割合。"
                        "\n"
                        "アクション = ACR。"
                        "「クーポン・メニュー」を見たお客様のうち、"
                        "予約完了ページまで進んだ割合。"
                        "\n\n"
                        "『ファネル』『発見段階』などの"
                        "専門的な表現は使わないでください。"
                        "\n"
                        "事実→分かること→確認ポイントの順で"
                        "簡潔に記述してください。"
                        "\n"
                        "価格変更や施策を直接断定・推奨せず、"
                        "確認すべき点として表現してください。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "metrics": data,
                            "pre_analysis": base_analysis,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        }

        request = Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(
                payload,
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={
                "Authorization": (
                    f"Bearer {api_key}"
                ),
                "Content-Type": (
                    "application/json"
                ),
            },
            method="POST",
        )

        try:

            with urlopen(
                request,
                timeout=60,
            ) as response:

                result = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

            output_text = result.get(
                "output_text",
                "",
            ).strip()

            if not output_text:
                return None

            return {
                "model": model,
                "text": output_text,
            }

        except Exception as exc:

            return {
                "model": model,
                "error": str(exc),
            }


def analyze_hpb_detail_pdf(
    pdf_path: str | Path,
) -> Dict[str, Any]:

    parser = HPBDetailReportParser()

    data = parser.parse(
        pdf_path
    )

    analyzer = QuantitativeAnalyzer()

    base_analysis = analyzer.analyze(
        data
    )

    ai_analysis = OptionalAIAnalyzer().analyze(
        data,
        base_analysis,
    )

    return {
        "metrics": data,
        "analysis": base_analysis,
        "ai_analysis": ai_analysis,
    }