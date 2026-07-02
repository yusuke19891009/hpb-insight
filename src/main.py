from scraper import HotPepperScraper
from exporter import CouponExporter


def main():

    print("=" * 60)
    print("HPB Insight")
    print("v1.0.0")
    print("=" * 60)

    url = input("HotPepperのURLを入力してください：").strip()

    if url == "":
        print("URLが入力されていません。")
        return

    if "beauty.hotpepper.jp" not in url:
        print("HotPepper BeautyのURLを入力してください。")
        return

    try:

        scraper = HotPepperScraper()

        shop = scraper.scrape(url)

        print("")
        print("=" * 60)
        print("取得結果")
        print("=" * 60)

        print(f"店舗名：{shop.name}")
        print(f"取得件数：{len(shop.coupons)}件")

        exporter = CouponExporter()
        exporter.export_csv(shop)

        print("")
        print("=" * 60)
        print("完了！")
        print("=" * 60)

    except Exception as e:

        print("")
        print("=" * 60)
        print("エラーが発生しました")
        print("=" * 60)

        print(e)


if __name__ == "__main__":
    main()