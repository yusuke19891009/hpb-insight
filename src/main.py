from shop_service import ShopService
from analysis import CouponAnalyzer
from area_analysis import AreaCouponAnalyzer
from pricing_analysis import PricingAnalyzer


def print_analysis_result(result):
    print("=" * 60)
    print("分析結果")
    print("=" * 60)

    if result is None:
        print("分析結果がありません。")
        print("=" * 60)
        return

    if isinstance(result, dict):
        for key, value in result.items():

            if isinstance(value, dict):
                print()
                print(f"【{key}】")

                for sub_key, sub_value in value.items():
                    print(f"{sub_key}：{sub_value}")

            elif isinstance(value, list):
                print()
                print(f"【{key}】")

                for item in value:
                    print(f"- {item}")

            else:
                print(f"{key}：{value}")

        print("=" * 60)
        return

    if isinstance(result, list):

        for item in result:
            print(item)

        print("=" * 60)
        return

    if hasattr(result, "__dict__"):

        data = vars(result)

        for key, value in data.items():

            if isinstance(value, dict):
                print()
                print(f"【{key}】")

                for sub_key, sub_value in value.items():
                    print(f"{sub_key}：{sub_value}")

            elif isinstance(value, list):
                print()
                print(f"【{key}】")

                for item in value:
                    print(f"- {item}")

            else:
                print(f"{key}：{value}")

        print("=" * 60)
        return

    print(result)
    print("=" * 60)


def print_area_analysis_result(result):
    print()
    print("=" * 60)
    print("エリア分析結果")
    print("=" * 60)

    if result is None:
        print("エリア分析結果がありません。")
        print("=" * 60)
        return

    shops = result.get("shops", {})

    print()
    print("【shops】")
    print(f"shop_count：{shops.get('shop_count')}")
    print(f"coupon_count：{shops.get('coupon_count')}")

    category = result.get("category", {})

    print()
    print("【category】")

    print(f"count：{category.get('count')}")
    print(f"shop_count：{category.get('shop_count')}")
    print(f"price_stats：{category.get('price_stats')}")

    target = result.get("target", {})

    print()
    print("【target】")

    print(f"count：{target.get('count')}")
    print(f"shop_count：{target.get('shop_count')}")
    print(f"price_stats：{target.get('price_stats')}")

    price = result.get("price", {})

    print()
    print("【price】")

    print(f"count：{price.get('count')}")
    print(f"average：{price.get('average')}")
    print(f"median：{price.get('median')}")
    print(f"minimum：{price.get('minimum')}")
    print(f"maximum：{price.get('maximum')}")

    print("=" * 60)


def print_pricing_summary(result):
    print()
    print("=" * 60)
    print("価格ポジション分析")
    print("=" * 60)

    if result is None:
        print("価格分析結果がありません。")
        print("=" * 60)
        return

    print()
    print(f"【店舗】{result.get('shop')}")

    print(
        f"有効価格クーポン数："
        f"{result.get('coupon_count')}件"
    )

    print()
    print("【自店舗価格】")

    shop_average = result.get("shop_average")
    shop_median = result.get("shop_median")

    if shop_average is not None:
        print(f"平均価格：{round(shop_average)}円")
    else:
        print("平均価格：判定不可")

    if shop_median is not None:
        print(f"中央値：{round(shop_median)}円")
    else:
        print("中央値：判定不可")

    print()
    print("【エリア価格】")

    area_average = result.get("area_average")
    area_median = result.get("area_median")

    if area_average is not None:
        print(f"平均価格：{round(area_average)}円")
    else:
        print("平均価格：判定不可")

    if area_median is not None:
        print(f"中央値：{round(area_median)}円")
    else:
        print("中央値：判定不可")

    print()
    print("【市場内ポジション】")

    difference = result.get(
        "difference_from_area_median"
    )

    ratio = result.get(
        "price_ratio_to_area_median"
    )

    position = result.get("position")

    if difference is not None:

        if difference > 0:
            difference_text = f"+{difference}円"
        else:
            difference_text = f"{difference}円"

        print(
            f"エリア平均との差額："
            f"{difference_text}"
        )

    else:
        print("エリア平均との差額：判定不可")

    if ratio is not None:
        print(
            f"中央値に対する価格比率："
            f"{ratio}%"
        )
    else:
        print(
            "中央値に対する価格比率："
            "判定不可"
        )

    print(
        f"価格ポジション："
        f"{position}"
    )

    print("=" * 60)


