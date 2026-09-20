from scraper import HotPepperScraper
from exporter import CouponExporter
from analysis import CouponAnalyzer


class ShopService:
    """
    店舗取得・分析・出力をまとめて管理するサービス。

    処理の流れ：

        URL
        ↓
        Scraper
        ↓
        Shop
        ↓
        Analyzer
        ↓
        分析結果表示
        ↓
        Exporter
        ↓
        CSV
    """

    def __init__(self):
        self.scraper = HotPepperScraper()
        self.exporter = CouponExporter()
        self.analyzer = CouponAnalyzer()

    # =========================================================
    # 店舗取得
    # =========================================================

    def scrape(self, url: str):
        """
        URLから店舗情報・クーポン情報を取得する。
        """

        return self.scraper.scrape(url)

    # =========================================================
    # 店舗概要表示
    # =========================================================

    def print_summary(self, shop):
        """
        店舗の基本情報を表示する。
        """

        print("")
        print("=" * 60)
        print("取得結果")
        print("=" * 60)

        print(f"店舗名：{shop.name}")
        print(f"取得件数：{len(shop.coupons)}件")

        print("=" * 60)

    # =========================================================
    # 分析
    # =========================================================

    def analyze(self, shop):
        """
        店舗のクーポンデータを分析する。
        """

        result = self.analyzer.analyze(shop)

        self._print_analysis(result)

        return result

    # =========================================================
    # 分析結果表示
    # =========================================================

    def _print_analysis(self, result):
        """
        分析結果をターミナルへ表示する。
        """

        print("")
        print("=" * 60)
        print("クーポン分析")
        print("=" * 60)

        print(f"店舗名：{result['shop_name']}")
        print(f"総クーポン数：{result['coupon_count']}件")

        # -----------------------------------------------------
        # 対象別分析
        # -----------------------------------------------------

        print("")
        print("【対象別件数】")

        target_count = result["target"]["count"]

        if target_count:
            for target, count in target_count.items():
                print(f"{target}：{count}件")
        else:
            print("データなし")

        print("")
        print("【対象別平均価格】")

        target_average = result["target"]["average_price"]

        if target_average:
            for target, average in target_average.items():

                if average is None:
                    print(f"{target}：データなし")
                else:
                    print(f"{target}：{average:,}円")
        else:
            print("データなし")

        # -----------------------------------------------------
        # カテゴリ分析
        # -----------------------------------------------------

        print("")
        print("【カテゴリ別件数】")

        category_count = result["category"]["count"]

        if category_count:
            for category, count in category_count.items():
                print(f"{category}：{count}件")
        else:
            print("データなし")

        print("")
        print("【カテゴリ別平均価格】")

        category_average = result["category"]["average_price"]

        if category_average:
            for category, average in category_average.items():

                if average is None:
                    print(f"{category}：データなし")
                else:
                    print(f"{category}：{average:,}円")
        else:
            print("データなし")

        # -----------------------------------------------------
        # 全体価格分析
        # -----------------------------------------------------

        price = result["price"]

        print("")
        print("【価格分析】")

        if price["average"] is None:
            print("平均価格：データなし")
            print("最低価格：データなし")
            print("最高価格：データなし")
        else:
            print(f"平均価格：{price['average']:,}円")
            print(f"最低価格：{price['minimum']:,}円")
            print(f"最高価格：{price['maximum']:,}円")

        print(f"価格取得件数：{price['count']}件")

        # -----------------------------------------------------
        # 掲載順位
        # -----------------------------------------------------

        order = result["order"]

        print("")
        print("【掲載順位】")

        if order["first"] is None:
            print("掲載順位データなし")
        else:
            print(f"最上位：{order['first']}位")
            print(f"最下位：{order['last']}位")

        print("")
        print("=" * 60)

    # =========================================================
    # CSV出力
    # =========================================================

    def export(self, shop):
        """
        既存のCSV出力処理を実行する。
        """

        return self.exporter.export_csv(shop)