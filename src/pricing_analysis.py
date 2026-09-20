from statistics import median


class PricingAnalyzer:
    """
    クーポン価格の市場内ポジション分析エンジン

    自店舗のクーポン価格と、エリア全体の価格統計を比較する。

    分析内容:
    - 自店舗価格
    - エリア平均
    - エリア中央値
    - 最低価格
    - 最高価格
    - 中央値との差額
    - 中央値に対する価格比率
    - 市場内ポジション
    """

    def analyze(self, shop, area_analysis):
        """
        店舗単位の価格ポジションを分析する。

        Parameters
        ----------
        shop : Shop
            分析対象店舗

        area_analysis : dict
            AreaAnalyzerの分析結果

        Returns
        -------
        dict
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

    def _judge_position(self, price, median_price):
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

    def _get_valid_price(self, coupon):

        value = getattr(coupon, "price", None)

        if value is None:
            return None

        if isinstance(value, str):

            value = value.strip()

            if not value:
                return None

            value = (
                value.replace(",", "")
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

    def _clean_value(self, value):

        if value is None:
            return ""

        return str(value).strip()