from scraper import HotPepperScraper


def main():

    print("=" * 60)
    print("HPB Insight")
    print("Sprint2")
    print("=" * 60)

    url = input("HotPepperのURLを入力してください：\n").strip()

    if not url:

        print("URLが入力されていません。")
        return

    scraper = HotPepperScraper()

    coupons = scraper.scrape(url)

    print("")
    print("=" * 60)
    print("取得完了")
    print(f"{len(coupons)}件取得しました。")
    print("=" * 60)


if __name__ == "__main__":
    main()