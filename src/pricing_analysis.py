from statistics import median


class PricingAnalyzer:
    """
    クーポン価格の市場内ポジション分析エンジン

    分析内容:
    - 店舗全体の価格ポジション
    - カテゴリ別の価格ポジション
    - 同一カテゴリを扱う他店舗との比較
    """

    # =========================================================
    # 店舗全体価格分析
    # =========================================================

    def analyze(self, shop, area_analysis):
        """
        店舗単位の価格ポジションを分析する。

        全クーポンを対象に、エリア全体の中央値と比較する。
        """

        coupons = getattr(shop, "coupons", []) or []

        area_price = (
            area_analysis.get("price", {})
            if isinstance(area_analysis, dict)
            else {}
        )

        area_average = area_price.get("average")
        area_median = area_price.get("median")
        area_minimum = area_price.get("minimum")
        area_maximum = area_price.get("maximum")

        results = []

        for coupon in coupons:

            price = self._get_valid_price(coupon)

            if price is None:
                continue

            result = {
                "order": getattr(coupon, "order", None),
                "target": self._clean_value(
                    getattr(coupon, "target", None)
                ) or "未分類",
                "category": self._clean_value(
                    getattr(coupon, "category", None)
                ) or "未分類",
                "title": self._clean_value(
                    getattr(coupon, "title", None)
                ),
                "price": price,
                "area_average": area_average,
                "area_median": area_median,
                "area_minimum": area_minimum,
                "area_maximum": area_maximum,
                "difference_from_median": None,
                "price_ratio_to_median": None,
                "position": None,
            }

            if area_median is not None and area_median > 0:

                difference = price - area_median

                ratio = (price / area_median) * 100

                result["difference_from_median"] = difference
                result["price_ratio_to_median"] = round(ratio, 1)
                result["position"] = self._judge_position(
                    price,
                    area_median
                )

            results.append(result)

        return {
            "shop": {
                "name": getattr(shop, "name", ""),
                "coupon_count": len(results),
            },
            "coupons": results,
        }

    # =========================================================
    # 店舗全体サマリー
    # =========================================================

    def analyze_summary(self, shop, area_analysis):
        """
        店舗全体の価格ポジションをまとめる。

        価格の中央値を店舗代表価格として使用する。
        """

        coupons = getattr(shop, "coupons", []) or []

        prices = []

        for coupon in coupons:

            price = self._get_valid_price(coupon)

            if price is not None:
                prices.append(price)

        if not prices:
            return {
                "shop": getattr(shop, "name", ""),
                "coupon_count": 0,
                "shop_average": None,
                "shop_median": None,
                "area_average": None,
                "area_median": None,
                "difference_from_area_median": None,
                "price_ratio_to_area_median": None,
                "position": "判定不可",
            }

        shop_average = round(sum(prices) / len(prices))
        shop_median = median(prices)

        area_price = (
            area_analysis.get("price", {})
            if isinstance(area_analysis, dict)
            else {}
        )

        area_average = area_price.get("average")
        area_median = area_price.get("median")

        difference = None
        ratio = None
        position = "判定不可"

        if area_median is not None and area_median > 0:

            difference = round(shop_median - area_median)

            ratio = round(
                (shop_median / area_median) * 100,
                1
            )

            position = self._judge_position(
                shop_median,
                area_median
            )

        return {
            "shop": getattr(shop, "name", ""),
            "coupon_count": len(prices),
            "shop_average": shop_average,
            "shop_median": shop_median,
            "area_average": area_average,
            "area_median": area_median,
            "difference_from_area_median": difference,
            "price_ratio_to_area_median": ratio,
            "position": position,
        }

    # =========================================================
    # カテゴリ別価格ポジション分析
    # =========================================================

    def analyze_category_summary(
        self,
        shop,
        area_analysis,
        shops=None
    ):
        """
        カテゴリ別の価格ポジションを分析する。

        自店舗のカテゴリ価格と、
        同じカテゴリを掲載している他店舗の価格を比較する。

        Parameters
        ----------
        shop : Shop
            分析対象店舗

        area_analysis : dict
            AreaCouponAnalyzerの分析結果

        shops : list[Shop]
            比較対象となる全店舗

        Returns
        -------
        dict
        """

        coupons = getattr(shop, "coupons", []) or []

        # -----------------------------------------------------
        # 自店舗のカテゴリ別価格を集計
        # -----------------------------------------------------

        shop_category_prices = {}

        for coupon in coupons:

            price = self._get_valid_price(coupon)

            if price is None:
                continue

            category = self._get_category(coupon)

            if category not in shop_category_prices:
                shop_category_prices[category] = []

            shop_category_prices[category].append(price)

        # -----------------------------------------------------
        # 他店舗のカテゴリ別価格を集計
        # -----------------------------------------------------

        comparison_category_prices = {}

        if shops:

            for other_shop in shops:

                # 自店舗自身は比較対象から除外
                if other_shop is shop:
                    continue

                other_coupons = (
                    getattr(other_shop, "coupons", []) or []
                )

                # 同一店舗内ではカテゴリごとにまとめる
                shop_prices = {}

                for coupon in other_coupons:

                    price = self._get_valid_price(coupon)

                    if price is None:
                        continue

                    category = self._get_category(coupon)

                    if category not in shop_prices:
                        shop_prices[category] = []

                    shop_prices[category].append(price)

                for category, prices in shop_prices.items():

                    if category not in comparison_category_prices:
                        comparison_category_prices[category] = {
                            "prices": [],
                            "shop_count": 0,
                        }

                    comparison_category_prices[
                        category
                    ]["prices"].extend(prices)

                    comparison_category_prices[
                        category
                    ]["shop_count"] += 1

        # -----------------------------------------------------
        # エリア分析データ
        # -----------------------------------------------------

        area_category = {}

        if isinstance(area_analysis, dict):

            area_category = area_analysis.get(
                "category",
                {}
            )

        area_price_stats = area_category.get(
            "price_stats",
            {}
        )

        # -----------------------------------------------------
        # カテゴリ別結果作成
        # -----------------------------------------------------

        results = []

        for category, prices in shop_category_prices.items():

            shop_average = round(sum(prices) / len(prices))
            shop_median = median(prices)

            comparison_data = comparison_category_prices.get(
                category,
                {}
            )

            comparison_prices = comparison_data.get(
                "prices",
                []
            )

            comparison_shop_count = comparison_data.get(
                "shop_count",
                0
            )

            # 比較対象店舗の中央値
            if comparison_prices:
                comparison_average = round(
                    sum(comparison_prices)
                    / len(comparison_prices)
                )

                comparison_median = median(
                    comparison_prices
                )

                comparison_minimum = min(
                    comparison_prices
                )

                comparison_maximum = max(
                    comparison_prices
                )

            else:
                comparison_average = None
                comparison_median = None
                comparison_minimum = None
                comparison_maximum = None

            # -------------------------------------------------
            # エリア全体の統計
            #
            # これは参考情報として残す。
            # 比較対象店舗数0の場合でも確認できる。
            # -------------------------------------------------

            area_stats = area_price_stats.get(
                category,
                {}
            )

            area_average = area_stats.get(
                "average"
            )

            area_median = area_stats.get(
                "median"
            )

            # -------------------------------------------------
            # 比較判定
            # -------------------------------------------------

            difference = None
            ratio = None
            position = "比較対象店舗なし"

            if (
                comparison_median is not None
                and comparison_median > 0
            ):

                difference = round(
                    shop_median - comparison_median
                )

                ratio = round(
                    (shop_median / comparison_median) * 100,
                    1
                )

                position = self._judge_position(
                    shop_median,
                    comparison_median
                )

            results.append({
                "category": category,
                "coupon_count": len(prices),

                "shop_average": shop_average,
                "shop_median": shop_median,

                "comparison_shop_count":
                    comparison_shop_count,

                "comparison_coupon_count":
                    len(comparison_prices),

                "comparison_average":
                    comparison_average,

                "comparison_median":
                    comparison_median,

                "comparison_minimum":
                    comparison_minimum,

                "comparison_maximum":
                    comparison_maximum,

                "area_average":
                    area_average,

                "area_median":
                    area_median,

                "difference_from_comparison_median":
                    difference,

                "price_ratio_to_comparison_median":
                    ratio,

                "position":
                    position,
            })

        # カテゴリ名順に並べる
        results.sort(
            key=lambda item: item["category"]
        )

        return {
            "shop": getattr(shop, "name", ""),
            "category_count": len(results),
            "categories": results,
        }

    # =========================================================
    # 判定
    # =========================================================

    def _judge_position(
        self,
        price,
        median_price
    ):
        """
        中央値を基準に価格ポジションを判定する。

        ±5%以内は「中央値付近」とする。
        """

        if median_price is None or median_price <= 0:
            return "判定不可"

        ratio = price / median_price

        if ratio < 0.95:
            return "中央値より安い"

        if ratio > 1.05:
            return "中央値より高い"

        return "中央値付近"

    # =========================================================
    # 価格取得
    # =========================================================

    def _get_valid_price(self, coupon):

        value = getattr(coupon, "price", None)

        if value is None:
            return None

        if isinstance(value, str):

            value = value.strip()

            if not value:
                return None

            value = (
                value
                .replace(",", "")
                .replace("円", "")
                .replace("￥", "")
                .replace("¥", "")
            )

            if not value:
                return None

        try:
            price = int(float(value))

        except (TypeError, ValueError):

            return None

        if price <= 0:
            return None

        return price

    # =========================================================
    # カテゴリ取得
    # =========================================================

    def _get_category(self, coupon):

        value = getattr(
            coupon,
            "category",
            None
        )

        if value is None:
            return "未分類"

        value = str(value).strip()

        if not value:
            return "未分類"

        return value

    # =========================================================
    # 文字列整形
    # =========================================================

    def _clean_value(self, value):

        if value is None:
            return ""

        return str(value).strip()