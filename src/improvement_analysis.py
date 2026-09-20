from __future__ import annotations

from typing import Any, Dict, List, Optional


class ImprovementAnalyzer:
    """
    ちゃぴおHPB Toolkit v2.1.0
    第6章「自店舗への改善提案」分析エンジン。

    現段階では、既存の価格分析・カテゴリ比較・
    価格品質分析から「改善検討候補」を機械的に生成する。
    将来、HPB運用ノウハウの知識ベース/AIと接続する前提の構造。
    """

    POSITION_THRESHOLD = 5.0

    def _num(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = (
            str(value)
            .replace(",", "")
            .replace("円", "")
            .replace("￥", "")
            .replace("¥", "")
            .replace("%", "")
            .strip()
        )
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _text(self, value: Any) -> str:
        return "" if value is None else str(value).strip()

    def _price(self, value: Any) -> str:
        number = self._num(value)
        return "—" if number is None else f"{number:,.0f}円"

    def _reference_level(self, data: Dict[str, Any]) -> str:
        return self._text(
            data.get("reference_level")
            or data.get("reference_confidence")
            or "比較不可"
        )

    def _base(
        self,
        title: str,
        category: str,
        reason: str,
        current: Optional[float],
        reference: Optional[float],
        detail: str,
        action: str,
        priority: str = "確認候補",
    ) -> Dict[str, Any]:
        return {
            "title": title,
            "category": category,
            "priority": priority,
            "reason": reason,
            "current_price": current,
            "reference_price": reference,
            "current_price_display": self._price(current),
            "reference_price_display": self._price(reference),
            "detail": detail,
            "action": action,
        }

    def _overall(
        self,
        pricing: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        current = self._num(pricing.get("shop_median"))
        reference = self._num(
            pricing.get("market_reference_price")
            or pricing.get("comparison_median")
        )
        if current is None or reference is None or reference <= 0:
            return None

        ratio = self._num(pricing.get("ratio"))
        if ratio is None:
            ratio = current / reference * 100

        level = self._reference_level(pricing)

        if level not in {"高", "中"}:
            return {
                "title": "市場参考価格の確認",
                "category": "全体価格",
                "priority": "参考情報",
                "reason": (
                    "市場参考価格の参考度が低いため、"
                    "価格変更の根拠としては慎重に扱います。"
                ),
                "current_price": current,
                "reference_price": reference,
                "current_price_display": self._price(current),
                "reference_price_display": self._price(reference),
                "detail": (
                    f"自店舗中央値{self._price(current)}、"
                    f"市場参考価格{self._price(reference)}です。"
                ),
                "action": (
                    "比較店舗数・有効クーポン数・クーポン内容を確認してから"
                    "価格変更の要否を判断します。"
                ),
            }

        if ratio < 95:
            return self._base(
                "クーポン価格水準の見直し候補",
                "全体価格",
                f"自店舗中央値が市場参考価格を下回り、価格対比率は{ratio:.1f}%です。",
                current,
                reference,
                f"自店舗中央値{self._price(current)}、市場参考価格{self._price(reference)}です。",
                (
                    "一律値上げではなく、カテゴリ別の価格差と各クーポンの"
                    "内容・所要時間・利用条件を確認し、見直し対象を絞ります。"
                ),
            )

        if ratio > 105:
            return self._base(
                "クーポン価格水準の整合性確認",
                "全体価格",
                f"自店舗中央値が市場参考価格を上回り、価格対比率は{ratio:.1f}%です。",
                current,
                reference,
                f"自店舗中央値{self._price(current)}、市場参考価格{self._price(reference)}です。",
                (
                    "値下げを前提とせず、メニュー内容・付加価値・利用条件が"
                    "掲載内容から十分に伝わるか確認します。"
                ),
            )

        return None

    def _categories(
        self,
        category_analysis: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []

        for category, data in category_analysis.items():
            if not isinstance(data, dict):
                continue

            current = self._num(data.get("shop_median"))
            reference = self._num(
                data.get("market_reference_price")
                or data.get("comparison_median")
            )
            if current is None or reference is None or reference <= 0:
                continue

            level = self._reference_level(data)
            if level not in {"高", "中"}:
                continue

            ratio = self._num(data.get("ratio"))
            if ratio is None:
                ratio = current / reference * 100

            if ratio < 95:
                result.append(
                    self._base(
                        "カテゴリ価格の見直し候補",
                        category,
                        (
                            f"{category}の自店舗中央値が市場参考価格を下回り、"
                            f"価格対比率は{ratio:.1f}%です。"
                        ),
                        current,
                        reference,
                        (
                            f"自店舗中央値{self._price(current)}、"
                            f"市場参考価格{self._price(reference)}です。"
                        ),
                        (
                            "該当カテゴリのクーポンを個別確認し、価格・施術内容・"
                            "所要時間・利用条件を踏まえて見直し対象を選定します。"
                        ),
                    )
                )

            elif ratio > 105:
                result.append(
                    self._base(
                        "カテゴリ価格と掲載内容の整合性確認",
                        category,
                        (
                            f"{category}の自店舗中央値が市場参考価格を上回り、"
                            f"価格対比率は{ratio:.1f}%です。"
                        ),
                        current,
                        reference,
                        (
                            f"自店舗中央値{self._price(current)}、"
                            f"市場参考価格{self._price(reference)}です。"
                        ),
                        (
                            "価格変更を前提とせず、メニュー内容や付加価値が"
                            "掲載内容から十分伝わる状態か確認します。"
                        ),
                    )
                )

        return result

    def _quality(
        self,
        pricing: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        quality = pricing.get("price_quality", {})
        if not isinstance(quality, dict):
            return []

        groups = [
            ("outliers", "統計的外れ値候補", "価格分布上の確認候補"),
            ("category_outliers", "カテゴリ別統計的外れ値候補", "カテゴリ内の価格分布上の確認候補"),
            ("low_price_attention", "低価格要確認", "極端な低価格のため内容確認が必要な候補"),
            ("high_price_attention", "高価格要確認", "極端な高価格のため内容確認が必要な候補"),
        ]

        result: List[Dict[str, Any]] = []

        for key, label, default_reason in groups:
            items = quality.get(key, [])
            if not isinstance(items, list):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue

                name = self._text(
                    item.get("coupon_name")
                    or item.get("title")
                    or item.get("name")
                    or "クーポン"
                )
                category = self._text(
                    item.get("category")
                    or item.get("normalized_category")
                    or "カテゴリ不明"
                )
                price = self._num(item.get("price"))
                reason = self._text(item.get("reason")) or default_reason

                result.append(
                    {
                        "title": f"{label}：内容確認候補",
                        "category": category,
                        "priority": "確認候補",
                        "reason": reason,
                        "current_price": price,
                        "reference_price": None,
                        "current_price_display": self._price(price),
                        "reference_price_display": "—",
                        "coupon_name": name,
                        "detail": f"クーポン「{name}」が価格分析上の確認候補として抽出されています。",
                        "action": (
                            "価格だけで異常と判断せず、クーポン名・施術内容・"
                            "利用条件・対象者条件を確認します。"
                        ),
                    }
                )

        return result

    def analyze(
        self,
        primary_shop: Any,
        pricing_result: Optional[Dict[str, Any]] = None,
        category_analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        pricing = pricing_result if isinstance(pricing_result, dict) else {}
        categories = category_analysis if isinstance(category_analysis, dict) else {}

        shop_name = self._text(getattr(primary_shop, "name", "")) or "自店舗"

        proposals: List[Dict[str, Any]] = []

        overall = self._overall(pricing)
        if overall:
            proposals.append(overall)

        proposals.extend(self._categories(categories))
        proposals.extend(self._quality(pricing))

        # 第6章初版では読みやすさを優先してカテゴリ候補を最大6件に制限。
        normal = [
            p for p in proposals
            if not p.get("coupon_name")
            and p.get("category") != "全体価格"
        ][:6]

        others = [
            p for p in proposals
            if p.get("coupon_name")
            or p.get("category") == "全体価格"
        ]

        final = others + normal

        return {
            "version": "v2.1.0",
            "shop_name": shop_name,
            "chapter_title": "6. 自店舗への改善提案",
            "proposal_count": len(final),
            "proposals": final,
            "summary": self._summary(final),
            "limitations": [
                "本章は価格分析・カテゴリ比較・価格品質分析から機械的に生成した改善検討候補です。",
                "クーポン内容・利用条件・対象者条件を確認せず、変更を断定するものではありません。",
                "市場参考価格の参考度が低い場合は、価格変更を強く提案しない設計です。",
                "HPB運用ノウハウを用いた具体的なページ文章・クーポン名・説明文の生成は、今後の知識ベース連携で拡張します。",
            ],
        }

    def _summary(self, proposals: List[Dict[str, Any]]) -> str:
        if not proposals:
            return "今回の価格分析データから、明確な改善検討候補は抽出されませんでした。"

        category_count = sum(
            1 for p in proposals
            if p.get("category") not in {"全体価格"}
            and not p.get("coupon_name")
        )
        quality_count = sum(1 for p in proposals if p.get("coupon_name"))
        overall_count = sum(1 for p in proposals if p.get("category") == "全体価格")

        parts = []
        if overall_count:
            parts.append("店舗全体の価格水準に関する確認候補")
        if category_count:
            parts.append(f"カテゴリ価格に関する検討候補{category_count}件")
        if quality_count:
            parts.append(f"クーポン内容の確認候補{quality_count}件")

        return "今回の分析では、" + "、".join(parts) + "を抽出しました。"


def analyze_improvements(
    primary_shop: Any,
    pricing_result: Optional[Dict[str, Any]] = None,
    category_analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return ImprovementAnalyzer().analyze(
        primary_shop=primary_shop,
        pricing_result=pricing_result,
        category_analysis=category_analysis,
    )
