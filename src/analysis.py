from statistics import mean


class CouponAnalyzer:
    """
    Hot Pepper Beauty クーポン分析エンジン

    分析結果を以下の構造で返す。

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
            "average_price": カテゴリ別平均価格
        },
        "price": {
            "count": 有効価格件数,
            "average": 平均価格,
            "minimum": 最低価格,
            "maximum": 最高価格
        },
        "order": {
            "first": 最上位掲載順位,
            "last": 最下位掲載順位
        }
    }

    ※ 価格0円・欠損値は価格分析から除外する。
    """

    # ==========================================================
    # メイン分析
    # ==========================================================

    def analyze(self, shop):
        """
        Shopオブジェクトを分析し、
        構造化された分析結果を返す。
        """

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

    # ==========================================================
    # 対象別分析
    # ==========================================================

    def _analyze_target(self, coupons):
        """
        新規・再来・全員・未分類などの対象別分析。
        """

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

    # ==========================================================
    # カテゴリ別分析
    # ==========================================================

    def _analyze_category(self, coupons):
        """
        クーポンカテゴリ別分析。
        """

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

        for category, values in prices.items():

            if values:
                average_price[category] = round(mean(values))

        return {
            "count": count,
            "average_price": average_price,
        }

    # ==========================================================
    # 全体価格分析
    # ==========================================================

    def _analyze_price(self, coupons):
        """
        全クーポンの価格分析。

        0円・None・空文字などは除外する。
        """

        prices = []

        for coupon in coupons:

            price = self._get_valid_price(coupon)

            if price is not None:
                prices.append(price)

        if not prices:

            return {
                "count": 0,
                "average": None,
                "minimum": None,
                "maximum": None,
            }

        return {
            "count": len(prices),
            "average": round(mean(prices)),
            "minimum": min(prices),
            "maximum": max(prices),
        }

    # ==========================================================
    # 掲載順位分析
    # ==========================================================

    def _analyze_order(self, coupons):
        """
        クーポン掲載順位を分析する。
        """

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

    # ==========================================================
    # 有効価格取得
    # ==========================================================

    def _get_valid_price(self, coupon):
        """
        クーポンから有効な価格を取得する。

        除外対象：
        - None
        - 空文字
        - 0
        - マイナス値
        - 数値変換できない値
        """

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

    # ==========================================================
    # 文字列整理
    # ==========================================================

    def _clean_value(self, value):
        """
        分析用の文字列を安全に整理する。
        """

        if value is None:
            return ""

        return str(value).strip()