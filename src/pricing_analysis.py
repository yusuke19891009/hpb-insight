from __future__ import annotations

from statistics import median
from typing import Any, Dict, List, Optional


class PricingAnalyzer:
    """
    HotPepper Beauty クーポン価格の市場比較分析を行うクラス。

    v1.8.0
    - 店舗別中央値を同じ重みで比較
    - カテゴリ名を正規化して比較
    - 「その他」を含むカテゴリを正規化
    - 店舗ごとのカテゴリ中央値を算出して比較
    - 市場参考価格を算出
    - 参考価格帯を算出
    - 参考度を比較店舗数＋比較クーポン数から判定
    """

    CATEGORY_ORDER = [
        "カット",
        "カラー",
        "パーマ",
        "縮毛矯正",
        "トリートメント",
        "ヘッドスパ",
        "エクステ",
        "その他",
    ]

    def _get_valid_price(
        self,
        coupon: Any,
    ) -> Optional[int]:
        """クーポンから有効な価格を取得する。"""

        price = getattr(coupon, "price", None)

        if price is None:
            return None

        if isinstance(price, str):
            value = (
                price.replace(",", "")
                .replace("円", "")
                .replace("￥", "")
                .replace("¥", "")
                .strip()
            )

            if not value:
                return None

            try:
                price = int(float(value))
            except ValueError:
                return None

        try:
            price = int(price)
        except (TypeError, ValueError):
            return None

        if price <= 0:
            return None

        return price

    def _clean_value(
        self,
        value: Any,
    ) -> str:
        """文字列を正規化する。"""

        if value is None:
            return ""

        return str(value).strip()

    # =========================================================
    # カテゴリ正規化
    # =========================================================

    def _normalize_category(
        self,
        category: Any,
    ) -> str:
        """
        カテゴリ名を比較用に正規化する。

        例:
        カラー + カット + トリートメント
        →
        カット + カラー + トリートメント

        カット + カラー + トリートメント + その他
        →
        カット + カラー + トリートメント

        カット + その他
        →
        カット
        """

        value = self._clean_value(category)

        if not value:
            return ""

        parts = value.split("+")
        cleaned_parts: List[str] = []

        for part in parts:
            part = part.strip()

            if not part:
                continue

            if part not in cleaned_parts:
                cleaned_parts.append(part)

        if not cleaned_parts:
            return ""

        # 「その他」が他のカテゴリと一緒なら除外
        if len(cleaned_parts) > 1:
            cleaned_parts = [
                part
                for part in cleaned_parts
                if part != "その他"
            ]

        if not cleaned_parts:
            return "その他"

        order_map = {
            name: index
            for index, name in enumerate(
                self.CATEGORY_ORDER
            )
        }

        cleaned_parts.sort(
            key=lambda item: (
                order_map.get(
                    item,
                    len(self.CATEGORY_ORDER),
                ),
                item,
            )
        )

        return " + ".join(cleaned_parts)

    def _get_shop_category_prices(
        self,
        shop: Any,
        category: str,
    ) -> List[int]:
        """指定カテゴリに該当する有効価格一覧を取得する。"""

        prices: List[int] = []

        target_category = self._normalize_category(
            category
        )

        coupons = getattr(
            shop,
            "coupons",
            [],
        )

        for coupon in coupons:
            coupon_category = self._normalize_category(
                getattr(
                    coupon,
                    "category",
                    "",
                )
            )

            if coupon_category != target_category:
                continue

            price = self._get_valid_price(
                coupon
            )

            if price is not None:
                prices.append(price)

        return prices

    def _round_price(
        self,
        price: float,
    ) -> int:
        """価格を100円単位に丸める。"""

        return int(
            round(price / 100.0) * 100
        )

    def _get_all_categories(
        self,
        shops: List[Any],
    ) -> List[str]:
        """全店舗から正規化後のカテゴリ一覧を取得する。"""

        categories = set()

        for shop in shops:
            coupons = getattr(
                shop,
                "coupons",
                [],
            )

            for coupon in coupons:
                category = self._normalize_category(
                    getattr(
                        coupon,
                        "category",
                        "",
                    )
                )

                if category:
                    categories.add(category)

        order_map = {
            name: index
            for index, name in enumerate(
                self.CATEGORY_ORDER
            )
        }

        return sorted(
            categories,
            key=lambda item: (
                tuple(
                    order_map.get(
                        part.strip(),
                        len(self.CATEGORY_ORDER),
                    )
                    for part in item.split("+")
                ),
                item,
            ),
        )

    # =========================================================
    # 参考度判定
    # =========================================================

    def _get_reference_level(
        self,
        comparison_shop_count: int,
        comparison_coupon_count: int,
    ) -> Dict[str, str]:
        """
        比較店舗数と比較クーポン数から参考度を判定する。

        基本ルール:
        - 0店舗 → 比較不可
        - 1店舗 → 低
        - 2店舗以上＋3クーポン以上 → 中
        - 3店舗以上＋6クーポン以上 → 高

        クーポン数が少ない場合は店舗数が多くても
        参考度を上げすぎない。
        """

        if comparison_shop_count <= 0:
            return {
                "reference_level": "比較不可",
                "reference_reason": (
                    "比較対象店舗に有効な価格データがありません"
                ),
            }

        if comparison_coupon_count <= 2:
            return {
                "reference_level": "低",
                "reference_reason": (
                    f"比較店舗は{comparison_shop_count}店舗ありますが、"
                    f"有効な比較クーポンが"
                    f"{comparison_coupon_count}件と少ないため"
                ),
            }

        if (
            comparison_shop_count >= 3
            and comparison_coupon_count >= 6
        ):
            return {
                "reference_level": "高",
                "reference_reason": (
                    f"比較店舗{comparison_shop_count}店舗、"
                    f"比較クーポン{comparison_coupon_count}件を"
                    "基準に算出"
                ),
            }

        if (
            comparison_shop_count >= 2
            and comparison_coupon_count >= 3
        ):
            return {
                "reference_level": "中",
                "reference_reason": (
                    f"比較店舗{comparison_shop_count}店舗、"
                    f"比較クーポン{comparison_coupon_count}件を"
                    "基準に算出"
                ),
            }

        return {
            "reference_level": "低",
            "reference_reason": (
                f"比較店舗{comparison_shop_count}店舗を"
                "基準に算出しているため"
            ),
        }

    # =========================================================
    # 市場参考価格
    # =========================================================

    def _recommend_price(
        self,
        shop_median: Optional[float],
        comparison_median: Optional[float],
        comparison_shop_count: int,
        comparison_coupon_count: int = 0,
    ) -> Dict[str, Any]:
        """
        比較店舗中央値を市場参考価格として返す。

        「適正価格」と断定せず、
        市場データ上の参考値として扱う。
        """

        reference_info = self._get_reference_level(
            comparison_shop_count,
            comparison_coupon_count,
        )

        if (
            comparison_median is None
            or comparison_shop_count == 0
        ):
            return {
                # v1.7互換
                "recommended_price": None,
                "recommended_min": None,
                "recommended_max": None,
                "recommendation_note": (
                    "比較対象店舗がないため市場参考価格を算出できません"
                ),

                # v1.8
                "market_reference_price": None,
                "reference_price_min": None,
                "reference_price_max": None,
                **reference_info,
            }

        reference_price = self._round_price(
            comparison_median
        )

        reference_min = self._round_price(
            comparison_median * 0.95
        )

        reference_max = self._round_price(
            comparison_median * 1.05
        )

        recommendation_note = (
            "比較店舗別中央値を同じ重みで算出した市場参考価格"
        )

        return {
            # v1.7互換
            "recommended_price": reference_price,
            "recommended_min": reference_min,
            "recommended_max": reference_max,
            "recommendation_note": recommendation_note,

            # v1.8
            "market_reference_price": reference_price,
            "reference_price_min": reference_min,
            "reference_price_max": reference_max,
            **reference_info,
        }

    # =========================================================
    # 全体価格分析
    # =========================================================

    def analyze(
        self,
        shop: Any,
        comparison_shops: List[Any],
    ) -> Dict[str, Any]:
        """
        店舗全体のクーポン価格ポジションを分析する。
        """

        shop_prices: List[int] = []

        for coupon in getattr(
            shop,
            "coupons",
            [],
        ):
            price = self._get_valid_price(
                coupon
            )

            if price is not None:
                shop_prices.append(price)

        comparison_shop_medians: List[float] = []
        comparison_coupon_count = 0

        for other_shop in comparison_shops:

            if other_shop is shop:
                continue

            prices: List[int] = []

            for coupon in getattr(
                other_shop,
                "coupons",
                [],
            ):
                price = self._get_valid_price(
                    coupon
                )

                if price is not None:
                    prices.append(price)

            if prices:
                comparison_coupon_count += len(
                    prices
                )

                comparison_shop_medians.append(
                    float(median(prices))
                )

        comparison_shop_count = len(
            comparison_shop_medians
        )

        result: Dict[str, Any] = {
            "shop_name": getattr(
                shop,
                "name",
                "",
            ),
            "shop_price_count": len(
                shop_prices
            ),
            "shop_average": None,
            "shop_median": None,

            "comparison_shop_count": (
                comparison_shop_count
            ),
            "comparison_coupon_count": (
                comparison_coupon_count
            ),
            "comparison_average": None,
            "comparison_median": None,
            "comparison_shop_medians": (
                comparison_shop_medians
            ),

            "difference": None,
            "ratio": None,
            "position": "比較不可",

            "comparison_method": (
                "店舗別中央値を同じ重みで比較"
            ),
        }

        if shop_prices:
            result["shop_average"] = round(
                sum(shop_prices)
                / len(shop_prices)
            )

            result["shop_median"] = float(
                median(shop_prices)
            )

        if comparison_shop_medians:
            result["comparison_average"] = round(
                sum(comparison_shop_medians)
                / len(
                    comparison_shop_medians
                )
            )

            result["comparison_median"] = float(
                median(
                    comparison_shop_medians
                )
            )

        if (
            result["shop_median"] is not None
            and result["comparison_median"] is not None
        ):
            difference = (
                result["shop_median"]
                - result["comparison_median"]
            )

            result["difference"] = (
                self._round_price(
                    difference
                )
            )

            if result["comparison_median"] != 0:
                result["ratio"] = round(
                    result["shop_median"]
                    / result["comparison_median"]
                    * 100,
                    1,
                )

            ratio = result["ratio"]

            if ratio is not None:
                if ratio < 95:
                    result["position"] = (
                        "中央値より安い"
                    )

                elif ratio > 105:
                    result["position"] = (
                        "中央値より高い"
                    )

                else:
                    result["position"] = (
                        "中央値付近"
                    )

        recommendation = self._recommend_price(
            result["shop_median"],
            result["comparison_median"],
            result["comparison_shop_count"],
            result["comparison_coupon_count"],
        )

        result.update(
            recommendation
        )

        return result

    def analyze_summary(
        self,
        shop: Any,
        comparison_shops: List[Any],
    ) -> Dict[str, Any]:
        """店舗全体の価格分析結果を返す。"""

        return self.analyze(
            shop,
            comparison_shops,
        )

    # =========================================================
    # カテゴリ別価格分析
    # =========================================================

    def analyze_category_summary(
        self,
        shop: Any,
        area_analysis: Optional[Dict[str, Any]],
        shops: Optional[List[Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        カテゴリ別の価格ポジションを分析する。

        正規化カテゴリごとに、
        各競合店舗の中央値を算出し、
        店舗を同じ重みで比較する。
        """

        if shops is None:
            shops = []

        categories = self._get_all_categories(
            shops
        )

        result: Dict[str, Dict[str, Any]] = {}

        for category in categories:

            shop_prices = (
                self._get_shop_category_prices(
                    shop,
                    category,
                )
            )

            if not shop_prices:
                continue

            shop_median = float(
                median(shop_prices)
            )

            comparison_shop_medians: List[
                float
            ] = []

            comparison_coupon_count = 0

            for other_shop in shops:

                if other_shop is shop:
                    continue

                other_prices = (
                    self._get_shop_category_prices(
                        other_shop,
                        category,
                    )
                )

                if not other_prices:
                    continue

                other_median = float(
                    median(other_prices)
                )

                comparison_shop_medians.append(
                    other_median
                )

                comparison_coupon_count += (
                    len(other_prices)
                )

            comparison_shop_count = len(
                comparison_shop_medians
            )

            comparison_average = None
            comparison_median = None
            comparison_min = None
            comparison_max = None

            if comparison_shop_medians:

                comparison_average = round(
                    sum(
                        comparison_shop_medians
                    )
                    / len(
                        comparison_shop_medians
                    )
                )

                comparison_median = float(
                    median(
                        comparison_shop_medians
                    )
                )

                comparison_min = min(
                    comparison_shop_medians
                )

                comparison_max = max(
                    comparison_shop_medians
                )

            difference = None
            ratio = None
            position = "比較不可"

            if comparison_median is not None:

                difference = (
                    self._round_price(
                        shop_median
                        - comparison_median
                    )
                )

                if comparison_median != 0:
                    ratio = round(
                        shop_median
                        / comparison_median
                        * 100,
                        1,
                    )

                if ratio is not None:

                    if ratio < 95:
                        position = (
                            "中央値より安い"
                        )

                    elif ratio > 105:
                        position = (
                            "中央値より高い"
                        )

                    else:
                        position = (
                            "中央値付近"
                        )

            recommendation = (
                self._recommend_price(
                    shop_median,
                    comparison_median,
                    comparison_shop_count,
                    comparison_coupon_count,
                )
            )

            result[category] = {
                "category": category,

                # 自店舗
                "shop_coupon_count": len(
                    shop_prices
                ),
                "shop_average": round(
                    sum(shop_prices)
                    / len(shop_prices)
                ),
                "shop_median": shop_median,

                # 比較店舗
                "comparison_shop_count": (
                    comparison_shop_count
                ),
                "comparison_coupon_count": (
                    comparison_coupon_count
                ),
                "comparison_average": (
                    comparison_average
                ),
                "comparison_median": (
                    comparison_median
                ),

                # 店舗別中央値
                "comparison_shop_medians": (
                    comparison_shop_medians
                ),
                "comparison_shop_median_min": (
                    comparison_min
                ),
                "comparison_shop_median_max": (
                    comparison_max
                ),

                # 比較結果
                "difference": difference,
                "ratio": ratio,
                "position": position,

                "comparison_method": (
                    "正規化カテゴリ・店舗別中央値を"
                    "同じ重みで比較"
                ),

                # 市場参考価格＋参考度
                **recommendation,
            }

        return result