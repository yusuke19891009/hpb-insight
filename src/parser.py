from bs4 import BeautifulSoup

from models import Coupon


class CouponParser:

    def parse_shop_name(self, html: str) -> str:
        """
        Hot Pepper Beauty掲載ページの店舗名を取得する。

        取得方針：
        1. h1は検索結果用名称なので「候補」として扱う
        2. h1の直後〜近傍にある、同一店舗URLへのリンク名を
           「掲載店舗名」として優先する
        3. 近傍で取得できない場合はh1へフォールバック

        これにより、
          アース 甲府昭和店(EARTH)
          → HAIR & MAKE EARTH 甲府昭和店

          ワンズ 徳行店(ONE'S)
          → ONE'S 徳行店

          ニュイ(NUI)
          → NUI〖ニュイ〗
        のようなHPB独自の表記を優先する。
        """

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        # -----------------------------------------------------
        # h1（検索結果用店舗名）
        # -----------------------------------------------------
        h1 = soup.select_one("h1")

        h1_name = ""

        if h1:
            h1_name = h1.get_text(
                " ",
                strip=True,
            )

            h1_name = h1_name.replace(
                "のクーポン・メニュー",
                "",
            ).strip()

        # -----------------------------------------------------
        # h1の後方にある「同一店舗ページへのリンク」を探す
        #
        # HPBでは、
        #   h1 = 検索結果用名称
        #   その近傍 = 掲載店舗名
        #
        # という構造があるため、ページ全体から無差別に
        # 候補を拾わず、DOM上の距離を重視する。
        # -----------------------------------------------------
        if h1:

            # h1自身を起点に、後続要素をDOM順で調べる
            elements_after_h1 = []

            for element in h1.find_all_next():
                elements_after_h1.append(element)

                # 店舗ヘッダーは通常かなり早い位置にある。
                # 深追いしてクーポンタイトルを拾わない。
                if len(elements_after_h1) >= 250:
                    break

            # 同一店舗URLへのリンク候補
            link_candidates = []

            for element in elements_after_h1:

                if element.name != "a":
                    continue

                href = element.get(
                    "href",
                    "",
                )

                if not href:
                    continue

                if "/slnH" not in href:
                    continue

                text = element.get_text(
                    " ",
                    strip=True,
                )

                if not text:
                    continue

                # 明らかな汎用リンクを除外
                excluded = (
                    "クーポン",
                    "メニュー",
                    "スタイリスト",
                    "スタイル",
                    "ブログ",
                    "地図",
                    "口コミ",
                    "サロン情報",
                    "空席確認",
                    "予約する",
                    "ブックマーク",
                )

                if any(
                    word in text
                    for word in excluded
                ):
                    continue

                # クーポン名を拾わないため、
                # 長すぎるテキストは除外。
                if len(text) > 80:
                    continue

                link_candidates.append(
                    text
                )

            # 重複除去しつつDOM順を維持
            unique_candidates = []

            for candidate in link_candidates:
                if candidate in unique_candidates:
                    continue

                unique_candidates.append(
                    candidate
                )

            # 最初の候補を採用。
            # これが「店舗ヘッダーの掲載名称」に最も近い。
            if unique_candidates:
                return unique_candidates[0]

        # -----------------------------------------------------
        # 予備：HPBで使われる店舗名系class
        # -----------------------------------------------------
        selectors = (
            ".slnName",
            ".salonName",
            "[class*='slnName']",
            "[class*='salonName']",
            "[itemprop='name']",
        )

        for selector in selectors:

            node = soup.select_one(
                selector
            )

            if not node:
                continue

            name = node.get_text(
                " ",
                strip=True,
            )

            if not name:
                continue

            if len(name) > 80:
                continue

            if any(
                word in name
                for word in (
                    "クーポン",
                    "メニュー",
                    "スタイリスト",
                )
            ):
                continue

            return name

        # -----------------------------------------------------
        # 最終フォールバック：h1
        # -----------------------------------------------------
        if h1_name:
            return h1_name

        return "Unknown"

    def parse(self, html: str):
        """クーポン一覧取得"""

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        coupons = []

        cards = soup.select(
            "td.bgWhite.p12.vaT.pr"
        )

        order = 1

        for card in cards:

            coupon = Coupon()

            coupon.order = order
            order += 1

            # -------------------------
            # 対象（新規・再来・全員）
            # -------------------------

            label = card.find_previous(
                "td",
                class_="couponLabelCT02",
            )

            if label:

                target = label.get_text(
                    " ",
                    strip=True,
                )

                target = (
                    target
                    .replace("\n", "")
                    .replace(" ", "")
                )

                if "新規" in target:
                    coupon.target = "新規"

                elif "再来" in target:
                    coupon.target = "再来"

                elif "全員" in target:
                    coupon.target = "全員"

            # -------------------------
            # カテゴリ
            # -------------------------

            icons = card.select(
                ".couponMenuIcon"
            )

            coupon.category = " + ".join(
                icon.get_text(
                    strip=True
                )
                for icon in icons
            )

            # -------------------------
            # タイトル
            # -------------------------

            title = card.select_one(
                ".couponMenuName"
            )

            if title:

                coupon.title = title.get_text(
                    strip=True
                )

            # -------------------------
            # 説明
            # -------------------------

            desc = card.select_one(
                ".couponDescription"
            )

            if desc:

                coupon.description = (
                    desc.get_text(
                        " ",
                        strip=True,
                    )
                )

            # -------------------------
            # 価格
            # -------------------------

            price = card.select_one(
                ".couponMenuPrice"
            )

            if price:

                coupon.price = (
                    price.get_text(
                        strip=True
                    )
                    .replace("¥", "")
                    .replace(",", "")
                )

            # -------------------------
            # 条件
            # -------------------------

            dl = card.select_one(
                ".couponConditionsList"
            )

            if dl:

                items = []

                dts = dl.find_all("dt")
                dds = dl.find_all("dd")

                for dt, dd in zip(
                    dts,
                    dds,
                ):

                    key = dt.get_text(
                        strip=True
                    )

                    value = dd.get_text(
                        strip=True
                    )

                    items.append(
                        f"{key}{value}"
                    )

                    if key.startswith(
                        "来店日条件"
                    ):
                        coupon.conditions = value

                    elif key.startswith(
                        "対象スタイリスト"
                    ):
                        coupon.stylist = value

                    elif key.startswith(
                        "その他条件"
                    ):
                        coupon.other = value

                # 表示用
                coupon.conditions = (
                    " / ".join(items)
                )

            coupons.append(coupon)

        return coupons
