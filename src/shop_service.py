from models import Shop
from exporter import CouponExporter


class ShopService:
    """
    HPB Insight のサービス層

    今後

    ・CSV出力
    ・Excel出力
    ・AI分析
    ・競合比較

    をここへ集約する。
    """

    def __init__(self):

        self.exporter = CouponExporter()

    def export(self, shop: Shop):

        return self.exporter.export_csv(shop)

    def total_coupon(self, shop: Shop):

        return len(shop.coupons)

    def print_summary(self, shop: Shop):

        print("")
        print("=" * 60)
        print("取得結果")
        print("=" * 60)
        print(f"店舗名：{shop.name}")
        print(f"取得件数：{len(shop.coupons)}件")
        print("=" * 60)