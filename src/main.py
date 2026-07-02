from scraper import HotPepperScraper
from exporter import CouponExporter


def main():

    print("=" * 60)
    print("HPB Insight")
    print("v0.2.0")
    print("=" * 60)

    url = input("HotPepperのURLを入力してください：").strip()

    if not url:
        print("URLが入力されていません。")
        return

    # ------------------------
    # スクレイピング
    # ------------------------

    scraper = HotPepperScraper()

    shop = scraper.scrape(url)

    print("")
    print("=" * 60)
    print("取得結果")
    print("=" * 60)

    print(f"店舗名：{shop.name}")
    print(f"取得件数：{len(shop.coupons)}件")

    # ------------------------
    # CSV出力
    # ------------------------

    exporter = CouponExporter()

    exporter.export_csv(shop)

    print("")
    print("=" * 60)
    print("完了！")
    print("=" * 60)


if __name__ == "__main__":
    main()