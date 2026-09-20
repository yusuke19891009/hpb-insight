from __future__ import annotations

from scraper import HotPepperScraper
from pricing_analysis import PricingAnalyzer
from area_analysis import AreaCouponAnalyzer


def print_separator():
    print("\n" + "=" * 70)


def print_reference_info(data: dict):
    """
    v1.8.0 市場参考価格情報を表示する。
    """

    reference_price = data.get(
        "market_reference_price"
    )

    reference_min = data.get(
        "reference_price_min"
    )

    reference_max = data.get(
        "reference_price_max"
    )

    reference_level = data.get(
        "reference_level",
        "比較不可",
    )

    reference_reason = data.get(
        "reference_reason",
        "",
    )

    print(
        f"市場参考価格: "
        f"{reference_price:,.0f}円"
        if reference_price is not None
        else "市場参考価格: 算出不可"
    )

    if (
        reference_min is not None
        and reference_max is not None
    ):
        print(
            f"参考価格帯: "
            f"{reference_min:,.0f}"
            f"～"
            f"{reference_max:,.0f}円"
        )

    print(
        f"参考度: {reference_level}"
    )

    if reference_reason:
        print(
            f"参考度の理由: {reference_reason}"
        )


def print_category_analysis(
    shop_name: str,
    category_analysis: dict,
):
    print_separator()
    print(
        f"【{shop_name}】カテゴリ別価格分析"
    )

    if not category_analysis:
        print(
            "カテゴリ別価格分析データがありません。"
        )
        return

    for category, data in category_analysis.items():

        print("\n" + "-" * 60)
        print(f"【{category}】")

        print(
            f"自店舗クーポン数: "
            f"{data.get('shop_coupon_count', 0)}"
        )

        shop_average = data.get(
            "shop_average"
        )

        if shop_average is not None:
            print(
                f"自店舗平均価格: "
                f"{shop_average:,.0f}円"
            )

        shop_median = data.get(
            "shop_median"
        )

        if shop_median is not None:
            print(
                f"自店舗中央値: "
                f"{shop_median:,.0f}円"
            )

        comparison_shop_count = data.get(
            "comparison_shop_count",
            0,
        )

        comparison_coupon_count = data.get(
            "comparison_coupon_count",
            0,
        )

        print(
            f"比較対象店舗数: "
            f"{comparison_shop_count}"
        )

        print(
            f"比較対象クーポン数: "
            f"{comparison_coupon_count}"
        )

        comparison_average = data.get(
            "comparison_average"
        )

        if comparison_average is not None:
            print(
                f"比較店舗中央値の平均: "
                f"{comparison_average:,.0f}円"
            )

        comparison_median = data.get(
            "comparison_median"
        )

        if comparison_median is not None:
            print(
                f"比較店舗中央値: "
                f"{comparison_median:,.0f}円"
            )

        difference = data.get(
            "difference"
        )

        if difference is not None:
            sign = (
                "+"
                if difference > 0
                else ""
            )

            print(
                f"比較店舗中央値との差: "
                f"{sign}{difference:,.0f}円"
            )

        ratio = data.get(
            "ratio"
        )

        if ratio is not None:
            print(
                f"価格対比率: "
                f"{ratio:.1f}%"
            )

        print(
            f"価格ポジション: "
            f"{data.get('position', '比較不可')}"
        )

        comparison_method = data.get(
            "comparison_method"
        )

        if comparison_method:
            print(
                f"比較方法: "
                f"{comparison_method}"
            )

        print("\n--- 市場参考価格 ---")

        print_reference_info(
            data
        )


