from shop_service import ShopService

try:
    from services.analysis import CouponAnalyzer
except ModuleNotFoundError:
    from analysis import CouponAnalyzer


def print_analysis_result(result):
    """
    分析結果をコンソールへ表示する。
    dict / list / オブジェクトのいずれにも対応する。
    """

    print()
    print("=" * 60)
    print("分析結果")
    print("=" * 60)

    if result is None:
        print("分析結果がありません。")
        print("=" * 60)
        return

    # ----------------------------------------------------------
    # dictの場合
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # listの場合
    # ----------------------------------------------------------

    if isinstance(result, list):

        for item in result:
            print(item)

        print("=" * 60)
        return

    # ----------------------------------------------------------
    # オブジェクトの場合
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # その他
    # ----------------------------------------------------------

    print(result)
    print("=" * 60)


def main():

    print("=" * 60)
    print("HPB Insight")
    print("v1.3.0")
    print("=" * 60)

    print("HotPepper URLを入力してください。")
    print("複数取得する場合は空行で終了します。")
    print("=" * 60)

    urls = []

    while True:

        url = input("> ").strip()

        if not url:
            break

        urls.append(url)

    if not urls:

        print("URLが入力されていません。")
        return

    service = ShopService()
    analyzer = CouponAnalyzer()

    shops = []

    # ==========================================================
    # スクレイピング
    # ==========================================================

    print()
    print("=" * 60)
    print(f"{len(urls)}店舗の取得を開始します")
    print("=" * 60)

    for index, url in enumerate(urls, start=1):

        print()
        print("=" * 60)
        print(f"{index} / {len(urls)} 店舗取得開始")
        print("=" * 60)

        try:

            shop = service.scrape(url)

            shops.append(shop)

            print()
            print("=" * 60)
            print("取得結果")
            print("=" * 60)
            print(f"店舗名：{shop.name}")
            print(f"取得件数：{len(shop.coupons)}件")
            print("=" * 60)

            service.export(shop)

        except KeyboardInterrupt:

            print()
            print("処理を中断しました。")
            return

        except Exception as e:

            print()
            print("=" * 60)
            print("スクレイピング中にエラーが発生しました")
            print("=" * 60)
            print(type(e).__name__)
            print(e)
            print("=" * 60)

    # ==========================================================
    # スクレイピング完了
    # ==========================================================

    print()
    print("=" * 60)
    print("スクレイピング処理完了")
    print("=" * 60)

    print(f"取得店舗数：{len(shops)}")

    total_coupons = sum(
        len(shop.coupons)
        for shop in shops
    )

    print(f"総クーポン数：{total_coupons}")

    print("=" * 60)

    # ==========================================================
    # 分析エンジン
    # ==========================================================

    print()
    print("=" * 60)
    print("分析エンジン起動")
    print("=" * 60)

    for shop in shops:

        print()
        print("-" * 60)
        print(f"【分析対象】{shop.name}")
        print("-" * 60)

        try:

            result = analyzer.analyze(shop)

            print_analysis_result(result)

        except Exception as e:

            print()
            print("=" * 60)
            print("分析中にエラーが発生しました")
            print("=" * 60)
            print(type(e).__name__)
            print(e)
            print("=" * 60)

    # ==========================================================
    # 全処理完了
    # ==========================================================

    print()
    print("=" * 60)
    print("全処理完了")
    print("=" * 60)

    print(f"取得店舗数：{len(shops)}")
    print(f"総クーポン数：{total_coupons}")

    print("=" * 60)


if __name__ == "__main__":
    main()