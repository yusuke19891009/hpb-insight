from __future__ import annotations

from statistics import median
from typing import Any, Dict, List, Optional


class PricingAnalyzer:
    """
    クーポン価格の市場比較・価格分析を行うクラス。

    v1.8
    - 比較対象店舗ごとにカテゴリ中央値を算出
    - 店舗別中央値を同じ重みで比較
    - カテゴリ名を正規化して比較
    - 「その他」を含むカテゴリの比較精度を向上
    - カテゴリ順が異なる場合も同一カテゴリとして扱う
    """

    # カテゴリの基本表示順
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
        """比較用文字列を正規化する。"""

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

        例：

        カラー + カット + トリートメント
        ↓
        カット + カラー + トリートメント

        カット + カラー + トリートメント + その他
        ↓
        カット + カラー + トリートメント

        カット + その他
        ↓
        カット

        その他
        ↓
        その他
        """

        value = self._clean_value(category)

        if not value:
            return ""

        # 「+」で構成要素を分割
        parts = value.split("+")

        cleaned_parts: List[str] = []

        for part in parts:
            part = part.strip()

            if not part:
                continue

            # 同じ要素が複数ある場合は1つにする
            if part not in cleaned_parts:
                cleaned_parts.append(part)

        if not cleaned_parts:
            return ""

        # 「その他」は他のカテゴリがある場合は
        # 比較上のノイズになりやすいため除外
        if len(cleaned_parts) > 1:
            cleaned_parts = [
                part
                for part in cleaned_parts
                if part != "その他"
            ]

        # その他しか残らなかった場合
        if not cleaned_parts:
            return "その他"

        # 基本カテゴリ順に並べる
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
        """
        1店舗について、
        正規化後の指定カテゴリに該当する
        有効価格一覧を取得する。
        """

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
        """
        全店舗の実データから、
        正規化後のカテゴリ一覧を作成する。
        """

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

        # カテゴリの基本順で並べる
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
    # 価格参考値
    # =========================================================

    def _recommend_price(
        self,
        shop_median: Optional[float],
        comparison_median: Optional[float],
        comparison_shop_count: int,
    ) -> Dict[str, Any]:
        """
        比較店舗中央値を基準に参考価格を算出する。
        """

        if (
            comparison_median is None
            or comparison_shop_count == 0
        ):
            return {
                "recommended_price": None,
                "recommended_min": None,
                "recommended_max": None,
                "recommendation_note": (
                    "比較対象店舗がないため算出不可"
                ),
            }

        reference_price = self._round_price(
            comparison_median
        )

        recommended_min = self._round_price(
            comparison_median * 0.95
        )

        recommended_max = self._round_price(
            comparison_median * 1.05
        )

        if comparison_shop_count == 1:
            note = (
                "1店舗のみを比較した参考価格"
            )

        elif comparison_shop_count == 2:
            note = (
                "2店舗を比較した参考価格"
            )

        else:
            note = (
                "比較店舗の中央値を基準にした参考価格"
            )

        return {
            "recommended_price": reference_price,
            "recommended_min": recommended_min,
            "recommended_max": recommended_max,
            "recommendation_note": note,
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
        店舗全体の価格ポジションを分析する。

        比較対象は店舗別中央値を
        同じ重みで比較する。
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
            "comparison_shop_count": len(
                comparison_shop_medians
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

        recommendation = (
            self._recommend_price(
                result["shop_median"],
                result["comparison_median"],
                result["comparison_shop_count"],
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

        v1.8ではカテゴリ名を正規化してから
        比較する。
        """

        if shops is None:
            shops = []

        # -----------------------------------------------------
        # 正規化カテゴリ一覧
        # -----------------------------------------------------
        categories = self._get_all_categories(
            shops
        )

        result: Dict[str, Dict[str, Any]] = {}

        # -----------------------------------------------------
        # カテゴリごとの分析
        # -----------------------------------------------------
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

            # -------------------------------------------------
            # 比較店舗
            # -------------------------------------------------
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

                # 1店舗につき1つの中央値
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

            # -------------------------------------------------
            # 比較店舗統計
            # -------------------------------------------------
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

            # -------------------------------------------------
            # 比較結果
            # -------------------------------------------------
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

            # -------------------------------------------------
            # 参考価格
            # -------------------------------------------------
            recommendation = (
                self._recommend_price(
                    shop_median,
                    comparison_median,
                    comparison_shop_count,
                )
            )

            # -------------------------------------------------
            # 結果
            # -------------------------------------------------
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

                # 比較方法
                "comparison_method": (
                    "正規化カテゴリ・"
                    "店舗別中央値を同じ重みで比較"
                ),

                # 参考価格
                **recommendation,
            }

        return result