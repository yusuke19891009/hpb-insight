from statistics import mean, median


class CouponAnalyzer:
    """
    Hot Pepper Beauty クーポン分析エンジン

    分析結果:

    {
        "shop": {
            "name": 店舗名,
            "coupon_count": クーポン総数
        },

        "target": {
            "count": 対象別件数,
            "average_price": 対象別平均価格
        },

        "category": {
            "count": カテゴリ別件数,
            "average_price": カテゴリ別平均価格,
            "price_stats": {
                カテゴリ: {
                    "count": 件数,
                    "average": 平均価格,
                    "median": 中央値,
                    "minimum": 最低価格,
                    "maximum": 最高価格
                }
            }
        },

        "price": {
            "count": 有効価格件数,
            "average": 平均価格,
            "median": 中央値,
            "minimum": 最低価格,
            "maximum": 最高価格
        },

        "order": {
            "first": 最上位掲載順位,
            "last": 最下位掲載順位
        }
    }
    """

    def analyze(self, shop):
        coupons = getattr(shop, "coupons", []) or []

        return {
            "shop": {
                "name": getattr(shop, "name", ""),
                "coupon_count": len(coupons),
            },
            "target": self._analyze_target(coupons),
            "category": self._analyze_category(coupons),
            "price": self._analyze_price(coupons),
            "order": self._analyze_order(coupons),
        }

    # =========================================================
    # 対象別分析
    # =========================================================

    def _analyze_target(self, coupons):
        count = {}
        prices = {}

        for coupon in coupons:
            target = self._clean_value(
                getattr(coupon, "target", None)
            )

            if not target:
                target = "未分類"

            count[target] = count.get(target, 0) + 1

            price = self._get_valid_price(coupon)

            if price is not None:
                prices.setdefault(target, []).append(price)

        average_price = {}

        for target, values in prices.items():
            if values:
                average_price[target] = round(mean(values))

        return {
            "count": count,
            "average_price": average_price,
        }

    # =========================================================
    # カテゴリ別分析
    # =========================================================

    def _analyze_category(self, coupons):
        count = {}
        prices = {}

        for coupon in coupons:
            category = self._clean_value(
                getattr(coupon, "category", None)
            )

            if not category:
                category = "未分類"

            count[category] = count.get(category, 0) + 1

            price = self._get_valid_price(coupon)

            if price is not None:
                prices.setdefault(category, []).append(price)

        average_price = {}
        price_stats = {}

        for category, values in prices.items():
            if not values:
                continue

            average_price[category] = round(mean(values))

            price_stats[category] = {
                "count": len(values),
                "average": round(mean(values)),
                "median": round(median(values)),
                "minimum": min(values),
                "maximum": max(values),
            }

        return {
            "count": count,
            "average_price": average_price,
            "price_stats": price_stats,
        }

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
    # 掲載順位分析
    # =========================================================

    def _analyze_order(self, coupons):
        orders = []

        for coupon in coupons:
            order = getattr(coupon, "order", None)

            if order is None:
                continue

            try:
                orders.append(int(order))
            except (TypeError, ValueError):
                continue

        if not orders:
            return {
                "first": None,
                "last": None,
            }

        return {
            "first": min(orders),
            "last": max(orders),
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