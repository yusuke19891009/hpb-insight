from __future__ import annotations

from datetime import datetime
from pathlib import Path
from statistics import median

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional

from scraper import HotPepperScraper
from pricing_analysis import PricingAnalyzer
from report_pdf import generate_pdf_report


VERSION = "v2.0.7"


def print_separator():
    print("\n" + "=" * 70)


def get_valid_price(coupon: Any) -> Optional[int]:
    price = getattr(coupon, "price", None)

    if price is None:
        return None

    if isinstance(price, str):
        value = (
            price.replace(",", "")
            .replace("円", "")
            .replace("￥", "")
            .replace("¥", "")
            .strip()
        )

        if not value:
            return None

        try:
            price = int(float(value))
        except ValueError:
            return None

    try:
        price = int(price)
    except (TypeError, ValueError):
        return None

    return price if price > 0 else None


def normalize_category(analyzer: PricingAnalyzer, category: Any) -> str:
    """
    PricingAnalyzer v1.8.x のカテゴリ正規化ロジックを利用する。
    フォールバックとして簡易正規化も行う。
    """
    try:
        return analyzer._normalize_category(category)
    except Exception:
        value = str(category or "").strip()
        if not value:
            return ""

        parts = []
        for part in value.split("+"):
            part = part.strip()
            if part and part not in parts:
                parts.append(part)

        parts = [p for p in parts if p != "その他"] or parts
        return " + ".join(parts)


def get_shop_prices(shop: Any) -> List[int]:
    return [
        price
        for coupon in getattr(shop, "coupons", [])
        for price in [get_valid_price(coupon)]
        if price is not None
    ]


def get_shop_summary(shop: Any) -> Dict[str, Any]:
    prices = get_shop_prices(shop)

    return {
        "name": getattr(shop, "name", "不明店舗"),
        "coupon_count": len(getattr(shop, "coupons", [])),
        "valid_price_count": len(prices),
        "average": round(sum(prices) / len(prices)) if prices else None,
        "median": float(median(prices)) if prices else None,
        "min": min(prices) if prices else None,
        "max": max(prices) if prices else None,
    }


def get_category_shop_summary(
    analyzer: PricingAnalyzer,
    shop: Any,
) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}

    for coupon in getattr(shop, "coupons", []):
        category = normalize_category(
            analyzer,
            getattr(coupon, "category", ""),
        )

        price = get_valid_price(coupon)

        if not category or price is None:
            continue

        result.setdefault(
            category,
            {"prices": [], "coupon_count": 0},
        )
        result[category]["prices"].append(price)
        result[category]["coupon_count"] += 1

    for category, data in result.items():
        prices = data["prices"]
        data["average"] = round(sum(prices) / len(prices))
        data["median"] = float(median(prices))
        data["min"] = min(prices)
        data["max"] = max(prices)
        del data["prices"]

    return result


def build_comparison_shop_rows(
    analyzer: PricingAnalyzer,
    comparison_shops: List[Any],
) -> List[Dict[str, Any]]:
    rows = []

    for shop in comparison_shops:
        summary = get_shop_summary(shop)
        category_summary = get_category_shop_summary(
            analyzer,
            shop,
        )

        rows.append(
            {
                **summary,
                "category_count": len(category_summary),
                "categories": category_summary,
            }
        )

    return rows


def build_category_rows(
    analyzer: PricingAnalyzer,
    primary_shop: Any,
    comparison_shops: List[Any],
    category_analysis: Dict[str, Any],
) -> List[Dict[str, Any]]:
    comparison_category_maps = [
        get_category_shop_summary(analyzer, shop)
        for shop in comparison_shops
    ]

    rows = []

    for category, data in category_analysis.items():
        comparison_values = []

        for shop, shop_map in zip(
            comparison_shops,
            comparison_category_maps,
        ):
            item = shop_map.get(category)

            if item and item.get("median") is not None:
                comparison_values.append(
                    {
                        "shop_name": getattr(
                            shop,
                            "name",
                            "不明店舗",
                        ),
                        "coupon_count": item["coupon_count"],
                        "median": item["median"],
                        "average": item["average"],
                    }
                )

        rows.append(
            {
                "category": category,
                "primary_coupon_count": data.get(
                    "shop_coupon_count",
                    0,
                ),
                "primary_average": data.get(
                    "shop_average"
                ),
                "primary_median": data.get(
                    "shop_median"
                ),
                "comparison_shop_count": data.get(
                    "comparison_shop_count",
                    0,
                ),
                "comparison_coupon_count": data.get(
                    "comparison_coupon_count",
                    0,
                ),
                "market_reference_price": data.get(
                    "market_reference_price"
                ),
                "reference_price_min": data.get(
                    "reference_price_min"
                ),
                "reference_price_max": data.get(
                    "reference_price_max"
                ),
                "position": data.get(
                    "position",
                    "比較不可",
                ),
                "reference_level": data.get(
                    "reference_level",
                    "比較不可",
                ),
                "difference": data.get("difference"),
                "ratio": data.get("ratio"),
                "comparison_stores": comparison_values,
            }
        )

    return rows


