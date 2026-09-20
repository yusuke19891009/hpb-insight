from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from playwright.sync_api import sync_playwright

from models import Shop
from parser import CouponParser


class HotPepperScraper:

    def scrape(self, url: str) -> Shop:

        # -----------------------------
        # URL整形
        # -----------------------------
        url = self._normalize_shop_url(url)

        top_url = url
        coupon_url = url + "coupon/"

        parser = CouponParser()

        shop = Shop()
        shop.url = top_url
        shop.coupons = []

        output_dir = Path("output/html")
        output_dir.mkdir(parents=True, exist_ok=True)

        # -----------------------------
        # HTML削除（最新のみ保持）
        # -----------------------------
        for file in output_dir.glob("*.html"):
            try:
                file.unlink()
            except Exception:
                pass

        print("")
        print("=" * 60)
        print("スクレイピング開始")
        print("=" * 60)

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=False
            )

            page = browser.new_page()

            # -----------------------------
            # TOPページ
            # -----------------------------
            print("")
            print("【TOPページ取得】")
            print(top_url)

            page.goto(
                top_url,
                wait_until="networkidle",
                timeout=60000
            )

            top_html = page.content()

            (output_dir / "top.html").write_text(
                top_html,
                encoding="utf-8"
            )

            shop.name = parser.parse_shop_name(top_html)

            # -----------------------------
            # クーポンページ
            # -----------------------------
            page_no = 1

            # 同一ページの無限取得防止
            seen_page_signatures = set()

            while True:

                if page_no == 1:
                    page_url = coupon_url
                else:
                    page_url = f"{coupon_url}PN{page_no}.html"

                print("")
                print("-" * 60)
                print(f"Page {page_no}")
                print(page_url)

                page.goto(
                    page_url,
                    wait_until="networkidle",
                    timeout=60000
                )

                html = page.content()

                # -----------------------------
                # 同一ページ検知
                # -----------------------------
                page_signature = self._create_page_signature(html)

                if page_signature in seen_page_signatures:
                    print("同一ページを検出しました。")
                    print("無限取得防止のため処理を終了します。")
                    break

                seen_page_signatures.add(page_signature)

                (output_dir / f"page{page_no}.html").write_text(
                    html,
                    encoding="utf-8"
                )

                coupons = parser.parse(html)

                count = len(coupons)

                print(f"取得件数：{count}件")

                # -----------------------------
                # 0件なら最終ページ
                # -----------------------------
                if count == 0:
                    print("最終ページ到達")
                    break

                shop.coupons.extend(coupons)

                page_no += 1

            browser.close()

        # -----------------------------
        # 掲載順再設定
        # -----------------------------
        for i, coupon in enumerate(shop.coupons, start=1):
            coupon.order = i

        print("")
        print("=" * 60)
        print("スクレイピング完了")
        print("=" * 60)
        print(f"店舗名：{shop.name}")
        print(f"取得件数：{len(shop.coupons)}件")
        print("=" * 60)

        return shop

    # =========================================================
    # URL正規化
    # =========================================================

    def _normalize_shop_url(self, url: str) -> str:
        """
        HotPepperの店舗URLを正規化する。

        例:

        入力:
        https://beauty.hotpepper.jp/slnH000797293/?cstt=5

        ↓

        https://beauty.hotpepper.jp/slnH000797293/

        クエリパラメータやフラグメントは削除する。
        """

        url = url.strip()

        if not url:
            raise ValueError("URLが空です。")

        parsed = urlsplit(url)

        if not parsed.scheme or not parsed.netloc:
            raise ValueError(
                f"URLの形式が正しくありません：{url}"
            )

        path = parsed.path

        # /coupon/ 以降が入力されていた場合も
        # 店舗トップURLへ戻す
        coupon_index = path.find("/coupon")

        if coupon_index != -1:
            path = path[:coupon_index]

        if not path.endswith("/"):
            path += "/"

        normalized_url = urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                path,
                "",
                "",
            )
        )

        return normalized_url

    # =========================================================
    # ページ重複検知
    # =========================================================

    def _create_page_signature(self, html: str) -> str:
        """
        ページ内容から簡易的な重複判定用シグネチャを作る。

        同じHTMLが何度も返ってきた場合、
        無限ページングを防止する。
        """

        import hashlib

        return hashlib.sha256(
            html.encode("utf-8")
        ).hexdigest()