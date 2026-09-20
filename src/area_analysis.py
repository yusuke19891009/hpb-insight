from statistics import mean, median


class AreaCouponAnalyzer:
    """
    Hot Pepper Beauty エリア分析エンジン

    複数店舗のクーポンデータを横断して分析する。

    分析結果:

    {
        "shops": {
            "shop_count": 店舗数,
            "coupon_count": 総クーポン数
        },

        "category": {
            "count": カテゴリ別クーポン件数,
            "shop_count": カテゴリを掲載している店舗数,
            "price_stats": カテゴリ別価格統計
        },

        "target": {
            "count": 対象別クーポン件数,
            "shop_count": 対象を掲載している店舗数,
            "price_stats": 対象別価格統計
        },

        "price": {
            "count": 有効価格件数,
            "average": 平均価格,
            "median": 中央値,
            "minimum": 最低価格,
            "maximum": 最高価格
        }
    }
    """

    def analyze(self, shops):
        shops = shops or []

        coupons = []

        for shop in shops:
            shop_coupons = getattr(shop, "coupons", []) or []
            coupons.extend(shop_coupons)

        return {
            "shops": {
                "shop_count": len(shops),
                "coupon_count": len(coupons),
            },

            "category": self._analyze_group(
                shops,
                coupons,
                field="category",
            ),

            "target": self._analyze_group(
                shops,
                coupons,
                field="target",
            ),

            "price": self._analyze_price(coupons),
        }

    # =========================================================
    # カテゴリ / 対象 共通分析
    # =========================================================

    def _analyze_group(self, shops, coupons, field):
        count = {}
        prices = {}
        shop_sets = {}

        for shop in shops:
            shop_name = getattr(shop, "name", "") or "名称未設定"
            shop_coupons = getattr(shop, "coupons", []) or []

            values_in_shop = set()

            for coupon in shop_coupons:
                value = self._clean_value(
                    getattr(coupon, field, None)
                )

                if not value:
                    value = "未分類"

                count[value] = count.get(value, 0) + 1

                values_in_shop.add(value)

                price = self._get_valid_price(coupon)

                if price is not None:
                    prices.setdefault(value, []).append(price)

            for value in values_in_shop:
                shop_sets.setdefault(value, set()).add(shop_name)

        shop_count = {
            value: len(shop_names)
            for value, shop_names in shop_sets.items()
        }

        return {
            "count": count,
            "shop_count": shop_count,
            "price_stats": self._build_price_stats(prices),
        }

    # =========================================================
    # 価格統計
    # =========================================================

    def _build_price_stats(self, prices):
        stats = {}

        for value, values in prices.items():
            if not values:
                continue

            stats[value] = {
                "count": len(values),
                "average": round(mean(values)),
                "median": round(median(values)),
                "minimum": min(values),
                "maximum": max(values),
            }

        return stats

    # =========================================================
    # 全体価格分析
    # =========================================================

    def _analyze_price(self, coupons):
        prices = []

        for coupon in coupons:
            price = self._get_valid_price(coupon)

            if price is not None:
                prices.append(price)

        if not prices:
            return {
                "count": 0,
                "average": None,
                "median": None,
                "minimum": None,
                "maximum": None,
            }

        return {
            "count": len(prices),
            "average": round(mean(prices)),
            "median": round(median(prices)),
            "minimum": min(prices),
            "maximum": max(prices),
        }

    # =========================================================
    # 有効価格判定
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
    # 文字列整形
    # =========================================================

    def _clean_value(self, value):
        if value is None:
            return ""

        return str(value).strip()