from scraper import HotPepperScraper
from shop_service import ShopService


def main():

    print("=" * 60)
    print("HPB Insight")
    print("v1.2.0")
    print("=" * 60)
    print("HotPepper URLを入力してください。")
    print("複数取得する場合は空行で終了します。")
    print("=" * 60)

    urls = []

    while True:

        url = input("> ").strip()

        if url == "":
            break

        if "beauty.hotpepper.jp" not in url:
            print("HotPepper BeautyのURLを入力してください。")
            continue

        urls.append(url)

    if len(urls) == 0:
        print("URLが入力されませんでした。")
        return

    scraper = HotPepperScraper()
    service = ShopService()

    total_coupon = 0

    for index, url in enumerate(urls, start=1):

        print("")
        print("=" * 60)
        print(f"{index} / {len(urls)} 店舗取得開始")
        print("=" * 60)

        try:

            shop = scraper.scrape(url)

            service.print_summary(shop)

            service.export(shop)

            total_coupon += len(shop.coupons)

        except KeyboardInterrupt:

            print("")
            print("処理を中断しました。")
            return

        except Exception as e:

            print("")
            print("=" * 60)
            print("取得失敗")
            print("=" * 60)
            print(e)

    print("")
    print("=" * 60)
    print("全処理完了")
    print("=" * 60)
    print(f"取得店舗数：{len(urls)}")
    print(f"総クーポン数：{total_coupon}")
    print("=" * 60)


if __name__ == "__main__":
    main()