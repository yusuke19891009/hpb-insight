from playwright.sync_api import sync_playwright


def open_hotpepper(url):

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        page.goto(url)

        # ページが完全に読み込まれるまで待つ
        page.wait_for_load_state("networkidle")

        # 店舗名取得
        shop_name = page.locator("h1").inner_text()

        print("===================================")
        print("店舗名：", shop_name)
        print("===================================")

        input("Enterキーを押すと終了します...")

        browser.close()

        return shop_name