def print_category_pricing_result(result):
    """
    カテゴリ別価格ポジションを表示する。
    """

    print()
    print("=" * 60)
    print("カテゴリ別価格ポジション分析")
    print("=" * 60)

    if result is None:
        print("カテゴリ分析結果がありません。")
        print("=" * 60)
        return

    shop_name = result.get(
        "shop",
        ""
    )

    categories = result.get(
        "categories",
        []
    )

    print()
    print(f"【店舗】{shop_name}")

    print(
        f"分析カテゴリ数："
        f"{len(categories)}"
    )

    if not categories:
        print()
        print("分析可能なカテゴリがありません。")
        print("=" * 60)
        return

    for item in categories:

        print()
        print("-" * 60)

        print(
            f"【{item.get('category')}】"
        )

        print(
            f"クーポン数："
            f"{item.get('coupon_count')}件"
        )

        print()
        print("自店舗価格")

        shop_average = item.get(
            "shop_average"
        )

        shop_median = item.get(
            "shop_median"
        )

        if shop_average is not None:
            print(
                f"平均："
                f"{round(shop_average)}円"
            )
        else:
            print("平均：判定不可")

        if shop_median is not None:
            print(
                f"中央値："
                f"{round(shop_median)}円"
            )
        else:
            print("中央値：判定不可")

        print()
        print("同カテゴリ比較")

        comparison_shop_count = item.get(
            "comparison_shop_count",
            0
        )

        comparison_coupon_count = item.get(
            "comparison_coupon_count",
            0
        )

        print(
            f"比較対象店舗数："
            f"{comparison_shop_count}店舗"
        )

        print(
            f"比較対象クーポン数："
            f"{comparison_coupon_count}件"
        )

        comparison_average = item.get(
            "comparison_average"
        )

        comparison_median = item.get(
            "comparison_median"
        )

        if comparison_average is not None:
            print(
                f"比較平均："
                f"{round(comparison_average)}円"
            )
        else:
            print("比較平均：なし")

        if comparison_median is not None:
            print(
                f"比較中央値："
                f"{round(comparison_median)}円"
            )
        else:
            print("比較中央値：なし")

        print()
        print("市場内ポジション")

        difference = item.get(
            "difference_from_comparison_median"
        )

        ratio = item.get(
            "price_ratio_to_comparison_median"
        )

        position = item.get(
            "position"
        )

        if difference is not None:

            if difference > 0:
                difference_text = (
                    f"+{difference}円"
                )
            else:
                difference_text = (
                    f"{difference}円"
                )

            print(
                f"比較中央値との差額："
                f"{difference_text}"
            )

        else:
            print(
                "比較中央値との差額："
                "比較対象なし"
            )

        if ratio is not None:
            print(
                f"比較中央値に対する価格比率："
                f"{ratio}%"
            )
        else:
            print(
                "比較中央値に対する価格比率："
                "比較対象なし"
            )

        print(
            f"価格ポジション："
            f"{position}"
        )

        print()
        print("参考：エリア全体")

        area_average = item.get(
            "area_average"
        )

        area_median = item.get(
            "area_median"
        )

        if area_average is not None:
            print(
                f"エリア全体平均："
                f"{round(area_average)}円"
            )
        else:
            print(
                "エリア全体平均：なし"
            )

        if area_median is not None:
            print(
                f"エリア全体中央値："
                f"{round(area_median)}円"
            )
        else:
            print(
                "エリア全体中央値：なし"
            )

    print()
    print("=" * 60)