def extract_review_candidates(
    pricing_result: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    quality = pricing_result.get("price_quality", {})

    return {
        "outliers": quality.get("outliers", []),
        "category_outliers": quality.get(
            "category_outliers",
            [],
        ),
        "low_price_attention": quality.get(
            "low_price_attention",
            [],
        ),
        "high_price_attention": quality.get(
            "high_price_attention",
            [],
        ),
    }


def print_primary_summary(
    primary_shop: Any,
    pricing_result: Dict[str, Any],
):
    name = getattr(primary_shop, "name", "不明店舗")

    print_separator()
    print(f"【分析対象店舗】{name}")
    print("-" * 70)

    print(
        f"取得クーポン数: "
        f"{pricing_result.get('shop_coupon_count', len(getattr(primary_shop, 'coupons', [])))}件"
    )
    print(
        f"有効価格データ数: "
        f"{pricing_result.get('shop_price_count', 0)}件"
    )

    if pricing_result.get("shop_average") is not None:
        print(
            f"自店舗平均価格: "
            f"{pricing_result['shop_average']:,.0f}円"
        )

    if pricing_result.get("shop_median") is not None:
        print(
            f"自店舗中央値: "
            f"{pricing_result['shop_median']:,.0f}円"
        )

    comparison_median = pricing_result.get(
        "comparison_median"
    )

    if comparison_median is not None:
        print(
            f"市場参考価格: "
            f"{comparison_median:,.0f}円"
        )

    print(
        f"価格ポジション: "
        f"{pricing_result.get('position', '比較不可')}"
    )

    ratio = pricing_result.get("ratio")
    if ratio is not None:
        print(f"価格対比率: {ratio:.1f}%")

    reference_level = pricing_result.get(
        "reference_level",
        "比較不可",
    )
    print(f"参考度: {reference_level}")


def print_comparison_summary(
    comparison_shops: List[Any],
):
    print_separator()
    print("【比較対象店舗】")
    print("-" * 70)

    if not comparison_shops:
        print("比較対象店舗はありません。")
        return

    for index, shop in enumerate(
        comparison_shops,
        start=1,
    ):
        summary = get_shop_summary(shop)

        print(
            f"{index}. {summary['name']} / "
            f"クーポン{summary['coupon_count']}件 / "
            f"中央値 "
            f"{summary['median']:,.0f}円"
            if summary["median"] is not None
            else (
                f"{index}. {summary['name']} / "
                f"クーポン{summary['coupon_count']}件 / "
                "有効価格なし"
            )
        )


def main():
    print("=" * 70)
    print(f"ちゃぴおHPB Toolkit {VERSION}")
    print(
        "自店舗を主役にしたクーポン価格分析・市場参考価格・"
        "営業確認候補・PDFレポート"
    )
    print("=" * 70)

    scraper = HotPepperScraper()
    analyzer = PricingAnalyzer()

    print("\n【1】分析対象となる自店舗URLを入力してください。")
    primary_url = input("自店舗URL: ").strip()

    if not primary_url:
        print("\n自店舗URLが入力されていません。")
        return

    print(
        "\n【2】比較対象店舗URLを入力してください。"
    )
    print(
        "複数入力できます。比較店舗の入力終了は空Enterです。\n"
    )

    comparison_urls: List[str] = []

    while True:
        url = input("比較店舗URL: ").strip()

        if not url:
            break

        comparison_urls.append(url)

    print_separator()
    print("店舗データの取得を開始します。")
    print("=" * 70)

    primary_shop = None
    comparison_shops: List[Any] = []

    # ---------------------------------------------------------
    # 自店舗
    # ---------------------------------------------------------
    print("\n[自店舗] データ取得中...")

    try:
        primary_shop = scraper.scrape(primary_url)
    except Exception as e:
        print(f"自店舗の取得に失敗しました: {e}")
        return

    if primary_shop is None:
        print("自店舗データを取得できませんでした。")
        return

    print(
        f"取得完了: {getattr(primary_shop, 'name', '不明店舗')} / "
        f"クーポン{len(getattr(primary_shop, 'coupons', []))}件"
    )

    # ---------------------------------------------------------
    # 比較店舗
    # ---------------------------------------------------------
    for index, url in enumerate(
        comparison_urls,
        start=1,
    ):
        print(
            f"\n[比較店舗 {index}/{len(comparison_urls)}] "
            "データ取得中..."
        )

        try:
            shop = scraper.scrape(url)

            if shop is None:
                print("取得できなかったためスキップします。")
                continue

            comparison_shops.append(shop)

            print(
                f"取得完了: {getattr(shop, 'name', '不明店舗')} / "
                f"クーポン{len(getattr(shop, 'coupons', []))}件"
            )

        except Exception as e:
            print(f"取得に失敗しました: {e}")

    # ---------------------------------------------------------
    # 価格分析
    # ---------------------------------------------------------
    print_separator()
    print("自店舗を主対象として価格分析を実行します。")
    print("=" * 70)

    try:
        pricing_result = analyzer.analyze_summary(
            primary_shop,
            [primary_shop] + comparison_shops,
        )
    except Exception as e:
        print(f"\n全体価格分析でエラーが発生しました: {e}")
        return

    try:
        category_analysis = analyzer.analyze_category_summary(
            primary_shop,
            {},
            [primary_shop] + comparison_shops,
        )
    except Exception as e:
        print(f"\nカテゴリ別価格分析でエラーが発生しました: {e}")
        category_analysis = {}

    primary_summary = get_shop_summary(primary_shop)
    comparison_rows = build_comparison_shop_rows(
        analyzer,
        comparison_shops,
    )

    category_rows = build_category_rows(
        analyzer,
        primary_shop,
        comparison_shops,
        category_analysis,
    )

    review_candidates = extract_review_candidates(
        pricing_result
    )

    print_primary_summary(
        primary_shop,
        pricing_result,
    )

    print_comparison_summary(
        comparison_shops
    )

    print_separator()
    print("【カテゴリ別比較】")
    print("-" * 70)

    for row in category_rows:
        reference = row.get(
            "market_reference_price"
        )

        reference_text = (
            f"{reference:,.0f}円"
            if reference is not None
            else "比較不可"
        )

        print(
            f"{row['category']} / "
            f"自店舗中央値: "
            f"{row['primary_median']:,.0f}円"
            if row.get("primary_median") is not None
            else (
                f"{row['category']} / "
                "自店舗中央値: データなし"
            )
        )

        print(
            f"  市場参考価格: {reference_text} / "
            f"ポジション: {row['position']}"
        )

    # ---------------------------------------------------------
    # PDF用レポートデータ
    # ---------------------------------------------------------
    report_data = {
        "version": VERSION,
        "created_at": datetime.now(),
        "primary_shop": {
            "name": getattr(
                primary_shop,
                "display_name",
                None,
            ) or getattr(
                primary_shop,
                "name",
                "不明店舗",
            ),
            "url": primary_url,
            "summary": primary_summary,
            "pricing": pricing_result,
            "category_analysis": category_analysis,
            "category_rows": category_rows,
            "review_candidates": review_candidates,
        },
        "comparison_shops": comparison_rows,
        "comparison_urls": comparison_urls,
        "notes": [
            "本レポートは自店舗を主対象として、比較対象店舗を市場・参考情報として扱います。",
            "市場参考価格は比較店舗ごとの価格中央値を同じ重みで比較して算出しています。",
            "営業確認候補は機械的な統計・価格閾値による候補抽出であり、異常価格と断定するものではありません。",
            "クーポンの内容・利用条件・対象者条件などは営業担当者による確認を前提とします。",
        ],
    }

    # ---------------------------------------------------------
    # PDF生成
    # ---------------------------------------------------------
    print_separator()
    print("PDFレポートを生成しています...")

    try:
        output_dir = Path("output")
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        output_path = (
            output_dir
            / f"HPB_自店舗分析レポート_{timestamp}.pdf"
        )

        generate_pdf_report(
            report_data,
            output_path,
        )

        print("\n" + "=" * 70)
        print("PDFレポートを生成しました。")
        print(f"保存先: {output_path}")
        print("=" * 70)

    except Exception as e:
        print("\nPDF生成でエラーが発生しました。")
        print(f"エラー内容: {e}")
        print(
            "\n価格分析自体は完了しています。"
            "report_pdf.py のエラー内容を確認してください。"
        )


if __name__ == "__main__":
    main()
