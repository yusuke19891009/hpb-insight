import csv
from datetime import datetime
from pathlib import Path

from models import Shop


class CouponExporter:

    def export_csv(self, shop: Shop):

        # -----------------------------
        # 出力フォルダ
        # -----------------------------
        output_dir = Path("output/csv")
        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # -----------------------------
        # ファイル名
        # -----------------------------
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        safe_name = (
            shop.name
            .replace("/", "／")
            .replace("\\", "＼")
            .replace(":", "：")
            .replace("*", "")
            .replace("?", "")
            .replace('"', "")
            .replace("<", "")
            .replace(">", "")
            .replace("|", "")
        )

        filename = (
            output_dir /
            f"{timestamp}_{safe_name}.csv"
        )

        # -----------------------------
        # CSV出力
        # -----------------------------
        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "店舗名",
                "店舗URL",
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

                writer.writerow([

                    shop.name,

                    shop.url,

                    coupon.order,

                    coupon.target,

                    coupon.category,

                    coupon.title,

                    coupon.price,

                    coupon.conditions,

                    coupon.stylist,

                    coupon.other,

                    coupon.description
                ])

        # -----------------------------
        # 完了ログ
        # -----------------------------
        print("")
        print("=" * 60)
        print("CSV保存完了")
        print("=" * 60)
        print(filename)
        print("=" * 60)

        return filename