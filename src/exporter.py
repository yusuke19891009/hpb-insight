import csv
from pathlib import Path
from datetime import datetime

from models import Shop


class CouponExporter:
    """クーポンCSV出力"""

    def export_csv(self, shop: Shop):

        output_dir = Path("output/csv")
        output_dir.mkdir(exist_ok=True)

        now = datetime.now().strftime("%Y%m%d_%H%M%S")

        shop_name = shop.name if shop.name else "shop"

        # Windowsで使えない文字を除去
        for c in r'\/:*?"<>|':
            shop_name = shop_name.replace(c, "")

        filename = output_dir / f"{shop_name}_{now}.csv"

        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "掲載順",
                "対象",
                "カテゴリ",
                "クーポン名",
                "価格",
                "来店条件",
                "対象スタイリスト",
                "その他条件",
                "説明"
            ])

            for coupon in shop.coupons:

                conditions = coupon.conditions

                visit = ""
                stylist = ""
                other = ""

                for item in conditions.split(" / "):

                    if item.startswith("来店日条件"):
                        visit = item.replace("来店日条件：", "")

                    elif item.startswith("対象スタイリスト"):
                        stylist = item.replace("対象スタイリスト：", "")

                    elif item.startswith("その他条件"):
                        other = item.replace("その他条件：", "")

                writer.writerow([
                    coupon.order,
                    coupon.target,
                    coupon.category,
                    coupon.title,
                    coupon.price,
                    visit,
                    stylist,
                    other,
                    coupon.description
                ])

        print("")
        print("=" * 60)
        print("CSV保存完了")
        print(filename)
        print("=" * 60)

        return filename