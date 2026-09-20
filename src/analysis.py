from statistics import mean


class CouponAnalyzer:
    """
    Hot Pepper Beauty クーポン分析エンジン

    役割：
    - クーポン件数の集計
    - 対象別集計
    - カテゴリ別集計
    - 価格統計
    - 欠損値・0円データの適切な除外
    """

    def analyze(self, shop):
        """
        店舗のクーポンデータを分析する。
        """

        coupons = getattr(shop, "coupons", []) or []

        result = {
            "shop_name": getattr(shop, "name", ""),
            "coupon_count": len(coupons),
            "target": self._analyze_target(coupons),
            "category": self._analyze_category(coupons),
            "price": self._analyze_price(coupons),
            "order": self._analyze_order(coupons),
        }

        return result

    # ==========================================================
    # 対象別分析
    # ==========================================================

    def _analyze_target(self, coupons):
        """
        新規・再来・全員などの対象別に集計する。
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
        クーポンカテゴリ別に集計する。
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
        全クーポンの価格を分析する。

        0円・None・空文字は有効価格として扱わない。
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
    # 掲載順分析
    # ==========================================================

    def _analyze_order(self, coupons):
        """
        掲載順の最初・最後を取得する。
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
    # 価格取得
    # ==========================================================

    def _get_valid_price(self, coupon):
        """
        クーポンから有効な価格だけを取得する。

        以下は無効：
        - None
        - 空文字
        - 0
        - 数値に変換できない値
        """

        value = getattr(coupon, "price", None)

        if value is None:
            return None

        if isinstance(value, str):

            cleaned = value.strip()

            if not cleaned:
                return None

            cleaned = (
                cleaned
                .replace(",", "")
                .replace("円", "")
                .replace("￥", "")
                .replace("¥", "")
            )

            if not cleaned:
                return None

            value = cleaned

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
        分析用の文字列を安全に整形する。
        """

        if value is None:
            return ""

        return str(value).strip()