from playwright.sync_api import sync_playwright

from parser import CouponParser


class HotPepperScraper:

    def scrape(self, url: str):

        # TOPページURL → クーポンページURL
        coupon_url = url.rstrip("/") + "/coupon/"

        print("")
        print("=" * 60)
        print("クーポンページ")
        print(coupon_url)
        print("=" * 60)

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=False
            )

            page = browser.new_page()

            print("クーポンページを開いています...")

            page.goto(
                coupon_url,
                wait_until="networkidle"
            )

            # JavaScript描画待ち
            page.wait_for_timeout(3000)

            html = page.content()

            # デバッグ用HTML保存
            with open(
                "output/page.html",
                "w",
                encoding="utf-8"
            ) as f:
                f.write(html)

            browser.close()

        parser = CouponParser()

        coupons = parser.parse(html)

        print("")
        print("=" * 60)
        print("取得結果")
        print("=" * 60)

        for coupon in coupons:

            print(f"[{coupon.order}] {coupon.target}")
            print(coupon.category)
            print(coupon.title)
            print(coupon.price)
            print(coupon.conditions)
            print("-" * 60)

        return coupons