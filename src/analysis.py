from collections import Counter, defaultdict
from statistics import mean
from typing import Any


class CouponAnalyzer:
    """
    クーポン分析エンジン

    役割：
    - クーポン件数集計
    - 対象別件数・平均価格
    - カテゴリ別件数・平均価格
    - 掲載順位情報
    - 分析結果を辞書形式で返却

    ※ このクラスではCSV保存を行わない。
      分析と出力を分離することで、将来的なExcel・GUI・AI分析へ
      拡張しやすい構成にする。
    """

    def analyze(self, shop) -> dict[str, Any]:
        """
        Shopオブジェクトを分析して結果を返す。
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

    # =========================================================
    # 対象別分析
    # =========================================================

    def _analyze_target(self, coupons) -> dict[str, Any]:
        """
        新規・再来・全員などの対象別分析。
        """

        counter = Counter()

        for coupon in coupons:
            target = self._clean_value(
                getattr(coupon, "target", "")
            )

            if target:
                counter[target] += 1

        averages = {}

        for target in counter:
            prices = []

            for coupon in coupons:
                coupon_target = self._clean_value(
                    getattr(coupon, "target", "")
                )

                if coupon_target != target:
                    continue

                price = self._get_price(coupon)

                if price is not None:
                    prices.append(price)

            averages[target] = self._average(prices)

        return {
            "count": dict(counter),
            "average_price": averages,
        }

    # =========================================================
    # カテゴリ分析
    # =========================================================

    def _analyze_category(self, coupons) -> dict[str, Any]:
        """
        クーポンカテゴリ別分析。
        """

        counter = Counter()
        prices_by_category = defaultdict(list)

        for coupon in coupons:
            category = self._clean_value(
                getattr(coupon, "category", "")
            )

            if not category:
                category = "未分類"

            counter[category] += 1

            price = self._get_price(coupon)

            if price is not None:
                prices_by_category[category].append(price)

        average_price = {}

        for category, prices in prices_by_category.items():
            average_price[category] = self._average(prices)

        return {
            "count": dict(counter),
            "average_price": average_price,
        }

    # =========================================================
    # 価格分析
    # =========================================================

    def _analyze_price(self, coupons) -> dict[str, Any]:
        """
        クーポン価格全体の分析。
        """

        prices = []

        for coupon in coupons:
            price = self._get_price(coupon)

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
            "average": self._average(prices),
            "minimum": min(prices),
            "maximum": max(prices),
        }

    # =========================================================
    # 掲載順位分析
    # =========================================================

    def _analyze_order(self, coupons) -> dict[str, Any]:
        """
        掲載順位の分析。
        """

        orders = []

        for coupon in coupons:
            order = getattr(coupon, "order", None)

            if isinstance(order, int):
                orders.append(order)

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
    # ユーティリティ
    # =========================================================

    def _get_price(self, coupon):
        """
        Coupon.priceを安全に数値化する。
        """

        price = getattr(coupon, "price", None)

        if price is None:
            return None

        if isinstance(price, int):
            return price

        if isinstance(price, float):
            return int(price)

        if isinstance(price, str):
            cleaned = (
                price
                .replace(",", "")
                .replace("円", "")
                .replace("¥", "")
                .strip()
            )

            if not cleaned:
                return None

            try:
                return int(float(cleaned))
            except ValueError:
                return None

        return None

    def _clean_value(self, value) -> str:
        """
        文字列を安全に整形する。
        """

        if value is None:
            return ""

        return str(value).strip()

    def _average(self, values):
        """
        平均値を整数で返す。
        """

        if not values:
            return None

        return round(mean(values))