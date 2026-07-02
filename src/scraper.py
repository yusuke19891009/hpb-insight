from pathlib import Path

from playwright.sync_api import sync_playwright

from models import Shop
from parser import CouponParser


class HotPepperScraper:

    def scrape(self, url: str) -> Shop:

        # -----------------------------
        # URL整形
        # -----------------------------
        if not url.endswith("/"):
            url += "/"

        top_url = url
        coupon_url = url + "coupon/"

        parser = CouponParser()

        shop = Shop()
        shop.url = top_url
        shop.coupons = []

        output_dir = Path("output/html")
        output_dir.mkdir(parents=True, exist_ok=True)

        # ============================================
        # 前回HTML削除（最新のみ保持）
        # ============================================

        for file in output_dir.glob("*.html"):
            file.unlink()

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=False
            )

            page = browser.new_page()

            # ============================================
            # TOPページ取得
            # ============================================

            print("")
            print("=" * 60)
            print("TOPページ取得")
            print(top_url)
            print("=" * 60)

            page.goto(
                top_url,
                wait_until="networkidle"
            )

            top_html = page.content()

            (output_dir / "top.html").write_text(
                top_html,
                encoding="utf-8"
            )

            shop.name = parser.parse_shop_name(top_html)

            # ============================================
            # クーポンページ取得
            # ============================================

            page_no = 1

            while True:

                if page_no == 1:
                    page_url = coupon_url
                else:
                    page_url = f"{coupon_url}PN{page_no}.html"

                print("")
                print("=" * 60)
                print(f"Page {page_no}")
                print(page_url)
                print("=" * 60)

                page.goto(
                    page_url,
                    wait_until="networkidle"
                )

                html = page.content()

                (output_dir / f"page{page_no}.html").write_text(
                    html,
                    encoding="utf-8"
                )

                coupons = parser.parse(html)

                print(f"取得件数 : {len(coupons)}")

                if len(coupons) == 0:

                    print("最終ページ到達")
                    break

                shop.coupons.extend(coupons)

                page_no += 1

            browser.close()

        # ============================================
        # 掲載順振り直し
        # ============================================

        for i, coupon in enumerate(shop.coupons, start=1):

            coupon.order = i

        print("")
        print("=" * 60)
        print("取得完了")
        print(f"店舗名 : {shop.name}")
        print(f"取得件数 : {len(shop.coupons)}")
        print("=" * 60)

        return shop