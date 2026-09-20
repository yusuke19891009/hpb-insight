from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from statistics import mean
from typing import Any


@dataclass
class AnalysisResult:
    """
    クーポン分析結果を保持するデータクラス。

    将来的にExcel出力・AIレポート・競合比較などへ
    発展させることを想定した共通データ構造。
    """

    total_coupons: int = 0

    category_count: dict[str, int] = field(default_factory=dict)
    category_average_price: dict[str, float] = field(default_factory=dict)

    target_count: dict[str, int] = field(default_factory=dict)
    target_average_price: dict[str, float] = field(default_factory=dict)


class AnalysisEngine:
    """
    HPBクーポン分析エンジン。

    現段階では以下を分析する。

    ・総クーポン数
    ・カテゴリ別件数
    ・カテゴリ別平均価格
    ・対象別件数
    ・対象別平均価格

    通常価格・販売価格・割引率は使用しない。
    """

    def analyze(self, shop: Any) -> AnalysisResult:
        """
        Shopオブジェクトを分析してAnalysisResultを返す。
        """

        coupons = getattr(shop, "coupons", None) or []

        result = AnalysisResult()

        result.total_coupons = len(coupons)

        result.category_count = self._count_by_category(coupons)

        result.category_average_price = self._average_price_by_category(
            coupons
        )

        result.target_count = self._count_by_target(coupons)

        result.target_average_price = self._average_price_by_target(
            coupons
        )

        return result

    # ==========================================================
    # カテゴリ別件数
    # ==========================================================

    def _count_by_category(
        self,
        coupons: list[Any],
    ) -> dict[str, int]:

        counter: Counter[str] = Counter()

        for coupon in coupons:

            category = self._get_category(coupon)

            if not category:
                category = "未分類"

            counter[category] += 1

        return dict(counter)

    # ==========================================================
    # カテゴリ別平均価格
    # ==========================================================

    def _average_price_by_category(
        self,
        coupons: list[Any],
    ) -> dict[str, float]:

        prices: dict[str, list[int]] = defaultdict(list)

        for coupon in coupons:

            category = self._get_category(coupon)

            if not category:
                category = "未分類"

            price = self._get_price(coupon)

            if price is None:
                continue

            prices[category].append(price)

        result: dict[str, float] = {}

        for category, values in prices.items():

            if not values:
                continue

            result[category] = round(mean(values), 0)

        return result

    # ==========================================================
    # 対象別件数
    # ==========================================================

    def _count_by_target(
        self,
        coupons: list[Any],
    ) -> dict[str, int]:

        counter: Counter[str] = Counter()

        for coupon in coupons:

            target = self._get_target(coupon)

            if not target:
                target = "未設定"

            counter[target] += 1

        return dict(counter)

    # ==========================================================
    # 対象別平均価格
    # ==========================================================

    def _average_price_by_target(
        self,
        coupons: list[Any],
    ) -> dict[str, float]:

        prices: dict[str, list[int]] = defaultdict(list)

        for coupon in coupons:

            target = self._get_target(coupon)

            if not target:
                target = "未設定"

            price = self._get_price(coupon)

            if price is None:
                continue

            prices[target].append(price)

        result: dict[str, float] = {}

        for target, values in prices.items():

            if not values:
                continue

            result[target] = round(mean(values), 0)

        return result

    # ==========================================================
    # Couponからカテゴリを取得
    # ==========================================================

    @staticmethod
    def _get_category(
        coupon: Any,
    ) -> str:

        value = getattr(
            coupon,
            "category",
            None,
        )

        if value is None:
            value = getattr(
                coupon,
                "coupon_category",
                None,
            )

        if value is None:
            return ""

        return str(value).strip()

    # ==========================================================
    # Couponから対象を取得
    # ==========================================================

    @staticmethod
    def _get_target(
        coupon: Any,
    ) -> str:

        value = getattr(
            coupon,
            "target",
            None,
        )

        if value is None:
            value = getattr(
                coupon,
                "target_type",
                None,
            )

        if value is None:
            return ""

        return str(value).strip()

    # ==========================================================
    # Couponから価格を取得
    # ==========================================================

    @staticmethod
    def _get_price(
        coupon: Any,
    ) -> int | None:

        value = getattr(
            coupon,
            "price",
            None,
        )

        if value is None:
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value)

        try:

            text = str(value).strip()

            if not text:
                return None

            # 「7,000円」などにも対応
            text = (
                text
                .replace(",", "")
                .replace("円", "")
                .strip()
            )

            return int(float(text))

        except (ValueError, TypeError):

            return None

    # ==========================================================
    # 分析結果をコンソール表示
    # ==========================================================

    def print_result(
        self,
        result: AnalysisResult,
    ) -> None:

        print("")
        print("=" * 60)
        print("分析結果")
        print("=" * 60)

        print("")
        print(f"総クーポン数：{result.total_coupons}件")

        print("")
        print("【カテゴリ別件数】")

        if result.category_count:

            for category, count in result.category_count.items():

                print(
                    f"{category}：{count}件"
                )

        else:

            print("データなし")

        print("")
        print("【カテゴリ別平均価格】")

        if result.category_average_price:

            for category, price in result.category_average_price.items():

                print(
                    f"{category}：{price:,.0f}円"
                )

        else:

            print("データなし")

        print("")
        print("【対象別件数】")

        if result.target_count:

            for target, count in result.target_count.items():

                print(
                    f"{target}：{count}件"
                )

        else:

            print("データなし")

        print("")
        print("【対象別平均価格】")

        if result.target_average_price:

            for target, price in result.target_average_price.items():

                print(
                    f"{target}：{price:,.0f}円"
                )

        else:

            print("データなし")

        print("")
        print("=" * 60)


# ==============================================================
# 単体テスト用
# ==============================================================

if __name__ == "__main__":

    from types import SimpleNamespace

    test_shop = SimpleNamespace(
        coupons=[
            SimpleNamespace(
                category="カット",
                target="新規",
                price=4000,
            ),
            SimpleNamespace(
                category="カット",
                target="再来",
                price=4500,
            ),
            SimpleNamespace(
                category="カラー",
                target="新規",
                price=7000,
            ),
            SimpleNamespace(
                category="カラー",
                target="全員",
                price=8000,
            ),
        ]
    )

    engine = AnalysisEngine()

    result = engine.analyze(test_shop)

    engine.print_result(result)
    