from pathlib import Path

from playwright.sync_api import sync_playwright

from models import Shop
from parser import CouponParser


class HotPepperScraper:

    def scrape(self, url: str) -> Shop:

        # クーポンURLへ変換
        if not url.endswith("/"):
            url += "/"

        coupon_url = url + "coupon/"

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

            html = page.content()

            browser.close()

        # HTML保存
        output_dir = Path("output/html")
        output_dir.mkdir(parents=True, exist_ok=True)

        html_path = output_dir / "page.html"

        with open(
            html_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(html)

        # 店舗名取得
        parser = CouponParser()

        shop = Shop()
        shop.url = coupon_url

        shop.name = parser.parse_shop_name(html)
        shop.coupons = parser.parse(html)

        return shop