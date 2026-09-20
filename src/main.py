from __future__ import annotations

from scraper import HotPepperScraper
from pricing_analysis import PricingAnalyzer
from area_analysis import AreaCouponAnalyzer


def print_separator():
    print("\n" + "=" * 70)


def print_category_analysis(
    shop_name: str,
    category_analysis: dict,
):
    print_separator()
    print(f"【{shop_name}】カテゴリ別価格分析")

    if not category_analysis:
        print("カテゴリ別価格分析データがありません。")
        return

    for category, data in category_analysis.items():
        print("\n" + "-" * 60)
        print(f"【{category}】")

        print(
            f"自店舗クーポン数: "
            f"{data.get('shop_coupon_count', 0)}"
        )

        shop_average = data.get("shop_average")
        shop_median = data.get("shop_median")

        if shop_average is not None:
            print(f"自店舗平均: {shop_average:,.0f}円")

        if shop_median is not None:
            print(f"自店舗中央値: {shop_median:,.0f}円")

        comparison_shop_count = data.get(
            "comparison_shop_count", 0
        )

        comparison_coupon_count = data.get(
            "comparison_coupon_count", 0
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
                f"比較店舗平均"
                f"（店舗中央値ベース）: "
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

        difference = data.get("difference")

        if difference is not None:
            sign = "+" if difference > 0 else ""
            print(
                f"比較店舗中央値との差: "
                f"{sign}{difference:,.0f}円"
            )

        ratio = data.get("ratio")

        if ratio is not None:
            print(f"価格比率: {ratio:.1f}%")

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

        recommended_price = data.get(
            "recommended_price"
        )

        recommended_min = data.get(
            "recommended_min"
        )

        recommended_max = data.get(
            "recommended_max"
        )

        recommendation_note = data.get(
            "recommendation_note"
        )

        if recommended_price is not None:
            print(
                f"適正価格参考値: "
                f"{recommended_price:,.0f}円"
            )

            if (
                recommended_min is not None
                and recommended_max is not None
            ):
                print(
                    f"参考価格帯: "
                    f"{recommended_min:,.0f}"
                    f"～"
                    f"{recommended_max:,.0f}円"
                )

        if recommendation_note:
            print(
                f"参考情報: "
                f"{recommendation_note}"
            )


def print_overall_analysis(
    shop_name: str,
    pricing_result: dict,
):
    print_separator()
    print(f"【{shop_name}】全体価格分析")

    print(
        f"自店舗価格データ数: "
        f"{pricing_result.get('shop_price_count', 0)}"
    )

    shop_average = pricing_result.get("shop_average")

    if shop_average is not None:
        print(
            f"自店舗平均: "
            f"{shop_average:,.0f}円"
        )

    shop_median = pricing_result.get("shop_median")

    if shop_median is not None:
        print(
            f"自店舗中央値: "
            f"{shop_median:,.0f}円"
        )

    comparison_shop_count = pricing_result.get(
        "comparison_shop_count", 0
    )

    comparison_coupon_count = pricing_result.get(
        "comparison_coupon_count", 0
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
            f"比較店舗平均"
            f"（店舗中央値ベース）: "
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

    difference = pricing_result.get("difference")

    if difference is not None:
        sign = "+" if difference > 0 else ""
        print(
            f"比較店舗中央値との差: "
            f"{sign}{difference:,.0f}円"
        )

    ratio = pricing_result.get("ratio")

    if ratio is not None:
        print(
            f"価格比率: "
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


def main():
    print("=" * 70)
    print("ちゃぴおHPB Toolkit v1.7.1")
    print("クーポン価格分析・店舗別中央値比較")
    print("=" * 70)

    scraper = HotPepperScraper()

    print("\nHotPepper Beautyの店舗URLを入力してください。")
    print("複数店舗を入力できます。")
    print("入力終了は空Enterです。\n")

    urls = []

    while True:
        url = input("URL: ").strip()

        if not url:
            break

        urls.append(url)

    if not urls:
        print("\nURLが入力されていません。")
        return

    print("\n" + "=" * 70)
    print(f"{len(urls)}店舗のデータ取得を開始します。")
    print("=" * 70)

    shops = []

    for index, url in enumerate(urls, start=1):
        print("\n" + "-" * 70)
        print(
            f"[{index}/{len(urls)}] 店舗データ取得中..."
        )

        try:
            # 元々動いていた正しい取得方法
            shop = scraper.scrape(url)

            if shop is None:
                print("店舗データを取得できませんでした。")
                continue

            shops.append(shop)

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
                f"取得中にエラーが発生しました: {e}"
            )

    if not shops:
        print("\n店舗データを取得できませんでした。")
        return

    # ---------------------------------------------------------
    # エリア分析
    # ---------------------------------------------------------
    try:
        area_analyzer = AreaCouponAnalyzer()
        area_analysis = area_analyzer.analyze(shops)
    except Exception as e:
        print(
            f"\nエリア分析でエラーが発生しました: {e}"
        )
        return

    # ---------------------------------------------------------
    # 価格分析
    # ---------------------------------------------------------
    pricing_analyzer = PricingAnalyzer()

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

        # 全体価格分析
        try:
            pricing_result = (
                pricing_analyzer.analyze_summary(
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
                f"\n全体価格分析エラー: {e}"
            )

        # カテゴリ別価格分析
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
                f"\nカテゴリ別価格分析エラー: {e}"
            )

    print_separator()
    print("分析が完了しました。")
    print("=" * 70)


if __name__ == "__main__":
    main()