def main():

    print("=" * 60)
    print("HPB Insight")
    print("v1.6.0")
    print("=" * 60)

    print(
        "HotPepper URLを入力してください。"
    )

    print(
        "複数取得する場合は、"
        "1店舗ずつ入力してください。"
    )

    print(
        "空行で入力を終了します。"
    )

    print("=" * 60)

    urls = []

    while True:

        url = input("> ").strip()

        if not url:
            break

        urls.append(url)

    if not urls:

        print(
            "URLが入力されていません。"
        )

        return

    service = ShopService()
    analyzer = CouponAnalyzer()
    area_analyzer = AreaCouponAnalyzer()
    pricing_analyzer = PricingAnalyzer()

    shops = []

    print()
    print("=" * 60)
    print(
        f"{len(urls)}店舗の取得を開始します"
    )
    print("=" * 60)

    # =========================================================
    # 店舗ごとのスクレイピング
    # =========================================================

    for index, url in enumerate(
        urls,
        start=1
    ):

        print()
        print("=" * 60)
        print(
            f"{index} / {len(urls)} 店舗取得開始"
        )
        print("=" * 60)

        try:

            shop = service.scrape(url)

            shops.append(shop)

            print()
            print("=" * 60)
            print("取得結果")
            print("=" * 60)

            print(
                f"店舗名：{shop.name}"
            )

            print(
                f"取得件数："
                f"{len(shop.coupons)}件"
            )

            print("=" * 60)

            service.export(shop)

        except KeyboardInterrupt:

            print()
            print(
                "処理を中断しました。"
            )

            return

        except Exception as e:

            print()
            print("=" * 60)
            print(
                "スクレイピング中に"
                "エラーが発生しました"
            )
            print("=" * 60)

            print(type(e).__name__)
            print(e)

            print("=" * 60)

    # =========================================================
    # スクレイピング全体結果
    # =========================================================

    print()
    print("=" * 60)
    print("スクレイピング処理完了")
    print("=" * 60)

    print(
        f"取得店舗数：{len(shops)}"
    )

    total_coupons = sum(
        len(shop.coupons)
        for shop in shops
    )

    print(
        f"総クーポン数："
        f"{total_coupons}"
    )

    print("=" * 60)

    # =========================================================
    # 店舗別分析
    # =========================================================

    print()
    print("=" * 60)
    print("店舗別分析エンジン起動")
    print("=" * 60)

    for shop in shops:

        print()
        print("-" * 60)
        print(
            f"【分析対象】"
            f"{shop.name}"
        )
        print("-" * 60)

        try:

            result = analyzer.analyze(shop)

            print_analysis_result(
                result
            )

        except Exception as e:

            print()
            print("=" * 60)
            print(
                "分析中に"
                "エラーが発生しました"
            )
            print("=" * 60)

            print(type(e).__name__)
            print(e)

            print("=" * 60)

    # =========================================================
    # エリア分析
    # =========================================================

    area_result = None

    if shops:

        print()
        print("=" * 60)
        print("エリア分析エンジン起動")
        print("=" * 60)

        try:

            area_result = (
                area_analyzer.analyze(
                    shops
                )
            )

            print_area_analysis_result(
                area_result
            )

        except Exception as e:

            print()
            print("=" * 60)
            print(
                "エリア分析中に"
                "エラーが発生しました"
            )
            print("=" * 60)

            print(type(e).__name__)
            print(e)

            print("=" * 60)

    # =========================================================
    # 価格ポジション分析
    # =========================================================

    if shops and area_result:

        print()
        print("=" * 60)
        print(
            "価格ポジション分析"
            "エンジン起動"
        )
        print("=" * 60)

        for shop in shops:

            print()
            print("-" * 60)
            print(
                f"【分析対象】"
                f"{shop.name}"
            )
            print("-" * 60)

            try:

                pricing_result = (
                    pricing_analyzer
                    .analyze_summary(
                        shop,
                        area_result
                    )
                )

                print_pricing_summary(
                    pricing_result
                )

            except Exception as e:

                print()
                print("=" * 60)
                print(
                    "価格ポジション分析中に"
                    "エラーが発生しました"
                )
                print("=" * 60)

                print(type(e).__name__)
                print(e)

                print("=" * 60)

    # =========================================================
    # カテゴリ別価格ポジション分析
    # =========================================================

    if shops and area_result:

        print()
        print("=" * 60)
        print(
            "カテゴリ別価格ポジション"
            "分析エンジン起動"
        )
        print("=" * 60)

        for shop in shops:

            print()
            print("-" * 60)
            print(
                f"【分析対象】"
                f"{shop.name}"
            )
            print("-" * 60)

            try:

                category_result = (
                    pricing_analyzer
                    .analyze_category_summary(
                        shop,
                        area_result,
                        shops
                    )
                )

                print_category_pricing_result(
                    category_result
                )

            except Exception as e:

                print()
                print("=" * 60)
                print(
                    "カテゴリ別価格分析中に"
                    "エラーが発生しました"
                )
                print("=" * 60)

                print(type(e).__name__)
                print(e)

                print("=" * 60)

    # =========================================================
    # 全処理完了
    # =========================================================

    print()
    print("=" * 60)
    print("全処理完了")
    print("=" * 60)

    print(
        f"取得店舗数："
        f"{len(shops)}"
    )

    print(
        f"総クーポン数："
        f"{total_coupons}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()