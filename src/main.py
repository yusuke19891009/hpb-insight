from __future__ import annotations

from scraper import HotPepperScraper
from pricing_analysis import PricingAnalyzer
from area_analysis import AreaCouponAnalyzer
from report_pdf import PDFReportGenerator


def print_separator():
    print("\n" + "=" * 70)


def print_reference_info(data: dict):
    """
    v1.8.0 市場参考価格情報を表示する。
    """

    reference_price = data.get(
        "market_reference_price"
    )

    reference_min = data.get(
        "reference_price_min"
    )

    reference_max = data.get(
        "reference_price_max"
    )

    reference_level = data.get(
        "reference_level",
        "比較不可",
    )

    reference_reason = data.get(
        "reference_reason",
        "",
    )

    print(
        f"市場参考価格: "
        f"{reference_price:,.0f}円"
        if reference_price is not None
        else "市場参考価格: 算出不可"
    )

    if (
        reference_min is not None
        and reference_max is not None
    ):
        print(
            f"参考価格帯: "
            f"{reference_min:,.0f}"
            f"～"
            f"{reference_max:,.0f}円"
        )

    print(
        f"参考度: {reference_level}"
    )

    if reference_reason:
        print(
            f"参考度の理由: {reference_reason}"
        )


def print_price_quality(data: dict):
    """v1.8.2 価格データ品質と営業確認候補を表示する。"""
    quality = data.get("price_quality", {})
    print("\n--- 価格データ品質 ---")
    print(f"品質判定: {quality.get('quality_status', '判定対象外')}")
    print(f"有効価格データ数: {quality.get('valid_price_count', 0)}")

    outlier_count = quality.get("outlier_count", 0)
    print(f"統計的外れ値候補: {outlier_count}件")
    if outlier_count:
        print(f"  低価格候補: {quality.get('low_outlier_count', 0)}件")
        print(f"  高価格候補: {quality.get('high_outlier_count', 0)}件")

    q1, q3 = quality.get("q1"), quality.get("q3")
    iqr = quality.get("iqr")
    lower, upper = quality.get("lower_bound"), quality.get("upper_bound")
    if q1 is not None and q3 is not None and iqr is not None:
        print(f"  店舗全体Q1: {q1:,.0f}円")
        print(f"  店舗全体Q3: {q3:,.0f}円")
        print(f"  店舗全体IQR: {iqr:,.0f}円")
        print(f"  判定下限: {lower:,.0f}円")
        print(f"  判定上限: {upper:,.0f}円")

    outliers = quality.get("outliers", [])
    if outliers:
        print("\n【営業確認候補：店舗全体の統計的外れ値】")
        for i, item in enumerate(outliers, 1):
            print(f"  [{i}] {item.get('price'):,.0f}円 ({item.get('direction', '')})")
            if item.get("coupon_name"): print(f"      クーポン: {item['coupon_name']}")
            if item.get("category"): print(f"      カテゴリ: {item['category']}")
            print(f"      判定: {item.get('reason', '')}")

    category_outliers = quality.get("category_outliers", [])
    print(f"\n【営業確認候補：カテゴリ別統計的外れ値】 {len(category_outliers)}件")
    for i, item in enumerate(category_outliers, 1):
        print(f"  [{i}] {item.get('price'):,.0f}円 ({item.get('direction', '')})")
        if item.get("coupon_name"): print(f"      クーポン: {item['coupon_name']}")
        if item.get("category"): print(f"      カテゴリ: {item['category']}")
        print(f"      判定: {item.get('reason', '')}")

    low_attention = quality.get("low_price_attention", [])
    high_attention = quality.get("high_price_attention", [])
    print(f"\n【営業確認候補：低価格要確認】 {len(low_attention)}件")
    for i, item in enumerate(low_attention, 1):
        print(f"  [{i}] {item.get('price'):,.0f}円")
        if item.get("coupon_name"): print(f"      クーポン: {item['coupon_name']}")
        if item.get("category"): print(f"      カテゴリ: {item['category']}")
        print(f"      判定: {item.get('reason', '要確認')}")

    print(f"\n【営業確認候補：高価格要確認】 {len(high_attention)}件")
    for i, item in enumerate(high_attention, 1):
        print(f"  [{i}] {item.get('price'):,.0f}円")
        if item.get("coupon_name"): print(f"      クーポン: {item['coupon_name']}")
        if item.get("category"): print(f"      カテゴリ: {item['category']}")
        print(f"      判定: {item.get('reason', '要確認')}")

    print("\n--- 判定方法 ---")
    print("  ・統計的外れ値 → 店舗全体IQR × 1.5")
    print("  ・カテゴリ別外れ値 → カテゴリIQR × 1.5")
    print("  ・低価格要確認 → 3,000円以下")
    print("  ・高価格要確認 → 30,000円以上")
    print("  ※要確認・外れ値候補は価格計算から除外しません")

    category_quality = quality.get("category_quality", {})
    skipped = [c for c, info in category_quality.items() if info.get("valid_price_count", 0) < 4]
    if skipped:
        print("\nカテゴリ別IQR判定対象外:")
        print("  " + "、".join(skipped) + "（有効価格4件未満）")

    reason = quality.get("quality_reason", "")
    if reason:
        print(f"\n総合判定理由: {reason}")

    if outliers or category_outliers or low_attention or high_attention:
        print("\n※「営業確認候補」は、価格の統計・閾値から機械的に抽出したものです。")
        print("  クーポン名・価格・カテゴリを確認し、利用条件やメニュー内容を踏まえて営業判断してください。")