def print_overall_analysis(
    shop_name: str,
    pricing_result: dict,
):
    print_separator()
    print(
        f"【{shop_name}】全体価格分析"
    )

    print(
        f"自店舗価格データ数: "
        f"{pricing_result.get('shop_price_count', 0)}"
    )

    shop_average = pricing_result.get(
        "shop_average"
    )

    if shop_average is not None:
        print(
            f"自店舗平均価格: "
            f"{shop_average:,.0f}円"
        )

    shop_median = pricing_result.get(
        "shop_median"
    )

    if shop_median is not None:
        print(
            f"自店舗中央値: "
            f"{shop_median:,.0f}円"
        )

    comparison_shop_count = pricing_result.get(
        "comparison_shop_count",
        0,
    )

    comparison_coupon_count = pricing_result.get(
        "comparison_coupon_count",
        0,
    )

    print(
        f"比較対象店舗数: "
        f"{comparison_shop_count}"
    )

    print(
        f"比較対象クーポン数: "
        f"{comparison_coupon_count}"
    )

    comparison_average = pricing_result.get(
        "comparison_average"
    )

    if comparison_average is not None:
        print(
            f"比較店舗中央値の平均: "
            f"{comparison_average:,.0f}円"
        )

    comparison_median = pricing_result.get(
        "comparison_median"
    )

    if comparison_median is not None:
        print(
            f"比較店舗中央値: "
            f"{comparison_median:,.0f}円"
        )

    difference = pricing_result.get(
        "difference"
    )

    if difference is not None:
        sign = (
            "+"
            if difference > 0
            else ""
        )

        print(
            f"比較店舗中央値との差: "
            f"{sign}{difference:,.0f}円"
        )

    ratio = pricing_result.get(
        "ratio"
    )

    if ratio is not None:
        print(
            f"価格対比率: "
            f"{ratio:.1f}%"
        )

    print(
        f"価格ポジション: "
        f"{pricing_result.get('position', '比較不可')}"
    )

    print(
        f"比較方法: "
        f"{pricing_result.get('comparison_method', '')}"
    )

    print("\n--- 市場参考価格 ---")

    print_reference_info(
        pricing_result
    )


def main():

    print("=" * 70)
    print(
        "ちゃぴおHPB Toolkit v1.8.0"
    )
    print(
        "クーポン価格分析・市場参考価格・参考度分析"
    )
    print("=" * 70)

    scraper = HotPepperScraper()

    print(
        "\nHotPepper Beautyの店舗URLを入力してください。"
    )

    print(
        "複数店舗を入力できます。"
    )

    print(
        "入力終了は空Enterです。\n"
    )

    urls = []

    while True:

        url = input("URL: ").strip()

        if not url:
            break

        urls.append(url)

    if not urls:
        print(
            "\nURLが入力されていません。"
        )
        return

    print("\n" + "=" * 70)

    print(
        f"{len(urls)}店舗のデータ取得を開始します。"
    )

    print("=" * 70)

    shops = []

    for index, url in enumerate(
        urls,
        start=1,
    ):

        print("\n" + "-" * 70)

        print(
            f"[{index}/{len(urls)}] "
            "店舗データ取得中..."
        )

        try:

            shop = scraper.scrape(
                url
            )

            if shop is None:

                print(
                    "店舗データを取得できませんでした。"
                )

                continue

            shops.append(
                shop
            )

            print(
                f"取得完了: "
                f"{getattr(shop, 'name', '不明')}"
            )

            print(
                f"クーポン数: "
                f"{len(getattr(shop, 'coupons', []))}"
            )

        except Exception as e:

            print(
                "取得中にエラーが発生しました: "
                f"{e}"
            )

    if not shops:

        print(
            "\n店舗データを取得できませんでした。"
        )

        return

    # =========================================================
    # エリア分析
    # =========================================================

    try:

        area_analyzer = (
            AreaCouponAnalyzer()
        )

        area_analysis = (
            area_analyzer.analyze(
                shops
            )
        )

    except Exception as e:

        print(
            "\nエリア分析でエラーが発生しました: "
            f"{e}"
        )

        return

    # =========================================================
    # 価格分析
    # =========================================================

    pricing_analyzer = (
        PricingAnalyzer()
    )

    for shop in shops:

        shop_name = getattr(
            shop,
            "name",
            "不明店舗",
        )

        print_separator()

        print(
            f"########## {shop_name} ##########"
        )

        # -----------------------------------------------------
        # 全体価格分析
        # -----------------------------------------------------

        try:

            pricing_result = (
                pricing_analyzer
                .analyze_summary(
                    shop,
                    shops,
                )
            )

            print_overall_analysis(
                shop_name,
                pricing_result,
            )

        except Exception as e:

            print(
                "\n全体価格分析エラー: "
                f"{e}"
            )

        # -----------------------------------------------------
        # カテゴリ別価格分析
        # -----------------------------------------------------

        try:

            category_analysis = (
                pricing_analyzer
                .analyze_category_summary(
                    shop,
                    area_analysis,
                    shops,
                )
            )

            print_category_analysis(
                shop_name,
                category_analysis,
            )

        except Exception as e:

            print(
                "\nカテゴリ別価格分析エラー: "
                f"{e}"
            )

    print_separator()

    print(
        "分析が完了しました。"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()