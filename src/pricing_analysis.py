from __future__ import annotations

from statistics import median, quantiles
from typing import Any, Dict, List, Optional


class PricingAnalyzer:
    """
    HotPepper Beauty クーポン価格の市場比較分析を行うクラス。

    v1.8.2
    - 店舗別中央値を同じ重みで比較
    - カテゴリ名を正規化して比較
    - 「その他」を含むカテゴリを正規化
    - 店舗ごとのカテゴリ中央値を算出して比較
    - 市場参考価格を算出
    - 参考価格帯を算出
    - 参考度を比較店舗数＋比較クーポン数から判定
    - 価格データ品質チェックを追加
    - 営業確認候補としてクーポン名・価格・カテゴリ・判定理由を保持
    - IQRによる外れ値候補を検出
    - 外れ値候補は元データ・価格分析から除外しない
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

    # =========================================================
    # 基本ユーティリティ
    # =========================================================

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
    # 価格データ品質チェック v1.8.1
    # =========================================================

    LOW_PRICE_ATTENTION_THRESHOLD = 3000
    HIGH_PRICE_ATTENTION_THRESHOLD = 30000
    CATEGORY_OUTLIER_MIN_COUNT = 4

    def _build_price_item(self, coupon: Any) -> Optional[Dict[str, Any]]:
        """クーポンを価格品質分析用のデータへ変換する。"""
        price = self._get_valid_price(coupon)
        if price is None:
            return None
        coupon_name = self._clean_value(getattr(coupon, "title", ""))
        if not coupon_name:
            coupon_name = self._clean_value(getattr(coupon, "name", ""))
        raw_category = self._clean_value(getattr(coupon, "category", ""))
        return {
            "price": price,
            "coupon_name": coupon_name,
            "category": raw_category,
            "normalized_category": self._normalize_category(raw_category),
        }

    def _calculate_iqr_bounds(self, prices: List[int]) -> Optional[Dict[str, float]]:
        """価格一覧からIQRと判定境界を算出する。"""
        if len(prices) < self.CATEGORY_OUTLIER_MIN_COUNT:
            return None
        try:
            quartile_values = quantiles(prices, n=4, method="inclusive")
            q1 = float(quartile_values[0])
            q3 = float(quartile_values[2])
        except Exception:
            return None
        iqr = q3 - q1
        return {
            "q1": q1, "q3": q3, "iqr": iqr,
            "lower_bound": q1 - 1.5 * iqr,
            "upper_bound": q3 + 1.5 * iqr,
        }

    def _get_price_quality(self, coupons: List[Any]) -> Dict[str, Any]:
        """
        価格データの品質を3層で確認する。

        1. 店舗全体の統計的外れ値: IQR×1.5
        2. カテゴリ別の統計的外れ値: IQR×1.5（4件以上）
        3. 極端な価格の要確認: 3,000円以下 / 30,000円以上

        フラグ付き価格も元データ・平均・中央値・市場参考価格から除外しない。
        """
        valid_items: List[Dict[str, Any]] = []
        for coupon in coupons:
            item = self._build_price_item(coupon)
            if item is not None:
                valid_items.append(item)

        prices = [item["price"] for item in valid_items]
        result: Dict[str, Any] = {
            "quality_status": "判定対象外",
            "quality_method": (
                "店舗全体IQR×1.5・カテゴリ別IQR×1.5・"
                "低価格3,000円以下・高価格30,000円以上"
            ),
            "valid_price_count": len(valid_items),
            "outlier_count": 0, "low_outlier_count": 0, "high_outlier_count": 0,
            "outliers": [],
            "category_outlier_count": 0,
            "category_low_outlier_count": 0,
            "category_high_outlier_count": 0,
            "category_outliers": [],
            "low_price_attention_count": 0,
            "high_price_attention_count": 0,
            "low_price_attention": [],
            "high_price_attention": [],
            "q1": None, "q3": None, "iqr": None,
            "lower_bound": None, "upper_bound": None,
            "category_quality": {},
        }

        # 1. 店舗全体IQR
        bounds = self._calculate_iqr_bounds(prices)
        if bounds is not None:
            result.update(bounds)
            for item in valid_items:
                price = item["price"]
                if price < bounds["lower_bound"]:
                    result["outliers"].append({**item, "direction": "低価格候補", "reason": "店舗全体のIQR下限を下回っています"})
                elif price > bounds["upper_bound"]:
                    result["outliers"].append({**item, "direction": "高価格候補", "reason": "店舗全体のIQR上限を上回っています"})

        result["outlier_count"] = len(result["outliers"])
        result["low_outlier_count"] = sum(1 for x in result["outliers"] if x["direction"] == "低価格候補")
        result["high_outlier_count"] = sum(1 for x in result["outliers"] if x["direction"] == "高価格候補")

        # 2. カテゴリ別IQR
        category_items: Dict[str, List[Dict[str, Any]]] = {}
        for item in valid_items:
            category = item["normalized_category"]
            if category:
                category_items.setdefault(category, []).append(item)

        for category, items in category_items.items():
            category_prices = [item["price"] for item in items]
            category_bounds = self._calculate_iqr_bounds(category_prices)
            info: Dict[str, Any] = {"valid_price_count": len(items), "q1": None, "q3": None, "iqr": None, "lower_bound": None, "upper_bound": None, "outlier_count": 0}
            if category_bounds is None:
                info["reason"] = "有効な価格データが4件未満のためカテゴリ別IQR判定を行いません"
                result["category_quality"][category] = info
                continue
            info.update(category_bounds)
            for item in items:
                price = item["price"]
                if price < category_bounds["lower_bound"]:
                    result["category_outliers"].append({**item, "direction": "低価格候補", "reason": "カテゴリのIQR下限を下回っています"})
                elif price > category_bounds["upper_bound"]:
                    result["category_outliers"].append({**item, "direction": "高価格候補", "reason": "カテゴリのIQR上限を上回っています"})
            info["outlier_count"] = sum(1 for x in result["category_outliers"] if x["normalized_category"] == category)
            result["category_quality"][category] = info

        result["category_outlier_count"] = len(result["category_outliers"])
        result["category_low_outlier_count"] = sum(1 for x in result["category_outliers"] if x["direction"] == "低価格候補")
        result["category_high_outlier_count"] = sum(1 for x in result["category_outliers"] if x["direction"] == "高価格候補")

        # 3. 極端な価格の要確認
        for item in valid_items:
            price = item["price"]
            if price <= self.LOW_PRICE_ATTENTION_THRESHOLD:
                result["low_price_attention"].append({
                    **item,
                    "reason": f"{self.LOW_PRICE_ATTENTION_THRESHOLD:,}円以下の極端な低価格のため要確認",
                })
            if price >= self.HIGH_PRICE_ATTENTION_THRESHOLD:
                result["high_price_attention"].append({
                    **item,
                    "reason": f"{self.HIGH_PRICE_ATTENTION_THRESHOLD:,}円以上の高価格のため要確認",
                })

        result["low_price_attention_count"] = len(result["low_price_attention"])
        result["high_price_attention_count"] = len(result["high_price_attention"])

        if not valid_items:
            result["quality_status"] = "判定対象外"
            result["quality_reason"] = "有効な価格データがありません"
        elif result["outlier_count"] or result["category_outlier_count"]:
            result["quality_status"] = "外れ値候補あり"
            result["quality_reason"] = "店舗全体またはカテゴリ単位のIQR基準から外れる価格データが検出されました"
        elif result["low_price_attention_count"] or result["high_price_attention_count"]:
            result["quality_status"] = "要確認価格あり"
            result["quality_reason"] = "極端な価格が含まれているため内容の確認を推奨します"
        else:
            result["quality_status"] = "問題候補なし"
            result["quality_reason"] = "統計的外れ値候補および要確認価格は検出されませんでした"

        return result

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

        target_category = (
            self._normalize_category(
                category
            )
        )

        coupons = getattr(
            shop,
            "coupons",
            [],
        )

        for coupon in coupons:

            coupon_category = (
                self._normalize_category(
                    getattr(
                        coupon,
                        "category",
                        "",
                    )
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

                category = (
                    self._normalize_category(
                        getattr(
                            coupon,
                            "category",
                            "",
                        )
                    )
                )

                if category:
                    categories.add(
                        category
                    )

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
                        len(
                            self.CATEGORY_ORDER
                        ),
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
        """

        reference_info = (
            self._get_reference_level(
                comparison_shop_count,
                comparison_coupon_count,
            )
        )

        if (
            comparison_median is None
            or comparison_shop_count == 0
        ):
            return {
                "recommended_price": None,
                "recommended_min": None,
                "recommended_max": None,
                "recommendation_note": (
                    "比較対象店舗がないため市場参考価格を算出できません"
                ),
                "market_reference_price": None,
                "reference_price_min": None,
                "reference_price_max": None,
                **reference_info,
            }

        reference_price = (
            self._round_price(
                comparison_median
            )
        )

        reference_min = (
            self._round_price(
                comparison_median * 0.95
            )
        )

        reference_max = (
            self._round_price(
                comparison_median * 1.05
            )
        )

        recommendation_note = (
            "比較店舗別中央値を同じ重みで算出した市場参考価格"
        )

        return {
            "recommended_price": reference_price,
            "recommended_min": reference_min,
            "recommended_max": reference_max,
            "recommendation_note": (
                recommendation_note
            ),
            "market_reference_price": (
                reference_price
            ),
            "reference_price_min": (
                reference_min
            ),
            "reference_price_max": (
                reference_max
            ),
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

        coupons = getattr(
            shop,
            "coupons",
            [],
        )

        shop_prices: List[int] = []

        for coupon in coupons:

            price = self._get_valid_price(
                coupon
            )

            if price is not None:
                shop_prices.append(
                    price
                )

        # v1.8.1 価格データ品質チェック
        price_quality = (
            self._get_price_quality(
                coupons
            )
        )

        comparison_shop_medians: List[
            float
        ] = []

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
                    prices.append(
                        price
                    )

            if prices:

                comparison_coupon_count += (
                    len(prices)
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

            # v1.8.1
            "price_quality": price_quality,
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

            result["comparison_average"] = (
                round(
                    sum(
                        comparison_shop_medians
                    )
                    / len(
                        comparison_shop_medians
                    )
                )
            )

            result["comparison_median"] = (
                float(
                    median(
                        comparison_shop_medians
                    )
                )
            )

        if (
            result["shop_median"] is not None
            and result["comparison_median"]
            is not None
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

            if (
                result["comparison_median"]
                != 0
            ):
                result["ratio"] = round(
                    result["shop_median"]
                    / result[
                        "comparison_median"
                    ]
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

        recommendation = (
            self._recommend_price(
                result["shop_median"],
                result["comparison_median"],
                result[
                    "comparison_shop_count"
                ],
                result[
                    "comparison_coupon_count"
                ],
            )
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

        result: Dict[
            str,
            Dict[str, Any]
        ] = {}

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

                "shop_coupon_count": len(
                    shop_prices
                ),
                "shop_average": round(
                    sum(shop_prices)
                    / len(shop_prices)
                ),
                "shop_median": shop_median,

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

                "comparison_shop_medians": (
                    comparison_shop_medians
                ),
                "comparison_shop_median_min": (
                    comparison_min
                ),
                "comparison_shop_median_max": (
                    comparison_max
                ),

                "difference": difference,
                "ratio": ratio,
                "position": position,

                "comparison_method": (
                    "正規化カテゴリ・店舗別中央値を"
                    "同じ重みで比較"
                ),

                **recommendation,
            }

        return result