def print_category_analysis(
    shop_name: str,
    category_analysis: dict,
):
    print_separator()
    print(
        f"【{shop_name}】カテゴリ別価格分析"
    )

    if not category_analysis:
        print(
            "カテゴリ別価格分析データがありません。"
        )
        return

    for category, data in category_analysis.items():

        print("\n" + "-" * 60)
        print(f"【{category}】")

        print(
            f"自店舗クーポン数: "
            f"{data.get('shop_coupon_count', 0)}"
        )

        shop_average = data.get(
            "shop_average"
        )

        if shop_average is not None:
            print(
                f"自店舗平均価格: "
                f"{shop_average:,.0f}円"
            )

        shop_median = data.get(
            "shop_median"
        )

        if shop_median is not None:
            print(
                f"自店舗中央値: "
                f"{shop_median:,.0f}円"
            )

        comparison_shop_count = data.get(
            "comparison_shop_count",
            0,
        )

        comparison_coupon_count = data.get(
            "comparison_coupon_count",
            0,
        )

        print(
            f"比較対象店舗数: "
            f"{comparison_shop_count}"
        )

        print(
            f"比較対象クーポン数: "
            f"{comparison_coupon_count}"
        )

        comparison_average = data.get(
            "comparison_average"
        )

        if comparison_average is not None:
            print(
                f"比較店舗中央値の平均: "
                f"{comparison_average:,.0f}円"
            )

        comparison_median = data.get(
            "comparison_median"
        )

        if comparison_median is not None:
            print(
                f"比較店舗中央値: "
                f"{comparison_median:,.0f}円"
            )

        difference = data.get(
            "difference"
        )

        if difference is not None:
            sign = (
                "+"
                if difference > 0
                else ""
            )

            print(
                f"比較店舗中央値との差: "
                f"{sign}{difference:,.0f}円"
            )

        ratio = data.get(
            "ratio"
        )

        if ratio is not None:
            print(
                f"価格対比率: "
                f"{ratio:.1f}%"
            )

        print(
            f"価格ポジション: "
            f"{data.get('position', '比較不可')}"
        )

        comparison_method = data.get(
            "comparison_method"
        )

        if comparison_method:
            print(
                f"比較方法: "
                f"{comparison_method}"
            )

        print("\n--- 市場参考価格 ---")

        print_reference_info(
            data
        )


def print_overall_analysis(
    shop_name: str,
    pricing_result: dict,
):
    print_separator()
    print(
        f"【{shop_name}】全体価格分析"
    )

    print(
        f"自店舗価格データ数: "
        f"{pricing_result.get('shop_price_count', 0)}"
    )

    shop_average = pricing_result.get(
        "shop_average"
    )

    if shop_average is not None:
        print(
            f"自店舗平均価格: "
            f"{shop_average:,.0f}円"
        )

    shop_median = pricing_result.get(
        "shop_median"
    )

    if shop_median is not None:
        print(
            f"自店舗中央値: "
            f"{shop_median:,.0f}円"
        )

    comparison_shop_count = pricing_result.get(
        "comparison_shop_count",
        0,
    )

    comparison_coupon_count = pricing_result.get(
        "comparison_coupon_count",
        0,
    )

    print(
        f"比較対象店舗数: "
        f"{comparison_shop_count}"
    )

    print(
        f"比較対象クーポン数: "
        f"{comparison_coupon_count}"
    )

    comparison_average = pricing_result.get(
        "comparison_average"
    )

    if comparison_average is not None:
        print(
            f"比較店舗中央値の平均: "
            f"{comparison_average:,.0f}円"
        )

    comparison_median = pricing_result.get(
        "comparison_median"
    )

    if comparison_median is not None:
        print(
            f"比較店舗中央値: "
            f"{comparison_median:,.0f}円"
        )

    difference = pricing_result.get(
        "difference"
    )

    if difference is not None:
        sign = (
            "+"
            if difference > 0
            else ""
        )

        print(
            f"比較店舗中央値との差: "
            f"{sign}{difference:,.0f}円"
        )

    ratio = pricing_result.get(
        "ratio"
    )

    if ratio is not None:
        print(
            f"価格対比率: "
            f"{ratio:.1f}%"
        )

    print(
        f"価格ポジション: "
        f"{pricing_result.get('position', '比較不可')}"
    )

    print(
        f"比較方法: "
        f"{pricing_result.get('comparison_method', '')}"
    )

    # ---------------------------------------------------------
    # v1.8.1 価格データ品質
    # ---------------------------------------------------------

    print_price_quality(
        pricing_result
    )

    print("\n--- 市場参考価格 ---")

    print_reference_info(
        pricing_result
    )


