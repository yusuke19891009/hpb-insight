from scraper import HotPepperScraper
from shop_service import ShopService


def main():

    print("=" * 60)
    print("HPB Insight")
    print("v1.1.0")
    print("=" * 60)

    url = input("HotPepperのURLを入力してください：").strip()

    if not url:
        print("URLが入力されていません。")
        return

    if "beauty.hotpepper.jp" not in url:
        print("HotPepper BeautyのURLを入力してください。")
        return

    try:

        scraper = HotPepperScraper()
        shop = scraper.scrape(url)

        service = ShopService()

        service.print_summary(shop)

        service.export(shop)

        print("")
        print("=" * 60)
        print("処理完了")
        print("=" * 60)

    except KeyboardInterrupt:

        print("")
        print("処理を中断しました。")

    except Exception as e:

        print("")
        print("=" * 60)
        print("エラーが発生しました")
        print("=" * 60)
        print(type(e).__name__)
        print(e)


if __name__ == "__main__":
    main()