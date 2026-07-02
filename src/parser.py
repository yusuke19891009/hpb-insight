from bs4 import BeautifulSoup

from models import Coupon


class CouponParser:

    def parse_shop_name(self, html: str) -> str:
        """店舗名を取得"""

        soup = BeautifulSoup(html, "html.parser")

        h1 = soup.select_one("h1")

        if h1:
            name = h1.get_text(strip=True)

            # 「○○のクーポン・メニュー」→「○○」
            name = name.replace("のクーポン・メニュー", "")

            return name

        return "Unknown"

    def parse(self, html: str):
        """クーポン一覧取得"""

        soup = BeautifulSoup(html, "html.parser")

        coupons = []

        cards = soup.select("td.bgWhite.p12.vaT.pr")

        order = 1

        for card in cards:

            coupon = Coupon()

            coupon.order = order
            order += 1

            # -------------------------
            # 対象（新規・再来・全員）
            # -------------------------

            label = card.find_previous("td", class_="couponLabelCT02")

            if label:

                target = label.get_text(" ", strip=True)
                target = target.replace("\n", "").replace(" ", "")

                if "新規" in target:
                    coupon.target = "新規"

                elif "再来" in target:
                    coupon.target = "再来"

                elif "全員" in target:
                    coupon.target = "全員"

            # -------------------------
            # カテゴリ
            # -------------------------

            icons = card.select(".couponMenuIcon")

            coupon.category = " + ".join(
                icon.get_text(strip=True)
                for icon in icons
            )

            # -------------------------
            # タイトル
            # -------------------------

            title = card.select_one(".couponMenuName")

            if title:
                coupon.title = title.get_text(strip=True)

            # -------------------------
            # 説明
            # -------------------------

            desc = card.select_one(".couponDescription")

            if desc:
                coupon.description = desc.get_text(" ", strip=True)

            # -------------------------
            # 価格
            # -------------------------

            price = card.select_one(".couponMenuPrice")

            if price:
                coupon.price = (
                    price.get_text(strip=True)
                    .replace("¥", "")
                    .replace(",", "")
                )

            # -------------------------
            # 条件
            # -------------------------

            dl = card.select_one(".couponConditionsList")

            if dl:

                items = []

                dts = dl.find_all("dt")
                dds = dl.find_all("dd")

                for dt, dd in zip(dts, dds):

                    key = dt.get_text(strip=True)
                    value = dd.get_text(strip=True)

                    items.append(f"{key}{value}")

                    if key.startswith("来店日条件"):
                        coupon.conditions = value

                    elif key.startswith("対象スタイリスト"):
                        coupon.stylist = value

                    elif key.startswith("その他条件"):
                        coupon.other = value

                # 表示用
                coupon.conditions = " / ".join(items)

            coupons.append(coupon)

        return coupons