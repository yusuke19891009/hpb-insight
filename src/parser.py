from bs4 import BeautifulSoup

from models import Coupon


class CouponParser:

    def parse(self, html: str):

        soup = BeautifulSoup(html, "html.parser")

        coupons = []

        order = 1

        # クーポン1件 = <tr>
        rows = soup.select("tr")

        for row in rows:

            # -----------------------------
            # 新規・再来・全員
            # -----------------------------
            label = row.select_one("td[class*=couponLabel]")

            if label is None:
                continue

            coupon = Coupon()

            coupon.order = order

            coupon.target = (
                label.get_text(" ", strip=True)
                .replace("\n", "")
                .replace(" ", "")
            )

            # -----------------------------
            # クーポン情報
            # -----------------------------
            body = row.select_one("td.bgWhite")

            if body is None:
                continue

            # -----------------------------
            # カテゴリ
            # -----------------------------
            icons = body.select("li.couponMenuIcon")

            categories = []

            for icon in icons:
                text = icon.get_text(strip=True)

                if text:
                    categories.append(text)

            coupon.category = " + ".join(categories)

            # -----------------------------
            # クーポン名
            # -----------------------------
            title = body.select_one("p.couponMenuName")

            if title:
                coupon.title = title.get_text(strip=True)

            # -----------------------------
            # 説明
            # -----------------------------
            description = body.select_one("p.couponDescription")

            if description:
                coupon.description = description.get_text(" ", strip=True)

            # -----------------------------
            # 価格
            # -----------------------------
            price = body.select_one("p.couponMenuPrice")

            if price:

                text = (
                    price.get_text()
                    .replace("¥", "")
                    .replace(",", "")
                    .strip()
                )

                try:
                    coupon.price = int(text)
                except:
                    coupon.price = 0

            # -----------------------------
            # 条件
            # -----------------------------
            dts = body.select("dl dt")
            dds = body.select("dl dd")

            conditions = []

            for dt, dd in zip(dts, dds):

                key = dt.get_text(strip=True)
                value = dd.get_text(" ", strip=True)

                conditions.append(f"{key}{value}")

            coupon.conditions = " / ".join(conditions)

            coupons.append(coupon)

            order += 1

        return coupons