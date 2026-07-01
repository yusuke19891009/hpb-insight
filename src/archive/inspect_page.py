from playwright.sync_api import sync_playwright

URL = "https://beauty.hotpepper.jp/slnH000680143/"


with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    page.goto(URL)

    page.wait_for_load_state("networkidle")

    with open("output/page.html", "w", encoding="utf-8") as f:
        f.write(page.content())

    print("保存完了！")

    input("Enterで終了")

    browser.close()