def main():
    print("=" * 70)
    print("ちゃぴおHPB Toolkit v1.9.1")
    print("クーポン価格分析・市場参考価格・営業確認候補分析・PDFレポート")
    print("=" * 70)

    scraper = HotPepperScraper()

    print("\nHotPepper Beautyの店舗URLを入力してください。")
    print("複数店舗を入力できます。")
    print("入力終了は空Enterです。\n")

    urls = []

    while True:
        url = input("URL: ").strip()
        if not url:
            break
        urls.append(url)

    if not urls:
        print("\nURLが入力されていません。")
        return

    print("\n" + "=" * 70)
    print(f"{len(urls)}店舗のデータ取得を開始します。")
    print("=" * 70)

    shops = []

    for index, url in enumerate(urls, start=1):
        print("\n" + "-" * 70)
        print(f"[{index}/{len(urls)}] 店舗データ取得中...")

        try:
            shop = scraper.scrape(url)

            if shop is None:
                print("店舗データを取得できませんでした。")
                continue

            shops.append(shop)

            print(f"取得完了: {getattr(shop, 'name', '不明')}")
            print(f"クーポン数: {len(getattr(shop, 'coupons', []))}")

        except Exception as e:
            print(f"取得中にエラーが発生しました: {e}")

    if not shops:
        print("\n店舗データを取得できませんでした。")
        return

    # =========================================================
    # エリア分析
    # =========================================================
    try:
        area_analyzer = AreaCouponAnalyzer()
        area_analysis = area_analyzer.analyze(shops)
    except Exception as e:
        print(f"\nエリア分析でエラーが発生しました: {e}")
        return

    # =========================================================
    # 価格分析
    # =========================================================
    pricing_analyzer = PricingAnalyzer()
    analysis_reports = []

    for shop in shops:
        shop_name = getattr(shop, "name", "不明店舗")
        coupons = getattr(shop, "coupons", [])

        print_separator()
        print(f"########## {shop_name} ##########")

        pricing_result = None
        category_analysis = {}

        # -----------------------------------------------------
        # 全体価格分析
        # -----------------------------------------------------
        try:
            pricing_result = pricing_analyzer.analyze_summary(
                shop,
                shops,
            )
            print_overall_analysis(
                shop_name,
                pricing_result,
            )
        except Exception as e:
            print(f"\n全体価格分析エラー: {e}")

        # -----------------------------------------------------
        # カテゴリ別価格分析
        # -----------------------------------------------------
        try:
            category_analysis = pricing_analyzer.analyze_category_summary(
                shop,
                area_analysis,
                shops,
            )
            print_category_analysis(
                shop_name,
                category_analysis,
            )
        except Exception as e:
            print(f"\nカテゴリ別価格分析エラー: {e}")

        if pricing_result is not None:
            analysis_reports.append({
                "shop": shop,
                "shop_name": shop_name,
                "coupon_count": len(coupons),
                "pricing_result": pricing_result,
                "category_analysis": category_analysis,
            })

    # =========================================================
    # PDFレポート生成 v1.9.1
    # =========================================================
    if analysis_reports:
        try:
            pdf_generator = PDFReportGenerator()
            pdf_path = pdf_generator.generate(
                analysis_reports=analysis_reports,
                shop_count=len(shops),
            )

            print_separator()
            print("PDFレポートを生成しました。")
            print(f"保存先: {pdf_path}")
        except Exception as e:
            print_separator()
            print(f"PDFレポート生成エラー: {e}")
            print("分析結果自体は正常に完了しています。")

    print_separator()
    print("分析が完了しました。")


if __name__ == "__main__":
    main()
